package fr.utopios.legacy;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class IsbnValidatorTest {

    @Test
    public void shouldAcceptValidIsbn() {
        assertTrue(IsbnValidator.isValid("978-0-321-12521-7"));
    }

    @Test
    public void shouldRejectWrongCheckDigit() {
        assertFalse(IsbnValidator.isValid("978-0-321-12521-8"));
    }

    @Test
    public void shouldRejectShortValue() {
        assertFalse(IsbnValidator.isValid("12345"));
    }
}
