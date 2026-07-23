"""OEE calculator with Six Big Losses categorization."""

from dataclasses import dataclass

@dataclass
class OEEResult:
    availability: float
    performance: float
    quality: float
    oee: float
    # Six Big Losses (minutes)
    breakdown_loss: float = 0.0
    setup_loss: float = 0.0
    small_stop_loss: float = 0.0
    speed_loss: float = 0.0
    startup_reject_loss: float = 0.0
    production_reject_loss: float = 0.0
    # Benchmarks
    availability_rating: str = ""
    performance_rating: str = ""
    quality_rating: str = ""
    oee_rating: str = ""

    def to_dict(self) -> dict:
        return {
            "availability": round(self.availability, 4),
            "performance": round(self.performance, 4),
            "quality": round(self.quality, 4),
            "oee": round(self.oee, 4),
            "six_big_losses": {
                "availability_losses": {
                    "breakdowns": round(self.breakdown_loss, 1),
                    "setup_adjustments": round(self.setup_loss, 1),
                },
                "performance_losses": {
                    "small_stops": round(self.small_stop_loss, 1),
                    "speed_loss": round(self.speed_loss, 1),
                },
                "quality_losses": {
                    "startup_rejects": round(self.startup_reject_loss, 1),
                    "production_rejects": round(self.production_reject_loss, 1),
                },
            },
            "ratings": {
                "availability": self.availability_rating,
                "performance": self.performance_rating,
                "quality": self.quality_rating,
                "oee": self.oee_rating,
            },
        }


def _rate(value: float, thresholds: list[tuple[float, str]]) -> str:
    for threshold, label in thresholds:
        if value >= threshold:
            return label
    return thresholds[-1][1]


_AVAILABILITY_RATINGS = [(0.88, "world-class"), (0.83, "good"), (0.75, "average"), (0.0, "poor")]
_PERFORMANCE_RATINGS = [(0.92, "world-class"), (0.85, "good"), (0.75, "average"), (0.0, "poor")]
_QUALITY_RATINGS = [(0.99, "world-class"), (0.97, "good"), (0.95, "average"), (0.0, "poor")]
_OEE_RATINGS = [(0.85, "world-class"), (0.75, "good"), (0.60, "average"), (0.0, "poor")]


def calculate_oee(
    planned_time_min: float,
    downtime_breakdown_min: float,
    downtime_setup_min: float,
    ideal_cycle_time_min: float,  # minutes per unit
    total_units: int,
    good_units: int,
    small_stops_min: float = 0.0,
) -> OEEResult:
    """Calculate OEE from raw production data."""
    available_time = planned_time_min - downtime_breakdown_min - downtime_setup_min
    availability = available_time / planned_time_min if planned_time_min > 0 else 0.0

    ideal_output = available_time / ideal_cycle_time_min if ideal_cycle_time_min > 0 else 0
    performance = total_units / ideal_output if ideal_output > 0 else 0.0
    performance = min(performance, 1.0)

    quality = good_units / total_units if total_units > 0 else 0.0

    oee = availability * performance * quality

    speed_loss = available_time - (total_units * ideal_cycle_time_min) - small_stops_min
    speed_loss = max(speed_loss, 0.0)

    rejected = total_units - good_units
    startup_rejects = int(rejected * 0.3)
    production_rejects = rejected - startup_rejects

    return OEEResult(
        availability=availability,
        performance=performance,
        quality=quality,
        oee=oee,
        breakdown_loss=downtime_breakdown_min,
        setup_loss=downtime_setup_min,
        small_stop_loss=small_stops_min,
        speed_loss=speed_loss,
        startup_reject_loss=startup_rejects * ideal_cycle_time_min,
        production_reject_loss=production_rejects * ideal_cycle_time_min,
        availability_rating=_rate(availability, _AVAILABILITY_RATINGS),
        performance_rating=_rate(performance, _PERFORMANCE_RATINGS),
        quality_rating=_rate(quality, _QUALITY_RATINGS),
        oee_rating=_rate(oee, _OEE_RATINGS),
    )


def oee_from_simulation(metrics, line_config) -> OEEResult:
    """Calculate OEE from SimPy LineMetrics."""
    ideal_cycle = 1.0 / line_config.speed_units_per_min if line_config.speed_units_per_min > 0 else 1.0
    total_units = metrics.units_produced + metrics.units_rejected
    return calculate_oee(
        planned_time_min=metrics.total_time,
        downtime_breakdown_min=metrics.downtime_mechanical,
        downtime_setup_min=metrics.downtime_changeover + metrics.downtime_cip,
        ideal_cycle_time_min=ideal_cycle,
        total_units=total_units,
        good_units=metrics.units_produced,
    )
