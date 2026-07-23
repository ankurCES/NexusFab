"""Spare parts inventory optimization with ABC-XYZ classification.

ABC by annual spend (item count): A=top 20%, B=next 30%, C=bottom 50%
XYZ by demand CV: X<0.5 (predictable), Y 0.5–1.0 (variable), Z≥1.0 (erratic)
ROP  = avg_daily_demand × lead_time_days + safety_stock
SS   = z × sqrt(LT × σ_d² + d_avg² × σ_LT²)   [full σ_LTD formula, research §3.2]
EOQ  = sqrt(2 × D × S / (H × C))  holding H = 25%
"""

import math
from dataclasses import dataclass, field

from nexusfab.seed.plants import PLANTS, get_plant

# Z-scores for common service levels
_Z_SCORES = {
    0.90: 1.282,
    0.95: 1.645,
    0.96: 1.751,
    0.97: 1.881,
    0.98: 2.054,
    0.99: 2.326,
    0.995: 2.576,
}

# Stockout cost multiplier by ABC class — A parts cause more production loss
_STOCKOUT_MULTIPLIERS = {"A": 10.0, "B": 4.0, "C": 1.5}

# Stock policy per ABC-XYZ cell (research §1 table: Stock Policy by Cell)
_ABC_XYZ_POLICY = {
    "AX": "jit",               # always-in-stock, ROP-based auto
    "AY": "buffer",            # forecast + safety stock
    "AZ": "critical_buffer",   # 3× safety stock, insurance spare
    "BX": "kanban",            # cycle stock, ROP-based
    "BY": "on_demand_buffer",  # 0–1 unit, semi-annual review
    "BZ": "consignment",       # make-to-order or consignment
    "CX": "bulk",              # 30-day supply, min-max
    "CY": "min_stock",         # minimal stock
    "CZ": "order_on_demand",   # order on failure
}

# Safety-stock policy multiplier (AZ = 3× buffer; BZ/CZ = no stock)
_SS_POLICY_MULT: dict[str, float] = {"AZ": 3.0, "BZ": 0.0, "CZ": 0.0, "CY": 0.5}

# Equipment type → typical demand CV for XYZ classification
_EQUIPMENT_CV: dict[str, float] = {
    "FILLER": 0.60,
    "CAPPER": 0.50,
    "LABELER": 0.70,
    "CONVEYOR": 0.45,
    "MIXER": 0.60,
    "PACKAGING": 0.55,
    "PASTEURIZER": 0.55,
    "HOMOGENIZER": 0.65,
    "DRYER": 0.70,
}

# Parts catalog: (name, unit_cost, default_qty, lead_time_days)
_PARTS_CATALOG: dict[str, list[tuple]] = {
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
class SparePartsCatalog:
    """Generic spare part category with plant-level usage rates (research §3.2)."""
    part_type: str
    unit_cost: float       # representative unit cost ($, midpoint of range)
    monthly_usage: float   # units/month/plant (midpoint)
    lead_time_days: int    # procurement lead time
    cv: float              # coefficient of variation (demand variability for XYZ)


# 8 cross-cutting part categories from research §3.2
_GENERIC_CATALOG: list[SparePartsCatalog] = [
    SparePartsCatalog("Bearings",             275.0,  5.00, 10, 0.45),
    SparePartsCatalog("Seals/Gaskets",        110.0, 10.00,  4, 0.30),
    SparePartsCatalog("Motors/Drives",       8500.0,  1.25, 42, 1.40),
    SparePartsCatalog("Sensors/Instruments", 1100.0,  2.50, 21, 0.75),
    SparePartsCatalog("Conveyor Belts",      1750.0,  0.75, 18, 0.85),
    SparePartsCatalog("Heating Elements",     900.0,  2.00, 10, 0.55),
    SparePartsCatalog("Valves",               450.0,  4.00, 14, 0.60),
    SparePartsCatalog("Pump Assemblies",     4500.0,  1.00, 31, 1.10),
]


@dataclass
class SparePartStatus:
    part_name: str
    equipment_type: str
    unit_cost: float
    qty_on_hand: int
    reorder_point: int
    lead_time_days: int
    abc_class: str
    xyz_class: str
    policy: str
    annual_demand: float
    safety_stock: int
    eoq: int
    stockout_risk: float
    stockout_cost: float
    needs_reorder: bool
    annual_cost: float
    service_level: float
    turns_ratio: float  # annual_demand / avg_on_hand (eoq/2 + safety_stock)

    @property
    def abc_xyz(self) -> str:
        return self.abc_class + self.xyz_class

    def to_dict(self) -> dict:
        return {
            "part": self.part_name,
            "equipment_type": self.equipment_type,
            "unit_cost": self.unit_cost,
            "on_hand": self.qty_on_hand,
            "reorder_point": self.reorder_point,
            "lead_time_days": self.lead_time_days,
            "abc_class": self.abc_class,
            "xyz_class": self.xyz_class,
            "abc_xyz": self.abc_xyz,
            "policy": self.policy,
            "annual_demand": round(self.annual_demand, 1),
            "safety_stock": self.safety_stock,
            "eoq": self.eoq,
            "stockout_risk": round(self.stockout_risk, 4),
            "stockout_cost": round(self.stockout_cost, 2),
            "needs_reorder": self.needs_reorder,
            "annual_cost": round(self.annual_cost, 2),
            "service_level": self.service_level,
            "turns_ratio": round(self.turns_ratio, 2),
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
        by_class: dict[str, list] = {}
        by_abc_xyz: dict[str, list] = {}
        for p in self.parts:
            by_class.setdefault(p.abc_class, []).append(p)
            by_abc_xyz.setdefault(p.abc_xyz, []).append(p)
        avg_turns = (
            sum(p.turns_ratio for p in self.parts) / len(self.parts)
            if self.parts else 0.0
        )
        return {
            "plant_id": self.plant_id or "all",
            "total_parts": len(self.parts),
            "inventory_value": round(self.total_inventory_value, 2),
            "needs_reorder": self.parts_needing_reorder,
            "high_risk": self.high_risk_count,
            "by_abc": {k: len(v) for k, v in sorted(by_class.items())},
            "by_abc_xyz": {k: len(v) for k, v in sorted(by_abc_xyz.items())},
            "avg_turns_ratio": round(avg_turns, 2),
            "parts": [p.to_dict() for p in self.parts],
        }


# ---------------------------------------------------------------------------
# Core classification helpers
# ---------------------------------------------------------------------------

def _xyz_classify(cv: float) -> str:
    if cv < 0.5:
        return "X"
    if cv < 1.0:
        return "Y"
    return "Z"


def _abc_classify_list(annual_values: list[float]) -> list[str]:
    """Rank by annual spend, assign A=top 20%, B=next 30%, C=bottom 50%."""
    n = len(annual_values)
    if n == 0:
        return []
    a_cut = max(1, math.ceil(n * 0.20))
    b_cut = max(a_cut + 1, math.ceil(n * 0.50))
    ranked = sorted(range(n), key=lambda i: -annual_values[i])
    labels = [""] * n
    for rank, idx in enumerate(ranked):
        if rank < a_cut:
            labels[idx] = "A"
        elif rank < b_cut:
            labels[idx] = "B"
        else:
            labels[idx] = "C"
    return labels


def _z_score(service_level: float) -> float:
    if service_level in _Z_SCORES:
        return _Z_SCORES[service_level]
    # ponytail: linear interp; upgrade to scipy.stats.norm.ppf if needed
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
    d_avg_daily: float,
    lead_time_days: float,
    service_level: float = 0.95,
    cv: float = 0.5,
    sigma_lt_ratio: float = 0.10,
) -> int:
    """Full σ_LTD safety stock: sqrt(LT·σ_d² + d_avg²·σ_LT²)."""
    z = _z_score(service_level)
    sigma_d = cv * d_avg_daily
    sigma_lt = lead_time_days * sigma_lt_ratio
    sigma_ltd = math.sqrt(lead_time_days * sigma_d ** 2 + d_avg_daily ** 2 * sigma_lt ** 2)
    return max(0, math.ceil(z * sigma_ltd))


def _apply_policy_ss(ss: int, abc_xyz: str) -> int:
    """Apply ABC-XYZ policy multiplier: AZ→3×, BZ/CZ→0, CY→0.5×."""
    mult = _SS_POLICY_MULT.get(abc_xyz, 1.0)
    if mult == 0.0:
        return 0
    return max(0, math.ceil(ss * mult))


def _eoq(
    annual_demand: float,
    unit_cost: float,
    ordering_cost: float = 150.0,
    holding_pct: float = 0.25,
) -> int:
    if annual_demand <= 0 or unit_cost <= 0:
        return 1
    return max(1, math.ceil(math.sqrt(2 * annual_demand * ordering_cost / (unit_cost * holding_pct))))


def _service_level_for_class(abc_class: str, base_level: float) -> float:
    offsets = {"A": 0.04, "B": 0.02, "C": 0.0}
    return min(0.99, base_level + offsets.get(abc_class, 0.0))


def _abc_simple(annual_value: float) -> str:
    # ponytail: absolute thresholds for cross-plant pooling filter only; full analysis uses _abc_classify_list
    if annual_value > 5000:
        return "A"
    if annual_value > 1000:
        return "B"
    return "C"


# ---------------------------------------------------------------------------
# Equipment-catalog analysis (MTBF-driven)
# ---------------------------------------------------------------------------

def _build_parts(
    plants, current_stock: dict[str, int], service_level: float,
) -> list[SparePartStatus]:
    # Pass 1: collect raw records, deduplicated by (equipment_type, part_name)
    raw: list[tuple] = []  # (etype, pname, cost, default_qty, lt, annual_demand, cv)
    seen: set[tuple[str, str]] = set()

    for plant in plants:
        for line in plant.lines:
            for eq in line.equipment:
                cv = _EQUIPMENT_CV.get(eq.equipment_type, 0.5)
                for part_name, cost, default_qty, lead_time in _PARTS_CATALOG.get(eq.equipment_type, []):
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
                    annual_demand = eq_count * (8760.0 / eq.mtbf_hours) * 1.2
                    raw.append((eq.equipment_type, part_name, cost, default_qty, lead_time, annual_demand, cv))

    if not raw:
        return []

    # Pass 2: percentile-based ABC classification across the full set
    annual_values = [cost * demand for _, _, cost, _, _, demand, _ in raw]
    abc_labels = _abc_classify_list(annual_values)

    parts = []
    for i, (etype, pname, cost, default_qty, lead_time, annual_demand, cv) in enumerate(raw):
        abc = abc_labels[i]
        xyz = _xyz_classify(cv)
        abc_xyz = abc + xyz
        policy = _ABC_XYZ_POLICY[abc_xyz]

        sl = _service_level_for_class(abc, service_level)
        d_avg_daily = annual_demand / 365.0

        ss_raw = _safety_stock(d_avg_daily, lead_time, sl, cv)
        ss = _apply_policy_ss(ss_raw, abc_xyz)
        eoq = _eoq(annual_demand, cost)
        rop = math.ceil(d_avg_daily * lead_time) + ss

        on_hand = current_stock.get(f"{etype}:{pname}", default_qty)

        lead_demand = d_avg_daily * lead_time
        if lead_demand > 0:
            stockout_risk = min(1.0, 1.0 - math.exp(-max(0.0, lead_demand - on_hand)))
        else:
            stockout_risk = 0.0

        multiplier = _STOCKOUT_MULTIPLIERS.get(abc, 1.5)
        stockout_cost = stockout_risk * cost * multiplier * annual_demand

        avg_on_hand = max(1.0, eoq / 2 + ss)
        turns_ratio = annual_demand / avg_on_hand

        parts.append(SparePartStatus(
            part_name=pname,
            equipment_type=etype,
            unit_cost=cost,
            qty_on_hand=on_hand,
            reorder_point=rop,
            lead_time_days=lead_time,
            abc_class=abc,
            xyz_class=xyz,
            policy=policy,
            annual_demand=annual_demand,
            safety_stock=ss,
            eoq=eoq,
            stockout_risk=stockout_risk,
            stockout_cost=stockout_cost,
            needs_reorder=on_hand <= rop,
            annual_cost=cost * annual_demand,
            service_level=sl,
            turns_ratio=turns_ratio,
        ))

    parts.sort(key=lambda p: (
        -{"A": 3, "B": 2, "C": 1}[p.abc_class],
        -{"Z": 3, "Y": 2, "X": 1}[p.xyz_class],
        -p.stockout_risk,
    ))
    return parts


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_plant_parts(
    plant_id: str,
    service_level: float = 0.95,
    current_stock: dict[str, int] | None = None,
) -> list[SparePartStatus]:
    """Classify generic spare parts for a plant using ABC-XYZ + ROP/EOQ.

    Uses _GENERIC_CATALOG (8 cross-cutting part types from research §3.2).
    ABC is percentile-based across the 8 categories.
    Stockout risk = 1 - service_level (probability per replenishment cycle).
    """
    if current_stock is None:
        current_stock = {}
    service_level = max(0.90, min(0.99, service_level))

    annual_values = [c.unit_cost * c.monthly_usage * 12 for c in _GENERIC_CATALOG]
    abc_labels = _abc_classify_list(annual_values)

    parts = []
    for i, cat in enumerate(_GENERIC_CATALOG):
        annual_demand = cat.monthly_usage * 12
        d_avg_daily = annual_demand / 365.0

        abc = abc_labels[i]
        xyz = _xyz_classify(cat.cv)
        abc_xyz = abc + xyz
        policy = _ABC_XYZ_POLICY[abc_xyz]

        sl = _service_level_for_class(abc, service_level)

        ss_raw = _safety_stock(d_avg_daily, cat.lead_time_days, sl, cat.cv)
        ss = _apply_policy_ss(ss_raw, abc_xyz)
        eoq = _eoq(annual_demand, cat.unit_cost)
        rop = math.ceil(d_avg_daily * cat.lead_time_days) + ss

        on_hand = current_stock.get(cat.part_type, max(ss, round(eoq / 2 + ss)))

        stockout_risk = 1.0 - sl  # per-cycle stockout probability at target service level
        multiplier = _STOCKOUT_MULTIPLIERS.get(abc, 1.5)
        stockout_cost = stockout_risk * cat.unit_cost * multiplier * annual_demand

        avg_on_hand = max(1.0, eoq / 2 + ss)
        turns_ratio = annual_demand / avg_on_hand

        parts.append(SparePartStatus(
            part_name=cat.part_type,
            equipment_type="generic",
            unit_cost=cat.unit_cost,
            qty_on_hand=on_hand,
            reorder_point=rop,
            lead_time_days=cat.lead_time_days,
            abc_class=abc,
            xyz_class=xyz,
            policy=policy,
            annual_demand=annual_demand,
            safety_stock=ss,
            eoq=eoq,
            stockout_risk=stockout_risk,
            stockout_cost=stockout_cost,
            needs_reorder=on_hand <= rop,
            annual_cost=cat.unit_cost * annual_demand,
            service_level=sl,
            turns_ratio=turns_ratio,
        ))

    parts.sort(key=lambda p: (
        -{"A": 3, "B": 2, "C": 1}[p.abc_class],
        -{"Z": 3, "Y": 2, "X": 1}[p.xyz_class],
    ))
    return parts


def analyze_inventory(
    plant_id: str | None = None,
    current_stock: dict[str, int] | None = None,
    service_level: float = 0.95,
) -> InventoryReport:
    """Analyze spare parts inventory for one or all plants (equipment-catalog driven)."""
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
            alerts.append(InventoryAlert(
                part_name=part.part_name,
                equipment_type=part.equipment_type,
                plant_ids=plant_ids,
                severity="critical",
                message=f"STOCKOUT: {part.part_name} — zero on hand, {part.lead_time_days}d lead time",
                qty_on_hand=part.qty_on_hand,
                reorder_point=part.reorder_point,
                stockout_risk=1.0,
            ))
        elif part.qty_on_hand <= part.safety_stock:
            alerts.append(InventoryAlert(
                part_name=part.part_name,
                equipment_type=part.equipment_type,
                plant_ids=plant_ids,
                severity="critical",
                message=f"Below safety stock: {part.part_name} ({part.qty_on_hand}/{part.safety_stock})",
                qty_on_hand=part.qty_on_hand,
                reorder_point=part.reorder_point,
                stockout_risk=part.stockout_risk,
            ))
        elif part.needs_reorder:
            alerts.append(InventoryAlert(
                part_name=part.part_name,
                equipment_type=part.equipment_type,
                plant_ids=plant_ids,
                severity="warning",
                message=f"Reorder needed: {part.part_name} ({part.qty_on_hand}/{part.reorder_point})",
                qty_on_hand=part.qty_on_hand,
                reorder_point=part.reorder_point,
                stockout_risk=part.stockout_risk,
            ))
        elif part.stockout_risk > 0.3:
            alerts.append(InventoryAlert(
                part_name=part.part_name,
                equipment_type=part.equipment_type,
                plant_ids=plant_ids,
                severity="warning",
                message=f"High stockout risk: {part.part_name} ({part.stockout_risk:.1%})",
                qty_on_hand=part.qty_on_hand,
                reorder_point=part.reorder_point,
                stockout_risk=part.stockout_risk,
            ))

    alerts.sort(key=lambda a: ({"critical": 0, "warning": 1, "info": 2}[a.severity], -a.stockout_risk))
    return alerts


def cross_plant_pooling(service_level: float = 0.95) -> list[PoolingCandidate]:
    """Identify A/B spares shared across plants where pooling reduces safety stock.

    Square-root law: pooled SS < sum of individual SS when demand is independent.
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
            (n, c, q, lt) for n, c, q, lt in _PARTS_CATALOG[etype] if n == part_name
        )
        _, cost, default_qty, lead_time = catalog_entry
        cv = _EQUIPMENT_CV.get(etype, 0.5)

        total_demand = 0.0
        separate_ss = 0
        for pid in plant_ids:
            plant = get_plant(pid)
            eq_count = sum(
                1 for l in plant.lines for e in l.equipment if e.equipment_type == etype
            )
            plant_demand = eq_count * (8760.0 / next(
                e.mtbf_hours for l in plant.lines for e in l.equipment if e.equipment_type == etype
            )) * 1.2
            total_demand += plant_demand
            sl = _service_level_for_class(_abc_simple(cost * plant_demand), service_level)
            separate_ss += _safety_stock(plant_demand / 365.0, lead_time, sl, cv)

        # ponytail: absolute thresholds for pool filter — only A/B class worth the logistics overhead
        if _abc_simple(cost * total_demand) == "C":
            continue

        sl = _service_level_for_class(_abc_simple(cost * total_demand), service_level)
        pooled_ss = _safety_stock(total_demand / 365.0, lead_time, sl, cv)
        savings = separate_ss - pooled_ss

        if savings > 0:
            candidates.append(PoolingCandidate(
                part_name=part_name,
                equipment_type=etype,
                abc_class=_abc_simple(cost * total_demand),
                plants_using=plant_ids,
                total_on_hand=default_qty * len(plant_ids),
                total_annual_demand=total_demand,
                pooled_safety_stock=pooled_ss,
                separate_safety_stock=separate_ss,
                savings_units=savings,
            ))

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

        actions.append(ReorderAction(
            part_name=part.part_name,
            equipment_type=part.equipment_type,
            current_qty=part.qty_on_hand,
            reorder_qty=reorder_qty,
            unit_cost=part.unit_cost,
            total_cost=part.unit_cost * reorder_qty,
            lead_time_days=part.lead_time_days,
            priority=priority,
        ))

    actions.sort(key=lambda a: (0 if a.priority == "urgent" else 1, -a.total_cost))
    return actions


if __name__ == "__main__":
    # --- Generic ABC-XYZ classification for PLT-001 ---
    parts = classify_plant_parts("PLT-001")

    print("=== ABC-XYZ Spare Parts Matrix — PLT-001 ===\n")
    col_w = 24
    print(f"{'':18}  {'X (CV<0.5)':^{col_w}}  {'Y (0.5≤CV<1.0)':^{col_w}}  {'Z (CV≥1.0)':^{col_w}}")
    print("-" * (18 + 3 * (col_w + 2)))
    abc_labels_display = {"A": "A (top 20% spend)", "B": "B (next 30%)", "C": "C (bottom 50%)"}
    for abc in ("A", "B", "C"):
        cells = []
        for xyz in ("X", "Y", "Z"):
            cell = [p for p in parts if p.abc_class == abc and p.xyz_class == xyz]
            if cell:
                names = " / ".join(p.part_name for p in cell)
                cells.append(f"{names[:col_w]:^{col_w}}")
            else:
                cells.append(f"{'—':^{col_w}}")
        print(f"{abc_labels_display[abc]:18}  {'  '.join(cells)}")

    print()
    print(f"{'Part':<22} {'Class':7} {'Policy':<20} {'ROP':>4} {'EOQ':>4} {'SS':>4} {'Turns':>6} {'Annual $':>10}")
    print("-" * 82)
    for p in parts:
        print(
            f"{p.part_name:<22} {p.abc_xyz:7} {p.policy:<20} "
            f"{p.reorder_point:>4} {p.eoq:>4} {p.safety_stock:>4} "
            f"{p.turns_ratio:>6.1f} {p.annual_cost:>10,.0f}"
        )

    inv_value = sum(p.unit_cost * p.qty_on_hand for p in parts)
    print(f"\nInventory value: ${inv_value:,.0f}  |  Parts: {len(parts)}")

    # Assertions
    assert any(p.abc_class == "A" for p in parts), "No A-class parts"
    assert any(p.xyz_class == "Z" for p in parts), "No Z-class parts"
    assert all(p.policy in _ABC_XYZ_POLICY.values() for p in parts), "Unknown policy"
    assert all(p.turns_ratio > 0 for p in parts), "Non-positive turns ratio"

    # --- Equipment-catalog analysis (backward compat) ---
    r = analyze_inventory("PLT-001")
    d = r.to_dict()
    print(f"\nEquipment-catalog: {d['total_parts']} parts, ${d['inventory_value']:,.0f}, "
          f"by_abc={d['by_abc']}, avg_turns={d['avg_turns_ratio']}")
    assert d["total_parts"] > 0
    assert d["inventory_value"] > 0
    assert all(p["service_level"] >= 0.95 for p in d["parts"])

    all_r = analyze_inventory()
    assert all_r.to_dict()["total_parts"] >= d["total_parts"]

    alerts = generate_alerts("PLT-001")
    print(f"Alerts: {len(alerts)} ({sum(1 for a in alerts if a.severity == 'critical')} critical)")

    pooling = cross_plant_pooling()
    print(f"Pooling candidates: {len(pooling)}")
    assert all(len(c.plants_using) >= 2 for c in pooling)

    reorders = generate_reorder("PLT-001")
    print(f"Reorders: {len(reorders)}, total cost ${sum(a.total_cost for a in reorders):,.0f}")

    print("\nPASS")
