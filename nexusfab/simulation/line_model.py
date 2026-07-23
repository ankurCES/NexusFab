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

@dataclass
class EquipmentConfig:
    name: str
    equipment_type: str
    mtbf_hours: float
    mttr_hours: float
    weibull_shape: float = 2.0  # shape param, 1.5-2.5 typical
    repair_sigma: float = 0.4

@dataclass
class LineConfig:
    name: str
    line_type: str
    speed_units_per_min: float
    equipment: list[EquipmentConfig] = field(default_factory=list)
    quality_rate: float = 0.97  # fraction good units
    speed_factor: float = 0.88  # actual vs rated speed (performance loss)
    micro_stop_probability: float = 0.03  # chance of 1-5 min micro-stop per minute
    micro_stop_max_min: float = 5.0

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
        # Wait for repair to complete
        if eq.failure_event:
            yield eq.failure_event
        repair_time = self.env.now - start
        self.metrics.downtime_mechanical += repair_time
        self.metrics.total_time += repair_time
        self.metrics.repairs += 1
        self._log("REPAIR_COMPLETE", eq.config.name, duration=repair_time)
        self.state = LineState.RUNNING

    def do_changeover(self, duration_minutes: float):
        return self.env.process(self._changeover(duration_minutes))

    def _changeover(self, duration_minutes: float):
        self.state = LineState.CHANGEOVER
        self._log("CHANGEOVER_START", duration=duration_minutes)
        yield self.env.timeout(duration_minutes)
        self.metrics.downtime_changeover += duration_minutes
        self.metrics.total_time += duration_minutes
        self._log("CHANGEOVER_END", duration=duration_minutes)
        self.state = LineState.RUNNING

    def do_cip(self, duration_minutes: float = 60.0):
        return self.env.process(self._cip(duration_minutes))

    def _cip(self, duration_minutes: float):
        self.state = LineState.CIP
        self._log("CIP_START", duration=duration_minutes)
        yield self.env.timeout(duration_minutes)
        self.metrics.downtime_cip += duration_minutes
        self.metrics.total_time += duration_minutes
        self._log("CIP_END", duration=duration_minutes)
        self.state = LineState.RUNNING
