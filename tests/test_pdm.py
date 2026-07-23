"""Verify RUL decreases as health degrades and alert levels are correct."""
import math

from nexusfab.optimization.predictive_maintenance import EquipmentPdM, _alert_level


def test_pdm():
    # Alert thresholds: GREEN > 168h, YELLOW > 72h, ORANGE > 24h, RED ≤ 24h
    assert _alert_level(200.0) == "GREEN"
    assert _alert_level(100.0) == "YELLOW"
    assert _alert_level(48.0) == "ORANGE"
    assert _alert_level(12.0) == "RED"
    assert _alert_level(0.0) == "RED"

    # RUL must decrease monotonically as health degrades (higher health → longer RUL)
    eq = EquipmentPdM("TEST-EQ", "FILLER", beta=2.2, eta=1100.0)
    rul_high = eq._rul_hours(1.0)
    rul_mid = eq._rul_hours(0.5)
    rul_low = eq._rul_hours(0.1)

    assert rul_high > rul_mid > rul_low >= 0, (
        f"RUL must decrease: {rul_high:.1f} > {rul_mid:.1f} > {rul_low:.1f}"
    )

    # At health=1.0, RUL = η × ln(2)^(1/β)
    expected_full = 1100.0 * (math.log(2) ** (1.0 / 2.2))
    assert abs(rul_high - expected_full) < 0.1, f"RUL formula wrong: {rul_high} vs {expected_full}"

    # At health=0, RUL must be 0
    assert eq._rul_hours(0.0) == 0.0

    print(f"PASS — RUL at full health {rul_high:.1f}h, at 50% {rul_mid:.1f}h, alert levels correct")


if __name__ == "__main__":
    test_pdm()
