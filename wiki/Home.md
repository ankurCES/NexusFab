# NexusFab Wiki

**NexusFab** is a full-stack digital twin for multi-plant manufacturing operations. It combines discrete-event simulation (SimPy), constraint-based optimization (OR-Tools), ML-driven predictive maintenance (scikit-learn), and a React analytics dashboard to model, monitor, and optimize factory networks end-to-end.

---

## 📚 Pages

| Page | Description |
|------|-------------|
| [Getting Started](Getting-Started) | Prerequisites, installation, first run |
| [Architecture](Architecture) | System design, module map, data flow |
| [API Reference](API-Reference) | Every REST endpoint with request/response examples |
| [Configuration](Configuration) | Environment variables and tuning knobs |
| [Contributing](Contributing) | Code style, branching, testing, PR workflow |

---

## Quick Links

- **Live API docs** — `http://localhost:8000/docs` (Swagger UI, auto-generated)
- **Dashboard** — `http://localhost:5173`
- **DB admin** — `http://localhost:8080` (Adminer)
- **Health probe** — `GET /api/health/live`

---

## Key Capabilities

| Domain | Engine |
|--------|--------|
| Production scheduling & sequencing | OR-Tools CP-SAT / TSP solver |
| Predictive maintenance | Weibull failure model + scikit-learn |
| Discrete-event simulation | SimPy (per-line, per-plant, network) |
| Energy optimization | PuLP / OR-Tools peak-shaving |
| Workforce planning | Shift optimization with regulatory constraints |
| Network optimization | Multi-plant MILP allocation + transport routing |
| Food-safety compliance | HACCP CCP monitoring, allergen matrix, CIP scheduling |
| Demand planning | Forecast with safety stock and service-level targeting |
| Spare parts management | ABC-XYZ classification, EOQ, cross-plant pooling |
| Real-time sensors | Simulated sensor streams via SSE |

---

## Plant Network (Seed Data)

| ID | Name | Category | Lines | Equipment |
|----|------|----------|-------|-----------|
| PLT-001 | NexWater-East | Water bottling | 4 | 15 |
| PLT-002 | NexConfec-Central | Confectionery | 3 | 12 |
| PLT-003 | NexDairy-North | Dairy | 3 | 14 |
| PLT-004 | NexPet-South | Pet food | 3 | 13 |
| PLT-005 | NexPrep-West | Prepared foods | 3 | 13 |

---

*Built with FastAPI · SimPy · OR-Tools · React · PostgreSQL*
