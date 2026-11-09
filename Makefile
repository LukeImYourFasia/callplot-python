# Gates for the Python port (DESIGN-PYTHON.md 3.1 and 4.7-4.8).
# Every gate prints its own counts and exits non-zero on any failure.

PY ?= python3
PYTEST ?= .venv/bin/pytest

.PHONY: check test unit golden cli snapshot fuzz oracle-check refs shots dist lint clean

test:
	$(PYTEST)

unit:
	$(PYTEST) tests/unit -q

golden:
	$(PYTEST) tests/golden -q

cli:
	$(PYTEST) tests/cli -q

snapshot:
	$(PYTEST) tests/golden/test_snapshots.py -q

# DESIGN-PYTHON.md 4.6: the trust check runs first, then the big run.
FUZZ_ARGS ?= --seed 42 --count 10000

fuzz:
	$(PYTEST) tests/fuzz_client_check.py
	$(PY) tools/fuzz.py $(FUZZ_ARGS)

oracle-check:
	$(PYTEST) tests/fuzz_client_check.py

refs:
	$(PYTEST) tests/golden/test_reference.py -q

shots:
	$(PY) tools/screenshot.py

dist:
	$(PY) -m build
	-twine check dist/*
	$(PY) tools/check_dist.py

lint:
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .
	.venv/bin/mypy

check: lint test

clean:
	rm -rf .mypy_cache .ruff_cache dist coverage .coverage*
	rm -rf src/callplot/__pycache__ tools/__pycache__ tests/__pycache__
	rm -rf tests/*/__pycache__
