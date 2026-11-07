package fr.utopios.library;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class InMemoryBookRepositoryTest {

    InMemoryBookRepository repository = new InMemoryBookRepository();

    @Test
    void shouldStartWithThreeBooksSortedById() {
        assertThat(repository.findAll())
                .extracting(Book::id)
                .containsExactly(1L, 2L, 3L);
    }

    @Test
    void shouldReplaceABookOnSave() {
        repository.save(new Book(2L, "Clean Code", 5));

        assertThat(repository.findById(2L)).get()
                .extracting(Book::copies).isEqualTo(5);
    }

    @Test
    void shouldReturnEmptyForUnknownId() {
        assertThat(repository.findById(404L)).isEmpty();
    }
}
