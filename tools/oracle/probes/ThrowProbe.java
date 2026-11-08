public class ThrowProbe {
    public static void main(String[] args) {
        System.out.print("a");
        System.out.flush();
        throw new RuntimeException("boom");
    }
}
