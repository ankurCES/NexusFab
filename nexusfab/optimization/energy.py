"""Energy optimization + sustainability tracking.

Models energy consumption per equipment type, identifies savings
opportunities, and tracks carbon footprint across the plant network.
Includes demand charges, critical peak pricing, power factor penalties,
and natural gas costs per docs/research/energy-workforce-simulation.md §1–2.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nexusfab.seed.plants import PLANTS, get_plant

# kWh per hour by equipment type (typical industrial)
_ENERGY_RATES = {
    "FILLER":       15.0,
    "CAPPER":        8.0,
    "LABELER":       5.0,
    "CONVEYOR":     12.0,
    "MIXER":        25.0,
    "PACKAGING":    10.0,
    "PASTEURIZER":  45.0,
    "HOMOGENIZER":  35.0,
    "DRYER":        55.0,
    # Plant-level utilities (shared, not on production lines)
    "COMPRESSOR":    112.0,   # 75-150 kW, compressed air
    "REFRIGERATION": 350.0,   # 200-500 kW, ammonia
    "CIP_HEATER":    140.0,   # 80-200 kW, hot water/steam for CIP
    "HVAC":          100.0,   # 50-150 kW per zone
    "SPRAY_DRYER":  1150.0,   # 800-1500 kW, largest single load
    "COOLING_TOWER":  52.0,   # 30-75 kW per cell
    "VACUUM_PUMP":    30.0,   # 15-45 kW
}

# ── Utility rate structure (docs/research/energy-workforce-simulation.md §2) ──

_PLANT_RATES = {
    "PLT-001": {  # TX — ERCOT
        "base_kwh": 0.08, "demand_kw": 8.50,
        "cpp_rate": 5.00, "cpp_events_year": 8,
        "cpp_months": (6, 7, 8, 9),
        "gas_mmbtu": 3.50, "gas_winter_prem": 0.15,
    },
    "PLT-002": {  # WI — WE Energies
        "base_kwh": 0.09, "demand_kw": 12.00,
        "cpp_rate": 0.30, "cpp_events_year": 5,
        "cpp_months": (6, 7, 8),
        "gas_mmbtu": 4.00, "gas_winter_prem": 0.25,
    },
    "PLT-003": {  # CA — PG&E
        "base_kwh": 0.14, "demand_kw": 22.00,
        "cpp_rate": 1.20, "cpp_events_year": 15,
        "cpp_months": (6, 7, 8, 9),
        "gas_mmbtu": 6.00, "gas_winter_prem": 0.15,
    },
    "PLT-004": {  # CO — Xcel Energy
        "base_kwh": 0.11, "demand_kw": 14.50,
        "cpp_rate": 0.35, "cpp_events_year": 6,
        "cpp_months": (6, 7, 8),
        "gas_mmbtu": 4.50, "gas_winter_prem": 0.20,
    },
    "PLT-005": {  # SC — Duke Energy
        "base_kwh": 0.10, "demand_kw": 10.00,
        "cpp_rate": 0.25, "cpp_events_year": 5,
        "cpp_months": (6, 7, 8),
        "gas_mmbtu": 5.00, "gas_winter_prem": 0.20,
    },
}

_ENERGY_COSTS = {pid: r["base_kwh"] for pid, r in _PLANT_RATES.items()}

# Startup inrush multiplier — motors draw 1.5-2.5× during ramp-up
_STARTUP_MULT = {
    "PASTEURIZER":  2.5,
    "HOMOGENIZER":  2.5,
    "DRYER":        2.0,
    "MIXER":        2.0,
    "FILLER":       1.5,
    "CAPPER":       1.5,
    "CONVEYOR":     1.8,
    "LABELER":      1.2,
    "PACKAGING":    1.3,
    "COMPRESSOR":    2.5,
    "REFRIGERATION": 3.0,   # ammonia compressor inrush
    "CIP_HEATER":    1.5,
    "HVAC":          2.0,
    "SPRAY_DRYER":   2.5,
    "COOLING_TOWER": 2.0,
    "VACUUM_PUMP":   1.8,
}

# ponytail: flat 10% standby, differentiate per-type if metering shows spread
_STANDBY_PCT = 0.10

# Typical power factor by equipment type (uncorrected motors)
_PF_BY_EQUIPMENT = {
    "PASTEURIZER":  0.86,
    "HOMOGENIZER":  0.84,
    "DRYER":        0.80,
    "MIXER":        0.83,
    "FILLER":       0.85,
    "CAPPER":       0.88,
    "CONVEYOR":     0.82,
    "LABELER":      0.92,
    "PACKAGING":    0.90,
    "COMPRESSOR":    0.85,
    "REFRIGERATION": 0.82,
    "CIP_HEATER":    0.95,   # resistive, near-unity PF
    "HVAC":          0.84,
    "SPRAY_DRYER":   0.80,
    "COOLING_TOWER": 0.83,
    "VACUUM_PUMP":   0.86,
}

_PF_THRESHOLD = 0.90

# Natural gas consumption (MMBtu/hour) — steam boilers and gas-fired equipment
_GAS_CONSUMPTION = {
    "PASTEURIZER": 0.8,
    "DRYER":       1.5,
    "BOILER":     12.0,    # 2-5 MW thermal ≈ 6.8-17 MMBtu/hr, midpoint
}

_WINTER_MONTHS = {11, 12, 1, 2, 3}

# kg CO2 per kWh (US grid average)
_CO2_FACTOR = 0.42
# kg CO2 per MMBtu natural gas (EPA)
_CO2_GAS_FACTOR = 53.06


# ── Plant-level utility equipment counts ──
# ponytail: static mapping, derive from asset DB if one exists
_PLANT_UTILITIES: dict[str, dict[str, int]] = {
    "PLT-001": {"COMPRESSOR": 1, "CIP_HEATER": 1, "HVAC": 2, "COOLING_TOWER": 2, "VACUUM_PUMP": 2, "BOILER": 1},
    "PLT-002": {"COMPRESSOR": 1, "REFRIGERATION": 1, "CIP_HEATER": 1, "HVAC": 2, "COOLING_TOWER": 2, "VACUUM_PUMP": 1, "BOILER": 1},
    "PLT-003": {"COMPRESSOR": 2, "REFRIGERATION": 2, "CIP_HEATER": 2, "HVAC": 3, "SPRAY_DRYER": 1, "COOLING_TOWER": 3, "VACUUM_PUMP": 2, "BOILER": 2},
    "PLT-004": {"COMPRESSOR": 1, "CIP_HEATER": 1, "HVAC": 2, "COOLING_TOWER": 2, "VACUUM_PUMP": 2, "BOILER": 1},
    "PLT-005": {"COMPRESSOR": 1, "CIP_HEATER": 1, "HVAC": 2, "COOLING_TOWER": 1, "VACUUM_PUMP": 1, "BOILER": 1},
}

# HVAC seasonal multiplier by month (weather-dependent load)
# ponytail: sine curve if real weather integration matters
_HVAC_SEASONAL = {1: 0.8, 2: 0.7, 3: 0.6, 4: 0.5, 5: 0.6, 6: 0.8, 7: 1.0, 8: 1.0, 9: 0.8, 10: 0.6, 11: 0.7, 12: 0.8}


@dataclass
class EquipmentEnergy:
    equipment_name: str
    equipment_type: str
    plant_id: str
    line_name: str
    kwh_per_hour: float
    running_hours: float
    total_kwh: float
    cost: float
    co2_kg: float

    def to_dict(self) -> dict:
        return {
            "equipment": self.equipment_name,
            "type": self.equipment_type,
            "plant_id": self.plant_id,
            "line": self.line_name,
            "kwh_per_hour": self.kwh_per_hour,
            "running_hours": round(self.running_hours, 1),
            "total_kwh": round(self.total_kwh, 1),
            "cost": round(self.cost, 2),
            "co2_kg": round(self.co2_kg, 1),
        }


@dataclass
class SavingsOpportunity:
    description: str
    plant_id: str
    equipment_type: str
    annual_kwh_savings: float
    annual_cost_savings: float
    annual_co2_savings_kg: float
    implementation_cost: float
    payback_months: float
    priority: str

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "plant_id": self.plant_id,
            "equipment_type": self.equipment_type,
            "annual_kwh_savings": round(self.annual_kwh_savings, 0),
            "annual_cost_savings": round(self.annual_cost_savings, 2),
            "annual_co2_savings_kg": round(self.annual_co2_savings_kg, 0),
            "implementation_cost": round(self.implementation_cost, 2),
            "payback_months": round(self.payback_months, 1),
            "priority": self.priority,
        }


@dataclass
class EnergyReport:
    plant_id: str | None
    period_days: int
    equipment_energy: list[EquipmentEnergy] = field(default_factory=list)
    savings: list[SavingsOpportunity] = field(default_factory=list)
    total_kwh: float = 0.0
    total_cost: float = 0.0
    total_co2_kg: float = 0.0
    kwh_per_ton: float = 0.0

    def to_dict(self) -> dict:
        by_type = {}
        for e in self.equipment_energy:
            by_type.setdefault(e.equipment_type, 0)
            by_type[e.equipment_type] += e.total_kwh
        return {
            "plant_id": self.plant_id or "all",
            "period_days": self.period_days,
            "total_kwh": round(self.total_kwh, 0),
            "total_cost": round(self.total_cost, 2),
            "total_co2_kg": round(self.total_co2_kg, 0),
            "kwh_per_ton": round(self.kwh_per_ton, 2),
            "by_equipment_type": {k: round(v, 0) for k, v in sorted(by_type.items(), key=lambda x: -x[1])},
            "savings_opportunities": [s.to_dict() for s in self.savings],
            "equipment_detail": [e.to_dict() for e in self.equipment_energy[:30]],
        }


# ponytail: predefined savings templates
_SAVINGS_TEMPLATES = [
    ("VFD on {type} motors", 0.15, 8000, "high"),
    ("LED lighting upgrade near {type}", 0.05, 3000, "medium"),
    ("Compressed air leak fix ({type} area)", 0.08, 1500, "high"),
    ("Heat recovery on {type}", 0.12, 15000, "medium"),
    ("Smart scheduling ({type} off-peak)", 0.10, 500, "high"),
]


def analyze_energy(
    plant_id: str | None = None,
    period_days: int = 30,
    utilization: float = 0.65,
    seed: int = 42,
) -> EnergyReport:
    """Analyze energy consumption and identify savings opportunities."""
    rng = random.Random(seed)
    report = EnergyReport(plant_id=plant_id, period_days=period_days)

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    total_tons = 0.0
    for plant in plants:
        cost_per_kwh = _ENERGY_COSTS.get(plant.id, 0.12)
        total_tons += plant.capacity_tons_per_day * period_days * utilization

        for line in plant.lines:
            for eq in line.equipment:
                kwh_rate = _ENERGY_RATES.get(eq.equipment_type, 10.0)
                # Running hours = period × 24h × utilization × random variance
                running_hours = period_days * 24 * utilization * rng.uniform(0.9, 1.1)
                total_kwh = kwh_rate * running_hours
                cost = total_kwh * cost_per_kwh
                co2 = total_kwh * _CO2_FACTOR

                report.equipment_energy.append(EquipmentEnergy(
                    equipment_name=eq.name,
                    equipment_type=eq.equipment_type,
                    plant_id=plant.id,
                    line_name=line.name,
                    kwh_per_hour=kwh_rate,
                    running_hours=running_hours,
                    total_kwh=total_kwh,
                    cost=cost,
                    co2_kg=co2,
                ))

        # Generate savings opportunities
        seen_types = set()
        for line in plant.lines:
            for eq in line.equipment:
                if eq.equipment_type in seen_types:
                    continue
                seen_types.add(eq.equipment_type)

                template = rng.choice(_SAVINGS_TEMPLATES)
                desc, pct_savings, impl_cost, priority = template
                annual_kwh = _ENERGY_RATES.get(eq.equipment_type, 10.0) * 8760 * utilization
                savings_kwh = annual_kwh * pct_savings
                savings_cost = savings_kwh * cost_per_kwh

                payback = impl_cost / savings_cost * 12 if savings_cost > 0 else 999

                report.savings.append(SavingsOpportunity(
                    description=desc.format(type=eq.equipment_type),
                    plant_id=plant.id,
                    equipment_type=eq.equipment_type,
                    annual_kwh_savings=savings_kwh,
                    annual_cost_savings=savings_cost,
                    annual_co2_savings_kg=savings_kwh * _CO2_FACTOR,
                    implementation_cost=impl_cost,
                    payback_months=payback,
                    priority=priority,
                ))

    report.equipment_energy.sort(key=lambda e: -e.total_kwh)
    report.savings.sort(key=lambda s: s.payback_months)
    report.total_kwh = sum(e.total_kwh for e in report.equipment_energy)
    report.total_cost = sum(e.cost for e in report.equipment_energy)
    report.total_co2_kg = sum(e.co2_kg for e in report.equipment_energy)
    report.kwh_per_ton = report.total_kwh / total_tons if total_tons > 0 else 0
    return report


# ── Off-peak energy optimization ──

_ENERGY_INTENSIVE_TYPES = {"PASTEURIZER", "HOMOGENIZER", "DRYER"}

# ponytail: flat tariff model — 3 periods, multiplier vs base rate
_TARIFF_PERIODS = [
    # (start_hour, end_hour, label, multiplier)
    (0,  6,  "off-peak", 0.5),
    (6,  9,  "shoulder", 0.8),
    (9,  17, "peak",     1.0),
    (17, 22, "shoulder", 0.8),
    (22, 24, "off-peak", 0.5),
]


def _tariff_multiplier(hour: int) -> tuple[str, float]:
    for start, end, label, mult in _TARIFF_PERIODS:
        if start <= hour < end:
            return label, mult
    return "peak", 1.0


@dataclass
class EnergyScheduleSlot:
    equipment_type: str
    plant_id: str
    line_name: str
    original_period: str
    optimized_period: str
    hours: float
    kwh: float
    baseline_cost: float
    optimized_cost: float
    savings: float

    def to_dict(self) -> dict:
        return {
            "equipment_type": self.equipment_type,
            "plant_id": self.plant_id,
            "line": self.line_name,
            "original_period": self.original_period,
            "optimized_period": self.optimized_period,
            "hours": round(self.hours, 1),
            "kwh": round(self.kwh, 1),
            "baseline_cost": round(self.baseline_cost, 2),
            "optimized_cost": round(self.optimized_cost, 2),
            "savings": round(self.savings, 2),
        }


@dataclass
class EnergyOptimizationResult:
    plant_id: str | None
    period_days: int
    baseline_cost: float = 0.0
    optimized_cost: float = 0.0
    total_savings: float = 0.0
    savings_pct: float = 0.0
    total_kwh: float = 0.0
    kwh_by_line: dict[str, float] = field(default_factory=dict)
    slots: list[EnergyScheduleSlot] = field(default_factory=list)
    tariff_schedule: list[dict] = field(default_factory=list)
    # Demand charge optimization
    peak_demand_kw: float = 0.0
    optimized_peak_kw: float = 0.0
    demand_charge_baseline: float = 0.0
    demand_charge_optimized: float = 0.0
    demand_savings: float = 0.0

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id or "all",
            "period_days": self.period_days,
            "baseline_cost": round(self.baseline_cost, 2),
            "optimized_cost": round(self.optimized_cost, 2),
            "total_savings": round(self.total_savings, 2),
            "savings_pct": round(self.savings_pct, 1),
            "total_kwh": round(self.total_kwh, 0),
            "kwh_by_line": {k: round(v, 1) for k, v in self.kwh_by_line.items()},
            "tariff_schedule": self.tariff_schedule,
            "slots": [s.to_dict() for s in self.slots],
            "peak_demand_kw": round(self.peak_demand_kw, 1),
            "optimized_peak_kw": round(self.optimized_peak_kw, 1),
            "demand_charge_baseline": round(self.demand_charge_baseline, 2),
            "demand_charge_optimized": round(self.demand_charge_optimized, 2),
            "demand_savings": round(self.demand_savings, 2),
        }


# ── Demand charge and full bill models ──

@dataclass
class CriticalPeakEvent:
    month: int
    day: int
    start_hour: int
    duration_hours: float
    rate: float
    estimated_kwh: float
    cost: float

    def to_dict(self) -> dict:
        return {
            "month": self.month, "day": self.day,
            "start_hour": self.start_hour,
            "duration_hours": round(self.duration_hours, 1),
            "rate": round(self.rate, 2),
            "estimated_kwh": round(self.estimated_kwh, 1),
            "cost": round(self.cost, 2),
        }


@dataclass
class MonthlyBill:
    plant_id: str
    period_days: int
    month: int
    energy_kwh: float
    energy_cost: float
    peak_demand_kw: float
    demand_rate: float
    demand_cost: float
    optimized_peak_kw: float
    optimized_demand_cost: float
    cpp_events: list[CriticalPeakEvent] = field(default_factory=list)
    cpp_total_cost: float = 0.0
    weighted_pf: float = 1.0
    pf_surcharge_pct: float = 0.0
    pf_penalty_cost: float = 0.0
    gas_mmbtu: float = 0.0
    gas_rate_effective: float = 0.0
    gas_cost: float = 0.0
    total_electric: float = 0.0
    total_bill: float = 0.0
    demand_pct: float = 0.0
    co2_kg: float = 0.0

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id,
            "period_days": self.period_days,
            "month": self.month,
            "energy_kwh": round(self.energy_kwh, 0),
            "energy_cost": round(self.energy_cost, 2),
            "peak_demand_kw": round(self.peak_demand_kw, 1),
            "demand_rate": round(self.demand_rate, 2),
            "demand_cost": round(self.demand_cost, 2),
            "optimized_peak_kw": round(self.optimized_peak_kw, 1),
            "optimized_demand_cost": round(self.optimized_demand_cost, 2),
            "cpp_events_count": len(self.cpp_events),
            "cpp_total_cost": round(self.cpp_total_cost, 2),
            "weighted_pf": round(self.weighted_pf, 3),
            "pf_surcharge_pct": round(self.pf_surcharge_pct, 1),
            "pf_penalty_cost": round(self.pf_penalty_cost, 2),
            "gas_mmbtu": round(self.gas_mmbtu, 1),
            "gas_cost": round(self.gas_cost, 2),
            "total_electric": round(self.total_electric, 2),
            "total_bill": round(self.total_bill, 2),
            "demand_pct": round(self.demand_pct, 1),
            "co2_kg": round(self.co2_kg, 0),
            "cpp_events": [e.to_dict() for e in self.cpp_events],
        }


# ── Helpers ──

def _estimate_peak_demand_kw(plant, staggered: bool = False) -> float:
    """Peak 15-min demand (kW). Worst case = all lines restart post-CIP simultaneously."""
    line_startup = []
    line_steady = []
    for line in plant.lines:
        startup = sum(
            _ENERGY_RATES.get(eq.equipment_type, 10.0) * _STARTUP_MULT.get(eq.equipment_type, 1.3)
            for eq in line.equipment
        )
        steady = sum(_ENERGY_RATES.get(eq.equipment_type, 10.0) for eq in line.equipment)
        line_startup.append(startup)
        line_steady.append(steady)

    if staggered and len(line_startup) > 1:
        # ponytail: stagger restarts — only one line in inrush at a time
        peaks = []
        for i, su in enumerate(line_startup):
            others = sum(d for j, d in enumerate(line_steady) if j != i)
            peaks.append(su + others)
        peak = max(peaks)
    else:
        peak = sum(line_startup)

    return peak * 1.15  # 15% demand factor per research §2.3


def _generate_cpp_events(plant_id: str, period_days: int, month: int, rng: random.Random) -> list[CriticalPeakEvent]:
    """Stochastic critical peak events, weather-correlated for CA/TX."""
    rates = _PLANT_RATES.get(plant_id, _PLANT_RATES["PLT-001"])
    if month not in rates["cpp_months"]:
        return []

    monthly_frac = period_days / 365
    expected = rates["cpp_events_year"] * monthly_frac * 2.0  # concentrated in CPP months
    n_events = rng.randint(0, max(1, int(expected * 1.5)))
    n_events = min(n_events, int(rates["cpp_events_year"] * monthly_frac * 3) + 1)

    events = []
    for _ in range(n_events):
        # CA: 4-9 PM window; TX: any afternoon; others: utility-called
        if plant_id == "PLT-003":
            start = rng.choice([16, 17, 18])
        elif plant_id == "PLT-001":
            start = rng.randint(13, 18)
        else:
            start = rng.randint(12, 18)
        events.append(CriticalPeakEvent(
            month=month,
            day=rng.randint(1, min(period_days, 28)),
            start_hour=start,
            duration_hours=rng.uniform(3.0, 5.0),
            rate=rates["cpp_rate"],
            estimated_kwh=0.0,
            cost=0.0,
        ))
    return events


def _weighted_power_factor(plant) -> float:
    """kW-weighted average power factor across all equipment."""
    total_kw = 0.0
    weighted = 0.0
    for line in plant.lines:
        for eq in line.equipment:
            kw = _ENERGY_RATES.get(eq.equipment_type, 10.0)
            pf = _PF_BY_EQUIPMENT.get(eq.equipment_type, 0.90)
            total_kw += kw
            weighted += kw * pf
    return weighted / total_kw if total_kw > 0 else 0.90


def calculate_monthly_bill(
    plant_id: str,
    period_days: int = 30,
    utilization: float = 0.65,
    month: int = 7,
    seed: int = 42,
) -> MonthlyBill:
    """Full monthly utility bill: energy + demand + CPP + PF penalty + gas."""
    rng = random.Random(seed)
    plant = get_plant(plant_id)
    assert plant, f"Unknown plant: {plant_id}"
    rates = _PLANT_RATES.get(plant_id, _PLANT_RATES["PLT-001"])

    # ── Energy charges (TOU-weighted) ──
    total_kwh = 0.0
    energy_cost = 0.0
    for line in plant.lines:
        for eq in line.equipment:
            kwh_rate = _ENERGY_RATES.get(eq.equipment_type, 10.0)
            running_hours = period_days * 24 * utilization * rng.uniform(0.9, 1.1)
            kwh = kwh_rate * running_hours
            total_kwh += kwh
            for start, end, _, mult in _TARIFF_PERIODS:
                frac = (end - start) / 24.0
                energy_cost += kwh * frac * rates["base_kwh"] * mult

    # ── Demand charges (15-min peak) ──
    peak_kw = _estimate_peak_demand_kw(plant, staggered=False)
    demand_cost = peak_kw * rates["demand_kw"]
    opt_peak_kw = _estimate_peak_demand_kw(plant, staggered=True)
    opt_demand_cost = opt_peak_kw * rates["demand_kw"]

    # ── Critical peak events ──
    cpp_events = _generate_cpp_events(plant_id, period_days, month, rng)
    plant_steady_kw = sum(
        _ENERGY_RATES.get(eq.equipment_type, 10.0)
        for line in plant.lines for eq in line.equipment
    ) * utilization
    for evt in cpp_events:
        evt.estimated_kwh = plant_steady_kw * evt.duration_hours
        evt.cost = evt.estimated_kwh * evt.rate
    cpp_total = sum(e.cost for e in cpp_events)

    # ── Power factor penalty ──
    wpf = _weighted_power_factor(plant)
    if wpf < _PF_THRESHOLD:
        # 1.5% surcharge per 0.01 PF below threshold
        pf_steps = int((_PF_THRESHOLD - wpf) / 0.01)
        pf_surcharge_pct = pf_steps * 1.5
    else:
        pf_surcharge_pct = 0.0
    pf_penalty = (energy_cost + demand_cost) * pf_surcharge_pct / 100

    # ── Natural gas ──
    gas_mmbtu = 0.0
    for line in plant.lines:
        for eq in line.equipment:
            gas_rate = _GAS_CONSUMPTION.get(eq.equipment_type)
            if gas_rate:
                running_hours = period_days * 24 * utilization * rng.uniform(0.9, 1.1)
                gas_mmbtu += gas_rate * running_hours
    gas_rate_eff = rates["gas_mmbtu"]
    if month in _WINTER_MONTHS:
        gas_rate_eff *= (1 + rates["gas_winter_prem"])
    gas_cost = gas_mmbtu * gas_rate_eff

    # ── Totals ──
    total_electric = energy_cost + demand_cost + cpp_total + pf_penalty
    total_bill = total_electric + gas_cost
    demand_pct = (demand_cost / total_electric * 100) if total_electric > 0 else 0
    co2 = total_kwh * _CO2_FACTOR + gas_mmbtu * _CO2_GAS_FACTOR

    return MonthlyBill(
        plant_id=plant_id, period_days=period_days, month=month,
        energy_kwh=total_kwh, energy_cost=energy_cost,
        peak_demand_kw=peak_kw, demand_rate=rates["demand_kw"],
        demand_cost=demand_cost,
        optimized_peak_kw=opt_peak_kw, optimized_demand_cost=opt_demand_cost,
        cpp_events=cpp_events, cpp_total_cost=cpp_total,
        weighted_pf=wpf, pf_surcharge_pct=pf_surcharge_pct,
        pf_penalty_cost=pf_penalty,
        gas_mmbtu=gas_mmbtu, gas_rate_effective=gas_rate_eff,
        gas_cost=gas_cost,
        total_electric=total_electric, total_bill=total_bill,
        demand_pct=demand_pct, co2_kg=co2,
    )


def optimize_energy_schedule(
    plant_id: str | None = None,
    period_days: int = 30,
    utilization: float = 0.65,
    seed: int = 42,
) -> EnergyOptimizationResult:
    """Schedule energy-intensive ops to off-peak + stagger startups for demand reduction.

    Returns baseline vs optimized cost comparison with per-slot detail.
    """
    rng = random.Random(seed)
    result = EnergyOptimizationResult(
        plant_id=plant_id,
        period_days=period_days,
        tariff_schedule=[
            {"start": s, "end": e, "period": l, "rate_multiplier": m}
            for s, e, l, m in _TARIFF_PERIODS
        ],
    )

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    for plant in plants:
        base_rate = _ENERGY_COSTS.get(plant.id, 0.12)

        for line in plant.lines:
            line_kwh = 0.0
            for eq in line.equipment:
                kwh_rate = _ENERGY_RATES.get(eq.equipment_type, 10.0)
                running_hours = period_days * 24 * utilization * rng.uniform(0.9, 1.1)
                total_kwh = kwh_rate * running_hours
                line_kwh += total_kwh
                result.total_kwh += total_kwh

                is_intensive = eq.equipment_type in _ENERGY_INTENSIVE_TYPES

                # Baseline: evenly distributed across all hours
                baseline_cost = 0.0
                for start, end, label, mult in _TARIFF_PERIODS:
                    period_fraction = (end - start) / 24.0
                    baseline_cost += total_kwh * period_fraction * base_rate * mult

                if is_intensive:
                    # Optimized: shift 70% of intensive ops to off-peak, 20% shoulder, 10% peak
                    # ponytail: fixed ratios, optimizer would use LP if precision matters
                    opt_cost = total_kwh * base_rate * (0.70 * 0.5 + 0.20 * 0.8 + 0.10 * 1.0)
                    result.slots.append(EnergyScheduleSlot(
                        equipment_type=eq.equipment_type,
                        plant_id=plant.id,
                        line_name=line.name,
                        original_period="distributed",
                        optimized_period="off-peak preferred",
                        hours=running_hours,
                        kwh=total_kwh,
                        baseline_cost=baseline_cost,
                        optimized_cost=opt_cost,
                        savings=baseline_cost - opt_cost,
                    ))
                    result.optimized_cost += opt_cost
                else:
                    result.optimized_cost += baseline_cost

                result.baseline_cost += baseline_cost

            result.kwh_by_line[line.name] = line_kwh

    # ── Demand charge optimization: stagger startups ──
    for plant in plants:
        rates = _PLANT_RATES.get(plant.id, _PLANT_RATES["PLT-001"])
        bp = _estimate_peak_demand_kw(plant, staggered=False)
        op = _estimate_peak_demand_kw(plant, staggered=True)
        result.peak_demand_kw += bp
        result.optimized_peak_kw += op
        result.demand_charge_baseline += bp * rates["demand_kw"]
        result.demand_charge_optimized += op * rates["demand_kw"]
        result.baseline_cost += bp * rates["demand_kw"]
        result.optimized_cost += op * rates["demand_kw"]

    result.demand_savings = result.demand_charge_baseline - result.demand_charge_optimized
    result.total_savings = result.baseline_cost - result.optimized_cost
    result.savings_pct = (result.total_savings / result.baseline_cost * 100) if result.baseline_cost > 0 else 0
    return result


# ponytail: alias per task spec
optimize_energy = optimize_energy_schedule


def load_profile_hourly(
    plant_id: str,
    date: datetime | None = None,
    utilization: float = 0.65,
) -> list[float]:
    """24-element list of kW by hour. Base load (40%) + production + HVAC."""
    plant = get_plant(plant_id)
    assert plant, f"Unknown plant: {plant_id}"
    month = date.month if date else 7

    utils = _PLANT_UTILITIES.get(plant_id, {})

    line_kw = sum(_ENERGY_RATES.get(eq.equipment_type, 10.0)
                  for l in plant.lines for eq in l.equipment)
    # Electric utilities only (BOILER is gas, HVAC handled separately)
    util_kw = sum(_ENERGY_RATES.get(t, 0) * n
                  for t, n in utils.items() if t not in ("HVAC", "BOILER"))
    hvac_kw = _ENERGY_RATES["HVAC"] * utils.get("HVAC", 0)

    rated_total = (line_kw + util_kw) * utilization
    base_kw = rated_total * 0.40
    prod_add = rated_total * 0.60

    # Startup surge — kW-weighted average across line equipment, 15 min of hour
    surge_kw = sum(
        _ENERGY_RATES.get(eq.equipment_type, 10.0) * (_STARTUP_MULT.get(eq.equipment_type, 1.3) - 1)
        for l in plant.lines for eq in l.equipment
    ) * utilization * 0.25

    hvac_season = _HVAC_SEASONAL.get(month, 0.7)

    profile = []
    for h in range(24):
        kw = base_kw
        if 6 <= h < 22:
            kw += prod_add
            if h == 6:
                kw += surge_kw
        kw += hvac_kw * hvac_season * (1.0 if 8 <= h <= 18 else 0.5)
        profile.append(round(kw, 1))
    return profile


if __name__ == "__main__":
    r = analyze_energy("PLT-001", period_days=30)
    d = r.to_dict()
    print(f"PLT-001 (30d): {d['total_kwh']:,.0f} kWh, ${d['total_cost']:,.0f}, {d['total_co2_kg']:,.0f} kg CO2")
    print(f"kWh/ton: {d['kwh_per_ton']:.1f}")
    print(f"Savings: {len(d['savings_opportunities'])}")
    for s in d['savings_opportunities'][:3]:
        print(f"  {s['description']}: ${s['annual_cost_savings']:,.0f}/yr, payback {s['payback_months']:.0f}mo")
    assert d['total_kwh'] > 0

    # Off-peak + demand optimization check
    opt = optimize_energy_schedule("PLT-003", period_days=30)
    od = opt.to_dict()
    print(f"\nEnergy optimization PLT-003:")
    print(f"  Baseline: ${od['baseline_cost']:,.2f}")
    print(f"  Optimized: ${od['optimized_cost']:,.2f}")
    print(f"  Savings: ${od['total_savings']:,.2f} ({od['savings_pct']:.1f}%)")
    print(f"  TOU slots shifted: {len(od['slots'])}")
    print(f"  Demand: {od['peak_demand_kw']:.0f} kW → {od['optimized_peak_kw']:.0f} kW (staggered)")
    print(f"  Demand savings: ${od['demand_savings']:,.2f}")
    assert od['total_savings'] > 0, "Should have savings from off-peak shifting + demand reduction"
    assert od['demand_savings'] > 0, "Should have savings from startup staggering"

    # ── Full monthly bill with demand charges (PLT-003 CA) ──
    bill = calculate_monthly_bill("PLT-003", period_days=30, month=7)
    bd = bill.to_dict()
    print(f"\nPLT-003 CA — Full Monthly Bill:")
    print(f"  Energy:     ${bd['energy_cost']:>10,.2f}  ({bd['energy_kwh']:,.0f} kWh)")
    print(f"  Demand:     ${bd['demand_cost']:>10,.2f}  ({bd['peak_demand_kw']:.0f} kW × ${bd['demand_rate']}/kW)")
    print(f"  CPP:        ${bd['cpp_total_cost']:>10,.2f}  ({bd['cpp_events_count']} events)")
    print(f"  PF penalty: ${bd['pf_penalty_cost']:>10,.2f}  (PF={bd['weighted_pf']:.3f}, +{bd['pf_surcharge_pct']:.1f}%)")
    print(f"  Gas:        ${bd['gas_cost']:>10,.2f}  ({bd['gas_mmbtu']:.0f} MMBtu)")
    print(f"  ─────────────────────────────")
    print(f"  Electric:   ${bd['total_electric']:>10,.2f}")
    print(f"  Total:      ${bd['total_bill']:>10,.2f}")
    print(f"  Demand %:   {bd['demand_pct']:.1f}% of electric bill")
    print(f"  CO2:        {bd['co2_kg']:,.0f} kg")
    print(f"  Demand opt: {bd['peak_demand_kw']:.0f} kW → {bd['optimized_peak_kw']:.0f} kW (staggered)")
    assert bd['demand_pct'] > 30, f"PLT-003 demand charges should be >30% of electric bill, got {bd['demand_pct']:.1f}%"

    # ── PLT-003 24h load profile ──
    profile = load_profile_hourly("PLT-003", datetime(2026, 7, 15))
    print(f"\nPLT-003 24h load profile (July):")
    peak_kw = max(profile)
    for h, kw in enumerate(profile):
        bar = "█" * int(kw / peak_kw * 40)
        tag = " ← PEAK" if kw == peak_kw else ""
        print(f"  {h:02d}:00  {kw:8.1f} kW  {bar}{tag}")
    peak_h = profile.index(peak_kw)
    print(f"  Peak: {peak_kw:.1f} kW at {peak_h:02d}:00")
    # Spray dryer (1150 kW) should be largest single equipment
    utils_003 = _PLANT_UTILITIES["PLT-003"]
    largest_type, largest_kw = max(
        ((t, _ENERGY_RATES.get(t, 0) * n) for t, n in utils_003.items() if t not in ("HVAC", "BOILER")),
        key=lambda x: x[1],
    )
    print(f"  Largest utility: {largest_type} at {largest_kw:.0f} kW")
    assert largest_type == "SPRAY_DRYER", f"Expected SPRAY_DRYER to dominate, got {largest_type}"
    assert 6 <= peak_h < 22, f"Peak should be during production hours, got {peak_h}:00"
    # Standby check
    night_kw = profile[3]
    print(f"  Night standby (03:00): {night_kw:.1f} kW ({night_kw / peak_kw * 100:.0f}% of peak)")
    assert night_kw < peak_kw * 0.55, "Night load should be well below peak"
    print("PASS")
