package fr.utopios.todo;

public record Todo(long id, String title, boolean done) {

    public Todo markDone() {
        return new Todo(id, title, true);
    }
}
