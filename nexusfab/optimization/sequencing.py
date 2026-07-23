"""Production sequencing optimizer — Asymmetric TSP via OR-Tools CP-SAT.

Algorithm: CP-SAT circuit constraint (Hamiltonian path/circuit) with:
- Soft allergen violation penalty (tier regression costs full CIP)
- Hard CIP frequency check for UHT lines (12h limit)
- SMED split: 60% internal (line stopped) / 40% external (parallel)
- Late-order penalty in objective via cumulative position estimates
- Minimum batch size guard (< 2h runs skip changeover cost)

See docs/research/production-operations.md §5.4 for problem formulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from nexusfab.seed.products import get_changeover_time, get_product

# ── SMED constants (§5.2) ────────────────────────────────────────────────────
SMED_INTERNAL_RATIO = 0.60      # fraction of changeover where line is stopped
SMED_EXTERNAL_RATIO = 0.40      # fraction parallelized during last batch

# ── Penalty / cost constants ──────────────────────────────────────────────────
ALLERGEN_VIOLATION_COST = 90    # minutes — full CIP cost for tier regression
LATE_PENALTY_PER_MIN = 5        # minutes of changeover equivalent per min late
UHT_CIP_INTERVAL_H = 12        # hard limit: no UHT run > 12h without CIP
MIN_BATCH_H = 2.0               # batches shorter than this skip changeover cost

# CP-SAT uses integers; scale minutes × 10 for 0.1 min resolution
_SCALE = 10


# ── Problem / solution types ──────────────────────────────────────────────────

@dataclass
class SequencingProblem:
    line_id: str
    products: list[str]                       # SKU ids in any initial order
    changeover_matrix: dict[str, dict[str, float]]  # {from: {to: minutes}}
    due_dates: dict[str, float] = field(default_factory=dict)   # {sku: minutes_from_now}
    batch_hours: dict[str, float] = field(default_factory=dict) # {sku: hours per run}
    is_uht_line: bool = False                  # enables CIP-interval check


@dataclass
class SequencingSolution:
    sequence: list[str]
    total_changeover_min: float       # raw sum of changeover times
    effective_changeover_min: float   # after SMED external parallelism
    smed_savings_min: float
    makespan: float                   # total hours (batch + internal changeover)
    late_orders: list[str]
    allergen_violations: int
    cip_interval_warning: bool        # True if UHT 12h limit would be breached
    solver_status: str


# ── Core optimizer ────────────────────────────────────────────────────────────

def optimize_sequence(
    problem: SequencingProblem,
    time_limit_sec: int = 30,
) -> SequencingSolution:
    """CP-SAT circuit-constraint TSP for production sequencing."""
    skus = problem.products
    n = len(skus)
    idx = {sku: i for i, sku in enumerate(skus)}

    # Build integer cost matrix (scaled)
    def _cost(i: int, j: int) -> int:
        if i == j:
            return 0
        from_sku, to_sku = skus[i], skus[j]
        raw = problem.changeover_matrix.get(from_sku, {}).get(to_sku, 60.0)
        # Minimum batch size guard: skip changeover cost for very short runs
        batch_h = problem.batch_hours.get(to_sku, MIN_BATCH_H)
        if batch_h < MIN_BATCH_H:
            raw = 0.0
        # Allergen soft penalty: tier regression → +full CIP cost
        p_from = get_product(from_sku)
        p_to = get_product(to_sku)
        if p_from and p_to and p_to.allergen_tier < p_from.allergen_tier:
            raw += ALLERGEN_VIOLATION_COST
        return round(raw * _SCALE)

    costs = [[_cost(i, j) for j in range(n)] for i in range(n)]

    # Due-date penalty: estimate position-weighted late cost
    # Naive: each position adds avg_batch time; weight objective by order priority
    avg_batch_min = sum(
        problem.batch_hours.get(s, 4.0) for s in skus
    ) / n * 60

    model = cp_model.CpModel()

    # x[i,j] = 1 if sku i is immediately followed by sku j
    x = {
        (i, j): model.new_bool_var(f"x_{i}_{j}")
        for i in range(n) for j in range(n) if i != j
    }

    # Circuit constraint: enforces Hamiltonian path (open path via dummy depot)
    # ponytail: depot node (index n) converts circuit→path; 0 cost arcs to/from it
    depot = n
    arcs: list[tuple[int, int, cp_model.IntVar | bool]] = []
    for i in range(n):
        for j in range(n):
            if i != j:
                arcs.append((i, j, x[i, j]))
    # Depot arcs: each node can start or end the path via the depot
    depot_out = [model.new_bool_var(f"d_out_{j}") for j in range(n)]
    depot_in  = [model.new_bool_var(f"d_in_{i}")  for i in range(n)]
    for j in range(n):
        arcs.append((depot, j, depot_out[j]))
    for i in range(n):
        arcs.append((i, depot, depot_in[i]))
    # Exactly one start and one end
    model.add_exactly_one(depot_out)
    model.add_exactly_one(depot_in)
    model.add_circuit(arcs)

    # Objective: minimize total changeover + allergen violation already in costs
    # Late penalty: soft weight for products with tight due dates
    late_weights: dict[int, int] = {}
    if problem.due_dates:
        for i, sku in enumerate(skus):
            dd = problem.due_dates.get(sku)
            if dd is not None:
                # proxy: products due sooner get higher penalty if placed late
                slack_positions = max(1, int(dd / avg_batch_min))
                if slack_positions < n:
                    late_weights[i] = round(
                        LATE_PENALTY_PER_MIN * (n - slack_positions) * _SCALE
                    )

    obj_terms = []
    for i in range(n):
        for j in range(n):
            if i != j:
                weight = costs[i][j]
                if j in late_weights:
                    weight += late_weights[j]
                obj_terms.append(weight * x[i, j])

    model.minimize(sum(obj_terms))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_sec
    solver.parameters.log_search_progress = False
    status = solver.solve(model)
    status_name = solver.status_name(status)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # Fallback: allergen-sorted nearest-neighbor
        seq = _allergen_nn_sequence(skus, problem.changeover_matrix)
    else:
        seq = _extract_sequence(solver, x, skus, n, depot_in)

    return _build_solution(seq, problem, status_name)


def _extract_sequence(
    solver: cp_model.CpSolver,
    x: dict,
    skus: list[str],
    n: int,
    depot_in: list,
) -> list[str]:
    """Walk the circuit to extract ordered sequence."""
    nxt: dict[int, int] = {}
    for i in range(n):
        for j in range(n):
            if i != j and solver.value(x[i, j]) == 1:
                nxt[i] = j
    # Start node has no real-node predecessor (only depot points to it)
    has_predecessor = set(nxt.values())
    starts = [i for i in range(n) if i not in has_predecessor]
    start = starts[0] if starts else 0
    seq, cur = [], start
    while len(seq) < n:
        seq.append(skus[cur])
        if cur not in nxt:
            break
        cur = nxt[cur]
    return seq


def _build_solution(
    seq: list[str],
    problem: SequencingProblem,
    status: str,
) -> SequencingSolution:
    """Compute derived metrics from a sequence."""
    skus = seq
    total_co = sum(
        problem.changeover_matrix.get(skus[i], {}).get(skus[i + 1], 60.0)
        for i in range(len(skus) - 1)
    )
    # SMED: external 40% runs in parallel with the previous batch's last 30 min
    effective_co = total_co * SMED_INTERNAL_RATIO
    smed_savings = total_co * SMED_EXTERNAL_RATIO

    # Makespan: sum batch hours + internal changeover
    batch_min = sum(problem.batch_hours.get(s, 4.0) * 60 for s in skus)
    makespan_h = (batch_min + effective_co) / 60

    # Late orders: cumulative time check vs due dates
    late: list[str] = []
    if problem.due_dates:
        t = 0.0
        for i, sku in enumerate(skus):
            t += problem.batch_hours.get(sku, 4.0) * 60
            if i < len(skus) - 1:
                t += problem.changeover_matrix.get(sku, {}).get(skus[i + 1], 60.0) * SMED_INTERNAL_RATIO
            dd = problem.due_dates.get(sku)
            if dd is not None and t > dd:
                late.append(sku)

    # Allergen violations
    violations = 0
    for i in range(len(skus) - 1):
        p_from = get_product(skus[i])
        p_to = get_product(skus[i + 1])
        if p_from and p_to and p_to.allergen_tier < p_from.allergen_tier:
            violations += 1

    # UHT CIP check
    cip_warn = False
    if problem.is_uht_line:
        run = 0.0
        for s in skus:
            run += problem.batch_hours.get(s, 4.0)
            if run > UHT_CIP_INTERVAL_H:
                cip_warn = True
                break

    return SequencingSolution(
        sequence=skus,
        total_changeover_min=round(total_co, 1),
        effective_changeover_min=round(effective_co, 1),
        smed_savings_min=round(smed_savings, 1),
        makespan=round(makespan_h, 2),
        late_orders=late,
        allergen_violations=violations,
        cip_interval_warning=cip_warn,
        solver_status=status,
    )


# ── Baseline comparators ──────────────────────────────────────────────────────

def fifo_sequence(problem: SequencingProblem) -> SequencingSolution:
    """Baseline: keep original order (FIFO)."""
    return _build_solution(list(problem.products), problem, "FIFO")


def allergen_sorted_sequence(problem: SequencingProblem) -> SequencingSolution:
    """Baseline: sort by allergen tier ascending (greedy rule, no TSP)."""
    skus = sorted(
        problem.products,
        key=lambda s: (get_product(s).allergen_tier if get_product(s) else 0),
    )
    return _build_solution(skus, problem, "ALLERGEN_SORT")


def _allergen_nn_sequence(
    skus: list[str],
    matrix: dict[str, dict[str, float]],
) -> list[str]:
    """Nearest-neighbor fallback: respect allergen tiers, minimize changeover."""
    remaining = list(skus)
    current = min(remaining, key=lambda s: get_product(s).allergen_tier if get_product(s) else 0)
    order = [current]
    remaining.remove(current)
    while remaining:
        cur_tier = get_product(current).allergen_tier if get_product(current) else 0
        eligible = [s for s in remaining if (get_product(s).allergen_tier if get_product(s) else 0) >= cur_tier]
        if not eligible:
            eligible = remaining
        current = min(eligible, key=lambda s: matrix.get(current, {}).get(s, 60.0))
        order.append(current)
        remaining.remove(current)
    return order


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_changeover_matrix(skus: list[str]) -> dict[str, dict[str, float]]:
    """Build asymmetric matrix from product catalog data."""
    return {
        from_sku: {
            to_sku: get_changeover_time(from_sku, to_sku)
            for to_sku in skus if to_sku != from_sku
        }
        for from_sku in skus
    }


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from nexusfab.seed.products import get_products_for_plant

    # 10-product mix on PLT-001-L1: all 6 PLT-001 SKUs + 4 PLT-005 products
    # (PLT-005 has allergen variety — SOY, GLUTEN, SESAME — making sequencing non-trivial)
    plt001 = [p.sku for p in get_products_for_plant("PLT-001")]
    plt005 = [p.sku for p in get_products_for_plant("PLT-005")]
    demo_skus = (plt001 + plt005)[:10]

    matrix = build_changeover_matrix(demo_skus)

    # Realistic batch hours: 4h average production run per SKU
    batch_hours = {s: 4.0 for s in demo_skus}
    # Two tight due dates to exercise late-order detection
    due_dates = {demo_skus[0]: 300.0, demo_skus[3]: 500.0}  # minutes from now

    problem = SequencingProblem(
        line_id="PLT-001-L1",
        products=demo_skus,
        changeover_matrix=matrix,
        due_dates=due_dates,
        batch_hours=batch_hours,
        is_uht_line=False,
    )

    print(f"\n{'─'*60}")
    print(f"Sequencing {len(demo_skus)} products on {problem.line_id}")
    print(f"{'─'*60}")

    opt   = optimize_sequence(problem, time_limit_sec=30)
    fifo  = fifo_sequence(problem)
    allg  = allergen_sorted_sequence(problem)

    def _fmt(sol: SequencingSolution, label: str) -> None:
        print(f"\n[{label}] status={sol.solver_status}")
        print(f"  Sequence : {' → '.join(sol.sequence)}")
        print(f"  Raw CO   : {sol.total_changeover_min:.0f} min")
        print(f"  Effective: {sol.effective_changeover_min:.0f} min  (SMED saves {sol.smed_savings_min:.0f} min)")
        print(f"  Makespan : {sol.makespan:.1f} h")
        print(f"  Late orders: {sol.late_orders or '—'}")
        print(f"  Allergen violations: {sol.allergen_violations}")
        if sol.cip_interval_warning:
            print("  ⚠ CIP interval warning: UHT 12h limit would be breached")

    _fmt(opt,  "CP-SAT OPTIMAL")
    _fmt(fifo, "FIFO BASELINE")
    _fmt(allg, "ALLERGEN SORT")

    saving_vs_fifo = fifo.total_changeover_min - opt.total_changeover_min
    saving_vs_allg = allg.total_changeover_min - opt.total_changeover_min
    print(f"\n{'─'*60}")
    print(f"Savings vs FIFO      : {saving_vs_fifo:+.0f} min raw changeover")
    print(f"Savings vs AllergenSort: {saving_vs_allg:+.0f} min raw changeover")
    print(f"SMED additional saving: {opt.smed_savings_min:.0f} min (external parallelism)")
    print(f"{'─'*60}\n")
