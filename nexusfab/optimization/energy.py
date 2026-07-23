"""Energy optimization + sustainability tracking.

Models energy consumption per equipment type, identifies savings
opportunities, and tracks carbon footprint across the plant network.
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
}

# $/kWh by region (simplified)
_ENERGY_COSTS = {
    "PLT-001": 0.12,  # Eastern
    "PLT-002": 0.11,  # Central
    "PLT-003": 0.10,  # Northern
    "PLT-004": 0.13,  # Southern
    "PLT-005": 0.14,  # Western
}

# kg CO2 per kWh (US grid average)
_CO2_FACTOR = 0.42


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


if __name__ == "__main__":
    r = analyze_energy("PLT-001", period_days=30)
    d = r.to_dict()
    print(f"PLT-001 (30d): {d['total_kwh']:,.0f} kWh, ${d['total_cost']:,.0f}, {d['total_co2_kg']:,.0f} kg CO2")
    print(f"kWh/ton: {d['kwh_per_ton']:.1f}")
    print(f"Savings: {len(d['savings_opportunities'])}")
    for s in d['savings_opportunities'][:3]:
        print(f"  {s['description']}: ${s['annual_cost_savings']:,.0f}/yr, payback {s['payback_months']:.0f}mo")
    assert d['total_kwh'] > 0
    print("PASS")
