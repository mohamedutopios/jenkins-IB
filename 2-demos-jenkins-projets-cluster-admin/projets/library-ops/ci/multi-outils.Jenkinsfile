// Pipeline multi-outils : Maven + npm en parallele, puis image Docker (slides 12 et 13)
pipeline {
  agent none
  options { timestamps() }
  environment { APP_VERSION = "2.0.${BUILD_NUMBER}" }
  stages {
    stage('Build') {
      parallel {
        stage('Backend (Maven)') {
          agent { label 'linux && maven' }
          tools { jdk 'jdk21'; maven 'maven-3.9' }
          steps {
            git url: 'http://gitea:3000/formation/library-core.git', branch: 'main', credentialsId: 'gitea-token'
            sh 'mvn -B -ntp -Drevision=$APP_VERSION clean verify'
          }
          post { always { junit 'target/surefire-reports/TEST-*.xml' } }
        }
        stage('Frontend (npm)') {
          agent { label 'linux' }
          tools { nodejs 'node-22' }
          steps {
            git url: 'http://gitea:3000/formation/library-web.git', branch: 'main', credentialsId: 'gitea-token'
            sh 'node -v && npm -v'
            sh 'npm ci && npm run lint && npm test'
            sh 'npm run build'
            stash name: 'web', includes: 'dist/**,Dockerfile'
          }
          post { always { junit 'test-results/*.xml' } }
        }
      }
    }
    stage('Image Docker') {
      agent { label 'linux && docker' }        // linux-2 (inbound) n'a pas de client Docker
      steps {
        unstash 'web'
        sh 'docker build -t library-web:$APP_VERSION .'
        sh 'docker image ls library-web'
      }
    }
  }
}
