#!/usr/bin/env bash
# Smoke-test the Docker Compose stack: build, start, wait until healthy, check endpoints, stop.
# Makes no model calls. Usage: scripts/smoke.sh
set -euo pipefail
cd "$(dirname "$0")/.."

URL="${XULAN_SMOKE_URL:-http://localhost:8000}"

cleanup() { docker compose down >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker compose up -d --build

echo "Waiting for ${URL}/api/health ..."
for _ in $(seq 1 30); do
  if curl -fsS "${URL}/api/health" >/dev/null 2>&1; then break; fi
  sleep 1
done

XULAN_SMOKE_URL="${URL}" uv run pytest -m smoke tests/smoke -q
echo "Smoke test passed."
