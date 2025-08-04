# variables --------------------------------------------------------->8---------
PYTHON ?= python3
PROJECT_NAME := $(shell basename $(CURDIR))
DOCKER_COMPOSE := docker compose
RUFF = uvx ruff
TY = uvx ty
STRIPOUT = uvx nbstripout
LINT_FLAGS := --fix --show-fixes --respect-gitignore --show-files
APP_DIR := $(CURDIR)/app
DOCKER_COMPOSE_FILE := $(APP_DIR)/compose.yml
SOURCE_DIR := investr
TEST_DIR := tests


# phony ------------------------------------------------------------->8---------
.PHONY: help \
		install \
		requirements build up down start stop restart status logs clean \
		health agent-health data-health openbb-health webui-health \
		lint format check test \
		docker-rmdi docker-rmdv compose-rmi docker-clean \
		browse cli mongosh


# default target ---------------------------------------------------->8---------
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_.-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Quick Start:"
	@echo "  make install    # Install dependencies"
	@echo "  make up         # Start application"
	@echo "  make test       # Run tests"


# setup targets ----------------------------------------------------->8---------
install: ## Install dependencies using uv
	@echo "Installing dependencies..."
	uv sync


# life cycle targets ------------------------------------------------>8---------
requirements: ## Create a requirements.txt file from the current environment
	@echo "Exporting requirements from uv..."
	uv export --format requirements-txt --no-hashes --no-emit-project \
		--output-file $(APP_DIR)/requirements.txt

build: requirements ## Build all application components
	@echo "Building Docker images..."
	$(DOCKER_COMPOSE) --file $(DOCKER_COMPOSE_FILE) build
	@echo "Cleaning up requirements.txt..."
	rm --force $(APP_DIR)/requirements.txt

up: ## Start the application using Docker Compose
	@echo "Starting application..."
	$(DOCKER_COMPOSE) --file $(DOCKER_COMPOSE_FILE) up --detach

down: ## Stop the application using Docker Compose
	@echo "Stopping application..."
	$(DOCKER_COMPOSE) --file $(DOCKER_COMPOSE_FILE) down

start: up ## Start the application using Docker Compose

stop: down ## Stop the application using Docker Compose

restart: down up ## Restart the application using Docker Compose
	@echo "Restarting application..."

status: ## Show the status of Docker containers
	@echo "Checking status of Docker containers..."
	$(DOCKER_COMPOSE) --file $(DOCKER_COMPOSE_FILE) ps

logs: ## Show logs of Docker containers
	@echo "Showing logs of Docker containers..."
	$(DOCKER_COMPOSE) --file $(DOCKER_COMPOSE_FILE) logs --follow

agent-health: ## Check health of the Agent service
	@echo "Checking health status of Agent API..."
	@curl -s http://localhost:8000/health | $(PYTHON) -m json.tool || echo "Agent API unavailable"

data-health: ## Check health of the Data service
	@echo "Checking health status of Data API..."
	@curl -s http://localhost:8002/health | $(PYTHON) -m json.tool || echo "Data API unavailable"

openbb-health: ## Check health of the OpenBB API service
	@echo "Checking health status of OpenBB API..."
	@curl -s http://localhost:8001/health | $(PYTHON) -m json.tool || echo "OpenBB API unavailable"

webui-health: ## Check health of the Web UI service
	@echo "Checking health status of Web UI..."
	@curl -s http://localhost:5000/api/health | $(PYTHON) -m json.tool || echo "Web UI unavailable"

health: agent-health data-health openbb-health webui-health ## Check health services


# code quality targets ---------------------------------------------->8---------
lint: ## Run linter
	@echo "Running linters..."
	$(RUFF) check $(SOURCE_DIR) $(LINT_FLAGS)
	$(RUFF) check $(TEST_DIR) $(LINT_FLAGS)

format: ## Run formatter
	@echo "Formatting code with black..."
	$(RUFF) format $(SOURCE_DIR)
	$(RUFF) format $(TEST_DIR)

check: lint format ## Run code quality checks
	@echo "Running code quality checks..."

type-check: ## Run type checker
	@echo "Running type checker..."
	$(TY) check $(SOURCE_DIR)

clean: ## Clean up temporary files
	@echo "Cleaning up temporary files..."
	rm -rf $(APP_DIR)/__pycache__
	rm -rf $(APP_DIR)/*.pyc


# docker housekeeping targets --------------------------------------->8---------
docker-rmdi: ## Remove dangling Docker images
	@echo "Removing dangling Docker images..."
	docker image list --filter="dangling=true" --format="{{.ID}}" | xargs -L1 docker rmi

docker-rmdv: ## Remove dangling Docker volumes
	@echo "Removing unused Docker volumes..."
	docker volume list --filter="dangling=true" --format="{{.Name}}" | xargs -L1 docker volume rm

compose-rmi: ## Remove images managed by this application
	@echo "Removing images managed by this application..."
	docker compose --file $(DOCKER_COMPOSE_FILE) down --rmi local

docker-clean: docker-rmdi docker-rmdv compose-rmi ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."


# test targets ------------------------------------------------------>8---------
test: ## Run tests using pytest
	@echo "Running tests..."
	$(PYTHON) -m pytest $(TEST_DIR)


# utility targets --------------------------------------------------->8---------
browse: ## Open the application in a web browser
	@echo "Opening application in web browser..."
	xdg-open http://localhost:5000

cli: ## Run the interactive CLI application
	@echo "Starting CLI application..."
	$(PYTHON) -m investr.cli.app

mongosh: ## Connect to MongoDB shell
	@echo "Connecting to MongoDB shell..."
	$(DOCKER_COMPOSE) --file $(DOCKER_COMPOSE_FILE) exec mongodb mongosh investr

