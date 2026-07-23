"""Product catalog + changeover matrix seed data."""

from dataclasses import dataclass, field

from nexusfab.seed.plants import seed_uuid

# ── Allergen tier mapping (US Big 9 severity for sequencing) ──
ALLERGEN_TIER_MAP: dict[str, int] = {
    "GLUTEN": 1, "DAIRY": 2, "SOY": 2, "SESAME": 2, "EGGS": 3, "NUTS": 4,
}


def compute_allergen_tier(allergens: list[str]) -> int:
    return max((ALLERGEN_TIER_MAP.get(a, 0) for a in allergens), default=0)


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
    allergen_tier: int = field(init=False)

    def __post_init__(self):
        self.allergen_tier = compute_allergen_tier(self.allergens)


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
    ProductSeed("CON-KB4", "NexBar Original 4-finger",  "CONFECTIONERY", "PLT-002", 5000, 30.0, ["GLUTEN", "DAIRY", "EGGS"],  "BAR_4F"),
    ProductSeed("CON-KBD", "NexBar Dark Chocolate",     "CONFECTIONERY", "PLT-002", 5000, 35.0, ["GLUTEN", "DAIRY"],           "BAR_4F"),
    ProductSeed("CON-KBW", "NexBar White Chocolate",    "CONFECTIONERY", "PLT-002", 5000, 40.0, ["GLUTEN", "DAIRY", "EGGS"],  "BAR_4F"),
    ProductSeed("CON-NUT", "NexBar Peanut",             "CONFECTIONERY", "PLT-002", 4000, 45.0, ["GLUTEN", "DAIRY", "NUTS", "EGGS"],   "BAR_4F"),
    ProductSeed("CON-AER", "NexAero Mint",              "CONFECTIONERY", "PLT-002", 4000, 35.0, ["DAIRY"],                     "BAR_STD"),
    ProductSeed("CON-MP8", "NexBar Multi-Pack 8ct",     "CONFECTIONERY", "PLT-002", 3000, 50.0, ["GLUTEN", "DAIRY", "EGGS"],  "MULTIPACK"),
    ProductSeed("CON-QST", "Quality Selection Box",     "CONFECTIONERY", "PLT-002", 2000, 90.0, ["GLUTEN", "DAIRY", "NUTS", "EGGS"],   "SEASONAL"),
    ProductSeed("CON-XMS", "Christmas Selection",       "CONFECTIONERY", "PLT-002", 2500, 120.0, ["GLUTEN", "DAIRY", "NUTS", "EGGS"],  "SEASONAL"),

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
    ProductSeed("PRE-N70", "NexNoodle Instant 70g",     "PREPARED_FOODS", "PLT-005", 15000, 20.0, ["GLUTEN", "SOY", "SESAME"],  "PACK_70"),
    ProductSeed("PRE-N5P", "NexNoodle 5-Pack",          "PREPARED_FOODS", "PLT-005",  5000, 35.0, ["GLUTEN", "SOY", "SESAME"],  "MULTIPACK"),
    ProductSeed("PRE-S8",  "NexSeason All-Purpose 8g",  "PREPARED_FOODS", "PLT-005", 30000, 15.0, [],                 "SACHET_8"),
    ProductSeed("PRE-SC2", "NexSauce Soy 200ml",        "PREPARED_FOODS", "PLT-005",  8000, 30.0, ["SOY", "GLUTEN"],  "BOTTLE_200"),
    ProductSeed("PRE-SC5", "NexSauce Chili 500ml",      "PREPARED_FOODS", "PLT-005",  5000, 35.0, [],                 "BOTTLE_500"),
    ProductSeed("PRE-CUP", "NexNoodle Cup 65g",         "PREPARED_FOODS", "PLT-005", 12000, 25.0, ["GLUTEN", "SOY", "SESAME"],  "CUP_65"),
]
# fmt: on


# ── CIP type classification (production-operations.md §5.1) ──

CIP_NONE = "none"
CIP_RINSE = "rinse"
CIP_STANDARD = "standard"
CIP_ALLERGEN = "allergen"
CIP_DEEP_CLEAN = "deep_clean"


# ── 5-tier CIP class requirements (nestle-compliance.md) ──
# (from_tier, to_tier) → (cip_class, duration_min, validation_method)

def _cip_for_tier_transition(from_tier: int, to_tier: int) -> tuple[str, float, str]:
    if from_tier == to_tier:
        return (CIP_RINSE, 15.0, "visual") if from_tier > 0 else (CIP_NONE, 0.0, "none")
    if from_tier == 4 and to_tier < 4:
        return (CIP_DEEP_CLEAN, 120.0, "ELISA")
    if from_tier < to_tier:
        return (CIP_ALLERGEN, 75.0, "LFD")
    return (CIP_STANDARD, 45.0, "ATP")


CIP_CLASS_REQUIREMENTS: dict[tuple[int, int], tuple[str, float, str]] = {
    (ft, tt): _cip_for_tier_transition(ft, tt) for ft in range(5) for tt in range(5)
}

# ponytail: validation hold added on top of CIP duration — LFD 15 min, ELISA 30 min
_CIP_VALIDATION_TIME: dict[str, float] = {
    CIP_NONE: 0.0, CIP_RINSE: 0.0, CIP_STANDARD: 0.0,
    CIP_ALLERGEN: 15.0, CIP_DEEP_CLEAN: 30.0,
}

# ── Product tier per SKU — the primary changeover cost driver per plant ──
# ponytail: tier captures allergen class + flavor intensity, not every product dimension

# fmt: off
_PRODUCT_TIER: dict[str, str] = {
    # PLT-001 Water: single tier, changeover is format-only
    "WAT-500S": "water", "WAT-500P": "water", "WAT-750S": "water",
    "WAT-1LS":  "water", "WAT-15S":  "water", "WAT-15P":  "water",
    # PLT-002 Confectionery: allergen tier (nuts) is the big driver
    "CON-KB4": "plain_choc", "CON-KBD": "dark_choc",  "CON-KBW": "plain_choc",
    "CON-NUT": "nut_choc",   "CON-AER": "plain_choc", "CON-MP8": "plain_choc",
    "CON-QST": "nut_choc",   "CON-XMS": "nut_choc",
    # PLT-003 Dairy: process format (powder vs UHT) drives changeover
    "DAI-P4":  "dairy_powder", "DAI-P9": "dairy_powder", "DAI-P18": "dairy_powder",
    "DAI-L2":  "dairy_uht",   "DAI-L5": "dairy_uht",    "DAI-L1":  "dairy_uht",
    # PLT-004 Pet Food: protein type + wet/dry format
    "PET-D1":   "dry_kibble", "PET-D5":  "dry_kibble", "PET-D15": "dry_kibble",
    "PET-DC1":  "dry_kibble",
    "PET-WC85": "wet_fish",   "PET-WC4": "wet_fish",
    "PET-WD4":  "wet_meat",
    "PET-TR":   "treats",
    # PLT-005 Prepared Foods: allergen class drives changeover
    "PRE-N70": "noodle_allergen", "PRE-N5P": "noodle_allergen", "PRE-CUP": "noodle_allergen",
    "PRE-S8":  "seasoning_plain", "PRE-SC5": "sauce_plain",
    "PRE-SC2": "sauce_allergen",
}
# fmt: on

# ── Asymmetric changeover matrices per plant category ──
# Derived from docs/research/production-operations.md §5.1
# Key: (from_tier, to_tier) → (minutes, cip_type)
# Core invariant: C[i→j] ≠ C[j→i] — allergen-heavy→clean costs more than reverse

_CHANGEOVER_MATRICES: dict[str, dict[tuple[str, str], tuple[float, str]]] = {
    "WATER": {
        # Single product type — changeovers are dry format swaps
        ("water", "water"): (15.0, CIP_NONE),
    },
    "CONFECTIONERY": {
        # §5.1 Snack/Confectionery matrix — nut allergen drives asymmetry
        ("plain_choc", "plain_choc"): (20.0, CIP_NONE),
        ("plain_choc", "dark_choc"):  (30.0, CIP_NONE),
        ("plain_choc", "nut_choc"):   (60.0, CIP_ALLERGEN),
        ("dark_choc",  "plain_choc"): (45.0, CIP_RINSE),
        ("dark_choc",  "dark_choc"):  (20.0, CIP_NONE),
        ("dark_choc",  "nut_choc"):   (90.0, CIP_ALLERGEN),
        ("nut_choc",   "plain_choc"): (120.0, CIP_DEEP_CLEAN),
        ("nut_choc",   "dark_choc"):  (120.0, CIP_DEEP_CLEAN),
        ("nut_choc",   "nut_choc"):   (30.0, CIP_RINSE),
    },
    "DAIRY": {
        # §5.1 Beverage/Dairy matrix — wet→dry needs full CIP
        ("dairy_powder", "dairy_powder"): (15.0, CIP_NONE),
        ("dairy_powder", "dairy_uht"):    (45.0, CIP_RINSE),
        ("dairy_uht",    "dairy_powder"): (90.0, CIP_STANDARD),
        ("dairy_uht",    "dairy_uht"):    (15.0, CIP_NONE),
    },
    "PET_FOOD": {
        # §5.1 flavor/protein transition — fish residue is hardest to clear
        ("dry_kibble", "dry_kibble"): (15.0, CIP_NONE),
        ("dry_kibble", "wet_fish"):   (45.0, CIP_RINSE),
        ("dry_kibble", "wet_meat"):   (30.0, CIP_RINSE),
        ("dry_kibble", "treats"):     (20.0, CIP_NONE),
        ("wet_fish",   "dry_kibble"): (60.0, CIP_STANDARD),
        ("wet_fish",   "wet_fish"):   (15.0, CIP_NONE),
        ("wet_fish",   "wet_meat"):   (45.0, CIP_RINSE),
        ("wet_fish",   "treats"):     (45.0, CIP_RINSE),
        ("wet_meat",   "dry_kibble"): (45.0, CIP_RINSE),
        ("wet_meat",   "wet_fish"):   (45.0, CIP_RINSE),
        ("wet_meat",   "wet_meat"):   (15.0, CIP_NONE),
        ("wet_meat",   "treats"):     (30.0, CIP_NONE),
        ("treats",     "dry_kibble"): (30.0, CIP_NONE),
        ("treats",     "wet_fish"):   (45.0, CIP_RINSE),
        ("treats",     "wet_meat"):   (30.0, CIP_NONE),
        ("treats",     "treats"):     (15.0, CIP_NONE),
    },
    "PREPARED_FOODS": {
        # §5.1 Dry Powder/Blending matrix — allergen→clean costs more
        ("noodle_allergen",  "noodle_allergen"):  (15.0, CIP_NONE),
        ("noodle_allergen",  "seasoning_plain"):  (45.0, CIP_RINSE),
        ("noodle_allergen",  "sauce_allergen"):   (20.0, CIP_NONE),
        ("noodle_allergen",  "sauce_plain"):      (45.0, CIP_RINSE),
        ("seasoning_plain",  "noodle_allergen"):  (20.0, CIP_NONE),
        ("seasoning_plain",  "seasoning_plain"):  (15.0, CIP_NONE),
        ("seasoning_plain",  "sauce_allergen"):   (25.0, CIP_NONE),
        ("seasoning_plain",  "sauce_plain"):      (15.0, CIP_NONE),
        ("sauce_allergen",   "noodle_allergen"):  (20.0, CIP_NONE),
        ("sauce_allergen",   "seasoning_plain"):  (45.0, CIP_RINSE),
        ("sauce_allergen",   "sauce_allergen"):   (15.0, CIP_NONE),
        ("sauce_allergen",   "sauce_plain"):      (30.0, CIP_RINSE),
        ("sauce_plain",      "noodle_allergen"):  (25.0, CIP_NONE),
        ("sauce_plain",      "seasoning_plain"):  (15.0, CIP_NONE),
        ("sauce_plain",      "sauce_allergen"):   (20.0, CIP_NONE),
        ("sauce_plain",      "sauce_plain"):      (15.0, CIP_NONE),
    },
}

# ponytail: +10 min for mechanical format swap within same tier, upgrade to per-format table if needed
_FORMAT_DELTA = 10.0


def get_changeover_info(from_sku: str, to_sku: str) -> tuple[float, str]:
    """Asymmetric changeover (minutes, cip_type) between two SKUs."""
    if from_sku == to_sku:
        return (0.0, CIP_NONE)
    p1 = get_product(from_sku)
    p2 = get_product(to_sku)
    if not p1 or not p2:
        return (60.0, CIP_STANDARD)
    t1 = _PRODUCT_TIER.get(p1.sku)
    t2 = _PRODUCT_TIER.get(p2.sku)
    if not t1 or not t2:
        return (60.0, CIP_STANDARD)
    matrix = _CHANGEOVER_MATRICES.get(p1.category)
    if not matrix:
        return (60.0, CIP_STANDARD)
    entry = matrix.get((t1, t2))
    if not entry:
        return (60.0, CIP_STANDARD)
    minutes, cip = entry
    if t1 == t2 and p1.format_type != p2.format_type:
        minutes += _FORMAT_DELTA
    minutes += _CIP_VALIDATION_TIME.get(cip, 0.0)
    return (minutes, cip)


def get_changeover_time(from_sku: str, to_sku: str) -> float:
    """Changeover minutes between two SKUs. Asymmetric: C[i→j] ≠ C[j→i]."""
    return get_changeover_info(from_sku, to_sku)[0]


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
    assert len(_PRODUCT_TIER) == 34, "every SKU needs a tier"

    # asymmetry: nut→plain costs more than plain→nut
    assert get_changeover_time("CON-NUT", "CON-KB4") > get_changeover_time("CON-KB4", "CON-NUT")
    # asymmetry: dairy UHT→powder costs more than powder→UHT
    assert get_changeover_time("DAI-L2", "DAI-P4") > get_changeover_time("DAI-P4", "DAI-L2")
    # asymmetry: wet_fish→dry costs more than dry→wet_fish
    assert get_changeover_time("PET-WC85", "PET-D1") > get_changeover_time("PET-D1", "PET-WC85")
    # format delta: same tier different format costs more than same format
    assert get_changeover_time("WAT-500S", "WAT-1LS") > get_changeover_time("WAT-500S", "WAT-500P")
    # self-transition is zero
    assert get_changeover_time("WAT-500S", "WAT-500S") == 0.0
    # CIP classification
    _, cip = get_changeover_info("CON-NUT", "CON-KB4")
    assert cip == CIP_DEEP_CLEAN, f"nut→plain should be deep_clean, got {cip}"
    _, cip = get_changeover_info("CON-KB4", "CON-NUT")
    assert cip == CIP_ALLERGEN, f"plain→nut should be allergen, got {cip}"
    # allergen→clean direction costs more than clean→allergen
    assert get_changeover_time("PRE-N70", "PRE-S8") > get_changeover_time("PRE-S8", "PRE-N70")

    # deterministic UUIDs
    assert seed_uuid("WAT-500S") == seed_uuid("WAT-500S")

    # allergen tier checks
    assert get_product("WAT-500S").allergen_tier == 0, "water should be tier 0"
    assert get_product("CON-AER").allergen_tier == 2, "dairy-only should be tier 2"
    assert get_product("CON-KB4").allergen_tier == 3, "egg product should be tier 3"
    assert get_product("CON-NUT").allergen_tier == 4, "nut product should be tier 4"
    assert get_product("PRE-N70").allergen_tier == 2, "soy/sesame should be tier 2"
    assert "EGGS" in get_product("CON-KB4").allergens
    assert "SESAME" in get_product("PRE-N70").allergens

    # CIP class requirements: nut→non-allergen requires 120min deep clean
    cip_cls, cip_dur, cip_val = CIP_CLASS_REQUIREMENTS[(4, 0)]
    assert cip_cls == CIP_DEEP_CLEAN and cip_dur == 120.0 and cip_val == "ELISA"
    # tier upgrade requires allergen CIP
    cip_cls, cip_dur, _ = CIP_CLASS_REQUIREMENTS[(0, 4)]
    assert cip_cls == CIP_ALLERGEN and cip_dur == 75.0
    # same tier (non-zero) requires rinse
    cip_cls, cip_dur, _ = CIP_CLASS_REQUIREMENTS[(2, 2)]
    assert cip_cls == CIP_RINSE and cip_dur == 15.0
    # same tier 0 requires nothing
    cip_cls, cip_dur, _ = CIP_CLASS_REQUIREMENTS[(0, 0)]
    assert cip_cls == CIP_NONE and cip_dur == 0.0

    # CIP validation time added to changeover
    nut_to_plain_min, nut_to_plain_cip = get_changeover_info("CON-NUT", "CON-KB4")
    assert nut_to_plain_cip == CIP_DEEP_CLEAN
    assert nut_to_plain_min >= 150.0, f"nut→plain should include 30min ELISA hold, got {nut_to_plain_min}"

    # print PLT-001 matrix to verify asymmetry
    print("PLT-001 (Water) changeover matrix:")
    p001 = get_products_for_plant("PLT-001")
    for p1 in p001:
        for p2 in p001:
            if p1.sku != p2.sku:
                mins, ct = get_changeover_info(p1.sku, p2.sku)
                print(f"  {p1.sku:>8} → {p2.sku:<8}  {mins:5.0f} min  ({ct})")

    # print allergen tier summary
    tiers = {t: [] for t in range(5)}
    for p in PRODUCTS:
        tiers[p.allergen_tier].append(p.sku)
    print("\nAllergen tiers:")
    for t, skus in tiers.items():
        print(f"  Tier {t}: {len(skus)} SKUs — {', '.join(skus[:4])}{'...' if len(skus) > 4 else ''}")

    print(f"\nOK — {len(PRODUCTS)} products, {len(_PRODUCT_TIER)} tiers, "
          f"{sum(len(m) for m in _CHANGEOVER_MATRICES.values())} matrix entries, "
          f"{len(CIP_CLASS_REQUIREMENTS)} CIP class entries")
