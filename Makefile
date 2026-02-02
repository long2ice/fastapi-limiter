checkfiles = fastapi_limiter/ tests/ examples/ conftest.py
py_warn = PYTHONDEVMODE=1

help:
	@echo "fastapi-limiter development makefile"
	@echo
	@echo  "usage: make <target>"
	@echo  "Targets:"
	@echo  "    up			Updates dev/test dependencies"
	@echo  "    deps		Ensure dev/test dependencies are installed"
	@echo  "    check		Checks that build is sane"
	@echo  "    build		Build package"
	@echo  "    test		Runs all tests"
	@echo  "    style		Auto-formats the code"

up:
	@uv sync --upgrade

deps:
	@uv sync --all-groups

style: deps
	@uv run ruff format $(checkfiles)

check: deps
	@uv run ruff check $(checkfiles)
	@uv run ty check $(checkfiles)

test: deps
	@$(py_warn) uv run pytest

build: deps
	@uv build

ci: check test
