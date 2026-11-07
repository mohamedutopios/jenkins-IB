// Etape 2 (demo 2) : outils, build Maven, rapports de tests et de couverture, archivage
pipeline {
  agent {
    label 'devsecops'
  }
  tools {
    jdk 'jdk21'
    maven 'maven-3.9'
  }
  stages {
    stage('Checkout') {
      steps {
        git branch: 'main', credentialsId: 'gitea-token', url: 'http://gitea:3000/formation/library-api-devsecops.git'
      }
    }
    stage('Build & tests') {
      steps {
        sh 'mvn -B -ntp clean verify'
      }
      post {
        always {
          junit 'target/surefire-reports/*.xml, target/failsafe-reports/*.xml'
          recordCoverage qualityGates: [[integerThreshold: 80, metric: 'LINE', threshold: 80.0]], tools: [[pattern: 'target/site/jacoco/jacoco.xml']]
        }
        success {
          archiveArtifacts artifacts: 'target/*.jar', fingerprint: true
        }
      }
    }
  }
}
