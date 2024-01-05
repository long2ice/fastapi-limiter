checkfiles = fastapi_limiter/ tests/ examples/ conftest.py
black_opts = -l 100 -t py38
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
	@poetry update

deps:
	@poetry install

style: deps
	isort -src $(checkfiles)
	black $(black_opts) $(checkfiles)

check: deps
	black --check $(black_opts) $(checkfiles) || (echo "Please run 'make style' to auto-fix style issues" && false)
	ruff $(checkfiles)
	bandit -x tests -r $(checkfiles)

test: deps
	$(py_warn) pytest

build: deps
	@poetry build

ci: check test
