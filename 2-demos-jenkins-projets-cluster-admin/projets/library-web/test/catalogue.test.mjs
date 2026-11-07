import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatBook, availableOnly } from '../src/catalogue.mjs';

test('affiche le nombre d exemplaires', () => {
  assert.equal(formatBook({ title: 'DDD', copies: 3 }), 'DDD - 3 exemplaire(s)');
});

test('signale un livre indisponible', () => {
  assert.equal(formatBook({ title: 'Clean Code', copies: 0 }), 'Clean Code - indisponible');
});

test('filtre les livres disponibles', () => {
  const books = [{ title: 'A', copies: 1 }, { title: 'B', copies: 0 }];
  assert.deepEqual(availableOnly(books).map((b) => b.title), ['A']);
});
