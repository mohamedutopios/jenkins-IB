package fr.utopios.inventaire;

public record Article(String sku, String libelle, int quantite) {

    public Article avecQuantite(int nouvelleQuantite) {
        return new Article(sku, libelle, nouvelleQuantite);
    }
}
