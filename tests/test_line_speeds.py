"""Verify all 17 lines have rated speeds and PLT-001-L4 is the fastest."""
from nexusfab.seed.plants import PLANTS


def test_line_speeds():
    lines = [(line.name, line.rated_speed_per_min) for plant in PLANTS for line in plant.lines]

    assert len(lines) == 17, f"Expected 17 lines, got {len(lines)}"

    for name, speed in lines:
        assert speed > 0, f"{name}: rated_speed_per_min must be > 0"

    # PLT-001-L4 (CANNING) is the fastest line
    speed_map = dict(lines)
    fastest_name = max(speed_map, key=speed_map.__getitem__)
    assert fastest_name == "PLT-001-L4", (
        f"Expected PLT-001-L4 to be fastest, got {fastest_name} at {speed_map[fastest_name]}"
    )
    assert speed_map["PLT-001-L4"] > speed_map["PLT-001-L1"], (
        "PLT-001-L4 must be faster than PLT-001-L1"
    )

    print(
        f"PASS — 17 lines, fastest is PLT-001-L4 at {speed_map['PLT-001-L4']:.0f} units/min"
    )


if __name__ == "__main__":
    test_line_speeds()
