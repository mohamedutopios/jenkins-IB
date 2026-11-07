package fr.utopios.library;

/** Un livre du catalogue et son nombre d'exemplaires disponibles. */
public record Book(Long id, String title, int copies) {

    public Book withCopies(int newCopies) {
        return new Book(id, title, newCopies);
    }
}
