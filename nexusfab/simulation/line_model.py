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

# --- CIP skid contention ---
CIP_PRIORITY_UHT_HARD = 1   # UHT/ASEPTIC hard-deadline (food safety)
CIP_PRIORITY_SCHEDULED = 2  # periodic scheduled CIP
CIP_PRIORITY_CHANGEOVER = 3 # between-product changeover CIP

UHT_CIP_MAX_INTERVAL_HOURS = 12.0  # food-safety hard limit

_UHT_LINE_TYPES = frozenset({"UHT", "ASEPTIC"})


class CIPSkidPool:
    """Physical CIP skid resources shared across lines in a plant.

    PLT-003: dedicated=True → 1 shared skid + 1 skid exclusively for UHT/ASEPTIC.
    Others: all lines compete for shared_capacity skids.
    """

    def __init__(self, env: simpy.Environment, plant_id: str,
                 shared_capacity: int, dedicated_uht: bool = False):
        self.plant_id = plant_id
        self.shared = simpy.PriorityResource(env, capacity=shared_capacity)
        # ponytail: dedicated skid only for PLT-003; None branch has zero cost
        self.dedicated = simpy.PriorityResource(env, capacity=1) if dedicated_uht else None
        self.hours_in_use: float = 0.0
        self.violations: list[str] = []

    def skid_for(self, line_type: str) -> simpy.PriorityResource:
        if self.dedicated and line_type.upper() in _UHT_LINE_TYPES:
            return self.dedicated
        return self.shared

    def utilization(self, sim_hours: float) -> float:
        total = (self.shared.capacity + (1 if self.dedicated else 0)) * sim_hours
        return self.hours_in_use / total if total else 0.0


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
    weibull_beta: float = 2.0
    weibull_eta: float | None = None  # ponytail: None → derive from mtbf_hours for backward compat
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
    cip_frequency_hours: float = 0.0  # 0 = no scheduled CIP
    cip_duration_range: tuple[float, float] = (0.0, 0.0)

@dataclass
class LineMetrics:
    total_time: float = 0.0
    running_time: float = 0.0
    downtime_mechanical: float = 0.0
    downtime_electrical: float = 0.0
    downtime_changeover: float = 0.0
    downtime_cip: float = 0.0
    downtime_other: float = 0.0
    downtime_short_staffed: float = 0.0
    units_produced: int = 0
    units_rejected: int = 0
    failures: int = 0
    repairs: int = 0
    cip_queue_wait_total: float = 0.0  # minutes waiting for a skid
    cip_queue_count: int = 0

    @property
    def avg_cip_queue_wait(self) -> float:
        return self.cip_queue_wait_total / self.cip_queue_count if self.cip_queue_count else 0.0

    @property
    def availability(self) -> float:
        if self.total_time == 0:
            return 0.0
        return self.running_time / self.total_time

    @property
    def total_downtime(self) -> float:
        return (self.downtime_mechanical + self.downtime_electrical +
                self.downtime_changeover + self.downtime_cip +
                self.downtime_other + self.downtime_short_staffed)


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
        eta = self.config.weibull_eta
        if eta is None:
            eta = self.config.mtbf_hours / math.gamma(1 + 1 / self.config.weibull_beta)
        return self.rng.weibullvariate(eta, self.config.weibull_beta)

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

    def __init__(self, env: simpy.Environment, config: LineConfig, rng: random.Random,
                 cip_pool: "CIPSkidPool | None" = None):
        self.env = env
        self.config = config
        self.rng = rng
        self.state = LineState.IDLE
        self.metrics = LineMetrics()
        self.events: list[SimEvent] = []
        self.equipment_procs: list[EquipmentProcess] = []

        self._cip_due = False
        self.workforce_factor = 1.0
        self._cip_pool = cip_pool
        self._last_cip_end: float | None = None

        for eq_cfg in config.equipment:
            ep = EquipmentProcess(env, eq_cfg, rng)
            self.equipment_procs.append(ep)

    def start(self):
        for ep in self.equipment_procs:
            ep.run()
        self.env.process(self._produce())
        if self.config.cip_frequency_hours > 0:
            self.env.process(self._cip_scheduler())

    def _log(self, event_type: str, equipment: str | None = None,
             detail: str = "", duration: float = 0.0):
        ev = SimEvent(self.env.now, event_type, self.config.name, equipment, detail, duration)
        self.events.append(ev)

    def _cip_scheduler(self):
        freq_min = self.config.cip_frequency_hours * 60
        while True:
            yield self.env.timeout(freq_min)
            self._cip_due = True

    def _do_scheduled_cip(self):
        lo, hi = self.config.cip_duration_range
        dur = self.rng.uniform(lo, hi) if hi > lo else lo
        self._cip_due = False
        priority = (CIP_PRIORITY_UHT_HARD
                    if self.config.line_type.upper() in _UHT_LINE_TYPES
                    else CIP_PRIORITY_SCHEDULED)
        yield from self._cip(dur, priority=priority)

    def _produce(self):
        self.state = LineState.RUNNING
        self._log("START", detail="Production started")

        while True:
            if self._cip_due:
                yield from self._do_scheduled_cip()
                continue

            failed_eq = self._check_failures()
            if failed_eq:
                yield from self._handle_failure(failed_eq)
                continue

            if self.workforce_factor <= 0.0:
                self.state = LineState.IDLE
                yield self.env.timeout(1.0)
                self.metrics.downtime_short_staffed += 1.0
                self.metrics.total_time += 1.0
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

            units = int(self.config.speed_units_per_min * self.config.speed_factor * self.workforce_factor)
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
        return self.env.process(self._cip(duration_minutes, priority=CIP_PRIORITY_CHANGEOVER))

    def _cip(self, duration_minutes: float, priority: int = CIP_PRIORITY_SCHEDULED):
        requested_at = self.env.now
        pool = self._cip_pool
        skid = req = None

        if pool is not None:
            skid = pool.skid_for(self.config.line_type)
            req = skid.request(priority=priority)
            yield req  # wait for a free skid

        wait_time = self.env.now - requested_at
        self.metrics.cip_queue_wait_total += wait_time
        self.metrics.cip_queue_count += 1

        # Food-safety violation: UHT/ASEPTIC CIP started too late
        if (self.config.line_type.upper() in _UHT_LINE_TYPES
                and self._last_cip_end is not None):
            overdue_h = (self.env.now - self._last_cip_end) / 60
            if overdue_h > UHT_CIP_MAX_INTERVAL_HOURS:
                msg = (f"{self.config.name}: food safety violation — "
                       f"CIP at {self.env.now/60:.1f}h, {overdue_h:.1f}h since last "
                       f"(max {UHT_CIP_MAX_INTERVAL_HOURS}h)")
                if pool is not None:
                    pool.violations.append(msg)

        self.state = LineState.CIP
        self._log("CIP_START", duration=duration_minutes)
        yield self.env.timeout(duration_minutes)

        if pool is not None:
            pool.hours_in_use += duration_minutes / 60
            skid.release(req)

        self._last_cip_end = self.env.now
        self.metrics.downtime_cip += duration_minutes
        self.metrics.total_time += duration_minutes
        self._log("CIP_END", duration=duration_minutes)
        self.state = LineState.RUNNING


if __name__ == "__main__":
    import random as _rand

    # --- Test 1: basic 24h check (no scheduled CIP) ---
    env = simpy.Environment()
    rng = _rand.Random(42)
    cfg = LineConfig(
        name="SELFCHECK-L1", line_type="FILLING", speed_units_per_min=120,
        equipment=[
            EquipmentConfig("FIL-01", "FILLER", mtbf_hours=80, mttr_hours=1.5, weibull_beta=1.8),
            EquipmentConfig("CAP-01", "CAPPER", mtbf_hours=120, mttr_hours=1.0),
            EquipmentConfig("CONV-01", "CONVEYOR", mtbf_hours=200, mttr_hours=0.5),
        ],
        changeover_matrix={("SKU-A", "SKU-B"): 25.0, ("SKU-B", "SKU-A"): 20.0},
    )
    line = ProductionLine(env, cfg, rng)
    line.start()
    env.run(until=24 * 60)

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
    print("PASS\n")

    # --- Test 2: 168h CIP schedule check ---
    SIM_HOURS = 168
    test_cases = [
        ("FILLING-12h",   12, (30, 45),  14),  # 168/12 = 14
        ("UHT-10h",       10, (90, 120), 16),  # 168/10 = 16 (hard limit 12h satisfied)
        ("ASEPTIC-8h",     8, (90, 150), 21),  # 168/8 = 21
        ("EXTRUSION-24h", 24, (90, 120),  7),  # 168/24 = 7
    ]
    for label, freq_h, dur_range, expected_cips in test_cases:
        env2 = simpy.Environment()
        rng2 = _rand.Random(42)
        cfg2 = LineConfig(
            name=f"CIP-CHECK-{label}", line_type="TEST",
            speed_units_per_min=100,
            equipment=[
                EquipmentConfig("EQ-01", "FILLER", mtbf_hours=500, mttr_hours=1.0, weibull_beta=2.0),
            ],
            cip_frequency_hours=freq_h,
            cip_duration_range=dur_range,
        )
        line2 = ProductionLine(env2, cfg2, rng2)
        line2.start()
        env2.run(until=SIM_HOURS * 60)

        cip_starts = [e for e in line2.events if e.event_type == "CIP_START"]
        cip_times = [e.time / 60 for e in cip_starts]  # hours

        # Verify interval between CIPs never exceeds frequency + 1 min tolerance
        for i in range(1, len(cip_times)):
            gap = cip_times[i] - cip_times[i - 1]
            assert gap <= freq_h + 0.1, (
                f"{label}: CIP gap {gap:.1f}h exceeds {freq_h}h limit at CIP #{i}")

        print(f"=== 168h CIP check: {label} (every {freq_h}h) ===")
        print(f"  CIP events: {len(cip_starts)} (expected ~{expected_cips})")
        print(f"  CIP downtime: {line2.metrics.downtime_cip:.0f} min")
        print(f"  First CIP at: {cip_times[0]:.1f}h")
        assert len(cip_starts) >= expected_cips - 1, (
            f"{label}: only {len(cip_starts)} CIPs, expected ~{expected_cips}")
        assert line2.metrics.downtime_cip > 0, f"{label}: zero CIP downtime"
        print("  PASS")

    print("\nALL CHECKS PASSED")

    # --- Test 3: PLT-002 CIP skid contention (1 skid, 3 lines, 168h) ---
    print("\n=== PLT-002: 1 CIP skid, 3 lines, 168h ===")
    SIM3_HOURS = 168
    env3 = simpy.Environment()
    rng3 = _rand.Random(7)
    pool = CIPSkidPool(env3, "PLT-002", shared_capacity=1)

    plt002_lines = [
        ProductionLine(env3, LineConfig(
            name=f"PLT002-L{i+1}", line_type="FILLING",
            speed_units_per_min=100,
            equipment=[EquipmentConfig(f"EQ-{i+1}", "FILLER",
                                       mtbf_hours=500, mttr_hours=1.0, weibull_beta=2.0)],
            cip_frequency_hours=8,
            cip_duration_range=(45, 60),
        ), rng3, cip_pool=pool)
        for i in range(3)
    ]
    for ln in plt002_lines:
        ln.start()
    env3.run(until=SIM3_HOURS * 60)

    for ln in plt002_lines:
        m = ln.metrics
        print(f"  {ln.config.name}: CIPs={m.cip_queue_count}, "
              f"avg_wait={m.avg_cip_queue_wait:.1f}min, avail={m.availability:.1%}")

    avg_wait = sum(l.metrics.avg_cip_queue_wait for l in plt002_lines) / len(plt002_lines)
    util = pool.utilization(SIM3_HOURS)
    print(f"  avg queue wait: {avg_wait:.1f}min (target <15min)")
    print(f"  skid utilization: {util:.1%}")
    print(f"  violations: {pool.violations or ['none']}")

    assert pool.hours_in_use > 0, "no CIP skid time recorded"
    assert any(l.metrics.cip_queue_count > 0 for l in plt002_lines), "no CIPs ran"
    assert util <= 1.0, f"utilization {util:.1%} exceeds 100%"
    print("  PASS")

    print("\nALL CHECKS PASSED")
