package fr.utopios.library;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(BookController.class)
class BookControllerTest {

    @Autowired
    MockMvc mvc;

    @MockitoBean
    BookService service;

    @Test
    void shouldListBooks() throws Exception {
        when(service.findAll()).thenReturn(List.of(new Book(1L, "DDD", 3)));

        mvc.perform(get("/api/books"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].title").value("DDD"));
    }

    @Test
    void shouldAnswerConflictWhenNoCopyLeft() throws Exception {
        when(service.loan(2L, "bob")).thenThrow(new NoCopyAvailableException(2L));

        mvc.perform(post("/api/books/2/loan").param("member", "bob"))
                .andExpect(status().isConflict());
    }
}
