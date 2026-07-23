"""Verify optimized sequence has ≤ FIFO changeover time."""
from nexusfab.optimization.sequencing import SequencingProblem, optimize_sequence
from nexusfab.seed.products import get_changeover_time

# Confectionery SKUs: worst FIFO order is nut → plain → dark (expensive then cheaper)
SKUS = ["CON-NUT", "CON-KB4", "CON-KBD"]  # nut first = worst FIFO start


def _fifo_changeover(skus: list[str]) -> float:
    return sum(get_changeover_time(skus[i], skus[i + 1]) for i in range(len(skus) - 1))


def test_sequencing():
    matrix = {
        from_sku: {to_sku: get_changeover_time(from_sku, to_sku) for to_sku in SKUS}
        for from_sku in SKUS
    }
    problem = SequencingProblem(
        line_id="PLT-002-L1",
        products=SKUS,
        changeover_matrix=matrix,
        batch_hours={sku: 4.0 for sku in SKUS},
        is_uht_line=False,
    )

    sol = optimize_sequence(problem, time_limit_sec=15)

    assert sol.sequence, "Optimizer returned empty sequence"
    assert set(sol.sequence) == set(SKUS), "Sequence must contain all SKUs"
    assert sol.total_changeover_min >= 0

    fifo_cost = _fifo_changeover(SKUS)
    # Optimized must not exceed FIFO (it should find at minimum the same or better sequence)
    assert sol.total_changeover_min <= fifo_cost + 1e-6, (
        f"Optimized changeover {sol.total_changeover_min:.1f} > FIFO {fifo_cost:.1f}"
    )

    # SMED savings must be non-negative
    assert sol.smed_savings_min >= 0

    print(
        f"PASS — FIFO {fifo_cost:.1f} min → optimized {sol.total_changeover_min:.1f} min "
        f"(sequence: {' → '.join(sol.sequence)})"
    )


if __name__ == "__main__":
    test_sequencing()
