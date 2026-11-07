package fr.utopios.library.core;

/** Regles d'emprunt partagees par library-api et library-portal. */
public final class LoanRules {

    /** Nombre maximal d'emprunts simultanes par adherent. */
    public static final int MAX_LOANS = 5;

    /** Duree d'un emprunt, en jours. */
    public static final int LOAN_DAYS = 21;

    private LoanRules() {
    }

    public static boolean canBorrow(int currentLoans, int availableCopies) {
        return currentLoans < MAX_LOANS && availableCopies > 0;
    }

    public static int lateFeeCents(int daysLate) {
        return daysLate <= 0 ? 0 : daysLate * 20;
    }
}
