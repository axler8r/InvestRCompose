# variables --------------------------------------------------------->8---------
PYTHON ?= python3
PROJECT_NAME := {shell basename $(CURDIR)}
DOCKER_COMPOSE := docker compose
UV := uv
RUFF = $(UV) run ruff
LINT_FLAGS := --fix --show-fixes --respect-gitignore --show-files
APP_DIR := $(CURDIR)/app
DOCKER_COMPOSE_FILE := $(APP_DIR)/compose.yml
SOURCE_DIR := investr
TEST_DIR := tests


# phony ------------------------------------------------------------->8---------
.PHONY: help install up down start stop restart clean lint format check test requirements build status logs mongosh


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

mongosh: ## Connect to MongoDB shell
	@echo "Connecting to MongoDB shell..."
	$(DOCKER_COMPOSE) --file $(DOCKER_COMPOSE_FILE) exec mongodb mongosh investr

clean: down ## Clean up Docker containers and images
	@echo "Cleaning up Docker containers and images..."
	$(DOCKER_COMPOSE) down --rmi all --volumes --remove-orphans


# code quality targets ---------------------------------------------->8---------
lint: ## Run linters
	@echo "Running linters..."
	$(RUFF) check $(SOURCE_DIR) $(LINT_FLAGS)
	$(RUFF) check $(TEST_DIR) $(LINT_FLAGS)

format: ## Format code using black
	@echo "Formatting code with black..."
	$(RUFF) format $(SOURCE_DIR) --verbose
	$(RUFF) format $(TEST_DIR) --verbose

check: lint format ## Run code quality checks
	@echo "Running code quality checks..."

# test targets ------------------------------------------------------>8---------
test: ## Run tests using pytest
	@echo "Running tests..."
	$(PYTHON) -m pytest $(TEST_DIR)

cli: ## Run the interactive CLI application
	@echo "Starting CLI application..."
	$(PYTHON) -m investr.cli.app
