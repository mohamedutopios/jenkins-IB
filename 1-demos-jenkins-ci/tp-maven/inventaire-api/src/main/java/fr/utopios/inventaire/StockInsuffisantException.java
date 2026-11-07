package fr.utopios.inventaire;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(HttpStatus.CONFLICT)
public class StockInsuffisantException extends RuntimeException {

    public StockInsuffisantException(String sku, int demande, int disponible) {
        super("Stock insuffisant pour " + sku + " : " + demande + " demandes, " + disponible + " disponibles");
    }
}
