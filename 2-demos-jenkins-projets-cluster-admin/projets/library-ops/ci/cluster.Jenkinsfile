// Repartition entre agents : un stage par agent, en parallele (slides 33 et 34)
pipeline {
  agent none
  options { timestamps() }
  stages {
    stage('Plates-formes') {
      parallel {
        stage('linux-1 (SSH)') {
          agent { label 'linux-1' }
          steps { sh 'echo "node=$NODE_NAME labels=$NODE_LABELS"; hostname; whoami; pwd' }
        }
        stage('linux-2 (inbound)') {
          agent { label 'linux-2' }
          steps { sh 'echo "node=$NODE_NAME labels=$NODE_LABELS"; hostname; whoami; pwd' }
        }
        stage('Docker (ephemere)') {
          agent { label 'docker-maven' }
          steps { sh 'echo "node=$NODE_NAME labels=$NODE_LABELS"; hostname; mvn -v | head -1' }
        }
      }
    }
  }
}
