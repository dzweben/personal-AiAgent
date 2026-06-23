# handy shortcuts so i do not have to remember the long commands.
# run `make help` to see what is here.

.DEFAULT_GOAL := help
PYTHON ?= python3
VENV ?= venv

.PHONY: help
help: ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

.PHONY: venv
venv: ## create a virtual environment
	$(PYTHON) -m venv $(VENV)
	@echo "now run: source $(VENV)/bin/activate"

.PHONY: install
install: ## install the project in editable mode with all extras
	pip install -e ".[all]"

.PHONY: install-core
install-core: ## install just the core deps
	pip install -e .

.PHONY: test
test: ## run the test suite
	pytest -q

.PHONY: cov
cov: ## run tests with a coverage report
	pytest --cov=agent --cov-report=term-missing -q

.PHONY: lint
lint: ## lint with ruff
	ruff check .

.PHONY: fmt
fmt: ## format with black and ruff
	black .
	ruff check --fix .

.PHONY: typecheck
typecheck: ## run mypy
	mypy agent

.PHONY: check
check: lint typecheck test ## lint, typecheck, and test in one go

.PHONY: run
run: ## run the classic cli entry point
	$(PYTHON) main.py

.PHONY: serve
serve: ## run the http api
	$(PYTHON) -m agent.server

.PHONY: tools
tools: ## list the tools the agent can load
	$(PYTHON) -m agent.cli tools

.PHONY: clean
clean: ## remove caches and build junk
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

.PHONY: docker
docker: ## build the docker image
	docker build -t personal-aiagent .
