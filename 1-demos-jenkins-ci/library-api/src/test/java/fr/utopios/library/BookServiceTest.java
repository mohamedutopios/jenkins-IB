package fr.utopios.library;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class BookServiceTest {

    @Mock
    BookRepository repository;

    @InjectMocks
    BookService service;

    @Test
    void shouldRejectLoanWhenNoCopyAvailable() {
        when(repository.findById(42L))
                .thenReturn(Optional.of(new Book(42L, "Clean Code", 0)));

        assertThrows(NoCopyAvailableException.class,
                () -> service.loan(42L, "mohamed"));
    }

    @Test
    void shouldDecrementCopiesOnLoan() {
        when(repository.findById(1L))
                .thenReturn(Optional.of(new Book(1L, "DDD", 3)));
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        service.loan(1L, "alice");

        verify(repository).save(argThat(b -> b.copies() == 2));
    }

    @Test
    void shouldRejectUnknownBook() {
        when(repository.findById(99L)).thenReturn(Optional.empty());

        assertThrows(BookNotFoundException.class, () -> service.findById(99L));
    }

    @Test
    void shouldIncrementCopiesOnReturn() {
        when(repository.findById(2L))
                .thenReturn(Optional.of(new Book(2L, "Clean Code", 1)));
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        Book returned = service.giveBack(2L);

        assertEquals(2, returned.copies());
    }
}
