# Repository work log.  One entry per chunk, each with the test commands and
# their pass/fail counts (DESIGN.md 5.4 rule 9).  Chunk ids here are P0..:
# this is the Python port of the plan in DESIGN.md sections 5.1/5.3.

# callplot-python progress

Spec: DESIGN.md v9 (the same document the JavaScript port was built from;
DESIGN.md stays untracked in this repo because it names the DRM archive
sample).  Goldens, fixtures and approved snapshots are copied from the
finished JavaScript port: they are language-neutral oracle truth, produced
by the real Java toolchain recorded in reference/JDK_VERSION,
reference/AWK_VERSION and reference/PLANTUML_VERSION.  The oracle is always
right; a mismatch means the port is wrong.

Work happens on the `port` branch, never on `main` (DESIGN.md 1.6-6, 5.4-8).

## Chunk P0 - corpus and toolchain (W0 equivalent)

Read: ../callplot-js/reference, samples, test/{fixtures,golden,snapshots}.

Build: the corpus as committed truth - 57 fixtures (53 callplot inputs, 4
packet traces), 2145 golden files, 212 approved new-output snapshots, 62
reference toolchain files (JDK/AWK/PlantUML version pins, the 0.2 Java
sources, the Xalan XSL set), 93 sample files, LICENSE, .gitignore,
pyproject.toml, this log.  The DRM archive sample is absent: no fixture,
golden, snapshot, sample, path or commit message refers to it.  Nothing in
reference/ was run or modified (DESIGN.md 1.3, 5.4-3).

Tests: none yet (no port code).

Done: the oracle corpus is committed, byte-identical to the JS port's.

