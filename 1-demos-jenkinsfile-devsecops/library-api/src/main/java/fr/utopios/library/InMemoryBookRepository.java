package fr.utopios.library;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Repository;

/** Stockage en memoire : suffisant pour la formation, pas de base de donnees a demarrer. */
@Repository
public class InMemoryBookRepository implements BookRepository {

    private final Map<Long, Book> books = new ConcurrentHashMap<>();

    public InMemoryBookRepository() {
        save(new Book(1L, "Domain-Driven Design", 3));
        save(new Book(2L, "Clean Code", 1));
        save(new Book(3L, "Continuous Delivery", 2));
    }

    @Override
    public List<Book> findAll() {
        return books.values().stream().sorted((a, b) -> a.id().compareTo(b.id())).toList();
    }

    @Override
    public Optional<Book> findById(Long id) {
        return Optional.ofNullable(books.get(id));
    }

    @Override
    public Book save(Book book) {
        books.put(book.id(), book);
        return book;
    }
}
