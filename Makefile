# Developer shortcuts. All targets use uv; run `make install` first.
.PHONY: install run fmt lint check test test-unit test-integration test-system test-acceptance smoke smoke-live docker-up docker-down

install:            ## Create .venv from uv.lock, including dev tools
	uv sync

run:                ## Start the app locally on http://localhost:8000
	PYTHONPATH=src uv run uvicorn xulan.app:app --port 8000

fmt:                ## Format code with Ruff
	uv run ruff format .
	uv run ruff check --fix .

lint:               ## Lint and check formatting without changing files
	uv run ruff check .
	uv run ruff format --check .

check: lint test    ## Everything CI should run

test:               ## All free test layers (smoke tests skip unless enabled)
	uv run pytest -q

test-unit:
	uv run pytest -q -m unit

test-integration:
	uv run pytest -q -m integration

test-system:
	uv run pytest -q -m system

test-acceptance:
	uv run pytest -q -m acceptance

smoke:              ## Build and start the container, check endpoints, stop (no model calls)
	scripts/smoke.sh

smoke-live:         ## ONE paid generation call (about USD 0.01) to verify the provider path
	XULAN_LIVE_SMOKE=1 uv run pytest -q -m smoke -k live

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
