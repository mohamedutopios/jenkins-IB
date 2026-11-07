package fr.utopios.legacy;

/** Validation d'ISBN-13 heritee de l'ancien systeme de catalogue. */
public final class IsbnValidator {

    private IsbnValidator() {
    }

    public static boolean isValid(String isbn) {
        if (isbn == null) {
            return false;
        }
        String digits = isbn.replace("-", "");
        if (digits.length() != 13 || !digits.chars().allMatch(Character::isDigit)) {
            return false;
        }
        int sum = 0;
        for (int i = 0; i < 12; i++) {
            int d = digits.charAt(i) - '0';
            sum += (i % 2 == 0) ? d : d * 3;
        }
        int check = (10 - sum % 10) % 10;
        return check == digits.charAt(12) - '0';
    }
}
