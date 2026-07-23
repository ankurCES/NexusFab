"""Verify all line types have a CIP schedule, and UHT frequency ≤ 12h."""
from nexusfab.seed.plants import CIP_SCHEDULES, PLANTS


def test_cip_schedules():
    all_line_types = {line.line_type for plant in PLANTS for line in plant.lines}
    missing = all_line_types - set(CIP_SCHEDULES)
    assert not missing, f"Line types without CIP schedule: {missing}"

    for line_type, sched in CIP_SCHEDULES.items():
        freq = sched["frequency_hours"]
        assert freq > 0, f"{line_type}: frequency_hours must be > 0"

        dur_min, dur_max = sched["duration_min"]
        assert dur_min > 0, f"{line_type}: duration lower bound must be > 0"
        assert dur_max >= dur_min, f"{line_type}: duration max < min"

    # UHT_FILLING food-safety hard limit: CIP every ≤ 12h
    uht_freq = CIP_SCHEDULES["UHT_FILLING"]["frequency_hours"]
    assert uht_freq <= 12, f"UHT_FILLING frequency {uht_freq}h exceeds 12h limit"

    # ASEPTIC is stricter (FDA FSMA)
    aseptic_freq = CIP_SCHEDULES["ASEPTIC"]["frequency_hours"]
    assert aseptic_freq <= 12, f"ASEPTIC frequency {aseptic_freq}h exceeds 12h limit"

    print(f"PASS — {len(CIP_SCHEDULES)} CIP schedules, UHT at {uht_freq}h ≤ 12h")


if __name__ == "__main__":
    test_cip_schedules()
