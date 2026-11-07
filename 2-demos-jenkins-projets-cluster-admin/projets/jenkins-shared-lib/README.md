# jenkins-shared-lib

Shared Library de la formation (slide 15), declaree dans Jenkins sous le nom `utopios-ci`.

- `vars/mavenBuild.groovy` : `mavenBuild(goals: 'clean verify')`
- `vars/notifyTeam.groovy` : `notifyTeam('dev-team@example.com')`
- `vars/javaServicePipeline.groovy` : pipeline complet parametre
- `src/fr/utopios/ci/Versioning.groovy` : helper de version
