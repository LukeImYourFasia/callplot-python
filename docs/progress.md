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

## Chunk P8 - html page renderer (layout + style + svg + table + page)

Read: DESIGN.md 3.12.2 (page contract), 3.12.3 (link/back-ref contract),
3.12.4 (geometry: estimated text width, pitch clamp 150..300, band stacking),
3.12.5 (detail table), 3.12.6 (radio-switch layouts), 3.12.7 (one CSS string);
the JS port's src/render/html/{layout,style,svg,table,page}.js.

Build: src/callplot/render/html/{layout,style,svg,table,page}.py plus the
package __init__.py, one module per JS module (DESIGN.md 2.2 file map); the
html geometry is JS floating-point arithmetic, so jcompat.py gains jsNum
(JS number -> string: integral doubles print bare, others shortest round-trip
repr) and jsRound (Math.round is half-toward-+Inf, Python round is
half-to-even - a real trap on the pitch step).  Geometry and drawing share
computeLayout, so they cannot drift.  Registered as _LANDED["html"] = pageOn;
NEW_MODES_DONE gains html_topbottom/html_sidebyside.

First run: 96 failures, all one class - five CSS var/property lines had the
trailing , and ; swapped against the approved snapshots.  Fixed in the port,
never the snapshots:

```
$ python3 tools/run-tests.py snapshot
[snapshot] pass 116 / fail 96          # before
[snapshot] pass 212 / fail 0           # after the css fix
```

Tests:

```
$ python3 tools/run-tests.py snapshot
[snapshot] pass 212 / fail 0
$ python3 tools/run-tests.py
[golden] pass 371 / fail 0
[snapshot] pass 212 / fail 0
[unit] pass 38 / fail 0
test: pass 621 / fail 0 in 0.2s
```

Done: all four new outputs (mmd, puml, html-topbottom html, html-sidebyside
html) reproduce the 212 approved snapshots byte for byte on all 53 fixtures,
including the crash fixtures (html throws before the first byte on the
bad-option ones, matching the truncated snapshots).

## Chunk P9 - six legacy table styles

Read: DESIGN.md 3.13 (pipeline), 3.13.1 (no XML intermediate, D8), 3.13.2
(per-style columns), 3.13.3 (Xalan serializer rules: XML decl first line,
no trailing line end, empty element -> <foo/>, <tt/> stays), 3.13.4 (Xalan
parse errors: bare &, raw '<' -> TableInputError, exit 255 goldens); the
JS port's src/render/table/{index,common,archtable,htmltable,htmltable2,htmltable3,nolinks,wordtable}.js.

Build: src/callplot/render/table/{__init__,common,index,archtable,htmltable,htmltable2,htmltable3,nolinks,wordtable}.py.
index.py: drawTextLines (XML lines, links follow the file's option - the
oracle runs jref -xml + Xalan, and W20 found the file's value beats a
forced one), checkPictureLine (bare & throws), fixLinkQuotes (Xalan's
double re-quote), escapeAnnotated (entity decode + rule-8 reprint, bad
char refs throw), rows per numbered message, STYLES map with the tmltable
alias (lib/tmltable.xsl is a byte copy of htmltable.xsl, section 1.3),
TABLE_STYLES exported for the CLI's style validation.  wordtable fixed
text copied from the goldens byte for byte (attribute order and the
".5pt;  " double space included).

Tests:

```
$ python3 tools/run-tests.py golden
[golden] pass 689 / fail 0
$ python3 tools/run-tests.py
[golden] pass 689 / fail 0
[snapshot] pass 212 / fail 0
[unit] pass 38 / fail 0
test: pass 939 / fail 0
```

689 = 53 fixtures x 13 modes (text, xml, pic, svg, vml, vxml, graffle +
six table styles); table-xml has only .err goldens, so the harness skips
it, exactly like the JS one.

Done: every legacy table style reproduces the Xalan oracles byte for byte,
including the styles' crash fixtures (bad bool/int inputs and the bare-&
annotation fixtures that make Xalan exit 255).

## Chunk P10 - packet-trace converter (prep, the awk oracle)

Read: DESIGN.md 3.14 (rules in file order), 3.14.1 (pinned awk semantics:
every rule in order, next stops the line, changing $0 re-splits, OFMT %.6g
via awkNum, sub first-match/gsub all), 3.14.2 rule table, 3.14.3 quirks
(first "from last" is the whole time of day; >52 addresses get an empty
letter; INFO matches INFORMATION; dash rules fall through to the ! line),
3.14.4 (debug lines are NOT written to a file named "debug" - the port
returns them; Appendix B); the JS port's src/prep/prep.js.

Build: src/callplot/prep.py (awkNum on top of jcompat's jsNum - %.6g then
shortest round-trip print, awkNumPrefix/tollTime field scanners, splitFields
with FS " " and fields padded to four, prep returning {"out", "debug"}).
__init__.py re-exports prep (section 2.3 API); test_golden.py's PREP_DONE
enables prep/prep-links over the four .trace fixtures.

Tests:

```
$ python3 tools/run-tests.py golden
[golden] pass 697 / fail 0
$ python3 tools/run-tests.py
[golden] pass 697 / fail 0
[snapshot] pass 212 / fail 0
[unit] pass 38 / fail 0
test: pass 947 / fail 0
```

697 = 689 + 8 prep goldens (4 traces x {prep, prep-links}, mawk 1.3.4 oracles
from gen-golden-extra.sh, recorded in reference/AWK_VERSION).

Done: first run green, no slip: the whole awk rule ladder, the t0/lt/t
ladder (t takes $0 BEFORE the gsub triple escapes it), the ALIAS/GUYS
letter-minting, the SIP/HTTP first-field removal (replace(f[0] + " ", "")
always matches at 0) and the %.6g time lines all reproduce mawk byte for
byte, with and without --links.

## Chunk P11 - the three commands (callplot, callplot-prep, plottable)

Read: DESIGN.md 3.7 (Main.java arg loop, verbatim usage text, error model,
exit codes), 3.14 (callplot-prep), 3.13.5 (plottable: -debug/-style
positionals, _x_<pid>.xml, unknown style exits 1), 4.4 (the 15 CLI cases:
8 W0-golden against test/golden/cli, 7 W17 condition cases); the JS port's
bin/{callplot,callplot-prep,plottable}.js, test/cli/test_cli.js.

Build: bin/callplot.py (the Main.java loop; the 8192-byte PrintWriter flush
model kept on crashed runs; `callplot: <Name>: msg` + exit 1; EPIPE exits 0
silently; graffle -- debug from the shared ctx.err flushed to stderr per
file; USAGE transcribed programmatically from the JS port's array - cmp of
both commands' no-arg stderr proved it byte-identical, 3866 bytes),
bin/callplot-prep.py (--links, --debug-file; the awk "debug" file is NOT
written - section 3.14.4), bin/plottable.py (-debug keeps _x_<pid>.xml,
unknown style exits 1 per 3.13.5, usage to stdout per the pinned
plottable_usage.expected).  Corpus: test/cli/*.json, test/cli/inputs/ and
plottable_usage.expected copied from the JS repo (language-neutral pins).
test/cli/test_cli.py: the [cli] harness mirroring the JS runner - golden
cases compare test/golden/cli/<name> {out,exit} (stdout bytes + exit code;
the .err files exist but 4.4 never compares stderr), condition cases reuse
existing goldens or check codes/pipe/temp-folder effects; an unhandled case
fails as a programmer error.

First run: 15/16 green; html_bad_layout_file (-html with a bad
opt/htmlLayout in the FILE) exited 0 because pickLayout read "htmlLayout"
in opts as a force, while JS's `opts.htmlLayout !== undefined` treats the
CLI's cleared value (undefined) as NOT forcing: the port uses None the same
way.  Fixed in the port (page.py picks opts.get(...) and falls through to
the file's option when it is None), never the pinned case:

```
$ python3 tools/run-tests.py cli
[cli] pass 15 / fail 1        # before
[cli] pass 16 / fail 0        # after the pickLayout fix
```

Tests:

```
$ python3 tools/run-tests.py cli
[cli] pass 16 / fail 0
$ python3 tools/run-tests.py
[cli] pass 16 / fail 0
[golden] pass 697 / fail 0
[snapshot] pass 212 / fail 0
[unit] pass 38 / fail 0
test: pass 963 / fail 0
```

16 = 8 oracle-golden cases + 8 condition cases (the DESIGN table's 15 rows
plus epipe's own runner case counted once: table_bad_style/html_bad_layout/
flag_wins/table_default/plottable usage+debug/prep_stdin/epipe).

Done: the commands match the oracle CLI goldens byte for byte (stdout and
exit code, crashed runs' stdout truncated at the 8192-byte flush boundary)
and the condition cases behave: unknown style exits 1 with empty stdout,
-html=sidebyside wins over the file's topbottom, plottable -debug retains
_x_<pid>.xml equal to the XML golden, callplot-prep writes no "debug" file,
a closed pipe exits 0 with empty stderr.

## Chunk P12 - fuzz tooling (frame client, pool, oracle trust check, fuzz runner)

Read: DESIGN.md 4.5 (grammar rules 1-6, 7 core modes, rule 5: java
non-zero exits compare the exit code only, first 50 diffs -> fixtures),
4.5.1 (CASE/RESULT byte frames, JAVA_TOOL_OPTIONS on every java leg,
timeouts belong to the runner: no RESULT in 5 s -> SIGKILL, record 124,
new harness; trust check: 300 seed-99 x 7 pool vs one-JVM-per-run, equal
exit codes/stdout), 4.5.2 (the probe table and the 6 classes Edgar provides;
FuzzOracle.java + probes were copied unchanged, cmp-identical to the JS
repo's oracle files, compiled per the README into reference/build-{tools,
probes}, both gitignored), 4.5.3 (traps: stderr is log-only - "Picked up
JAVA_TOOL_OPTIONS" must never be read as data; reference/build must NOT be
on -cp; per-case loader); W19a-W19e acceptance (1,000 FileProbe frames:
sizes 0, 1, 8,191, 8,192, 8,193, 100,000, non-ASCII, holding "RESULT");
tools/oracle/{client,pool,check-oracle}.js and tools/fuzz.js as the port.

Build: tools/oracle/cases.py (the mulberry32 case generator; verified
byte-identical to the JS tooling: 12-number RNG stream and the sha256 of
every case of seed 99 x 300 match /tmp/opencode/{js,py}-cases.txt exactly),
tools/oracle/client.py (OracleClient: one harness JVM via Popen, byte-frame
buffer, deadline via select+os.read, stderr to a temp file, never read as
protocol data), tools/oracle/pool.py (runHarnessTasks: 8 client threads off
a shared queue; 5 s timeout -> SIGKILL + exit 124 + fresh harness process;
a harness that died mid-run records 124 with the reason), tools/oracle-
check.py (the 10 probe checks of the 4.5.2 table - ExitProbe 7/`hi\n`,
ReturnProbe 0/`ok\n`, ThrowProbe 1/`a`, StaticProbe x3 all `1\n` in one
process, FileProbe round-trip of `é/` + newline + 10,000 x, LoopProbe 124
then the next case works - plus the W19a 1,000-file probe frame sizes check,
then the 300 x 7 trust check; the one-JVM leg is the JS tools/jref.sh
invocation inlined, no jref script in this repo), tools/fuzz.py (the 7 core
modes, fresh Out/RunContext/opts per run on the port side, rule 5, first
50 diffs as test/fixtures/fuzz/seedS_caseK).  Makefile fuzz: FUZZ_ARGS
defaults --seed 42 --count 10000 (fuzz.py exits 2 without them, the JS
usage error mirrored).

First runs: two client slips, both fixed in the port, never in the oracle
files: (a) select.select arity - 3.14's select.select is (rlist, wlist,
xlist, timeout), the 3-argument call raised TypeError "arguments 1-3 must
be sequences"; (b) bytes buffer - `del self.buf[:frameEnd]` raised
TypeError on bytes (no item deletion); re-sliced instead.  After the fixes
probes 10/10 green, seed-5 x 3 trust check clean, seed-42 x 30 fuzz clean.

Tests:

```
$ make lint
$ make oracle-check
probes: pass 10 / fail 0
trust check: seed 99, cases 300, modes 7
runs: 2100
harness path: 2.4 s
jref path: 19.3 s (9 ms/run)
diffs: 0
TRUST CHECK PASS
$ make fuzz
cases: 10000, runs: 70000, diffs: 0, fixtures saved: 0
time: 55.8 s
$ python3 tools/run-tests.py
[cli] pass 16 / fail 0
[golden] pass 697 / fail 0
[snapshot] pass 212 / fail 0
[unit] pass 38 / fail 0
test: pass 963 / fail 0
```

Measured times for 4.5.1 (recorded as the design asks): the harness path
did 2,100 runs in 2.4 s against the one-JVM-per-run path's 19.3 s (9 ms/
run, not the ~300 ms/start-up the design estimate assumed: this OpenJDK
1.8 server VM pays ~9 ms warm per java leg); the pool is still ~8x faster
per run, and the full fuzz of 70,000 runs took 55.8 s wall, minutes not
hours as 4.5.1 expects.

Done: the harness was checked before use (probes then the 2,100-run trust
check, both green); 10,000 seed-42 cases x 7 modes match one-JVM-per-run
java and the Python port with 0 differences, so no fuzz fixtures were
needed and the golden corpus stays as it is; cases.py emits exactly the
JS generator's stream, so both ports fuzz the same cases.

## Chunk P13 - the syntax gate (mmdc + plantuml.jar over the snapshots)

Read: DESIGN.md 4.2/4.7 ("syntax": mmdc on every Mermaid snapshot, java
-jar plantuml.jar -checkonly on every PlantUML snapshot; empty snapshots
are the crashing fixtures' flushed output - skipped, counted; exit 0 =
every non-empty accepted; section 2.6: tools/ only, exec with argument
arrays, never a built shell string); the JS port's tools/syntax-check.js
and tools/mmdc-puppeteer.json (--no-sandbox for the headless fd check).

Build: tools/syntax-check.py (walks test/snapshots, .mmd -> node
node_modules/@mermaid-js/mermaid-cli/src/cli.js -i ... -o /tmp/opencode/
syntax/... -p tools/mmdc-puppeteer.json, .puml -> java -jar reference/
plantuml.jar -checkonly; failures print the stderr head, then the counts),
tools/mmdc-puppeteer.json (same one-line puppeteer config as the JS repo).
Toolchain setup (gitignored, never committed): node_modules copied
byte-identical from the JS repo's proven tree (same mermaid-cli 12.2.0 +
puppeteer versions; 522 M, node_modules/ is in .gitignore, so the repo
stays a Python repo with no package.json).

First run: green on the first try, no slips: 96 accepted, 10 empty
skipped - the same split as the JS gate (212 snapshots total in the
[snapshot] harness; the 106 mmd/puml ones minus the 10 the crashing
fixtures flush as empty).

Tests:

```
$ make lint
$ make syntax
syntax: 96 accepted, 10 empty skipped
$ python3 tools/run-tests.py
test: pass 963 / fail 0
```

Done: every non-empty Mermaid snapshot parses in mermaid-cli and every
non-empty PlantUML snapshot parses in the archive's plantuml.jar; the
gate exits 0 and matches the JS port's gate counts exactly.

## Chunk P14 - the refs gate, the screenshot tool, the README, Appendix B

Read: DESIGN.md 4.10 (samples/reference: every output for every sample;
compatible outputs from the oracle - jref one-JVM-per-run for the 7 core
modes, the plottable pipeline jref -xml + Xalan per archive .xsl for the
6 table styles, htmltable built from tmltable.xsl per 3.13.2; new outputs
byte-copied from the approved snapshots; trace_sip: .msd from the
archive's prep.awk in a fresh temp dir (the 0.2 awk drops a debug file in
the cwd), verified against the trace_sip.prep.out golden, its 4 new
outputs rendered by the port, the raw .trace copied; index.html one
table, every cell a link, fred/fred2 legacy-table cells marked "(no
numbered messages)"; 5 x 17 = 85), 4.7 shots (README sample-output
pictures from committed HTML), Appendix C README draft, Appendix B errata
format; the JS port's tools/gen-reference.js, tools/screenshot.js,
README.md.

Build: tools/gen-reference.py (the same pipeline: the jref invocation
inlined - no jref script in this repo - awk prep with drift check against
the golden, Xalan over the archive .xsl files, new outputs copied from
test/snapshots or rendered by the port for trace_sip, index.html, count
check 85), tools/screenshot.py (the puppeteer capture runs in node from
the repo's gitignored node_modules, driven as a module -e so bare imports
resolve; the two JS-tool notes kept: sidebyside captured at 1500 px,
wordtable body re-wrapped for the capture only; PNGs under 8,000 bytes
fail), README.md (Appendix C draft adapted: python entry points,
make-target development section, embedded docs/images PNGs),
docs/appendix-b.md (the 4 DESIGN Appendix B rows + the port's own notes:
CLI error line instead of a JVM stack trace; the JS CLI never flushed
ctx.err for graffle's System.err debug lines - this port does, verified
against ../callplot-js/bin/callplot.js; EPIPE exit 0).

Gates: refs regenerated all 85 outputs and git showed ZERO drift against
the committed samples/reference - the oracle pipeline and the approved
snapshots reproduce the committed bytes, including the port-rendered
trace_sip new outputs. shots: 8/8 PNGs, all well above the 8,000-byte
floor (smallest 58,787; verified visually: numbered rows, annotation
columns, both html layouts). syntax gate landed green in P13 (96/10).

Tests:

```
$ make refs
wrote 85 outputs + trace_sip.trace + trace_sip.msd + index.html under samples/reference
$ git status --porcelain samples/reference   # (drift check)
$ make shots
docs/images/fred_annot-table-archtable.png: 58787 bytes (clip 1004x538)
... 8 shots, exit 0
$ make syntax
syntax: 96 accepted, 10 empty skipped
$ python3 tools/run-tests.py
test: pass 963 / fail 0
```

Done: samples/reference is complete and drift-free, docs/images shows the
table styles and html layouts as non-blank pictures, the README carries
the Sample output section with them, and Appendix B records the errata
including this port's fixes over the JS port's slips.
