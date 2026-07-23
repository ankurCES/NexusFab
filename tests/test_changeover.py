"""Verify asymmetric changeover matrices for 3 categories, C[A→B] ≠ C[B→A]."""
from nexusfab.seed.products import _CHANGEOVER_MATRICES


def test_changeover():
    # At least 3 non-trivial categories with asymmetric transitions
    asymmetric_categories = []
    for category, matrix in _CHANGEOVER_MATRICES.items():
        found_asymmetry = False
        for (a, b), (cost_ab, _) in matrix.items():
            if a == b:
                continue
            reverse = matrix.get((b, a))
            if reverse is not None and reverse[0] != cost_ab:
                found_asymmetry = True
                break
        if found_asymmetry:
            asymmetric_categories.append(category)

    assert len(asymmetric_categories) >= 3, (
        f"Expected ≥3 asymmetric categories, got {asymmetric_categories}"
    )

    # Spot-check: CONFECTIONERY nut→plain costs more than plain→nut
    conf = _CHANGEOVER_MATRICES["CONFECTIONERY"]
    nut_to_plain = conf[("nut_choc", "plain_choc")][0]
    plain_to_nut = conf[("plain_choc", "nut_choc")][0]
    assert nut_to_plain > plain_to_nut, (
        f"nut→plain ({nut_to_plain}) should cost more than plain→nut ({plain_to_nut})"
    )

    # Spot-check: DAIRY uht→powder costs more than powder→uht (wet→dry needs full CIP)
    dairy = _CHANGEOVER_MATRICES["DAIRY"]
    uht_to_powder = dairy[("dairy_uht", "dairy_powder")][0]
    powder_to_uht = dairy[("dairy_powder", "dairy_uht")][0]
    assert uht_to_powder > powder_to_uht, (
        f"uht→powder ({uht_to_powder}) should cost more than powder→uht ({powder_to_uht})"
    )

    print(f"PASS — {len(asymmetric_categories)} asymmetric categories: {asymmetric_categories}")


if __name__ == "__main__":
    test_changeover()
