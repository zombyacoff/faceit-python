.PHONY: check fix format lock refresh sync test type

check:
	ruff check

fix:
	ruff check --fix

format:
	ruff format

lock:
	uv lock

refresh:
	make lock
	make sync

sync:
	uv sync --all-extras

test:
	pytest

type:
	mypy .
