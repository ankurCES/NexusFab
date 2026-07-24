---
created_at: 2026-07-23T16:18:14.097444+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: FILLER equipment has no VIB tag — use MIXER for bearing PdM demos
source: memory_save_learning
---
# FILLER equipment has no VIB tag — use MIXER for bearing PdM demos

In `nexusfab/simulation/sensor_stream.py`, `_SENSOR_SETS["FILLER"]` only has FLOW, PRES, TEMP, SPD — **no VIB sensor**. MIXER (`_SENSOR_SETS["MIXER"]`) has VIB at 10 Hz.

When wiring up `failure_signatures.py`'s bearing signature (which injects on tag pattern `"VIB"`), any `FailureEvent` targeting a FILLER equipment_id will silently no-op on the VIB effect — the delta loop finds no matching tags and skips it. The TEMP effect does fire on FILLER.

For bearing/vibration PdM demos on PLT-001-L1, target `PLT001-L1-MXR` (MIXER), not `PLT001-L1-FIL`. The MIXER's `_FAILURE_MODES` entry includes `"bearing wear"` which is the keyword the bearing `FailureSignature` matches on.

This also applies to any PdM pipeline that feeds `inject_signatures`: validate that the target equipment's sensor set contains tags matching the signature's `tag_pattern` before assuming injection will fire. A future improvement would be to emit a warning when an active window finds no matching tags on its equipment, surfacing misconfiguration instead of silent no-ops.

Key files:
- `nexusfab/simulation/sensor_stream.py`: `_SENSOR_SETS` — equipment-type → sensor list
- `nexusfab/simulation/failure_signatures.py`: `SensorEffect.tag_pattern` matching in `inject_signatures()`
- `nexusfab/seed/plants.py`: PLT-001-L1 equipment list (MXR at position 1, FIL at position 2)
