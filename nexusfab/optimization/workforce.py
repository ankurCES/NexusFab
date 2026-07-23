"""Workforce optimization + shift planning.

Operator skill matrix, shift coverage analysis, and training gap identification.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nexusfab.seed.plants import PLANTS, get_plant

# Skill levels: 0=none, 1=basic, 2=proficient, 3=expert
_SKILL_NAMES = ["machine_operation", "quality_control", "maintenance_basic", "safety", "changeover", "cip"]

# Operators per line per shift (typical)
_OPERATORS_PER_LINE = 3
_SHIFTS_PER_DAY = 3


@dataclass
class OperatorProfile:
    operator_id: str
    name: str
    plant_id: str
    shift: int
    skills: dict[str, int]
    years_experience: float
    certification_expires: datetime | None = None

    def skill_score(self) -> float:
        return sum(self.skills.values()) / (len(self.skills) * 3.0)

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
    priority: str  # "high" | "medium" | "low"

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
class WorkforceReport:
    plant_id: str | None
    operators: list[OperatorProfile] = field(default_factory=list)
    shift_coverage: list[ShiftCoverage] = field(default_factory=list)
    training_gaps: list[TrainingGap] = field(default_factory=list)
    total_operators: int = 0
    avg_skill_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id or "all",
            "total_operators": self.total_operators,
            "avg_skill_score": round(self.avg_skill_score, 3),
            "shift_coverage": [s.to_dict() for s in self.shift_coverage],
            "training_gaps_count": len(self.training_gaps),
            "training_gaps": [g.to_dict() for g in self.training_gaps[:20]],
            "operators": [o.to_dict() for o in self.operators[:30]],
        }


# ponytail: names pool, deterministic from seed
_FIRST_NAMES = ["Alex", "Jordan", "Sam", "Casey", "Morgan", "Pat", "Riley", "Quinn", "Drew", "Jamie",
                "Taylor", "Avery", "Reese", "Dakota", "Skyler", "Kai", "Robin", "Sage", "Rowan", "Blair"]
_LAST_NAMES = ["Chen", "Patel", "Smith", "Garcia", "Kim", "Lopez", "Nguyen", "Brown", "Davis", "Wilson",
               "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "White", "Harris", "Clark", "Lewis"]


def generate_workforce(
    plant_id: str | None = None,
    seed: int = 42,
    base_date: datetime | None = None,
) -> WorkforceReport:
    """Generate workforce report with operators, coverage, and training gaps."""
    if base_date is None:
        base_date = datetime(2026, 7, 23, 0, 0, 0)

    rng = random.Random(seed)
    report = WorkforceReport(plant_id=plant_id)

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    op_counter = 0
    for plant in plants:
        required_per_shift = len(plant.lines) * _OPERATORS_PER_LINE

        for shift in range(1, _SHIFTS_PER_DAY + 1):
            # Generate operators (85-110% of required)
            n_ops = rng.randint(int(required_per_shift * 0.85), int(required_per_shift * 1.1))
            shift_operators = []

            for _ in range(n_ops):
                op_counter += 1
                first = rng.choice(_FIRST_NAMES)
                last = rng.choice(_LAST_NAMES)
                years = round(rng.uniform(0.5, 25.0), 1)

                skills = {}
                for skill in _SKILL_NAMES:
                    base_level = min(3, max(0, int(years / 5)))
                    skills[skill] = min(3, base_level + rng.randint(0, 1))

                cert_exp = base_date + timedelta(days=rng.randint(-30, 365))

                op = OperatorProfile(
                    operator_id=f"OP-{plant.id}-{op_counter:03d}",
                    name=f"{first} {last}",
                    plant_id=plant.id,
                    shift=shift,
                    skills=skills,
                    years_experience=years,
                    certification_expires=cert_exp,
                )
                shift_operators.append(op)
                report.operators.append(op)

            # Shift coverage
            avg_skill = sum(o.skill_score() for o in shift_operators) / len(shift_operators) if shift_operators else 0
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

    # Training gaps: operators with skill < 2 in critical areas
    critical_skills = {"safety": 2, "machine_operation": 2, "quality_control": 2}
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
    return report


if __name__ == "__main__":
    r = generate_workforce("PLT-001")
    d = r.to_dict()
    print(f"PLT-001: {d['total_operators']} operators, avg skill {d['avg_skill_score']:.2f}")
    print(f"Training gaps: {d['training_gaps_count']}")
    print(f"Shifts: {len(d['shift_coverage'])}")
    for s in d['shift_coverage']:
        print(f"  Shift {s['shift']}: {s['available']}/{s['required']} ({s['coverage_pct']:.0%}) gaps={s['gaps']}")
    assert d['total_operators'] > 0
    print("PASS")
