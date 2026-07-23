"""Production scheduling engine with changeover optimization.

Uses OR-Tools CP-SAT solver to sequence production orders on lines,
minimizing total changeover time while respecting allergen sequencing
(non-allergen before allergen) and format compatibility constraints.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ortools.sat.python import cp_model

from nexusfab.seed.plants import get_plant
from nexusfab.seed.products import get_changeover_time, get_product, get_products_for_plant

# ponytail: flat dict, one entry per line_type→formats. Add entries when new lines/formats appear.
LINE_FORMAT_COMPAT: dict[str, set[str]] = {
    "PET_BOTTLING": {"PET_500", "PET_750", "PET_1L", "PET_15L"},
    "GLASS_BOTTLING": {"PET_750"},
    "CANNING": set(),
    "MOULDING": {"BAR_4F", "BAR_STD"},
    "ENROBING": {"BAR_4F", "BAR_STD", "SEASONAL"},
    "WRAPPING": {"MULTIPACK", "SEASONAL"},
    "UHT_FILLING": {"UHT_200", "UHT_500", "UHT_1L"},
    "POWDER_PACKING": {"TIN_400", "TIN_900", "TIN_1800"},
    "ASEPTIC": {"UHT_200", "UHT_500", "UHT_1L"},
    "EXTRUSION": {"BAG_1K", "BAG_5K", "BAG_15K"},
    "RETORT_CANNING": {"CAN_85", "CAN_400"},
    "KIBBLE_COATING": {"BAG_1K", "BAG_5K", "POUCH"},
    "MIXING_COOKING": {"PACK_70", "SACHET_8", "CUP_65"},
    "FILLING": {"BOTTLE_200", "BOTTLE_500", "SACHET_8"},
    "NOODLE_LINE": {"PACK_70", "MULTIPACK", "CUP_65"},
}


@dataclass
class ProductionOrder:
    order_id: str
    sku: str
    quantity: int
    due_date: datetime
    priority: int = 1  # 1=normal, 2=high, 3=urgent


@dataclass
class ScheduledRun:
    order_id: str
    line_name: str
    sku: str
    product_name: str
    start_time: datetime
    end_time: datetime
    quantity: int
    changeover_minutes: float
    sequence_position: int


@dataclass
class ScheduleResult:
    plant_id: str
    horizon_hours: float
    runs: list[ScheduledRun] = field(default_factory=list)
    total_changeover_minutes: float = 0.0
    naive_changeover_minutes: float = 0.0
    improvement_pct: float = 0.0
    solver_status: str = ""
    unscheduled_orders: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id,
            "horizon_hours": self.horizon_hours,
            "total_runs": len(self.runs),
            "total_changeover_minutes": round(self.total_changeover_minutes, 1),
            "naive_changeover_minutes": round(self.naive_changeover_minutes, 1),
            "improvement_pct": round(self.improvement_pct, 1),
            "solver_status": self.solver_status,
            "unscheduled_orders": self.unscheduled_orders,
            "schedule": [
                {
                    "order_id": r.order_id,
                    "line": r.line_name,
                    "sku": r.sku,
                    "product": r.product_name,
                    "start": r.start_time.isoformat(),
                    "end": r.end_time.isoformat(),
                    "quantity": r.quantity,
                    "changeover_min": r.changeover_minutes,
                    "position": r.sequence_position,
                }
                for r in self.runs
            ],
        }


def _line_compatible(line_type: str, format_type: str) -> bool:
    return format_type in LINE_FORMAT_COMPAT.get(line_type, set())


def _fifo_baseline(plant_id: str, orders: list[ProductionOrder]) -> float:
    """Total changeover if we process orders in arrival (FIFO) order on first compatible line."""
    plant = get_plant(plant_id)
    if not plant:
        return 0.0

    line_last_sku: dict[str, str] = {}
    line_load: dict[str, int] = {ln.name: 0 for ln in plant.lines}
    total = 0.0

    for order in orders:
        product = get_product(order.sku)
        if not product:
            continue
        best_line = None
        best_load = float("inf")
        for line in plant.lines:
            if not _line_compatible(line.line_type, product.format_type):
                continue
            if line_load[line.name] < best_load:
                best_line = line.name
                best_load = line_load[line.name]
        if not best_line:
            continue
        last = line_last_sku.get(best_line)
        if last:
            total += get_changeover_time(last, order.sku)
        line_last_sku[best_line] = order.sku
        line_load[best_line] += 1

    return total


def _optimize_line_sequence(
    orders: list[ProductionOrder],
    time_limit: float = 10.0,
) -> tuple[list[int], list[float], str]:
    """CP-SAT circuit constraint to find minimum-changeover sequence on one line.

    Enforces allergen ordering: all non-allergen orders before any allergen order.
    Returns (index_sequence, changeover_per_position, solver_status_name).
    """
    n = len(orders)

    # Precompute changeover costs between all order pairs
    co: dict[tuple[int, int], float] = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                co[(i, j)] = get_changeover_time(orders[i].sku, orders[j].sku)

    scale = 10  # ponytail: integer scale for CP-SAT, 0.1 min precision

    model = cp_model.CpModel()

    # Circuit: nodes 0..n-1 are orders, node n is depot
    arcs: list[tuple[int, int, cp_model.IntVar]] = []
    arc_vars: dict[tuple[int, int], cp_model.IntVar] = {}
    for i in range(n + 1):
        for j in range(n + 1):
            if i == j:
                continue
            lit = model.new_bool_var(f"a_{i}_{j}")
            arcs.append((i, j, lit))
            arc_vars[(i, j)] = lit

    model.add_circuit(arcs)

    # Objective: minimize changeover between consecutive orders (depot arcs cost 0)
    model.minimize(sum(
        int(co[(i, j)] * scale) * arc_vars[(i, j)]
        for i in range(n) for j in range(n) if i != j
    ))

    # Position variables for allergen ordering
    pos = [model.new_int_var(0, n - 1, f"p_{i}") for i in range(n)]
    model.add_all_different(pos)

    # Link positions to circuit: depot→j ⇒ pos[j]=0, i→j ⇒ pos[j]=pos[i]+1
    for j in range(n):
        model.add(pos[j] == 0).only_enforce_if(arc_vars[(n, j)])
        for i in range(n):
            if i != j:
                model.add(pos[j] == pos[i] + 1).only_enforce_if(arc_vars[(i, j)])

    # Allergen constraint: non-allergen orders before allergen orders
    for i in range(n):
        pi = get_product(orders[i].sku)
        if pi and pi.allergens:
            continue  # i has allergens, skip
        for j in range(n):
            if i == j:
                continue
            pj = get_product(orders[j].sku)
            if pj and pj.allergens:
                model.add(pos[i] < pos[j])

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.solve(model)
    status_name = solver.status_name(status)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        seq = sorted(range(n), key=lambda i: solver.value(pos[i]))
        changeovers = [0.0]
        for k in range(1, len(seq)):
            changeovers.append(co[(seq[k - 1], seq[k])])
        return seq, changeovers, status_name

    # Fallback: allergen-sorted by due date
    seq = sorted(range(n), key=lambda i: (
        len(get_product(orders[i].sku).allergens) if get_product(orders[i].sku) else 0,
        orders[i].due_date,
    ))
    changeovers = [0.0]
    for k in range(1, len(seq)):
        changeovers.append(get_changeover_time(orders[seq[k - 1]].sku, orders[seq[k]].sku))
    return seq, changeovers, f"FALLBACK({status_name})"


def generate_schedule(
    plant_id: str,
    orders: list[ProductionOrder],
    start_time: datetime | None = None,
    horizon_hours: float = 168.0,
    solver_time_limit: float = 30.0,
) -> ScheduleResult:
    """Generate optimized schedule: assign orders to format-compatible lines, then
    sequence each line via CP-SAT to minimize changeover while enforcing allergen ordering."""
    plant = get_plant(plant_id)
    if not plant:
        raise ValueError(f"Plant {plant_id} not found")

    if start_time is None:
        start_time = datetime(2026, 7, 23, 6, 0, 0)

    result = ScheduleResult(plant_id=plant_id, horizon_hours=horizon_hours)
    result.naive_changeover_minutes = _fifo_baseline(plant_id, orders)

    # Phase 1: format-aware assignment — group same-format orders on same line
    line_orders: dict[str, list[ProductionOrder]] = {ln.name: [] for ln in plant.lines}
    line_formats: dict[str, set[str]] = {ln.name: set() for ln in plant.lines}

    assignable: list[tuple[ProductionOrder, str]] = []
    for order in orders:
        product = get_product(order.sku)
        if not product:
            result.unscheduled_orders.append(order.order_id)
            continue
        assignable.append((order, product.format_type))

    # Sort by format to cluster same-format orders together during assignment
    assignable.sort(key=lambda x: x[1])

    for order, fmt in assignable:
        best_line = None
        best_score = (float("inf"), float("inf"))
        for line in plant.lines:
            if not _line_compatible(line.line_type, fmt):
                continue
            fmts = line_formats[line.name]
            # Prefer: same format already present (0), empty line (1), new format on busy line (2)
            pen = 0 if fmt in fmts else (1 if not fmts else 2)
            score = (pen, len(line_orders[line.name]))
            if score < best_score:
                best_line = line.name
                best_score = score
        if best_line is None:
            result.unscheduled_orders.append(order.order_id)
            continue
        line_orders[best_line].append(order)
        line_formats[best_line].add(fmt)

    # Phase 2: optimize sequence per line
    line_speeds = {ln.name: ln.speed_units_per_min for ln in plant.lines}
    n_lines = max(sum(1 for v in line_orders.values() if v), 1)
    per_line_limit = solver_time_limit / n_lines
    total_changeover = 0.0
    statuses: list[str] = []

    for line_name, line_ords in line_orders.items():
        if not line_ords:
            continue

        if len(line_ords) == 1:
            seq, changeovers = [0], [0.0]
        else:
            seq, changeovers, st = _optimize_line_sequence(line_ords, per_line_limit)
            statuses.append(st)

        current_time = start_time
        for pos_idx, order_idx in enumerate(seq):
            order = line_ords[order_idx]
            product = get_product(order.sku)
            co_min = changeovers[pos_idx]

            run_start = current_time + timedelta(minutes=co_min)
            speed = line_speeds.get(line_name, 100.0)
            prod_min = order.quantity / speed if speed > 0 else 480.0
            run_end = run_start + timedelta(minutes=prod_min)

            if run_end > start_time + timedelta(hours=horizon_hours):
                result.unscheduled_orders.append(order.order_id)
                continue

            result.runs.append(ScheduledRun(
                order_id=order.order_id,
                line_name=line_name,
                sku=order.sku,
                product_name=product.name if product else order.sku,
                start_time=run_start,
                end_time=run_end,
                quantity=order.quantity,
                changeover_minutes=co_min,
                sequence_position=pos_idx + 1,
            ))
            total_changeover += co_min
            current_time = run_end

    result.total_changeover_minutes = total_changeover
    result.solver_status = "; ".join(statuses) if statuses else "trivial"
    if result.naive_changeover_minutes > 0:
        result.improvement_pct = (
            (1 - result.total_changeover_minutes / result.naive_changeover_minutes) * 100
        )

    return result


def generate_sample_orders(
    plant_id: str, n_orders: int = 20, seed: int = 42,
) -> list[ProductionOrder]:
    """Generate sample orders for testing."""
    import random

    rng = random.Random(seed)
    products = get_products_for_plant(plant_id)
    if not products:
        return []

    base_time = datetime(2026, 7, 23, 6, 0, 0)
    orders = []
    for i in range(n_orders):
        product = rng.choice(products)
        orders.append(ProductionOrder(
            order_id=f"ORD-{plant_id}-{i + 1:03d}",
            sku=product.sku,
            quantity=rng.randint(1000, product.units_per_batch * 2),
            due_date=base_time + timedelta(hours=rng.randint(24, 168)),
            priority=rng.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0],
        ))
    return orders


if __name__ == "__main__":
    import time

    for plant_id in ("PLT-001", "PLT-002", "PLT-005"):
        orders = generate_sample_orders(plant_id, n_orders=25, seed=42)
        assert orders, f"No orders for {plant_id}"

        t0 = time.monotonic()
        result = generate_schedule(plant_id, orders)
        elapsed = time.monotonic() - t0

        print(f"\n{'='*60}")
        print(f"Plant {plant_id}  |  {len(orders)} orders → {len(result.runs)} scheduled")
        print(f"Solver: {result.solver_status} in {elapsed:.1f}s")
        print(f"FIFO changeover:      {result.naive_changeover_minutes:.0f} min")
        print(f"Optimized changeover: {result.total_changeover_minutes:.0f} min")
        print(f"Improvement:          {result.improvement_pct:.1f}%")
        print(f"Unscheduled:          {result.unscheduled_orders}")

        # AC2: 30%+ improvement over FIFO
        assert result.improvement_pct >= 30, (
            f"{plant_id}: only {result.improvement_pct:.1f}% improvement (need 30%+)"
        )

        # AC4: under 30 seconds
        assert elapsed < 30, f"{plant_id}: solver took {elapsed:.1f}s (limit 30s)"

        # AC3: allergen sequencing — on each line, non-allergen runs before allergen runs
        by_line: dict[str, list[ScheduledRun]] = {}
        for r in result.runs:
            by_line.setdefault(r.line_name, []).append(r)
        for ln, runs in by_line.items():
            runs_sorted = sorted(runs, key=lambda r: r.sequence_position)
            seen_allergen = False
            for r in runs_sorted:
                p = get_product(r.sku)
                has_allergen = bool(p and p.allergens)
                if seen_allergen and not has_allergen:
                    raise AssertionError(
                        f"{ln}: non-allergen {r.sku} at pos {r.sequence_position} after allergen"
                    )
                if has_allergen:
                    seen_allergen = True

        # AC5: Gantt JSON export
        gantt = result.to_dict()
        assert "schedule" in gantt
        assert gantt["total_runs"] == len(result.runs)

        # Print first 5 runs as sample
        print("Sample schedule (first 5 runs):")
        for r in result.runs[:5]:
            st = r.start_time.strftime("%H:%M")
            et = r.end_time.strftime("%H:%M")
            print(f"  {r.sequence_position:2d}. [{r.line_name}] {r.sku:10s} "
                  f"CO={r.changeover_minutes:5.0f}m  {st}-{et}")

    print(f"\n{'='*60}")
    print("All checks passed.")
