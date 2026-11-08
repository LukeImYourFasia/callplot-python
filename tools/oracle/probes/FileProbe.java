import java.nio.file.Files;
import java.nio.file.Paths;

public class FileProbe {
    public static void main(String[] args) throws Exception {
        byte[] data = Files.readAllBytes(Paths.get(args[args.length - 1]));
        System.out.write(data);
        System.out.flush();
    }
}
