"""Verify demand charges are defined and PLT-003 (CA/PG&E) has the highest rate."""
from nexusfab.optimization.energy import _PLANT_RATES
from nexusfab.seed.plants import PLANTS


def test_energy_full():
    plant_ids = {p.id for p in PLANTS}

    # All plants must have a rate entry (or fall back — here we verify all 5 are explicit)
    for pid in plant_ids:
        assert pid in _PLANT_RATES, f"{pid}: missing energy rate entry"

    for pid, rates in _PLANT_RATES.items():
        # Every entry must have a positive demand charge
        assert rates["demand_kw"] > 0, f"{pid}: demand_kw must be > 0"
        assert rates["base_kwh"] > 0, f"{pid}: base_kwh must be > 0"
        assert rates["gas_mmbtu"] > 0, f"{pid}: gas_mmbtu must be > 0"
        # CPP rate must be positive and events > 0
        assert rates["cpp_rate"] > 0, f"{pid}: cpp_rate must be > 0"
        assert rates["cpp_events_year"] > 0, f"{pid}: cpp_events_year must be > 0"

    # PLT-003 (CA PG&E) must have the highest demand charge
    demand_rates = {pid: r["demand_kw"] for pid, r in _PLANT_RATES.items()}
    highest = max(demand_rates, key=demand_rates.__getitem__)
    assert highest == "PLT-003", (
        f"Expected PLT-003 to have highest demand rate, got {highest} "
        f"({demand_rates[highest]:.2f} vs PLT-003 {demand_rates['PLT-003']:.2f})"
    )

    # PLT-003 also has highest base kwh rate
    kwh_rates = {pid: r["base_kwh"] for pid, r in _PLANT_RATES.items()}
    highest_kwh = max(kwh_rates, key=kwh_rates.__getitem__)
    assert highest_kwh == "PLT-003", (
        f"Expected PLT-003 to have highest kWh rate, got {highest_kwh}"
    )

    print(
        f"PASS — PLT-003 demand_kw={demand_rates['PLT-003']:.2f} "
        f"base_kwh={kwh_rates['PLT-003']:.3f}, highest in network"
    )


if __name__ == "__main__":
    test_energy_full()
