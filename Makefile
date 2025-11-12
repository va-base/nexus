.PHONY: help setup bootstrap ingest test run eval clean

help:
	@echo "Nexus v0 - Investment Research System"
	@echo ""
	@echo "Targets:"
	@echo "  setup      - Initialize database and seed fixtures"
	@echo "  bootstrap  - Load initial data from data/initial/"
	@echo "  ingest     - Run ingestion pipelines on fixtures"
	@echo "  test       - Run unit and integration tests"
	@echo "  run        - Start all services (docker-compose up)"
	@echo "  eval       - Run evaluation suite"
	@echo "  clean      - Stop services and remove volumes"

setup:
	@echo "Setting up Nexus..."
	docker-compose up -d postgres redis
	@echo "Waiting for services..."
	sleep 10
	docker-compose run --rm worker python scripts/seed_fixtures.py
	@echo "Setup complete!"

bootstrap:
	@echo "Bootstrapping initial data..."
	docker-compose run --rm worker python scripts/bootstrap_initial_data.py
	@echo "Bootstrap complete!"

ingest:
	@echo "Running ingestion pipelines..."
	docker-compose run --rm worker python -m nexus.monitoring.filings_flow
	docker-compose run --rm worker python -m nexus.monitoring.earnings_flow
	docker-compose run --rm worker python -m nexus.monitoring.hiring_flow
	@echo "Ingestion complete!"

test:
	@echo "Running tests..."
	docker-compose run --rm worker pytest tests/ -v
	@echo "Tests complete!"

run:
	@echo "Starting Nexus services..."
	docker-compose up -d
	@echo "Services started!"
	@echo "  API: http://localhost:8000"
	@echo "  UI: http://localhost:8501"
	@echo "  Prefect: http://localhost:4200"

eval:
	@echo "Running evaluation suite..."
	docker-compose run --rm worker python scripts/eval_extraction.py
	@echo "Evaluation complete!"

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "Cleanup complete!"
