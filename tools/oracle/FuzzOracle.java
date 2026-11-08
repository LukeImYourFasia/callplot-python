import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.security.Permission;

/**
 * Fuzz oracle harness. See DESIGN.md section 4.5.1.
 *
 * Usage: java -cp reference/build-tools FuzzOracle <classDir> <mainClass>
 *
 * Request:  "CASE <id> <modeFlag> <n>\n" then n bytes of input.
 * Response: "RESULT <id> <exitCode> <m>\n" then m bytes of stdout.
 *
 * Each case runs in a new class loader, so static fields start fresh, as in a new JVM.
 * Java 8 only: it needs a SecurityManager to catch System.exit.
 */
public class FuzzOracle {

    /** Thrown by checkExit when the code under test calls System.exit. */
    private static final class ExitTrap extends SecurityException {
        final int status;

        ExitTrap(int status) {
            super("System.exit(" + status + ")");
            this.status = status;
        }
    }

    /** True only when the harness itself exits. Then checkExit lets the exit through. */
    private static volatile boolean harnessExit = false;

    private static PrintStream realErr;

    public static void main(String[] args) throws Exception {
        realErr = System.err;
        if (args.length != 2) {
            realErr.println("usage: FuzzOracle <classDir> <mainClass>");
            System.exit(2);
        }
        File dir = new File(args[0]).getAbsoluteFile();
        if (!dir.isDirectory()) {
            realErr.println("FuzzOracle: not a folder: " + dir);
            System.exit(2);
        }
        // toURI() adds the trailing "/". Without it, the loader reads the folder as a jar.
        URL url = dir.toURI().toURL();
        String mainClass = args[1];

        DataInputStream in = new DataInputStream(new BufferedInputStream(System.in));
        OutputStream out = new BufferedOutputStream(new FileOutputStream(FileDescriptor.out));
        PrintStream realOut = System.out;
        PrintStream dropErr = new PrintStream(new OutputStream() {
            @Override
            public void write(int b) {
            }

            @Override
            public void write(byte[] b, int off, int len) {
            }
        });
        File tmp = File.createTempFile("fuzzoracle", ".in");
        tmp.deleteOnExit();

        // Allow everything except System.exit from the code under test.
        System.setSecurityManager(new SecurityManager() {
            @Override
            public void checkPermission(Permission p) {
            }

            @Override
            public void checkPermission(Permission p, Object context) {
            }

            @Override
            public void checkExit(int status) {
                if (!harnessExit) {
                    throw new ExitTrap(status);
                }
            }
        });

        while (true) {
            String header = readHeader(in);
            if (header == null) {
                break;
            }
            String[] f = header.split(" ");
            if (f.length != 4 || !f[0].equals("CASE")) {
                fail("bad request header: " + header);
            }
            String id = f[1];
            String mode = f[2];
            int n = Integer.parseInt(f[3]);
            byte[] input = new byte[n];
            in.readFully(input);

            FileOutputStream fo = new FileOutputStream(tmp);
            fo.write(input);
            fo.close();
            String[] caseArgs = mode.equals("text")
                    ? new String[] { tmp.getPath() }
                    : new String[] { mode, tmp.getPath() };

            URLClassLoader loader = new URLClassLoader(new URL[] { url }, null);
            Method m = null;
            try {
                m = loader.loadClass(mainClass).getMethod("main", String[].class);
            } catch (ReflectiveOperationException e) {
                fail("cannot load " + mainClass + " from " + url + ": " + e);
            }

            ByteArrayOutputStream buf = new ByteArrayOutputStream();
            int code = 0;
            System.setOut(new PrintStream(buf, true));
            System.setErr(dropErr);
            try {
                m.invoke(null, (Object) caseArgs);
            } catch (InvocationTargetException e) {
                code = exitCodeOf(e.getCause());
            } catch (IllegalAccessException e) {
                code = -1;
            } finally {
                System.out.flush();
                System.setOut(realOut);
                System.setErr(realErr);
                loader.close();
            }
            if (code == -1) {
                fail("cannot call " + mainClass + ".main");
            }

            byte[] result = buf.toByteArray();
            String head = "RESULT " + id + " " + code + " " + result.length + "\n";
            out.write(head.getBytes(StandardCharsets.US_ASCII));
            out.write(result);
            out.flush();
        }
        tmp.delete();
        harnessExit = true;
        System.exit(0);
    }

    /** An ExitTrap anywhere in the cause chain gives its status. Any other throwable gives 1. */
    private static int exitCodeOf(Throwable t) {
        for (Throwable c = t; c != null; c = c.getCause()) {
            if (c instanceof ExitTrap) {
                return ((ExitTrap) c).status;
            }
        }
        return 1;
    }

    /** Reads one header line as bytes, up to "\n". Returns null at end of input. */
    private static String readHeader(DataInputStream in) throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream();
        while (true) {
            int b = in.read();
            if (b == -1) {
                if (line.size() == 0) {
                    return null;
                }
                fail("input ended inside a header");
            }
            if (b == '\n') {
                return new String(line.toByteArray(), StandardCharsets.US_ASCII);
            }
            if (line.size() > 1024) {
                fail("header longer than 1024 bytes");
            }
            line.write(b);
        }
    }

    /** A harness bug, not a result of the code under test. Log it and stop with exit code 3. */
    private static void fail(String message) {
        realErr.println("FuzzOracle: " + message);
        realErr.flush();
        harnessExit = true;
        System.exit(3);
    }
}
