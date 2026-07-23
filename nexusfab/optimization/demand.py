"""Demand planning and forecasting with seasonality and promotion overlays.

Seasonal patterns per spec:
- Beverages (WATER): 2:1 summer peak:trough
- Confectionery: 4x holiday spikes (Valentine's, Easter, Halloween, Christmas)
- Dairy (ice cream component): 3:1 summer peak:trough
- PET_FOOD / PREPARED_FOODS: mild seasonal variation

Includes configurable MAPE (25-50% SKU-level), safety stock calculation,
make-to-stock vs make-to-order classification, and promotion calendar overlay.
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

# ── Raw material lead times (supply-chain-demand.md §5.2) ──
# ponytail: midpoint of range; domestic preferred, import-only uses import_days
RAW_MATERIAL_LEAD_TIMES: dict[str, dict] = {
    "source_water":   {"domestic_days": 0,    "import_days": None,  "storage": "ambient"},
    "co2":            {"domestic_days": 1.5,  "import_days": None,  "storage": "ambient"},
    "pet_preforms":   {"domestic_days": 10.5, "import_days": 35.0,  "storage": "ambient"},
    "cocoa":          {"domestic_days": None,  "import_days": 70.0,  "storage": "ambient"},
    "raw_milk":       {"domestic_days": 0,    "import_days": None,  "storage": "chilled"},
    "cultures":       {"domestic_days": 21.0, "import_days": 35.0,  "storage": "frozen"},
    "tetra_pak":      {"domestic_days": 24.5, "import_days": 49.0,  "storage": "ambient"},
    "meat_meal":      {"domestic_days": 10.5, "import_days": 35.0,  "storage": "cool"},
    "vitamin_premix": {"domestic_days": 24.5, "import_days": 70.0,  "storage": "cool"},
    "spice_blend":    {"domestic_days": 10.5, "import_days": 35.0,  "storage": "ambient"},
}

# $/pallet/week by storage regime
HOLDING_COSTS: dict[str, tuple[float, float]] = {
    "ambient": (3.50, 5.00),
    "cool":    (5.50, 7.50),
    "chilled": (8.00, 12.00),
    "frozen":  (12.00, 18.00),
}

# Category → bottleneck raw material (longest lead time drives planning)
_CATEGORY_BOTTLENECK: dict[str, str] = {
    "WATER":          "pet_preforms",
    "CONFECTIONERY":  "cocoa",
    "DAIRY":          "tetra_pak",
    "PET_FOOD":       "vitamin_premix",
    "PREPARED_FOODS": "spice_blend",
}

# plant_id → category lookup (avoids repeated PLANTS scans)
_PLANT_CATEGORY: dict[str, str] = {p.id: p.category for p in PLANTS}

# ── Promotion overlay ──────────────────────────────────────────────────────────

# Additional MAPE widening applied to bounds during active promotions.
# The base target_mape already covers normal forecast uncertainty; these are
# the extra bands from promotional lift uncertainty (research doc §1.3).
# ponytail: ±8% normal → ±15-30% promo per task spec; stored as fractions
_PROMO_EXTRA_MAPE: dict[str, float] = {
    "price_promotion":    0.20,
    "display_feature":    0.15,
    "new_product_launch": 0.30,
    "seasonal":           0.10,
}


@dataclass
class PromotionEvent:
    name: str
    promo_type: str          # "price_promotion"|"display_feature"|"new_product_launch"|"seasonal"
    start_date: datetime
    duration_weeks: int
    affected_categories: list[str]
    volume_lift_pct: float   # 0.25 = +25%; negative allowed (e.g. melt risk)
    pre_build_weeks: int = 0
    affected_skus: list[str] = field(default_factory=list)  # empty = all in category

    @property
    def end_date(self) -> datetime:
        return self.start_date + timedelta(weeks=self.duration_weeks)

    def is_active(self, week_start: datetime) -> bool:
        return self.start_date <= week_start < self.end_date

    def is_prebuild(self, week_start: datetime) -> bool:
        if self.pre_build_weeks <= 0:
            return False
        pb_start = self.start_date - timedelta(weeks=self.pre_build_weeks)
        return pb_start <= week_start < self.start_date

    def ramp_factor(self, week_start: datetime) -> float:
        """Fractional lift multiplier accounting for ramp shapes."""
        if not self.is_active(week_start):
            return 0.0
        week_idx = int((week_start - self.start_date).days / 7)
        if self.promo_type == "new_product_launch":
            # 8-week ramp: 20% → 60% → 100% of target
            if week_idx < 2:
                return 0.20
            if week_idx < 4:
                return 0.60
            return 1.0
        if self.promo_type == "seasonal" and self.duration_weeks >= 6:
            # gradual 4-week ramp up/down at edges
            ramp = min(4, self.duration_weeks // 3)
            if ramp > 0:
                if week_idx < ramp:
                    return (week_idx + 1) / ramp
                if week_idx >= self.duration_weeks - ramp:
                    return (self.duration_weeks - week_idx) / ramp
        return 1.0


class PromotionCalendar:
    def __init__(self, events: list[PromotionEvent] | None = None):
        self.events: list[PromotionEvent] = events or []

    def active_events(self, week_start: datetime, category: str, sku: str) -> list[PromotionEvent]:
        result = []
        for e in self.events:
            if not e.is_active(week_start):
                continue
            if category not in e.affected_categories:
                continue
            if e.affected_skus and sku not in e.affected_skus:
                continue
            result.append(e)
        return result

    def prebuild_events(self, week_start: datetime, category: str, sku: str) -> list[PromotionEvent]:
        result = []
        for e in self.events:
            if not e.is_prebuild(week_start):
                continue
            if category not in e.affected_categories:
                continue
            if e.affected_skus and sku not in e.affected_skus:
                continue
            result.append(e)
        return result

    @classmethod
    def seed(cls, base_year: int = 2026) -> "PromotionCalendar":
        """Standard retail promotion calendar seeded for NexusFab's 5-category portfolio."""
        y = base_year
        return cls([
            # Summer sustained lift (Jun-Aug, 13 weeks)
            PromotionEvent("Summer Water Lift",         "seasonal",        datetime(y, 6, 1), 13, ["WATER"],          0.15, pre_build_weeks=2),
            PromotionEvent("Summer Confectionery Melt", "seasonal",        datetime(y, 6, 1), 13, ["CONFECTIONERY"], -0.10),
            # Back-to-School (Aug)
            PromotionEvent("Back-to-School Water",      "display_feature", datetime(y, 8, 1),  4, ["WATER"],          0.25, pre_build_weeks=1),
            PromotionEvent("Back-to-School Prepared",   "display_feature", datetime(y, 8, 1),  4, ["PREPARED_FOODS"], 0.15, pre_build_weeks=1),
            # Halloween (Oct)
            PromotionEvent("Halloween Confectionery",   "price_promotion", datetime(y, 10, 1), 4, ["CONFECTIONERY"],  0.40, pre_build_weeks=2),
            PromotionEvent("Halloween Pet Treats",      "price_promotion", datetime(y, 10, 1), 4, ["PET_FOOD"],       0.10, pre_build_weeks=1, affected_skus=["PET-TR"]),
            # Thanksgiving (Nov)
            PromotionEvent("Thanksgiving Prepared",     "seasonal",        datetime(y, 11, 1), 4, ["PREPARED_FOODS"], 0.30, pre_build_weeks=2),
            PromotionEvent("Thanksgiving Dairy",        "seasonal",        datetime(y, 11, 1), 4, ["DAIRY"],          0.20, pre_build_weeks=2),
            # Christmas (Dec)
            PromotionEvent("Christmas Confectionery",   "seasonal",        datetime(y, 12, 1), 4, ["CONFECTIONERY"],  0.35, pre_build_weeks=2),
            PromotionEvent("Christmas Dairy",           "seasonal",        datetime(y, 12, 1), 4, ["DAIRY"],          0.15, pre_build_weeks=2),
            PromotionEvent("Christmas Pet Gifts",       "seasonal",        datetime(y, 12, 1), 4, ["PET_FOOD"],       0.25, pre_build_weeks=2),
            # Super Bowl (Feb current and next year — calendar spans Jan y → Jan y+1)
            PromotionEvent("Super Bowl Water",          "display_feature", datetime(y, 2, 1), 2, ["WATER"],           0.20, pre_build_weeks=1),
            PromotionEvent("Super Bowl Prepared",       "display_feature", datetime(y, 2, 1), 2, ["PREPARED_FOODS"],  0.15, pre_build_weeks=1),
            PromotionEvent("Super Bowl Water (next)",   "display_feature", datetime(y+1, 2, 1), 2, ["WATER"],         0.20, pre_build_weeks=1),
            PromotionEvent("Super Bowl Prepared (next)","display_feature", datetime(y+1, 2, 1), 2, ["PREPARED_FOODS"], 0.15, pre_build_weeks=1),
        ])


# ── Core data model ────────────────────────────────────────────────────────────

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
    lead_time_days: float = 14.0
    primary_material: str = ""
    # Promotion overlay fields
    promo_lift_pct: float = 0.0       # net fractional lift applied this week
    promo_event_name: str = ""        # comma-separated names of active events
    pre_build_units: int = 0          # extra production units to build inventory pre-promo
    promo_extra_mape: float = 0.0     # additional uncertainty from promo (on top of target_mape)

    def to_dict(self) -> dict:
        d = {
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
            "lead_time_days": round(self.lead_time_days, 1),
            "primary_material": self.primary_material,
        }
        if self.promo_lift_pct:
            d["promo_lift_pct"] = round(self.promo_lift_pct, 4)
            d["promo_event"] = self.promo_event_name
            d["pre_build_units"] = self.pre_build_units
            d["promo_extra_mape"] = round(self.promo_extra_mape, 3)
        return d


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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _material_lead_time_weeks(category: str, fallback: float = 2.0) -> float:
    """Lead time in weeks for a category's bottleneck raw material."""
    mat_key = _CATEGORY_BOTTLENECK.get(category)
    if not mat_key:
        return fallback
    mat = RAW_MATERIAL_LEAD_TIMES[mat_key]
    days = mat["domestic_days"] if mat["domestic_days"] is not None else mat["import_days"]
    return days / 7.0 if days is not None else fallback


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


# ── Promotion overlay ──────────────────────────────────────────────────────────

def apply_promotions(
    base_demand: list[DemandForecast],
    calendar: PromotionCalendar,
    date_range: tuple[datetime, datetime] | None = None,
    target_mape: float = 0.35,
) -> list[DemandForecast]:
    """Apply promotional overlays to a list of DemandForecast objects (mutates in-place).

    For each forecast week:
    - Sums lift from all active PromotionEvents matching category/SKU.
    - Applies NPL ramp (20%→60%→100%) and seasonal ramp shapes.
    - Widens lower/upper bounds by the extra promo uncertainty.
    - Adds pre_build_units for upcoming promos in the pre-build window.
    """
    for f in base_demand:
        if date_range and not (date_range[0] <= f.period_start < date_range[1]):
            continue

        category = _PLANT_CATEGORY.get(f.plant_id, "")

        # Active promotions this week
        active = calendar.active_events(f.period_start, category, f.sku)
        net_lift = 0.0
        max_extra_mape = 0.0
        event_names = []
        for e in active:
            ramp = e.ramp_factor(f.period_start)
            net_lift += e.volume_lift_pct * ramp
            max_extra_mape = max(max_extra_mape, _PROMO_EXTRA_MAPE.get(e.promo_type, 0.15))
            event_names.append(e.name)

        if net_lift != 0.0:
            base_units = f.forecast_units
            f.forecast_units = max(0, int(base_units * (1 + net_lift)))
            f.promo_lift_pct = net_lift
            f.promo_event_name = ", ".join(event_names)
            f.promo_extra_mape = max_extra_mape
            effective_mape = target_mape + max_extra_mape
            f.lower_bound = max(0, int(f.forecast_units * (1 - effective_mape)))
            f.upper_bound = int(f.forecast_units * (1 + effective_mape))

        # Pre-build: produce inventory ahead of upcoming promotions
        prebuild = calendar.prebuild_events(f.period_start, category, f.sku)
        for e in prebuild:
            if e.pre_build_weeks <= 0 or e.volume_lift_pct <= 0:
                continue
            # Spread total promo extra demand evenly across pre-build window
            weekly_extra = int(f.forecast_units * e.volume_lift_pct / e.pre_build_weeks)
            f.pre_build_units += weekly_extra

    return base_demand


# ── Demand generation ──────────────────────────────────────────────────────────

def generate_demand_plan(
    plant_id: str | None = None,
    horizon_weeks: int = 12,
    base_date: datetime | None = None,
    seed: int = 42,
    target_mape: float = 0.35,
    service_level: float = 0.95,
    lead_time_weeks: float = 2.0,
    calendar: PromotionCalendar | None = None,
) -> DemandPlan:
    """Generate demand forecast with seasonal adjustment, safety stock, MTS/MTO split,
    and optional promotion calendar overlay."""
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
        total_line_speed = sum(l.rated_speed_per_min for l in plant.lines)
        lt_weeks = _material_lead_time_weeks(plant.category, lead_time_weeks)
        lt_days = lt_weeks * 7.0
        mat_key = _CATEGORY_BOTTLENECK.get(plant.category, "")

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
                ss = _safety_stock(base_demand * season, target_mape, service_level, lt_weeks)

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
                    lead_time_days=lt_days,
                    primary_material=mat_key,
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

    if calendar is not None:
        apply_promotions(plan.forecasts, calendar, target_mape=target_mape)

    plan.total_forecast_units = sum(f.forecast_units for f in plan.forecasts)
    return plan


if __name__ == "__main__":
    # ── Regression checks (original behaviour) ──────────────────────────────
    p = generate_demand_plan("PLT-001", horizon_weeks=4)
    d = p.to_dict()
    print(f"PLT-001 (4w): {d['total_forecasts']} forecasts, {d['total_units']:,} units")
    print(f"MTS: {d['mts_pct']:.0%} ({d['mts_units']:,}), MTO: {d['mto_units']:,}")
    print(f"Gaps: {len(d['capacity_gaps'])}")
    for g in d['capacity_gaps']:
        print(f"  {g['period']}: {g['status']} ({g['gap_pct']:.1%})")

    assert d['forecasts'][0]['safety_stock'] > 0
    assert d['forecasts'][0]['fulfillment_type'] in ("MTS", "MTO")
    assert d['total_forecasts'] > 0
    assert d['total_units'] > 0

    water_s = _SEASONALITY["WATER"]
    assert max(water_s) / min(water_s) >= 1.9, "WATER should be ~2:1"
    conf_s = _SEASONALITY["CONFECTIONERY"]
    assert max(conf_s) / min(conf_s) >= 3.5, "CONFECTIONERY should be ~4:1"
    dairy_s = _SEASONALITY["DAIRY"]
    assert max(dairy_s) / min(dairy_s) >= 2.8, "DAIRY should be ~3:1"

    cocoa_lt = _material_lead_time_weeks("CONFECTIONERY")
    water_lt = _material_lead_time_weeks("WATER")
    assert cocoa_lt > water_lt * 5, f"cocoa {cocoa_lt:.1f}w should be >> water {water_lt:.1f}w"
    print(f"Lead times: WATER={water_lt:.1f}w, CONFECTIONERY={cocoa_lt:.1f}w (ratio {cocoa_lt/water_lt:.1f}x)")

    assert d['forecasts'][0]['lead_time_days'] > 0
    assert d['forecasts'][0]['primary_material'] != ""

    all_p = generate_demand_plan(horizon_weeks=4)
    ad = all_p.to_dict()
    print(f"\nAll plants (4w): {ad['total_forecasts']} forecasts")
    assert ad['mts_units'] > 0, "Should have MTS items"
    assert ad['mto_units'] > 0, "Should have MTO items"

    lt_by_mat = {}
    for f in ad['forecasts']:
        lt_by_mat[f['primary_material']] = f['lead_time_days']
    assert lt_by_mat["cocoa"] > lt_by_mat["pet_preforms"], "cocoa should have longer lead time than PET"
    print(f"Lead times by material: {lt_by_mat}")

    # ── 12-month promo overlay for PLT-001 ───────────────────────────────────
    print("\n" + "=" * 70)
    print("PLT-001 (WATER) — 12-month demand: base vs promoted")
    print("=" * 70)

    cal = PromotionCalendar.seed(2026)
    base_date = datetime(2026, 1, 1)
    base_plan = generate_demand_plan("PLT-001", horizon_weeks=52, base_date=base_date, seed=42)
    promo_plan = generate_demand_plan("PLT-001", horizon_weeks=52, base_date=base_date, seed=42, calendar=cal)

    # Aggregate weekly totals across all SKUs for PLT-001
    from collections import defaultdict
    base_by_week: dict[int, int] = defaultdict(int)
    promo_by_week: dict[int, int] = defaultdict(int)
    promo_name_by_week: dict[int, str] = {}
    prebuild_by_week: dict[int, int] = defaultdict(int)

    for f in base_plan.forecasts:
        wk = int((f.period_start - base_date).days / 7) + 1
        base_by_week[wk] += f.forecast_units

    for f in promo_plan.forecasts:
        wk = int((f.period_start - base_date).days / 7) + 1
        promo_by_week[wk] += f.forecast_units
        if f.promo_event_name and wk not in promo_name_by_week:
            promo_name_by_week[wk] = f.promo_event_name
        prebuild_by_week[wk] += f.pre_build_units

    max_units = max(promo_by_week.values()) if promo_by_week else 1
    bar_width = 30

    # Verify promos were applied
    assert any(promo_by_week[w] != base_by_week[w] for w in range(1, 53)), "No promo lift detected"
    assert any(prebuild_by_week[w] > 0 for w in range(1, 53)), "No pre-build units detected"

    print(f"{'Wk':<4} {'Date':<11} {'Base':>8} {'Promo':>8} {'Lift':>6}  Chart")
    print("-" * 70)
    for wk in range(1, 53):
        date = base_date + timedelta(weeks=wk - 1)
        base = base_by_week[wk]
        promo = promo_by_week[wk]
        lift = (promo - base) / max(base, 1)
        bars = int(promo / max_units * bar_width)
        base_bars = int(base / max_units * bar_width)
        bar = "█" * base_bars + "░" * (bars - base_bars) + " " * (bar_width - bars)
        event = promo_name_by_week.get(wk, "")
        pb = f" [+{prebuild_by_week[wk]:,} pre-build]" if prebuild_by_week[wk] > 0 else ""
        label = f" ← {event}{pb}" if event or pb else ""
        lift_str = f"{lift:+.0%}" if abs(lift) > 0.005 else "    -"
        print(f"W{wk:<3} {date.strftime('%Y-%m-%d')} {base:>8,} {promo:>8,} {lift_str:>6}  |{bar}|{label}")

    promo_weeks = sum(1 for w in range(1, 53) if promo_by_week[w] != base_by_week[w])
    total_extra = sum(promo_by_week[w] - base_by_week[w] for w in range(1, 53))
    print(f"\nPromo-affected weeks: {promo_weeks}/52 | Extra units: {total_extra:,} | Events: {len(cal.events)}")
    print("PASS")
