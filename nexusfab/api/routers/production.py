"""Production scheduling, sequencing, and KPI API endpoints."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from nexusfab.api.schemas.production import ChangeoverMatrix, ProductionKPIs, ProductionSchedule, SequencingSolution
from nexusfab.optimization.scheduling import generate_sample_orders, generate_schedule
from nexusfab.optimization.sequencing import (
    SequencingProblem,
    build_changeover_matrix,
    fifo_sequence,
    optimize_sequence,
)
from nexusfab.seed.plants import get_plant
from nexusfab.seed.products import PRODUCTS, get_changeover_info, get_product, get_products_for_plant
from nexusfab.simulation.runner import run_plant

router = APIRouter(prefix="/api/production", tags=["Production"])


def _sku_category(sku: str) -> str:
    p = get_product(sku)
    return p.category if p else "UNKNOWN"


@router.get("/schedule/{plant_id}", response_model=ProductionSchedule, summary="Production schedule as Gantt blocks — production runs and changeovers per line")
async def production_schedule(plant_id: str, days: int = 7, seed: int = 42):
    plant = get_plant(plant_id)
    if not plant:
        raise HTTPException(404, f"Plant {plant_id} not found")

    horizon_hours = float(days * 24)
    n_orders = max(20, days * 6)
    orders = generate_sample_orders(plant_id, n_orders, seed)
    if not orders:
        raise HTTPException(404, f"No products for {plant_id}")

    result = generate_schedule(plant_id, orders, horizon_hours=horizon_hours)

    by_line: dict[str, list] = defaultdict(list)
    for r in result.runs:
        by_line[r.line_name].append(r)

    lines_data = []
    for line_name, runs in sorted(by_line.items()):
        runs.sort(key=lambda r: r.start_time)
        blocks = []
        for i, r in enumerate(runs):
            # Gap between prev.end and current.start = changeover block
            if i > 0:
                prev = runs[i - 1]
                gap_start = prev.end_time
                gap_end = r.start_time
                if gap_end > gap_start:
                    _, cip_type = get_changeover_info(prev.sku, r.sku)
                    blocks.append({
                        "type": "changeover",
                        "cip_type": cip_type,
                        "from_sku": prev.sku,
                        "to_sku": r.sku,
                        "start": gap_start.isoformat(),
                        "end": gap_end.isoformat(),
                        "minutes": r.changeover_minutes,
                    })
            blocks.append({
                "type": "production",
                "sku": r.sku,
                "product": r.product_name,
                "category": _sku_category(r.sku),
                "start": r.start_time.isoformat(),
                "end": r.end_time.isoformat(),
                "quantity": r.quantity,
                "order_id": r.order_id,
            })
        lines_data.append({"line": line_name, "blocks": blocks})

    all_starts = [r.start_time for runs in by_line.values() for r in runs]
    t_start = min(all_starts) if all_starts else None
    t_end = (t_start + timedelta(hours=horizon_hours)) if t_start else None

    return {
        "plant_id": plant_id,
        "days": days,
        "start": t_start.isoformat() if t_start else "",
        "end": t_end.isoformat() if t_end else "",
        "horizon_hours": horizon_hours,
        "total_changeover_minutes": result.total_changeover_minutes,
        "lines": lines_data,
    }


class OptimizeSequenceRequest(BaseModel):
    plant_id: str
    line_id: str = ""
    skus: list[str] = Field(default_factory=list)
    batch_hours: dict[str, float] = Field(default_factory=dict)
    due_dates: dict[str, float] = Field(default_factory=dict)
    is_uht_line: bool = False
    time_limit_sec: int = Field(default=15, ge=1, le=60)


@router.post("/optimize-sequence", response_model=SequencingSolution, summary="Optimize SKU sequence using TSP/MILP to minimize changeover time")
async def post_optimize_sequence(req: OptimizeSequenceRequest):
    skus = req.skus
    if not skus:
        products = get_products_for_plant(req.plant_id)
        if not products:
            raise HTTPException(404, f"No products for {req.plant_id}")
        skus = [p.sku for p in products]

    matrix = build_changeover_matrix(skus)
    batch_hours = req.batch_hours or {s: 4.0 for s in skus}

    problem = SequencingProblem(
        line_id=req.line_id or f"{req.plant_id}-L1",
        products=skus,
        changeover_matrix=matrix,
        due_dates=req.due_dates,
        batch_hours=batch_hours,
        is_uht_line=req.is_uht_line,
    )

    fifo = fifo_sequence(problem)
    opt = optimize_sequence(problem, time_limit_sec=req.time_limit_sec)

    def _sol(s) -> dict:
        return {
            "sequence": s.sequence,
            "total_changeover_min": s.total_changeover_min,
            "effective_changeover_min": s.effective_changeover_min,
            "smed_savings_min": s.smed_savings_min,
            "makespan": s.makespan,
            "late_orders": s.late_orders,
            "allergen_violations": s.allergen_violations,
            "cip_interval_warning": s.cip_interval_warning,
            "solver_status": s.solver_status,
        }

    return {
        "plant_id": req.plant_id,
        "line_id": problem.line_id,
        "products": [
            {"sku": s, "name": next((p.name for p in PRODUCTS if p.sku == s), s)}
            for s in skus
        ],
        "fifo": _sol(fifo),
        "optimized": _sol(opt),
        "changeover_reduction_min": round(fifo.total_changeover_min - opt.total_changeover_min, 1),
        "changeover_reduction_pct": round(
            (fifo.total_changeover_min - opt.total_changeover_min)
            / max(fifo.total_changeover_min, 1) * 100,
            1,
        ),
    }


@router.get("/changeover-matrix/{plant_category}", response_model=ChangeoverMatrix, summary="Changeover time matrix between all SKU pairs for a plant category")
async def changeover_matrix(plant_category: str):
    category = plant_category.upper()
    products = [p for p in PRODUCTS if p.category == category]
    if not products:
        raise HTTPException(404, f"No products for category {category}")

    entries = []
    for fp in products:
        for tp in products:
            if fp.sku == tp.sku:
                continue
            mins, cip = get_changeover_info(fp.sku, tp.sku)
            rev_mins, _ = get_changeover_info(tp.sku, fp.sku)
            entries.append({
                "from_sku": fp.sku,
                "to_sku": tp.sku,
                "minutes": mins,
                "cip_type": cip,
                "asymmetric": abs(mins - rev_mins) > 5,
            })

    seen: set[frozenset] = set()
    asym_pairs = []
    for e in entries:
        if e["asymmetric"]:
            key = frozenset([e["from_sku"], e["to_sku"]])
            if key not in seen:
                seen.add(key)
                rev = next(
                    (x["minutes"] for x in entries if x["from_sku"] == e["to_sku"] and x["to_sku"] == e["from_sku"]),
                    0,
                )
                asym_pairs.append({"from_sku": e["from_sku"], "to_sku": e["to_sku"], "a_to_b": e["minutes"], "b_to_a": rev})

    return {
        "plant_category": category,
        "products": [{"sku": p.sku, "name": p.name, "allergen_tier": p.allergen_tier} for p in products],
        "matrix": entries,
        "asymmetric_pairs": asym_pairs,
    }


@router.get("/kpis/{plant_id}", response_model=ProductionKPIs, summary="Production KPIs — OEE, availability, performance, quality, and throughput per line")
async def production_kpis(plant_id: str, duration_hours: float = 168.0, seed: int = 42):
    plant = get_plant(plant_id)
    if not plant:
        raise HTTPException(404, f"Plant {plant_id} not found")

    plant_result = run_plant(plant_id, duration_hours, seed)

    # Compute changeover % from schedule
    line_co: dict[str, float] = defaultdict(float)
    try:
        orders = generate_sample_orders(plant_id, 40, seed)
        if orders:
            sched = generate_schedule(plant_id, orders, horizon_hours=duration_hours)
            for r in sched.runs:
                if r.changeover_minutes:
                    line_co[r.line_name] += r.changeover_minutes
    except Exception:
        pass

    available_minutes = duration_hours * 60
    lines_kpis = []
    for lr in plant_result.line_results:
        line_seed = next((l for l in plant.lines if l.name == lr.line_name), None)
        rated = line_seed.rated_speed_per_min if line_seed else 10.0
        # ponytail: target = theoretical at 85% attainable OEE; adjust if you have demand data
        units_target = int(rated * available_minutes * 0.85)
        co_min = line_co.get(lr.line_name, 0.0)
        lines_kpis.append({
            "line": lr.line_name,
            "oee": round(lr.oee, 4),
            "availability": round(lr.availability, 4),
            "performance": round(lr.performance, 4),
            "quality": round(lr.quality, 4),
            "right_first_time": round(lr.quality, 4),
            "changeover_pct": round(co_min / available_minutes * 100, 1) if available_minutes else 0.0,
            "units_produced": lr.metrics.units_produced,
            "units_target": units_target,
        })

    return {
        "plant_id": plant_id,
        "plant_name": plant.name,
        "duration_hours": duration_hours,
        "plant_oee": round(plant_result.plant_oee, 4),
        "total_units": plant_result.total_units,
        "lines": lines_kpis,
    }
