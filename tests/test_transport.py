"""Verify 10 inter-plant routes exist and cold chain surcharge applies to dairy."""
from nexusfab.optimization.network import (
    COLD_CHAIN_SURCHARGE_PCT,
    _TRANSPORT_MATRIX,
    transport_cost_pallet,
)


def test_transport():
    # 5 plants → C(5,2) = 10 unique routes
    assert len(_TRANSPORT_MATRIX) == 10, (
        f"Expected 10 routes, got {len(_TRANSPORT_MATRIX)}"
    )

    # All routes have positive cost and lead time
    for route, (cost, hours) in _TRANSPORT_MATRIX.items():
        assert cost > 0, f"Route {route}: cost must be > 0"
        assert hours > 0, f"Route {route}: lead time must be > 0"

    # Dairy surcharge: PLT-003 route always triggers cold chain
    ambient = transport_cost_pallet("PLT-001", "PLT-002")
    assert not ambient["cold_chain"], "PLT-001↔PLT-002 should not be cold chain"

    dairy = transport_cost_pallet("PLT-003", "PLT-001")
    assert dairy["cold_chain"], "PLT-003 routes must be cold chain"

    base_cost = _TRANSPORT_MATRIX[frozenset({"PLT-001", "PLT-003"})][0]
    expected = round(base_cost * (1 + COLD_CHAIN_SURCHARGE_PCT), 2)
    assert dairy["cost_per_pallet"] == expected, (
        f"Dairy surcharge wrong: expected {expected}, got {dairy['cost_per_pallet']}"
    )

    # Explicit DAIRY category also triggers surcharge on non-PLT-003 route
    cat_dairy = transport_cost_pallet("PLT-001", "PLT-002", product_category="DAIRY")
    assert cat_dairy["cold_chain"], "DAIRY category should trigger cold chain on any route"
    assert cat_dairy["cost_per_pallet"] > ambient["cost_per_pallet"]

    print(f"PASS — 10 routes, surcharge {COLD_CHAIN_SURCHARGE_PCT*100:.0f}%, dairy cold chain verified")


if __name__ == "__main__":
    test_transport()
