// Job de supervision de la plate-forme (slide 49) : echoue si un service de la chaine ne repond pas
pipeline {
  agent { label 'linux' }
  triggers { cron('H/30 * * * *') }
  options { timestamps(); buildDiscarder(logRotator(numToKeepStr: '50')) }
  stages {
    stage('Services') {
      steps {
        sh 'curl -sf -o /dev/null http://jenkins:8080/login && echo "jenkins OK"'
        sh 'curl -sf http://nexus:8081/service/rest/v1/status && echo "nexus OK"'
        sh 'curl -sf -o /dev/null http://gitea:3000/api/healthz && echo "gitea OK"'
      }
    }
    stage('Agents') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'jenkins-api', usernameVariable: 'U', passwordVariable: 'T')]) {
          sh '''
            curl -sfg -u "$U:$T" "http://jenkins:8080/computer/api/json?tree=computer[displayName,offline]" > nodes.json
            cat nodes.json
            ! grep -q '"offline":true' nodes.json
          '''
        }
      }
    }
  }
  post { failure { emailext subject: '[Jenkins] Supervision en echec', body: '${BUILD_URL}', to: 'admin@example.com' } }
}
