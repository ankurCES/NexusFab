"""Regulatory compliance: allergen sequencing, CIP validation, HACCP CCP monitoring,
batch traceability, and hold-and-release tracking.

All data is deterministic sim from seed — no database needed.
"""

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.seed.products import (
    CIP_CLASS_REQUIREMENTS,
    PRODUCTS,
    compute_allergen_tier,
    get_changeover_time,
    get_products_for_plant,
)


# ── Allergen sequencing ──

ALLERGEN_SEVERITY = {"NUTS": 4, "EGGS": 3, "DAIRY": 2, "SOY": 2, "SESAME": 2, "GLUTEN": 1}


@dataclass
class AllergenSequenceRule:
    from_sku: str
    to_sku: str
    allergens_introduced: list[str]
    requires_cip: bool
    cip_duration_min: float
    cip_class: str  # none | rinse | standard | allergen | deep_clean
    cip_validation_min: float  # LFD 15min, ELISA 30min hold
    sequence_ok: bool  # True if from→to is permitted (lower tier → higher tier)

    def to_dict(self) -> dict:
        return {
            "from_sku": self.from_sku,
            "to_sku": self.to_sku,
            "allergens_introduced": self.allergens_introduced,
            "requires_cip": self.requires_cip,
            "cip_duration_min": self.cip_duration_min,
            "cip_class": self.cip_class,
            "cip_validation_min": self.cip_validation_min,
            "sequence_ok": self.sequence_ok,
        }


def check_allergen_sequence(from_sku: str, to_sku: str) -> AllergenSequenceRule:
    """Check if transitioning from_sku → to_sku is allergen-safe using 5-tier CIP classes."""
    from nexusfab.seed.products import get_product
    p1 = get_product(from_sku)
    p2 = get_product(to_sku)
    a1 = set(p1.allergens) if p1 else set()
    a2 = set(p2.allergens) if p2 else set()
    introduced = sorted(a2 - a1)

    tier_from = compute_allergen_tier(sorted(a1))
    tier_to = compute_allergen_tier(sorted(a2))
    cip_class, cip_duration, validation = CIP_CLASS_REQUIREMENTS[(tier_from, tier_to)]
    validation_min = {"ELISA": 30.0, "LFD": 15.0}.get(validation, 0.0)

    requires_cip = cip_class not in ("none", "rinse")
    # same-tier rinse still required if new allergens introduced
    if introduced and cip_class == "rinse":
        requires_cip = True

    return AllergenSequenceRule(
        from_sku=from_sku,
        to_sku=to_sku,
        allergens_introduced=introduced,
        requires_cip=requires_cip,
        cip_duration_min=cip_duration,
        cip_class=cip_class,
        cip_validation_min=validation_min,
        sequence_ok=tier_from <= tier_to,
    )


# ── CIP validation tracking ──

CIP_TYPES = {
    "none": {"duration_min": 0, "chemicals": []},
    "rinse": {"duration_min": 15, "chemicals": ["water"]},
    "standard": {"duration_min": 45, "chemicals": ["caustic", "acid", "sanitizer"]},
    "allergen": {"duration_min": 75, "chemicals": ["caustic", "acid", "sanitizer", "allergen_surfactant"]},
    "deep_clean": {"duration_min": 120, "chemicals": ["caustic", "acid", "sanitizer", "allergen_surfactant", "enzymatic"]},
}


@dataclass
class CIPRecord:
    cip_id: str
    line_name: str
    plant_id: str
    cip_type: str
    start_time: datetime
    end_time: datetime
    duration_min: float
    validated: bool
    validation_notes: str
    triggered_by: str  # "allergen_transition" | "scheduled" | "deviation"

    def to_dict(self) -> dict:
        return {
            "cip_id": self.cip_id,
            "line": self.line_name,
            "plant_id": self.plant_id,
            "type": self.cip_type,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat(),
            "duration_min": self.duration_min,
            "validated": self.validated,
            "notes": self.validation_notes,
            "triggered_by": self.triggered_by,
        }


# ── HACCP CCP monitoring ──

# ponytail: static CCP definitions per line type. Real system would be DB-backed.
# All 18 CCPs: 17 from nestle-compliance.md §3.1.1 + CCP-W4 for CANNING (100% line coverage).
HACCP_CCPS = {
    # ── PLT-001 Water ──
    "PET_BOTTLING": [
        {"ccp_id": "CCP-W1", "name": "Ozone Concentration", "target": 0.3, "unit": "mg/L",
         "critical_limit_low": 0.2, "critical_limit_high": 0.4, "frequency_min": 1},
        {"ccp_id": "CCP-W2", "name": "UV Dose (254 nm)", "target": 40.0, "unit": "mJ/cm²",
         "critical_limit_low": 40.0, "critical_limit_high": None, "frequency_min": 1},
    ],
    "GLASS_BOTTLING": [
        {"ccp_id": "CCP-W3", "name": "Bottle Rinse Temperature", "target": 85.0, "unit": "°C",
         "critical_limit_low": 82.0, "critical_limit_high": None, "frequency_min": 15},
    ],
    "CANNING": [
        # ponytail: not in research doc, added for 100% coverage. Mirrors GLASS_BOTTLING rinse CCP.
        {"ccp_id": "CCP-W4", "name": "Can Rinse Temperature", "target": 85.0, "unit": "°C",
         "critical_limit_low": 82.0, "critical_limit_high": None, "frequency_min": 15},
    ],
    # ── PLT-002 Confectionery ──
    "MOULDING": [
        {"ccp_id": "CCP-07", "name": "Tempering Temperature", "target": 31.0, "unit": "°C",
         "critical_limit_low": 29.0, "critical_limit_high": 33.0, "frequency_min": 10},
    ],
    "ENROBING": [
        {"ccp_id": "CCP-08", "name": "Enrobing Temperature", "target": 32.0, "unit": "°C",
         "critical_limit_low": 30.0, "critical_limit_high": 34.0, "frequency_min": 10},
    ],
    "WRAPPING": [
        {"ccp_id": "CCP-C3", "name": "Metal Detection", "target": 0.0, "unit": "ppm",
         "critical_limit_low": None, "critical_limit_high": 0.5, "frequency_min": 1},
    ],
    # ── PLT-003 Dairy ──
    "UHT_FILLING": [
        {"ccp_id": "CCP-01", "name": "Pasteurization Temperature", "target": 137.0, "unit": "°C",
         "critical_limit_low": 135.0, "critical_limit_high": 145.0, "frequency_min": 5},
        {"ccp_id": "CCP-02", "name": "Hold Time", "target": 4.0, "unit": "sec",
         "critical_limit_low": 3.5, "critical_limit_high": None, "frequency_min": 5},
    ],
    "POWDER_PACKING": [
        {"ccp_id": "CCP-06", "name": "Metal Detection", "target": 0.0, "unit": "ppm",
         "critical_limit_low": None, "critical_limit_high": 0.5, "frequency_min": 1},
    ],
    "ASEPTIC": [
        {"ccp_id": "CCP-03", "name": "Sterilization Temperature", "target": 142.0, "unit": "°C",
         "critical_limit_low": 140.0, "critical_limit_high": 150.0, "frequency_min": 3},
    ],
    # ── PLT-004 Pet Food ──
    "EXTRUSION": [
        {"ccp_id": "CCP-10", "name": "Extrusion Temperature", "target": 140.0, "unit": "°C",
         "critical_limit_low": 130.0, "critical_limit_high": 155.0, "frequency_min": 5},
    ],
    "RETORT_CANNING": [
        {"ccp_id": "CCP-04", "name": "Retort Temperature", "target": 121.0, "unit": "°C",
         "critical_limit_low": 118.0, "critical_limit_high": 130.0, "frequency_min": 5},
        {"ccp_id": "CCP-05", "name": "Retort Pressure", "target": 1.05, "unit": "bar",
         "critical_limit_low": 0.95, "critical_limit_high": 1.15, "frequency_min": 5},
    ],
    "KIBBLE_COATING": [
        {"ccp_id": "CCP-P4", "name": "Moisture Activity", "target": 0.55, "unit": "aw",
         "critical_limit_low": None, "critical_limit_high": 0.65, "frequency_min": 30},
    ],
    # ── PLT-005 Prepared Foods ──
    "MIXING_COOKING": [
        {"ccp_id": "CCP-09", "name": "Cooking Temperature", "target": 95.0, "unit": "°C",
         "critical_limit_low": 90.0, "critical_limit_high": 100.0, "frequency_min": 5},
    ],
    "FILLING": [
        {"ccp_id": "CCP-F2", "name": "Fill Temperature (Hot-Fill)", "target": 88.0, "unit": "°C",
         "critical_limit_low": 85.0, "critical_limit_high": None, "frequency_min": 5},
    ],
    "NOODLE_LINE": [
        {"ccp_id": "CCP-N3", "name": "Frying Oil Temperature", "target": 150.0, "unit": "°C",
         "critical_limit_low": 140.0, "critical_limit_high": 160.0, "frequency_min": 5},
    ],
}


@dataclass
class CCPReading:
    ccp_id: str
    ccp_name: str
    line_name: str
    timestamp: datetime
    value: float
    unit: str
    in_spec: bool
    deviation: float  # from target

    def to_dict(self) -> dict:
        return {
            "ccp_id": self.ccp_id,
            "ccp_name": self.ccp_name,
            "line": self.line_name,
            "timestamp": self.timestamp.isoformat(),
            "value": round(self.value, 2),
            "unit": self.unit,
            "in_spec": self.in_spec,
            "deviation": round(self.deviation, 3),
        }


# ── Batch traceability ──

@dataclass
class BatchRecord:
    batch_id: str
    plant_id: str
    line_name: str
    sku: str
    product_name: str
    start_time: datetime
    end_time: datetime
    quantity: int
    raw_materials: list[str]
    operator_ids: list[str]
    cip_before: str | None  # CIP record ID
    ccp_readings: list[str]  # CCP reading IDs
    status: str  # "released" | "on_hold" | "rejected" | "pending_review"
    hold_reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "plant_id": self.plant_id,
            "line": self.line_name,
            "sku": self.sku,
            "product": self.product_name,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat(),
            "quantity": self.quantity,
            "raw_materials": self.raw_materials,
            "operators": self.operator_ids,
            "cip_before": self.cip_before,
            "ccp_readings": self.ccp_readings,
            "status": self.status,
            "hold_reason": self.hold_reason,
        }


# ── Hold and release ──

@dataclass
class HoldRelease:
    hold_id: str
    batch_id: str
    hold_reason: str
    hold_date: datetime
    release_date: datetime | None
    status: str  # "on_hold" | "released" | "rejected"
    reviewed_by: str | None
    disposition: str | None  # "release_as_is" | "rework" | "destroy"

    def to_dict(self) -> dict:
        return {
            "hold_id": self.hold_id,
            "batch_id": self.batch_id,
            "reason": self.hold_reason,
            "hold_date": self.hold_date.isoformat(),
            "release_date": self.release_date.isoformat() if self.release_date else None,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "disposition": self.disposition,
        }


# ── Compliance report ──

@dataclass
class ComplianceReport:
    plant_id: str | None
    allergen_checks: list[AllergenSequenceRule] = field(default_factory=list)
    cip_records: list[CIPRecord] = field(default_factory=list)
    ccp_readings: list[CCPReading] = field(default_factory=list)
    batch_records: list[BatchRecord] = field(default_factory=list)
    hold_releases: list[HoldRelease] = field(default_factory=list)
    ccp_compliance_pct: float = 0.0
    cip_validation_pct: float = 0.0
    batches_on_hold: int = 0

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id or "all",
            "ccp_compliance_pct": round(self.ccp_compliance_pct, 2),
            "cip_validation_pct": round(self.cip_validation_pct, 2),
            "batches_on_hold": self.batches_on_hold,
            "total_batches": len(self.batch_records),
            "allergen_checks": [a.to_dict() for a in self.allergen_checks[:20]],
            "cip_records": [c.to_dict() for c in self.cip_records[:20]],
            "ccp_readings": [r.to_dict() for r in self.ccp_readings[:30]],
            "batch_records": [b.to_dict() for b in self.batch_records[:20]],
            "hold_releases": [h.to_dict() for h in self.hold_releases[:10]],
        }


def _det_hash(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def generate_compliance_report(
    plant_id: str | None = None,
    seed: int = 42,
    base_date: datetime | None = None,
    days: int = 7,
) -> ComplianceReport:
    """Generate a full regulatory compliance report with simulated data."""
    if base_date is None:
        base_date = datetime(2026, 7, 23, 0, 0, 0)

    rng = random.Random(seed)
    report = ComplianceReport(plant_id=plant_id)

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    batch_counter = 0
    cip_counter = 0

    for plant in plants:
        products = get_products_for_plant(plant.id)
        if not products:
            continue

        for line in plant.lines:
            current_time = base_date

            # Simulate production runs on this line
            prev_sku = None
            for day in range(days):
                n_runs = rng.randint(2, 4)
                for run_idx in range(n_runs):
                    product = rng.choice(products)

                    # Allergen check against previous run
                    if prev_sku:
                        allergen_check = check_allergen_sequence(prev_sku, product.sku)
                        report.allergen_checks.append(allergen_check)

                        # Generate CIP if needed
                        if allergen_check.requires_cip:
                            cip_counter += 1
                            cip_type = allergen_check.cip_class
                            cip_dur = allergen_check.cip_duration_min + allergen_check.cip_validation_min
                            cip_start = current_time
                            cip_end = cip_start + timedelta(minutes=cip_dur)
                            validated = rng.random() > 0.05  # 95% validation rate
                            report.cip_records.append(CIPRecord(
                                cip_id=f"CIP-{plant.id}-{cip_counter:04d}",
                                line_name=line.name,
                                plant_id=plant.id,
                                cip_type=cip_type,
                                start_time=cip_start,
                                end_time=cip_end,
                                duration_min=cip_dur,
                                validated=validated,
                                validation_notes="Pass" if validated else "ATP swab above threshold",
                                triggered_by="allergen_transition",
                            ))
                            current_time = cip_end

                    # HACCP CCP readings during this run
                    ccps = HACCP_CCPS.get(line.line_type, [])
                    ccp_ids = []
                    for ccp in ccps:
                        reading_time = current_time + timedelta(minutes=rng.randint(5, 30))
                        target = ccp["target"]
                        # 97% in-spec
                        noise = rng.gauss(0, 0.5)
                        value = target + noise
                        low = ccp.get("critical_limit_low")
                        high = ccp.get("critical_limit_high")
                        in_spec = True
                        if low is not None and value < low:
                            in_spec = False
                        if high is not None and value > high:
                            in_spec = False

                        reading_id = f"CCP-R-{_det_hash(f'{line.name}-{day}-{run_idx}-{ccp['ccp_id']}'):08x}"
                        ccp_ids.append(reading_id)
                        report.ccp_readings.append(CCPReading(
                            ccp_id=ccp["ccp_id"],
                            ccp_name=ccp["name"],
                            line_name=line.name,
                            timestamp=reading_time,
                            value=value,
                            unit=ccp["unit"],
                            in_spec=in_spec,
                            deviation=value - target,
                        ))

                    # Batch record
                    batch_counter += 1
                    prod_duration = rng.randint(60, 240)
                    batch_start = current_time
                    batch_end = batch_start + timedelta(minutes=prod_duration)
                    qty = rng.randint(1000, product.units_per_batch)

                    # ponytail: raw materials = product allergens + base ingredients
                    raw_mats = [f"RM-{product.category}-BASE"]
                    raw_mats += [f"RM-{a}" for a in product.allergens]

                    ops = [f"OP-{plant.id}-{rng.randint(1, 30):03d}" for _ in range(rng.randint(2, 4))]

                    # Hold decisions: CCP out-of-spec → hold, random QA hold (2%)
                    any_oos = any(not r.in_spec for r in report.ccp_readings[-len(ccp_ids):] if ccp_ids)
                    qa_hold = rng.random() < 0.02
                    if any_oos:
                        status = "on_hold"
                        hold_reason = "CCP deviation detected"
                    elif qa_hold:
                        status = "on_hold"
                        hold_reason = "Random QA sampling"
                    else:
                        status = "released"
                        hold_reason = None

                    last_cip = report.cip_records[-1].cip_id if report.cip_records else None

                    batch = BatchRecord(
                        batch_id=f"BATCH-{plant.id}-{batch_counter:05d}",
                        plant_id=plant.id,
                        line_name=line.name,
                        sku=product.sku,
                        product_name=product.name,
                        start_time=batch_start,
                        end_time=batch_end,
                        quantity=qty,
                        raw_materials=raw_mats,
                        operator_ids=ops,
                        cip_before=last_cip if prev_sku else None,
                        ccp_readings=ccp_ids,
                        status=status,
                        hold_reason=hold_reason,
                    )
                    report.batch_records.append(batch)

                    # Hold-and-release tracking
                    if status == "on_hold":
                        report.batches_on_hold += 1
                        # Simulate resolution: 80% released, 15% rework, 5% reject
                        resolve_roll = rng.random()
                        if resolve_roll < 0.80:
                            disp = "release_as_is"
                            rel_status = "released"
                        elif resolve_roll < 0.95:
                            disp = "rework"
                            rel_status = "released"
                        else:
                            disp = "destroy"
                            rel_status = "rejected"

                        release_dt = batch_end + timedelta(hours=rng.randint(2, 48))
                        report.hold_releases.append(HoldRelease(
                            hold_id=f"HOLD-{batch.batch_id}",
                            batch_id=batch.batch_id,
                            hold_reason=hold_reason or "",
                            hold_date=batch_end,
                            release_date=release_dt,
                            status=rel_status,
                            reviewed_by=f"QA-{rng.randint(1, 5):02d}",
                            disposition=disp,
                        ))

                    current_time = batch_end + timedelta(minutes=rng.randint(10, 30))
                    prev_sku = product.sku

    # Compute compliance percentages
    if report.ccp_readings:
        in_spec_count = sum(1 for r in report.ccp_readings if r.in_spec)
        report.ccp_compliance_pct = in_spec_count / len(report.ccp_readings) * 100

    if report.cip_records:
        validated_count = sum(1 for c in report.cip_records if c.validated)
        report.cip_validation_pct = validated_count / len(report.cip_records) * 100

    return report


if __name__ == "__main__":
    # CCP coverage check: every line type in the plant network must have ≥1 CCP
    all_line_types = {ls.line_type for ps in PLANTS for ls in ps.lines}
    missing = all_line_types - set(HACCP_CCPS)
    assert not missing, f"Line types missing CCPs: {missing}"
    print(f"CCP coverage: {len(HACCP_CCPS)}/{len(all_line_types)} line types, "
          f"{sum(len(v) for v in HACCP_CCPS.values())} total CCPs — 100%")

    r = generate_compliance_report("PLT-002", days=3)
    d = r.to_dict()
    print(f"PLT-002 Compliance Report:")
    print(f"  Batches: {d['total_batches']}, on hold: {d['batches_on_hold']}")
    print(f"  CCP compliance: {d['ccp_compliance_pct']:.1f}%")
    print(f"  CIP validation: {d['cip_validation_pct']:.1f}%")
    print(f"  Allergen checks: {len(d['allergen_checks'])}")
    print(f"  Hold/release: {len(d['hold_releases'])}")
    assert d['total_batches'] > 0
    assert d['ccp_compliance_pct'] > 80  # should be ~97%
    assert d['cip_validation_pct'] > 80  # should be ~95%
    assert all(b['batch_id'] for b in d['batch_records'])
    for ac in d['allergen_checks']:
        if ac['allergens_introduced']:
            assert ac['requires_cip'], f"Missing CIP for {ac}"

    # 5-tier CIP class checks
    rule_nut_clean = check_allergen_sequence("CON-NUT", "WAT-500S")
    assert rule_nut_clean.cip_class == "deep_clean", f"nut→water should be deep_clean, got {rule_nut_clean.cip_class}"
    assert rule_nut_clean.cip_duration_min == 120.0
    assert rule_nut_clean.cip_validation_min == 30.0, "ELISA hold = 30 min"
    assert not rule_nut_clean.sequence_ok, "tier 4→0 is a sequencing violation"

    rule_upgrade = check_allergen_sequence("WAT-500S", "CON-KB4")
    assert rule_upgrade.cip_class == "allergen", f"water→egg product should be allergen, got {rule_upgrade.cip_class}"
    assert rule_upgrade.cip_validation_min == 15.0, "LFD hold = 15 min"
    assert rule_upgrade.sequence_ok, "tier 0→3 is OK (upgrade)"

    rule_same = check_allergen_sequence("DAI-P4", "DAI-L2")
    assert rule_same.cip_class == "rinse", f"same-tier dairy should be rinse, got {rule_same.cip_class}"

    print(f"  5-tier CIP: nut→clean={rule_nut_clean.cip_class}/{rule_nut_clean.cip_duration_min}min, "
          f"upgrade={rule_upgrade.cip_class}/{rule_upgrade.cip_duration_min}min")

    # Full-network report: all plants should generate CCP readings
    r_all = generate_compliance_report(days=3)
    line_types_with_readings = {reading.line_name for reading in r_all.ccp_readings}
    print(f"  Lines with CCP readings: {len(line_types_with_readings)}")
    assert len(r_all.ccp_readings) > 0, "No CCP readings generated"
    print("PASS")
