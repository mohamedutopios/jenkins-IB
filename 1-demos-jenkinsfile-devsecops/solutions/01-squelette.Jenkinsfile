// Etape 1 (demo 1) : squelette genere avec les deux generateurs
pipeline {
  agent {
    label 'devsecops'
  }
  stages {
    stage('Checkout') {
      steps {
        git branch: 'main', credentialsId: 'gitea-token', url: 'http://gitea:3000/formation/library-api-devsecops.git'
        sh 'ls -la'
      }
    }
  }
}
