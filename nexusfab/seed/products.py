"""Product catalog + changeover matrix seed data."""

from dataclasses import dataclass, field

@dataclass
class ProductSeed:
    sku: str
    name: str
    category: str
    plant_id: str
    units_per_batch: int
    changeover_minutes: float
    allergens: list[str] = field(default_factory=list)
    format_type: str = ""

PRODUCTS: list[ProductSeed] = [
    # PLT-001: Water/Beverages
    ProductSeed("WAT-500S", "Pure Spring 500ml Still", "WATER", "PLT-001", 12000, 20.0, [], "PET_500"),
    ProductSeed("WAT-500P", "Pure Spring 500ml Sparkling", "WATER", "PLT-001", 12000, 25.0, [], "PET_500"),
    ProductSeed("WAT-750S", "Pure Spring 750ml Still", "WATER", "PLT-001", 8000, 20.0, [], "PET_750"),
    ProductSeed("WAT-1LS", "Pure Spring 1L Still", "WATER", "PLT-001", 6000, 30.0, [], "PET_1L"),
    ProductSeed("WAT-15S", "Pure Spring 1.5L Still", "WATER", "PLT-001", 5000, 35.0, [], "PET_15L"),
    ProductSeed("WAT-15P", "Pure Spring 1.5L Sparkling", "WATER", "PLT-001", 5000, 35.0, [], "PET_15L"),
    ProductSeed("BEV-CAN", "NexTea Iced Tea 330ml Can", "WATER", "PLT-001", 15000, 45.0, [], "CAN_330"),
    ProductSeed("BEV-TP", "NexMilk Chocolate 200ml Tetra", "WATER", "PLT-001", 10000, 60.0, ["DAIRY"], "TETRA_200"),

    # PLT-002: Confectionery
    ProductSeed("CON-KB4", "NexBar Original 4-finger", "CONFECTIONERY", "PLT-002", 5000, 30.0, ["GLUTEN", "DAIRY"], "BAR_4F"),
    ProductSeed("CON-KB2", "NexBar Original 2-finger", "CONFECTIONERY", "PLT-002", 8000, 25.0, ["GLUTEN", "DAIRY"], "BAR_2F"),
    ProductSeed("CON-KBD", "NexBar Dark Chocolate", "CONFECTIONERY", "PLT-002", 5000, 35.0, ["GLUTEN", "DAIRY"], "BAR_4F"),
    ProductSeed("CON-KBW", "NexBar White Chocolate", "CONFECTIONERY", "PLT-002", 5000, 40.0, ["GLUTEN", "DAIRY"], "BAR_4F"),
    ProductSeed("CON-SMT", "NexSmarts Tube", "CONFECTIONERY", "PLT-002", 6000, 45.0, ["DAIRY"], "TUBE"),
    ProductSeed("CON-MP8", "NexBar Multi-Pack 8ct", "CONFECTIONERY", "PLT-002", 3000, 50.0, ["GLUTEN", "DAIRY"], "MULTIPACK"),
    ProductSeed("CON-AER", "NexAero Mint", "CONFECTIONERY", "PLT-002", 4000, 35.0, ["DAIRY"], "BAR_STD"),
    ProductSeed("CON-QST", "Quality Selection Box", "CONFECTIONERY", "PLT-002", 2000, 90.0, ["GLUTEN", "DAIRY", "NUTS"], "SEASONAL"),
    ProductSeed("CON-NUT", "NexBar Peanut", "CONFECTIONERY", "PLT-002", 4000, 45.0, ["GLUTEN", "DAIRY", "NUTS"], "BAR_4F"),
    ProductSeed("CON-CAR", "NexBar Caramel", "CONFECTIONERY", "PLT-002", 4500, 40.0, ["GLUTEN", "DAIRY"], "BAR_4F"),
    ProductSeed("CON-HLW", "Halloween Shapes", "CONFECTIONERY", "PLT-002", 3000, 120.0, ["GLUTEN", "DAIRY"], "SEASONAL"),
    ProductSeed("CON-XMS", "Christmas Selection", "CONFECTIONERY", "PLT-002", 2500, 120.0, ["GLUTEN", "DAIRY", "NUTS"], "SEASONAL"),

    # PLT-003: Dairy
    ProductSeed("DAI-P4", "NexMilk Powder 400g", "DAIRY", "PLT-003", 4000, 40.0, ["DAIRY"], "TIN_400"),
    ProductSeed("DAI-P9", "NexMilk Powder 900g", "DAIRY", "PLT-003", 3000, 40.0, ["DAIRY"], "TIN_900"),
    ProductSeed("DAI-P18", "NexMilk Powder 1.8kg", "DAIRY", "PLT-003", 2000, 45.0, ["DAIRY"], "TIN_1800"),
    ProductSeed("DAI-L2", "NexMilk UHT 200ml", "DAIRY", "PLT-003", 10000, 30.0, ["DAIRY"], "UHT_200"),
    ProductSeed("DAI-L5", "NexMilk UHT 500ml", "DAIRY", "PLT-003", 7000, 30.0, ["DAIRY"], "UHT_500"),
    ProductSeed("DAI-L1", "NexMilk UHT 1L", "DAIRY", "PLT-003", 5000, 35.0, ["DAIRY"], "UHT_1L"),

    # PLT-004: Pet Food
    ProductSeed("PET-D1", "NexPet Dry Dog 1kg", "PET_FOOD", "PLT-004", 6000, 25.0, [], "BAG_1K"),
    ProductSeed("PET-D5", "NexPet Dry Dog 5kg", "PET_FOOD", "PLT-004", 3000, 30.0, [], "BAG_5K"),
    ProductSeed("PET-D15", "NexPet Dry Dog 15kg", "PET_FOOD", "PLT-004", 1500, 35.0, [], "BAG_15K"),
    ProductSeed("PET-WC85", "NexPet Wet Cat 85g", "PET_FOOD", "PLT-004", 20000, 20.0, [], "CAN_85"),
    ProductSeed("PET-WC4", "NexPet Wet Cat 400g", "PET_FOOD", "PLT-004", 10000, 25.0, [], "CAN_400"),
    ProductSeed("PET-WD4", "NexPet Wet Dog 400g", "PET_FOOD", "PLT-004", 10000, 25.0, [], "CAN_400"),
    ProductSeed("PET-TR", "NexPet Treats Pouch", "PET_FOOD", "PLT-004", 8000, 30.0, [], "POUCH"),
    ProductSeed("PET-DC1", "NexPet Dry Cat 1kg", "PET_FOOD", "PLT-004", 6000, 25.0, [], "BAG_1K"),

    # PLT-005: Prepared Foods
    ProductSeed("PRE-N70", "NexNoodle Instant 70g", "PREPARED_FOODS", "PLT-005", 15000, 20.0, ["GLUTEN", "SOY"], "PACK_70"),
    ProductSeed("PRE-N5P", "NexNoodle 5-Pack", "PREPARED_FOODS", "PLT-005", 5000, 35.0, ["GLUTEN", "SOY"], "MULTIPACK"),
    ProductSeed("PRE-S8", "NexSeason All-Purpose 8g", "PREPARED_FOODS", "PLT-005", 30000, 15.0, [], "SACHET_8"),
    ProductSeed("PRE-SC2", "NexSauce Soy 200ml", "PREPARED_FOODS", "PLT-005", 8000, 30.0, ["SOY", "GLUTEN"], "BOTTLE_200"),
    ProductSeed("PRE-SC5", "NexSauce Chili 500ml", "PREPARED_FOODS", "PLT-005", 5000, 35.0, [], "BOTTLE_500"),
    ProductSeed("PRE-CUP", "NexNoodle Cup 65g", "PREPARED_FOODS", "PLT-005", 12000, 25.0, ["GLUTEN", "SOY"], "CUP_65"),
]

# Changeover times (minutes) between format types
# ponytail: flat dict, key = (from_format, to_format). Missing = default 60 min
CHANGEOVER_MATRIX: dict[tuple[str, str], float] = {}

def _same_format_changeovers():
    """Same format = 15-30 min, different format same plant = 30-60 min."""
    formats = {p.format_type for p in PRODUCTS}
    for f1 in formats:
        for f2 in formats:
            if f1 == f2:
                CHANGEOVER_MATRIX[(f1, f2)] = 20.0
            else:
                CHANGEOVER_MATRIX[(f1, f2)] = 45.0

_same_format_changeovers()

def get_changeover_time(from_format: str, to_format: str, has_allergen_transition: bool = False) -> float:
    base = CHANGEOVER_MATRIX.get((from_format, to_format), 60.0)
    if has_allergen_transition:
        base += 90.0  # CIP for allergen transition
    return base

def get_products_for_plant(plant_id: str) -> list[ProductSeed]:
    return [p for p in PRODUCTS if p.plant_id == plant_id]

def get_product(sku: str) -> ProductSeed | None:
    return next((p for p in PRODUCTS if p.sku == sku), None)
