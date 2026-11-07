package fr.utopios.portal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class LoanServiceBeanTest {

    LoanServiceBean service = new LoanServiceBean();

    @Test
    void shouldDelegateToLibraryCore() {
        assertTrue(service.canBorrow(1, 2));
        assertEquals(60, service.lateFeeCents(3));
    }
}
