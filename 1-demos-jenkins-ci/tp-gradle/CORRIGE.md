# Corrigé — TP Gradle et Mattermost

Document formateur : à ne pas distribuer avec l'énoncé. Relevé sur Jenkins 2.580.2, Gradle 8.14.3, Mattermost 10.11.4, Gitea 1.24.7, plugins Gradle 2.20, Coverage 4.3515, Warnings 13.10345, Mattermost Notification 3.1.3.

Fichiers du corrigé : `corrige/Jenkinsfile` (Jenkinsfile final) et `corrige/TodoLifecycleTest.java` (test de l'exercice 6).

## Avant la séance

- Préchargez les images : `docker pull mattermost/mattermost-preview:10.11.4` (environ 1 Go) et faites un premier build de `todo-api` sur le poste de présentation : le wrapper télécharge Gradle 8.14.3 (≈ 130 Mo) et les dépendances Spring Boot.
- Port utilisé en plus du kit : **8065** (Mattermost). Variable `MATTERMOST_PORT` pour le changer.
- `mattermost-preview` ne conserve rien après `docker compose down` : le compte, le canal et le webhook sont à recréer (et l'**Endpoint** à corriger dans Jenkins).

---

## Exercice 0

`init-todo-api.ps1` lit `../.env` (compte `formation`), crée le dépôt privé et pousse le projet en forçant le bit exécutable de `gradlew` (`git update-index --chmod=+x`) : sans cela, un dépôt poussé depuis Windows donne `./gradlew: Permission denied` sur l'agent.

Erreur fréquente : `Compte formation refuse par http://localhost:3000` → la démo 0 (`scripts/init-gitea.ps1`) n'a pas été faite.

---

## Exercice 1

| Étape | Écran |
|---|---|
| Choix du client | **View in Browser** |
| Compte | **Email address** `formation@example.com`, **Choose a Username** `formation`, **Choose a Password** `Formation-2026` → **Create Account** |
| Organisation | **Organization name** `Formation` → **Continue** ; **What tools do you use?** → **Skip** ; **Invite your team members** → **Finish setup** |
| Canal | barre latérale **Add channels** → créer un canal public nommé `ci` |
| Webhook | icône en grille en haut à gauche → **Integrations** → **Incoming Webhooks** → **Add Incoming Webhook** : **Title** `jenkins`, **Channel** `ci` → **Save** |

Adresse directe du formulaire : http://localhost:8065/formation/integrations/incoming_webhooks/add.

**Réponse à la question.** Non : Mattermost affiche `http://localhost:8065/hooks/<id>` (son **Site URL**). Dans le conteneur Jenkins, `localhost` est Jenkins lui-même. L'URL à donner à Jenkins est `http://mattermost:8065/hooks/<id>` (nom du conteneur sur le réseau `ci-formation`). Même raisonnement que `http://gitea:3000` à la démo 7.

---

## Exercice 2

1. **Manage Jenkins → Plugins → Installed plugins** : `Gradle Plugin` est présent. **Available plugins** → `Mattermost` → cocher **Mattermost Notification** → **Install**.
2. **Manage Jenkins → System** → section **Global Mattermost Notifier Settings** :

   | Champ | Valeur |
   |---|---|
   | **Endpoint** | `http://mattermost:8065/hooks/<id>` |
   | **Channel** | `ci` |
   | **Icon to use** | vide |
   | **Build Server URL** | prérempli (`http://localhost:8080/`) : sert aux liens des messages |
   | **Use Custom Proxy** | décoché |

   **Test Connection** → `Success`, et dans `#ci` : `Mattermost/Jenkins plugin: you're all set! (parameters: room='ci', icon='null', buildServerUrl='http://localhost:8080/')`. Puis **Save**.

   Si le test échoue avec une connexion refusée : `localhost` au lieu de `mattermost` dans l'Endpoint.
3. Gitea → avatar → **Settings** → **Applications** → **Generate New Token** : **Token Name** `jenkins-packages`, **Repository and Organization Access** : **All**, ligne **package** : **Read and Write** (le reste **No Access**). Jenkins → **Manage Jenkins → Credentials** → **Add Credentials** → **Username with password** : **Scope** `Global`, **Username** `formation`, **Password** le jeton, **ID** `gitea-packages`, **Description** `Gitea - publication de paquets`.

**Réponse à la question.** `gitea-token` n'a que **repository : Read** (moindre privilège, démo 7) : Gitea refuserait la publication (HTTP 401). Un jeton par usage : si celui de publication fuit, on le révoque sans casser les clones.

---

## Exercice 3

**New Item** → `todo-api-freestyle` → **Freestyle project** :

| Section | Réglage |
|---|---|
| **General** | **Restrict where this project can be run** → **Label Expression** `linux` |
| **Source Code Management** | **Git** : **Repository URL** `http://gitea:3000/formation/todo-api.git`, **Credentials** `formation/******`, **Branch Specifier** `*/main` |
| **Build Steps** | **Add build step** → **Invoke Gradle script** → cocher **Use Gradle Wrapper**, cocher **Make gradlew executable**, **Wrapper location** vide (racine du dépôt), **Tasks** `clean build` |
| **Post-build Actions** | **Publish JUnit test result report** → **Test report XMLs** `build/test-results/test/*.xml` |

Console du premier build :
```
[todo-api-freestyle] $ /home/jenkins/agent/workspace/todo-api-freestyle/gradlew clean build
Downloading https://services.gradle.org/distributions/gradle-8.14.3-bin.zip
...
BUILD SUCCESSFUL in 43s
Recording test results
Finished: SUCCESS
```

**Réponses.** Deuxième build plus rapide : la distribution Gradle et les dépendances sont en cache dans `~/.gradle` de l'agent. Le wrapper fige la version de Gradle **dans le dépôt** (`gradle/wrapper/gradle-wrapper.properties`) : chaque développeur, chaque agent et chaque branche utilise la même, sans rien déclarer dans **Tools** ; changer de version est un commit, relu et réversible.

---

## Exercice 4

Jenkinsfile minimal :

```groovy
pipeline {
  agent { label 'linux' }
  stages {
    stage('Build & Test') {
      steps {
        withGradle {
          sh './gradlew --no-daemon clean build'
        }
      }
      post {
        always {
          junit 'build/test-results/test/*.xml'
        }
      }
    }
  }
}
```

Job : **New Item** → `todo-api-pipeline` → **Pipeline** → **Definition** : **Pipeline script from SCM**, **SCM** Git, même URL et credential, **Branch Specifier** `*/main`, **Script Path** `Jenkinsfile`.

Points à faire remarquer :
- `--no-daemon` : sur un agent de CI, un démon Gradle qui survit au build garde de la mémoire et des fichiers ouverts. Gradle l'indique : `To honour the JVM settings for this build a single-use Daemon process will be forked.`
- `withGradle` : ajoute la détection des build scans et l'annotation de la console Gradle ; il n'installe pas Gradle (c'est le wrapper qui le fait).
- `junit` dans le `post { always }` **du stage** : publié même quand `gradlew` échoue sur un test.

---

## Exercice 5

- **New Item** → `todo-api` → **Multibranch Pipeline** → **Branch Sources** → **Add source** → **Git** : URL et credential identiques, **Behaviours** : **Discover branches**.
- Gitea → dépôt `formation/todo-api` → **Settings** du dépôt → **Webhooks** (adresse directe : http://localhost:3000/formation/todo-api/settings/hooks) → **Add Webhook** → **Gitea** : **Target URL** `http://jenkins:8080/git/notifyCommit?url=http://gitea:3000/formation/todo-api.git&token=<jeton de la démo 10>`, **Trigger On** : **Custom Events…** → **Create**, **Delete**, **Push**.
- **Test Delivery** : réponse `Scheduled indexing of todo-api`.

**Réponse à la question.** Non. `notifyCommit` ne relance que les jobs **qui scrutent** ce dépôt : les Multibranch (indexation) et les jobs avec **Poll SCM** coché. `todo-api-pipeline` et `todo-api-freestyle` n'ont pas de déclencheur ; la réponse du webhook commence d'ailleurs par `No git jobs using repository: http://gitea:3000/formation/todo-api.git`.

Piège déjà vu : webhook créé dans **avatar → Settings → Webhooks** (compte) au lieu des réglages du dépôt : il fonctionne, mais sa page n'a pas de **Test Delivery**.

---

## Exercice 6

```groovy
      post {
        always {
          junit 'build/test-results/test/*.xml'
          recordCoverage tools: [[parser: 'JACOCO', pattern: 'build/reports/jacoco/test/jacocoTestReport.xml']],
                         qualityGates: [[metric: 'LINE', threshold: 70.0, criticality: 'UNSTABLE']]
          recordIssues tools: [checkStyle(pattern: 'build/reports/checkstyle/*.xml'),
                               spotBugs(pattern: 'build/reports/spotbugs/*.xml')],
                       qualityGates: [[threshold: 5, type: 'TOTAL', criticality: 'UNSTABLE']]
        }
      }
```

Console attendue (projet fourni) :
```
[Coverage] Line Coverage: 75.68% (28/37)
[Coverage]    - [Whole project - Line Coverage]: ≪Success≫ - (Actual value: 75.68%, Quality gate: 70.00)
[CheckStyle]    - [Total (any severity)]: ≪Success≫ - (Actual value: 1, Quality gate: 5.00)
[SpotBugs]    - [Total (any severity)]: ≪Success≫ - (Actual value: 1, Quality gate: 5.00)
```

- Alerte Checkstyle : `'42' is a magic number. [MagicNumber]` dans `TodoServiceTest.java`.
- Alerte SpotBugs : `EI_EXPOSE_REP2` sur le constructeur de `TodoController` (il garde une référence au service : faux positif classique avec l'injection Spring, à discuter).
- Avec `threshold: 80.0` : `Some quality gates have been missed: overall result is UNSTABLE` puis `[Whole project - Line Coverage]: ≪Unstable≫ - (Actual value: 75.68%, Quality gate: 80.00)`.
- Étape 4 : copier `corrige/TodoLifecycleTest.java` dans `src/test/java/fr/utopios/todo/` → **35/37 lignes (94,6 %)**, build **SUCCESS**. Il couvre `GET /{id}`, `PUT /{id}/done` et `DELETE /{id}` (y compris le 404).

Ligne `No blamer installed yet. You need to install the 'git-forensics' plugin` : sans conséquence (elle sert à attribuer les alertes aux auteurs des commits).

**Réponses.** `build.gradle` règle `ignoreFailures = true` pour Checkstyle et SpotBugs : Gradle produit les rapports sans échouer, et c'est **Jenkins**, par les quality gates, qui décide du statut. On centralise ainsi la politique (seuils) dans le Jenkinsfile, visible et versionnée.

---

## Exercice 7

```groovy
  options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
    timeout(time: 20, unit: 'MINUTES')
    disableConcurrentBuilds()
    timestamps()
  }

  parameters {
    booleanParam(name: 'PUBLIER', defaultValue: false,
                 description: 'Publier le JAR dans le registre Maven de Gitea (branche main uniquement)')
  }

  environment {
    APP_VERSION = "1.0.${BUILD_NUMBER}"
  }
```
et dans le stage : `sh './gradlew --no-daemon clean build -Pversion=$APP_VERSION'` (guillemets simples : c'est le shell qui lit la variable).

`build.gradle` prend `-Pversion` en priorité et vaut `1.0.0-SNAPSHOT` sans lui.

**Réponse.** **Build with Parameters** n'apparaît qu'après le premier build : Jenkins ne connaît la directive `parameters` qu'en exécutant le Jenkinsfile (piège de la démo 11). Le Directive Generator écrit `timeout(20)` quand l'unité est `MINUTES` : les deux écritures sont équivalentes (voir `PIPELINE-SYNTAX.md`).

---

## Exercice 8

```groovy
  post {
    success {
      mattermostSend color: 'good',
                     message: ":white_check_mark: ${currentBuild.fullDisplayName} reussi (<${env.BUILD_URL}|ouvrir>)"
    }
    unstable {
      mattermostSend color: 'warning',
                     message: ":warning: ${currentBuild.fullDisplayName} instable : seuil de couverture ou de qualite depasse (<${env.BUILD_URL}|ouvrir>)"
    }
    failure {
      mattermostSend color: 'danger',
                     message: ":x: ${currentBuild.fullDisplayName} en echec (<${env.BUILD_URL}console|console>)"
    }
    fixed {
      mattermostSend color: 'good',
                     message: ":tada: ${currentBuild.fullDisplayName} : la branche est reparee"
    }
  }
```

Message reçu : `✅ todo-api » main #5 reussi (ouvrir)`, avec la barre de couleur à gauche ; l'expéditeur affiché est `jenkins`. Les liens sont construits à partir de **Build Server URL** (exercice 2).

- Guillemets **doubles** ici : c'est Groovy qui remplace `${...}` (aucun secret dans ces messages, voir la démo 9 pour la règle inverse).
- `fixed` s'ajoute à `success` : au retour au vert, deux messages.
- **Réponse.** `env.JOB_NAME` est le nom technique, encodé pour une URL (`todo-api/feature%2Fcompteur`). `currentBuild.fullDisplayName` donne le nom affiché : `todo-api » feature/compteur #3`.

---

## Exercice 9

```groovy
    stage('Publish') {
      when {
        allOf { branch 'main'; expression { params.PUBLIER } }
      }
      environment {
        GITEA_PKG = credentials('gitea-packages')
      }
      steps {
        withGradle {
          sh './gradlew --no-daemon publish -Pversion=$APP_VERSION -x test'
        }
      }
    }
```

- `credentials()` sur un **Username with password** crée `GITEA_PKG` (`user:jeton`), `GITEA_PKG_USR` et `GITEA_PKG_PSW` : `build.gradle` lit les deux dernières.
- Console : `> Task :publishMavenPublicationToGiteaRepository`, `> Task :publish`, `BUILD SUCCESSFUL`. Le paquet est sur http://localhost:3000/formation/-/packages (`fr.utopios:todo-api`, version `1.0.<n>`).
- Version unique par build (`1.0.${BUILD_NUMBER}`) : Gitea refuse de republier une version existante (HTTP 400). Le stage ne tourne que sur `main`, sinon deux branches au même numéro de build entreraient en collision.

| Erreur | Cause |
|---|---|
| `Using insecure protocols with repositories, without explicit opt-in, is unsupported.` | `allowInsecureProtocol = true` retiré de `build.gradle` (Gitea du kit en HTTP) |
| `Received status code 401` | jeton sans **package : Read and Write**, ou `gitea-token` utilisé à la place de `gitea-packages` |
| `Received status code 400` | version déjà publiée (le fichier existe déjà dans Gitea) |

---

## Bonus

```groovy
    stage('Validation') {
      when {
        allOf { branch 'main'; expression { params.PUBLIER } }
      }
      steps {
        mattermostSend color: '#439FE0',
                       message: "En attente de validation : ${currentBuild.fullDisplayName} (<${env.BUILD_URL}input/|valider>)"
        timeout(time: 15, unit: 'MINUTES') {
          input message: "Publier todo-api ${env.APP_VERSION} ?", ok: 'Publier'
        }
      }
    }
```

Console : `Timeout set to expire in 15 min`, `Publier todo-api 1.0.4 ?`, `Publier or Abort`, puis après le clic `Approved by admin`. Le lien du message ouvre la page `input/` du build. Sans réponse, le build se termine **ABORTED**, et aucun des blocs `success`, `unstable` ou `failure` ne s'exécute (ajouter `aborted { }` si l'équipe veut en être prévenue).

---

## Jenkinsfile final

Voir `corrige/Jenkinsfile`. Il a été exécuté en entier : SUCCESS sur `main` (avec et sans publication), UNSTABLE sur une branche au seuil de 80 %, FAILURE puis `fixed`, et chaque notification reçue dans `#ci`.
