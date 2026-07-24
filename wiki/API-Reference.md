# API Reference

[← Home](Home)

> **Interactive docs**: `http://localhost:8000/docs` (Swagger UI) provides a live, clickable version of every endpoint below.

All endpoints are prefixed with `/api`. Responses are JSON unless noted otherwise.

---

## Health & Observability

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/health/live` | Liveness probe — returns `{"status": "ok"}` |
| `GET` | `/api/health/ready` | Readiness probe — checks DB, migrations, seed data, sensor sim |
| `GET` | `/api/health/detailed` | Uptime, DB pool stats, per-plant OEE snapshot, memory usage |
| `GET` | `/api/health/errors` | Last 100 errors with timestamps |
| `GET` | `/api/metrics` | Prometheus-format metrics (requests, errors, sim events, pool size) |

---

## Plants & Lines

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/plants` | List all plants with geo-coordinates |
| `GET` | `/api/plants/{plant_id}/lines` | List production lines for a plant |

---

## OEE & Metrics

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/oee/plant/{plant_id}` | OEE summary for all lines in a plant |
| `GET` | `/api/oee/{plant_id}/{line_name}` | OEE breakdown for a single line |
| `GET` | `/api/metrics/dashboard` | Full dashboard — all plants with best/worst lines |
| `GET` | `/api/metrics/downtime-pareto/{plant_id}` | Downtime Pareto chart by cause |

---

## Simulation

| Method | Path | Summary |
|--------|------|---------|
| `POST` | `/api/simulate/run` | Run discrete-event simulation for a plant or line |
| `POST` | `/api/simulate/scenario` | Run a seeded what-if scenario by ID |
| `GET` | `/api/simulate/scenarios` | List all available scenarios |

### `POST /api/simulate/run` — Example

```json
// Request
{
  "plant_id": "PLT-001",
  "line_name": null,
  "duration_hours": 168,
  "seed": 42
}

// Response (truncated)
{
  "plant_oee": 0.6234,
  "total_units": 1842300,
  "total_failures": 47,
  "lines": [
    {
      "name": "PLT-001-L1",
      "oee": 0.6512,
      "availability": 0.8701,
      "performance": 0.7891,
      "quality": 0.9487
    }
  ]
}
```

---

## Scenarios

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/scenarios` | List all 10 seeded what-if scenarios |
| `POST` | `/api/scenarios/run` | Run a seeded scenario by ID |
| `POST` | `/api/scenarios/custom` | Run a fully parameterized custom scenario |
| `POST` | `/api/scenarios/run-all` | Run all scenarios, return summary table |

### Custom Scenario Parameters

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `plant_id` | string | *required* | Target plant |
| `force_failure_at_hour` | float | null | Inject equipment failure at hour N |
| `failure_equipment` | string | null | Which equipment fails |
| `demand_multiplier` | float | 1.0 | Scale demand (0.1–10.0) |
| `cip_duration_multiplier` | float | 1.0 | Scale CIP duration (0.5–5.0) |
| `energy_rate_multiplier` | float | 1.0 | Scale energy cost |
| `workforce_availability` | float | 1.0 | Fraction of workforce available |

---

## Production Scheduling

| Method | Path | Summary |
|--------|------|---------|
| `POST` | `/api/optimize/schedule` | Generate schedule from sample orders |
| `POST` | `/api/optimize/schedule/custom` | Schedule from custom order list |
| `POST` | `/api/optimize/reroute` | Suggest alternative lines on failure |
| `GET` | `/api/production/schedule/{plant_id}` | Gantt-ready schedule blocks |
| `POST` | `/api/production/optimize-sequence` | TSP/MILP SKU sequencing |
| `GET` | `/api/production/changeover-matrix/{category}` | Changeover time matrix |
| `GET` | `/api/production/kpis/{plant_id}` | Line-level KPIs (OEE, RFT, changeover %) |

---

## Maintenance

| Method | Path | Summary |
|--------|------|---------|
| `POST` | `/api/maintenance/schedule` | Generate maintenance schedule |
| `GET` | `/api/maintenance/schedule/{plant_id}` | Plant-specific schedule |
| `POST` | `/api/maintenance/optimize` | Group tasks to minimize downtime |
| `GET` | `/api/maintenance/predictions/{plant_id}` | ML failure predictions with RUL + alert levels |
| `GET` | `/api/maintenance/history/{plant_id}` | Historical failures with severity and cost |
| `GET` | `/api/maintenance/health/{plant_id}` | Equipment health index per plant |

---

## Spare Parts

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/spares/` | Inventory analysis (all plants) |
| `GET` | `/api/spares/{plant_id}` | Plant inventory with days-to-stockout |
| `GET` | `/api/spares/status/{plant_id}` | Full status with ABC-XYZ classification |
| `GET` | `/api/spares/alerts` | Stockout and low-stock alerts |
| `GET` | `/api/spares/pooling` | Cross-plant pooling candidates |
| `POST` | `/api/spares/reorder` | EOQ-based reorder actions |

---

## Sensors

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/sensors/{plant_id}/{line_id}/equipment` | List equipment on a line |
| `GET` | `/api/sensors/{plant_id}/{line_id}/{equipment_id}` | Current sensor readings |
| `GET` | `/api/sensors/{equipment_id}/history` | Time-series history (up to 720 h) |
| `GET` | `/api/sensors/stream/{plant_id}` | **SSE** live stream (readings every 2 s) |

---

## Network & Demand

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/network/status` | Network utilization, OEE, transfers |
| `POST` | `/api/network/analyze` | Custom utilization/OEE overrides |
| `GET` | `/api/network/flow` | Flow graph (nodes = plants, edges = routes) |
| `POST` | `/api/network/balance` | Load-balance; optionally simulate plant failure |
| `POST` | `/api/network/simulate` | Run simulation across plants |
| `GET` | `/api/network/transport/{from}/{to}` | Pallet transport cost between plants |
| `GET` | `/api/network/flows` | All inter-plant routes with cost and transit time |
| `GET` | `/api/network/allocation` | Product × plant allocation grid |
| `GET` | `/api/network/milp-optimize` | MILP 4-week allocation vs greedy baseline |
| `GET` | `/api/demand/forecast/{plant_id}` | Demand forecast for N weeks |
| `POST` | `/api/demand/plan` | Custom plan with MAPE target, service level, lead time |

---

## Energy

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/energy/{plant_id}` | Consumption, cost, CO₂ for a plant |
| `GET` | `/api/energy` | Energy across all plants |
| `POST` | `/api/energy/analyze` | Custom period and utilization |
| `POST` | `/api/energy/optimize` | Peak shaving and off-peak load shifting |

---

## Workforce

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/workforce/{plant_id}` | Shift schedule and labor cost |
| `GET` | `/api/workforce` | All plants workforce |

---

## Compliance (HACCP / Food Safety)

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/api/compliance/{plant_id}` | Regulatory compliance report |
| `GET` | `/api/compliance` | All-plants compliance |
| `GET` | `/api/compliance/allergen-check?from_sku=X&to_sku=Y` | Allergen conflict + CIP class |
| `GET` | `/api/compliance/{plant_id}/ccps` | Critical Control Point status |
| `GET` | `/api/compliance/{plant_id}/allergens` | Allergen matrix per product |
| `GET` | `/api/compliance/{plant_id}/cip` | CIP schedule events |
| `GET` | `/api/compliance/{plant_id}/score` | Composite compliance score with 30-day trend |

---

## Analytics

| Method | Path | Summary |
|--------|------|---------|
| `POST` | `/api/analytics/kpi` | KPI trends over N periods — OEE, energy, waste, OTIF |

---

## Error Responses

All errors follow a consistent shape:

```json
{
  "detail": "Plant PLT-999 not found"
}
```

| Status | Meaning |
|--------|---------|
| 404 | Resource not found (plant, line, equipment, scenario) |
| 400 | Invalid input (bad SKU, constraint violation) |
| 422 | Validation error (Pydantic) |
| 500 | Unhandled server error (logged to `/api/health/errors`) |

---

See also: [Architecture](Architecture) · [Configuration](Configuration)
