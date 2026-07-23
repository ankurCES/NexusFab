"""Workforce scheduling & optimization.

Shift assignment, 5-level skill matrix, overtime optimization (1.5x-2x premium),
cross-training coverage, and line-operator qualification matching.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nexusfab.seed.plants import PLANTS, get_plant

# ponytail: 5-level skill matrix per spec. 0=none, 1=basic, 2=proficient, 3=advanced, 4=expert
SKILL_LEVELS = {0: "none", 1: "basic", 2: "proficient", 3: "advanced", 4: "expert"}
SKILL_NAMES = [
    "machine_operation", "quality_control", "maintenance_basic",
    "safety", "changeover", "cip", "haccp_monitoring",
]

OPERATORS_PER_LINE = 3
SHIFTS_PER_DAY = 3
SHIFT_HOURS = 8
MAX_OVERTIME_HOURS = 4
MAX_WEEKLY_HOURS = 48
MIN_REST_HOURS = 11  # between shifts, EU Working Time Directive style

# Overtime premium tiers
OT_PREMIUM = {
    "standard": 1.5,   # first 2 hours OT
    "extended": 2.0,   # beyond 2 hours OT
}
OT_TIER_BOUNDARY = 2  # hours


@dataclass
class OperatorProfile:
    operator_id: str
    name: str
    plant_id: str
    shift: int
    skills: dict[str, int]  # skill_name → 0-4
    years_experience: float
    certification_expires: datetime | None = None
    qualified_lines: list[str] = field(default_factory=list)
    base_hourly_rate: float = 25.0

    def skill_score(self) -> float:
        return sum(self.skills.values()) / (len(self.skills) * 4.0)

    def can_operate_line(self, min_level: int = 2) -> bool:
        return self.skills.get("machine_operation", 0) >= min_level

    def overtime_cost(self, ot_hours: float) -> float:
        if ot_hours <= 0:
            return 0.0
        tier1 = min(ot_hours, OT_TIER_BOUNDARY)
        tier2 = max(0.0, ot_hours - OT_TIER_BOUNDARY)
        return (tier1 * self.base_hourly_rate * OT_PREMIUM["standard"] +
                tier2 * self.base_hourly_rate * OT_PREMIUM["extended"])

    def to_dict(self) -> dict:
        return {
            "id": self.operator_id,
            "name": self.name,
            "plant_id": self.plant_id,
            "shift": self.shift,
            "skills": self.skills,
            "skill_score": round(self.skill_score(), 3),
            "experience_years": self.years_experience,
            "cert_expires": self.certification_expires.isoformat() if self.certification_expires else None,
            "qualified_lines": self.qualified_lines,
        }


@dataclass
class ShiftAssignment:
    operator_id: str
    operator_name: str
    line_name: str
    shift: int
    date: str
    regular_hours: float
    overtime_hours: float
    overtime_cost: float
    skill_match_score: float  # how well operator matches the line's needs

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "operator_name": self.operator_name,
            "line": self.line_name,
            "shift": self.shift,
            "date": self.date,
            "regular_hours": self.regular_hours,
            "overtime_hours": round(self.overtime_hours, 1),
            "overtime_cost": round(self.overtime_cost, 2),
            "skill_match": round(self.skill_match_score, 3),
        }


@dataclass
class ShiftCoverage:
    plant_id: str
    shift: int
    required_operators: int
    available_operators: int
    coverage_pct: float
    avg_skill_score: float
    gaps: list[str]

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id,
            "shift": self.shift,
            "required": self.required_operators,
            "available": self.available_operators,
            "coverage_pct": round(self.coverage_pct, 4),
            "avg_skill": round(self.avg_skill_score, 3),
            "gaps": self.gaps,
        }


@dataclass
class TrainingGap:
    operator_id: str
    operator_name: str
    skill: str
    current_level: int
    required_level: int
    priority: str

    def to_dict(self) -> dict:
        return {
            "operator": self.operator_id,
            "name": self.operator_name,
            "skill": self.skill,
            "current": self.current_level,
            "required": self.required_level,
            "priority": self.priority,
        }


@dataclass
class CrossTrainingCandidate:
    operator_id: str
    operator_name: str
    current_lines: list[str]
    target_line: str
    gap_skills: dict[str, int]  # skill → levels needed
    training_hours_est: float
    coverage_benefit: str  # which shift gap this would close

    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "operator_name": self.operator_name,
            "current_lines": self.current_lines,
            "target_line": self.target_line,
            "gap_skills": self.gap_skills,
            "training_hours": round(self.training_hours_est, 1),
            "coverage_benefit": self.coverage_benefit,
        }


@dataclass
class WorkforceReport:
    plant_id: str | None
    operators: list[OperatorProfile] = field(default_factory=list)
    shift_coverage: list[ShiftCoverage] = field(default_factory=list)
    training_gaps: list[TrainingGap] = field(default_factory=list)
    shift_assignments: list[ShiftAssignment] = field(default_factory=list)
    cross_training: list[CrossTrainingCandidate] = field(default_factory=list)
    total_operators: int = 0
    avg_skill_score: float = 0.0
    total_overtime_hours: float = 0.0
    total_overtime_cost: float = 0.0

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id or "all",
            "total_operators": self.total_operators,
            "avg_skill_score": round(self.avg_skill_score, 3),
            "total_overtime_hours": round(self.total_overtime_hours, 1),
            "total_overtime_cost": round(self.total_overtime_cost, 2),
            "shift_coverage": [s.to_dict() for s in self.shift_coverage],
            "training_gaps_count": len(self.training_gaps),
            "training_gaps": [g.to_dict() for g in self.training_gaps[:20]],
            "operators": [o.to_dict() for o in self.operators[:30]],
            "shift_assignments": [a.to_dict() for a in self.shift_assignments[:50]],
            "cross_training": [c.to_dict() for c in self.cross_training[:10]],
        }


_FIRST_NAMES = ["Alex", "Jordan", "Sam", "Casey", "Morgan", "Pat", "Riley", "Quinn", "Drew", "Jamie",
                "Taylor", "Avery", "Reese", "Dakota", "Skyler", "Kai", "Robin", "Sage", "Rowan", "Blair"]
_LAST_NAMES = ["Chen", "Patel", "Smith", "Garcia", "Kim", "Lopez", "Nguyen", "Brown", "Davis", "Wilson",
               "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "White", "Harris", "Clark", "Lewis"]


def _line_skill_requirements(line_type: str) -> dict[str, int]:
    """Minimum skill levels required to operate a given line type."""
    base = {"machine_operation": 2, "safety": 2, "quality_control": 1}
    if "UHT" in line_type or "ASEPTIC" in line_type or "PASTEUR" in line_type:
        base["cip"] = 3
        base["haccp_monitoring"] = 3
    elif "RETORT" in line_type:
        base["cip"] = 2
        base["haccp_monitoring"] = 3
    elif line_type in ("MOULDING", "ENROBING"):
        base["changeover"] = 3
        base["cip"] = 2
    elif "POWDER" in line_type:
        base["cip"] = 2
    return base


def _operator_line_match_score(op: OperatorProfile, line_type: str) -> float:
    """0.0-1.0 match score: how well operator's skills meet line requirements."""
    reqs = _line_skill_requirements(line_type)
    if not reqs:
        return 0.5
    met = sum(1 for skill, lvl in reqs.items() if op.skills.get(skill, 0) >= lvl)
    return met / len(reqs)


def generate_workforce(
    plant_id: str | None = None,
    seed: int = 42,
    base_date: datetime | None = None,
    schedule_days: int = 7,
) -> WorkforceReport:
    """Generate workforce report with operators, coverage, shift assignments,
    overtime optimization, and cross-training candidates."""
    if base_date is None:
        base_date = datetime(2026, 7, 23, 0, 0, 0)

    rng = random.Random(seed)
    report = WorkforceReport(plant_id=plant_id)

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    op_counter = 0
    for plant in plants:
        required_per_shift = len(plant.lines) * OPERATORS_PER_LINE

        for shift in range(1, SHIFTS_PER_DAY + 1):
            n_ops = rng.randint(int(required_per_shift * 0.85), int(required_per_shift * 1.1))
            shift_operators: list[OperatorProfile] = []

            for _ in range(n_ops):
                op_counter += 1
                first = rng.choice(_FIRST_NAMES)
                last = rng.choice(_LAST_NAMES)
                years = round(rng.uniform(0.5, 25.0), 1)

                skills: dict[str, int] = {}
                for skill in SKILL_NAMES:
                    base_level = min(4, max(0, int(years / 4)))
                    skills[skill] = min(4, base_level + rng.randint(-1, 1))
                    skills[skill] = max(0, skills[skill])

                cert_exp = base_date + timedelta(days=rng.randint(-30, 365))

                # Determine which lines this operator is qualified for
                qualified = []
                for line in plant.lines:
                    if _operator_line_match_score(
                        OperatorProfile("", "", "", 0, skills, 0),
                        line.line_type,
                    ) >= 0.7:
                        qualified.append(line.name)

                rate = 22.0 + years * 0.8 + rng.uniform(-2, 3)

                op = OperatorProfile(
                    operator_id=f"OP-{plant.id}-{op_counter:03d}",
                    name=f"{first} {last}",
                    plant_id=plant.id,
                    shift=shift,
                    skills=skills,
                    years_experience=years,
                    certification_expires=cert_exp,
                    qualified_lines=qualified,
                    base_hourly_rate=round(rate, 2),
                )
                shift_operators.append(op)
                report.operators.append(op)

            # Shift coverage
            avg_skill = (sum(o.skill_score() for o in shift_operators) / len(shift_operators)
                         if shift_operators else 0)
            gaps = []
            if len(shift_operators) < required_per_shift:
                gaps.append(f"Understaffed by {required_per_shift - len(shift_operators)}")
            if avg_skill < 0.5:
                gaps.append("Low average skill level")

            low_skill_count = sum(1 for o in shift_operators if o.skill_score() < 0.4)
            if low_skill_count > len(shift_operators) * 0.3:
                gaps.append(f"{low_skill_count} operators below minimum skill threshold")

            report.shift_coverage.append(ShiftCoverage(
                plant_id=plant.id,
                shift=shift,
                required_operators=required_per_shift,
                available_operators=len(shift_operators),
                coverage_pct=len(shift_operators) / required_per_shift if required_per_shift > 0 else 0,
                avg_skill_score=avg_skill,
                gaps=gaps,
            ))

        # Shift assignments: assign operators to lines for schedule_days
        # ponytail: greedy assignment by skill match, O(ops*lines) per day. LP if throughput matters.
        plant_ops = [o for o in report.operators if o.plant_id == plant.id]
        weekly_ot: dict[str, float] = {o.operator_id: 0.0 for o in plant_ops}

        for day_offset in range(schedule_days):
            day_str = (base_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")

            for shift in range(1, SHIFTS_PER_DAY + 1):
                shift_ops = [o for o in plant_ops if o.shift == shift]

                for line in plant.lines:
                    # Sort operators by match score for this line (best first)
                    scored = [(o, _operator_line_match_score(o, line.line_type)) for o in shift_ops]
                    scored.sort(key=lambda x: -x[1])

                    assigned_count = 0
                    for op, match_score in scored:
                        if assigned_count >= OPERATORS_PER_LINE:
                            break
                        if match_score < 0.5:
                            continue

                        # Check weekly overtime cap
                        current_weekly = weekly_ot.get(op.operator_id, 0.0)
                        ot_needed = 0.0
                        # Some days need overtime to meet demand
                        if rng.random() < 0.2:  # 20% chance of OT need
                            ot_needed = min(
                                rng.uniform(1, MAX_OVERTIME_HOURS),
                                MAX_WEEKLY_HOURS - (SHIFT_HOURS * min(day_offset + 1, 5)) - current_weekly,
                            )
                            ot_needed = max(0, ot_needed)

                        ot_cost = op.overtime_cost(ot_needed)
                        weekly_ot[op.operator_id] = current_weekly + ot_needed

                        report.shift_assignments.append(ShiftAssignment(
                            operator_id=op.operator_id,
                            operator_name=op.name,
                            line_name=line.name,
                            shift=shift,
                            date=day_str,
                            regular_hours=SHIFT_HOURS,
                            overtime_hours=ot_needed,
                            overtime_cost=ot_cost,
                            skill_match_score=match_score,
                        ))
                        report.total_overtime_hours += ot_needed
                        report.total_overtime_cost += ot_cost
                        assigned_count += 1

        # Cross-training candidates: find ops who almost qualify for undermanned lines
        shift_line_coverage: dict[tuple[int, str], int] = {}
        for a in report.shift_assignments:
            if a.operator_id.startswith(f"OP-{plant.id}"):
                key = (a.shift, a.line_name)
                shift_line_coverage[key] = shift_line_coverage.get(key, 0) + 1

        for shift in range(1, SHIFTS_PER_DAY + 1):
            for line in plant.lines:
                covered = shift_line_coverage.get((shift, line.name), 0)
                if covered >= OPERATORS_PER_LINE * schedule_days:
                    continue
                # Find operators on this shift qualified for other lines but not this one
                shift_ops = [o for o in plant_ops if o.shift == shift]
                reqs = _line_skill_requirements(line.line_type)
                for op in shift_ops:
                    if line.name in op.qualified_lines:
                        continue
                    gap_skills = {}
                    for sk, lvl in reqs.items():
                        if op.skills.get(sk, 0) < lvl:
                            gap_skills[sk] = lvl - op.skills.get(sk, 0)
                    if gap_skills and sum(gap_skills.values()) <= 3:
                        hours = sum(gap_skills.values()) * 16  # ~16h training per level
                        report.cross_training.append(CrossTrainingCandidate(
                            operator_id=op.operator_id,
                            operator_name=op.name,
                            current_lines=op.qualified_lines[:3],
                            target_line=line.name,
                            gap_skills=gap_skills,
                            training_hours_est=hours,
                            coverage_benefit=f"Shift {shift} {line.name} coverage gap",
                        ))

    # Training gaps
    critical_skills = {"safety": 2, "machine_operation": 2, "quality_control": 2, "haccp_monitoring": 2}
    for op in report.operators:
        for skill, required in critical_skills.items():
            if op.skills.get(skill, 0) < required:
                gap_size = required - op.skills.get(skill, 0)
                report.training_gaps.append(TrainingGap(
                    operator_id=op.operator_id,
                    operator_name=op.name,
                    skill=skill,
                    current_level=op.skills.get(skill, 0),
                    required_level=required,
                    priority="high" if gap_size >= 2 else "medium",
                ))

    report.training_gaps.sort(key=lambda g: (0 if g.priority == "high" else 1, g.skill))
    report.total_operators = len(report.operators)
    report.avg_skill_score = (
        sum(o.skill_score() for o in report.operators) / len(report.operators)
        if report.operators else 0
    )
    report.cross_training.sort(key=lambda c: c.training_hours_est)
    return report


# ── Labor cost constants (§2.4 energy-workforce-simulation research) ──

WAGE_RATES: dict[str, float] = {
    "operator": 25.0, "senior_operator": 29.0, "technician": 34.0,
    "supervisor": 43.0, "qa_inspector": 31.5,
}
BURDEN_MULTIPLIER = 1.35

PREMIUM_NIGHT = 1.10
PREMIUM_SAT = 1.15
PREMIUM_SUN = 1.25
PREMIUM_HOLIDAY = 2.00
OT_MULT = 1.50
DOUBLE_OT_MULT = 2.00

PLANT_COL: dict[str, float] = {
    "PLT-001": 0.95,  # Arlington TX
    "PLT-002": 0.92,  # Burlington WI
    "PLT-003": 1.15,  # Modesto CA
    "PLT-004": 1.05,  # Denver CO
    "PLT-005": 0.88,  # Gaffney SC
}

# ponytail: fixed default roster, override per-plant when actual headcounts known
DEFAULT_ROSTER: dict[str, int] = {
    "operator": 36, "senior_operator": 12, "technician": 9,
    "supervisor": 3, "qa_inspector": 6,
}


def calculate_labor_cost(
    plant_id: str,
    shift_roster: dict[str, int] | None = None,
    period_days: int = 30,
    holiday_days: int = 0,
    avg_weekly_hours: float = 42.0,
) -> dict:
    """Fully-burdened labor cost with multiplicatively stacking premiums.

    shift_roster: {role: headcount} total workers per role (defaults to DEFAULT_ROSTER).
    """
    if shift_roster is None:
        shift_roster = DEFAULT_ROSTER
    col = PLANT_COL.get(plant_id, 1.0)
    weeks = period_days / 7
    night_f = 1 / 3
    hol_f = holiday_days / period_days if period_days else 0.0

    # ponytail: analytical expected multiplier per independent category, O(1) per role
    e_shift = (1 - night_f) + night_f * PREMIUM_NIGHT
    e_day = (max(0.0, 5 / 7 - hol_f) + 1 / 7 * PREMIUM_SAT
             + 1 / 7 * PREMIUM_SUN + hol_f * PREMIUM_HOLIDAY)
    awh = avg_weekly_hours or 40.0
    reg = min(40.0, awh)
    ot = max(0.0, min(60.0, awh) - 40.0)
    dot = max(0.0, awh - 60.0)
    e_ot = (reg + ot * OT_MULT + dot * DOUBLE_OT_MULT) / awh
    eff = e_shift * e_day * e_ot

    total = 0.0
    breakdown: dict[str, float] = {}
    base_sum = 0.0

    for role, count in shift_roster.items():
        rate = WAGE_RATES.get(role)
        if rate is None:
            continue
        burdened = rate * BURDEN_MULTIPLIER * col
        hours = awh * weeks * count
        base = hours * burdened
        breakdown[role] = round(base * eff, 2)
        total += base * eff
        base_sum += base

    premiums = {
        "night": round(base_sum * (e_shift - 1) * e_day * e_ot, 2),
        "weekend": round(base_sum * e_shift * e_ot * (
            1 / 7 * (PREMIUM_SAT - 1) + 1 / 7 * (PREMIUM_SUN - 1)), 2),
        "holiday": round(base_sum * e_shift * e_ot * hol_f * (PREMIUM_HOLIDAY - 1), 2),
        "overtime": round(base_sum * e_shift * e_day * ot / awh * (OT_MULT - 1), 2),
        "double_overtime": round(base_sum * e_shift * e_day * dot / awh * (DOUBLE_OT_MULT - 1), 2),
    }

    return {
        "total": round(total, 2),
        "breakdown_by_role": breakdown,
        "premium_costs": premiums,
        "overtime_pct": round((ot + dot) / awh * 100, 2),
        "labor_cost_per_hour": round(total / (period_days * 24) if period_days else 0, 2),
    }


def cost_per_unit(plant_id: str, units_produced: int, period_days: int = 30,
                  shift_roster: dict[str, int] | None = None) -> float:
    """Labor component of COGS: total labor cost / units produced."""
    if units_produced <= 0:
        return 0.0
    lc = calculate_labor_cost(plant_id, shift_roster, period_days)
    return round(lc["total"] / units_produced, 4)


if __name__ == "__main__":
    r = generate_workforce("PLT-001")
    d = r.to_dict()
    print(f"PLT-001: {d['total_operators']} operators, avg skill {d['avg_skill_score']:.2f}")
    print(f"Training gaps: {d['training_gaps_count']}")
    print(f"OT: {d['total_overtime_hours']:.1f}h, ${d['total_overtime_cost']:.2f}")
    print(f"Shift assignments: {len(d['shift_assignments'])}")
    print(f"Cross-training candidates: {len(d['cross_training'])}")
    for s in d['shift_coverage']:
        print(f"  Shift {s['shift']}: {s['available']}/{s['required']} ({s['coverage_pct']:.0%}) gaps={s['gaps']}")
    assert d['total_operators'] > 0
    assert d['total_overtime_hours'] >= 0
    assert len(d['shift_assignments']) > 0

    # Labor cost: PLT-003 (CA, CoL 1.15) vs PLT-005 (SC, CoL 0.88)
    print("\n── Labor Cost (30-day, default roster, 42h avg week) ──")
    ca = calculate_labor_cost("PLT-003", period_days=30)
    sc = calculate_labor_cost("PLT-005", period_days=30)
    for tag, lc in [("PLT-003 CA", ca), ("PLT-005 SC", sc)]:
        print(f"  {tag}: ${lc['total']:,.2f}  OT%={lc['overtime_pct']:.1f}  $/hr={lc['labor_cost_per_hour']:.2f}")
        print(f"    premiums: {lc['premium_costs']}")
    ratio = ca["total"] / sc["total"]
    print(f"  CA/SC ratio: {ratio:.3f}  (expected ~{PLANT_COL['PLT-003']/PLANT_COL['PLT-005']:.3f})")
    assert ratio > 1.0, "CA should cost more than SC"
    assert abs(ratio - PLANT_COL["PLT-003"] / PLANT_COL["PLT-005"]) < 0.01
    assert ca["overtime_pct"] == sc["overtime_pct"], "OT% should be identical (same hours)"
    assert ca["labor_cost_per_hour"] > sc["labor_cost_per_hour"]
    cpu = cost_per_unit("PLT-003", 500_000)
    assert cpu > 0
    print(f"  PLT-003 cost/unit (500k units): ${cpu:.4f}")
    print("PASS")
