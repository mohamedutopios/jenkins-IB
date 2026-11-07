// Script de demarrage (slide 55) : execute a chaque demarrage du controller, donc idempotent.
import jenkins.model.Jenkins

def j = Jenkins.get()
def message = 'Jenkins de formation - demos library (partie 2) - configure par init.groovy.d'
if (j.systemMessage != message) {
  j.systemMessage = message
  j.save()
  println '[init] message systeme mis a jour'
} else {
  println '[init] message systeme deja en place'
}
