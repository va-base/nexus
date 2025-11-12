# Nexus v0 - Investment Research System

Nexus is a unified research, monitoring, and belief-management system built for next-generation investing. It ingests structured and unstructured data, extracts claims via LLMs, maintains calibrated belief states on hypotheses, triggers investigations, and updates positions—all with audited provenance.

## Quick Start

```bash
# Setup database and seed fixtures
make setup

# Bootstrap your initial data (optional)
# See docs/INITIAL_DATA_SETUP.md for details
make bootstrap

# Start all services
make run

# Access the system
# - API: http://localhost:8000
# - UI: http://localhost:8501
# - Prefect: http://localhost:4200

# Run ingestion pipelines
make ingest

# Run tests
make test

# Run evaluation suite
make eval

# Clean up
make clean
```

## Initial Data Setup

Nexus provides a flexible system for bootstrapping your initial knowledge and investment data. You can add:

- **Companies** you want to track (public or private)
- **Investment themes** and focus areas
- **Hypotheses** to monitor and evaluate
- **Raw thoughts, emails, and notes** as unstructured evidence
- **Research memos** with structured analysis
- **Priorities** and current focus areas

See [docs/INITIAL_DATA_SETUP.md](docs/INITIAL_DATA_SETUP.md) for a complete guide with examples and templates.

**Quick start:**
```bash
# 1. Add your data to data/initial/
cd data/initial/
cp companies.json.example companies.json
# Edit companies.json with your companies

# 2. Run bootstrap
make bootstrap
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for complete system design, including:
- Component architecture with Mermaid diagram
- Data models and schemas
- Monitoring pipelines (filings, earnings, hiring)
- Investigation playbooks
- Belief update logic with log-odds
- Provenance and compliance system
- Evaluation metrics and KPIs

## System Components

- **Event Bus**: Redis Streams for event-driven architecture
- **Database**: PostgreSQL with pgvector for embeddings
- **Lakehouse**: DuckDB + Parquet for analytics
- **Orchestration**: Prefect 2 for workflow management
- **LLM**: Mock extractor (default) with LiteLLM support
- **API**: FastAPI REST endpoints
- **UI**: Streamlit dashboard

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env

# Run individual services
python -m nexus.api.main  # API server
python -m nexus.monitoring.worker  # Worker
streamlit run nexus/ui/app.py  # UI

# Run specific monitoring flow
python -m nexus.monitoring.filings_flow
python -m nexus.monitoring.earnings_flow
python -m nexus.monitoring.hiring_flow
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_belief_engine.py -v

# Run with coverage
pytest tests/ --cov=nexus --cov-report=html
```

## Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `LLM_BACKEND`: LLM backend (mock, openai, anthropic)
- `OPENAI_API_KEY`: OpenAI API key (if using OpenAI)
- `ANTHROPIC_API_KEY`: Anthropic API key (if using Anthropic)

## Project Structure

```
nexus/
├── nexus/              # Main application code
│   ├── api/           # FastAPI endpoints
│   ├── belief/        # Belief update engine
│   ├── extraction/    # Claim extraction
│   ├── ingestion/     # Data parsers and validators
│   ├── investigation/ # Investigation playbooks
│   ├── monitoring/    # Monitoring flows
│   ├── storage/       # Storage adapters
│   ├── ui/            # Streamlit UI
│   └── utils/         # Utilities
├── tests/             # Test suite
├── scripts/           # Utility scripts
├── data/              # Data directory
│   ├── fixtures/      # Sample data
│   └── parquet/       # Parquet files
├── db/                # Database initialization
└── docker-compose.yml # Docker services
```

## License

Proprietary - All rights reserved
