.DEFAULT_GOAL := help

EXAMPLE ?= examples/01_ray_init.py
CLUSTER_EXAMPLE ?= examples/cluster/01_nodes.py

.PHONY: help install format lint test test-v test-cluster run cluster-check cluster-up cluster-status cluster-run cluster-down check-all clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-14s %s\n", $$1, $$2}'

install:  ## Install all dependencies
	uv sync --all-groups

format:  ## Auto-format and fix lint issues
	uv run --with ruff ruff format examples tests cluster
	uv run --with ruff ruff check --select E9,F63,F7,F82 --fix examples tests cluster

lint:  ## Run critical ruff checks (syntax, undefined names)
	uv run --with ruff ruff check --select E9,F63,F7,F82 examples tests cluster

test:  ## Run the local test suite
	uv run python -m pytest tests/test_all.py

test-v:  ## Run the full test suite verbosely
	uv run python -m pytest -v

test-cluster:  ## Run cluster-related tests on a local two-node Ray setup
	uv run python -m pytest tests/test_cluster_cli.py tests/test_cluster_examples.py -v

run:  ## Run one local example (override with EXAMPLE=examples/02_remote_tasks.py)
	uv run $(EXAMPLE)

cluster-check:  ## Validate optional Tailscale/SSH cluster prerequisites
	uv run cluster/ray_cluster.py check

cluster-up:  ## Start the optional two-node Tailscale/SSH Ray cluster
	uv run cluster/ray_cluster.py up

cluster-status:  ## Show status for the optional Ray cluster
	uv run cluster/ray_cluster.py status

cluster-run:  ## Run one example on the optional Ray cluster (override with CLUSTER_EXAMPLE=...)
	uv run cluster/ray_cluster.py run $(CLUSTER_EXAMPLE)

cluster-down:  ## Stop the optional Ray cluster
	uv run cluster/ray_cluster.py down

check-all: install format lint test clean  ## Run format, lint, local tests, and clean
	@echo "All checks passed!"

clean:  ## Remove generated outputs and caches
	rm -rf dist build *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage coverage.xml
	rm -rf out
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name .DS_Store -exec rm {} +
