package fr.utopios.inventaire;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

// Test d'integration : l'application demarre sur un port aleatoire (lance par Failsafe)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class StockApiIT {

    @Autowired
    private TestRestTemplate http;

    @Test
    void referencerPuisEntrerEnStock() {
        ResponseEntity<Article> cree = http.postForEntity("/api/articles",
            Map.of("sku", "ECRAN-27", "libelle", "Ecran 27 pouces"), Article.class);
        assertThat(cree.getStatusCode()).isEqualTo(HttpStatus.CREATED);

        ResponseEntity<Article> entree = http.postForEntity("/api/articles/ECRAN-27/entrees?quantite=4",
            null, Article.class);
        assertThat(entree.getBody().quantite()).isEqualTo(4);
    }

    @Test
    void laSanteDeLApplicationEstUp() {
        ResponseEntity<String> sante = http.getForEntity("/actuator/health", String.class);

        assertThat(sante.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(sante.getBody()).contains("UP");
    }
}
