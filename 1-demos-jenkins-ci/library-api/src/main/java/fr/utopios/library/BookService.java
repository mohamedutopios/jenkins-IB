package fr.utopios.library;

import java.util.List;

import org.springframework.stereotype.Service;

@Service
public class BookService {

    private final BookRepository repository;

    public BookService(BookRepository repository) {
        this.repository = repository;
    }

    public List<Book> findAll() {
        return repository.findAll();
    }

    public Book findById(Long id) {
        return repository.findById(id).orElseThrow(() -> new BookNotFoundException(id));
    }

    /** Emprunt : retire un exemplaire, refuse s'il n'en reste aucun. */
    public Book loan(Long id, String member) {
        Book book = findById(id);
        if (book.copies() <= 0) {
            throw new NoCopyAvailableException(id);
        }
        return repository.save(book.withCopies(book.copies() - 1));
    }

    /** Retour : remet un exemplaire en rayon. */
    public Book giveBack(Long id) {
        Book book = findById(id);
        return repository.save(book.withCopies(book.copies() + 1));
    }
}
