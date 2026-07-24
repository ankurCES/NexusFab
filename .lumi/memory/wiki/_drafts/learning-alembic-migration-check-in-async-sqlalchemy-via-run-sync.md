---
created_at: 2026-07-23T17:28:09.482443+00:00
created_by_agent: memory_save_learning
evidence_session: null
confidence: medium
promoted_at: null
description: Alembic migration check in async SQLAlchemy via run_sync
source: memory_save_learning
---
# Alembic migration check in async SQLAlchemy via run_sync

When building a `/health/ready` endpoint that verifies Alembic migration state against an async SQLAlchemy engine, the alembic `MigrationContext` API is synchronous only. Use `conn.run_sync()` to bridge:

```python
async with engine.connect() as conn:
    current = await conn.run_sync(
        lambda sync_conn: MigrationContext.configure(sync_conn).get_current_revision()
    )
head = ScriptDirectory.from_config(alembic_cfg).get_current_head()
ok = current == head
```

This lives in `nexusfab/api/health.py` inside the `readiness()` endpoint. The `ScriptDirectory` reads from `alembic.ini` on disk; the file path must be relative to the process working directory (it's resolved at call time, not import time).

Also: the simulation runner (`nexusfab/simulation/runner.py`) needed module-level `_sim_last_at: float` and `_sim_events_total: int` sentinels, updated inside `run_plant()` with `global` declaration, so the health probe can check recency without any inter-module coupling via callbacks or events.

`pool.overflow()` on asyncpg pools returns negative values when the pool has unused capacity below its max_overflow setting — this is not an error, just SQLAlchemy's convention for "below the overflow ceiling".
