package fr.utopios.inventaire;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class StockServiceTest {

    private StockService service;

    @BeforeEach
    void preparer() {
        service = new StockService();
        service.referencer("CLAV-01", "Clavier");
    }

    @Test
    void unArticleReferenceEstVide() {
        assertThat(service.trouver("CLAV-01").quantite()).isZero();
    }

    @Test
    void uneEntreeAugmenteLeStock() {
        service.entrer("CLAV-01", 5);

        assertThat(service.trouver("CLAV-01").quantite()).isEqualTo(5);
    }

    @Test
    void uneSortieDiminueLeStock() {
        service.entrer("CLAV-01", 5);
        service.sortir("CLAV-01", 2);

        assertThat(service.trouver("CLAV-01").quantite()).isEqualTo(3);
    }

    @Test
    void uneSortieSuperieureAuStockEstRefusee() {
        service.entrer("CLAV-01", 1);

        assertThatThrownBy(() -> service.sortir("CLAV-01", 2))
            .isInstanceOf(StockInsuffisantException.class);
    }

    @Test
    void unArticleInconnuEstSignale() {
        assertThatThrownBy(() -> service.trouver("INCONNU"))
            .isInstanceOf(ArticleInconnuException.class);
    }
}
