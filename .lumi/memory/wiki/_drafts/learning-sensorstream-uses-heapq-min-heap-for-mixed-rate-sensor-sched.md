---
created_at: 2026-07-23T16:12:29.990290+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: SensorStream uses heapq min-heap for mixed-rate sensor scheduling
source: memory_save_learning
---
# SensorStream uses heapq min-heap for mixed-rate sensor scheduling

In `nexusfab/simulation/sensor_stream.py`, the `SensorStream.stream()` method schedules sensor firings with a min-heap `(next_fire_time, sensor_index)` — the same pattern used in `nexusfab/simulation/failure_generator.py`. This correctly handles mixed sample rates (vibration at 10 Hz, all others at 1 Hz) in O(n_readings × log(n_sensors)) instead of a naïve O(n_readings × n_sensors) scan.

**Key design decisions:**

- `_TYPE_MAP` maps seed `equipment_type` strings (e.g. `"DRYER"`, `"PASTEURIZER"`) to sensor-set keys (`"EXTRUDER"`, `"UHT"`). PLT-001-L1's CAPPER and LABELER — not in the task's sensor-set spec — fall back to `"CONVEYOR"` (speed/vibration/power). Adding a new equipment type requires only a one-line entry in `_TYPE_MAP`.

- Degradation uses two physics rules anchored in the task spec: vibration drift +0.1 mm/s per 100h past 70% η, temperature drift +0.2°C per 100h. The drift is applied as an additive offset to `spec.setpoint` before sampling `random.gauss`, so noise and drift compose naturally.

- Quality (`GOOD` / `UNCERTAIN` / `BAD`) is determined solely by `age / weibull_eta` thresholds (0.70 and 0.90), not by reading value — this mirrors OPC-UA quality codes (sensor health, not measurement range).

- `_abs()` and `_pct()` builder functions keep the sensor-spec tables readable as two-column data; `_pct` converts percent noise to absolute sigma at definition time so `_SensorSpec.sigma` is always absolute.

PLT-001-L1 produces 14 tags and ~147,600 readings per hour (3 VIB sensors × 36,000 + 11 slow sensors × 3,600).
