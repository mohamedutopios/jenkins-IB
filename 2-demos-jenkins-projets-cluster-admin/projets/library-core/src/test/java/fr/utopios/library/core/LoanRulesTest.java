package fr.utopios.library.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class LoanRulesTest {

    @Test
    void shouldAllowLoanUnderTheLimit() {
        assertTrue(LoanRules.canBorrow(2, 1));
    }

    @Test
    void shouldRefuseLoanAtTheLimit() {
        assertFalse(LoanRules.canBorrow(LoanRules.MAX_LOANS, 3));
    }

    @Test
    void shouldRefuseLoanWithoutCopy() {
        assertFalse(LoanRules.canBorrow(0, 0));
    }

    @Test
    void shouldChargeTwentyCentsPerLateDay() {
        assertEquals(0, LoanRules.lateFeeCents(0));
        assertEquals(140, LoanRules.lateFeeCents(7));
    }
}
