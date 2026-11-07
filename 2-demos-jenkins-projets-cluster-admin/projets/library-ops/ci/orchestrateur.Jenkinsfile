// Orchestrateur de la suite Library : build job, parallele, copie d'artefacts (slide 5)
pipeline {
  agent none                                   // l'orchestrateur n'occupe pas d'executor en attendant
  options { timestamps() }
  stages {
    stage('Suite Library') {
      parallel {
        stage('core') {
          steps {
            script {
              def core = build job: 'library/library-core/main', wait: true, propagate: true
              echo "library-core #${core.number} : ${core.result}"
              env.CORE_BUILD = "${core.number}"
            }
          }
        }
        stage('legacy') {
          steps {
            script {
              // propagate: false : on lit le resultat et on decide soi-meme
              def legacy = build job: 'library/library-legacy', wait: true, propagate: false
              echo "library-legacy #${legacy.number} : ${legacy.result}"
              if (legacy.result != 'SUCCESS') { unstable("library-legacy en ${legacy.result}") }
            }
          }
        }
      }
    }
    stage('Fetch core jar') {
      agent { label 'linux' }
      steps {
        copyArtifacts projectName: 'library/library-core/main',
                      selector: specific("${env.CORE_BUILD}"),
                      filter: 'target/library-core-*.jar',
                      target: 'libs/', flatten: true, fingerprintArtifacts: true
        sh 'ls -l libs/'
      }
    }
    stage('Portal') {
      steps { build job: 'library/library-portal/main' }
    }
  }
}
