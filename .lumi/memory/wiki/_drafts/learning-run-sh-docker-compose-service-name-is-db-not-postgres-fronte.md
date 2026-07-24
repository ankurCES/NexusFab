---
created_at: 2026-07-23T17:41:14.189568+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: 'run.sh: docker-compose service name is `db`, not `postgres`; frontend port is 5173'
source: memory_save_learning
---
# run.sh: docker-compose service name is `db`, not `postgres`; frontend port is 5173

When writing `run.sh` for NexusFab, two non-obvious mismatches between the task spec and actual config:

**1. docker-compose service name**
The `docker-compose.yml` service for Postgres is named `db`, not `postgres`. The task spec said `docker compose up -d postgres adminer`, but the correct command is `docker compose up -d db adminer`. Using the wrong name silently does nothing (compose ignores unknown service names when listed alongside valid ones in some versions, or errors in others). Anchored in `docker-compose.yml` lines 1-26.

**2. Frontend port**
The task spec specified port 3000 for the frontend pre-flight check, but `frontend/vite.config.ts` configures Vite on port **5173** (default). The pre-flight port check and the logged URL must use 5173, not 3000.

**3. `--prod` flag uses uvicorn --workers, not gunicorn**
`gunicorn` is not in `pyproject.toml` dependencies. For production mode, `uvicorn nexusfab.main:app --workers 4` achieves the same multi-process behaviour without an extra dep. Commented with `# ponytail:` in `run.sh`.

**4. `python -m nexusfab.seed` is a no-op**
`nexusfab/seed/__init__.py` is empty — running `python -m nexusfab.seed` exits cleanly but seeds nothing. The script uses `|| true` so startup doesn't fail. Actual seed data lives in `nexusfab/seed/plants.py`, `products.py`, `history.py` (each has its own `__main__` block for direct invocation).

These mismatches would cause silent failures or wrong port checks in any future run.sh iteration.
