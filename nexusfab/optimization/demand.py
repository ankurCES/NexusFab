"""Demand planning and forecasting.

Generates demand forecasts using moving average + seasonal factors,
then matches against plant capacity for gap analysis.
"""

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.seed.products import PRODUCTS, get_products_for_plant


# Seasonal indices by category (12 months, Jan=0)
_SEASONALITY = {
    "WATER":          [0.7, 0.75, 0.85, 0.95, 1.1, 1.3, 1.4, 1.35, 1.1, 0.9, 0.75, 0.7],
    "CONFECTIONERY":  [0.8, 0.9, 0.95, 1.1, 0.9, 0.85, 0.8, 0.85, 1.0, 1.1, 1.3, 1.5],
    "DAIRY":          [1.0, 1.0, 0.95, 0.95, 1.0, 1.05, 1.05, 1.0, 1.0, 0.95, 0.95, 1.0],
    "PET_FOOD":       [0.9, 0.9, 0.95, 1.0, 1.05, 1.1, 1.1, 1.05, 1.0, 0.95, 0.9, 0.95],
    "PREPARED_FOODS": [1.0, 0.95, 0.9, 0.85, 0.9, 0.95, 0.9, 0.85, 1.0, 1.1, 1.2, 1.3],
}


@dataclass
class DemandForecast:
    sku: str
    product_name: str
    plant_id: str
    period_start: datetime
    period_end: datetime
    forecast_units: int
    lower_bound: int
    upper_bound: int
    seasonal_factor: float
    trend_factor: float

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "product": self.product_name,
            "plant_id": self.plant_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "forecast_units": self.forecast_units,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "seasonal_factor": round(self.seasonal_factor, 3),
            "trend_factor": round(self.trend_factor, 3),
        }


@dataclass
class CapacityGap:
    plant_id: str
    plant_name: str
    period: str
    demand_units: int
    capacity_units: int
    gap_units: int
    gap_pct: float
    status: str  # "surplus" | "tight" | "shortfall"

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id,
            "plant": self.plant_name,
            "period": self.period,
            "demand": self.demand_units,
            "capacity": self.capacity_units,
            "gap": self.gap_units,
            "gap_pct": round(self.gap_pct, 4),
            "status": self.status,
        }


@dataclass
class DemandPlan:
    horizon_weeks: int
    forecasts: list[DemandForecast] = field(default_factory=list)
    capacity_gaps: list[CapacityGap] = field(default_factory=list)
    total_forecast_units: int = 0

    def to_dict(self) -> dict:
        by_plant = {}
        for f in self.forecasts:
            by_plant.setdefault(f.plant_id, 0)
            by_plant[f.plant_id] += f.forecast_units
        return {
            "horizon_weeks": self.horizon_weeks,
            "total_forecasts": len(self.forecasts),
            "total_units": self.total_forecast_units,
            "by_plant": by_plant,
            "capacity_gaps": [g.to_dict() for g in self.capacity_gaps],
            "forecasts": [f.to_dict() for f in self.forecasts[:50]],
        }


def generate_demand_plan(
    plant_id: str | None = None,
    horizon_weeks: int = 12,
    base_date: datetime | None = None,
    seed: int = 42,
) -> DemandPlan:
    """Generate demand forecast with seasonal adjustment + capacity gap analysis."""
    if base_date is None:
        base_date = datetime(2026, 7, 23, 0, 0, 0)

    rng = random.Random(seed)
    plan = DemandPlan(horizon_weeks=horizon_weeks)

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    for plant in plants:
        products = get_products_for_plant(plant.id)
        seasonal = _SEASONALITY.get(plant.category, [1.0] * 12)
        total_line_speed = sum(l.speed_units_per_min for l in plant.lines)

        for week in range(horizon_weeks):
            week_start = base_date + timedelta(weeks=week)
            week_end = week_start + timedelta(weeks=1)
            month_idx = week_start.month - 1
            season = seasonal[month_idx]
            trend = 1.0 + week * 0.002  # 0.2% weekly growth

            weekly_plant_demand = 0

            for product in products:
                base_demand = product.units_per_batch * 3  # ~3 batches/week base
                forecast = int(base_demand * season * trend * rng.uniform(0.85, 1.15))
                lower = int(forecast * 0.8)
                upper = int(forecast * 1.25)

                plan.forecasts.append(DemandForecast(
                    sku=product.sku,
                    product_name=product.name,
                    plant_id=plant.id,
                    period_start=week_start,
                    period_end=week_end,
                    forecast_units=forecast,
                    lower_bound=lower,
                    upper_bound=upper,
                    seasonal_factor=season,
                    trend_factor=trend,
                ))
                weekly_plant_demand += forecast

            # Capacity gap: weekly capacity = line speed × minutes/week × OEE
            weekly_capacity = int(total_line_speed * 60 * 24 * 7 * plant.starting_oee)
            gap = weekly_capacity - weekly_plant_demand
            gap_pct = gap / weekly_capacity if weekly_capacity > 0 else 0

            if gap_pct > 0.15:
                status = "surplus"
            elif gap_pct > 0:
                status = "tight"
            else:
                status = "shortfall"

            plan.capacity_gaps.append(CapacityGap(
                plant_id=plant.id,
                plant_name=plant.name,
                period=f"W{week+1} ({week_start.strftime('%Y-%m-%d')})",
                demand_units=weekly_plant_demand,
                capacity_units=weekly_capacity,
                gap_units=gap,
                gap_pct=gap_pct,
                status=status,
            ))

    plan.total_forecast_units = sum(f.forecast_units for f in plan.forecasts)
    return plan


if __name__ == "__main__":
    p = generate_demand_plan("PLT-001", horizon_weeks=4)
    d = p.to_dict()
    print(f"PLT-001 (4w): {d['total_forecasts']} forecasts, {d['total_units']:,} units")
    print(f"Gaps: {len(d['capacity_gaps'])}")
    for g in d['capacity_gaps']:
        print(f"  {g['period']}: {g['status']} ({g['gap_pct']:.1%})")
    assert d['total_forecasts'] > 0
    assert d['total_units'] > 0

    all_p = generate_demand_plan(horizon_weeks=4)
    print(f"All plants (4w): {all_p.to_dict()['total_forecasts']} forecasts")
    print("PASS")
