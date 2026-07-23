"""Generate 30 days of historical production data for all plants."""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nexusfab.seed.plants import PLANTS
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

# OEE tuning by plant category
_OEE_PARAMS = {
    "WATER":          {"avail": (0.78, 0.92), "perf": (0.75, 0.90), "qual": (0.96, 0.99)},
    "CONFECTIONERY":  {"avail": (0.70, 0.85), "perf": (0.70, 0.85), "qual": (0.94, 0.98)},
    "DAIRY":          {"avail": (0.65, 0.80), "perf": (0.65, 0.82), "qual": (0.93, 0.97)},
    "PET_FOOD":       {"avail": (0.75, 0.90), "perf": (0.72, 0.88), "qual": (0.95, 0.99)},
    "PREPARED_FOODS": {"avail": (0.68, 0.83), "perf": (0.68, 0.85), "qual": (0.94, 0.98)},
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
                        duration = rng.uniform(min_dur, max_dur)
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
                    ))

    return data


def print_summary(data: HistoryData):
    print(f"Production runs: {len(data.production_runs):,}")
    print(f"Downtime events: {len(data.downtime_events):,}")
    print(f"OEE records:     {len(data.oee_records):,}")

    by_plant: dict[str, list[float]] = {}
    for rec in data.oee_records:
        by_plant.setdefault(rec.plant_id, []).append(rec.oee)
    for pid, oees in sorted(by_plant.items()):
        avg = sum(oees) / len(oees)
        print(f"  {pid}: avg OEE = {avg:.4f} ({len(oees)} shifts)")


if __name__ == "__main__":
    data = generate_history()
    print_summary(data)
