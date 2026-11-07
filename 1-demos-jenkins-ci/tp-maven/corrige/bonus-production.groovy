// Corrige du bonus : stage a ajouter apres 'Deploiement recette', dans stages { }
    stage('Production') {
      when {
        branch 'main'
        beforeAgent true
      }
      steps {
        timeout(time: 10, unit: 'MINUTES') {
          input message: "Mettre inventaire-api ${env.VERSION} en production ?", ok: 'Deployer'
        }
        sh """
          docker rm -f inventaire-prod || true
          docker run -d --name inventaire-prod --network ci-formation -p 8098:8080 inventaire-api:${env.VERSION}
        """
        retry(10) {
          sleep 3
          httpRequest url: 'http://inventaire-prod:8080/actuator/health', validResponseCodes: '200',
                      validResponseContent: 'UP', responseHandle: 'NONE', wrapAsMultipart: false
        }
      }
    }
