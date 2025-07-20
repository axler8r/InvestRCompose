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
.PHONY: help install up down start stop restart clean lint format check test


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

clean: down ## Clean up Docker containers and images
	@echo "Cleaning up Docker containers and images..."
	$(DOCKER_COMPOSE) down --rmi all --volumes --remove-orphans


# utility targets --------------------------------------------------->8---------


# test targets ------------------------------------------------------>8---------
test: ## Run tests using pytest
	@echo "Running tests..."
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing


# data management targets ------------------------------------------->8---------


# environment targets ----------------------------------------------->8---------

