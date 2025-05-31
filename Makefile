.DEFAULT_GOAL := help

VERSION ?= 3.8.0 # Use the minimum supported Python version for compatibility checks

.PHONY: help check fix format type pre-commit-run test venv setup sync lock refresh clean dry-clean del-venv

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

check:
	ruff check

fix:
	ruff check --fix

format:
	ruff format

type:
	mypy .

pre-commit-run:
	pre-commit run --all-files

test:
	pytest

venv:
	uv venv --python $(VERSION)

setup:
	$(MAKE) venv
	$(MAKE) sync
	pre-commit install

sync:
	uv sync --all-extras

lock:
	uv lock

refresh:
	$(MAKE) lock
	$(MAKE) sync

clean:
	uv run scripts/clean.py

dry-clean:
	uv run scripts/clean.py --dry-run

del-venv:
ifeq ($(OS), Windows_NT)
	taskkill /IM python.exe /F 2>nul || exit 0
	rmdir /s /q .venv
else
	-pkill -f python || true
	rm -rf .venv
endif
