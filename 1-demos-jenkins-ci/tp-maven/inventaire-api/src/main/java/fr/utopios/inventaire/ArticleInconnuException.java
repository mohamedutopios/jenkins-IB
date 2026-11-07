package fr.utopios.inventaire;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(HttpStatus.NOT_FOUND)
public class ArticleInconnuException extends RuntimeException {

    public ArticleInconnuException(String sku) {
        super("Article inconnu : " + sku);
    }
}
