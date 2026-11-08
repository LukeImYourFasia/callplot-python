# Appendix B. Spec errata and known differences

Each row: date, section, what the spec said, what the original tool (or a
port) does, and the fixture that covers it.

| Date | Section | Spec said | Original tool / this port does | Fixture |
|------|---------|-----------|--------------------------------|---------|
| 2026-11-05 | 1.3 | — | The 2002 jar's diagram has 1 fewer bar line at the top than the 0.2 core. The goldens use the 0.2 core. | — (the DRM archive sample is not in this repo's corpus) |
| 2026-11-05 | 3.14.4 | — | `prep.awk` appends its debug lines to a file literally named `debug` in the current folder. This port returns them and the CLI writes them only where `--debug-file` pointed. (Deliberate.) | `prep_stdin` |
| 2026-11-05 | 3.13.4 | — | Xalan exits 255 on bad annotation text (a raw `<` or `&`). This port exits 1. (Deliberate.) | `tbl_raw_lt`, `tbl_bare_amp` |
| 2026-11-05 | 3.7 | — | A crashing java run can leak up to 8 KB of buffered stdout: `java -cp` PrintWriter over a BufferedWriter flushes whole 8192-byte buffer loads as it dies. The golden harness rule AND both ports keep exactly those whole loads for a crashed file; the CLI here models it too, so the exit-1 cases pin the same bytes the JVM wrote. (Accepted.) | `long_label_crash` |
| 2026-11-08 | 3.7 | "a stack trace or a clear error, exit 1" | A JVM throw dumps a stack trace. This port prints one line `callplot: <ErrorType>: <message>` on stderr and exits 1; unreadable files print `callplot: Error: <os message>`. The tests never compare stderr, per section 4.4. (Port choice, mirrors the JS port.) | every error CLI case |
| 2026-11-08 | 3.7 | "graffle ``--`` debug lines go to stderr (System.err)" | The JS CLI never flushed the RunContext's `ctx.err` buffer: its graffle debug lines went nowhere. This port flushes what is new in `ctx.err` to stderr after each file, as the spec says. (The JS port's slip, corrected here; no test compares stderr.) | `multi_graffle_ids` |
| 2026-11-08 | 3.7 | — | A closed pipe: `python3 ... \| head -1` gets SIGPIPE -> CPython may die noisily. Both ports catch the write's EPIPE and exit 0 with empty stderr, matching the JS port's epipe case. | `epipe` |

Notes for the table above:

- The usage text is kept verbatim from `Main.java:79-159` - wrong defaults,
  stray tabs, all of it (DESIGN 3.7), then one block listing the new flags.
  `plottable`'s usage goes to STDOUT because the 2008 script echoed it there;
  that is pinned by `test/cli/plottable_usage.expected`, not by any spec prose.
- `plottable -debug` writes `_x_<pid>.xml` in the current folder - the script
  used the shell's `$$`, this port uses the process pid. Same side-output role
  (DESIGN 3.13.5, Appendix A question 6: kept for compatibility).
