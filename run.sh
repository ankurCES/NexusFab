#!/usr/bin/env bash
# NexusFab launcher — git clone && ./run.sh → stack running
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
R='\033[0;31m' G='\033[0;32m' Y='\033[1;33m' B='\033[0;34m' C='\033[0;36m' N='\033[0m'

# ── Flags ───────────────────────────────────────────────────────────────────
NO_SEED=0 PROD=0 RESET=0 API_ONLY=0
for arg in "$@"; do
  case $arg in
    --no-seed)  NO_SEED=1 ;;
    --prod)     PROD=1 ;;
    --reset)    RESET=1 ;;
    --api-only) API_ONLY=1 ;;
    *) echo "Unknown flag: $arg  (valid: --no-seed --prod --reset --api-only)"; exit 1 ;;
  esac
done

# ── Logging ──────────────────────────────────────────────────────────────────
mkdir -p logs
_ts() { date '+%H:%M:%S'; }
run()    { echo -e "$(_ts) ${R}[run]${N} $*"; }
db()     { echo -e "$(_ts) ${C}[db]${N} $*"      | tee -a logs/db.log; }
api()    { echo -e "$(_ts) ${B}[api]${N} $*"     | tee -a logs/api.log; }
sensor() { echo -e "$(_ts) ${Y}[sensor]${N} $*"  | tee -a logs/sensor.log; }
fe()     { echo -e "$(_ts) ${G}[frontend]${N} $*" | tee -a logs/frontend.log; }

# ── Cleanup ──────────────────────────────────────────────────────────────────
PIDS=()
cleanup() {
  run "Shutting down..."
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  docker compose stop db adminer 2>/dev/null || true
  run "Done."
}
trap cleanup INT TERM

# ── Pre-flight ───────────────────────────────────────────────────────────────
run "Pre-flight checks..."

command -v docker >/dev/null 2>&1          || { run "ERROR: docker not found"; exit 1; }
docker compose version >/dev/null 2>&1     || { run "ERROR: docker compose not found"; exit 1; }
command -v python3 >/dev/null 2>&1         || { run "ERROR: python3 not found"; exit 1; }
command -v node >/dev/null 2>&1            || { run "ERROR: node not found"; exit 1; }

# Python 3.11+
py_ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
py_ok=$(python3 -c 'import sys; print(1 if sys.version_info >= (3,11) else 0)')
[ "$py_ok" = "1" ] || { run "ERROR: Python 3.11+ required (found $py_ver)"; exit 1; }

# Node 18+
node_ver=$(node -e 'process.stdout.write(process.version.slice(1).split(".")[0])')
[ "$node_ver" -ge 18 ] 2>/dev/null        || { run "ERROR: Node 18+ required (found $(node --version))"; exit 1; }

# Ports: 5432 (postgres), 8000 (api), 5173 (vite)
API_PORT="${API_PORT:-8000}"
for port in 5432 "$API_PORT" 5173; do
  # ponytail: lsof -iTCP is the simplest cross-platform port check on macOS/Linux
  if lsof -iTCP:"$port" -sTCP:LISTEN -n -P >/dev/null 2>&1; then
    run "ERROR: port $port already in use — stop the conflicting process first"; exit 1
  fi
done

# .env — auto-generate from example if missing
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    run ".env created from .env.example — review before production use"
  else
    run "ERROR: .env missing and no .env.example found"; exit 1
  fi
fi

run "Pre-flight OK (Python $py_ver, Node $(node --version))"

# ── Reset ─────────────────────────────────────────────────────────────────────
if [ "$RESET" = "1" ]; then
  run "Resetting volumes..."
  docker compose down -v
fi

# ── 1. Database ───────────────────────────────────────────────────────────────
db "Starting postgres + adminer..."
docker compose up -d db adminer

db "Waiting for postgres..."
deadline=$((SECONDS + 60))
until docker compose exec -T db pg_isready -U nexusfab -q 2>/dev/null; do
  [ "$SECONDS" -lt "$deadline" ] || { db "ERROR: DB not ready after 60s"; exit 1; }
  sleep 1
done
db "Ready"

# ── 2. Migrations ─────────────────────────────────────────────────────────────
db "Running migrations..."
python3 -m alembic upgrade head 2>&1 | tee -a logs/db.log

# ── 3. Seed ────────────────────────────────────────────────────────────────────
if [ "$NO_SEED" = "0" ]; then
  db "Seeding data..."
  # ponytail: seed __init__.py may be empty — || true prevents failure if it's a no-op
  python3 -m nexusfab.seed 2>&1 | tee -a logs/db.log || true
fi

# ── 4. Sensor simulator (background) ─────────────────────────────────────────
sensor "Starting sensor simulator..."
python3 -m nexusfab.simulation.sensor_stream --background >> logs/sensor.log 2>&1 &
PIDS+=($!)

# ── 5. API (background) ───────────────────────────────────────────────────────
if [ "$PROD" = "1" ]; then
  api "Starting API (uvicorn, 4 workers — prod)..."
  # ponytail: uvicorn --workers instead of gunicorn — same result, no extra dep
  python3 -m uvicorn nexusfab.main:app --host 0.0.0.0 --port "$API_PORT" --workers 4 >> logs/api.log 2>&1 &
else
  api "Starting API (uvicorn dev)..."
  python3 -m uvicorn nexusfab.main:app --host 0.0.0.0 --port "$API_PORT" --reload >> logs/api.log 2>&1 &
fi
PIDS+=($!)

# ── 6. Health check loop ──────────────────────────────────────────────────────
api "Waiting for API readiness..."
READY_URL="http://localhost:${API_PORT}/api/health/ready"
deadline=$((SECONDS + 60))
status=""
while [ "$SECONDS" -lt "$deadline" ]; do
  status=$(curl -sf -o /dev/null -w "%{http_code}" "$READY_URL" 2>/dev/null || true)
  [ "$status" = "200" ] && break
  sleep 5
done

if [ "$status" = "200" ]; then
  api "Ready → http://localhost:${API_PORT}"
else
  api "WARNING: health check timed out — check logs/api.log"
fi

# ── 7. Frontend ───────────────────────────────────────────────────────────────
if [ "$API_ONLY" = "1" ]; then
  run "API-only mode. API: http://localhost:${API_PORT}  |  Logs: logs/"
  wait "${PIDS[@]}"
else
  fe "Installing deps..."
  (cd frontend && npm install --silent 2>&1 | tee -a ../logs/frontend.log) || true
  fe "Starting Vite dev server → http://localhost:5173"
  (cd frontend && npm run dev 2>&1 | tee -a ../logs/frontend.log)
fi

# Cleanup fires via trap on exit
