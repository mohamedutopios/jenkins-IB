package fr.utopios.inventaire;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Service;

@Service
public class StockService {

    private final Map<String, Article> articles = new ConcurrentHashMap<>();

    public List<Article> lister() {
        return new ArrayList<>(articles.values());
    }

    public Article trouver(String sku) {
        Article article = articles.get(sku);
        if (article == null) {
            throw new ArticleInconnuException(sku);
        }
        return article;
    }

    public Article referencer(String sku, String libelle) {
        if (sku == null || sku.isBlank()) {
            throw new IllegalArgumentException("Le SKU est obligatoire");
        }
        Article article = new Article(sku, libelle, 0);
        articles.put(sku, article);
        return article;
    }

    public Article entrer(String sku, int quantite) {
        if (quantite <= 0) {
            throw new IllegalArgumentException("La quantite doit etre positive");
        }
        Article article = trouver(sku);
        Article maj = article.avecQuantite(article.quantite() + quantite);
        articles.put(sku, maj);
        return maj;
    }

    public Article sortir(String sku, int quantite) {
        if (quantite <= 0) {
            throw new IllegalArgumentException("La quantite doit etre positive");
        }
        Article article = trouver(sku);
        if (article.quantite() < quantite) {
            throw new StockInsuffisantException(sku, quantite, article.quantite());
        }
        Article maj = article.avecQuantite(article.quantite() - quantite);
        articles.put(sku, maj);
        return maj;
    }

    public int valeurTotale() {
        int total = 0;
        for (Article article : articles.values()) {
            total = total + article.quantite();
        }
        return total;
    }
}
