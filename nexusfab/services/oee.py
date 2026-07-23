"""OEE calculator with Six Big Losses categorization."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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


_AVAILABILITY_RATINGS = [(0.90, "world-class"), (0.83, "good"), (0.75, "average"), (0.0, "poor")]
_PERFORMANCE_RATINGS = [(0.95, "world-class"), (0.85, "good"), (0.75, "average"), (0.0, "poor")]
_QUALITY_RATINGS = [(0.999, "world-class"), (0.97, "good"), (0.95, "average"), (0.0, "poor")]

_BREAKDOWN_TYPES = {"mechanical", "electrical", "process", "other"}
_SETUP_TYPES = {"changeover", "cip", "planned_maintenance"}
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


async def async_calculate_oee(
    session: AsyncSession,
    line_id: uuid.UUID,
    start: datetime,
    end: datetime,
    *,
    shift_number: int = 1,
) -> OEEResult:
    """Query DB for production/downtime data, calculate OEE, and persist the record."""
    from nexusfab.models.downtime import DowntimeEvent
    from nexusfab.models.oee import OEERecord
    from nexusfab.models.plant import ProductionLine
    from nexusfab.models.production import ProductionRun

    line = (await session.execute(
        select(ProductionLine).where(ProductionLine.id == line_id)
    )).scalar_one()
    ideal_cycle = 1.0 / line.speed_units_per_min if line.speed_units_per_min > 0 else 1.0

    planned_time = (end - start).total_seconds() / 60.0

    runs = (await session.execute(
        select(
            func.coalesce(func.sum(ProductionRun.actual_qty), 0),
            func.coalesce(func.sum(ProductionRun.good_qty), 0),
        ).where(
            ProductionRun.line_id == line_id,
            ProductionRun.start_time >= start,
            ProductionRun.start_time < end,
        )
    )).one()
    total_units, good_units = int(runs[0]), int(runs[1])

    dt_rows = (await session.execute(
        select(DowntimeEvent).where(
            DowntimeEvent.line_id == line_id,
            DowntimeEvent.start_time >= start,
            DowntimeEvent.start_time < end,
        )
    )).scalars().all()

    breakdown_min = 0.0
    setup_min = 0.0
    for evt in dt_rows:
        if evt.end_time is None:
            continue
        mins = (evt.end_time - evt.start_time).total_seconds() / 60.0
        if evt.downtime_type.value in _BREAKDOWN_TYPES:
            breakdown_min += mins
        else:
            setup_min += mins

    result = calculate_oee(
        planned_time_min=planned_time,
        downtime_breakdown_min=breakdown_min,
        downtime_setup_min=setup_min,
        ideal_cycle_time_min=ideal_cycle,
        total_units=total_units,
        good_units=good_units,
    )

    record = OEERecord(
        line_id=line_id,
        shift_date=start.date(),
        shift_number=shift_number,
        availability=result.availability,
        performance=result.performance,
        quality=result.quality,
        oee=result.oee,
        six_big_losses=result.to_dict()["six_big_losses"],
    )
    session.add(record)
    await session.commit()

    return result


if __name__ == "__main__":
    r = calculate_oee(
        planned_time_min=480,
        downtime_breakdown_min=30,
        downtime_setup_min=20,
        ideal_cycle_time_min=0.5,
        total_units=800,
        good_units=790,
        small_stops_min=10,
    )
    d = r.to_dict()
    assert 0 < r.availability < 1, f"availability out of range: {r.availability}"
    assert 0 < r.performance <= 1, f"performance out of range: {r.performance}"
    assert 0 < r.quality <= 1, f"quality out of range: {r.quality}"
    assert abs(r.oee - r.availability * r.performance * r.quality) < 1e-9
    assert r.breakdown_loss == 30
    assert r.setup_loss == 20
    assert "availability_losses" in d["six_big_losses"]
    assert "performance_losses" in d["six_big_losses"]
    assert "quality_losses" in d["six_big_losses"]
    assert all(v in ("world-class", "good", "average", "poor") for v in d["ratings"].values())
    print(f"OEE={r.oee:.2%}  A={r.availability:.2%} P={r.performance:.2%} Q={r.quality:.2%}")
    print(f"Ratings: {d['ratings']}")
    print("All checks passed.")
