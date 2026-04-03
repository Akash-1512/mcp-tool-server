.PHONY: help run-local run-prod run-agent-local run-ui mode \
        seed-db test-unit test-integration lint format \
        docker-up docker-down install

# ─── Default ─────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "mcp-tool-server — available targets"
	@echo "────────────────────────────────────"
	@echo "  make install          Install dependencies via uv"
	@echo "  make seed-db          Create and seed local SQLite database"
	@echo "  make run-local        Start MCP server (LOCAL DEMO mode)"
	@echo "  make run-prod         Start MCP server (PRODUCTION mode)"
	@echo "  make run-agent-local  Run LangGraph agent (LOCAL DEMO mode)"
	@echo "  make run-ui           Launch Streamlit chat UI"
	@echo "  make mode             Print active infrastructure mode"
	@echo "  make test-unit        Run unit tests"
	@echo "  make test-integration Run integration tests (requires live server)"
	@echo "  make lint             Run flake8 linter"
	@echo "  make format           Run black + isort formatters"
	@echo "  make docker-up        Start all services via docker-compose"
	@echo "  make docker-down      Stop all services"
	@echo ""

# ─── Install ─────────────────────────────────────────────────────────────────
install:
	uv pip install -r requirements.txt

# ─── Database ────────────────────────────────────────────────────────────────
seed-db:
	@echo "Seeding local SQLite database from data/seed.sql..."
	@python -c "import sqlite3, pathlib; \
		conn = sqlite3.connect('data/enterprise.db'); \
		conn.executescript(pathlib.Path('data/seed.sql').read_text()); \
		conn.commit(); conn.close(); \
		print('Database seeded: data/enterprise.db')"

# ─── Server ──────────────────────────────────────────────────────────────────
run-local:
	DEMO_MODE=true uvicorn mcp_server.main:app --reload --port 8003

run-prod:
	DEMO_MODE=false uvicorn mcp_server.main:app --port 8003

# ─── Agent ───────────────────────────────────────────────────────────────────
run-agent-local:
	DEMO_MODE=true python agent/langgraph_agent.py

# ─── UI ──────────────────────────────────────────────────────────────────────
run-ui:
	streamlit run ui/chat_ui.py

# ─── Mode check ──────────────────────────────────────────────────────────────
mode:
	@python -c "import os; print('MODE:', 'LOCAL DEMO' if os.getenv('DEMO_MODE')=='true' else 'AZURE PRODUCTION')"

# ─── Tests ───────────────────────────────────────────────────────────────────
test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	pytest tests/integration/ -v --tb=short

# ─── Code quality ────────────────────────────────────────────────────────────
lint:
	flake8 mcp_server/ agent/ ui/ tests/ --max-line-length=100

format:
	black mcp_server/ agent/ ui/ tests/ --line-length=100
	isort mcp_server/ agent/ ui/ tests/

# ─── Docker ──────────────────────────────────────────────────────────────────
docker-up:
	docker-compose up --build

docker-down:
	docker-compose down -v