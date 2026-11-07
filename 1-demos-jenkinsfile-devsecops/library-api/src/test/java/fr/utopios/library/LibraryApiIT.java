package fr.utopios.library;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;

/** Test d'integration : demarre l'application complete (Failsafe, phase verify). */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class LibraryApiIT {

    @Autowired
    TestRestTemplate rest;

    @Test
    void healthShouldBeUp() {
        String body = rest.getForObject("/actuator/health", String.class);
        assertThat(body).contains("UP");
    }

    @Test
    void shouldLoanABook() {
        Book book = rest.postForObject("/api/books/1/loan?member=alice", null, Book.class);
        assertThat(book.copies()).isEqualTo(2);
    }
}
