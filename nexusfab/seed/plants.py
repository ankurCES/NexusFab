"""Nestlé 5-plant network seed data."""

import math
import uuid
from dataclasses import dataclass, field

NEXUSFAB_NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def seed_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(NEXUSFAB_NS, name)


# Weibull (β=shape, η=scale in hours) from docs/research/maintenance-spare-parts.md §1
WEIBULL_BY_TYPE: dict[str, tuple[float, float]] = {
    "FILLER":      (2.2, 1100),   # Rotary Filler
    "MIXER":       (2.0, 3400),   # Mixer/paddle
    "CAPPER":      (1.8,  900),   # Linear Filler analog
    "LABELER":     (1.5,  590),   # Flow-wrap analog
    "CONVEYOR":    (1.0, 1500),   # Belt Conveyor (exponential)
    "PACKAGING":   (1.8,  870),   # Cartoner
    "PASTEURIZER": (2.5, 2200),   # UHT Sterilizer (tubular)
    "HOMOGENIZER": (2.0, 1250),   # UHT Sterilizer (plate)
    "DRYER":       (3.0,  615),   # Extruder (twin-screw) analog
}


@dataclass
class EquipmentSeed:
    name: str
    equipment_type: str
    weibull_beta: float
    weibull_eta: float
    mttr_hours: float
    position: int

    @property
    def mtbf_hours(self) -> float:
        """Mean time between failures derived from Weibull: E[X] = η·Γ(1 + 1/β)."""
        return self.weibull_eta * math.gamma(1 + 1 / self.weibull_beta)


@dataclass
class LineSeed:
    name: str
    line_type: str
    rated_speed_per_min: float
    bottleneck_equipment: str = ""
    equipment: list[EquipmentSeed] = field(default_factory=list)
    upstream_lines: list[str] = field(default_factory=list)


@dataclass
class PlantSeed:
    id: str
    name: str
    location: str
    category: str
    capacity_tons_per_day: float
    lines: list[LineSeed] = field(default_factory=list)
    lat: float = 0.0
    lon: float = 0.0
    starting_oee: float = 0.60
    target_oee: float = 0.78
    oee_benchmark_world_class: tuple[float, float] = (0.80, 0.90)


def _e(name: str, etype: str, mtbf: float, mttr: float, pos: int) -> EquipmentSeed:
    beta, _ = WEIBULL_BY_TYPE[etype]
    eta = mtbf / math.gamma(1 + 1 / beta)
    return EquipmentSeed(name, etype, beta, eta, mttr, pos)


# fmt: off
PLANTS: list[PlantSeed] = [
    # ── PLT-001  Water bottling (Perrier-style) ── 4 lines, 15 equipment
    PlantSeed(
        id="PLT-001", name="NexWater-East", location="Eastern Region",
        category="WATER", capacity_tons_per_day=1400.0,
        lat=40.71, lon=-74.01, starting_oee=0.62, target_oee=0.80,
        oee_benchmark_world_class=(0.87, 0.92),
        lines=[
            LineSeed("PLT-001-L1", "PET_BOTTLING", 600.0, "PLT001-L1-FIL", [
                _e("PLT001-L1-MXR", "MIXER",    350, 3.0, 1),
                _e("PLT001-L1-FIL", "FILLER",   160, 2.5, 2),
                _e("PLT001-L1-CAP", "CAPPER",   280, 1.0, 3),
                _e("PLT001-L1-LBL", "LABELER",  400, 1.0, 4),
            ]),
            LineSeed("PLT-001-L2", "PET_BOTTLING", 500.0, "PLT001-L2-FIL", [
                _e("PLT001-L2-FIL", "FILLER",   180, 2.0, 1),
                _e("PLT001-L2-CAP", "CAPPER",   250, 1.5, 2),
                _e("PLT001-L2-LBL", "LABELER",  350, 0.8, 3),
                _e("PLT001-L2-CNV", "CONVEYOR", 1200, 0.5, 4),
            ]),
            LineSeed("PLT-001-L3", "GLASS_BOTTLING", 400.0, "PLT001-L3-FIL", [
                _e("PLT001-L3-MXR", "MIXER",    400, 3.5, 1),
                _e("PLT001-L3-FIL", "FILLER",   140, 3.0, 2),
                _e("PLT001-L3-CAP", "CAPPER",   300, 1.0, 3),
                _e("PLT001-L3-LBL", "LABELER",  450, 0.7, 4),
            ]),
            LineSeed("PLT-001-L4", "CANNING", 700.0, "PLT001-L4-FIL", [
                _e("PLT001-L4-FIL", "FILLER",   200, 1.5, 1),
                _e("PLT001-L4-CAP", "CAPPER",   320, 0.5, 2),
                _e("PLT001-L4-CNV", "CONVEYOR", 1500, 0.8, 3),
            ]),
        ],
    ),
    # ── PLT-002  Confectionery (KitKat-style) ── 3 lines, 12 equipment
    PlantSeed(
        id="PLT-002", name="NexConfec-Central", location="Central Region",
        category="CONFECTIONERY", capacity_tons_per_day=140.0,
        lat=41.88, lon=-87.63, starting_oee=0.55, target_oee=0.78,
        oee_benchmark_world_class=(0.76, 0.84),
        lines=[
            LineSeed("PLT-002-L1", "MOULDING", 400.0, "PLT002-L1-FIL", [
                _e("PLT002-L1-MXR", "MIXER",     350, 4.0, 1),
                _e("PLT002-L1-FIL", "FILLER",    130, 3.0, 2),
                _e("PLT002-L1-CAP", "CAPPER",    300, 1.5, 3),
                _e("PLT002-L1-PKG", "PACKAGING", 250, 2.0, 4),
            ]),
            LineSeed("PLT-002-L2", "ENROBING", 300.0, "PLT002-L2-FIL", [
                _e("PLT002-L2-MXR", "MIXER",     380, 3.5, 1),
                _e("PLT002-L2-FIL", "FILLER",    150, 2.5, 2),
                _e("PLT002-L2-LBL", "LABELER",   400, 1.0, 3),
                _e("PLT002-L2-PKG", "PACKAGING", 280, 2.5, 4),
            ]),
            LineSeed("PLT-002-L3", "WRAPPING", 500.0, "PLT002-L3-FIL", [
                _e("PLT002-L3-FIL", "FILLER",    170, 2.0, 1),
                _e("PLT002-L3-LBL", "LABELER",   350, 0.8, 2),
                _e("PLT002-L3-CNV", "CONVEYOR",  1000, 1.0, 3),
                _e("PLT002-L3-PKG", "PACKAGING", 300, 1.5, 4),
            ]),
        ],
    ),
    # ── PLT-003  Dairy (Nido-style) ── 3 lines, 14 equipment
    PlantSeed(
        id="PLT-003", name="NexDairy-North", location="Northern Region",
        category="DAIRY", capacity_tons_per_day=550.0,
        lat=44.98, lon=-93.27, starting_oee=0.48, target_oee=0.72,
        oee_benchmark_world_class=(0.75, 0.82),
        lines=[
            LineSeed("PLT-003-L1", "UHT_FILLING", 300.0, "PLT003-L1-PST", [
                _e("PLT003-L1-PST", "PASTEURIZER",  350, 4.0, 1),
                _e("PLT003-L1-HMG", "HOMOGENIZER",  400, 3.5, 2),
                _e("PLT003-L1-FIL", "FILLER",       150, 2.5, 3),
                _e("PLT003-L1-CAP", "CAPPER",       250, 1.0, 4),
                _e("PLT003-L1-CNV", "CONVEYOR",     1200, 0.5, 5),
            ]),
            LineSeed("PLT-003-L2", "POWDER_PACKING", 350.0, "PLT003-L2-PST", [
                _e("PLT003-L2-PST", "PASTEURIZER",  380, 4.5, 1),
                _e("PLT003-L2-HMG", "HOMOGENIZER",  420, 3.0, 2),
                _e("PLT003-L2-FIL", "FILLER",       160, 2.0, 3),
                _e("PLT003-L2-CAP", "CAPPER",       280, 1.5, 4),
                _e("PLT003-L2-PKG", "PACKAGING",    300, 2.0, 5),
            ]),
            LineSeed("PLT-003-L3", "ASEPTIC", 250.0, "PLT003-L3-FIL", [
                _e("PLT003-L3-FIL", "FILLER",   120, 4.0, 1),
                _e("PLT003-L3-CAP", "CAPPER",   200, 2.0, 2),
                _e("PLT003-L3-LBL", "LABELER",  300, 1.5, 3),
                _e("PLT003-L3-CNV", "CONVEYOR", 1500, 0.7, 4),
            ]),
        ],
    ),
    # ── PLT-004  Pet Food (Purina-style) ── 4 lines, 16 equipment
    PlantSeed(
        id="PLT-004", name="NexPet-South", location="Southern Region",
        category="PET_FOOD", capacity_tons_per_day=420.0,
        lat=33.75, lon=-84.39, starting_oee=0.60, target_oee=0.78,
        oee_benchmark_world_class=(0.76, 0.84),
        lines=[
            LineSeed("PLT-004-L1", "EXTRUSION", 500.0, "PLT004-L1-DRY", [
                _e("PLT004-L1-MXR", "MIXER",     450, 3.0, 1),
                _e("PLT004-L1-DRY", "DRYER",     380, 5.0, 2),
                _e("PLT004-L1-FIL", "FILLER",    170, 2.0, 3),
                _e("PLT004-L1-PKG", "PACKAGING", 350, 1.8, 4),
            ]),
            LineSeed("PLT-004-L2", "EXTRUSION", 450.0, "PLT004-L2-DRY", [
                _e("PLT004-L2-MXR", "MIXER",     420, 3.5, 1),
                _e("PLT004-L2-DRY", "DRYER",     400, 4.0, 2),
                _e("PLT004-L2-FIL", "FILLER",    190, 1.5, 3),
                _e("PLT004-L2-PKG", "PACKAGING", 320, 2.0, 4),
            ]),
            LineSeed("PLT-004-L3", "RETORT_CANNING", 300.0, "PLT004-L3-FIL", [
                _e("PLT004-L3-FIL", "FILLER",   140, 3.0, 1),
                _e("PLT004-L3-CAP", "CAPPER",   280, 1.0, 2),
                _e("PLT004-L3-LBL", "LABELER",  450, 0.5, 3),
                _e("PLT004-L3-CNV", "CONVEYOR", 1800, 0.5, 4),
            ]),
            LineSeed("PLT-004-L4", "KIBBLE_COATING", 400.0, "PLT004-L4-MXR", [
                _e("PLT004-L4-MXR", "MIXER",     500, 2.5, 1),
                _e("PLT004-L4-FIL", "FILLER",    200, 1.0, 2),
                _e("PLT004-L4-CNV", "CONVEYOR",  2000, 0.5, 3),
                _e("PLT004-L4-PKG", "PACKAGING", 400, 1.5, 4),
            ], upstream_lines=["PLT-004-L1", "PLT-004-L2"]),
        ],
    ),
    # ── PLT-005  Prepared Foods (Maggi-style) ── 3 lines, 12 equipment
    PlantSeed(
        id="PLT-005", name="NexPrepared-West", location="Western Region",
        category="PREPARED_FOODS", capacity_tons_per_day=220.0,
        lat=34.05, lon=-118.24, starting_oee=0.52, target_oee=0.72,
        oee_benchmark_world_class=(0.71, 0.80),
        lines=[
            LineSeed("PLT-005-L1", "MIXING_COOKING", 250.0, "PLT005-L1-MXR", [
                _e("PLT005-L1-MXR", "MIXER",     350, 4.0, 1),
                _e("PLT005-L1-FIL", "FILLER",    140, 3.0, 2),
                _e("PLT005-L1-CAP", "CAPPER",    260, 1.2, 3),
                _e("PLT005-L1-PKG", "PACKAGING", 200, 2.5, 4),
            ]),
            LineSeed("PLT-005-L2", "FILLING", 300.0, "PLT005-L2-FIL", [
                _e("PLT005-L2-FIL", "FILLER",    160, 2.5, 1),
                _e("PLT005-L2-LBL", "LABELER",   380, 1.0, 2),
                _e("PLT005-L2-CNV", "CONVEYOR",  1100, 0.8, 3),
                _e("PLT005-L2-PKG", "PACKAGING", 250, 2.0, 4),
            ]),
            LineSeed("PLT-005-L3", "NOODLE_LINE", 280.0, "PLT005-L3-FIL", [
                _e("PLT005-L3-MXR", "MIXER",     400, 3.0, 1),
                _e("PLT005-L3-FIL", "FILLER",    130, 3.5, 2),
                _e("PLT005-L3-CAP", "CAPPER",    240, 1.5, 3),
                _e("PLT005-L3-PKG", "PACKAGING", 220, 2.5, 4),
            ]),
        ],
    ),
]
# fmt: on


# CIP schedule per line type — docs/research/production-operations.md §1.3
CIP_SCHEDULES: dict[str, dict] = {
    "PET_BOTTLING":    {"frequency_hours": 24,  "duration_min": (45, 60),   "trigger": "time"},
    "GLASS_BOTTLING":  {"frequency_hours": 24,  "duration_min": (60, 90),   "trigger": "time"},
    "CANNING":         {"frequency_hours": 24,  "duration_min": (45, 60),   "trigger": "time"},
    "UHT_FILLING":     {"frequency_hours": 10,  "duration_min": (90, 120),  "trigger": "hard_limit_12h"},
    "ASEPTIC":         {"frequency_hours": 8,   "duration_min": (90, 150),  "trigger": "fda_fsma"},
    "POWDER_PACKING":  {"frequency_hours": 48,  "duration_min": (60, 90),   "trigger": "time"},
    "MOULDING":        {"frequency_hours": 24,  "duration_min": (60, 90),   "trigger": "time"},
    "ENROBING":        {"frequency_hours": 24,  "duration_min": (60, 90),   "trigger": "time"},
    "WRAPPING":        {"frequency_hours": 48,  "duration_min": (30, 45),   "trigger": "time"},
    "EXTRUSION":       {"frequency_hours": 24,  "duration_min": (90, 120),  "trigger": "time"},
    "RETORT_CANNING":  {"frequency_hours": 168, "duration_min": (240, 360), "trigger": "weekly_deep"},
    "KIBBLE_COATING":  {"frequency_hours": 24,  "duration_min": (60, 90),   "trigger": "time"},
    "MIXING_COOKING":  {"frequency_hours": 8,   "duration_min": (45, 60),   "trigger": "allergen"},
    "FILLING":         {"frequency_hours": 12,  "duration_min": (30, 45),   "trigger": "time"},
    "NOODLE_LINE":     {"frequency_hours": 24,  "duration_min": (60, 75),   "trigger": "time"},
}

# Weekly planned downtime budget (hours) per plant
WEEKLY_PLANNED_DOWNTIME: dict[str, float] = {
    "PLT-001": 19.0,
    "PLT-002": 29.0,
    "PLT-003": 39.0,
    "PLT-004": 31.0,
    "PLT-005": 27.0,
}


def get_all_plants() -> list[PlantSeed]:
    return PLANTS


def get_plant(plant_id: str) -> PlantSeed | None:
    return next((p for p in PLANTS if p.id == plant_id), None)


# ── DB seeding ──


async def seed_plants(session) -> None:
    from sqlalchemy import select

    from nexusfab.models.enums import EquipmentType, PlantCategory
    from nexusfab.models.plant import Equipment, Plant, ProductionLine

    exists = await session.execute(select(Plant).limit(1))
    if exists.scalar_one_or_none():
        return

    for ps in PLANTS:
        plant = Plant(
            id=seed_uuid(ps.id),
            name=ps.name,
            location=ps.location,
            category=PlantCategory(ps.category.lower()),
            capacity_tons_per_day=ps.capacity_tons_per_day,
            status="active",
            lat=ps.lat,
            lon=ps.lon,
        )
        session.add(plant)
        for ls in ps.lines:
            line = ProductionLine(
                id=seed_uuid(ls.name),
                plant_id=plant.id,
                name=ls.name,
                line_type=ls.line_type,
                speed_units_per_min=ls.rated_speed_per_min,
            )
            session.add(line)
            for eq in ls.equipment:
                session.add(Equipment(
                    id=seed_uuid(eq.name),
                    line_id=line.id,
                    name=eq.name,
                    equipment_type=EquipmentType(eq.equipment_type.lower()),
                    mtbf_hours=eq.mtbf_hours,
                    mttr_hours=eq.mttr_hours,
                    position_in_line=eq.position,
                ))

    await session.commit()


if __name__ == "__main__":
    for plant in PLANTS:
        print(f"\n=== {plant.id} {plant.name} ===")
        for line in plant.lines:
            for eq in line.equipment:
                print(f"  {eq.name:20s} {eq.equipment_type:14s} "
                      f"β={eq.weibull_beta:.1f}  η={eq.weibull_eta:5.0f}h  "
                      f"MTBF={eq.mtbf_hours:.0f}h  MTTR={eq.mttr_hours:.1f}h")
    all_types = {eq.equipment_type for p in PLANTS for l in p.lines for eq in l.equipment}
    missing = all_types - set(WEIBULL_BY_TYPE)
    assert not missing, f"Missing Weibull params for: {missing}"
    n = sum(len(l.equipment) for p in PLANTS for l in p.lines)
    print(f"\nPASS — {n} equipment across {len(PLANTS)} plants, all types have Weibull β/η")
