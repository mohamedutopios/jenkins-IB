package fr.utopios.todo;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

// Corrige de l'exercice 6 : a copier dans src/test/java/fr/utopios/todo/
@SpringBootTest
@AutoConfigureMockMvc
class TodoLifecycleTest {

    @Autowired
    private MockMvc mvc;

    @Test
    void createCompleteThenDeleteTodo() throws Exception {
        String location = mvc.perform(post("/api/todos")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"title\":\"Atteindre 80 % de couverture\"}"))
            .andExpect(status().isCreated())
            .andReturn().getResponse().getContentAsString();
        long id = Long.parseLong(location.replaceAll(".*\"id\":(\\d+).*", "$1"));

        mvc.perform(get("/api/todos/" + id))
            .andExpect(status().isOk());

        mvc.perform(put("/api/todos/" + id + "/done"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.done").value(true));

        mvc.perform(delete("/api/todos/" + id))
            .andExpect(status().isNoContent());

        mvc.perform(delete("/api/todos/" + id))
            .andExpect(status().isNotFound());
    }
}
