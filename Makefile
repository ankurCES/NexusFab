.PHONY: dev test docker-up docker-down seed

dev:
	uvicorn nexusfab.api.main:app --reload --port 8000

test:
	pytest -v

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

seed:
	python -m nexusfab.seed
