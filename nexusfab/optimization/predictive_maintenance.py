"""Predictive maintenance engine — Isolation Forest anomaly detection + Weibull RUL.

Pipeline per equipment:
    sensor window (1h) → feature extraction → IsolationForest score
    → health index [0,1] → Weibull RUL (hrs) → alert level
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from sklearn.ensemble import IsolationForest

from nexusfab.seed.plants import PLANTS, EquipmentSeed, LineSeed, PlantSeed, get_plant

AlertLevel = Literal["GREEN", "YELLOW", "ORANGE", "RED"]

# Alert thresholds in hours (§4 of task spec)
_ALERT_HOURS: list[tuple[float, AlertLevel]] = [
    (168.0, "GREEN"),
    (72.0,  "YELLOW"),
    (24.0,  "ORANGE"),
    (0.0,   "RED"),
]


def _alert_level(rul_hours: float) -> AlertLevel:
    for threshold, level in _ALERT_HOURS:
        if rul_hours > threshold:
            return level
    return "RED"


# ── Feature extraction ────────────────────────────────────────────────────────

def _slope(arr: np.ndarray) -> float:
    """OLS slope — rate of change across the window."""
    n = len(arr)
    x = np.arange(n, dtype=float)
    xm, ym = x.mean(), arr.mean()
    denom = np.sum((x - xm) ** 2)
    return float(np.sum((x - xm) * (arr - ym)) / (denom + 1e-12))


def _spectral_bands(arr: np.ndarray) -> list[float]:
    """FFT power in three bands: low/mid/high (for VIB tags only)."""
    spectrum = np.abs(np.fft.rfft(arr - arr.mean())) ** 2
    n = max(len(spectrum), 1)
    cuts = [0, max(1, n // 10), max(1, n // 4), n]
    return [float(spectrum[cuts[i]:cuts[i + 1]].sum()) for i in range(3)]


def extract_features(sensor_history: dict[str, list[float]]) -> dict[str, float]:
    """Compute ~6-9 features per sensor tag from a rolling 1h window.

    Args:
        sensor_history: tag → list[float] (≥ 2 samples; any resolution).

    Returns:
        Flat feature dict keyed by ``<tag>_<stat>``.
    """
    feats: dict[str, float] = {}
    for tag, values in sensor_history.items():
        arr = np.array(values, dtype=float)
        if len(arr) < 2:
            continue
        feats[f"{tag}_mean"]  = float(arr.mean())
        feats[f"{tag}_std"]   = float(arr.std())
        feats[f"{tag}_max"]   = float(arr.max())
        feats[f"{tag}_min"]   = float(arr.min())
        feats[f"{tag}_rms"]   = float(np.sqrt(np.mean(arr ** 2)))
        feats[f"{tag}_slope"] = _slope(arr)
        if "VIB" in tag.upper():
            for i, e in enumerate(_spectral_bands(arr)):
                feats[f"{tag}_band{i}"] = e
    return feats


# ── Per-equipment PdM model ───────────────────────────────────────────────────

@dataclass
class EquipmentPdM:
    equipment_name: str
    equipment_type: str
    beta: float   # Weibull shape
    eta: float    # Weibull scale (characteristic life, hrs)

    _model: IsolationForest = field(
        default_factory=lambda: IsolationForest(
            n_estimators=100, contamination=0.05, random_state=42
        )
    )
    _feature_names: list[str] = field(default_factory=list)
    _trained: bool = field(default=False)
    _score_history: list[float] = field(default_factory=list)
    # Training distribution stats for z-score normalization.
    # Raw IF scores are stored; rolling mean is z-scored to produce
    # anomaly_score ∈ [-1, 1] with threshold at -0.5 (spec requirement).
    _score_mean: float = field(default=0.0)
    _score_std:  float = field(default=0.05)   # fallback if not trained
    _HEALTH_WINDOW: int = field(default=20, init=False)

    def train(self, windows: list[dict[str, list[float]]]) -> None:
        """Fit on normal-operation windows (first 500h recommended)."""
        rows = [extract_features(w) for w in windows]
        rows = [r for r in rows if r]
        if not rows:
            return
        self._feature_names = sorted(rows[0])
        X = np.array([[r.get(f, 0.0) for f in self._feature_names] for r in rows])
        self._model.fit(X)
        # Fit distribution of healthy scores so we can z-score later.
        train_scores = self._model.decision_function(X)
        self._score_mean = float(train_scores.mean())
        self._score_std  = float(train_scores.std() + 1e-9)
        self._trained = True
        # Seed rolling history at the healthy baseline so the first predict_rul()
        # call starts in GREEN rather than needing a warm-up period.
        self._score_history = [self._score_mean] * self._HEALTH_WINDOW

    def _raw_score(self, sensor_history: dict[str, list[float]]) -> float:
        """Raw IsolationForest decision_function score. Negative = anomalous."""
        if not self._trained or not sensor_history:
            return self._score_mean   # assume healthy baseline
        feats = extract_features(sensor_history)
        row = np.array([[feats.get(f, 0.0) for f in self._feature_names]])
        return float(self._model.decision_function(row)[0])

    def _normalized_anomaly_score(self) -> float:
        """Anomaly score ∈ [-1, 1] from rolling mean z-scored against training.

        - rolling_mean at training mean → score ≈ 0  (normal operation)
        - rolling_mean 2 std below mean → score = -1 (fully anomalous)
        - Threshold at -0.5: 1 std below training mean → schedule maintenance

        Uses rolling mean of last 20 windows to smooth out single-window noise.
        """
        if not self._score_history:
            return 0.0
        K = self._HEALTH_WINDOW
        rolling = float(np.mean(self._score_history[-K:]))
        # Scale so that ±2σ from training mean maps to ±1
        z = (rolling - self._score_mean) / (2.0 * self._score_std)
        return float(np.clip(z, -1.0, 1.0))

    @staticmethod
    def _health_from_score(anomaly_score: float) -> float:
        """Health ∈ [0, 1] from anomaly_score ∈ [-1, 1].

        Maps: -1.0 → 0.0 (failed), -0.5 → 0.33 (urgent), 0.0 → 0.67 (normal),
              0.5 → 1.0 (excellent).

        ponytail: linear map; non-linear (e.g. logistic) if false-alert rate matters.
        """
        return float(np.clip((anomaly_score + 1.0) / 1.5, 0.0, 1.0))

    def _rul_hours(self, health: float) -> float:
        """Weibull median RUL adjusted by health index.

        RUL = η_adjusted × ln(2)^(1/β),   η_adjusted = η × health_index
        """
        eta_adj = self.eta * health
        if eta_adj < 0.1:
            return 0.0
        return eta_adj * (math.log(2) ** (1.0 / self.beta))

    def predict_rul(self, sensor_history: dict[str, list[float]]) -> dict:
        """Run the full pipeline for one 1h sensor window.

        Returns:
            {equipment_name, rul_hours, health_index, anomaly_score ∈ [-1,1],
             alert_level, confidence, top_features}
        """
        raw = self._raw_score(sensor_history)
        self._score_history.append(raw)
        score_norm = self._normalized_anomaly_score()
        hi  = self._health_from_score(score_norm)
        rul = self._rul_hours(hi)
        feats = extract_features(sensor_history)
        top_feats = sorted(feats, key=lambda k: abs(feats[k]), reverse=True)[:5]
        # Confidence: stable rolling score → high; noisy → low
        recent = self._score_history[-10:]
        score_std = float(np.std(recent)) if len(recent) >= 2 else self._score_std
        confidence = float(np.clip(1.0 - score_std / (self._score_std * 10), 0.30, 0.95))
        return {
            "equipment_name": self.equipment_name,
            "equipment_type": self.equipment_type,
            "rul_hours": round(rul, 1),
            "health_index": round(hi, 3),
            "anomaly_score": round(score_norm, 4),   # ∈ [-1, 1], threshold −0.5
            "alert_level": _alert_level(rul),
            "confidence": round(confidence, 2),
            "top_features": top_feats,
        }


# ── Module-level registry and public API ─────────────────────────────────────

_registry: dict[str, EquipmentPdM] = {}


def _get_pdm(equip: EquipmentSeed) -> EquipmentPdM:
    if equip.name not in _registry:
        _registry[equip.name] = EquipmentPdM(
            equipment_name=equip.name,
            equipment_type=equip.equipment_type,
            beta=equip.weibull_beta,
            eta=equip.weibull_eta,
        )
    return _registry[equip.name]


def _find_equipment(equipment_id: str) -> EquipmentSeed | None:
    for plant in PLANTS:
        for line in plant.lines:
            for equip in line.equipment:
                if equip.name == equipment_id:
                    return equip
    return None


def predict_rul(equipment_id: str, sensor_history: dict[str, list[float]]) -> dict:
    """Predict RUL for one equipment from its current 1h sensor window.

    Args:
        equipment_id: Equipment name (e.g. ``"PLT001-L1-MXR"``).
        sensor_history: tag → list of values over the last hour.

    Returns:
        Dict with rul_hours, confidence, alert_level, top_features.
    """
    equip = _find_equipment(equipment_id)
    if equip is None:
        raise ValueError(f"Equipment {equipment_id!r} not found in plant seeds")
    return _get_pdm(equip).predict_rul(sensor_history)


def batch_predict(plant_id: str) -> list[dict]:
    """Predict RUL for every equipment in a plant.

    Uses last cached model state (no new sensor data).  Train first with
    ``_get_pdm(equip).train(windows)`` for meaningful scores.

    Args:
        plant_id: e.g. ``"PLT-001"``.

    Returns:
        List of predict_rul dicts, one per equipment, with ``line`` added.
    """
    plant = get_plant(plant_id)
    if plant is None:
        raise ValueError(f"Plant {plant_id!r} not found")
    results = []
    for line in plant.lines:
        for equip in line.equipment:
            r = _get_pdm(equip).predict_rul({})
            r["line"] = line.name
            results.append(r)
    return results


def get_maintenance_schedule(
    plant_id: str, horizon_days: int = 30
) -> list[dict]:
    """Recommended maintenance schedule for all at-risk equipment.

    Args:
        plant_id: e.g. ``"PLT-001"``.
        horizon_days: Only include equipment with RUL ≤ this window.

    Returns:
        List sorted by priority (RED first), each entry with:
        equipment_name, line, rul_hours, alert_level, scheduled_in_hours, priority.
    """
    plant = get_plant(plant_id)
    if plant is None:
        raise ValueError(f"Plant {plant_id!r} not found")
    _PRIORITY = {"RED": 1, "ORANGE": 2, "YELLOW": 3, "GREEN": 4}
    horizon_hours = horizon_days * 24
    schedule = []
    for line in plant.lines:
        for equip in line.equipment:
            r = _get_pdm(equip).predict_rul({})
            if r["rul_hours"] <= horizon_hours:
                schedule.append({
                    "equipment_name": equip.name,
                    "equipment_type": equip.equipment_type,
                    "line": line.name,
                    "rul_hours": r["rul_hours"],
                    "alert_level": r["alert_level"],
                    # ponytail: schedule at 80% RUL to give a maintenance buffer
                    "scheduled_in_hours": round(r["rul_hours"] * 0.8, 1),
                    "priority": _PRIORITY[r["alert_level"]],
                })
    return sorted(schedule, key=lambda x: x["priority"])


# ── __main__: bearing failure demo ────────────────────────────────────────────

if __name__ == "__main__":
    import random
    random.seed(0)
    np.random.seed(0)

    # Demo equipment: β=2.2, η=600h.
    # At healthy health≈0.667 (z=0 after training): RUL ≈ 348h → GREEN.
    # As anomaly score drops to -1.0 (z≤-2σ after full degradation): health→0 → RED.
    DEMO_BETA, DEMO_ETA = 2.2, 600.0
    pdm = EquipmentPdM("DEMO-MXR", "MIXER", DEMO_BETA, DEMO_ETA)

    def _window(vib_mean: float, n: int = 120) -> dict[str, list[float]]:
        """Simulate 1h of MIXER sensors. Noise is 5% of vib_mean (physical: sensor noise)."""
        sigma = max(0.15, vib_mean * 0.05)
        return {
            "VIB":  list(np.random.normal(vib_mean, sigma, n).clip(0)),
            "TEMP": list(np.random.normal(25.0 + vib_mean * 0.3, 0.5, n)),
            "PWR":  list(np.random.normal(45.0, 0.5, n)),
        }

    # ── 1. Train on 500 windows of normal operation (VIB ~ 3.0 mm/s) ─────────
    print("Training on 500h normal operation (VIB baseline = 3 mm/s)...")
    normal_windows = [_window(3.0) for _ in range(500)]
    pdm.train(normal_windows)

    # ── 2. Simulate 168h bearing failure timeline ─────────────────────────────
    # VIB escalation per §6.2 research doc:
    #   Phase 1 (h 0–79):    healthy,           VIB = 3 mm/s
    #   Phase 2 (h 80–119):  early wear,        VIB linearly rises 3 → 12 mm/s
    #   Phase 3 (h 120–154): rapid degradation, VIB linearly rises 12 → 60 mm/s
    #   Phase 4 (h 155–167): near failure,      VIB = 60–150 mm/s

    def _vib_at_hour(h: int) -> float:
        if h < 80:
            return 3.0
        if h < 120:
            return 3.0 + (12.0 - 3.0) * (h - 80) / 40
        if h < 155:
            return 12.0 + (60.0 - 12.0) * (h - 120) / 35
        return 60.0 + (150.0 - 60.0) * (h - 155) / 12

    timeline: list[dict] = []
    for h in range(168):
        vib = _vib_at_hour(h)
        result = pdm.predict_rul(_window(vib))
        result["hour"] = h
        result["vib_mm_s"] = round(vib, 1)
        timeline.append(result)

    # Print key checkpoints
    checkpoints = [0, 50, 85, 110, 125, 145, 158, 167]
    print(f"\n{'Hour':>5} {'VIB mm/s':>10} {'Score':>8} {'HI':>6} "
          f"{'RUL(h)':>8} {'Alert':>8}")
    print("-" * 58)
    for r in timeline:
        if r["hour"] in checkpoints:
            print(f"{r['hour']:>5} {r['vib_mm_s']:>10.1f} {r['anomaly_score']:>8.4f} "
                  f"{r['health_index']:>6.3f} {r['rul_hours']:>8.1f} {r['alert_level']:>8}")

    # ── 3. Verify GREEN→YELLOW→ORANGE→RED appear in that order ───────────────
    # We don't require strict monotonicity per-window (rolling mean can wobble
    # while transitioning), but FIRST appearance of each level must escalate.
    _P = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}
    first_seen: dict[str, int] = {}
    for r in timeline:
        al = r["alert_level"]
        if al not in first_seen:
            first_seen[al] = r["hour"]

    missing = {"GREEN", "YELLOW", "ORANGE", "RED"} - first_seen.keys()
    assert not missing, f"Never saw alert level(s): {missing} in 168h timeline"

    order = sorted(first_seen, key=lambda x: first_seen[x])
    assert order == ["GREEN", "YELLOW", "ORANGE", "RED"], (
        f"Alert levels first appeared out of order: {order}\n"
        f"  first_seen hours: {first_seen}"
    )

    print(f"\nFirst seen: " + "  ".join(
        f"{al}@h{first_seen[al]}" for al in ["GREEN", "YELLOW", "ORANGE", "RED"]
    ))
    print("PASS — GREEN→YELLOW→ORANGE→RED transitions match bearing failure timeline.")

    # ── 3. Spot-check batch API on PLT-001 (untrained = baseline estimates) ──
    results = batch_predict("PLT-001")
    print(f"\nbatch_predict('PLT-001'): {len(results)} equipment, "
          f"all at baseline health (untrained)")
    for r in results[:3]:
        print(f"  {r['equipment_name']}: RUL={r['rul_hours']}h  {r['alert_level']}")

    sched = get_maintenance_schedule("PLT-001", horizon_days=30)
    print(f"\nget_maintenance_schedule (30d): {len(sched)} items need attention")
