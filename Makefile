# Gates for the Python port.  Every target prints node-test-style pass/fail
# counts (DESIGN.md 5.4 rule 9) and exits non-zero on any failure.
PY ?= python3

.PHONY: test unit golden cli snapshot syntax shots refs fuzz oracle-check check lint clean

test:
	$(PY) tools/run-tests.py

unit:
	$(PY) tools/run-tests.py unit

golden:
	$(PY) tools/run-tests.py golden

cli:
	$(PY) tools/run-tests.py cli

snapshot:
	$(PY) tools/run-tests.py snapshot

syntax:
	$(PY) tools/syntax-check.py

shots:
	$(PY) tools/screenshot.py

refs:
	$(PY) tools/gen-reference.py

# DESIGN.md 4.5 runs at scale: the gate passes the seed/count defaults (fuzz.py
# exits 2 without them).
FUZZ_ARGS ?= --seed 42 --count 10000

fuzz:
	$(PY) tools/fuzz.py $(FUZZ_ARGS)

oracle-check:
	$(PY) tools/oracle-check.py

check: lint
	$(PY) tools/run-tests.py

lint:
	$(PY) -m compileall -q src bin tools

clean:
	rm -rf src/__pycache__ src/callplot/__pycache__ src/callplot/render/__pycache__ \
		tools/__pycache__ test/unit/__pycache__ test/golden/__pycache__
