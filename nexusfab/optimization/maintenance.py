"""Preventive maintenance scheduler.

Generates PM schedules based on equipment MTBF, usage hours,
and maintenance intervals. Prioritizes by criticality and
failure probability. Includes predictive condition triggers
(vibration ISO 10816, temperature anomaly, current deviation)
and PM grouping to minimize total line downtime.
"""

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nexusfab.seed.plants import PLANTS, EquipmentSeed, get_plant

# Maintenance interval multipliers (fraction of MTBF)
_PM_INTERVAL_FACTOR = 0.7  # schedule PM at 70% of MTBF
_INSPECTION_INTERVAL_FACTOR = 0.3  # inspect at 30% of MTBF

# Cost per maintenance type ($/event)
_PM_COSTS = {
    "FILLER": 2500.0,
    "CAPPER": 1200.0,
    "LABELER": 800.0,
    "CONVEYOR": 600.0,
    "MIXER": 3000.0,
    "PACKAGING": 1500.0,
    "PASTEURIZER": 4000.0,
    "HOMOGENIZER": 3500.0,
    "DRYER": 2800.0,
}

_INSPECTION_COST_FACTOR = 0.15  # inspection = 15% of PM cost

# ── ISO 10816 vibration thresholds (mm/s RMS) ──
# ponytail: Class II for small equip, Class III for large. Two tiers covers the fleet.
_VIBRATION_THRESHOLDS: dict[str, tuple[float, float]] = {
    # (warning, critical) — "unsatisfactory" and "unacceptable" zones
    "FILLER":       (2.8, 7.1),   # Class II
    "CAPPER":       (2.8, 7.1),
    "LABELER":      (2.8, 7.1),
    "CONVEYOR":     (4.5, 11.2),  # Class III — large rigid
    "MIXER":        (4.5, 11.2),
    "PACKAGING":    (2.8, 7.1),
    "PASTEURIZER":  (4.5, 11.2),
    "HOMOGENIZER":  (4.5, 11.2),
    "DRYER":        (4.5, 11.2),
}

# Temperature: flag if bearing temp exceeds baseline + delta (°C)
_TEMP_WARNING_DELTA = 15.0
_TEMP_CRITICAL_DELTA = 30.0
_TEMP_BASELINES: dict[str, float] = {
    "FILLER": 45.0, "CAPPER": 40.0, "LABELER": 38.0, "CONVEYOR": 42.0,
    "MIXER": 55.0, "PACKAGING": 40.0, "PASTEURIZER": 85.0,
    "HOMOGENIZER": 65.0, "DRYER": 75.0,
}

# Motor current: flag if drawn current deviates from rated by this fraction
_CURRENT_WARNING_PCT = 0.15
_CURRENT_CRITICAL_PCT = 0.30


@dataclass
class ConditionTrigger:
    sensor: str  # "vibration" | "temperature" | "current"
    value: float
    threshold: float
    severity: str  # "warning" | "critical"
    unit: str

    def to_dict(self) -> dict:
        return {
            "sensor": self.sensor,
            "value": round(self.value, 2),
            "threshold": round(self.threshold, 2),
            "severity": self.severity,
            "unit": self.unit,
        }


def _deterministic_float(name: str, hours: float, salt: str, lo: float, hi: float) -> float:
    """Deterministic pseudo-random float from equipment name + hours. No randomness."""
    h = hashlib.md5(f"{name}:{hours:.1f}:{salt}".encode()).hexdigest()
    frac = int(h[:8], 16) / 0xFFFFFFFF
    return lo + frac * (hi - lo)


def simulate_condition(eq: EquipmentSeed, hours_since_pm: float) -> list[ConditionTrigger]:
    """Simulate sensor readings. Readings degrade as usage approaches MTBF."""
    triggers: list[ConditionTrigger] = []
    wear = hours_since_pm / eq.mtbf_hours  # 0→fresh, 1→at MTBF

    # Vibration (ISO 10816)
    warn_t, crit_t = _VIBRATION_THRESHOLDS.get(eq.equipment_type, (2.8, 7.1))
    base_vib = warn_t * 0.3
    vib = base_vib + (crit_t - base_vib) * wear ** 1.5
    vib += _deterministic_float(eq.name, hours_since_pm, "vib", -0.3, 0.3)
    if vib >= crit_t:
        triggers.append(ConditionTrigger("vibration", vib, crit_t, "critical", "mm/s RMS"))
    elif vib >= warn_t:
        triggers.append(ConditionTrigger("vibration", vib, warn_t, "warning", "mm/s RMS"))

    # Temperature
    baseline = _TEMP_BASELINES.get(eq.equipment_type, 45.0)
    temp = baseline + _TEMP_CRITICAL_DELTA * wear ** 1.8
    temp += _deterministic_float(eq.name, hours_since_pm, "temp", -2.0, 2.0)
    if temp >= baseline + _TEMP_CRITICAL_DELTA:
        triggers.append(ConditionTrigger("temperature", temp, baseline + _TEMP_CRITICAL_DELTA, "critical", "°C"))
    elif temp >= baseline + _TEMP_WARNING_DELTA:
        triggers.append(ConditionTrigger("temperature", temp, baseline + _TEMP_WARNING_DELTA, "warning", "°C"))

    # Current deviation
    rated_current = 10.0 + eq.mttr_hours * 2  # ponytail: synthetic rated amps from repair complexity
    current = rated_current * (1.0 + 0.4 * wear ** 2)
    current += _deterministic_float(eq.name, hours_since_pm, "cur", -0.2, 0.2)
    dev = abs(current - rated_current) / rated_current
    if dev >= _CURRENT_CRITICAL_PCT:
        triggers.append(ConditionTrigger("current", current, rated_current * (1 + _CURRENT_CRITICAL_PCT), "critical", "A"))
    elif dev >= _CURRENT_WARNING_PCT:
        triggers.append(ConditionTrigger("current", current, rated_current * (1 + _CURRENT_WARNING_PCT), "warning", "A"))

    return triggers


@dataclass
class MaintenanceAction:
    equipment_name: str
    equipment_type: str
    plant_id: str
    line_name: str
    action_type: str  # "PM" | "INSPECTION" | "CONDITION_BASED"
    scheduled_date: datetime
    estimated_duration_hours: float
    estimated_cost: float
    priority: int  # 1=low, 2=medium, 3=high, 4=critical
    failure_probability: float
    days_until_due: float
    condition_triggers: list[ConditionTrigger] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "equipment": self.equipment_name,
            "type": self.equipment_type,
            "plant_id": self.plant_id,
            "line": self.line_name,
            "action": self.action_type,
            "scheduled": self.scheduled_date.isoformat(),
            "duration_hours": round(self.estimated_duration_hours, 1),
            "cost": round(self.estimated_cost, 2),
            "priority": self.priority,
            "failure_prob": round(self.failure_probability, 4),
            "days_until_due": round(self.days_until_due, 1),
        }
        if self.condition_triggers:
            d["condition_triggers"] = [t.to_dict() for t in self.condition_triggers]
        return d


@dataclass
class MaintenanceSchedule:
    plant_id: str | None
    horizon_days: int
    actions: list[MaintenanceAction] = field(default_factory=list)
    total_cost: float = 0.0
    total_hours: float = 0.0

    def to_dict(self) -> dict:
        by_priority = {}
        for a in self.actions:
            by_priority.setdefault(a.priority, []).append(a)
        return {
            "plant_id": self.plant_id or "all",
            "horizon_days": self.horizon_days,
            "total_actions": len(self.actions),
            "total_cost": round(self.total_cost, 2),
            "total_hours": round(self.total_hours, 1),
            "by_priority": {
                k: len(v) for k, v in sorted(by_priority.items(), reverse=True)
            },
            "actions": [a.to_dict() for a in self.actions],
        }


def _failure_probability(hours_since_pm: float, mtbf: float, shape: float = 2.0) -> float:
    """Weibull CDF: probability of failure by `hours_since_pm`."""
    scale = mtbf / math.gamma(1 + 1 / shape)
    return 1 - math.exp(-((hours_since_pm / scale) ** shape))


def _priority_from_failure_prob(prob: float) -> int:
    if prob >= 0.8:
        return 4
    if prob >= 0.5:
        return 3
    if prob >= 0.2:
        return 2
    return 1


def generate_maintenance_schedule(
    plant_id: str | None = None,
    horizon_days: int = 30,
    current_date: datetime | None = None,
    usage_hours: dict[str, float] | None = None,
) -> MaintenanceSchedule:
    """Generate PM schedule for one plant or all plants."""
    if current_date is None:
        current_date = datetime(2026, 7, 23, 0, 0, 0)

    if usage_hours is None:
        usage_hours = {}

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    schedule = MaintenanceSchedule(plant_id=plant_id, horizon_days=horizon_days)

    for plant in plants:
        for line in plant.lines:
            for eq in line.equipment:
                _schedule_equipment(
                    schedule, eq, plant.id, line.name,
                    current_date, horizon_days,
                    usage_hours.get(eq.name, eq.mtbf_hours * 0.5),
                )

    schedule.actions.sort(key=lambda a: (-a.priority, a.scheduled_date))
    schedule.total_cost = sum(a.estimated_cost for a in schedule.actions)
    schedule.total_hours = sum(a.estimated_duration_hours for a in schedule.actions)
    return schedule


def _schedule_equipment(
    schedule: MaintenanceSchedule,
    eq: EquipmentSeed,
    plant_id: str,
    line_name: str,
    current_date: datetime,
    horizon_days: int,
    hours_since_last_pm: float,
):
    pm_interval = eq.mtbf_hours * _PM_INTERVAL_FACTOR
    inspection_interval = eq.mtbf_hours * _INSPECTION_INTERVAL_FACTOR

    pm_cost = _PM_COSTS.get(eq.equipment_type, 1500.0)
    pm_duration = eq.mttr_hours * 1.5  # PM takes ~1.5x repair time

    # Hours until next PM
    hours_until_pm = max(0, pm_interval - hours_since_last_pm)
    days_until_pm = hours_until_pm / 24.0

    # Failure probability at current usage
    fail_prob = _failure_probability(hours_since_last_pm, eq.mtbf_hours)
    priority = _priority_from_failure_prob(fail_prob)

    # Condition triggers — predictive maintenance signals
    triggers = simulate_condition(eq, hours_since_last_pm)
    has_critical = any(t.severity == "critical" for t in triggers)

    if has_critical:
        # Condition-based action: schedule immediately when critical trigger fires
        schedule.actions.append(MaintenanceAction(
            equipment_name=eq.name,
            equipment_type=eq.equipment_type,
            plant_id=plant_id,
            line_name=line_name,
            action_type="CONDITION_BASED",
            scheduled_date=current_date + timedelta(hours=4),
            estimated_duration_hours=pm_duration,
            estimated_cost=pm_cost * 1.2,  # urgent premium
            priority=4,
            failure_probability=fail_prob,
            days_until_due=0.17,
            condition_triggers=triggers,
        ))
    elif days_until_pm <= horizon_days:
        pm_date = current_date + timedelta(hours=hours_until_pm)
        schedule.actions.append(MaintenanceAction(
            equipment_name=eq.name,
            equipment_type=eq.equipment_type,
            plant_id=plant_id,
            line_name=line_name,
            action_type="PM",
            scheduled_date=pm_date,
            estimated_duration_hours=pm_duration,
            estimated_cost=pm_cost,
            priority=max(priority, 3) if triggers else priority,
            failure_probability=fail_prob,
            days_until_due=days_until_pm,
            condition_triggers=triggers,
        ))

    # Schedule inspections
    hours_until_inspection = max(0, inspection_interval - (hours_since_last_pm % inspection_interval))
    insp_date = current_date + timedelta(hours=hours_until_inspection)
    while insp_date < current_date + timedelta(days=horizon_days):
        if abs((insp_date - current_date).total_seconds() / 3600 - hours_until_pm) > 24:
            schedule.actions.append(MaintenanceAction(
                equipment_name=eq.name,
                equipment_type=eq.equipment_type,
                plant_id=plant_id,
                line_name=line_name,
                action_type="INSPECTION",
                scheduled_date=insp_date,
                estimated_duration_hours=pm_duration * 0.3,
                estimated_cost=pm_cost * _INSPECTION_COST_FACTOR,
                priority=max(1, priority - 1),
                failure_probability=fail_prob,
                days_until_due=(insp_date - current_date).days,
            ))
        insp_date += timedelta(hours=inspection_interval)


# ── PM Grouping Optimizer ──
# When a line must go down for one PM, pull forward nearby PMs on the same line
# to share the downtime window. Reduces total distinct downtime events.

_GROUP_PULL_FORWARD_DAYS = 7.0  # pull PM forward if within this window


@dataclass
class PMGroup:
    line_name: str
    plant_id: str
    window_start: datetime
    window_end: datetime
    actions: list[MaintenanceAction] = field(default_factory=list)
    total_duration_hours: float = 0.0
    total_cost: float = 0.0
    downtime_saved_hours: float = 0.0

    def to_dict(self) -> dict:
        return {
            "line": self.line_name,
            "plant_id": self.plant_id,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "tasks": [a.to_dict() for a in self.actions],
            "total_duration_hours": round(self.total_duration_hours, 1),
            "total_cost": round(self.total_cost, 2),
            "downtime_saved_hours": round(self.downtime_saved_hours, 1),
        }


@dataclass
class OptimizedSchedule:
    plant_id: str | None
    horizon_days: int
    groups: list[PMGroup] = field(default_factory=list)
    ungrouped: list[MaintenanceAction] = field(default_factory=list)
    total_downtime_hours_before: float = 0.0
    total_downtime_hours_after: float = 0.0
    downtime_reduction_pct: float = 0.0

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id or "all",
            "horizon_days": self.horizon_days,
            "groups": [g.to_dict() for g in self.groups],
            "ungrouped_count": len(self.ungrouped),
            "total_downtime_before_hours": round(self.total_downtime_hours_before, 1),
            "total_downtime_after_hours": round(self.total_downtime_hours_after, 1),
            "downtime_reduction_pct": round(self.downtime_reduction_pct, 1),
        }


def optimize_maintenance_groups(
    plant_id: str | None = None,
    horizon_days: int = 30,
    current_date: datetime | None = None,
    usage_hours: dict[str, float] | None = None,
    pull_forward_days: float = _GROUP_PULL_FORWARD_DAYS,
) -> OptimizedSchedule:
    """Generate PM schedule then group tasks on the same line to minimize downtime windows.

    For each line, the earliest PM/CONDITION_BASED action anchors a group. Other
    actions on the same line within `pull_forward_days` get pulled into that window.
    Parallel work during one downtime = less total downtime than serial stops.
    """
    schedule = generate_maintenance_schedule(
        plant_id=plant_id, horizon_days=horizon_days,
        current_date=current_date, usage_hours=usage_hours,
    )

    # Separate PM/CONDITION_BASED (groupable) from INSPECTION (ungrouped)
    groupable = [a for a in schedule.actions if a.action_type in ("PM", "CONDITION_BASED")]
    inspections = [a for a in schedule.actions if a.action_type == "INSPECTION"]

    # Group by line
    by_line: dict[str, list[MaintenanceAction]] = {}
    for a in groupable:
        by_line.setdefault(a.line_name, []).append(a)

    result = OptimizedSchedule(plant_id=plant_id, horizon_days=horizon_days)
    result.ungrouped = inspections

    # Before: each PM is its own downtime event (line startup/shutdown overhead = 1h each)
    startup_overhead = 1.0
    total_before = sum(a.estimated_duration_hours + startup_overhead for a in groupable)

    total_after = 0.0
    for line_name, actions in by_line.items():
        actions.sort(key=lambda a: a.scheduled_date)

        # Greedy grouping: anchor on earliest, pull forward anything within window
        remaining = list(actions)
        while remaining:
            anchor = remaining.pop(0)
            group = PMGroup(
                line_name=line_name,
                plant_id=anchor.plant_id,
                window_start=anchor.scheduled_date,
                window_end=anchor.scheduled_date + timedelta(hours=anchor.estimated_duration_hours),
                actions=[anchor],
                total_duration_hours=anchor.estimated_duration_hours,
                total_cost=anchor.estimated_cost,
            )

            pulled = []
            still_remaining = []
            for a in remaining:
                gap_days = (a.scheduled_date - anchor.scheduled_date).total_seconds() / 86400
                if gap_days <= pull_forward_days:
                    pulled.append(a)
                else:
                    still_remaining.append(a)
            remaining = still_remaining

            for a in pulled:
                group.actions.append(a)
                group.total_cost += a.estimated_cost
                # Parallel work: max duration, not sum (techs work simultaneously)
                group.total_duration_hours = max(
                    group.total_duration_hours, a.estimated_duration_hours
                )
            group.window_end = group.window_start + timedelta(hours=group.total_duration_hours)

            # Downtime saved = what we avoided by not stopping the line N separate times
            individual_hours = sum(a.estimated_duration_hours + startup_overhead for a in group.actions)
            grouped_hours = group.total_duration_hours + startup_overhead
            group.downtime_saved_hours = individual_hours - grouped_hours

            total_after += grouped_hours
            result.groups.append(group)

    result.total_downtime_hours_before = total_before
    result.total_downtime_hours_after = total_after
    if total_before > 0:
        result.downtime_reduction_pct = (1 - total_after / total_before) * 100

    return result


if __name__ == "__main__":
    # Basic schedule check
    sched = generate_maintenance_schedule("PLT-001", horizon_days=30)
    d = sched.to_dict()
    print(f"PLT-001: {d['total_actions']} actions, ${d['total_cost']:,.0f}, {d['total_hours']:.0f}h")
    print(f"Priority: {d['by_priority']}")
    assert d['total_actions'] > 0
    assert d['total_cost'] > 0

    all_sched = generate_maintenance_schedule(horizon_days=14)
    print(f"All plants (14d): {all_sched.to_dict()['total_actions']} actions")
    assert all_sched.to_dict()['total_actions'] > sched.to_dict()['total_actions']

    # Condition triggers check
    cond_actions = [a for a in sched.actions if a.condition_triggers]
    print(f"Actions with condition triggers: {len(cond_actions)}")
    cb_actions = [a for a in sched.actions if a.action_type == "CONDITION_BASED"]
    print(f"Condition-based urgent actions: {len(cb_actions)}")
    for a in cb_actions[:3]:
        trigs = ", ".join(f"{t.sensor}={t.value:.1f}{t.unit} ({t.severity})" for t in a.condition_triggers)
        print(f"  {a.equipment_name}: {trigs}")

    # Optimization / grouping check
    opt = optimize_maintenance_groups("PLT-001", horizon_days=30)
    od = opt.to_dict()
    print(f"\nOptimized PLT-001:")
    print(f"  Groups: {len(od['groups'])}")
    print(f"  Downtime before: {od['total_downtime_before_hours']}h")
    print(f"  Downtime after:  {od['total_downtime_after_hours']}h")
    print(f"  Reduction:       {od['downtime_reduction_pct']}%")
    assert od['downtime_reduction_pct'] > 0, "Grouping should reduce downtime"
    for g in od['groups'][:3]:
        print(f"  [{g['line']}] {len(g['tasks'])} tasks, {g['total_duration_hours']}h, saved {g['downtime_saved_hours']}h")

    print("\nPASS")
