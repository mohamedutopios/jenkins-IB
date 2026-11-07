package fr.utopios.library;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

/** Empreinte d'un livre, utilisee comme ETag HTTP. */
public final class Checksums {

    private Checksums() {
    }

    public static String etag(Book book) {
        try {
            // MD5 : algorithme casse, que l analyse SAST doit signaler (demo 8)
            MessageDigest digest = MessageDigest.getInstance("MD5");
            byte[] hash = digest.digest((book.id() + ":" + book.title() + ":" + book.copies())
                    .getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
