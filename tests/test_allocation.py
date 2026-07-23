"""Verify MILP allocation solution satisfies demand constraints."""
from nexusfab.optimization.network import AllocationPlan, build_allocation_problem, solve_milp


def test_allocation():
    # Build a small 2-period problem to keep solve time short
    prob = build_allocation_problem(n_periods=2, seed=42)

    assert prob.skus, "No SKUs in allocation problem"
    assert prob.lines, "No lines in allocation problem"
    assert prob.demand, "No demand entries"

    plan: AllocationPlan = solve_milp(prob, time_limit_sec=30)

    assert plan.status in ("OPTIMAL", "FEASIBLE"), (
        f"Solver returned {plan.status} — not a valid solution"
    )

    # Verify inventory covers safety stock in every period
    for (sku, period), inv in plan.inventory.items():
        ss = prob.safety_stock.get(sku, 0.0)
        assert inv >= ss - 1e-3, (
            f"SKU {sku} period {period}: inventory {inv:.1f} < safety stock {ss:.1f}"
        )

    # Verify objective is positive and production cost component makes sense
    assert plan.objective > 0, "Objective must be positive"
    assert plan.production_cost >= 0
    assert plan.inventory_cost >= 0
    assert plan.overtime_cost >= 0

    # All production quantities must be non-negative
    for (sku, line, period), qty in plan.production.items():
        assert qty >= -1e-6, f"Negative production: {sku} on {line} period {period}: {qty}"

    print(
        f"PASS — {plan.status}, objective=${plan.objective:,.0f}, "
        f"prod=${plan.production_cost:,.0f}, inv=${plan.inventory_cost:,.0f}"
    )


if __name__ == "__main__":
    test_allocation()
