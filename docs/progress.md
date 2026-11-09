# Repository work log.  One entry per chunk, each with the test commands and
# their pass/fail counts (DESIGN.md 5.4 rule 9, DESIGN-PYTHON.md 5.2).

# callplot-python progress

Specs: `docs/DESIGN.md` (v11) for behavior, `docs/DESIGN-PYTHON.md` (v1,
2026-11-08) for language, layout, tools and commands.  Goldens, fixtures,
approved snapshots and reference outputs are committed truth from the Java
oracle (recorded in `reference/JDK_VERSION`, `reference/AWK_VERSION`,
`reference/PLANTUML_VERSION`): the oracle is always right, a mismatch means
this port is wrong.  Work happens on a branch, never on `main`.

## What landed on the restructure branch

The first attempt (`port` branch up to `1405501`) copied the JS port file by
file, including its `bin/` folder of by-path scripts.  The restructure
re-lands the same engine onto the Pythonic design: entry points through
`[project.scripts]` and no `bin/`, `src/callplot/` split per DESIGN-PYTHON.md
2.2 with `renderers/table/` and `renderers/html/` packages, a pytest harness
under `tests/`, and one CI job set under `.github/workflows/python.yml`.
The branch lands as one commit per chunk, PY0..PY15, so the branch can be
squashed later.

Byte fidelity: no renderer string literal was edited during the restructure;
the html/table modules were checked against the `git show HEAD:` blobs
(STRING-token multiset compare) before and after the fold.

## Verification so far (all against the committed oracle data)

```
golden    tests/golden/test_golden.py      697 passed, 0 failed
snapshot  tests/golden/test_snapshots.py   212 passed, 0 failed
reference tests/golden/test_reference.py    85 passed, 0 failed   (5 samples x 17)
unit      tests/unit/ (7 files)            417 passed, 0 failed   (101/47/61/27/51/59/71)
cli       tests/cli/test_cli.py             19 passed, 0 failed   (16 json cases + 3 extra)
                                            --------------------
          pytest -m "not fuzz"            1430 passed, 0 failed
```

The unit layer is `test_jcompat`, `test_parser`, `test_flow`, `test_ir`,
`test_escape`, `test_prep` and the added `test_entry` (Appendix B row: the
coverage gate cannot be met through the subprocess CLI layer).  The golden
harness rule stays as DESIGN.md 4.4 states: a `.exit` file that is not `0`
expects a `CallplotError` throw and its stdout is not compared; a `0` exit
compares bytes exactly, with a unified diff on a mismatch.

`docs/diagrams/{api,person-flow,run-internals}.msd` still render byte-identical
to their committed `.txt`, through the API and through the installed
`callplot`.

## Gates (DESIGN-PYTHON.md 4.7)

```
make lint (= ruff check . + ruff format --check . + mypy)   all green
  ruff check .                                            All checks passed (0 findings)
  ruff format --check .                                   57 files already formatted (docs/ excluded, Appendix B)
  mypy (strict, files = ["src"])                          Success: no issues found in 37 source files
.venv/bin/pytest --cov -m "not fuzz"            97.12% >= fail_under 90
                                                (2196 statements, 55 uncovered, 16 branch misses)
.venv/bin/python -m build                       callplot_py-0.1.0.tar.gz + .whl
.venv/bin/twine check dist/*                    PASSED x 2
.venv/bin/python tools/check_dist.py            ok, 43 entries, all inside callplot/ +
                                                callplot_py-*.dist-info/
```

Uncovered lines left are entry-module branches no path takes (rule 9/10 of
`section 3.6` inside the flag loop of `cli.py`, the table style's bad
character-reference throws) and `__init__.py`'s uninstalled-version fallback.

## Fuzz status (DESIGN-PYTHON.md 4.6)

`tools/oracle_client.py` (DESIGN.md 4.5.1 frame: one client per worker thread,
`threading.Timer` kill, exit code 124 for a case that never answered) and the
rewritten `tools/fuzz.py` (our own generator over the grammar of DESIGN.md 4.5
steps 1-3) are in the tree.  Runs so far: seed 99 x 40 = 280 runs 0 diffs, seed
1 x 300 = 2100 runs 0 diffs, and then the closing pair:

```
.venv/bin/pytest -m fuzz tests/fuzz_client_check.py   1 passed in 17.8 s
      client == one JVM per run, seed 99 x 300 cases x 7 modes = 2100 runs,
      0 diffs, up to 12 JVMs live at once
.venv/bin/python tools/fuzz.py --seed 1 --count 10000 cases 10000, runs 70000,
      diffs 0, fixtures saved 0, 59.7 s
```

The trust check runs FIRST, because a harness client that disagrees with the
plain java call would otherwise be blamed on the port (DESIGN.md 4.5.3: fix the
harness, never the data).  `test/fixtures/fuzz/` stayed empty: 0 diffs meant
0 fixtures, so PY14 commits no fixture files.

## Errata

All differences from the two specs are rows in `docs/appendix-b.md`, dated
2026-11-09 for this restructure: the paths.py `parents[1]` layout note, the
`prep()`/`prep_debug()` debug transport, the 4th `RunContext` `err` field, the
"no partial output" model that replaces the 8192-byte flush habit, the
`callplot-py` wheel-naming note, the `RuntimeException` class kept, the html
`table.py` fold, this log being re-added after `f545a2b` dropped it, the added
in-process entry-test file, `runpy` for the `-m` leg, `callplot-prep`'s argparse
exit 2, the first attempt's `awk_num` OFMT bug now fixed per DESIGN-PYTHON.md
3.8 rule 3, the ruff `per-file-ignores` extension for tests and tools, the
Makefile's `oracle-check`/`refs` retarget, the CI cron/per-job `if:` mechanics,
and `.gitignore` taking `dist/` plus the coverage data file.

## Next

1. Land the branch as PY0..PY15, one commit per chunk, on
   `py-restructure` off `port`.
2. Push and open the pull request against `port` for Edgar.
