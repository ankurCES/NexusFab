"""Failure signature injection — pre-failure sensor patterns for PdM training.

Injects realistic degradation curves into SensorStream readings so predictive
maintenance models train on realistic pre-failure data.

Usage:
    raw = SensorStream(plant, line).stream(duration_seconds)
    events = list(FailureGenerator(equipment).generate(duration_hours))
    enriched = inject_signatures(raw, events)
    for batch in enriched:
        store(batch)
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Iterator

from nexusfab.simulation.failure_generator import FailureEvent


@dataclass
class SensorEffect:
    """One sensor's degradation pattern during pre-failure window."""
    tag_pattern: str                               # substring matched against OPC-UA tag
    transform_fn: Callable[[float, float], float]  # (t_to_failure_h, baseline) → new value


@dataclass
class FailureSignature:
    """Pre-failure degradation signature matched to a failure mode keyword."""
    failure_mode: str       # |-separated keywords; any match fires the signature
    lead_time_hours: float  # how far before failure the degradation begins
    sensor_effects: list[SensorEffect] = field(default_factory=list)


# ── Bearing failure (7-14 day lead → 240 h midpoint) ─────────────────────────
def _bearing_vib(lead: float = 240.0) -> SensorEffect:
    # Vibration: 2→8 mm/s ramp + BPFO/BPFI harmonic spikes in last 48 h
    def fn(t: float, base: float) -> float:
        ramp = max(0.0, 1.0 - t / lead)
        spike = abs(random.gauss(0, 2.0)) if t < 48.0 else 0.0
        return base + 6.0 * ramp + spike
    return SensorEffect("VIB", fn)


def _bearing_temp(lead: float = 240.0) -> SensorEffect:
    # Temperature: +10 °C in last 72 h
    def fn(t: float, base: float) -> float:
        return base if t > 72.0 else base + 10.0 * (1.0 - t / 72.0)
    return SensorEffect("TEMP", fn)


# ── Pump cavitation (3-7 day lead → 120 h midpoint) ──────────────────────────
def _cav_pres(lead: float = 120.0) -> SensorEffect:
    # Pressure: oscillation amplitude grows as failure approaches
    def fn(t: float, base: float) -> float:
        amp = 0.15 * abs(base) * max(0.0, 1.0 - t / lead)
        return base + random.gauss(0, amp + 1e-6)
    return SensorEffect("PRES", fn)


def _cav_flow(lead: float = 120.0) -> SensorEffect:
    # Flow: intermittent 10-30 % drops, probability grows with proximity
    def fn(t: float, base: float) -> float:
        ramp = max(0.0, 1.0 - t / lead)
        if random.random() < 0.20 * ramp:
            return base * (1.0 - random.uniform(0.10, 0.30))
        return base
    return SensorEffect("FLOW", fn)


def _cav_vib(lead: float = 120.0) -> SensorEffect:
    # Vibration: broadband linear increase
    def fn(t: float, base: float) -> float:
        return base + 3.0 * max(0.0, 1.0 - t / lead)
    return SensorEffect("VIB", fn)


# ── Motor winding failure (14-30 day lead → 504 h midpoint) ──────────────────
def _motor_pwr(lead: float = 504.0) -> SensorEffect:
    # Power: gradual +17.5 % above rated (midpoint of 10-25 %)
    def fn(t: float, base: float) -> float:
        return base * (1.0 + 0.175 * max(0.0, 1.0 - t / lead))
    return SensorEffect("PWR", fn)


def _motor_temp(lead: float = 504.0) -> SensorEffect:
    # Temperature: steady +30 °C rise (midpoint of 20-40 °C)
    def fn(t: float, base: float) -> float:
        return base + 30.0 * max(0.0, 1.0 - t / lead)
    return SensorEffect("TEMP", fn)


def _motor_vib(lead: float = 504.0) -> SensorEffect:
    # Vibration: 2× line-frequency component growing (approximated as DC offset)
    def fn(t: float, base: float) -> float:
        return base + 2.0 * max(0.0, 1.0 - t / lead)
    return SensorEffect("VIB", fn)


# ── Seal degradation (7-21 day lead → 336 h midpoint) ────────────────────────
def _seal_pres(lead: float = 336.0) -> SensorEffect:
    # Pressure: slow decline + micro-leak spikes
    def fn(t: float, base: float) -> float:
        ramp = max(0.0, 1.0 - t / lead)
        decline = base * (1.0 - 0.08 * ramp)
        spike = base * random.uniform(0.05, 0.10) if random.random() < 0.05 * ramp else 0.0
        return decline + spike
    return SensorEffect("PRES", fn)


def _seal_flow(lead: float = 336.0) -> SensorEffect:
    # Flow: upstream/downstream imbalance — growing deviation
    def fn(t: float, base: float) -> float:
        return base * (1.0 - 0.15 * max(0.0, 1.0 - t / lead))
    return SensorEffect("FLOW", fn)


def _seal_temp(lead: float = 336.0) -> SensorEffect:
    # Temperature: localized hot spots ±5.5 °C (midpoint of 3-8 °C)
    def fn(t: float, base: float) -> float:
        amp = 5.5 * max(0.0, 1.0 - t / lead)
        return base + random.uniform(-amp, amp)
    return SensorEffect("TEMP", fn)


# ── Module-level signature catalogue ─────────────────────────────────────────
SIGNATURES: list[FailureSignature] = [
    FailureSignature(
        failure_mode="bearing",
        lead_time_hours=240.0,
        sensor_effects=[_bearing_vib(), _bearing_temp()],
    ),
    FailureSignature(
        failure_mode="pump cavitation",
        lead_time_hours=120.0,
        sensor_effects=[_cav_pres(), _cav_flow(), _cav_vib()],
    ),
    FailureSignature(
        failure_mode="motor",
        lead_time_hours=504.0,
        sensor_effects=[_motor_pwr(), _motor_temp(), _motor_vib()],
    ),
    FailureSignature(
        failure_mode="seal|gasket",
        lead_time_hours=336.0,
        sensor_effects=[_seal_pres(), _seal_flow(), _seal_temp()],
    ),
]


def inject_signatures(
    stream: Iterator[list[dict]],
    failure_events: list[FailureEvent],
    signatures: list[FailureSignature] | None = None,
    false_alarm_rate: float = 0.05,
    rng: random.Random | None = None,
) -> Iterator[list[dict]]:
    """Wrap a SensorStream iterator, injecting pre-failure patterns and false alarms.

    Deltas from overlapping signatures are accumulated additively so equipment
    showing multiple concurrent degradation modes combines correctly.

    Args:
        stream:           SensorStream.stream() iterator — timestamps in seconds.
        failure_events:   FailureGenerator output — timestamps in hours.
        signatures:       Override SIGNATURES catalogue if provided.
        false_alarm_rate: Fraction of readings that receive a spurious anomaly
                          unrelated to any real failure (default 5 %).
        rng:              Seeded Random for false-alarm reproducibility.
                          Note: transform fns use module-level random directly.
    """
    # ponytail: transform fns use module random; rng= only controls false alarms
    _rng = rng if rng is not None else random
    sigs = signatures if signatures is not None else SIGNATURES

    # Pre-compute active pre-failure windows: (start_s, end_s, equipment_id, sig)
    windows: list[tuple[float, float, str, FailureSignature]] = []
    for ev in failure_events:
        fail_s = ev.timestamp * 3600.0
        for sig in sigs:
            keywords = sig.failure_mode.split("|")
            if any(kw in ev.failure_mode for kw in keywords):
                windows.append((
                    fail_s - sig.lead_time_hours * 3600.0,
                    fail_s,
                    ev.equipment_id,
                    sig,
                ))

    for batch in stream:
        out: list[dict] = []
        for reading in batch:
            tag: str = reading["tag"]
            t_s: float = reading["timestamp"]
            base: float = reading["value"]
            delta = 0.0

            # Accumulate signature deltas for all matching windows
            for start_s, end_s, eq_id, sig in windows:
                if start_s <= t_s < end_s and eq_id in tag:
                    t_to_fail = (end_s - t_s) / 3600.0
                    for fx in sig.sensor_effects:
                        if fx.tag_pattern in tag:
                            delta += fx.transform_fn(t_to_fail, base) - base

            # False alarm: spurious anomaly unrelated to real failure
            if _rng.random() < false_alarm_rate:
                delta += _rng.gauss(0, abs(base) * 0.10 + 0.10)

            if delta:
                reading = dict(reading)
                reading["value"] = round(base + delta, 4)
            out.append(reading)
        yield out


if __name__ == "__main__":
    """Bearing failure injection demo — PLT001-L1-MXR VIB ramp-up."""
    from nexusfab.seed.plants import get_plant
    from nexusfab.simulation.sensor_stream import SensorStream

    random.seed(42)
    plant = get_plant("PLT-001")
    assert plant, "PLT-001 not found"

    FAIL_AT_H = 240.0  # bearing failure at t=240h
    LEAD_H = 240.0     # 10-day lead window

    # One FailureEvent for the MIXER (MIXER has VIB; FILLER does not)
    ev = FailureEvent(
        equipment_id="PLT001-L1-MXR",
        timestamp=FAIL_AT_H,
        failure_mode="bearing wear",
        severity=4,
        mttr_hours=6.0,
        requires_spare_part=True,
    )

    # 1 reading/hour per sensor — fast enough for a demo over 240 h
    ss = SensorStream(plant, "PLT-001-L1", sample_rate_hz=1.0 / 3600.0)
    raw = ss.stream(duration_seconds=FAIL_AT_H * 3600.0)
    enriched = inject_signatures(raw, [ev], rng=random.Random(42))

    # Collect hourly VIB readings
    vib: dict[int, float] = {}
    for batch in enriched:
        for r in batch:
            if "MXR" in r["tag"] and "VIB" in r["tag"]:
                hr = int(r["timestamp"] / 3600)
                vib[hr] = r["value"]

    # Print trend table — every 24 h plus the last 48 h
    hours = sorted(vib)
    show = set(range(0, int(FAIL_AT_H), 24)) | set(hours[-48:])
    max_v = max(vib.values())

    print(f"\nBearing failure — PLT001-L1-MXR VIB trend (failure at {FAIL_AT_H:.0f} h)\n")
    print(f"{'Hour':>5}  {'VIB mm/s':>10}  Trend")
    print("-" * 55)
    for hr in [h for h in hours if h in show]:
        v = vib[hr]
        bar = "█" * max(1, int(30 * v / max_v))
        flag = "  ← SPIKE" if hr >= FAIL_AT_H - 48 and v > 5.0 else ""
        print(f"{hr:>5}  {v:>10.3f}  {bar}{flag}")

    # Sanity check: last-quarter VIB mean > first-quarter VIB mean
    q1 = [vib[h] for h in hours[: len(hours) // 4]]
    q4 = [vib[h] for h in hours[-len(hours) // 4 :]]
    assert sum(q4) / len(q4) > sum(q1) / len(q1), "VIB should ramp toward failure"
    print("\nPASS — VIB ramps up correctly across bearing failure window")
