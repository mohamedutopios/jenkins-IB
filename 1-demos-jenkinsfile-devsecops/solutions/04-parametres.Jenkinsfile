// Etape 4 (demo 4) : parametres du build
pipeline {
  agent {
    label 'devsecops'
  }
  tools {
    jdk 'jdk21'
    maven 'maven-3.9'
  }
  options {
    buildDiscarder logRotator(numToKeepStr: '20')
    disableConcurrentBuilds()
    timeout(20)
    timestamps()
  }
  parameters {
    string(name: 'VERSION_BASE', defaultValue: '1.4', description: 'Version majeure.mineure ; le numero de build complete la version')
    choice(name: 'SEUIL_BLOQUANT', choices: ['CRITICAL', 'HIGH,CRITICAL'], description: 'Severites de vulnerabilite qui bloquent le pipeline')
    booleanParam(name: 'ANALYSE_SONAR', defaultValue: true, description: 'Lancer l analyse SonarQube')
  }
  environment {
    APP_VERSION = "${params.VERSION_BASE}.${BUILD_NUMBER}"
  }
  triggers {
    pollSCM('H/5 * * * *')
  }
  stages {
    stage('Checkout') {
      steps {
        git branch: 'main', credentialsId: 'gitea-token', url: 'http://gitea:3000/formation/library-api-devsecops.git'
      }
    }
    stage('Contexte') {
      steps {
        echo "Version : ${env.APP_VERSION} - seuil bloquant : ${params.SEUIL_BLOQUANT} - SonarQube : ${params.ANALYSE_SONAR}"
        sh 'echo "Variable shell : VERSION_BASE=$VERSION_BASE"'
      }
    }
    stage('Build & tests') {
      steps {
        sh 'mvn -B -ntp -Drevision=$APP_VERSION clean verify'
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
