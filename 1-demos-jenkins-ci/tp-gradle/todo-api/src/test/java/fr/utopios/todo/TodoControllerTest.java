package fr.utopios.todo;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
class TodoControllerTest {

    @Autowired
    private MockMvc mvc;

    @Test
    void createThenReadTodo() throws Exception {
        mvc.perform(post("/api/todos")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"title\":\"Publier dans Gitea\"}"))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.title").value("Publier dans Gitea"));

        mvc.perform(get("/api/todos"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].done").value(false));
    }

    @Test
    void unknownTodoReturns404() throws Exception {
        mvc.perform(get("/api/todos/999"))
            .andExpect(status().isNotFound());
    }
}
