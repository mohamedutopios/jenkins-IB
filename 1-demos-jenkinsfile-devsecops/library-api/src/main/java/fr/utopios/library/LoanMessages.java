package fr.utopios.library;

import java.util.Map;

import org.apache.commons.text.StringSubstitutor;

/** Messages envoyes aux adherents, construits a partir de gabarits. */
public final class LoanMessages {

    private static final String LOAN_TEMPLATE = "Bonjour ${member}, vous avez emprunte \"${title}\".";

    private LoanMessages() {
    }

    public static String loanConfirmation(Book book, String member) {
        return StringSubstitutor.replace(LOAN_TEMPLATE, Map.of("member", member, "title", book.title()));
    }
}
