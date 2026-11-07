// Mise en forme du catalogue affiche par le front
export function formatBook(book) {
  const dispo = book.copies > 0 ? `${book.copies} exemplaire(s)` : 'indisponible';
  return `${book.title} - ${dispo}`;
}

export function availableOnly(books) {
  return books.filter((b) => b.copies > 0);
}
