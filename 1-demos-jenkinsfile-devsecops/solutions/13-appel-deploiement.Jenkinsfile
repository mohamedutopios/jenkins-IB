// Etape 13 (demo 13) : le pipeline appelle le pipeline de deploiement library-api-deploy
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
    booleanParam(name: 'DEPLOYER_RECETTE', defaultValue: true, description: 'Deployer l image en recette (branche main seulement)')
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
    stage('Analyses') {
      parallel {
        stage('Dependances (Trivy)') {
          steps {
            // Rapport complet (toutes severites) pour Jenkins, puis controle bloquant sur le seuil choisi
            sh 'trivy fs --scanners vuln --offline-scan --no-progress --format json --output trivy-fs.json pom.xml'
            sh "trivy fs --scanners vuln --offline-scan --no-progress --severity ${params.SEUIL_BLOQUANT} --exit-code 1 pom.xml"
          }
          post {
            always {
              recordIssues enabledForFailure: true, sourceCodeRetention: 'LAST_BUILD', tools: [trivy(id: 'trivy-fs', name: 'Trivy - dependances', pattern: 'trivy-fs.json')]
            }
          }
        }
        stage('SAST (Semgrep)') {
          steps {
            // Un constat de SAST n'est pas forcement une faille : le build passe UNSTABLE, il n'echoue pas
            catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
              sh 'semgrep scan --config p/java --metrics=off --error --sarif --output semgrep.sarif --exclude target .'
            }
          }
          post {
            always {
              recordIssues enabledForFailure: true, sourceCodeRetention: 'LAST_BUILD', tools: [sarif(id: 'semgrep', name: 'Semgrep', pattern: 'semgrep.sarif')]
            }
          }
        }
        stage('Dockerfile (Hadolint)') {
          when {
            anyOf {
              branch 'main'
              changeset 'Dockerfile'
            }
          }
          steps {
            sh 'hadolint --format json --failure-threshold error Dockerfile > hadolint.json'
          }
          post {
            always {
              recordIssues enabledForFailure: true, sourceCodeRetention: 'LAST_BUILD', tools: [hadoLint(pattern: 'hadolint.json')]
            }
          }
        }
        stage('Qualite (SonarQube)') {
          when {
            expression { params.ANALYSE_SONAR }
          }
          steps {
            withSonarQubeEnv('sonarqube') {
              sh 'mvn -B -ntp sonar:sonar -Dsonar.projectName=library-api-devsecops'
            }
          }
        }
      }
    }
    stage('Quality Gate') {
      when {
        expression { params.ANALYSE_SONAR }
      }
      steps {
        timeout(time: 5, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }
    stage('Image') {
      when {
        branch 'main'
      }
      steps {
        sh 'docker build -t library-api-devsecops:$APP_VERSION .'
        // Couche systeme de l'image ; les dependances Java sont deja couvertes par le stage Trivy
        sh "trivy image --scanners vuln --pkg-types os --ignore-unfixed --no-progress --severity ${params.SEUIL_BLOQUANT} --exit-code 1 library-api-devsecops:${env.APP_VERSION}"
        // SBOM CycloneDX : inventaire des composants livres, archive avec le build
        sh 'trivy fs --format cyclonedx --offline-scan --output sbom.cdx.json pom.xml'
        archiveArtifacts artifacts: 'sbom.cdx.json', fingerprint: true
      }
    }
    stage('Deploiement recette') {
      when {
        allOf {
          branch 'main'
          expression { params.DEPLOYER_RECETTE }
        }
      }
      steps {
        script {
          def deploiement = build job: 'devsecops/library-api-deploy', parameters: [string(name: 'IMAGE', value: "library-api-devsecops:${env.APP_VERSION}"), string(name: 'ENVIRONNEMENT', value: 'recette')], propagate: false
          echo "library-api-deploy #${deploiement.number} : ${deploiement.result}"
          if (deploiement.result == 'SUCCESS') {
            echo "Recette : ${deploiement.buildVariables.URL_DEPLOYEE}"
          } else {
            unstable("Deploiement en recette en ${deploiement.result}")
          }
        }
      }
    }
  }
  post {
    always {
      script {
        currentBuild.description = "v${env.APP_VERSION} - ${env.BRANCH_NAME}"
      }
    }
    unstable {
      echo 'Build UNSTABLE : voir les onglets Semgrep, Trivy et HadoLint du build'
    }
    failure {
      echo "Build en echec sur ${env.BRANCH_NAME} : ${env.BUILD_URL}console"
    }
    fixed {
      echo 'Le build est repare'
    }
  }
}
