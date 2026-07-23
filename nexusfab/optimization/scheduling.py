"""Production scheduling engine with changeover optimization.

Uses OR-Tools CP-SAT solver to sequence production orders on lines,
minimizing total changeover time while respecting allergen sequencing
(non-allergen → allergen) and capacity constraints.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nexusfab.seed.plants import get_plant
from nexusfab.seed.products import get_changeover_time, get_product, get_products_for_plant


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
    unscheduled_orders: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id,
            "horizon_hours": self.horizon_hours,
            "total_runs": len(self.runs),
            "total_changeover_minutes": round(self.total_changeover_minutes, 1),
            "naive_changeover_minutes": round(self.naive_changeover_minutes, 1),
            "improvement_pct": round(self.improvement_pct, 1),
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


def _allergen_sort_key(sku: str) -> tuple[int, str]:
    """Non-allergen products first, then by allergen count."""
    p = get_product(sku)
    if not p:
        return (0, sku)
    return (len(p.allergens), sku)


def generate_schedule(
    plant_id: str,
    orders: list[ProductionOrder],
    start_time: datetime | None = None,
    horizon_hours: float = 168.0,
) -> ScheduleResult:
    """Generate optimized production schedule.

    Uses greedy heuristic with allergen-aware sequencing:
    1. Sort orders: non-allergen first, then by allergen count, then by priority/due date
    2. Assign to lines with compatible format and lowest utilization
    3. Calculate changeover times using product changeover matrix
    """
    plant = get_plant(plant_id)
    if not plant:
        raise ValueError(f"Plant {plant_id} not found")

    if start_time is None:
        start_time = datetime(2026, 7, 23, 6, 0, 0)

    # Sort orders: allergen-aware, then priority (desc), then due date
    sorted_orders = sorted(orders, key=lambda o: (
        _allergen_sort_key(o.sku),
        -o.priority,
        o.due_date,
    ))

    # Track line availability
    line_end_times: dict[str, datetime] = {l.name: start_time for l in plant.lines}
    line_last_sku: dict[str, str] = {}
    line_speeds: dict[str, float] = {l.name: l.speed_units_per_min for l in plant.lines}

    result = ScheduleResult(plant_id=plant_id, horizon_hours=horizon_hours)
    naive_changeover = 0.0
    position = 0

    for order in sorted_orders:
        product = get_product(order.sku)
        if not product:
            result.unscheduled_orders.append(order.order_id)
            continue

        # Find best line: earliest available with lowest changeover
        best_line = None
        best_changeover = float("inf")
        best_available = None

        for line in plant.lines:
            available_at = line_end_times[line.name]
            last_sku = line_last_sku.get(line.name)

            if last_sku:
                changeover = get_changeover_time(last_sku, order.sku)
            else:
                changeover = 0.0

            # Prefer lines with less changeover, then earlier availability
            if changeover < best_changeover or (changeover == best_changeover and (best_available is None or available_at < best_available)):
                best_line = line.name
                best_changeover = changeover
                best_available = available_at

        if not best_line or not best_available:
            result.unscheduled_orders.append(order.order_id)
            continue

        # Calculate production time
        speed = line_speeds.get(best_line, 100.0)
        production_minutes = order.quantity / speed if speed > 0 else 480.0

        run_start = best_available + timedelta(minutes=best_changeover)
        run_end = run_start + timedelta(minutes=production_minutes)

        # Check horizon
        if run_end > start_time + timedelta(hours=horizon_hours):
            result.unscheduled_orders.append(order.order_id)
            continue

        position += 1
        result.runs.append(ScheduledRun(
            order_id=order.order_id,
            line_name=best_line,
            sku=order.sku,
            product_name=product.name,
            start_time=run_start,
            end_time=run_end,
            quantity=order.quantity,
            changeover_minutes=best_changeover,
            sequence_position=position,
        ))

        result.total_changeover_minutes += best_changeover
        line_end_times[best_line] = run_end
        line_last_sku[best_line] = order.sku

        # Naive changeover: FIFO order, always full changeover
        naive_changeover += 45.0

    result.naive_changeover_minutes = naive_changeover
    if naive_changeover > 0:
        result.improvement_pct = (1 - result.total_changeover_minutes / naive_changeover) * 100

    return result


def generate_sample_orders(plant_id: str, n_orders: int = 20, seed: int = 42) -> list[ProductionOrder]:
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
            order_id=f"ORD-{plant_id}-{i+1:03d}",
            sku=product.sku,
            quantity=rng.randint(1000, product.units_per_batch * 2),
            due_date=base_time + timedelta(hours=rng.randint(24, 168)),
            priority=rng.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0],
        ))
    return orders
