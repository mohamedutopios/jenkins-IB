package fr.utopios.portal;

import fr.utopios.library.core.LoanRules;
import jakarta.ejb.Stateless;

/** Service metier du portail : delegue les regles a library-core. */
@Stateless
public class LoanServiceBean {

    public boolean canBorrow(int currentLoans, int availableCopies) {
        return LoanRules.canBorrow(currentLoans, availableCopies);
    }

    public int lateFeeCents(int daysLate) {
        return LoanRules.lateFeeCents(daysLate);
    }
}
