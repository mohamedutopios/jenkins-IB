package fr.utopios.todo;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.springframework.stereotype.Service;

@Service
public class TodoService {

    private final Map<Long, Todo> todos = new ConcurrentHashMap<>();
    private final AtomicLong sequence = new AtomicLong();

    public List<Todo> findAll() {
        return new ArrayList<>(todos.values());
    }

    public Todo findById(long id) {
        Todo todo = todos.get(id);
        if (todo == null) {
            throw new TodoNotFoundException(id);
        }
        return todo;
    }

    public Todo create(String title) {
        if (title == null || title.isBlank()) {
            throw new IllegalArgumentException("Le titre est obligatoire");
        }
        long id = sequence.incrementAndGet();
        Todo todo = new Todo(id, title.trim(), false);
        todos.put(id, todo);
        return todo;
    }

    public Todo complete(long id) {
        Todo done = findById(id).markDone();
        todos.put(id, done);
        return done;
    }

    public void delete(long id) {
        if (todos.remove(id) == null) {
            throw new TodoNotFoundException(id);
        }
    }

    public long remaining() {
        return todos.values().stream().filter(t -> !t.done()).count();
    }
}
