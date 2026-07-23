"""Verify cocoa lead time > water, and all materials have a storage regime."""
from nexusfab.optimization.demand import (
    RAW_MATERIAL_LEAD_TIMES,
    _CATEGORY_BOTTLENECK,
    _material_lead_time_weeks,
)

VALID_STORAGE = {"ambient", "chilled", "frozen", "cool"}


def test_lead_times():
    # Every material entry has a storage regime
    for mat, info in RAW_MATERIAL_LEAD_TIMES.items():
        assert "storage" in info, f"{mat}: missing storage regime"
        assert info["storage"] in VALID_STORAGE, (
            f"{mat}: unknown storage '{info['storage']}'"
        )
        # At least one lead time (domestic or import) must be defined
        d = info.get("domestic_days")
        i = info.get("import_days")
        assert d is not None or i is not None, f"{mat}: no lead time defined"

    # Cocoa (confectionery) has longer lead time than source_water (water)
    cocoa_lt = _material_lead_time_weeks("CONFECTIONERY")
    water_lt = _material_lead_time_weeks("WATER")
    assert cocoa_lt > water_lt, (
        f"cocoa ({cocoa_lt:.1f}w) should be longer than water ({water_lt:.1f}w)"
    )

    # All plant categories map to a known material
    for category, mat_key in _CATEGORY_BOTTLENECK.items():
        assert mat_key in RAW_MATERIAL_LEAD_TIMES, (
            f"Category {category} maps to unknown material '{mat_key}'"
        )

    print(
        f"PASS — {len(RAW_MATERIAL_LEAD_TIMES)} materials, "
        f"cocoa {cocoa_lt:.1f}w > water {water_lt:.1f}w"
    )


if __name__ == "__main__":
    test_lead_times()
