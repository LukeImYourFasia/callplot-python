# tools/oracle (DESIGN.md sections 4.5.1 and 4.5.2)

Edgar provides these files. Do not write, edit, or regenerate them.

- `FuzzOracle.java`: the long-lived Java 8 harness.
- `probes/*.java`: 6 probe classes that test the harness.

Build:

    javac -nowarn -d reference/build-tools tools/oracle/FuzzOracle.java
    javac -d reference/build-probes tools/oracle/probes/*.java

Run against callplot:

    JAVA_TOOL_OPTIONS=-Dfile.encoding=UTF-8 java -cp reference/build-tools FuzzOracle reference/build com.dynamicsoft.callplot.Main

Harness exit codes: 0 = stdin closed, 2 = bad arguments, 3 = harness error (message on stderr).

Verified on OpenJDK 1.8.0_504 on 2026-11-07: all probe checks pass, and 2,121 runs
(fred, fred2, fred_annot and 300 random inputs, 7 modes each) match one-JVM-per-run Java with 0 differences.
