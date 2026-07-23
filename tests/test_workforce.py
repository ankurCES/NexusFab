"""Verify fatigue factor is in [0,1] and shift coverage logic."""
from nexusfab.optimization.workforce import SHIFTS_PER_DAY, SHIFT_HOURS
from nexusfab.simulation.workforce_sim import fatigue_factor


def test_workforce():
    # fatigue_factor must always return [0, 1]
    test_cases = [
        (0, False, 0),
        (4, False, 0),
        (6, False, 0),
        (8, True, 0),
        (11, True, 7),
        (12, True, 10),  # extreme: night + 10 consecutive days
    ]
    for hour, is_night, consec in test_cases:
        f = fatigue_factor(hour, is_night, consec)
        assert 0.0 <= f <= 1.0, f"fatigue_factor({hour}, {is_night}, {consec}) = {f} out of [0,1]"

    # Monotone: longer hours → lower (or equal) fatigue factor (day shift, fresh)
    factors = [fatigue_factor(h, False, 0) for h in [0, 4, 6, 8, 10, 12]]
    for i in range(len(factors) - 1):
        assert factors[i] >= factors[i + 1], f"Fatigue not monotone at index {i}: {factors}"

    # Night shift reduces performance vs day shift
    day = fatigue_factor(6, False, 0)
    night = fatigue_factor(6, True, 0)
    assert night < day, f"Night ({night}) should be worse than day ({day})"

    # Standard shift config
    assert SHIFTS_PER_DAY == 3, f"Expected 3 shifts/day, got {SHIFTS_PER_DAY}"
    assert SHIFT_HOURS == 8, f"Expected 8h shifts, got {SHIFT_HOURS}"
    assert SHIFTS_PER_DAY * SHIFT_HOURS == 24, "Shifts must cover 24h"

    print(f"PASS — fatigue_factor [0,1] for all cases, {SHIFTS_PER_DAY}×{SHIFT_HOURS}h shifts")


if __name__ == "__main__":
    test_workforce()
