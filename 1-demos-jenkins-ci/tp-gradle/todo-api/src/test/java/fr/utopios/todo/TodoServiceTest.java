package fr.utopios.todo;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class TodoServiceTest {

    private final TodoService service = new TodoService();

    @Test
    void createAddsAnOpenTodo() {
        Todo todo = service.create("  Ecrire le Jenkinsfile ");

        assertThat(todo.title()).isEqualTo("Ecrire le Jenkinsfile");
        assertThat(todo.done()).isFalse();
        assertThat(service.findAll()).hasSize(1);
    }

    @Test
    void createRejectsBlankTitle() {
        assertThatThrownBy(() -> service.create(" "))
            .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void completeMarksTodoAsDone() {
        Todo todo = service.create("Configurer Mattermost");

        assertThat(service.complete(todo.id()).done()).isTrue();
        assertThat(service.remaining()).isZero();
    }

    @Test
    void findByIdFailsForUnknownId() {
        assertThatThrownBy(() -> service.findById(42))
            .isInstanceOf(TodoNotFoundException.class);
    }
}
