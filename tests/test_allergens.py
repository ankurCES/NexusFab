"""Verify 6 allergens defined, nut-to-free transition requires deep clean."""
from nexusfab.seed.products import (
    ALLERGEN_TIER_MAP,
    CIP_DEEP_CLEAN,
    _CHANGEOVER_MATRICES,
)


def test_allergens():
    # US Big 9 subset: exactly 6 tracked allergens
    assert len(ALLERGEN_TIER_MAP) == 6, (
        f"Expected 6 allergens, got {ALLERGEN_TIER_MAP}"
    )
    expected = {"GLUTEN", "DAIRY", "SOY", "SESAME", "EGGS", "NUTS"}
    assert set(ALLERGEN_TIER_MAP) == expected, (
        f"Allergen set mismatch: {set(ALLERGEN_TIER_MAP)}"
    )

    # NUTS must be highest tier
    nut_tier = ALLERGEN_TIER_MAP["NUTS"]
    assert nut_tier == max(ALLERGEN_TIER_MAP.values()), "NUTS must be highest allergen tier"

    # Nut-to-allergen-free changeover requires deep clean (CONFECTIONERY matrix)
    conf = _CHANGEOVER_MATRICES["CONFECTIONERY"]
    _, cip_type = conf[("nut_choc", "plain_choc")]
    assert cip_type == CIP_DEEP_CLEAN, (
        f"nut_choc→plain_choc should require deep_clean, got '{cip_type}'"
    )
    _, cip_type2 = conf[("nut_choc", "dark_choc")]
    assert cip_type2 == CIP_DEEP_CLEAN, (
        f"nut_choc→dark_choc should require deep_clean, got '{cip_type2}'"
    )

    print(f"PASS — 6 allergens, NUTS tier={nut_tier}, nut→free requires {CIP_DEEP_CLEAN}")


if __name__ == "__main__":
    test_allergens()
