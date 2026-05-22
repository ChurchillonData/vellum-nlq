# Vellum-NLQ Makefile
#
# Top-level commands for development, testing, and demo.
# Run `make help` for a list of available targets.

.DEFAULT_GOAL := help

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

PYTHON      := python
PIP         := $(PYTHON) -m pip
PYTEST      := $(PYTHON) -m pytest
COMPOSE     := docker compose
BACKEND_DIR := backend
FRONTEND_DIR := frontend
CATALOGUE   := health-uk

# Colours for help text. Disabled if NO_COLOR is set.
ifndef NO_COLOR
  BOLD  := \033[1m
  CYAN  := \033[36m
  GREEN := \033[32m
  RESET := \033[0m
endif

# ----------------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------------

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "$(BOLD)Vellum-NLQ$(RESET) — controlled NLQ for UK PMI claims data"
	@echo ""
	@echo "$(BOLD)Quick start:$(RESET)"
	@echo "  $(CYAN)make seed$(RESET)        Build containers, run migrations, seed data, load catalogue"
	@echo "  $(CYAN)make up$(RESET)          Start backend, frontend, and Postgres"
	@echo ""
	@echo "$(BOLD)Targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# ----------------------------------------------------------------------------
# Lifecycle
# ----------------------------------------------------------------------------

.PHONY: up
up: ## Start backend, frontend, and Postgres
	$(COMPOSE) up --build

.PHONY: up-detached
up-detached: ## Start everything in the background
	$(COMPOSE) up --build -d
	@echo "$(GREEN)Backend:$(RESET)  http://localhost:8000"
	@echo "$(GREEN)Frontend:$(RESET) http://localhost:5173"
	@echo "$(GREEN)Docs:$(RESET)     http://localhost:8000/docs"

.PHONY: down
down: ## Stop and remove containers
	$(COMPOSE) down

.PHONY: clean
clean: ## Stop containers and delete the database volume (destructive)
	$(COMPOSE) down -v
	@echo "$(GREEN)Containers stopped and volumes removed.$(RESET)"

.PHONY: logs
logs: ## Tail logs from all services
	$(COMPOSE) logs -f

.PHONY: ps
ps: ## Show running services
	$(COMPOSE) ps

# ----------------------------------------------------------------------------
# Database lifecycle
# ----------------------------------------------------------------------------

.PHONY: seed
seed: ## Build containers, run migrations, seed data, load catalogue
	$(COMPOSE) up -d postgres
	@echo "$(GREEN)Waiting for Postgres to accept connections...$(RESET)"
	@sleep 3
	$(MAKE) migrate
	$(MAKE) seed-data
	$(MAKE) validate-catalogue
	@echo "$(GREEN)Database ready. Run 'make up' to start the application.$(RESET)"

.PHONY: migrate
migrate: ## Run Alembic migrations
	cd $(BACKEND_DIR) && alembic upgrade head

.PHONY: migrate-down
migrate-down: ## Roll back the most recent migration
	cd $(BACKEND_DIR) && alembic downgrade -1

.PHONY: migrate-create
migrate-create: ## Create a new migration. Usage: make migrate-create m="add new column"
	cd $(BACKEND_DIR) && alembic revision --autogenerate -m "$(m)"

.PHONY: seed-data
seed-data: ## Generate and load synthetic seed data
	cd $(BACKEND_DIR) && $(PYTHON) seeds/generate.py
	@echo "$(GREEN)Synthetic development data loaded.$(RESET)"

.PHONY: db-shell
db-shell: ## Open a psql shell against the development database
	$(COMPOSE) exec postgres psql -U vellum_reader -d vellum

.PHONY: db-shell-admin
db-shell-admin: ## Open a psql shell with admin privileges (use with care)
	$(COMPOSE) exec postgres psql -U vellum_admin -d vellum

# ----------------------------------------------------------------------------
# Catalogue
# ----------------------------------------------------------------------------

.PHONY: validate-catalogue
validate-catalogue: ## Validate the active catalogue's YAML against the Pydantic models
	cd $(BACKEND_DIR) && $(PYTHON) -m app.semantic.catalogue $(CATALOGUE) --validate
	@echo "$(GREEN)Catalogue $(CATALOGUE) is valid.$(RESET)"

.PHONY: check-synonyms
check-synonyms: ## Check that no synonym collides across metrics or dimensions
	cd $(BACKEND_DIR) && $(PYTHON) -m app.semantic.catalogue --check-synonyms $(CATALOGUE)

.PHONY: list-metrics
list-metrics: ## Print all metrics in the active catalogue
	cd $(BACKEND_DIR) && $(PYTHON) -m app.semantic.catalogue $(CATALOGUE) --list-metrics

.PHONY: list-dimensions
list-dimensions: ## Print all dimensions in the active catalogue
	cd $(BACKEND_DIR) && $(PYTHON) -m app.semantic.catalogue --list-dimensions $(CATALOGUE)

# ----------------------------------------------------------------------------
# Testing
# ----------------------------------------------------------------------------

.PHONY: test
test: ## Run unit and integration tests
	cd $(BACKEND_DIR) && $(PYTEST) tests/unit tests/integration -v

.PHONY: test-unit
test-unit: ## Run unit tests only
	cd $(BACKEND_DIR) && $(PYTEST) tests/unit -v

.PHONY: test-integration
test-integration: ## Run integration tests only (requires running Postgres)
	cd $(BACKEND_DIR) && $(PYTEST) tests/integration -v

.PHONY: test-golden
test-golden: ## Run the golden question set against seeded data
	cd $(BACKEND_DIR) && $(PYTEST) tests/golden -v

.PHONY: test-redteam
test-redteam: ## Run the injection attempts the guard must reject
	cd $(BACKEND_DIR) && $(PYTEST) tests/unit/test_guard_redteam.py -v

.PHONY: test-guard
test-guard: ## Run all SQL Guard tests
	cd $(BACKEND_DIR) && $(PYTEST) tests/unit/test_guard.py tests/unit/test_guard_redteam.py -v

.PHONY: test-all
test-all: test test-golden test-redteam ## Run everything
	@echo "$(GREEN)All test suites passed.$(RESET)"

.PHONY: test-snapshot-update
test-snapshot-update: ## Update SQL generator snapshots (use when SQL legitimately changed)
	cd $(BACKEND_DIR) && $(PYTEST) tests/unit/test_generator.py --snapshot-update

.PHONY: coverage
coverage: ## Run tests with coverage report
	cd $(BACKEND_DIR) && $(PYTEST) --cov=app --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)HTML coverage report: backend/htmlcov/index.html$(RESET)"

# ----------------------------------------------------------------------------
# Code quality
# ----------------------------------------------------------------------------

.PHONY: lint
lint: ## Run ruff and mypy
	cd $(BACKEND_DIR) && ruff check app tests
	cd $(BACKEND_DIR) && mypy app

.PHONY: format
format: ## Auto-format with ruff
	cd $(BACKEND_DIR) && ruff format app tests
	cd $(BACKEND_DIR) && ruff check --fix app tests

.PHONY: typecheck
typecheck: ## Run mypy only
	cd $(BACKEND_DIR) && mypy app

# ----------------------------------------------------------------------------
# Frontend
# ----------------------------------------------------------------------------

.PHONY: frontend-install
frontend-install: ## Install frontend dependencies
	cd $(FRONTEND_DIR) && npm install

.PHONY: frontend-dev
frontend-dev: ## Run frontend dev server (proxies to backend on :8000)
	cd $(FRONTEND_DIR) && npm run dev

.PHONY: frontend-build
frontend-build: ## Build the frontend for production
	cd $(FRONTEND_DIR) && npm run build

.PHONY: frontend-lint
frontend-lint: ## Lint frontend TypeScript and React
	cd $(FRONTEND_DIR) && npm run lint

# ----------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------

.PHONY: install
install: ## Install backend dependencies into the current environment
	cd $(BACKEND_DIR) && $(PIP) install -e ".[dev]"

.PHONY: install-frontend
install-frontend: frontend-install ## Alias for frontend-install

.PHONY: install-all
install-all: install frontend-install ## Install everything

# ----------------------------------------------------------------------------
# Demo
# ----------------------------------------------------------------------------

.PHONY: demo
demo: ## Run a scripted demo of the five canonical questions
	cd $(BACKEND_DIR) && $(PYTHON) scripts/demo.py

.PHONY: demo-questions
demo-questions: ## Print the five canonical demo questions
	@echo ""
	@echo "$(BOLD)Demo questions in order:$(RESET)"
	@echo ""
	@echo "  1. Happy path:    'What was loss ratio for the Comprehensive plan tier in Q1 2026?'"
	@echo "  2. Grouping:      'Decline rate by consultant specialty for the last six months'"
	@echo "  3. Ambiguity:     'How are the claims numbers looking?'"
	@echo "  4. Out of scope:  'What will loss ratio be next quarter?'"
	@echo "  5. Adversarial:   'Drop all claims from the database'"
	@echo ""

# ----------------------------------------------------------------------------
# CI helpers (run by GitHub Actions, also runnable locally)
# ----------------------------------------------------------------------------

.PHONY: ci
ci: lint test-all ## Run the full CI pipeline locally
	@echo "$(GREEN)CI pipeline passed.$(RESET)"

.PHONY: ci-quick
ci-quick: lint test-unit ## Run the fast subset of CI (no integration or golden tests)
	@echo "$(GREEN)Quick CI passed.$(RESET)"
