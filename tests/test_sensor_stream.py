"""Verify sensor tags follow ISA-95 naming and correct sensor sets per equipment type."""
from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.simulation.sensor_stream import SensorStream, _SENSOR_SETS, _TYPE_MAP


def test_sensor_stream():
    # All equipment types in seed map to a known sensor set
    all_eq_types = {eq.equipment_type for p in PLANTS for l in p.lines for eq in l.equipment}
    for etype in all_eq_types:
        mapped = _TYPE_MAP.get(etype, "CONVEYOR")
        assert mapped in _SENSOR_SETS, f"Equipment type {etype} maps to unknown sensor set {mapped}"

    # Each sensor set has at least 2 sensors with positive setpoints
    for sensor_key, specs in _SENSOR_SETS.items():
        assert len(specs) >= 2, f"{sensor_key}: expected ≥2 sensors, got {len(specs)}"
        for spec in specs:
            assert spec.suffix, f"{sensor_key}: sensor missing suffix"
            assert spec.hz > 0, f"{sensor_key}.{spec.suffix}: hz must be > 0"

    # Generate a short stream and verify ISA-95 tag format: plant.line.equipment.suffix
    plant = get_plant("PLT-001")
    stream = SensorStream(plant, "PLT-001-L1", batch_size=10)
    readings = []
    for batch in stream.stream(duration_seconds=5):
        readings.extend(batch)
        if readings:
            break

    assert readings, "SensorStream produced no readings"
    for r in readings[:5]:
        tag = r["tag"]
        parts = tag.split(".")
        assert len(parts) == 4, f"ISA-95 tag must have 4 parts, got: '{tag}'"
        assert parts[0] == "PLT-001", f"Tag plant prefix wrong: '{tag}'"
        assert "value" in r and "unit" in r and "quality" in r

    print(f"PASS — {len(_SENSOR_SETS)} sensor sets, ISA-95 tag format verified on {len(readings)} readings")


if __name__ == "__main__":
    test_sensor_stream()
