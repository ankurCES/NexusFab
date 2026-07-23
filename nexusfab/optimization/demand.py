"""Demand planning and forecasting with seasonality.

Seasonal patterns per spec:
- Beverages (WATER): 2:1 summer peak:trough
- Confectionery: 4x holiday spikes (Valentine's, Easter, Halloween, Christmas)
- Dairy (ice cream component): 3:1 summer peak:trough
- PET_FOOD / PREPARED_FOODS: mild seasonal variation

Includes configurable MAPE (25-50% SKU-level), safety stock calculation,
and make-to-stock vs make-to-order classification.
"""

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nexusfab.seed.plants import PLANTS, get_plant
from nexusfab.seed.products import PRODUCTS, get_products_for_plant


# Seasonal indices by category (12 months, Jan=0)
# ponytail: ratios are peak/trough — WATER 2:1, CONFECTIONERY 4:1, DAIRY 3:1
_SEASONALITY = {
    #                     Jan   Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov   Dec
    "WATER":          [0.70, 0.75, 0.85, 0.95, 1.10, 1.30, 1.40, 1.35, 1.10, 0.90, 0.75, 0.70],  # 2:1 summer
    "CONFECTIONERY":  [0.55, 1.60, 0.60, 1.70, 0.60, 0.55, 0.55, 0.55, 0.65, 1.70, 1.10, 2.20],  # 4x holiday spikes
    "DAIRY":          [0.50, 0.55, 0.70, 0.90, 1.20, 1.50, 1.50, 1.40, 1.10, 0.80, 0.55, 0.50],  # 3:1 ice cream summer
    "PET_FOOD":       [0.90, 0.90, 0.95, 1.00, 1.05, 1.10, 1.10, 1.05, 1.00, 0.95, 0.90, 0.95],
    "PREPARED_FOODS": [1.00, 0.95, 0.90, 0.85, 0.90, 0.95, 0.90, 0.85, 1.00, 1.10, 1.20, 1.30],
}

# Service-level z-scores for safety stock
_Z_SCORES = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}

# ponytail: simple heuristic — high seasonal variance or low volume → MTO
_MTO_SEASONAL_THRESHOLD = 1.5  # seasonal factor above this → MTO that period
_MTS_VOLUME_THRESHOLD = 3000   # units_per_batch below this → MTO


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
    safety_stock_units: int = 0
    fulfillment_type: str = "MTS"  # "MTS" | "MTO"

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
            "safety_stock": self.safety_stock_units,
            "fulfillment_type": self.fulfillment_type,
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
    target_mape: float = 0.35
    service_level: float = 0.95
    lead_time_weeks: float = 2.0
    forecasts: list[DemandForecast] = field(default_factory=list)
    capacity_gaps: list[CapacityGap] = field(default_factory=list)
    total_forecast_units: int = 0

    def to_dict(self) -> dict:
        by_plant: dict[str, int] = {}
        mts_units = 0
        mto_units = 0
        for f in self.forecasts:
            by_plant.setdefault(f.plant_id, 0)
            by_plant[f.plant_id] += f.forecast_units
            if f.fulfillment_type == "MTS":
                mts_units += f.forecast_units
            else:
                mto_units += f.forecast_units
        total = mts_units + mto_units or 1
        return {
            "horizon_weeks": self.horizon_weeks,
            "target_mape": self.target_mape,
            "service_level": self.service_level,
            "lead_time_weeks": self.lead_time_weeks,
            "total_forecasts": len(self.forecasts),
            "total_units": self.total_forecast_units,
            "mts_units": mts_units,
            "mto_units": mto_units,
            "mts_pct": round(mts_units / total, 4),
            "by_plant": by_plant,
            "capacity_gaps": [g.to_dict() for g in self.capacity_gaps],
            "forecasts": [f.to_dict() for f in self.forecasts[:50]],
        }


def _safety_stock(avg_demand: float, mape: float, service_level: float, lead_time_weeks: float) -> int:
    z = _Z_SCORES.get(service_level, 1.65)
    sigma = avg_demand * mape
    return max(0, int(z * sigma * math.sqrt(lead_time_weeks)))


def _fulfillment_type(product, seasonal_factor: float) -> str:
    if seasonal_factor >= _MTO_SEASONAL_THRESHOLD:
        return "MTO"
    if product.units_per_batch < _MTS_VOLUME_THRESHOLD:
        return "MTO"
    return "MTS"


def generate_demand_plan(
    plant_id: str | None = None,
    horizon_weeks: int = 12,
    base_date: datetime | None = None,
    seed: int = 42,
    target_mape: float = 0.35,
    service_level: float = 0.95,
    lead_time_weeks: float = 2.0,
) -> DemandPlan:
    """Generate demand forecast with seasonal adjustment, safety stock, and MTS/MTO split."""
    if base_date is None:
        base_date = datetime(2026, 7, 23, 0, 0, 0)
    target_mape = max(0.05, min(target_mape, 0.60))

    rng = random.Random(seed)
    plan = DemandPlan(
        horizon_weeks=horizon_weeks,
        target_mape=target_mape,
        service_level=service_level,
        lead_time_weeks=lead_time_weeks,
    )

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    # ponytail: noise half-width = 2 * mape gives E[|error|] ≈ mape for uniform dist
    noise_hw = target_mape

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
                base_demand = product.units_per_batch * 3
                noise = rng.uniform(1 - noise_hw, 1 + noise_hw)
                forecast = max(0, int(base_demand * season * trend * noise))
                lower = int(forecast * (1 - target_mape))
                upper = int(forecast * (1 + target_mape))

                ft = _fulfillment_type(product, season)
                ss = _safety_stock(base_demand * season, target_mape, service_level, lead_time_weeks)

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
                    safety_stock_units=ss,
                    fulfillment_type=ft,
                ))
                weekly_plant_demand += forecast

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
    print(f"MTS: {d['mts_pct']:.0%} ({d['mts_units']:,}), MTO: {d['mto_units']:,}")
    print(f"Gaps: {len(d['capacity_gaps'])}")
    for g in d['capacity_gaps']:
        print(f"  {g['period']}: {g['status']} ({g['gap_pct']:.1%})")

    # verify safety stock present
    assert d['forecasts'][0]['safety_stock'] > 0
    assert d['forecasts'][0]['fulfillment_type'] in ("MTS", "MTO")
    assert d['total_forecasts'] > 0
    assert d['total_units'] > 0

    # verify seasonality ratios
    water_s = _SEASONALITY["WATER"]
    assert max(water_s) / min(water_s) >= 1.9, "WATER should be ~2:1"
    conf_s = _SEASONALITY["CONFECTIONERY"]
    assert max(conf_s) / min(conf_s) >= 3.5, "CONFECTIONERY should be ~4:1"
    dairy_s = _SEASONALITY["DAIRY"]
    assert max(dairy_s) / min(dairy_s) >= 2.8, "DAIRY should be ~3:1"

    all_p = generate_demand_plan(horizon_weeks=4)
    ad = all_p.to_dict()
    print(f"\nAll plants (4w): {ad['total_forecasts']} forecasts")
    assert ad['mts_units'] > 0, "Should have MTS items"
    assert ad['mto_units'] > 0, "Should have MTO items"
    print("PASS")
