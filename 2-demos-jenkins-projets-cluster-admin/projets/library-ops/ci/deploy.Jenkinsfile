// Pipeline CD de promotion : une version deja publiee dans Nexus traverse dev -> recette -> prod (slides 19 a 22)
// Ne construit rien : telecharge l'artefact et l'installe.
pipeline {
  agent none
  parameters {
    string(name: 'VERSION', defaultValue: '1.4.1', description: 'Version de library-api publiee dans Nexus (maven-releases)')
    string(name: 'CHANGE_REF', defaultValue: '', description: 'Reference du change, obligatoire pour la production')
  }
  options { timestamps() }        // pas de disableConcurrentBuilds : le milestone arbitre entre promotions
  // params.* existe des le premier build ; les variables d'environnement des parametres, non
  environment { APP_VERSION = "${params.VERSION}" }
  stages {
    stage('Validate') {
      steps {
        script {
          if (params.VERSION.endsWith('-SNAPSHOT')) { error('Pas de SNAPSHOT dans la chaine de promotion') }
          currentBuild.displayName = "#${BUILD_NUMBER} v${params.VERSION}"
        }
      }
    }
    stage('Fetch') {
      agent { label 'linux' }
      environment { NEXUS = credentials('nexus-deploy') }
      steps {
        sh '''
          URL=http://nexus:8081/repository/maven-releases/fr/utopios/library-api/$APP_VERSION/library-api-$APP_VERSION.jar
          curl -sf -u "$NEXUS_USR:$NEXUS_PSW" -o library-api.jar "$URL"
          ls -l library-api.jar
        '''
        stash name: 'jar', includes: 'library-api.jar'
      }
    }
    stage('Dev') {
      agent { label 'linux && docker' }
      steps { unstash 'jar'; deployTo('dev', 8092) }
    }
    stage('Recette') {
      agent { label 'linux && docker' }
      options { lock('env-recette') }
      steps { unstash 'jar'; deployTo('recette', 8093) }
    }
    stage('Approbation prod') {
      steps {
        script { if (!params.CHANGE_REF?.trim()) { error('CHANGE_REF obligatoire pour la production') } }
        timeout(time: 1, unit: 'HOURS') {
          input message: "Promouvoir ${params.VERSION} en production (${params.CHANGE_REF}) ?", ok: 'Promouvoir'
        }
        milestone 1                        // une promotion plus recente annule celle-ci
      }
    }
    stage('Prod') {
      agent { label 'linux && docker' }
      options { lock('env-production') }
      steps {
        unstash 'jar'
        deployTo('prod', 8094)
        script {
          currentBuild.description = "v${params.VERSION} en production (${params.CHANGE_REF})"
          currentBuild.keepLog = true      // Keep this build forever : trace de la mise en production
        }
      }
    }
  }
}

// Deploiement idempotent d'un environnement : conteneur library-api-<env> recree avec le JAR
def deployTo(String envName, int port) {
  withEnv(["ENV_NAME=${envName}", "PORT=${port}"]) {
    sh '''
      docker rm -f library-api-$ENV_NAME 2>/dev/null || true
      docker create --name library-api-$ENV_NAME --network ci-formation -p $PORT:8080 \
             eclipse-temurin:21-jre-alpine java -jar /app.jar
      docker cp library-api.jar library-api-$ENV_NAME:/app.jar
      docker start library-api-$ENV_NAME
      for i in $(seq 1 30); do curl -sf http://library-api-$ENV_NAME:8080/actuator/health && exit 0; sleep 2; done; exit 1
    '''
  }
}
