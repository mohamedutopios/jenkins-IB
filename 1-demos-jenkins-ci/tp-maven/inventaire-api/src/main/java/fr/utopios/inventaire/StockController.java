package fr.utopios.inventaire;

import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/articles")
public class StockController {

    private final StockService service;

    public StockController(StockService service) {
        this.service = service;
    }

    @GetMapping
    public List<Article> lister() {
        return service.lister();
    }

    @GetMapping("/{sku}")
    public Article trouver(@PathVariable String sku) {
        return service.trouver(sku);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Article referencer(@RequestBody Map<String, String> corps) {
        return service.referencer(corps.get("sku"), corps.get("libelle"));
    }

    @PostMapping("/{sku}/entrees")
    public Article entrer(@PathVariable String sku, @RequestParam int quantite) {
        return service.entrer(sku, quantite);
    }

    @PostMapping("/{sku}/sorties")
    public Article sortir(@PathVariable String sku, @RequestParam int quantite) {
        return service.sortir(sku, quantite);
    }
}
