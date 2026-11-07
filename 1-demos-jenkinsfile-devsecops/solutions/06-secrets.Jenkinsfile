// Etape 6 (demo 6) : recherche de secrets dans l'historique Git (Gitleaks)
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
    stage('Contexte') {
      steps {
        echo "Version : ${env.APP_VERSION} - seuil bloquant : ${params.SEUIL_BLOQUANT} - SonarQube : ${params.ANALYSE_SONAR}"
      }
    }
    stage('Secrets (Gitleaks)') {
      steps {
        sh 'gitleaks git --no-banner --no-color --redact --verbose --report-format sarif --report-path gitleaks.sarif'
      }
      post {
        always {
          recordIssues enabledForFailure: true, sourceCodeRetention: 'NEVER', tools: [sarif(id: 'gitleaks', name: 'Gitleaks', pattern: 'gitleaks.sarif')]
        }
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
