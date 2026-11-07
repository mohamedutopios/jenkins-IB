// Pipeline complet parametre : un Jenkinsfile de service tient en quelques lignes (slide 15)
def call(Map cfg = [:]) {
  pipeline {
    agent { label cfg.label ?: 'linux' }
    options { timestamps() }
    stages {
      stage('Build') {
        steps { mavenBuild(goals: cfg.goals ?: 'clean verify') }
      }
      stage('Version') {
        steps { echo "Version calculee : ${fr.utopios.ci.Versioning.fromBuild(env.BUILD_NUMBER as int, cfg.base ?: '2.3')}" }
      }
    }
    post {
      failure { notifyTeam(cfg.mail ?: 'dev-team@example.com') }
      fixed   { notifyTeam(cfg.mail ?: 'dev-team@example.com') }
    }
  }
}
