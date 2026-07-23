"""Shift pattern simulation for workforce scheduling.

Generates crew rosters per plant, tracks hourly operator coverage,
and flags gaps where lines can't run due to understaffing.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from nexusfab.seed.plants import get_plant


class ShiftType(str, Enum):
    DAY = "day"
    AFTERNOON = "afternoon"
    NIGHT = "night"
    DAY12 = "day12"
    NIGHT12 = "night12"
    OFF = "off"


# (start_hour, end_hour) — end < start means overnight
SHIFT_HOURS: dict[ShiftType, tuple[int, int]] = {
    ShiftType.DAY: (6, 14),
    ShiftType.AFTERNOON: (14, 22),
    ShiftType.NIGHT: (22, 6),
    ShiftType.DAY12: (6, 18),
    ShiftType.NIGHT12: (18, 6),
}

MIN_OPERATORS_PER_LINE = 2
MIN_TECH_PER_N_LINES = 3


@dataclass
class ShiftSchedule:
    plant_id: str
    pattern: str
    crews: int
    operators_per_line: int
    tech_per_n_lines: int
    rotation_cycle: list[ShiftType]
    shift_duration_hours: int = 8
    weekend_premium: bool = False
    ot_cap_hours_per_week: int | None = None
    seasonal_flex: float = 0.0


@dataclass
class ShiftSlot:
    shift_id: str
    crew: int
    start: datetime
    end: datetime
    shift_type: ShiftType
    headcount: int
    roles: dict[str, int]


# ── Rotation cycles ──

_CYCLE_3X8 = [
    ShiftType.DAY, ShiftType.DAY,
    ShiftType.AFTERNOON, ShiftType.AFTERNOON,
    ShiftType.NIGHT, ShiftType.NIGHT,
    ShiftType.OFF, ShiftType.OFF,
]

_CYCLE_2X12 = [
    ShiftType.DAY12, ShiftType.DAY12,
    ShiftType.OFF, ShiftType.OFF,
    ShiftType.NIGHT12, ShiftType.NIGHT12,
    ShiftType.OFF, ShiftType.OFF,
]

# 5-crew variant: extra afternoon block = "swing" overlap
_CYCLE_3X8_SWING = [
    ShiftType.DAY, ShiftType.DAY,
    ShiftType.AFTERNOON, ShiftType.AFTERNOON,
    ShiftType.NIGHT, ShiftType.NIGHT,
    ShiftType.AFTERNOON, ShiftType.AFTERNOON,
    ShiftType.OFF, ShiftType.OFF,
]

_CYCLE_2X12_3CREW = [
    ShiftType.DAY12, ShiftType.DAY12,
    ShiftType.NIGHT12, ShiftType.NIGHT12,
    ShiftType.OFF, ShiftType.OFF,
]


# ── Plant-specific schedules ──

PLANT_SCHEDULES: dict[str, ShiftSchedule] = {
    # PLT-001: Water/Bev, Arlington TX — 3×8h continental, 4 crews rotating
    "PLT-001": ShiftSchedule(
        "PLT-001", "continental_3x8", crews=4,
        operators_per_line=3, tech_per_n_lines=2,
        rotation_cycle=list(_CYCLE_3X8),
    ),
    # PLT-002: Confectionery, Burlington WI — 2×12h, 3 crews, weekend premium
    "PLT-002": ShiftSchedule(
        "PLT-002", "pitman_2x12", crews=3,
        operators_per_line=3, tech_per_n_lines=3,
        rotation_cycle=list(_CYCLE_2X12_3CREW),
        shift_duration_hours=12, weekend_premium=True,
    ),
    # PLT-003: Dairy, Modesto CA — 3×8h + swing, 5 crews (UHT 24/7, Powder 5×16)
    "PLT-003": ShiftSchedule(
        "PLT-003", "continental_3x8_swing", crews=5,
        operators_per_line=4, tech_per_n_lines=2,
        rotation_cycle=list(_CYCLE_3X8_SWING),
    ),
    # PLT-004: Pet Food, Denver CO — 2×12h, 4 crews, OT cap 16h/week
    "PLT-004": ShiftSchedule(
        "PLT-004", "dupont_2x12", crews=4,
        operators_per_line=2, tech_per_n_lines=3,
        rotation_cycle=list(_CYCLE_2X12),
        shift_duration_hours=12, ot_cap_hours_per_week=16,
    ),
    # PLT-005: Prepared, Gaffney SC — 3×8h, 4 crews, seasonal flex +20% summer
    "PLT-005": ShiftSchedule(
        "PLT-005", "continental_3x8", crews=4,
        operators_per_line=2, tech_per_n_lines=3,
        rotation_cycle=list(_CYCLE_3X8),
        seasonal_flex=0.20,
    ),
}


def _line_count(plant_id: str) -> int:
    plant = get_plant(plant_id)
    return len(plant.lines) if plant else 0


def _shift_roles(schedule: ShiftSchedule, num_lines: int, month: int = 1) -> dict[str, int]:
    ops = schedule.operators_per_line * num_lines
    techs = math.ceil(num_lines / schedule.tech_per_n_lines)
    # seasonal flex: +N% headcount Jun–Aug
    if schedule.seasonal_flex and 6 <= month <= 8:
        ops = math.ceil(ops * (1 + schedule.seasonal_flex))
    return {"operators": ops, "technicians": techs, "supervisor": 1, "qa": 1}


def generate_shift_roster(
    plant_id: str,
    weeks: int = 4,
    start: datetime | None = None,
) -> list[ShiftSlot]:
    schedule = PLANT_SCHEDULES[plant_id]
    num_lines = _line_count(plant_id)

    if start is None:
        start = datetime(2026, 1, 5)  # Monday

    cycle = schedule.rotation_cycle
    cycle_len = len(cycle)
    crew_offset = cycle_len // schedule.crews

    roster: list[ShiftSlot] = []
    slot_n = 0

    for day in range(weeks * 7):
        day_date = start + timedelta(days=day)
        roles = _shift_roles(schedule, num_lines, day_date.month)
        headcount = sum(roles.values())

        for crew in range(schedule.crews):
            pos = (day + crew * crew_offset) % cycle_len
            stype = cycle[pos]
            if stype is ShiftType.OFF:
                continue

            sh, eh = SHIFT_HOURS[stype]
            s = day_date.replace(hour=sh, minute=0, second=0, microsecond=0)
            if eh < sh:
                e = (day_date + timedelta(days=1)).replace(hour=eh, minute=0, second=0, microsecond=0)
            else:
                e = day_date.replace(hour=eh, minute=0, second=0, microsecond=0)

            slot_n += 1
            roster.append(ShiftSlot(
                shift_id=f"{plant_id}-S{slot_n:04d}",
                crew=crew,
                start=s,
                end=e,
                shift_type=stype,
                headcount=headcount,
                roles=dict(roles),
            ))

    return roster


def hourly_coverage(roster: list[ShiftSlot]) -> list[dict]:
    """Operators + technicians on duty per hour across the roster span."""
    if not roster:
        return []
    t0 = min(s.start for s in roster)
    t1 = max(s.end for s in roster)
    hours = int((t1 - t0).total_seconds() // 3600)

    # ponytail: O(hours × slots) brute scan, bucket-sort if profiling flags it
    out = []
    for h in range(hours):
        t = t0 + timedelta(hours=h)
        ops = tech = 0
        for slot in roster:
            if slot.start <= t < slot.end:
                ops += slot.roles["operators"]
                tech += slot.roles["technicians"]
        out.append({"hour": h, "time": t, "operators": ops, "technicians": tech})
    return out


def find_coverage_gaps(plant_id: str, roster: list[ShiftSlot]) -> list[dict]:
    """Hours where staffing < minimum (2 ops/line + 1 tech per 3 lines)."""
    num_lines = _line_count(plant_id)
    min_ops = MIN_OPERATORS_PER_LINE * num_lines
    min_tech = math.ceil(num_lines / MIN_TECH_PER_N_LINES)

    gaps = []
    for entry in hourly_coverage(roster):
        reasons = []
        if entry["operators"] < min_ops:
            reasons.append(f"operators {entry['operators']}/{min_ops}")
        if entry["technicians"] < min_tech:
            reasons.append(f"technicians {entry['technicians']}/{min_tech}")
        if reasons:
            gaps.append({"hour": entry["hour"], "time": entry["time"], "reason": ", ".join(reasons)})
    return gaps


def available_operators_per_line_hour(
    plant_id: str, roster: list[ShiftSlot]
) -> list[tuple[datetime, float]]:
    """Operators-per-line per hour — constraint feed for SimPy runner."""
    num_lines = _line_count(plant_id)
    if num_lines == 0:
        return []
    return [(e["time"], e["operators"] / num_lines) for e in hourly_coverage(roster)]


def staffing_ok(
    plant_id: str, roster: list[ShiftSlot], sim_minutes: float, roster_start: datetime,
) -> bool:
    """Point-in-time staffing check for SimPy. True if lines can run."""
    t = roster_start + timedelta(minutes=sim_minutes)
    num_lines = _line_count(plant_id)
    min_ops = MIN_OPERATORS_PER_LINE * num_lines
    min_tech = math.ceil(num_lines / MIN_TECH_PER_N_LINES)
    ops = tech = 0
    for slot in roster:
        if slot.start <= t < slot.end:
            ops += slot.roles["operators"]
            tech += slot.roles["technicians"]
    return ops >= min_ops and tech >= min_tech


# ── Absenteeism model ──

# Day-of-week absence rates (0=Mon … 6=Sun)
_ABSENCE_RATE_DOW = [0.07, 0.04, 0.04, 0.04, 0.06, 0.03, 0.03]
_NIGHT_ABSENCE_PREMIUM = 0.015
_SEASONAL_ABSENCE_MONTHS = {11, 12, 1, 2}
_SEASONAL_ABSENCE_BONUS = 0.03


def _absence_rate(dt: datetime, is_night: bool) -> float:
    rate = _ABSENCE_RATE_DOW[dt.weekday()]
    if is_night:
        rate += _NIGHT_ABSENCE_PREMIUM
    if dt.month in _SEASONAL_ABSENCE_MONTHS:
        rate += _SEASONAL_ABSENCE_BONUS
    return rate


def apply_absenteeism(
    roster: list[ShiftSlot], rng: random.Random,
) -> tuple[list[ShiftSlot], float]:
    """Apply random absences per shift slot. Returns (modified_roster, absence_rate)."""
    total_scheduled = 0
    total_absent = 0
    result: list[ShiftSlot] = []
    for slot in roster:
        is_night = slot.shift_type in (ShiftType.NIGHT, ShiftType.NIGHT12)
        rate = _absence_rate(slot.start, is_night)
        new_roles: dict[str, int] = {}
        for role, count in slot.roles.items():
            absent = sum(1 for _ in range(count) if rng.random() < rate)
            new_roles[role] = count - absent
            total_scheduled += count
            total_absent += absent
        result.append(ShiftSlot(
            shift_id=slot.shift_id, crew=slot.crew,
            start=slot.start, end=slot.end,
            shift_type=slot.shift_type,
            headcount=sum(new_roles.values()), roles=new_roles,
        ))
    return result, total_absent / total_scheduled if total_scheduled else 0.0


# ── Fatigue model ──

def fatigue_factor(hour_in_shift: float, is_night: bool = False, consecutive_days: int = 0) -> float:
    """Performance multiplier 0.0-1.0 from shift fatigue curves."""
    if hour_in_shift <= 4:
        f = 1.00
    elif hour_in_shift <= 8:
        f = 0.98
    elif hour_in_shift <= 10:
        f = 0.93
    else:
        f = 0.85
    if is_night:
        f -= 0.03
    if consecutive_days > 5:
        f -= 0.01 * (consecutive_days - 5)
    return max(0.0, min(1.0, f))


def _consecutive_days_for_crew(roster: list[ShiftSlot], crew_id: int, current_dt: datetime) -> int:
    # ponytail: O(14 × roster) linear scan, index if profiling flags it
    d = current_dt.date() if isinstance(current_dt, datetime) else current_dt
    consec = 0
    for back in range(1, 15):
        check = d - timedelta(days=back)
        if any(s.crew == crew_id and s.start.date() == check for s in roster):
            consec += 1
        else:
            break
    return consec


# ── Workforce schedule builder ──

def build_workforce_schedule(
    plant_id: str,
    roster: list[ShiftSlot],
    roster_start: datetime,
    sim_hours: float,
) -> list[tuple[float, float]]:
    """Precompute hourly (sim_minute, workforce_factor) for SimPy integration."""
    # ponytail: O(hours × roster) brute scan, fine for ≤4-week sims
    num_lines = _line_count(plant_id)
    if num_lines == 0:
        return [(0.0, 1.0)]

    schedule: list[tuple[float, float]] = []
    for h in range(int(sim_hours) + 1):
        t_min = float(h * 60)
        t = roster_start + timedelta(hours=h)

        ops = 0
        fatigue_vals: list[float] = []
        for slot in roster:
            if slot.start <= t < slot.end:
                ops += slot.roles.get("operators", 0)
                hours_in = (t - slot.start).total_seconds() / 3600
                is_night = slot.shift_type in (ShiftType.NIGHT, ShiftType.NIGHT12)
                consec = _consecutive_days_for_crew(roster, slot.crew, t)
                fatigue_vals.append(fatigue_factor(hours_in, is_night, consec))

        ops_per_line = ops / num_lines
        avg_fatigue = sum(fatigue_vals) / len(fatigue_vals) if fatigue_vals else 1.0

        if ops_per_line < 1:
            wf = 0.0
        elif ops_per_line < MIN_OPERATORS_PER_LINE:
            wf = 0.5 * avg_fatigue
        else:
            wf = avg_fatigue

        schedule.append((t_min, wf))

    return schedule


def _roster_overtime_hours(roster: list[ShiftSlot]) -> float:
    ot = 0.0
    for slot in roster:
        shift_h = (slot.end - slot.start).total_seconds() / 3600
        if shift_h > 8:
            ot += (shift_h - 8) * slot.headcount
    return ot


def run_plant_with_workforce(
    plant_id: str,
    duration_hours: float = 168.0,
    seed: int = 42,
    line_names: list[str] | None = None,
):
    """Run plant simulation with absenteeism and fatigue effects applied."""
    from nexusfab.simulation.runner import run_plant

    rng = random.Random(seed)
    start = datetime(2026, 1, 5)
    weeks = max(1, int(duration_hours / 168))

    roster = generate_shift_roster(plant_id, weeks=weeks, start=start)
    roster_abs, absence_rate = apply_absenteeism(roster, rng)
    wf_schedule = build_workforce_schedule(plant_id, roster_abs, start, duration_hours)
    ot_hours = _roster_overtime_hours(roster_abs)

    result = run_plant(plant_id, duration_hours, seed, line_names, wf_schedule)
    result.absence_rate = absence_rate
    result.overtime_hours = ot_hours
    return result


if __name__ == "__main__":
    from nexusfab.simulation.runner import run_plant

    plant_id = "PLT-003"
    weeks = 4
    duration = weeks * 168
    seed = 42

    nominal = run_plant(plant_id, duration, seed)
    adjusted = run_plant_with_workforce(plant_id, duration, seed)

    print(f"=== PLT-003 {weeks}-week simulation ===")
    print(f"Absence rate:    {adjusted.absence_rate:.1%}")
    print(f"Overtime hours:  {adjusted.overtime_hours:.0f}")

    print(f"\n{'Line':<16} {'Nominal OEE':>12} {'Adjusted OEE':>13} {'Delta':>8}")
    print("-" * 52)
    for nom_lr, adj_lr in zip(nominal.line_results, adjusted.line_results):
        delta = adj_lr.oee - nom_lr.oee
        print(f"{nom_lr.line_name:<16} {nom_lr.oee:>11.1%} {adj_lr.oee:>12.1%} {delta:>+7.1%}")

    print(f"\n{'Plant avg':<16} {nominal.plant_oee:>11.1%} {adjusted.plant_oee:>12.1%} "
          f"{adjusted.plant_oee - nominal.plant_oee:>+7.1%}")

    # Self-checks
    assert 0.03 < adjusted.absence_rate < 0.15, (
        f"Absence rate {adjusted.absence_rate} out of range")
    assert adjusted.plant_oee < nominal.plant_oee, (
        "Workforce effects should reduce OEE")
    assert adjusted.plant_oee > 0, "OEE should be positive"

    assert fatigue_factor(2, False, 3) == 1.0
    assert fatigue_factor(6, False, 3) == 0.98
    assert fatigue_factor(9, False, 3) == 0.93
    assert fatigue_factor(11, False, 3) == 0.85
    assert fatigue_factor(6, True, 3) == 0.95   # 0.98 - 0.03
    assert fatigue_factor(6, False, 7) == 0.96   # 0.98 - 0.01*2

    print("\nPASS — absenteeism and fatigue model integrated")
