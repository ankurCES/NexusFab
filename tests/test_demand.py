"""Demand planning tests — seasonality ratios, safety stock, MTS/MTO split."""

from nexusfab.optimization.demand import (
    _SEASONALITY,
    _safety_stock,
    generate_demand_plan,
)


def test_seasonality_ratios():
    water = _SEASONALITY["WATER"]
    assert max(water) / min(water) >= 1.9, "WATER 2:1"

    conf = _SEASONALITY["CONFECTIONERY"]
    assert max(conf) / min(conf) >= 3.5, "CONFECTIONERY 4:1"

    dairy = _SEASONALITY["DAIRY"]
    assert max(dairy) / min(dairy) >= 2.8, "DAIRY 3:1"


def test_safety_stock_positive():
    ss = _safety_stock(avg_demand=10000, mape=0.35, service_level=0.95, lead_time_weeks=2.0)
    assert ss > 0
    ss_higher = _safety_stock(avg_demand=10000, mape=0.50, service_level=0.99, lead_time_weeks=4.0)
    assert ss_higher > ss


def test_demand_plan_basic():
    plan = generate_demand_plan("PLT-001", horizon_weeks=4, seed=42)
    d = plan.to_dict()
    assert d["total_forecasts"] > 0
    assert d["total_units"] > 0
    assert d["mts_units"] + d["mto_units"] == d["total_units"]

    f0 = d["forecasts"][0]
    assert "safety_stock" in f0
    assert "fulfillment_type" in f0
    assert f0["fulfillment_type"] in ("MTS", "MTO")


def test_mts_mto_split_present():
    plan = generate_demand_plan(horizon_weeks=4)
    d = plan.to_dict()
    assert d["mts_units"] > 0, "should have MTS"
    assert d["mto_units"] > 0, "should have MTO"


def test_mape_bounds():
    plan_low = generate_demand_plan("PLT-001", horizon_weeks=4, target_mape=0.25)
    plan_high = generate_demand_plan("PLT-001", horizon_weeks=4, target_mape=0.50)
    assert plan_low.target_mape == 0.25
    assert plan_high.target_mape == 0.50


def test_deterministic_with_seed():
    a = generate_demand_plan("PLT-002", horizon_weeks=4, seed=99)
    b = generate_demand_plan("PLT-002", horizon_weeks=4, seed=99)
    assert a.total_forecast_units == b.total_forecast_units
