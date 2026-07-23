"""Tests for multi-plant network optimization and inter-plant rerouting."""

from nexusfab.optimization.network import (
    PALLETS_PER_TRUCK,
    analyze_network,
    balance_network,
    transport_cost_pallet,
)
from nexusfab.simulation.runner import run_network


def test_transport_cost_pallet_range():
    tc = transport_cost_pallet("PLT-001", "PLT-005")
    assert 50.0 <= tc["cost_per_pallet"] <= 500.0
    assert 4.0 <= tc["lead_time_hours"] <= 48.0
    assert tc["min_pallets"] == PALLETS_PER_TRUCK


def test_transport_cost_same_plant():
    tc = transport_cost_pallet("PLT-001", "PLT-001")
    assert tc["cost_per_pallet"] == 0.0
    assert tc["lead_time_hours"] == 0.0


def test_analyze_network_flow_graph():
    report = analyze_network()
    d = report.to_dict()
    assert d["plant_count"] == 5
    fg = d["flow_graph"]
    assert len(fg["nodes"]) == 5
    assert len(fg["edges"]) > 0
    statuses = {n["status"] for n in fg["nodes"]}
    assert statuses <= {"normal", "overloaded", "underloaded"}


def test_balance_network_failure():
    utils = {"PLT-001": 0.85, "PLT-002": 0.70, "PLT-003": 0.50, "PLT-004": 0.60, "PLT-005": 0.55}
    report = balance_network(utils, failed_plant="PLT-001")
    d = report.to_dict()
    failed = next(p for p in d["plants"] if p["plant_id"] == "PLT-001")
    assert failed["utilization"] == 0.0
    remaining = [p for p in d["plants"] if p["plant_id"] != "PLT-001"]
    assert all(p["utilization"] <= 0.95 for p in remaining)


def test_run_network():
    r = run_network(duration_hours=24, seed=42)
    assert r["plant_count"] == 5
    assert r["total_units"] > 0
    assert all(pid in r["utilizations"] for pid in ["PLT-001", "PLT-002", "PLT-003", "PLT-004", "PLT-005"])


def test_transfers_enforce_minimum_truck():
    report = analyze_network(
        utilizations={"PLT-001": 0.95, "PLT-002": 0.40, "PLT-003": 0.40, "PLT-004": 0.95, "PLT-005": 0.40},
    )
    for t in report.transfers:
        assert t.pallets >= PALLETS_PER_TRUCK
        assert t.transfer_tons >= PALLETS_PER_TRUCK
