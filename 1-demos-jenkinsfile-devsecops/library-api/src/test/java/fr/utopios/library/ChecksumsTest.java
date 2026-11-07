package fr.utopios.library;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;

import org.junit.jupiter.api.Test;

class ChecksumsTest {

    @Test
    void sameBookGivesSameEtag() {
        assertEquals(Checksums.etag(new Book(1L, "Clean Code", 2)), Checksums.etag(new Book(1L, "Clean Code", 2)));
    }

    @Test
    void etagChangesWithCopies() {
        assertNotEquals(Checksums.etag(new Book(1L, "Clean Code", 2)), Checksums.etag(new Book(1L, "Clean Code", 1)));
    }
}
