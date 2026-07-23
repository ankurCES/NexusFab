"""Nestlé 5-plant network seed data."""

from dataclasses import dataclass, field

@dataclass
class EquipmentSeed:
    name: str
    equipment_type: str
    mtbf_hours: float
    mttr_hours: float
    position: int

@dataclass
class LineSeed:
    name: str
    line_type: str
    speed_units_per_min: float
    equipment: list[EquipmentSeed] = field(default_factory=list)

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

def _equip(name: str, etype: str, mtbf: float, mttr: float, pos: int) -> EquipmentSeed:
    return EquipmentSeed(name, etype, mtbf, mttr, pos)

def _bottling_equipment(prefix: str) -> list[EquipmentSeed]:
    return [
        _equip(f"{prefix}-MXR", "MIXER", 450.0, 3.5, 1),
        _equip(f"{prefix}-FIL", "FILLER", 160.0, 2.5, 2),
        _equip(f"{prefix}-CAP", "CAPPER", 280.0, 1.0, 3),
        _equip(f"{prefix}-LBL", "LABELER", 200.0, 1.0, 4),
        _equip(f"{prefix}-CNV", "CONVEYOR", 750.0, 1.0, 5),
        _equip(f"{prefix}-PKG", "PACKAGING", 140.0, 2.0, 6),
    ]

def _confec_equipment(prefix: str) -> list[EquipmentSeed]:
    return [
        _equip(f"{prefix}-MXR", "MIXER", 400.0, 4.0, 1),
        _equip(f"{prefix}-FIL", "FILLER", 130.0, 3.0, 2),
        _equip(f"{prefix}-CAP", "CAPPER", 300.0, 1.5, 3),
        _equip(f"{prefix}-LBL", "LABELER", 180.0, 1.0, 4),
        _equip(f"{prefix}-CNV", "CONVEYOR", 600.0, 1.0, 5),
        _equip(f"{prefix}-PKG", "PACKAGING", 120.0, 2.5, 6),
    ]

def _dairy_equipment(prefix: str) -> list[EquipmentSeed]:
    return [
        _equip(f"{prefix}-PST", "PASTEURIZER", 350.0, 4.0, 1),
        _equip(f"{prefix}-HMG", "HOMOGENIZER", 400.0, 3.5, 2),
        _equip(f"{prefix}-FIL", "FILLER", 150.0, 2.5, 3),
        _equip(f"{prefix}-CAP", "CAPPER", 250.0, 1.0, 4),
        _equip(f"{prefix}-CNV", "CONVEYOR", 700.0, 1.0, 5),
        _equip(f"{prefix}-PKG", "PACKAGING", 130.0, 2.0, 6),
    ]

def _petfood_equipment(prefix: str) -> list[EquipmentSeed]:
    return [
        _equip(f"{prefix}-MXR", "MIXER", 500.0, 3.0, 1),
        _equip(f"{prefix}-DRY", "DRYER", 380.0, 5.0, 2),
        _equip(f"{prefix}-FIL", "FILLER", 170.0, 2.0, 3),
        _equip(f"{prefix}-CAP", "CAPPER", 320.0, 1.0, 4),
        _equip(f"{prefix}-CNV", "CONVEYOR", 800.0, 0.8, 5),
        _equip(f"{prefix}-PKG", "PACKAGING", 150.0, 1.8, 6),
    ]

def _prepared_equipment(prefix: str) -> list[EquipmentSeed]:
    return [
        _equip(f"{prefix}-MXR", "MIXER", 350.0, 4.0, 1),
        _equip(f"{prefix}-FIL", "FILLER", 140.0, 3.0, 2),
        _equip(f"{prefix}-CAP", "CAPPER", 260.0, 1.2, 3),
        _equip(f"{prefix}-LBL", "LABELER", 190.0, 1.0, 4),
        _equip(f"{prefix}-CNV", "CONVEYOR", 650.0, 1.0, 5),
        _equip(f"{prefix}-PKG", "PACKAGING", 110.0, 2.5, 6),
    ]

PLANTS: list[PlantSeed] = [
    PlantSeed(
        id="PLT-001", name="NexWater-East", location="Eastern Region",
        category="WATER", capacity_tons_per_day=1400.0,
        lat=40.71, lon=-74.01, starting_oee=0.62, target_oee=0.80,
        lines=[
            LineSeed("PLT-001-L1", "PET_BOTTLING", 600.0, _bottling_equipment("PLT001-L1")),
            LineSeed("PLT-001-L2", "PET_BOTTLING", 500.0, _bottling_equipment("PLT001-L2")),
            LineSeed("PLT-001-L3", "PET_BOTTLING", 800.0, _bottling_equipment("PLT001-L3")),
            LineSeed("PLT-001-L4", "GLASS_BOTTLING", 400.0, _bottling_equipment("PLT001-L4")),
            LineSeed("PLT-001-L5", "PET_BOTTLING", 600.0, _bottling_equipment("PLT001-L5")),
            LineSeed("PLT-001-L6", "PET_BOTTLING", 500.0, _bottling_equipment("PLT001-L6")),
            LineSeed("PLT-001-L7", "CANNING", 700.0, _bottling_equipment("PLT001-L7")),
            LineSeed("PLT-001-L8", "TETRA_PAK", 350.0, _bottling_equipment("PLT001-L8")),
        ],
    ),
    PlantSeed(
        id="PLT-002", name="NexConfec-Central", location="Central Region",
        category="CONFECTIONERY", capacity_tons_per_day=140.0,
        lat=41.88, lon=-87.63, starting_oee=0.55, target_oee=0.78,
        lines=[
            LineSeed("PLT-002-L1", "MOULDING", 400.0, _confec_equipment("PLT002-L1")),
            LineSeed("PLT-002-L2", "MOULDING", 350.0, _confec_equipment("PLT002-L2")),
            LineSeed("PLT-002-L3", "ENROBING", 300.0, _confec_equipment("PLT002-L3")),
            LineSeed("PLT-002-L4", "ENROBING", 280.0, _confec_equipment("PLT002-L4")),
            LineSeed("PLT-002-L5", "WRAPPING", 500.0, _confec_equipment("PLT002-L5")),
            LineSeed("PLT-002-L6", "WRAPPING", 450.0, _confec_equipment("PLT002-L6")),
            LineSeed("PLT-002-L7", "MOULDING", 380.0, _confec_equipment("PLT002-L7")),
            LineSeed("PLT-002-L8", "ENROBING", 320.0, _confec_equipment("PLT002-L8")),
            LineSeed("PLT-002-L9", "WRAPPING", 480.0, _confec_equipment("PLT002-L9")),
            LineSeed("PLT-002-L10", "PACKAGING", 600.0, _confec_equipment("PLT002-L10")),
            LineSeed("PLT-002-L11", "MOULDING", 400.0, _confec_equipment("PLT002-L11")),
            LineSeed("PLT-002-L12", "SEASONAL", 250.0, _confec_equipment("PLT002-L12")),
        ],
    ),
    PlantSeed(
        id="PLT-003", name="NexDairy-North", location="Northern Region",
        category="DAIRY", capacity_tons_per_day=550.0,
        lat=44.98, lon=-93.27, starting_oee=0.48, target_oee=0.72,
        lines=[
            LineSeed("PLT-003-L1", "UHT_FILLING", 300.0, _dairy_equipment("PLT003-L1")),
            LineSeed("PLT-003-L2", "UHT_FILLING", 280.0, _dairy_equipment("PLT003-L2")),
            LineSeed("PLT-003-L3", "ASEPTIC", 250.0, _dairy_equipment("PLT003-L3")),
            LineSeed("PLT-003-L4", "FROZEN_FILLING", 200.0, _dairy_equipment("PLT003-L4")),
            LineSeed("PLT-003-L5", "POWDER_PACKING", 350.0, _dairy_equipment("PLT003-L5")),
            LineSeed("PLT-003-L6", "POWDER_PACKING", 320.0, _dairy_equipment("PLT003-L6")),
        ],
    ),
    PlantSeed(
        id="PLT-004", name="NexPet-South", location="Southern Region",
        category="PET_FOOD", capacity_tons_per_day=420.0,
        lat=33.75, lon=-84.39, starting_oee=0.60, target_oee=0.78,
        lines=[
            LineSeed("PLT-004-L1", "EXTRUSION", 500.0, _petfood_equipment("PLT004-L1")),
            LineSeed("PLT-004-L2", "EXTRUSION", 450.0, _petfood_equipment("PLT004-L2")),
            LineSeed("PLT-004-L3", "RETORT_CANNING", 300.0, _petfood_equipment("PLT004-L3")),
            LineSeed("PLT-004-L4", "RETORT_CANNING", 280.0, _petfood_equipment("PLT004-L4")),
            LineSeed("PLT-004-L5", "KIBBLE_COATING", 400.0, _petfood_equipment("PLT004-L5")),
            LineSeed("PLT-004-L6", "PACKAGING", 550.0, _petfood_equipment("PLT004-L6")),
            LineSeed("PLT-004-L7", "EXTRUSION", 480.0, _petfood_equipment("PLT004-L7")),
            LineSeed("PLT-004-L8", "RETORT_CANNING", 320.0, _petfood_equipment("PLT004-L8")),
            LineSeed("PLT-004-L9", "TREATS", 250.0, _petfood_equipment("PLT004-L9")),
            LineSeed("PLT-004-L10", "PACKAGING", 500.0, _petfood_equipment("PLT004-L10")),
        ],
    ),
    PlantSeed(
        id="PLT-005", name="NexPrepared-West", location="Western Region",
        category="PREPARED_FOODS", capacity_tons_per_day=220.0,
        lat=34.05, lon=-118.24, starting_oee=0.52, target_oee=0.72,
        lines=[
            LineSeed("PLT-005-L1", "MIXING_COOKING", 250.0, _prepared_equipment("PLT005-L1")),
            LineSeed("PLT-005-L2", "MIXING_COOKING", 230.0, _prepared_equipment("PLT005-L2")),
            LineSeed("PLT-005-L3", "FILLING", 300.0, _prepared_equipment("PLT005-L3")),
            LineSeed("PLT-005-L4", "FILLING", 280.0, _prepared_equipment("PLT005-L4")),
            LineSeed("PLT-005-L5", "FREEZING", 200.0, _prepared_equipment("PLT005-L5")),
            LineSeed("PLT-005-L6", "PACKAGING", 400.0, _prepared_equipment("PLT005-L6")),
            LineSeed("PLT-005-L7", "SEASONING", 350.0, _prepared_equipment("PLT005-L7")),
            LineSeed("PLT-005-L8", "NOODLE_LINE", 300.0, _prepared_equipment("PLT005-L8")),
        ],
    ),
]

def get_all_plants() -> list[PlantSeed]:
    return PLANTS

def get_plant(plant_id: str) -> PlantSeed | None:
    return next((p for p in PLANTS if p.id == plant_id), None)
