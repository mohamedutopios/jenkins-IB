// Step global notifyTeam('dev-team@example.com') : mail de changement d'etat
def call(String to = 'dev-team@example.com') {
  emailext subject: "[Jenkins] ${currentBuild.currentResult} ${env.JOB_NAME} #${env.BUILD_NUMBER}",
           body: "${env.BUILD_URL}", to: to
}
