# Förder-Radar – Convenience targets
# Usage: make <target>  (run from repo root)

.PHONY: test lint check typecheck brief dashboard clean install help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime + dev dependencies
	pip install mcp/requirements.txt mcp/requirements-dev.txt

test: ## Run the full test suite with coverage
	cd mcp && pytest --cov=. --cov-report=term-missing

lint: ## Run ruff linter
	ruff check mcp/*.py

typecheck: ## Run mypy type checker
	cd mcp && mypy *.py

check: lint typecheck test ## Run lint + typecheck + test (CI-equivalent)

brief: ## Generate a weekly brief for the default profile
	cd mcp && python3 brief.py --felder Biologie Nachhaltigkeit --karriere postdoc

dashboard: ## Sync data and start a local dashboard server
	bash dashboard/sync-data.sh
	cd dashboard && python3 -m http.server 8080

clean: ## Remove Python caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
