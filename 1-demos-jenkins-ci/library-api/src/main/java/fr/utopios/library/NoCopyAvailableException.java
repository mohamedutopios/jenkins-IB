package fr.utopios.library;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(HttpStatus.CONFLICT)
public class NoCopyAvailableException extends RuntimeException {

    public NoCopyAvailableException(Long id) {
        super("Aucun exemplaire disponible pour le livre " + id);
    }
}
