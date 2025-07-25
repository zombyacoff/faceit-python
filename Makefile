.DEFAULT_GOAL := help

PYTHON_VERSION ?= 3.8 # Use the minimum supported Python version for compatibility checks

.PHONY: help
help:
	@echo Available targets:
	@echo   check            Run ruff linter
	@echo   fix              Auto-fix lint issues with ruff
	@echo   format           Format code with ruff
	@echo   type             Run mypy type checks
	@echo   pre-commit-run   Run all pre-commit hooks on all files
	@echo   test             Run tests with pytest
	@echo   venv             Create virtual environment with specified Python version
	@echo   setup            Create venv, install dependencies, install pre-commit hooks
	@echo   sync             Sync dependencies
	@echo   lock             Update dependency lock file
	@echo   refresh          Update lock file and sync dependencies
	@echo   clean            Remove caches and temporary files
	@echo   dry-clean        Show what would be deleted (dry run)
	@echo   del-venv         Terminate Python processes and delete .venv

.PHONY: check
check:
	uv run ruff check

.PHONY: fix
fix:
	uv run ruff check --fix

.PHONY: format
format:
	uv run ruff format

.PHONY: type
type:
	uv run mypy .

.PHONY: pre-commit-run
pre-commit-run:
	uv run pre-commit run --all-files

.PHONY: test
test:
	uv run pytest

.PHONY: venv
venv:
	uv venv --python $(PYTHON_VERSION)

.PHONY: setup
setup:
	$(MAKE) venv
	$(MAKE) sync
	uv run pre-commit install

.PHONY: sync
sync:
	uv sync --all-extras

.PHONY: lock
lock:
	uv lock

.PHONY: refresh
refresh:
	$(MAKE) lock
	$(MAKE) sync

.PHONY: clean
clean:
	uv run scripts/clean.py

.PHONY: dry-clean
dry-clean:
	uv run scripts/clean.py --dry-run

.PHONY: del-venv
del-venv:
ifeq ($(OS),Windows_NT)
	-taskkill /IM python.exe /F 2>nul
	@if exist .venv rmdir /s /q .venv
else
	-pkill -f python || true
	[ -d .venv ] && rm -rf .venv || true
endif
