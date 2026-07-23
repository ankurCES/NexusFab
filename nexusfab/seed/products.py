"""Product catalog + changeover matrix seed data."""

from dataclasses import dataclass, field

from nexusfab.seed.plants import seed_uuid


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


# fmt: off
PRODUCTS: list[ProductSeed] = [
    # ── PLT-001: Water/Beverages — 6 SKUs ──
    ProductSeed("WAT-500S", "Pure Spring 500ml Still",      "WATER", "PLT-001", 12000, 20.0, [],               "PET_500"),
    ProductSeed("WAT-500P", "Pure Spring 500ml Sparkling",  "WATER", "PLT-001", 12000, 25.0, [],               "PET_500"),
    ProductSeed("WAT-750S", "Pure Spring 750ml Still",      "WATER", "PLT-001",  8000, 20.0, [],               "PET_750"),
    ProductSeed("WAT-1LS",  "Pure Spring 1L Still",         "WATER", "PLT-001",  6000, 30.0, [],               "PET_1L"),
    ProductSeed("WAT-15S",  "Pure Spring 1.5L Still",       "WATER", "PLT-001",  5000, 35.0, [],               "PET_15L"),
    ProductSeed("WAT-15P",  "Pure Spring 1.5L Sparkling",   "WATER", "PLT-001",  5000, 35.0, [],               "PET_15L"),

    # ── PLT-002: Confectionery — 8 SKUs ──
    ProductSeed("CON-KB4", "NexBar Original 4-finger",  "CONFECTIONERY", "PLT-002", 5000, 30.0, ["GLUTEN", "DAIRY"],           "BAR_4F"),
    ProductSeed("CON-KBD", "NexBar Dark Chocolate",     "CONFECTIONERY", "PLT-002", 5000, 35.0, ["GLUTEN", "DAIRY"],           "BAR_4F"),
    ProductSeed("CON-KBW", "NexBar White Chocolate",    "CONFECTIONERY", "PLT-002", 5000, 40.0, ["GLUTEN", "DAIRY"],           "BAR_4F"),
    ProductSeed("CON-NUT", "NexBar Peanut",             "CONFECTIONERY", "PLT-002", 4000, 45.0, ["GLUTEN", "DAIRY", "NUTS"],   "BAR_4F"),
    ProductSeed("CON-AER", "NexAero Mint",              "CONFECTIONERY", "PLT-002", 4000, 35.0, ["DAIRY"],                     "BAR_STD"),
    ProductSeed("CON-MP8", "NexBar Multi-Pack 8ct",     "CONFECTIONERY", "PLT-002", 3000, 50.0, ["GLUTEN", "DAIRY"],           "MULTIPACK"),
    ProductSeed("CON-QST", "Quality Selection Box",     "CONFECTIONERY", "PLT-002", 2000, 90.0, ["GLUTEN", "DAIRY", "NUTS"],   "SEASONAL"),
    ProductSeed("CON-XMS", "Christmas Selection",       "CONFECTIONERY", "PLT-002", 2500, 120.0, ["GLUTEN", "DAIRY", "NUTS"],  "SEASONAL"),

    # ── PLT-003: Dairy — 6 SKUs ──
    ProductSeed("DAI-P4",  "NexMilk Powder 400g",  "DAIRY", "PLT-003",  4000, 40.0, ["DAIRY"], "TIN_400"),
    ProductSeed("DAI-P9",  "NexMilk Powder 900g",  "DAIRY", "PLT-003",  3000, 40.0, ["DAIRY"], "TIN_900"),
    ProductSeed("DAI-P18", "NexMilk Powder 1.8kg", "DAIRY", "PLT-003",  2000, 45.0, ["DAIRY"], "TIN_1800"),
    ProductSeed("DAI-L2",  "NexMilk UHT 200ml",   "DAIRY", "PLT-003", 10000, 30.0, ["DAIRY"], "UHT_200"),
    ProductSeed("DAI-L5",  "NexMilk UHT 500ml",   "DAIRY", "PLT-003",  7000, 30.0, ["DAIRY"], "UHT_500"),
    ProductSeed("DAI-L1",  "NexMilk UHT 1L",      "DAIRY", "PLT-003",  5000, 35.0, ["DAIRY"], "UHT_1L"),

    # ── PLT-004: Pet Food — 8 SKUs ──
    ProductSeed("PET-D1",   "NexPet Dry Dog 1kg",   "PET_FOOD", "PLT-004",  6000, 25.0, [], "BAG_1K"),
    ProductSeed("PET-D5",   "NexPet Dry Dog 5kg",   "PET_FOOD", "PLT-004",  3000, 30.0, [], "BAG_5K"),
    ProductSeed("PET-D15",  "NexPet Dry Dog 15kg",  "PET_FOOD", "PLT-004",  1500, 35.0, [], "BAG_15K"),
    ProductSeed("PET-WC85", "NexPet Wet Cat 85g",   "PET_FOOD", "PLT-004", 20000, 20.0, [], "CAN_85"),
    ProductSeed("PET-WC4",  "NexPet Wet Cat 400g",  "PET_FOOD", "PLT-004", 10000, 25.0, [], "CAN_400"),
    ProductSeed("PET-WD4",  "NexPet Wet Dog 400g",  "PET_FOOD", "PLT-004", 10000, 25.0, [], "CAN_400"),
    ProductSeed("PET-TR",   "NexPet Treats Pouch",  "PET_FOOD", "PLT-004",  8000, 30.0, [], "POUCH"),
    ProductSeed("PET-DC1",  "NexPet Dry Cat 1kg",   "PET_FOOD", "PLT-004",  6000, 25.0, [], "BAG_1K"),

    # ── PLT-005: Prepared Foods — 6 SKUs ──
    ProductSeed("PRE-N70", "NexNoodle Instant 70g",     "PREPARED_FOODS", "PLT-005", 15000, 20.0, ["GLUTEN", "SOY"],  "PACK_70"),
    ProductSeed("PRE-N5P", "NexNoodle 5-Pack",          "PREPARED_FOODS", "PLT-005",  5000, 35.0, ["GLUTEN", "SOY"],  "MULTIPACK"),
    ProductSeed("PRE-S8",  "NexSeason All-Purpose 8g",  "PREPARED_FOODS", "PLT-005", 30000, 15.0, [],                 "SACHET_8"),
    ProductSeed("PRE-SC2", "NexSauce Soy 200ml",        "PREPARED_FOODS", "PLT-005",  8000, 30.0, ["SOY", "GLUTEN"],  "BOTTLE_200"),
    ProductSeed("PRE-SC5", "NexSauce Chili 500ml",      "PREPARED_FOODS", "PLT-005",  5000, 35.0, [],                 "BOTTLE_500"),
    ProductSeed("PRE-CUP", "NexNoodle Cup 65g",         "PREPARED_FOODS", "PLT-005", 12000, 25.0, ["GLUTEN", "SOY"],  "CUP_65"),
]
# fmt: on


# ── Changeover matrix ──
# ponytail: flat dict keyed by (from_format, to_format), computed once at import.
# Three tiers per spec: same format 15-30, different format 30-60, allergen transition 60-120 + CIP.

CHANGEOVER_MATRIX: dict[tuple[str, str], float] = {}

_FORMAT_CATEGORIES = {}
for _p in PRODUCTS:
    _FORMAT_CATEGORIES[_p.format_type] = _p.category


def _build_changeover_matrix():
    formats = {p.format_type for p in PRODUCTS}
    for f1 in sorted(formats):
        for f2 in sorted(formats):
            if f1 == f2:
                CHANGEOVER_MATRIX[(f1, f2)] = 20.0  # same format: 15-30
            elif _FORMAT_CATEGORIES.get(f1) == _FORMAT_CATEGORIES.get(f2):
                CHANGEOVER_MATRIX[(f1, f2)] = 45.0  # different format, same category: 30-60
            else:
                CHANGEOVER_MATRIX[(f1, f2)] = 60.0  # cross-category baseline


_build_changeover_matrix()


def get_changeover_time(from_sku: str, to_sku: str) -> float:
    """Changeover minutes between two SKUs, including CIP for allergen transitions."""
    p1 = get_product(from_sku)
    p2 = get_product(to_sku)
    if not p1 or not p2:
        return 60.0
    base = CHANGEOVER_MATRIX.get((p1.format_type, p2.format_type), 60.0)
    # allergen transition: new allergens introduced → CIP required
    if p2.allergens and set(p2.allergens) - set(p1.allergens):
        base = max(base, 60.0) + 60.0  # 60-120 min + CIP
    return base


def get_products_for_plant(plant_id: str) -> list[ProductSeed]:
    return [p for p in PRODUCTS if p.plant_id == plant_id]


def get_product(sku: str) -> ProductSeed | None:
    return next((p for p in PRODUCTS if p.sku == sku), None)


# ── DB seeding ──


async def seed_products(session) -> None:
    from sqlalchemy import select

    from nexusfab.models.product import Product

    exists = await session.execute(select(Product).limit(1))
    if exists.scalar_one_or_none():
        return

    for ps in PRODUCTS:
        session.add(Product(
            id=seed_uuid(ps.sku),
            sku=ps.sku,
            name=ps.name,
            category=ps.category,
            plant_id=seed_uuid(ps.plant_id),
            units_per_batch=ps.units_per_batch,
            changeover_minutes=ps.changeover_minutes,
            allergens=ps.allergens or None,
        ))

    await session.commit()


if __name__ == "__main__":
    # self-check
    by_plant = {}
    for p in PRODUCTS:
        by_plant.setdefault(p.plant_id, []).append(p)

    assert len(by_plant["PLT-001"]) == 6, f"Water: {len(by_plant['PLT-001'])}"
    assert len(by_plant["PLT-002"]) == 8, f"Confectionery: {len(by_plant['PLT-002'])}"
    assert len(by_plant["PLT-003"]) == 6, f"Dairy: {len(by_plant['PLT-003'])}"
    assert len(by_plant["PLT-004"]) == 8, f"Pet Food: {len(by_plant['PLT-004'])}"
    assert len(by_plant["PLT-005"]) == 6, f"Prepared: {len(by_plant['PLT-005'])}"
    assert len(PRODUCTS) == 34

    # changeover tiers
    assert get_changeover_time("WAT-500S", "WAT-500P") == 20.0   # same format
    assert get_changeover_time("WAT-500S", "WAT-1LS") == 45.0    # different format, same plant
    assert get_changeover_time("PRE-S8", "PRE-SC2") > 60.0       # allergen transition (SOY introduced)

    # deterministic UUIDs
    assert seed_uuid("WAT-500S") == seed_uuid("WAT-500S")

    print(f"OK — {len(PRODUCTS)} products, {len(CHANGEOVER_MATRIX)} changeover pairs")
