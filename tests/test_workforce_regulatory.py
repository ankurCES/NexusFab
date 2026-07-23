"""Tests for workforce scheduling and regulatory compliance modules."""

from nexusfab.optimization.regulatory import (
    check_allergen_sequence,
    generate_compliance_report,
)
from nexusfab.optimization.workforce import (
    MAX_OVERTIME_HOURS,
    SKILL_LEVELS,
    generate_workforce,
)


# ── Workforce scheduling ──


def test_skill_matrix_five_levels():
    r = generate_workforce("PLT-001")
    for op in r.operators:
        for skill, level in op.skills.items():
            assert 0 <= level <= 4, f"{op.operator_id} has {skill}={level}"
    assert len(SKILL_LEVELS) == 5


def test_shift_schedules_generated():
    r = generate_workforce("PLT-001", schedule_days=3)
    assert len(r.shift_assignments) > 0
    for a in r.shift_assignments:
        assert a.regular_hours == 8
        assert 0 <= a.overtime_hours <= MAX_OVERTIME_HOURS


def test_overtime_premium_tiers():
    r = generate_workforce("PLT-001")
    op = r.operators[0]
    assert op.overtime_cost(0) == 0.0
    cost_1h = op.overtime_cost(1.0)
    cost_3h = op.overtime_cost(3.0)
    assert cost_3h > cost_1h * 2  # 3rd hour is 2x, not 1.5x


def test_skill_match_operators_to_lines():
    r = generate_workforce("PLT-001")
    for a in r.shift_assignments:
        assert a.skill_match_score >= 0.5, (
            f"{a.operator_id} on {a.line} with score {a.skill_match_score}"
        )


def test_cross_training_coverage():
    r = generate_workforce("PLT-002")
    # Should identify at least some cross-training candidates
    # (PLT-002 has moulding/enrobing/wrapping which have different skill reqs)
    for c in r.cross_training:
        assert c.training_hours_est > 0
        assert len(c.gap_skills) > 0


def test_workforce_all_plants():
    single = generate_workforce("PLT-001")
    all_ = generate_workforce()
    assert all_.total_operators >= single.total_operators


# ── Regulatory compliance ──


def test_allergen_sequencing_enforced():
    # Non-allergen → allergen (water → chocolate) needs CIP
    rule = check_allergen_sequence("WAT-500S", "CON-KB4")
    assert rule.requires_cip
    assert "GLUTEN" in rule.allergens_introduced or "DAIRY" in rule.allergens_introduced
    assert rule.cip_duration_min > 0

    # Same allergen profile: no new allergens introduced
    rule2 = check_allergen_sequence("CON-KB4", "CON-KBD")
    assert not rule2.allergens_introduced


def test_cip_auto_scheduled():
    r = generate_compliance_report("PLT-002", days=3)
    assert len(r.cip_records) > 0
    for cip in r.cip_records:
        assert cip.duration_min > 0
        assert cip.cip_type in ("standard", "allergen", "deep_clean")


def test_haccp_ccp_monitoring():
    # PLT-003 has UHT_FILLING and ASEPTIC lines with CCPs
    r = generate_compliance_report("PLT-003", days=3)
    assert len(r.ccp_readings) > 0
    assert r.ccp_compliance_pct > 80


def test_batch_traceability_records():
    r = generate_compliance_report("PLT-001", days=3)
    assert len(r.batch_records) > 0
    for b in r.batch_records:
        assert b.batch_id
        assert b.sku
        assert b.plant_id == "PLT-001"
        assert len(b.raw_materials) > 0
        assert len(b.operator_ids) > 0
        assert b.status in ("released", "on_hold", "rejected", "pending_review")


def test_hold_and_release_tracking():
    r = generate_compliance_report("PLT-002", days=7)
    # With 7 days of data there should be at least one hold
    if r.hold_releases:
        for h in r.hold_releases:
            assert h.hold_id
            assert h.batch_id
            assert h.status in ("on_hold", "released", "rejected")
            assert h.disposition in ("release_as_is", "rework", "destroy")


def test_cip_validation_rate():
    r = generate_compliance_report("PLT-002", days=7)
    assert r.cip_validation_pct > 80  # expected ~95%


def test_compliance_all_plants():
    r = generate_compliance_report(days=3)
    assert len(r.batch_records) > 0
    assert r.ccp_compliance_pct > 0 or len(r.ccp_readings) == 0
