"""Sensor data stream generator — OPC-UA / ISA-95 tag structure.

Tag format: <plant_id>.<line_name>.<equipment_id>.<sensor_suffix>
Sample rates: vibration 10 Hz, all others 1 Hz (overridable per stream).
"""
from __future__ import annotations

import heapq
import random
from dataclasses import dataclass
from typing import Iterator, Literal

from nexusfab.seed.plants import EquipmentSeed, LineSeed, PlantSeed  # noqa: F401

Quality = Literal["GOOD", "UNCERTAIN", "BAD"]


@dataclass(frozen=True)
class _SensorSpec:
    suffix: str
    setpoint: float
    sigma: float  # always absolute
    unit: str
    hz: float


def _abs(suffix: str, setpoint: float, sigma: float, unit: str, hz: float = 1.0) -> _SensorSpec:
    return _SensorSpec(suffix, setpoint, sigma, unit, hz)


def _pct(suffix: str, setpoint: float, pct: float, unit: str, hz: float = 1.0) -> _SensorSpec:
    return _SensorSpec(suffix, setpoint, setpoint * pct, unit, hz)


# Per equipment-type sensor sets — ISA-5.1 loop-tag suffix conventions
_SENSOR_SETS: dict[str, list[_SensorSpec]] = {
    "FILLER": [
        _pct("FLOW", 1200.0, 0.02,  "L/min"),
        _abs("PRES",    2.5, 0.02,  "bar"),
        _abs("TEMP",   20.0, 0.5,   "°C"),
        _pct("SPD",   900.0, 0.005, "RPM"),
    ],
    "UHT": [  # UHT Sterilizer / PASTEURIZER / HOMOGENIZER
        _abs("TEMP_Z1",  72.0, 0.5,  "°C"),
        _abs("TEMP_Z2",  90.0, 0.5,  "°C"),
        _abs("TEMP_Z3", 138.0, 0.5,  "°C"),
        _abs("PRES_1",    3.0, 0.02, "bar"),
        _abs("PRES_2",    2.5, 0.02, "bar"),
        _pct("FLOW",  5000.0, 0.02,  "L/min"),
    ],
    "MIXER": [
        _pct("PWR",   45.0, 0.01,  "kW"),
        _pct("SPD",  120.0, 0.005, "RPM"),
        _abs("TEMP",  25.0, 0.5,   "°C"),
        _abs("VIB",    3.0, 0.15,  "mm/s", hz=10.0),
    ],
    "EXTRUDER": [  # DRYER type in seed (twin-screw extruder)
        _abs("TEMP_Z1",  80.0, 0.5,  "°C"),
        _abs("TEMP_Z2", 120.0, 0.5,  "°C"),
        _abs("TEMP_Z3", 150.0, 0.5,  "°C"),
        _abs("TEMP_Z4", 170.0, 0.5,  "°C"),
        _abs("TEMP_Z5", 180.0, 0.5,  "°C"),
        _abs("PRES_1",   80.0, 0.02, "bar"),
        _abs("PRES_2",  120.0, 0.02, "bar"),
        _abs("PRES_3",  150.0, 0.02, "bar"),
        _pct("PWR",      90.0, 0.01,  "kW"),
        _pct("SPD",     600.0, 0.005, "RPM"),
    ],
    "CONVEYOR": [
        _pct("SPD", 1450.0, 0.005, "RPM"),
        _abs("VIB",    2.5, 0.15,  "mm/s", hz=10.0),
        _pct("PWR",   12.0, 0.01,  "kW"),
    ],
    "CIP_SKID": [
        _pct("FLOW",  500.0, 0.02, "L/min"),
        _abs("TEMP",   75.0, 0.5,  "°C"),
        _abs("COND",   25.0, 0.5,  "mS/cm"),  # conductivity for rinse-phase detection
        _abs("PRES",    2.0, 0.02, "bar"),
    ],
}

# Seed equipment_type → _SENSOR_SETS key; unmapped types fall back to CONVEYOR
_TYPE_MAP: dict[str, str] = {
    "FILLER":      "FILLER",
    "PASTEURIZER": "UHT",
    "HOMOGENIZER": "UHT",
    "MIXER":       "MIXER",
    "DRYER":       "EXTRUDER",
    "CONVEYOR":    "CONVEYOR",
    "CIP_SKID":    "CIP_SKID",
    "CAPPER":      "CONVEYOR",
    "LABELER":     "CONVEYOR",
    "PACKAGING":   "CONVEYOR",
}


class SensorStream:
    """Generates realistic OPC-UA sensor readings for a production line.

    Yields batches of reading dicts:
        {"tag", "timestamp", "value", "unit", "quality": "GOOD"|"UNCERTAIN"|"BAD"}

    Degradation: when equipment age > 70% of Weibull η, readings drift and
    quality degrades to UNCERTAIN; at 90% η quality becomes BAD.
    """

    def __init__(
        self,
        plant: PlantSeed,
        line_name: str,
        equipment_ages: dict[str, float] | None = None,
        batch_size: int = 100,
        sample_rate_hz: float | None = None,
    ) -> None:
        line = next(l for l in plant.lines if l.name == line_name)
        self._plant_id = plant.id
        self._line = line
        self._ages = equipment_ages or {}
        self._batch_size = batch_size
        self._rate_override = sample_rate_hz

        self._sensors: list[tuple[str, _SensorSpec, EquipmentSeed]] = []
        for eq in line.equipment:
            key = _TYPE_MAP.get(eq.equipment_type.upper())
            if key is None:
                continue
            for spec in _SENSOR_SETS[key]:
                tag = f"{plant.id}.{line.name}.{eq.name}.{spec.suffix}"
                self._sensors.append((tag, spec, eq))

    @property
    def tag_count(self) -> int:
        return len(self._sensors)

    def _quality(self, eq: EquipmentSeed, age: float) -> Quality:
        if eq.weibull_eta <= 0:
            return "GOOD"
        pct = age / eq.weibull_eta
        if pct >= 0.90:
            return "BAD"
        if pct >= 0.70:
            return "UNCERTAIN"
        return "GOOD"

    def _drift(self, spec: _SensorSpec, eq: EquipmentSeed, age: float) -> float:
        """Return drift offset when age > 70% of η (per-sensor-type physics)."""
        if eq.weibull_eta <= 0 or age < 0.70 * eq.weibull_eta:
            return 0.0
        excess_100h = (age - 0.70 * eq.weibull_eta) / 100.0
        if "VIB" in spec.suffix:
            return 0.1 * excess_100h   # +0.1 mm/s per 100h degradation
        if "TEMP" in spec.suffix:
            return 0.2 * excess_100h   # +0.2°C per 100h degradation
        return 0.0

    def stream(
        self, duration_seconds: float, start_time: float = 0.0
    ) -> Iterator[list[dict]]:
        """Yield batches of readings over [start_time, start_time + duration_seconds)."""
        intervals = [
            1.0 / (self._rate_override or spec.hz)
            for _, spec, _ in self._sensors
        ]
        heap: list[tuple[float, int]] = [
            (start_time + intervals[i], i) for i in range(len(self._sensors))
        ]
        heapq.heapify(heap)

        end = start_time + duration_seconds
        batch: list[dict] = []

        while heap:
            t, i = heapq.heappop(heap)
            if t >= end:
                break
            tag, spec, eq = self._sensors[i]
            age = self._ages.get(eq.name, 0.0)
            value = round(
                random.gauss(spec.setpoint + self._drift(spec, eq, age), spec.sigma), 4
            )
            batch.append({
                "tag": tag,
                "timestamp": round(t, 6),
                "value": value,
                "unit": spec.unit,
                "quality": self._quality(eq, age),
            })
            heapq.heappush(heap, (t + intervals[i], i))
            if len(batch) >= self._batch_size:
                yield batch
                batch = []

        if batch:
            yield batch


if __name__ == "__main__":
    import statistics
    from nexusfab.seed.plants import get_plant

    random.seed(42)
    plant = get_plant("PLT-001")
    assert plant, "PLT-001 not found in seed data"

    ss = SensorStream(plant, "PLT-001-L1", batch_size=500)
    all_readings: list[dict] = []
    for batch in ss.stream(3600.0):  # 1 hour
        all_readings.extend(batch)

    by_tag: dict[str, list[float]] = {}
    units: dict[str, str] = {}
    qualities: dict[str, str] = {}
    for r in all_readings:
        by_tag.setdefault(r["tag"], []).append(r["value"])
        units[r["tag"]] = r["unit"]
        qualities[r["tag"]] = r["quality"]

    print(f"\nPLT-001-L1 | tags: {ss.tag_count} | total readings: {len(all_readings):,}\n")
    print(f"{'Tag':<55} {'N':>7} {'Mean':>10} {'Stdev':>10}  {'Unit':<8} Quality")
    print("-" * 110)
    for tag in sorted(by_tag):
        vals = by_tag[tag]
        mean = statistics.mean(vals)
        stdev = statistics.stdev(vals) if len(vals) > 1 else 0.0
        print(
            f"{tag:<55} {len(vals):>7,} {mean:>10.3f} {stdev:>10.4f}  "
            f"{units[tag]:<8} {qualities[tag]}"
        )

    assert ss.tag_count > 0
    assert len(all_readings) > 0
    print("\nPASS")
