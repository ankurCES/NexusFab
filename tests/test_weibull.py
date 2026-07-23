"""Verify Weibull params are loaded and valid for all equipment in the plant network."""
from nexusfab.seed.plants import PLANTS, WEIBULL_BY_TYPE


def test_weibull():
    # All 9 named equipment types have positive β and η
    for etype, (beta, eta) in WEIBULL_BY_TYPE.items():
        assert beta > 0, f"{etype}: β must be > 0, got {beta}"
        assert eta > 0, f"{etype}: η must be > 0, got {eta}"

    # Every equipment instance across all 17 lines inherits valid Weibull params
    for plant in PLANTS:
        for line in plant.lines:
            for eq in line.equipment:
                assert eq.weibull_beta > 0, f"{eq.name}: β={eq.weibull_beta}"
                assert eq.weibull_eta > 0, f"{eq.name}: η={eq.weibull_eta}"
                assert eq.mtbf_hours > 0, f"{eq.name}: MTBF={eq.mtbf_hours}"

    # All equipment types present in the network have Weibull entries
    all_types = {eq.equipment_type for p in PLANTS for l in p.lines for eq in l.equipment}
    missing = all_types - set(WEIBULL_BY_TYPE)
    assert not missing, f"Missing Weibull params for types: {missing}"

    total_eq = sum(len(l.equipment) for p in PLANTS for l in p.lines)
    print(f"PASS — {len(WEIBULL_BY_TYPE)} Weibull types, {total_eq} equipment instances validated")


if __name__ == "__main__":
    test_weibull()
