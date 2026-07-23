"""Verify all line types have CCPs with valid critical limits."""
from nexusfab.optimization.regulatory import HACCP_CCPS
from nexusfab.seed.plants import PLANTS


def test_ccps():
    # Every line type in the plant network must have at least one CCP
    all_line_types = {line.line_type for plant in PLANTS for line in plant.lines}
    missing = all_line_types - set(HACCP_CCPS)
    assert not missing, f"Line types without CCPs: {missing}"

    for line_type, ccps in HACCP_CCPS.items():
        assert ccps, f"{line_type}: empty CCP list"
        for ccp in ccps:
            # Each CCP must have an id, at least one critical limit, and a frequency
            assert ccp.get("ccp_id"), f"{line_type}: CCP missing id"
            assert ccp.get("frequency_min", 0) > 0, f"{ccp['ccp_id']}: frequency_min must be > 0"

            low = ccp.get("critical_limit_low")
            high = ccp.get("critical_limit_high")
            assert low is not None or high is not None, f"{ccp['ccp_id']}: must have at least one limit"

            # If both limits set, low must be < high
            if low is not None and high is not None:
                assert low < high, f"{ccp['ccp_id']}: low {low} >= high {high}"

    total_ccps = sum(len(v) for v in HACCP_CCPS.values())
    print(f"PASS — {len(HACCP_CCPS)} line types, {total_ccps} CCPs, all limits valid")


if __name__ == "__main__":
    test_ccps()
