# Contributing

[← Home](Home)

---

## Development Setup

```bash
git clone https://github.com/ankurCES/NexusFab.git
cd NexusFab
uv sync                       # or: pip install -e .[dev]
cp .env.example .env
docker compose up -d db       # PostgreSQL
alembic upgrade head
```

---

## Branching Model

| Branch | Purpose |
|--------|---------|
| `main` | Stable, release-ready |
| `feat/*` | New features |
| `fix/*` | Bug fixes |
| `docs/*` | Documentation changes |

```bash
git checkout -b feat/my-feature
# ... make changes ...
git push -u origin feat/my-feature
# Open PR → main
```

---

## Code Style

### Python

- **Linter**: [Ruff](https://docs.astral.sh/ruff/) — configured in `pyproject.toml`
- **Target**: Python 3.12
- **Line length**: 99 characters
- **Rules**: `E` (pycodestyle), `F` (pyflakes), `I` (isort), `N` (naming), `UP` (pyupgrade), `B` (bugbear), `SIM` (simplify)

```bash
# Check
ruff check .

# Auto-fix
ruff check --fix .

# Format
ruff format .
```

### Frontend

- TypeScript with strict mode
- ESLint + OxLint (`.oxlintrc.json`)

---

## Testing

```bash
# Full suite (20 modules)
make test

# Specific test
pytest tests/test_sequencing.py -v

# With coverage
pytest --cov=nexusfab -v
```

### Test Coverage Areas

| Module | Tests |
|--------|-------|
| Allergen constraints | `test_allergens.py` |
| Network allocation | `test_allocation.py` |
| Critical Control Points | `test_ccps.py` |
| Changeover logic | `test_changeover.py` |
| CIP scheduling | `test_cip_schedules.py` |
| Demand planning | `test_demand.py` |
| Energy optimization | `test_energy_full.py`, `test_energy_scenarios.py` |
| Failure generation | `test_failure_gen.py` |
| Lead times | `test_lead_times.py` |
| Line speeds | `test_line_speeds.py` |
| Network optimization | `test_network.py` |
| Predictive maintenance | `test_pdm.py` |
| Sensor streams | `test_sensor_stream.py` |
| SKU sequencing | `test_sequencing.py` |
| Spare parts | `test_spare_parts.py` |
| Transport routing | `test_transport.py` |
| Weibull models | `test_weibull.py` |
| Workforce scheduling | `test_workforce.py`, `test_workforce_regulatory.py` |

---

## Adding a New API Endpoint

1. **Schema** — Create or extend a Pydantic model in `nexusfab/api/schemas/`
2. **Router** — Add the endpoint in the appropriate file under `nexusfab/api/routers/`
3. **Register** — If it's a new router file, include it in `nexusfab/api/router.py`
4. **Test** — Add a test in `tests/`
5. **Verify** — `ruff check . && make test`

---

## Adding a New Optimization Module

1. Create the solver in `nexusfab/optimization/`
2. Wire it through a router endpoint
3. Add seed data in `nexusfab/seed/` if needed
4. Write tests covering edge cases and solver feasibility

---

## PR Checklist

- [ ] `ruff check .` passes with no warnings
- [ ] `make test` passes (all 20 modules)
- [ ] New endpoints appear in Swagger UI (`/docs`)
- [ ] Docstrings on public functions
- [ ] Wiki updated if adding a new domain module

---

## Project Structure Reference

```
NexusFab/
├── nexusfab/
│   ├── api/
│   │   ├── routers/       # 13 endpoint modules
│   │   ├── schemas/       # 15 Pydantic response models
│   │   ├── router.py      # Central router registration
│   │   └── health.py      # Health probes + metrics
│   ├── models/            # 8 SQLAlchemy ORM models
│   ├── optimization/      # 11 solver modules
│   ├── simulation/        # 7 SimPy engine modules
│   ├── services/          # OEE calculation
│   ├── seed/              # In-memory demo data
│   ├── config.py          # pydantic-settings
│   ├── database.py        # Async SQLAlchemy engine
│   └── main.py            # FastAPI app
├── frontend/              # React 19 + Vite + Tailwind
├── tests/                 # 20 test modules
├── alembic/               # DB migrations
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── run.sh
```

---

See also: [Getting Started](Getting-Started) · [Architecture](Architecture) · [API Reference](API-Reference)
