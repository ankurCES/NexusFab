"""Generate 30 days of historical production data for all plants."""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nexusfab.seed.plants import PLANTS, seed_uuid
from nexusfab.seed.products import get_products_for_plant


@dataclass
class ProductionRunRecord:
    line_name: str
    plant_id: str
    product_sku: str
    start_time: datetime
    end_time: datetime
    shift: int
    planned_qty: int
    actual_qty: int
    good_qty: int


@dataclass
class DowntimeRecord:
    line_name: str
    plant_id: str
    equipment_name: str | None
    start_time: datetime
    end_time: datetime
    downtime_type: str  # mechanical, electrical, process, changeover, cip
    root_cause: str
    duration_minutes: float


@dataclass
class OEEShiftRecord:
    line_name: str
    plant_id: str
    timestamp: datetime
    shift: int
    availability: float
    performance: float
    quality: float
    oee: float
    six_big_losses: dict | None = None


@dataclass
class HistoryData:
    production_runs: list[ProductionRunRecord] = field(default_factory=list)
    downtime_events: list[DowntimeRecord] = field(default_factory=list)
    oee_records: list[OEEShiftRecord] = field(default_factory=list)


# Downtime cause weights and typical durations
_DOWNTIME_CAUSES = [
    ("mechanical", 0.40, 30, 240, ["Bearing failure", "Seal wear", "Belt breakage", "Motor overload", "Gear damage"]),
    ("electrical", 0.15, 15, 120, ["Sensor fault", "PLC error", "Drive failure", "Wiring fault", "Control board"]),
    ("process",    0.20, 10, 60,  ["Material jam", "Viscosity issue", "Temperature deviation", "Pressure drop", "Flow blockage"]),
    ("changeover", 0.15, 20, 90,  ["SKU changeover", "Format change", "Tool change"]),
    ("cip",        0.10, 45, 180, ["Scheduled CIP", "Allergen CIP", "Extended CIP"]),
]

# OEE tuning — targets 55-75% typical, some 80%+
_OEE_PARAMS = {
    "WATER":          {"avail": (0.80, 0.95), "perf": (0.78, 0.93), "qual": (0.97, 0.995)},
    "CONFECTIONERY":  {"avail": (0.75, 0.90), "perf": (0.75, 0.90), "qual": (0.96, 0.99)},
    "DAIRY":          {"avail": (0.74, 0.88), "perf": (0.75, 0.89), "qual": (0.95, 0.99)},
    "PET_FOOD":       {"avail": (0.78, 0.93), "perf": (0.76, 0.91), "qual": (0.96, 0.995)},
    "PREPARED_FOODS": {"avail": (0.74, 0.88), "perf": (0.75, 0.89), "qual": (0.95, 0.99)},
}


def _weibull_duration(rng: random.Random, min_d: float, max_d: float) -> float:
    # ponytail: Weibull shape=1.5 (increasing failure rate), scale tuned to midpoint
    mean = (min_d + max_d) / 2
    raw = rng.weibullvariate(mean / 0.9027, 1.5)
    return max(min_d, min(max_d, raw))


def _six_big_losses(rng: random.Random, avail: float, perf: float, qual: float) -> dict:
    """Distribute OEE losses across six big loss categories (minutes per shift)."""
    avail_loss = (1 - avail) * 480
    perf_loss = (1 - perf) * avail * 480
    qual_loss = (1 - qual) * avail * perf * 480
    a_split = rng.uniform(0.3, 0.7)
    p_split = rng.uniform(0.3, 0.7)
    q_split = rng.uniform(0.3, 0.7)
    return {
        "equipment_failure": round(avail_loss * a_split, 1),
        "setup_adjustments": round(avail_loss * (1 - a_split), 1),
        "small_stops": round(perf_loss * p_split, 1),
        "reduced_speed": round(perf_loss * (1 - p_split), 1),
        "process_defects": round(qual_loss * q_split, 1),
        "reduced_yield": round(qual_loss * (1 - q_split), 1),
    }


def generate_history(days: int = 30, seed: int = 42) -> HistoryData:
    """Generate historical production data for all plants."""
    rng = random.Random(seed)
    data = HistoryData()
    base_date = datetime(2026, 6, 23, 0, 0, 0)  # 30 days before "today"

    for plant in PLANTS:
        products = get_products_for_plant(plant.id)
        if not products:
            continue
        params = _OEE_PARAMS.get(plant.category, _OEE_PARAMS["WATER"])

        for line in plant.lines:
            for day in range(days):
                for shift in range(1, 4):  # 3 shifts per day
                    shift_start = base_date + timedelta(days=day, hours=(shift - 1) * 8)
                    shift_end = shift_start + timedelta(hours=8)
                    shift_minutes = 480.0

                    # Generate 1-3 production runs per shift
                    n_runs = rng.randint(1, 3)
                    run_duration = shift_minutes / n_runs
                    downtime_minutes = 0.0
                    shift_produced = 0
                    shift_good = 0

                    avail = rng.uniform(*params["avail"])
                    perf = rng.uniform(*params["perf"])
                    qual = rng.uniform(*params["qual"])

                    for r in range(n_runs):
                        product = rng.choice(products)
                        run_start = shift_start + timedelta(minutes=r * run_duration)
                        run_end = run_start + timedelta(minutes=run_duration)

                        ideal_qty = int(line.speed_units_per_min * run_duration * perf)
                        actual_qty = int(ideal_qty * avail)
                        good_qty = int(actual_qty * qual)

                        data.production_runs.append(ProductionRunRecord(
                            line_name=line.name, plant_id=plant.id,
                            product_sku=product.sku,
                            start_time=run_start, end_time=run_end,
                            shift=shift,
                            planned_qty=int(line.speed_units_per_min * run_duration),
                            actual_qty=actual_qty, good_qty=good_qty,
                        ))
                        shift_produced += actual_qty
                        shift_good += good_qty

                    # Generate downtime events (0-3 per shift)
                    n_events = rng.choices([0, 1, 2, 3], weights=[0.3, 0.4, 0.2, 0.1])[0]
                    for _ in range(n_events):
                        cause_type, _, min_dur, max_dur, causes = rng.choices(
                            _DOWNTIME_CAUSES, weights=[c[1] for c in _DOWNTIME_CAUSES]
                        )[0]
                        duration = _weibull_duration(rng, min_dur, max_dur)
                        dt_start = shift_start + timedelta(minutes=rng.uniform(0, shift_minutes - duration))
                        equipment_name = rng.choice(line.equipment).name if line.equipment else None

                        data.downtime_events.append(DowntimeRecord(
                            line_name=line.name, plant_id=plant.id,
                            equipment_name=equipment_name,
                            start_time=dt_start,
                            end_time=dt_start + timedelta(minutes=duration),
                            downtime_type=cause_type,
                            root_cause=rng.choice(causes),
                            duration_minutes=round(duration, 1),
                        ))
                        downtime_minutes += duration

                    data.oee_records.append(OEEShiftRecord(
                        line_name=line.name, plant_id=plant.id,
                        timestamp=shift_start, shift=shift,
                        availability=round(avail, 4),
                        performance=round(perf, 4),
                        quality=round(qual, 4),
                        oee=round(avail * perf * qual, 4),
                        six_big_losses=_six_big_losses(rng, avail, perf, qual),
                    ))

    return data


async def seed_history(session) -> None:
    """Seed production_runs, downtime_events, oee_records tables from generated data."""
    from sqlalchemy import select

    from nexusfab.models.downtime import DowntimeEvent
    from nexusfab.models.enums import DowntimeType
    from nexusfab.models.oee import OEERecord
    from nexusfab.models.production import ProductionRun

    exists = await session.execute(select(ProductionRun).limit(1))
    if exists.scalar_one_or_none():
        return

    data = generate_history()

    for r in data.production_runs:
        session.add(ProductionRun(
            id=seed_uuid(f"run-{r.line_name}-{r.start_time.isoformat()}"),
            line_id=seed_uuid(r.line_name),
            product_id=seed_uuid(r.product_sku),
            start_time=r.start_time,
            end_time=r.end_time,
            planned_qty=r.planned_qty,
            actual_qty=r.actual_qty,
            good_qty=r.good_qty,
        ))

    for d in data.downtime_events:
        session.add(DowntimeEvent(
            id=seed_uuid(f"dt-{d.line_name}-{d.start_time.isoformat()}"),
            line_id=seed_uuid(d.line_name),
            equipment_id=seed_uuid(d.equipment_name) if d.equipment_name else None,
            start_time=d.start_time,
            end_time=d.end_time,
            downtime_type=DowntimeType(d.downtime_type),
            root_cause=d.root_cause,
        ))

    for o in data.oee_records:
        session.add(OEERecord(
            id=seed_uuid(f"oee-{o.line_name}-{o.timestamp.date()}-s{o.shift}"),
            line_id=seed_uuid(o.line_name),
            shift_date=o.timestamp.date(),
            shift_number=o.shift,
            availability=o.availability,
            performance=o.performance,
            quality=o.quality,
            oee=o.oee,
            six_big_losses=o.six_big_losses,
        ))

    await session.commit()


def _print_summary(data: HistoryData):
    print(f"Production runs: {len(data.production_runs):,}")
    print(f"Downtime events: {len(data.downtime_events):,}")
    print(f"OEE records:     {len(data.oee_records):,}")

    oees = [r.oee for r in data.oee_records]
    print(f"OEE range: {min(oees):.4f} – {max(oees):.4f}, avg {sum(oees)/len(oees):.4f}")

    by_plant: dict[str, list[float]] = {}
    for rec in data.oee_records:
        by_plant.setdefault(rec.plant_id, []).append(rec.oee)
    for pid, plant_oees in sorted(by_plant.items()):
        avg = sum(plant_oees) / len(plant_oees)
        print(f"  {pid}: avg OEE = {avg:.4f} ({len(plant_oees)} shifts)")


if __name__ == "__main__":
    data = generate_history()
    _print_summary(data)

    # self-check
    assert len(data.production_runs) > 2000
    assert len(data.downtime_events) > 1000
    assert len(data.oee_records) > 1000
    oees = [r.oee for r in data.oee_records]
    assert 0.50 < sum(oees) / len(oees) < 0.80, f"avg OEE out of range: {sum(oees)/len(oees):.4f}"
    assert any(o > 0.80 for o in oees), "no OEE records above 80%"
    assert all(r.six_big_losses for r in data.oee_records), "missing six_big_losses"
    print("OK — all checks passed")
