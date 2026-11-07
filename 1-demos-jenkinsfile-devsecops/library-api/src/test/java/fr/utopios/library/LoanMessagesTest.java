package fr.utopios.library;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class LoanMessagesTest {

    @Test
    void shouldFillMemberAndTitle() {
        String message = LoanMessages.loanConfirmation(new Book(1L, "Clean Code", 2), "alice");
        assertEquals("Bonjour alice, vous avez emprunte \"Clean Code\".", message);
    }
}
