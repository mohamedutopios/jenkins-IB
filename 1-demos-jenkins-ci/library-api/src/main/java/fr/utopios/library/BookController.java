package fr.utopios.library;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/books")
public class BookController {

    private final BookService service;

    public BookController(BookService service) {
        this.service = service;
    }

    @GetMapping
    public List<Book> findAll() {
        return service.findAll();
    }

    @GetMapping("/{id}")
    public Book findById(@PathVariable Long id) {
        return service.findById(id);
    }

    @PostMapping("/{id}/loan")
    public Book loan(@PathVariable Long id, @RequestParam String member) {
        return service.loan(id, member);
    }

    @PostMapping("/{id}/return")
    public Book giveBack(@PathVariable Long id) {
        return service.giveBack(id);
    }
}
