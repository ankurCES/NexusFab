"""SimPy production line model with Weibull failures and lognormal repairs."""

import math
import random
from dataclasses import dataclass, field
from enum import Enum

import simpy

class LineState(str, Enum):
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    REPAIR = "REPAIR"
    CHANGEOVER = "CHANGEOVER"
    CIP = "CIP"
    IDLE = "IDLE"

@dataclass
class SimEvent:
    time: float
    event_type: str
    line_name: str
    equipment_name: str | None = None
    detail: str = ""
    duration: float = 0.0

_ELECTRICAL_TYPES = {"CONVEYOR"}  # ponytail: expand set if seed adds electrical equipment

# ponytail: simple mapping, product-category pairs → CIP minutes
_CIP_DURATION: dict[tuple[str, str], float] = {
    ("DAIRY", "DAIRY"): 60.0,
    ("DAIRY", "CONFECTIONERY"): 90.0,
    ("CONFECTIONERY", "DAIRY"): 90.0,
    ("CONFECTIONERY", "CONFECTIONERY"): 45.0,
}
_CIP_DEFAULT = 45.0  # min for same-category, 75 for cross-category


def cip_duration_minutes(from_cat: str, to_cat: str) -> float:
    """30-90 min CIP based on product category transition."""
    key = (from_cat.upper(), to_cat.upper())
    if key in _CIP_DURATION:
        return _CIP_DURATION[key]
    return 75.0 if from_cat != to_cat else _CIP_DEFAULT


@dataclass
class EquipmentConfig:
    name: str
    equipment_type: str
    mtbf_hours: float
    mttr_hours: float
    weibull_shape: float = 2.0  # shape param, 1.5-2.5 typical
    repair_sigma: float = 0.4

    @property
    def failure_category(self) -> str:
        return "electrical" if self.equipment_type.upper() in _ELECTRICAL_TYPES else "mechanical"

@dataclass
class LineConfig:
    name: str
    line_type: str
    speed_units_per_min: float
    equipment: list[EquipmentConfig] = field(default_factory=list)
    quality_rate: float = 0.97
    speed_factor: float = 0.88
    micro_stop_probability: float = 0.03
    micro_stop_max_min: float = 5.0
    changeover_matrix: dict[tuple[str, str], float] = field(default_factory=dict)

@dataclass
class LineMetrics:
    total_time: float = 0.0
    running_time: float = 0.0
    downtime_mechanical: float = 0.0
    downtime_electrical: float = 0.0
    downtime_changeover: float = 0.0
    downtime_cip: float = 0.0
    downtime_other: float = 0.0
    units_produced: int = 0
    units_rejected: int = 0
    failures: int = 0
    repairs: int = 0

    @property
    def availability(self) -> float:
        if self.total_time == 0:
            return 0.0
        return self.running_time / self.total_time

    @property
    def total_downtime(self) -> float:
        return (self.downtime_mechanical + self.downtime_electrical +
                self.downtime_changeover + self.downtime_cip + self.downtime_other)


class EquipmentProcess:
    """Single piece of equipment that fails and gets repaired."""

    def __init__(self, env: simpy.Environment, config: EquipmentConfig, rng: random.Random):
        self.env = env
        self.config = config
        self.rng = rng
        self.failed = False
        self.failure_event: simpy.Event | None = None

    def time_to_failure(self) -> float:
        """Weibull-distributed time to failure (hours)."""
        scale = self.config.mtbf_hours / math.gamma(1 + 1 / self.config.weibull_shape)
        return self.rng.weibullvariate(scale, self.config.weibull_shape)

    def repair_time(self) -> float:
        """Lognormal-distributed repair time (hours)."""
        mu = math.log(self.config.mttr_hours)
        return self.rng.lognormvariate(mu, self.config.repair_sigma)

    def run(self) -> simpy.Process:
        return self.env.process(self._lifecycle())

    def _lifecycle(self):
        while True:
            ttf = self.time_to_failure()
            yield self.env.timeout(ttf * 60)  # convert hours to minutes
            self.failed = True
            self.failure_event = self.env.event()
            repair_mins = self.repair_time() * 60
            yield self.env.timeout(repair_mins)
            self.failed = False
            self.failure_event.succeed()
            self.failure_event = None


class ProductionLine:
    """SimPy process for a single production line."""

    def __init__(self, env: simpy.Environment, config: LineConfig, rng: random.Random):
        self.env = env
        self.config = config
        self.rng = rng
        self.state = LineState.IDLE
        self.metrics = LineMetrics()
        self.events: list[SimEvent] = []
        self.equipment_procs: list[EquipmentProcess] = []

        for eq_cfg in config.equipment:
            ep = EquipmentProcess(env, eq_cfg, rng)
            self.equipment_procs.append(ep)

    def start(self):
        for ep in self.equipment_procs:
            ep.run()
        self.env.process(self._produce())

    def _log(self, event_type: str, equipment: str | None = None,
             detail: str = "", duration: float = 0.0):
        ev = SimEvent(self.env.now, event_type, self.config.name, equipment, detail, duration)
        self.events.append(ev)

    def _produce(self):
        self.state = LineState.RUNNING
        self._log("START", detail="Production started")

        while True:
            failed_eq = self._check_failures()
            if failed_eq:
                yield from self._handle_failure(failed_eq)
                continue

            # Micro-stop check
            if self.rng.random() < self.config.micro_stop_probability:
                stop_dur = self.rng.uniform(1.0, self.config.micro_stop_max_min)
                self.state = LineState.IDLE
                yield self.env.timeout(stop_dur)
                self.metrics.downtime_other += stop_dur
                self.metrics.total_time += stop_dur
                self.state = LineState.RUNNING
                continue

            # Produce for 1 minute at reduced speed
            self.state = LineState.RUNNING
            yield self.env.timeout(1.0)
            self.metrics.running_time += 1.0
            self.metrics.total_time += 1.0

            units = int(self.config.speed_units_per_min * self.config.speed_factor)
            good = int(units * self.config.quality_rate)
            rejected = units - good
            self.metrics.units_produced += good
            self.metrics.units_rejected += rejected

    def _check_failures(self) -> EquipmentProcess | None:
        for ep in self.equipment_procs:
            if ep.failed:
                return ep
        return None

    def _handle_failure(self, eq: EquipmentProcess):
        self.state = LineState.FAILED
        self.metrics.failures += 1
        start = self.env.now
        self._log("FAILURE", eq.config.name, f"{eq.config.equipment_type} failure")

        self.state = LineState.REPAIR
        if eq.failure_event:
            yield eq.failure_event
        repair_time = self.env.now - start

        if eq.config.failure_category == "electrical":
            self.metrics.downtime_electrical += repair_time
        else:
            self.metrics.downtime_mechanical += repair_time

        self.metrics.total_time += repair_time
        self.metrics.repairs += 1
        self._log("REPAIR_COMPLETE", eq.config.name, duration=repair_time)
        self.state = LineState.RUNNING

    def do_changeover(self, duration_minutes: float | None = None,
                      from_product: str | None = None,
                      to_product: str | None = None):
        if duration_minutes is None:
            duration_minutes = self.config.changeover_matrix.get(
                (from_product or "", to_product or ""), 30.0)
        return self.env.process(self._changeover(duration_minutes))

    def _changeover(self, duration_minutes: float):
        self.state = LineState.CHANGEOVER
        self._log("CHANGEOVER_START", duration=duration_minutes)
        yield self.env.timeout(duration_minutes)
        self.metrics.downtime_changeover += duration_minutes
        self.metrics.total_time += duration_minutes
        self._log("CHANGEOVER_END", duration=duration_minutes)
        self.state = LineState.RUNNING

    def do_cip(self, duration_minutes: float | None = None,
               from_category: str | None = None,
               to_category: str | None = None):
        if duration_minutes is None:
            duration_minutes = cip_duration_minutes(
                from_category or "", to_category or "")
        return self.env.process(self._cip(duration_minutes))

    def _cip(self, duration_minutes: float):
        self.state = LineState.CIP
        self._log("CIP_START", duration=duration_minutes)
        yield self.env.timeout(duration_minutes)
        self.metrics.downtime_cip += duration_minutes
        self.metrics.total_time += duration_minutes
        self._log("CIP_END", duration=duration_minutes)
        self.state = LineState.RUNNING


if __name__ == "__main__":
    import random as _rand
    env = simpy.Environment()
    rng = _rand.Random(42)
    cfg = LineConfig(
        name="SELFCHECK-L1", line_type="FILLING", speed_units_per_min=120,
        equipment=[
            EquipmentConfig("FIL-01", "FILLER", mtbf_hours=80, mttr_hours=1.5, weibull_shape=1.8),
            EquipmentConfig("CAP-01", "CAPPER", mtbf_hours=120, mttr_hours=1.0),
            EquipmentConfig("CONV-01", "CONVEYOR", mtbf_hours=200, mttr_hours=0.5),
        ],
        changeover_matrix={("SKU-A", "SKU-B"): 25.0, ("SKU-B", "SKU-A"): 20.0},
    )
    line = ProductionLine(env, cfg, rng)
    line.start()
    env.run(until=24 * 60)  # 24 hours in minutes

    m = line.metrics
    print(f"=== 24h self-check: {cfg.name} ===")
    print(f"running:  {m.running_time:.0f} min")
    print(f"downtime: mech={m.downtime_mechanical:.0f} elec={m.downtime_electrical:.0f} "
          f"chg={m.downtime_changeover:.0f} cip={m.downtime_cip:.0f} other={m.downtime_other:.0f}")
    print(f"units:    {m.units_produced} good, {m.units_rejected} rejected")
    print(f"failures: {m.failures}  repairs: {m.repairs}")
    print(f"avail:    {m.availability:.1%}")
    print(f"events:   {len(line.events)}")
    assert m.running_time > 0, "line never ran"
    assert m.failures > 0, "no failures in 24h — Weibull params too generous?"
    assert m.units_produced > 0, "zero units produced"
    assert m.availability < 1.0, "100% availability — failures didn't register"
    assert len(line.events) >= 2, "too few events logged"
    print("PASS")
