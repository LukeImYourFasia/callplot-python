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

## Chunk P4 - svg renderer

Read: DESIGN.md 3.4.3, 3.5 typing rule; the JS port's src/render/svg.js.

Build: src/callplot/render/svg.py (svgOn, drawPlayerSvg, textout,
drawMessageSvg) with the fixed SVG text copied character for character from
the Java literals; f.vmlXSize/vmlYSize are set by the prologue; the stagger
ternary bumps ctx.mynum only when stagger is on; every number goes through
fmtI/fmtD and column*width uses Java int division via idiv.

First run exposed a real porting slip caught by the oracle, not by the goldens
being edited:

```
$ python3 tools/run-tests.py golden
[golden] pass 164 / fail 48
... [golden] zero_pitch svg: stdout bytes differ
--- port zero_pitch svg
+++ oracle zero_pitch svg
-<svg width='1' height='1' viewBox='0 0 10 9'>
+<svg width='1in' height='1in' viewBox='0 0 10 9'>
```

The port had dropped the "in" units in the <svg> element; after fixing the
literal (never the golden):

```
$ python3 tools/run-tests.py golden
[golden] pass 212 / fail 0
```

Done: svg is byte-identical to the oracle on all 53 fixtures (212 = 53 x 4
modes text/xml/pic/svg).

## Chunk P5 - VML renderer (also drives -vxml)

Read: DESIGN.md 3.4.4, 3.8 #1 (the unclosed <plot>/<picture> bug kept), 3.8 #5
(arrows drawn at the final Y), 3.5 typing rule; the JS port's src/render/vml.js.

Build: src/callplot/render/vml.py (vmlOn, drawPlayerVml, drawMessageVml).
Kept bug-compatible on purpose: the VML epilogue never closes <plot>/<picture>,
wid stays Java-int through the idiv/parseJavaInt chain so it prints without a
".0" while the doubles print with one, and the caption's first line is read
through arrAt so an empty caption still throws IndexError.

Tests (first run, no port bug found this chunk):

```
$ python3 tools/run-tests.py golden
[golden] pass 318 / fail 0
```

318 = 53 fixtures x {text, xml, pic, svg, vml, vxml}.

Done: vml and vxml are byte-identical to the oracle on every fixture,
including the fixtures whose oracle run crashed mid-buffer.

## Chunk P6 - OmniGraffle renderer

Read: DESIGN.md 3.4.5, 3.6 (shared player/message ids and stagger counters via
RunContext), 3.8 #6 (caption[0] mutation survives into the XML epilogue
comments) and #7 (repeatLabel debug lines land on stderr, not stdout); the
JS port's src/render/graffle.js.

Build: src/callplot/render/graffle.py (emit, the seven fixed plist text blocks
copied verbatim, graffleOn, drawPlayerGraffle, drawMessageGraffle).  Graffle
draws messages BEFORE players (Flow.java:551-559); it shares printComment
with render/text.py for the -xml epilogue; ids come from ctx.playerId/ctx.
messageId so they carry across files like the Java statics; the repeatLabel
debug line goes to ctx.err.  Registered in index.py's dispatch table;
test_golden.py's MODES_DONE gains graffle.

First run: the oracle caught the first RTF header line missing its
`<string>` prefix (`{\rtf1...` vs `<string>{\rtf1...`) in all 44 fixtures
whose graffle output has an RTF block; fixed in the port, never the golden:

```
$ python3 tools/run-tests.py golden
[golden] pass 327 / fail 44
... zero_caption_graffle graffle: stdout bytes differ
-{\rtf1\mac\ansicpg10000\cocoartf824\cocoasubrtf110
+<string>{\rtf1\mac\ansicpg10000\cocoartf824\cocoasubrtf110
```

After the fix:

```
$ python3 tools/run-tests.py golden
[golden] pass 371 / fail 0
```

Done: all seven landed modes (text, xml, pic, svg, vml, vxml, graffle) are
byte-identical to the oracle on all 53 fixtures: 371 = 53 x 7, 0 fail,
including the fixtures whose oracle run crashed (throw required, partial
output cut at the 8192-byte PrintWriter boundary).

## Chunk P7 - mermaid + plantuml renderers, snapshot harness

Read: DESIGN.md 3.9 (IR), 3.10 (mermaid), 3.11 (plantuml + its escape table),
4.7 (approved snapshots, the stdout model of 4.4); the JS port's
src/render/{mermaid,plantuml}.js, test/snapshot.test.js.

Build: src/callplot/render/{mermaid,plantuml}.py, one-to-one with the IR
dicts; registered in index.py's dispatch table (they read buildModel(f), not
Flow).  test/snapshot/test_snapshot.py: the [snapshot] harness mirroring the
JS one: render fresh through plotFlow, byte-compare test/snapshots/<fixture>
.<ext>, the same 8192-byte PrintWriter truncation on a throw, unified diff
printed on mismatch, a missing snapshot fails as a programmer error rather
than passing.

Decision pinned here: mermaid, plantuml and html have NO goldens - the Java
oracle never produced them (section 4.7).  The oracle for these three is the
212 approved snapshots (53 fixtures x {mmd, puml, html-topbottom,
html-sidebyside}), and the golden harness's mode map stays at the 13
Java-pinned modes + 8 prep.  The html layout entries join NEW_MODES_DONE
when the html renderer lands.

Tests:

```
$ python3 tools/run-tests.py snapshot
[snapshot] pass 106 / fail 0
$ python3 tools/run-tests.py
[golden] pass 371 / fail 0
[snapshot] pass 106 / fail 0
[unit] pass 38 / fail 0
test: pass 515 / fail 0 in 0.14s
```

106 = 53 fixtures x {mmd, puml}.

Done: mermaid and plantuml reproduce the approved snapshots byte for byte on
every fixture, on the first run, no porting slip.
