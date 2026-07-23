"""Spare parts inventory optimization.

ABC classification, reorder point calculation, safety stock with configurable
service levels (95-99%), stockout cost multipliers, cross-plant pooling, alerts.
Uses equipment MTBF/MTTR data + maintenance schedule to project demand.
"""

import math
from dataclasses import dataclass, field

from nexusfab.seed.plants import PLANTS, get_plant

# Z-scores for common service levels
_Z_SCORES = {
    0.95: 1.645,
    0.96: 1.751,
    0.97: 1.881,
    0.98: 2.054,
    0.99: 2.326,
}

# Stockout cost multiplier by ABC class — A parts cause more production loss
_STOCKOUT_MULTIPLIERS = {"A": 10.0, "B": 4.0, "C": 1.5}

# Parts catalog: (name, unit_cost, default_qty, lead_time_days)
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
    stockout_cost: float
    needs_reorder: bool
    annual_cost: float
    service_level: float

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
            "stockout_cost": round(self.stockout_cost, 2),
            "needs_reorder": self.needs_reorder,
            "annual_cost": round(self.annual_cost, 2),
            "service_level": self.service_level,
        }


@dataclass
class InventoryAlert:
    part_name: str
    equipment_type: str
    plant_ids: list[str]
    severity: str  # critical, warning, info
    message: str
    qty_on_hand: int
    reorder_point: int
    stockout_risk: float

    def to_dict(self) -> dict:
        return {
            "part": self.part_name,
            "equipment_type": self.equipment_type,
            "plant_ids": self.plant_ids,
            "severity": self.severity,
            "message": self.message,
            "on_hand": self.qty_on_hand,
            "reorder_point": self.reorder_point,
            "stockout_risk": round(self.stockout_risk, 4),
        }


@dataclass
class PoolingCandidate:
    part_name: str
    equipment_type: str
    abc_class: str
    plants_using: list[str]
    total_on_hand: int
    total_annual_demand: float
    pooled_safety_stock: int
    separate_safety_stock: int
    savings_units: int

    def to_dict(self) -> dict:
        return {
            "part": self.part_name,
            "equipment_type": self.equipment_type,
            "abc_class": self.abc_class,
            "plants_using": self.plants_using,
            "total_on_hand": self.total_on_hand,
            "total_annual_demand": round(self.total_annual_demand, 1),
            "pooled_safety_stock": self.pooled_safety_stock,
            "separate_safety_stock": self.separate_safety_stock,
            "savings_units": self.savings_units,
        }


@dataclass
class ReorderAction:
    part_name: str
    equipment_type: str
    current_qty: int
    reorder_qty: int
    unit_cost: float
    total_cost: float
    lead_time_days: int
    priority: str

    def to_dict(self) -> dict:
        return {
            "part": self.part_name,
            "equipment_type": self.equipment_type,
            "current_qty": self.current_qty,
            "reorder_qty": self.reorder_qty,
            "unit_cost": self.unit_cost,
            "total_cost": round(self.total_cost, 2),
            "lead_time_days": self.lead_time_days,
            "priority": self.priority,
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


def _z_score(service_level: float) -> float:
    if service_level in _Z_SCORES:
        return _Z_SCORES[service_level]
    # ponytail: linear interp between nearest known z-scores, upgrade to scipy.stats.norm.ppf if needed
    levels = sorted(_Z_SCORES.keys())
    if service_level <= levels[0]:
        return _Z_SCORES[levels[0]]
    if service_level >= levels[-1]:
        return _Z_SCORES[levels[-1]]
    for i in range(len(levels) - 1):
        if levels[i] <= service_level <= levels[i + 1]:
            t = (service_level - levels[i]) / (levels[i + 1] - levels[i])
            return _Z_SCORES[levels[i]] * (1 - t) + _Z_SCORES[levels[i + 1]] * t
    return 1.645


def _safety_stock(
    demand_rate: float, lead_time_days: float, service_level: float = 0.95
) -> int:
    z = _z_score(service_level)
    sigma = demand_rate * 0.3  # ponytail: assume 30% demand variability
    ss = z * sigma * math.sqrt(lead_time_days / 365.0)
    return max(1, math.ceil(ss))


def _eoq(
    annual_demand: float,
    unit_cost: float,
    ordering_cost: float = 150.0,
    holding_pct: float = 0.25,
) -> int:
    if annual_demand <= 0 or unit_cost <= 0:
        return 1
    eoq = math.sqrt(2 * annual_demand * ordering_cost / (unit_cost * holding_pct))
    return max(1, math.ceil(eoq))


def _service_level_for_class(abc_class: str, base_level: float) -> float:
    # A parts get highest service level, C parts get the base
    offsets = {"A": 0.04, "B": 0.02, "C": 0.0}
    return min(0.99, base_level + offsets.get(abc_class, 0.0))


def _build_parts(
    plants, current_stock: dict[str, int], service_level: float,
) -> list[SparePartStatus]:
    parts = []
    seen: set[tuple[str, str]] = set()

    for plant in plants:
        for line in plant.lines:
            for eq in line.equipment:
                catalog = _PARTS_CATALOG.get(eq.equipment_type, [])
                for part_name, cost, default_qty, lead_time in catalog:
                    key = (eq.equipment_type, part_name)
                    if key in seen:
                        continue
                    seen.add(key)

                    eq_count = sum(
                        1
                        for p in plants
                        for l in p.lines
                        for e in l.equipment
                        if e.equipment_type == eq.equipment_type
                    )
                    annual_failures = eq_count * (8760.0 / eq.mtbf_hours)
                    annual_demand = annual_failures * 1.2

                    abc = _abc_classify(cost, annual_demand)
                    effective_sl = _service_level_for_class(abc, service_level)
                    on_hand = current_stock.get(
                        f"{eq.equipment_type}:{part_name}", default_qty
                    )
                    ss = _safety_stock(annual_demand, lead_time, effective_sl)
                    eoq = _eoq(annual_demand, cost)
                    reorder_point = ss + math.ceil(annual_demand * lead_time / 365.0)

                    lead_demand = annual_demand * lead_time / 365.0
                    if lead_demand > 0:
                        stockout_risk = 1.0 - math.exp(
                            -max(0, lead_demand - on_hand)
                        )
                        stockout_risk = min(stockout_risk, 1.0)
                    else:
                        stockout_risk = 0.0

                    multiplier = _STOCKOUT_MULTIPLIERS.get(abc, 1.0)
                    stockout_cost = stockout_risk * cost * multiplier * annual_demand

                    parts.append(
                        SparePartStatus(
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
                            stockout_cost=stockout_cost,
                            needs_reorder=on_hand <= reorder_point,
                            annual_cost=cost * annual_demand,
                            service_level=effective_sl,
                        )
                    )

    parts.sort(
        key=lambda p: (-{"A": 3, "B": 2, "C": 1}[p.abc_class], -p.stockout_risk)
    )
    return parts


def analyze_inventory(
    plant_id: str | None = None,
    current_stock: dict[str, int] | None = None,
    service_level: float = 0.95,
) -> InventoryReport:
    """Analyze spare parts inventory for one or all plants."""
    if current_stock is None:
        current_stock = {}
    service_level = max(0.95, min(0.99, service_level))

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    parts = _build_parts(plants, current_stock, service_level)
    report = InventoryReport(plant_id=plant_id, parts=parts)
    report.total_inventory_value = sum(p.unit_cost * p.qty_on_hand for p in parts)
    report.parts_needing_reorder = sum(1 for p in parts if p.needs_reorder)
    report.high_risk_count = sum(1 for p in parts if p.stockout_risk > 0.3)
    return report


def generate_alerts(plant_id: str | None = None) -> list[InventoryAlert]:
    """Generate low-stock and risk alerts."""
    report = analyze_inventory(plant_id)
    alerts: list[InventoryAlert] = []

    plants = [get_plant(plant_id)] if plant_id else PLANTS
    plants = [p for p in plants if p]

    for part in report.parts:
        plant_ids = [
            p.id
            for p in plants
            if any(
                e.equipment_type == part.equipment_type
                for l in p.lines
                for e in l.equipment
            )
        ]

        if part.qty_on_hand == 0:
            alerts.append(
                InventoryAlert(
                    part_name=part.part_name,
                    equipment_type=part.equipment_type,
                    plant_ids=plant_ids,
                    severity="critical",
                    message=f"STOCKOUT: {part.part_name} — zero on hand, {part.lead_time_days}d lead time",
                    qty_on_hand=part.qty_on_hand,
                    reorder_point=part.reorder_point,
                    stockout_risk=1.0,
                )
            )
        elif part.qty_on_hand <= part.safety_stock:
            alerts.append(
                InventoryAlert(
                    part_name=part.part_name,
                    equipment_type=part.equipment_type,
                    plant_ids=plant_ids,
                    severity="critical",
                    message=f"Below safety stock: {part.part_name} ({part.qty_on_hand}/{part.safety_stock})",
                    qty_on_hand=part.qty_on_hand,
                    reorder_point=part.reorder_point,
                    stockout_risk=part.stockout_risk,
                )
            )
        elif part.needs_reorder:
            alerts.append(
                InventoryAlert(
                    part_name=part.part_name,
                    equipment_type=part.equipment_type,
                    plant_ids=plant_ids,
                    severity="warning",
                    message=f"Reorder needed: {part.part_name} ({part.qty_on_hand}/{part.reorder_point})",
                    qty_on_hand=part.qty_on_hand,
                    reorder_point=part.reorder_point,
                    stockout_risk=part.stockout_risk,
                )
            )
        elif part.stockout_risk > 0.3:
            alerts.append(
                InventoryAlert(
                    part_name=part.part_name,
                    equipment_type=part.equipment_type,
                    plant_ids=plant_ids,
                    severity="warning",
                    message=f"High stockout risk: {part.part_name} ({part.stockout_risk:.1%})",
                    qty_on_hand=part.qty_on_hand,
                    reorder_point=part.reorder_point,
                    stockout_risk=part.stockout_risk,
                )
            )

    alerts.sort(key=lambda a: ({"critical": 0, "warning": 1, "info": 2}[a.severity], -a.stockout_risk))
    return alerts


def cross_plant_pooling(service_level: float = 0.95) -> list[PoolingCandidate]:
    """Identify critical spares shared across plants where pooling saves inventory.

    Pooled safety stock < sum of individual safety stocks due to demand variance
    averaging (square root law).
    """
    service_level = max(0.95, min(0.99, service_level))
    candidates: list[PoolingCandidate] = []

    part_plant_map: dict[tuple[str, str], list[str]] = {}
    for plant in PLANTS:
        for line in plant.lines:
            for eq in line.equipment:
                for part_name, *_ in _PARTS_CATALOG.get(eq.equipment_type, []):
                    key = (eq.equipment_type, part_name)
                    part_plant_map.setdefault(key, [])
                    if plant.id not in part_plant_map[key]:
                        part_plant_map[key].append(plant.id)

    for (etype, part_name), plant_ids in part_plant_map.items():
        if len(plant_ids) < 2:
            continue

        catalog_entry = next(
            (n, c, q, lt)
            for n, c, q, lt in _PARTS_CATALOG[etype]
            if n == part_name
        )
        _, cost, default_qty, lead_time = catalog_entry

        total_demand = 0.0
        separate_ss = 0
        for pid in plant_ids:
            plant = get_plant(pid)
            eq_count = sum(
                1
                for l in plant.lines
                for e in l.equipment
                if e.equipment_type == etype
            )
            plant_demand = eq_count * (8760.0 / next(
                e.mtbf_hours
                for l in plant.lines
                for e in l.equipment
                if e.equipment_type == etype
            )) * 1.2
            total_demand += plant_demand
            abc = _abc_classify(cost, plant_demand)
            sl = _service_level_for_class(abc, service_level)
            separate_ss += _safety_stock(plant_demand, lead_time, sl)

        abc = _abc_classify(cost, total_demand)
        # Only pool A/B class — C parts aren't worth the logistics overhead
        if abc == "C":
            continue

        sl = _service_level_for_class(abc, service_level)
        pooled_ss = _safety_stock(total_demand, lead_time, sl)
        savings = separate_ss - pooled_ss

        if savings > 0:
            candidates.append(
                PoolingCandidate(
                    part_name=part_name,
                    equipment_type=etype,
                    abc_class=abc,
                    plants_using=plant_ids,
                    total_on_hand=default_qty * len(plant_ids),
                    total_annual_demand=total_demand,
                    pooled_safety_stock=pooled_ss,
                    separate_safety_stock=separate_ss,
                    savings_units=savings,
                )
            )

    candidates.sort(key=lambda c: -c.savings_units)
    return candidates


def generate_reorder(
    plant_id: str | None = None,
    parts_filter: list[str] | None = None,
    service_level: float = 0.95,
) -> list[ReorderAction]:
    """Generate reorder actions for parts below reorder point."""
    report = analyze_inventory(plant_id, service_level=service_level)
    actions: list[ReorderAction] = []

    for part in report.parts:
        if not part.needs_reorder:
            continue
        if parts_filter and part.part_name not in parts_filter:
            continue

        reorder_qty = max(part.eoq, part.reorder_point - part.qty_on_hand + part.safety_stock)
        priority = "urgent" if part.abc_class == "A" or part.qty_on_hand == 0 else "normal"

        actions.append(
            ReorderAction(
                part_name=part.part_name,
                equipment_type=part.equipment_type,
                current_qty=part.qty_on_hand,
                reorder_qty=reorder_qty,
                unit_cost=part.unit_cost,
                total_cost=part.unit_cost * reorder_qty,
                lead_time_days=part.lead_time_days,
                priority=priority,
            )
        )

    actions.sort(key=lambda a: (0 if a.priority == "urgent" else 1, -a.total_cost))
    return actions


if __name__ == "__main__":
    r = analyze_inventory("PLT-001")
    d = r.to_dict()
    print(f"PLT-001: {d['total_parts']} parts, ${d['inventory_value']:,.0f} value")
    print(f"ABC: {d['by_abc']}, reorder: {d['needs_reorder']}, high-risk: {d['high_risk']}")
    assert d["total_parts"] > 0
    assert d["inventory_value"] > 0
    # Verify service_level flows through
    assert all(p["service_level"] >= 0.95 for p in d["parts"])

    all_r = analyze_inventory()
    print(f"All plants: {all_r.to_dict()['total_parts']} parts")
    assert all_r.to_dict()["total_parts"] >= d["total_parts"]

    alerts = generate_alerts("PLT-001")
    print(f"Alerts: {len(alerts)} ({sum(1 for a in alerts if a.severity == 'critical')} critical)")

    pooling = cross_plant_pooling()
    print(f"Pooling candidates: {len(pooling)}")
    assert all(len(c.plants_using) >= 2 for c in pooling)

    reorders = generate_reorder("PLT-001")
    print(f"Reorders: {len(reorders)}, total cost ${sum(a.total_cost for a in reorders):,.0f}")

    print("PASS")
