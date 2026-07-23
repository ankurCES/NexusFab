"""Verify failure events have valid modes and severity in range 1-5."""
from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.simulation.failure_generator import FailureGenerator, _FAILURE_MODES


def test_failure_gen():
    # All equipment types with defined failure modes have non-empty mode lists
    for etype, modes in _FAILURE_MODES.items():
        assert modes, f"{etype}: empty failure mode list"
        # Cumulative weights must end at 1.0
        assert abs(modes[-1][1] - 1.0) < 1e-9, f"{etype}: cumulative weight != 1.0"

    # Generate events for a real plant and validate all fields
    plant = get_plant("PLT-002")
    all_eq = [eq for line in plant.lines for eq in line.equipment]
    gen = FailureGenerator(all_eq)

    events = list(gen.generate(duration_hours=8760))
    assert events, "FailureGenerator produced no events for 1-year horizon"

    for ev in events:
        assert 1 <= ev.severity <= 5, f"Severity out of range: {ev.severity}"
        assert ev.failure_mode, f"Empty failure mode for {ev.equipment_id}"
        assert ev.timestamp >= 0, f"Negative timestamp: {ev.timestamp}"
        assert ev.mttr_hours > 0, f"mttr_hours must be > 0"
        assert isinstance(ev.requires_spare_part, bool)

    # Events in chronological order
    timestamps = [e.timestamp for e in events]
    assert timestamps == sorted(timestamps), "Events not in chronological order"

    print(f"PASS — {len(events)} failure events, all severity 1-5, valid modes")


if __name__ == "__main__":
    test_failure_gen()
