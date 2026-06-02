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
	@echo "$(BOLD)Vellum-NLQ$(RESET) - controlled NLQ for UK PMI claims data"
	@echo ""
	@echo "$(BOLD)Quick start:$(RESET)"
	@echo "  $(CYAN)make install$(RESET)     Install backend dependencies"
	@echo "  $(CYAN)make test-unit$(RESET)   Run the current reliable test suite"
	@echo "  $(CYAN)make up$(RESET)          Start the target Docker stack when configured"
	@echo ""
	@echo "$(BOLD)Targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# ----------------------------------------------------------------------------
# Lifecycle
# ----------------------------------------------------------------------------

.PHONY: up
up: ## Start the target Docker stack when configured
	$(COMPOSE) up --build

.PHONY: up-detached
up-detached: ## Start the target Docker stack in the background
	$(COMPOSE) up --build -d
	@echo "$(GREEN)Postgres:$(RESET) localhost:5432 / database vellum"

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
seed: ## Target: build containers, run migrations, seed data, load catalogue
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
seed-data: ## Generate synthetic development data
	cd $(BACKEND_DIR) && $(PYTHON) seeds/generate.py
	@echo "$(GREEN)Synthetic development data generated.$(RESET)"

.PHONY: seed-portfolio-data
seed-portfolio-data: ## Generate the large portfolio demo dataset
	cd $(BACKEND_DIR) && $(PYTHON) seeds/generate.py --profile portfolio
	@echo "$(GREEN)Synthetic portfolio demo data generated.$(RESET)"

.PHONY: db-shell
db-shell: ## Open a psql shell with the read-only application role
	$(COMPOSE) exec postgres psql -U vellum_readonly -d vellum

.PHONY: db-shell-seed
db-shell-seed: ## Open a psql shell with the seed-data role
	$(COMPOSE) exec postgres psql -U vellum_seeder -d vellum

.PHONY: db-shell-admin
db-shell-admin: ## Open a psql shell with admin privileges
	$(COMPOSE) exec postgres psql -U vellum_admin -d vellum

.PHONY: db-check
db-check: ## Check local Postgres URLs and roles before seeding/execution
	cd $(BACKEND_DIR) && $(PYTHON) -m app.dbcheck

.PHONY: postgres-smoke
postgres-smoke: ## Verify seeded Postgres tables and guarded query execution
	cd $(BACKEND_DIR) && $(PYTHON) -m app.postgres_smoke

.PHONY: db-reset-local
db-reset-local: ## Destructive: recreate the local Postgres volume, migrate, and check roles
	$(PYTHON) scripts/reset_local_postgres.py --yes

# ----------------------------------------------------------------------------
# Catalogue
# ----------------------------------------------------------------------------

.PHONY: validate-catalogue
validate-catalogue: ## Validate the active catalogue YAML against Pydantic models
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
test: test-unit ## Run the current reliable backend test suite

.PHONY: test-unit
test-unit: ## Run unit tests only
	cd $(BACKEND_DIR) && $(PYTEST) tests/unit -v

.PHONY: test-integration
test-integration: ## Run optional live Postgres integration tests
	cd $(BACKEND_DIR) && $(PYTEST) tests/integration -v

.PHONY: test-golden
test-golden: ## Run YAML golden questions through the ask endpoint
	cd $(BACKEND_DIR) && $(PYTEST) tests/golden -v

.PHONY: test-redteam
test-redteam: ## Run red-team question and SQL guard cases
	cd $(BACKEND_DIR) && $(PYTEST) tests/redteam -v

.PHONY: test-guard
test-guard: ## Run implemented SQL Guard tests
	cd $(BACKEND_DIR) && $(PYTEST) tests/unit/test_guard.py -v

.PHONY: test-all
test-all: test-unit test-golden test-redteam ## Run all currently implemented tests
	@echo "$(GREEN)Implemented test suites passed.$(RESET)"

.PHONY: test-snapshot-update
test-snapshot-update: ## Update SQL generator snapshots when SQL legitimately changed
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
frontend-dev: ## Run the frontend dev server
	cd $(FRONTEND_DIR) && npm run dev

.PHONY: frontend-build
frontend-build: ## Build the frontend for production
	cd $(FRONTEND_DIR) && npm run build

.PHONY: frontend-lint
frontend-lint: ## Type-check and build the frontend
	cd $(FRONTEND_DIR) && npm run build

# ----------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------

.PHONY: install
install: ## Install backend dependencies into the current environment
	cd $(BACKEND_DIR) && $(PIP) install -e ".[dev]"

.PHONY: install-frontend
install-frontend: frontend-install ## Alias for frontend-install

.PHONY: install-all
install-all: install frontend-install ## Install implemented dependencies

# ----------------------------------------------------------------------------
# Demo
# ----------------------------------------------------------------------------

.PHONY: demo
demo: ## Planned: run a scripted demo of the canonical questions
	@echo "$(GREEN)Scripted demo is planned; use GET /ask/examples for current demo questions.$(RESET)"

.PHONY: demo-questions
demo-questions: ## Print the canonical demo questions
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
# CI helpers
# ----------------------------------------------------------------------------

.PHONY: ci
ci: lint test-all frontend-build ## Run the implemented CI pipeline locally
	@echo "$(GREEN)CI pipeline passed.$(RESET)"

.PHONY: ci-quick
ci-quick: lint test-unit ## Run the fast subset of CI
	@echo "$(GREEN)Quick CI passed.$(RESET)"
