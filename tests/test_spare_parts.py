"""Spare parts inventory module tests."""

from nexusfab.optimization.spare_parts import (
    _abc_classify,
    _safety_stock,
    _z_score,
    analyze_inventory,
    cross_plant_pooling,
    generate_alerts,
    generate_reorder,
)


def test_abc_classification():
    assert _abc_classify(1000.0, 10.0) == "A"  # 10k
    assert _abc_classify(100.0, 20.0) == "B"   # 2k
    assert _abc_classify(10.0, 5.0) == "C"     # 50


def test_z_scores_increase():
    prev = 0.0
    for sl in [0.95, 0.96, 0.97, 0.98, 0.99]:
        z = _z_score(sl)
        assert z > prev
        prev = z


def test_safety_stock_increases_with_service_level():
    ss95 = _safety_stock(100.0, 28, 0.95)
    ss99 = _safety_stock(100.0, 28, 0.99)
    assert ss99 > ss95


def test_analyze_inventory_single_plant():
    r = analyze_inventory("PLT-001")
    assert r.plant_id == "PLT-001"
    assert len(r.parts) > 0
    assert r.total_inventory_value > 0
    assert all(p.abc_class in ("A", "B", "C") for p in r.parts)
    assert all(p.service_level >= 0.95 for p in r.parts)


def test_analyze_inventory_all_plants():
    single = analyze_inventory("PLT-001")
    all_ = analyze_inventory()
    assert len(all_.parts) >= len(single.parts)


def test_alerts_generated():
    alerts = generate_alerts("PLT-001")
    assert isinstance(alerts, list)
    for a in alerts:
        assert a.severity in ("critical", "warning", "info")


def test_cross_plant_pooling():
    candidates = cross_plant_pooling()
    assert len(candidates) > 0
    for c in candidates:
        assert len(c.plants_using) >= 2
        assert c.savings_units > 0
        assert c.abc_class in ("A", "B")  # C excluded


def test_reorder_generation():
    actions = generate_reorder("PLT-001")
    for a in actions:
        assert a.reorder_qty > 0
        assert a.priority in ("urgent", "normal")
        assert a.total_cost == a.unit_cost * a.reorder_qty
