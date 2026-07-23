"""Weibull-based equipment failure event generator."""

from __future__ import annotations

import heapq
import random
from dataclasses import dataclass
from typing import Iterator

from nexusfab.seed.plants import EquipmentSeed


# Failure modes — docs/research/maintenance-spare-parts.md §2
# Cumulative weights for weighted random selection.
_FAILURE_MODES: dict[str, list[tuple[str, float]]] = {
    "FILLER":      [("seal wear", .40), ("valve leak", .65), ("motor burnout", .80), ("sensor drift", 1.0)],
    "PASTEURIZER": [("tube fouling", .35), ("gasket failure", .60), ("pump cavitation", .80), ("control fault", 1.0)],
    "HOMOGENIZER": [("tube fouling", .35), ("gasket failure", .60), ("pump cavitation", .80), ("control fault", 1.0)],
    "MIXER":       [("bearing wear", .30), ("seal failure", .55), ("blade erosion", .80), ("gearbox", 1.0)],
    "DRYER":       [("screw wear", .30), ("barrel erosion", .55), ("heater failure", .80), ("die blockage", 1.0)],
    "CONVEYOR":    [("belt tracking", .35), ("roller bearing", .65), ("chain stretch", .85), ("motor", 1.0)],
    "CAPPER":      [("seal wear", .40), ("valve leak", .65), ("motor burnout", .80), ("sensor drift", 1.0)],
    "LABELER":     [("belt tracking", .35), ("roller bearing", .65), ("chain stretch", .85), ("motor", 1.0)],
    "PACKAGING":   [("bearing wear", .30), ("seal failure", .55), ("motor burnout", .80), ("sensor drift", 1.0)],
    "CIP_SKID":    [("valve sticking", .30), ("pump wear", .55), ("instrument drift", .80), ("heating element", 1.0)],
}
_DEFAULT_MODES = [("mechanical failure", .50), ("sensor drift", 1.0)]


def _pick_mode(etype: str) -> str:
    modes = _FAILURE_MODES.get(etype.upper(), _DEFAULT_MODES)
    r = random.random()
    for mode, cum in modes:
        if r <= cum:
            return mode
    return modes[-1][0]


def _pick_severity() -> int:
    """60% minor(1-2), 30% moderate(3), 10% critical(4-5)."""
    r = random.random()
    if r < 0.60:
        return random.randint(1, 2)
    if r < 0.90:
        return 3
    return random.randint(4, 5)


@dataclass
class FailureEvent:
    equipment_id: str
    timestamp: float        # hours from simulation start
    failure_mode: str
    severity: int           # 1–5
    mttr_hours: float
    requires_spare_part: bool


class FailureGenerator:
    """Yields FailureEvent objects in chronological order across all equipment.

    Usage:
        gen = FailureGenerator(equipment_list)
        for event in gen.generate(duration_hours=8760):
            process(event)
    """

    def __init__(
        self,
        equipment: list[EquipmentSeed],
        equipment_ids: list[str] | None = None,
    ) -> None:
        self._equip = equipment
        # ponytail: default IDs to names — caller overrides for UUID-keyed DBs
        self._ids = equipment_ids if equipment_ids is not None else [e.name for e in equipment]

    def generate(self, duration_hours: float, start_time: float = 0.0) -> Iterator[FailureEvent]:
        """Yield failure events in time order for [start_time, start_time + duration_hours)."""
        # Min-heap: (absolute_timestamp, equipment_index)
        heap: list[tuple[float, int]] = []
        for i, eq in enumerate(self._equip):
            t = start_time + eq.weibull_eta * random.weibullvariate(1, eq.weibull_beta)
            heapq.heappush(heap, (t, i))

        end = start_time + duration_hours
        while heap:
            t, i = heapq.heappop(heap)
            if t >= end:
                break
            eq = self._equip[i]
            sev = _pick_severity()
            # MTTR scales with severity: minor→0.75×, moderate→1.25×, critical→1.75×
            mttr = round(eq.mttr_hours * (0.5 + 0.25 * sev), 2)
            yield FailureEvent(
                equipment_id=self._ids[i],
                timestamp=round(t, 3),
                failure_mode=_pick_mode(eq.equipment_type),
                severity=sev,
                mttr_hours=mttr,
                requires_spare_part=sev >= 3,
            )
            # Renewal: next failure scheduled from repair completion
            next_t = t + mttr + eq.weibull_eta * random.weibullvariate(1, eq.weibull_beta)
            heapq.heappush(heap, (next_t, i))


if __name__ == "__main__":
    from collections import defaultdict
    from nexusfab.seed.plants import get_plant

    random.seed(42)
    plant = get_plant("PLT-001")
    assert plant, "PLT-001 not found in seed data"

    all_equip: list[EquipmentSeed] = [eq for line in plant.lines for eq in line.equipment]
    gen = FailureGenerator(all_equip)

    DURATION = 1000.0
    events = list(gen.generate(DURATION))

    # Failure rate by equipment type
    counts_by_type: dict[str, int] = defaultdict(int)
    for ev in events:
        idx = next(i for i, e in enumerate(all_equip) if e.name == ev.equipment_id)
        counts_by_type[all_equip[idx].equipment_type] += 1

    print(f"\nPLT-001 — {len(events)} failure events over {DURATION:.0f}h\n")
    print(f"{'Type':<14} {'Count':>6} {'Rate/1000h':>12}")
    print("-" * 36)
    for etype, cnt in sorted(counts_by_type.items()):
        print(f"{etype:<14} {cnt:>6} {cnt / DURATION * 1000:>12.1f}")

    # Verify β>1 equipment shows increasing hazard: failures/500h in second half > first half
    print("\nIncreasing-failure-rate check (β > 1 → 2nd-half rate > 1st-half rate):")
    mid = DURATION / 2
    for eq in all_equip:
        if eq.weibull_beta <= 1.0:
            continue
        first  = sum(1 for ev in events if ev.equipment_id == eq.name and ev.timestamp < mid)
        second = sum(1 for ev in events if ev.equipment_id == eq.name and ev.timestamp >= mid)
        arrow = "OK" if second >= first else "WARN"
        print(f"  {eq.name:22s} β={eq.weibull_beta:.1f}  first={first:3d}  second={second:3d}  [{arrow}]")

    warn_count = sum(
        1 for eq in all_equip if eq.weibull_beta > 1.0 and
        sum(1 for ev in events if ev.equipment_id == eq.name and ev.timestamp >= mid) <
        sum(1 for ev in events if ev.equipment_id == eq.name and ev.timestamp < mid)
    )
    # Statistical note: with few events, stochastic variance can flip the check on single runs.
    # Use seed=42 + 1000h; most β>1 equipment should show second ≥ first.
    total_beta_gt1 = sum(1 for eq in all_equip if eq.weibull_beta > 1.0)
    print(f"\n{total_beta_gt1 - warn_count}/{total_beta_gt1} β>1 equipment show increasing failure rate")
    assert warn_count <= total_beta_gt1 // 2, (
        f"Too many β>1 equipment NOT showing wear-out trend ({warn_count}/{total_beta_gt1})"
    )
    print("PASS")
