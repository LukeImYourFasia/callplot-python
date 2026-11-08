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


## Chunk P1 - core package

Read: DESIGN.md 2.2, 3.1-3.9, 3.5, 3.6; the JS port's src/{constants,jcompat,
out,context,model,escape,flow,parser,ir,index}.js; test/unit/{jcompat,parser,
flow}.test.js.

Build: src/callplot/{constants,jcompat,out,context,model,escape,flow,parser,
ir,index}.py plus test/unit suites and tools/run-tests.py, the [unit]/[golden]/
[cli]/[snapshot] tag runner with node-test-style counts.  Java-faithful
details pinned here: `idiv` truncates toward zero; `javaTrim` strips only
code points <= 0x20; `parseJavaInt` is strict and int-ranged; `javaSplit`
keeps Java's trailing-empty drop and the all-empty -> [] case (probed on the
reference JVM when the corpus was generated); Parser.java:75's slash rule is
a fixed-width lookbehind that `re` compiles as is, so no scanner rewrite was
needed; Parser.java:85's `tkn++` is mirrored by an explicit index; `from` is
a Python keyword, so Message.from is `from_`.

Tests:

```
$ python3 tools/run-tests.py unit
[unit] pass 38 / fail 0
```

Done: the core parses and lays out every fixture exactly like the Java
oracle's goldens expect (the unit tests pin the parser/flow state machine;
the goldens themselves are compared in P2).

## Chunk P2 - TEXT and XML renderers + golden harness

Read: DESIGN.md 3.4 (TEXT/XML line loop, CharBuf, crunch, the XML link scan
that can run past the buffer end), 4.1; the JS port's src/render/text.js,
test/golden.test.js.

Build: src/callplot/render/text.py (plotOn, drawTextLines, writeLineXml,
drawPlayer, drawMessage, copyCaption, printComment) with the Java line
ranges in comments; test/golden/test_golden.py: byte compare, exit-code
semantics (a non-zero golden exit requires a throw), the 8192-byte
PrintWriter flush model for crashed runs, and a unified diff printed on
mismatch (DESIGN.md 4.1, which the JS port never implemented).

Tests:

```
$ python3 tools/run-tests.py golden
[golden] pass 106 / fail 0
$ python3 tools/run-tests.py unit
[unit] pass 38 / fail 0
$ python3 tools/run-tests.py
[golden] pass 106 / fail 0
[unit] pass 38 / fail 0
test: pass 144 / fail 0 in 0.05s
```

106 = 53 fixtures x {text, xml}: the 4 packet traces have no text/xml goldens
(their goldens are prep goldens, which land with the prep chunk).

Done: text and xml outputs are byte-identical to the oracle on every fixture,
including the fixtures whose oracle run crashed.  Modes whose renderer has
not landed raise RendererNotPortedError, so their goldens cannot pass by
accident.

## Chunk P3 - pic renderer

Read: DESIGN.md 3.4.2 (PIC/XPICTURE), 3.8 #8; the JS port's src/render/pic.js.

Build: src/callplot/render/pic.py (picOn, drawPlayerPic, drawMessagePic) with
the Java line ranges in comments; registered in index.py's static dispatch
table; test/golden/test_golden.py's MODES_DONE gains pic.  PIC keeps the
shared drawPictureOn skeleton, prints .PS/.PE, never calls columnOf, so the
fixtures with unknown aliases stay clean here, and every number goes through
fmtD (the -1.0 * line / 6.0 double math).

Tests:

```
$ python3 tools/run-tests.py golden
[golden] pass 159 / fail 0
$ python3 tools/run-tests.py
[golden] pass 159 / fail 0
[unit] pass 38 / fail 0
test: pass 197 / fail 0 in 0.06s
```

159 = 53 fixtures x {text, xml, pic}.

Done: pic output is byte-identical to the oracle on every fixture.
