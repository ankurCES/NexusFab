"""Spare parts inventory optimization.

ABC classification, reorder point calculation, and stock-out risk analysis.
Uses equipment MTBF/MTTR data + maintenance schedule to project demand.
"""

import math
from dataclasses import dataclass, field

from nexusfab.seed.plants import PLANTS, get_plant

# Parts catalog per equipment type
_PARTS_CATALOG = {
    "FILLER": [
        ("Filling valve assembly", 850.0, 8, 14),
        ("Piston seals kit", 120.0, 20, 7),
        ("Nozzle tips (set of 12)", 340.0, 6, 10),
    ],
    "CAPPER": [
        ("Capping head assembly", 450.0, 4, 14),
        ("Torque springs (set)", 65.0, 30, 5),
        ("Chuck inserts", 180.0, 10, 7),
    ],
    "LABELER": [
        ("Print head", 620.0, 3, 21),
        ("Label sensor", 95.0, 12, 5),
        ("Drive belt", 45.0, 20, 3),
    ],
    "CONVEYOR": [
        ("Drive motor", 1200.0, 2, 28),
        ("Belt section (3m)", 280.0, 6, 7),
        ("Bearing set", 85.0, 20, 5),
    ],
    "MIXER": [
        ("Agitator blade set", 560.0, 4, 14),
        ("Shaft seal", 190.0, 8, 7),
        ("Coupling assembly", 340.0, 3, 21),
    ],
    "PACKAGING": [
        ("Sealing jaw assembly", 720.0, 4, 14),
        ("Film tension roller", 180.0, 6, 7),
        ("Cutter blade set", 95.0, 15, 5),
    ],
    "PASTEURIZER": [
        ("Heat exchanger plates (set of 4)", 2200.0, 2, 28),
        ("Temperature sensor probe", 150.0, 6, 7),
        ("Gasket kit", 280.0, 8, 10),
    ],
    "HOMOGENIZER": [
        ("Plunger assembly", 1800.0, 2, 28),
        ("Valve seat", 650.0, 4, 14),
        ("Piston seal kit", 220.0, 8, 7),
    ],
    "DRYER": [
        ("Heating element", 950.0, 3, 21),
        ("Fan motor", 1100.0, 2, 28),
        ("Temperature controller", 380.0, 4, 14),
    ],
}


@dataclass
class SparePartStatus:
    part_name: str
    equipment_type: str
    unit_cost: float
    qty_on_hand: int
    reorder_point: int
    lead_time_days: int
    abc_class: str
    annual_demand: float
    safety_stock: int
    eoq: int
    stockout_risk: float
    needs_reorder: bool
    annual_cost: float

    def to_dict(self) -> dict:
        return {
            "part": self.part_name,
            "equipment_type": self.equipment_type,
            "unit_cost": self.unit_cost,
            "on_hand": self.qty_on_hand,
            "reorder_point": self.reorder_point,
            "lead_time_days": self.lead_time_days,
            "abc_class": self.abc_class,
            "annual_demand": round(self.annual_demand, 1),
            "safety_stock": self.safety_stock,
            "eoq": self.eoq,
            "stockout_risk": round(self.stockout_risk, 4),
            "needs_reorder": self.needs_reorder,
            "annual_cost": round(self.annual_cost, 2),
        }


@dataclass
class InventoryReport:
    plant_id: str | None
    parts: list[SparePartStatus] = field(default_factory=list)
    total_inventory_value: float = 0.0
    parts_needing_reorder: int = 0
    high_risk_count: int = 0

    def to_dict(self) -> dict:
        by_class = {}
        for p in self.parts:
            by_class.setdefault(p.abc_class, []).append(p)
        return {
            "plant_id": self.plant_id or "all",
            "total_parts": len(self.parts),
            "inventory_value": round(self.total_inventory_value, 2),
            "needs_reorder": self.parts_needing_reorder,
            "high_risk": self.high_risk_count,
            "by_abc": {k: len(v) for k, v in sorted(by_class.items())},
            "parts": [p.to_dict() for p in self.parts],
        }


def _abc_classify(unit_cost: float, annual_demand: float) -> str:
    annual_value = unit_cost * annual_demand
    if annual_value > 5000:
        return "A"
    if annual_value > 1000:
        return "B"
    return "C"


def _safety_stock(demand_rate: float, lead_time_days: float, service_level: float = 0.95) -> int:
    z = 1.645 if service_level >= 0.95 else 1.28
    sigma = demand_rate * 0.3  # ponytail: assume 30% demand variability
    ss = z * sigma * math.sqrt(lead_time_days / 365.0)
    return max(1, math.ceil(ss))


def _eoq(annual_demand: float, unit_cost: float, ordering_cost: float = 150.0, holding_pct: float = 0.25) -> int:
    if annual_demand <= 0 or unit_cost <= 0:
        return 1
    eoq = math.sqrt(2 * annual_demand * ordering_cost / (unit_cost * holding_pct))
    return max(1, math.ceil(eoq))


def analyze_inventory(
    plant_id: str | None = None,
    current_stock: dict[str, int] | None = None,
) -> InventoryReport:
    """Analyze spare parts inventory for one or all plants."""
    if current_stock is None:
        current_stock = {}

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    report = InventoryReport(plant_id=plant_id)
    seen_parts: set[tuple[str, str]] = set()

    for plant in plants:
        for line in plant.lines:
            for eq in line.equipment:
                catalog = _PARTS_CATALOG.get(eq.equipment_type, [])
                for part_name, cost, default_qty, lead_time in catalog:
                    key = (eq.equipment_type, part_name)
                    if key in seen_parts:
                        continue
                    seen_parts.add(key)

                    # Annual demand = equipment count × (8760 / MTBF) × parts_per_failure
                    eq_count = sum(
                        1 for p in plants for l in p.lines
                        for e in l.equipment if e.equipment_type == eq.equipment_type
                    )
                    annual_failures = eq_count * (8760.0 / eq.mtbf_hours)
                    annual_demand = annual_failures * 1.2  # 1.2 parts per failure avg

                    on_hand = current_stock.get(f"{eq.equipment_type}:{part_name}", default_qty)
                    ss = _safety_stock(annual_demand, lead_time)
                    eoq = _eoq(annual_demand, cost)
                    reorder_point = ss + math.ceil(annual_demand * lead_time / 365.0)
                    abc = _abc_classify(cost, annual_demand)

                    # Stockout risk: probability of demand exceeding on_hand during lead time
                    lead_demand = annual_demand * lead_time / 365.0
                    if lead_demand > 0:
                        stockout_risk = 1.0 - math.exp(-max(0, lead_demand - on_hand))
                        stockout_risk = min(stockout_risk, 1.0)
                    else:
                        stockout_risk = 0.0

                    part = SparePartStatus(
                        part_name=part_name,
                        equipment_type=eq.equipment_type,
                        unit_cost=cost,
                        qty_on_hand=on_hand,
                        reorder_point=reorder_point,
                        lead_time_days=lead_time,
                        abc_class=abc,
                        annual_demand=annual_demand,
                        safety_stock=ss,
                        eoq=eoq,
                        stockout_risk=stockout_risk,
                        needs_reorder=on_hand <= reorder_point,
                        annual_cost=cost * annual_demand,
                    )
                    report.parts.append(part)

    report.parts.sort(key=lambda p: (-{"A": 3, "B": 2, "C": 1}[p.abc_class], -p.stockout_risk))
    report.total_inventory_value = sum(p.unit_cost * p.qty_on_hand for p in report.parts)
    report.parts_needing_reorder = sum(1 for p in report.parts if p.needs_reorder)
    report.high_risk_count = sum(1 for p in report.parts if p.stockout_risk > 0.3)
    return report


if __name__ == "__main__":
    r = analyze_inventory("PLT-001")
    d = r.to_dict()
    print(f"PLT-001: {d['total_parts']} parts, ${d['inventory_value']:,.0f} value")
    print(f"ABC: {d['by_abc']}, reorder: {d['needs_reorder']}, high-risk: {d['high_risk']}")
    assert d['total_parts'] > 0
    assert d['inventory_value'] > 0

    all_r = analyze_inventory()
    print(f"All plants: {all_r.to_dict()['total_parts']} parts")
    assert all_r.to_dict()['total_parts'] >= d['total_parts']
    print("PASS")
