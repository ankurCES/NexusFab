"""Preventive maintenance scheduler.

Generates PM schedules based on equipment MTBF, usage hours,
and maintenance intervals. Prioritizes by criticality and
failure probability.
"""

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


@dataclass
class MaintenanceAction:
    equipment_name: str
    equipment_type: str
    plant_id: str
    line_name: str
    action_type: str  # "PM" | "INSPECTION"
    scheduled_date: datetime
    estimated_duration_hours: float
    estimated_cost: float
    priority: int  # 1=low, 2=medium, 3=high, 4=critical
    failure_probability: float
    days_until_due: float

    def to_dict(self) -> dict:
        return {
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

    if days_until_pm <= horizon_days:
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
            priority=priority,
            failure_probability=fail_prob,
            days_until_due=days_until_pm,
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


if __name__ == "__main__":
    sched = generate_maintenance_schedule("PLT-001", horizon_days=30)
    d = sched.to_dict()
    print(f"PLT-001: {d['total_actions']} actions, ${d['total_cost']:,.0f}, {d['total_hours']:.0f}h")
    print(f"Priority: {d['by_priority']}")
    assert d['total_actions'] > 0
    assert d['total_cost'] > 0

    all_sched = generate_maintenance_schedule(horizon_days=14)
    print(f"All plants (14d): {all_sched.to_dict()['total_actions']} actions")
    assert all_sched.to_dict()['total_actions'] > sched.to_dict()['total_actions']
    print("PASS")
