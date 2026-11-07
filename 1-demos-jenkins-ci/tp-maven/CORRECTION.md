# Correction pas à pas — TP Pipeline Maven `inventaire-api`

Document formateur. Chaque step et chaque directive est obtenu dans **Pipeline Syntax** : on indique l'écran, les champs remplis, le bouton, le **texte exact généré**, puis **où le coller** et ce qu'on corrige ensuite à la main.

Relevé sur Jenkins 2.580.2 avec Pipeline Utility Steps 3.810, HTTP Request 1.659, Lockable Resources 1582, Workspace Cleanup 0.49, Coverage 4.3515 et Warnings 13.10345 ; Maven 3.9.11 (wrapper), ntfy 2.14.0. Le Jenkinsfile final est dans `corrige/Jenkinsfile`, le bonus dans `corrige/bonus-production.groovy`.

---

## Avant la séance

- Préchargez les images : `docker pull binwiederhier/ntfy:v2.14.0` et `docker pull eclipse-temurin:21-jre-alpine` (image de base du `Dockerfile`).
- Faites un premier build sur le poste de présentation : le wrapper télécharge Maven 3.9.11, puis Spring Boot, JaCoCo et PMD.
- Ports utilisés en plus du kit : **8070** (ntfy), **8097** (recette), **8098** (production). Variable `NTFY_PORT` dans `docker-compose.yml` pour changer le premier.

---

## Mémo : utiliser Pipeline Syntax

| | Snippet Generator | Declarative Directive Generator |
|---|---|---|
| Ouvrir | menu du job → **Pipeline Syntax**, ou http://localhost:8080/pipeline-syntax/ | menu de gauche de la même page → **Declarative Directive Generator**, ou http://localhost:8080/directive-generator/ |
| Choisir | liste **Sample Step** | liste **Sample Directive** |
| Générer | **Generate Pipeline Script** | **Generate Declarative Directive** |
| Produit | un **step** : une action | une **directive** : un bloc de structure |
| Se colle | dans `steps { }` ou dans une condition de `post` | sous `pipeline { }` ou sous `stage('…') { }` |

Trois comportements des générateurs à connaître (constatés pendant ce TP) :

1. **Les valeurs par défaut ne sont pas écrites.** `recordCoverage` avec `JaCoCo` et `Mark the step and the build as unstable` ne produit ni `parser: 'JACOCO'` ni `criticality: 'UNSTABLE'` : ce sont les valeurs par défaut du step, même si le formulaire affiche autre chose en premier. De même `timeout(20)` pour 20 minutes, `sleep 3` pour 3 secondes.
2. **Certaines listes s'affichent sur `NANOSECONDS`** (**Unit** de `sleep`, `timeout`) : la choisir explicitement, sinon le code généré est `unit: 'NANOSECONDS'`.
3. **Certaines options ont une case à cocher interne** (**Discard old builds**, **Do not allow concurrent builds**) : sans elle, l'option est absente du texte généré.

---

## Exercice 0 — Préparer l'environnement

1. À la racine du kit : `docker compose up -d` (Jenkins, Gitea, `linux-1`…).
2. Dans `tp-maven` :
   ```powershell
   docker compose up -d
   ```
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\init-inventaire-api.ps1
   ```
   Sortie : `Depot formation/inventaire-api cree (prive)` puis `Projet pousse : http://localhost:3000/formation/inventaire-api`.
3. Ouvrir http://localhost:8070/inventaire : la page ntfy du topic `inventaire`, vide pour l'instant.

Le script force le bit exécutable de `mvnw` dans Git (`git update-index --chmod=+x mvnw`). Sans cela, un dépôt poussé depuis Windows donne `./mvnw: Permission denied` sur l'agent.

---

## Exercice 1 — Plugins

1. **Manage Jenkins → Plugins → Installed plugins** : `Lockable Resources plugin` (démo 6) et `Jenkins Workspace Cleanup Plugin` (plugins suggérés) sont présents ; `Coverage Plugin` et `Warnings Plugin` aussi (démo 6).
2. **Available plugins** → rechercher `Pipeline Utility Steps` → cocher ; rechercher `HTTP Request` → cocher → **Install**. Pas de redémarrage nécessaire.
3. http://localhost:8080/pipeline-syntax/ → **Sample Step** contient :

   | Step | Plugin |
   |---|---|
   | `readMavenPom: Read a maven project file.` | Pipeline Utility Steps |
   | `httpRequest: Perform an HTTP Request and return a response object` | HTTP Request |
   | `lock: Lock shared resource` | Lockable Resources |
   | `cleanWs: Delete workspace when build is done` | Workspace Cleanup |

Message clé : un step absent de **Sample Step** n'existe pas sur l'instance ; le Snippet Generator est aussi le moyen le plus rapide de vérifier qu'un plugin est installé.

---

## Exercice 2 — Premier Jenkinsfile

### 2.1 Le step `sh`

- **Sample Step** : `sh: Shell Script`
- **Shell Script** : `./mvnw -B -ntp clean package`
- **Generate Pipeline Script** →
  ```groovy
  sh './mvnw -B -ntp clean package'
  ```
- **Où :** dans `steps { }` du stage `Build & tests unitaires`.

### 2.2 Le step `junit`

- **Sample Step** : `junit: Archive JUnit-formatted test results`
- **Test report XMLs** : `target/surefire-reports/*.xml` (le reste par défaut)
- **Generate Pipeline Script** →
  ```groovy
  junit 'target/surefire-reports/*.xml'
  ```
- **Où :** dans `post { always { } }` **du stage** : les rapports sont publiés même si un test échoue (Maven s'arrête alors en erreur).

### 2.3 Le step `archiveArtifacts`

- **Sample Step** : `archiveArtifacts: Archive the artifacts`
- **Files to archive** : `target/*.jar`
- **Advanced** → cocher **Fingerprint all archived artifacts**
- **Generate Pipeline Script** →
  ```groovy
  archiveArtifacts artifacts: 'target/*.jar', fingerprint: true, followSymlinks: false
  ```
- **Où :** dans `post { success { } }` du stage : on n'archive qu'un JAR dont les tests passent. `followSymlinks: false` est ajouté par le générateur ; on peut le garder ou l'enlever.

### 2.4 Le Jenkinsfile après l'exercice 2

```groovy
pipeline {
  agent { label 'linux' }
  stages {
    stage('Build & tests unitaires') {
      steps {
        sh './mvnw -B -ntp clean package'
      }
      post {
        always {
          junit 'target/surefire-reports/*.xml'
        }
        success {
          archiveArtifacts artifacts: 'target/*.jar', fingerprint: true, followSymlinks: false
        }
      }
    }
  }
}
```

### 2.5 Le job

**New Item** → `inventaire-api` → **Multibranch Pipeline** → **OK** → **Branch Sources** → **Add source** → **Git** :

| Champ | Valeur |
|---|---|
| **Project Repository** | `http://gitea:3000/formation/inventaire-api.git` |
| **Credentials** | `formation/******` (`gitea-token`) |
| **Behaviours** | **Discover branches** (par défaut) |

**Save** : l'indexation trouve `main` et lance le build.

### 2.6 Résultat

```
+ ./mvnw -B -ntp clean package
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
Recording test results
Archiving artifacts
```
Page du build : **Tests** (5), **Build Artifacts** `inventaire-api-1.2.0.jar`, **See Fingerprints**.

**Réponses.** `junit` en `always` : on veut voir **quel** test a échoué, donc publier le rapport justement quand ça casse. `archiveArtifacts` en `success` : un JAR non testé ne doit pas être livrable. `-ntp` (*no transfer progress*) supprime les milliers de lignes de téléchargement de la console ; `-B` (*batch*) désactive les couleurs et l'interactivité.

---

## Exercice 3 — Version lue dans le POM

### 3.1 Le step `readMavenPom`

- **Sample Step** : `readMavenPom: Read a maven project file.`
- Seul champ : **File**. Laissé vide, le générateur écrit `readMavenPom file: ''` : saisir `pom.xml`.
- **Generate Pipeline Script** →
  ```groovy
  readMavenPom file: 'pom.xml'
  ```

### 3.2 Où le coller

Le step **renvoie une valeur** (le modèle Maven du projet) : pour la ranger dans une variable, il faut du Groovy, donc un bloc `script { }` dans `steps`. Nouveau premier stage :

```groovy
    stage('Version') {
      steps {
        script {
          def pom = readMavenPom file: 'pom.xml'
          env.VERSION = pom.version
          currentBuild.displayName = "#${env.BUILD_NUMBER} - ${env.VERSION}"
        }
      }
    }
```

- `pom.version` : `1.2.0`, la balise `<version>` du `pom.xml`.
- `env.VERSION = …` crée une **variable d'environnement** : elle vit jusqu'à la fin du build, dans tous les stages, et le shell la lit en `$VERSION`. Une variable `def VERSION` disparaîtrait à la sortie du bloc `script`.
- `currentBuild.displayName` : le nom affiché dans l'historique (voir **Global Variables Reference** → `currentBuild`).
- `readMavenPom` lit le fichier **dans le workspace de l'agent** (c'est un step), contrairement à un `new File('pom.xml')` Groovy qui chercherait sur le controller. Aucune approbation de script n'est demandée.

### 3.3 Résultat

Console `[Pipeline] readMavenPom` ; historique : `#2 - 1.2.0`.

**Piège.** Le stage `Version` doit être **le premier** : les stages suivants utilisent `$VERSION`. Un Multibranch fait le checkout avant le premier stage (`Declarative: Checkout SCM`), le `pom.xml` est donc déjà là.

---

## Exercice 4 — Tests d'intégration et analyse en parallèle

### 4.1 Les steps

Générés comme à l'exercice 2 :

| Sample Step | Champ | Texte généré |
|---|---|---|
| `sh: Shell Script` | `./mvnw -B -ntp failsafe:integration-test failsafe:verify` | `sh './mvnw -B -ntp failsafe:integration-test failsafe:verify'` |
| `junit: Archive JUnit-formatted test results` | `target/failsafe-reports/*.xml` | `junit 'target/failsafe-reports/*.xml'` |
| `sh: Shell Script` | `./mvnw -B -ntp pmd:pmd pmd:cpd` | `sh './mvnw -B -ntp pmd:pmd pmd:cpd'` |

### 4.2 La structure `parallel`

`parallel` n'est ni dans le Snippet Generator ni dans le Directive Generator sous cette forme : c'est une **section de stage**, qui remplace `steps`. On l'écrit à la main (le Directive Generator propose `stage: Stage` pour générer le squelette d'un stage si besoin) :

```groovy
    stage('Verifications') {
      parallel {
        stage('Tests d\'integration') {
          steps {
            sh './mvnw -B -ntp failsafe:integration-test failsafe:verify'
          }
          post {
            always {
              junit 'target/failsafe-reports/*.xml'
            }
          }
        }
        stage('Analyse PMD') {
          steps {
            sh './mvnw -B -ntp pmd:pmd pmd:cpd'
          }
        }
      }
    }
```

- `\'` : l'apostrophe de « d'integration » est échappée, le nom étant entre guillemets simples.
- On appelle directement les **goals** Failsafe et PMD (`plugin:goal`) sans relancer le cycle de vie : les classes et les tests sont déjà compilés par `package`. Les deux branches lisent `target/classes` et écrivent dans des dossiers différents (`target/failsafe-reports`, `target/pmd.xml`) : elles peuvent tourner ensemble.

### 4.3 Résultat

**Pipeline Overview** : `Verifications` avec deux branches côte à côte. Console :
```
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 2.641 s -- in fr.utopios.inventaire.StockApiIT
```
**Tests** : 7 (5 + 2).

**Réponse.** `Build & tests unitaires` produit ce que les deux autres lisent (classes compilées, JAR) : il doit finir avant. Les deux vérifications sont **indépendantes** entre elles.

---

## Exercice 5 — Seuils de qualité

### 5.1 `recordCoverage` (Snippet Generator)

- **Sample Step** : `recordCoverage: Record code coverage results`
- Bloc **Code Coverage Tools** : **Coverage Parser** `JaCoCo Coverage Reports`, **Report File Pattern** `target/site/jacoco/jacoco.xml`
- **Add Quality Gate** :

  | Champ | Valeur |
  |---|---|
  | **Threshold** | `50` |
  | **Baseline** | `Whole project` |
  | **Metric** | `Line Coverage` |
  | **Aggregation** | par défaut |
  | **Step or Build Result** | `Mark the step and the build as unstable` |

- **Generate Pipeline Script** →
  ```groovy
  recordCoverage qualityGates: [[integerThreshold: 50, metric: 'LINE', threshold: 50.0]], tools: [[pattern: 'target/site/jacoco/jacoco.xml']]
  ```

Ni `parser: 'JACOCO'` ni `criticality: 'UNSTABLE'` : ce sont les **valeurs par défaut** du step (vérifiez-le : choisissez `Cobertura` et `Fail the step and the build`, le texte affiche alors `parser: 'COBERTURA'` et `criticality: 'FAILURE'`).

### 5.2 `recordIssues` (Snippet Generator)

- **Sample Step** : `recordIssues: Record compiler warnings and static analysis results`
- **Static Analysis Tools** → **Tool** `PMD`, **Report File Pattern** `target/pmd.xml`
- **Add Tool** → **Tool** `CPD`, **Report File Pattern** `target/cpd.xml`
- **Advanced** (le bouton en bas du formulaire, pas ceux des outils) → **Quality gates** → **Add Quality Gate** : **Threshold** `5`, **Type** `Total (any severity)`, **Result** `Mark the step and the build as unstable`
- **Generate Pipeline Script** →
  ```groovy
  recordIssues qualityGates: [[integerThreshold: 5, threshold: 5.0, type: 'TOTAL']], sourceCodeRetention: 'LAST_BUILD', tools: [pmdParser(pattern: 'target/pmd.xml'), cpd(pattern: 'target/cpd.xml')]
  ```

### 5.3 Où les coller

Nouveau stage après `Verifications` : ces steps lisent les rapports des deux branches parallèles.

```groovy
    stage('Rapports qualite') {
      steps {
        recordCoverage qualityGates: [[integerThreshold: 50, metric: 'LINE', threshold: 50.0]],
                       tools: [[pattern: 'target/site/jacoco/jacoco.xml']]
        recordIssues qualityGates: [[integerThreshold: 5, threshold: 5.0, type: 'TOTAL']],
                     sourceCodeRetention: 'LAST_BUILD',
                     tools: [pmdParser(pattern: 'target/pmd.xml'), cpd(pattern: 'target/cpd.xml')]
      }
    }
```
(Retours à la ligne ajoutés pour la lisibilité : Groovy accepte la coupure après une virgule.)

### 5.4 Résultat

```
[Coverage] Line Coverage: ...
[Coverage]    - [Whole project - Line Coverage]: ≪Success≫ - (Actual value: 58.33%, Quality gate: 50.00)
[PMD]    - [Total (any severity)]: ≪Success≫ - (Actual value: 1, Quality gate: 5.00)
[CPD]    - [Total (any severity)]: ≪Success≫ - (Actual value: 2, Quality gate: 5.00)
```
Menu du build : **Coverage**, **PMD Warnings**, **CPD Duplications**.

- Alerte PMD : `UnnecessaryImport`, l'import inutilisé `java.util.Optional` de `StockService` (laissé exprès).
- CPD : un même bloc de code trouvé à **deux** endroits, lignes 36-40 et 46-50 de `StockService` (le début de `entrer` et de `sortir` : contrôle de la quantité puis `trouver`), d'où `Actual value: 2`. Le `pom.xml` règle `minimumTokens` à 25 pour que la duplication soit détectée.
- La couverture ne compte que les **tests unitaires** : le rapport JaCoCo est produit à la phase `test` (voir `pom.xml`), avant Failsafe.

### 5.5 Seuil à 60 %

Sur `feature/seuil`, remplacer `50` et `50.0` par `60` et `60.0` :
```
[Coverage] -> Some quality gates have been missed: overall result is UNSTABLE
[Coverage]    - [Whole project - Line Coverage]: ≪Unstable≫ - (Actual value: 58.33%, Quality gate: 60.00)
```
Build **UNSTABLE**. `integerThreshold` et `threshold` portent la même valeur : le plugin lit `threshold` et garde l'autre pour compatibilité ; on modifie les deux.

---

## Exercice 6 — `options` et `parameters` (Directive Generator)

### 6.1 `options`

http://localhost:8080/directive-generator/ → **Sample Directive** `options: Options`. Chaque **Add** ouvre la liste des options ; on en ajoute quatre :

| Add → | Réglages dans le bloc ajouté |
|---|---|
| `buildDiscarder: Discard old builds` | cocher la case **Discard old builds** du bloc, puis **Strategy** `Log Rotation`, **Max # of builds to keep** `10` |
| `timeout: Enforce time limit` | **Timeout** `20`, **Unit** `MINUTES` (vérifier la liste) |
| `timestamps: Timestamps` | rien |
| `disableConcurrentBuilds: Do not allow concurrent builds` | cocher la case **Do not allow concurrent builds** du bloc (laisser **Abort previous builds** décochée) |

**Generate Declarative Directive** →
```groovy
options {
  buildDiscarder logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '', numToKeepStr: '10')
  timeout(20)
  timestamps
  disableConcurrentBuilds()
}
```

**Où :** directement sous `pipeline {`, après `agent`. Un seul bloc `options` par pipeline.

À corriger à la main (facultatif) : `timestamps` → `timestamps()` (les deux sont acceptés).

**Piège constaté.** Sans les cases internes **Discard old builds** et **Do not allow concurrent builds**, ces deux options **n'apparaissent pas** dans le texte généré, sans message d'erreur.

### 6.2 `parameters`

**Sample Directive** `parameters: Parameters` → **Add** :

| Add → | Champs |
|---|---|
| `booleanParam: Boolean Parameter` | **Name** `DEPLOYER_RECETTE`, cocher **Set by Default**, **Description** `Deployer en recette apres les tests` |
| `choice: Choice Parameter` | **Name** `NIVEAU_LOG`, **Choices** `INFO` / `DEBUG` / `WARN` (une par ligne, la première est la valeur par défaut), **Description** `Niveau de log de l application deployee` |

**Generate Declarative Directive** →
```groovy
parameters {
  booleanParam defaultValue: true, description: 'Deployer en recette apres les tests', name: 'DEPLOYER_RECETTE'
  choice choices: ['INFO', 'DEBUG', 'WARN'], description: 'Niveau de log de l application deployee', name: 'NIVEAU_LOG'
}
```
**Où :** sous `pipeline {`, après `options`. Apostrophe évitée dans la description (`l application`) : elle fermerait la chaîne.

### 6.3 Résultat

Console : `Timeout set to expire in 20 min`, lignes horodatées. Après ce build, **Build with Parameters** propose les deux paramètres.

**Réponses.** Case non cochée : option absente, aucun avertissement — toujours relire le texte généré. **Build with Parameters** après un build : Jenkins ne découvre la directive `parameters` qu'en exécutant le Jenkinsfile, puis enregistre les paramètres dans la configuration du job.

---

## Exercice 7 — Image Docker et déploiement sous verrou

### 7.1 Construire l'image

**Sample Step** `sh: Shell Script` → **Shell Script** :
```
docker build --build-arg JAR=target/inventaire-api-$VERSION.jar -t inventaire-api:$VERSION .
```
→ `sh 'docker build --build-arg JAR=target/inventaire-api-$VERSION.jar -t inventaire-api:$VERSION .'`

Stage `Image Docker`, après `Rapports qualite`. Guillemets simples : c'est le shell qui lit `$VERSION` (variable d'environnement de l'exercice 3). Console : `naming to docker.io/library/inventaire-api:1.2.0 done`.

### 7.2 La condition (Directive Generator)

**Sample Directive** `when: When Condition` :
- **When Condition** : `allOf: Execute the stage if all nested conditions are true`
- **Add** → `branch: Execute the stage if the current branch matches a pattern` → **Branch pattern** `main`
- cocher **Evaluate Before Agent**
- **Generate Declarative Directive** →
  ```groovy
  when {
    allOf {
      branch 'main'
    }
    beforeAgent true
  }
  ```

La liste des conditions (`allOf`, `anyOf`, `branch`, `buildingTag`, `changeRequest`, `changelog`, `changeset`, `environment`, `isRestartedRun`, `not`, `tag`, `triggeredBy`) **ne contient pas `expression`** : on l'ajoute à la main dans `allOf` :

```groovy
      when {
        allOf {
          branch 'main'
          expression { params.DEPLOYER_RECETTE }
        }
        beforeAgent true
      }
```

Le générateur propose `environment` (**Environment variable name** `DEPLOYER_RECETTE`, **Expected value** `true` → `environment name: 'DEPLOYER_RECETTE', value: 'true'`), mais il compare des **textes** ; `expression { params.DEPLOYER_RECETTE }` lit directement le booléen du paramètre.

**Où :** sous `stage('Deploiement recette') {`, avant `steps`. `beforeAgent true` : la condition est évaluée avant de réserver un agent, utile si le stage en déclarait un.

### 7.3 Le verrou (Snippet Generator)

- **Sample Step** : `lock: Lock shared resource`
- **Resource** : `recette-inventaire` (les autres champs vides)
- **Generate Pipeline Script** →
  ```groovy
  lock(resource: 'recette-inventaire', timeoutUnit: 'SECONDS') {
      // some block
  }
  ```

C'est un **step à bloc** : tout ce qui est dans ses accolades s'exécute verrou tenu. `timeoutUnit: 'SECONDS'` n'a d'effet qu'avec **Timeout for resource allocation** : on peut le supprimer.

La ressource n'a pas besoin d'exister : Lockable Resources la crée à la volée (on peut aussi la déclarer dans **Manage Jenkins → Lockable Resources**). Le menu du build propose ensuite **Lockable resources**.

### 7.4 Le stage complet

```groovy
    stage('Deploiement recette') {
      when {
        allOf {
          branch 'main'
          expression { params.DEPLOYER_RECETTE }
        }
        beforeAgent true
      }
      steps {
        lock(resource: 'recette-inventaire') {
          sh """
            docker rm -f inventaire-recette || true
            docker run -d --name inventaire-recette --network ci-formation -p 8097:8080 \
              -e LOGGING_LEVEL_ROOT=${params.NIVEAU_LOG} inventaire-api:${env.VERSION}
          """
        }
      }
    }
```

- `"""…"""` : chaîne Groovy multi-lignes **interpolée** : Groovy remplace `${params.NIVEAU_LOG}` et `${env.VERSION}` avant d'envoyer la commande au shell. Pas de secret ici, donc pas de risque (règle de la démo 9).
- `docker rm -f … || true` : le premier déploiement n'a pas de conteneur à supprimer.
- `--network ci-formation` : Jenkins (smoke test) et ntfy joignent l'application par son nom.

### 7.5 Résultat

```
Trying to acquire lock on [Resource: recette-inventaire]
Lock acquired on [Resource: recette-inventaire], resources: [recette-inventaire]
...
Lock released on resource [Resource: recette-inventaire], resources: [recette-inventaire]
```
http://localhost:8097/actuator/health → `{"status":"UP"}`. Sur une autre branche : `Stage "Deploiement recette" skipped due to when conditional`.

**Réponse.** Sans verrou, deux builds (deux branches, ou `main` relancé) pourraient exécuter `docker rm` / `docker run` en même temps et laisser la recette dans un état incohérent. Le second build attend `Trying to acquire lock` jusqu'à la libération.

---

## Exercice 8 — Smoke test

### 8.1 `httpRequest` (Snippet Generator)

- **Sample Step** : `httpRequest: Perform an HTTP Request and return a response object`
- **URL** : `http://inventaire-recette:8080/actuator/health`, **HTTP mode** `GET` (défaut)
- **Advanced** :

  | Champ | Valeur |
  |---|---|
  | **Response codes expected** | `200` (défaut `100:399`) |
  | **Response content expected** | `UP` |
  | **Response body in console?** | `Yes` |

- **Generate Pipeline Script** →
  ```groovy
  httpRequest consoleLogResponseBody: true, responseHandle: 'NONE', url: 'http://inventaire-recette:8080/actuator/health', validResponseCodes: '200', validResponseContent: 'UP', wrapAsMultipart: false
  ```

Si le code ou le contenu ne correspondent pas, le step **échoue** : c'est ce qui en fait un test.

### 8.2 `retry` et `sleep`

| Sample Step | Champs | Texte généré |
|---|---|---|
| `retry: Retry the body up to N times` | **Retry Count** `10` | `retry(10) {` … `// some block` … `}` |
| `sleep: Sleep` | **Sleep time** `3`, **Unit** `SECONDS` | `sleep 3` |

**Piège :** la liste **Unit** de `sleep` s'affiche sur `NANOSECONDS` ; sans la changer, le texte est `sleep time: 3, unit: 'NANOSECONDS'` et l'attente est nulle. Avec `SECONDS`, valeur par défaut, le générateur écrit simplement `sleep 3`.

### 8.3 Où les coller

Dans le bloc du `lock`, après le `sh` : le verrou couvre le déploiement **et** sa vérification.

```groovy
        lock(resource: 'recette-inventaire') {
          sh """
            ...
          """
          retry(10) {
            sleep 3
            httpRequest consoleLogResponseBody: true, responseHandle: 'NONE',
                        url: 'http://inventaire-recette:8080/actuator/health',
                        validResponseCodes: '200', validResponseContent: 'UP', wrapAsMultipart: false
          }
        }
```

### 8.4 Résultat

```
Sleeping for 3 sec
HttpMethod: GET
URL: http://inventaire-recette:8080/actuator/health
Sending request to url: http://inventaire-recette:8080/actuator/health
Response Code: 200
{"status":"UP"}
```
Sur le poste de test, la première tentative a suffi (démarrage en moins de 3 s). Avec une URL fausse, les 10 tentatives échouent et le build passe en **FAILURE**.

---

## Exercice 9 — Notifications ntfy et nettoyage

### 9.1 Le squelette `post` (Directive Generator)

**Sample Directive** `post: Post Stage or Build Conditions`. Le formulaire liste les conditions par leur **description** :

| Cocher | Condition générée |
|---|---|
| *Run if the build status is "Success" or hasnt been set yet* | `success` |
| *Run if the build status is "Unstable"* | `unstable` |
| *Run if the build status is "Failure"* | `failure` |
| *Run if the previous build was not successful and the current builds status is "Success"* | `fixed` |
| *Always run after all other conditions, regardless of build status* | `cleanup` |

**Generate Declarative Directive** →
```groovy
post {
  unstable {
    // One or more steps need to be included within each condition's block.
  }
  cleanup {
    // One or more steps need to be included within each condition's block.
  }
  success {
    // One or more steps need to be included within each condition's block.
  }
  failure {
    // One or more steps need to be included within each condition's block.
  }
  fixed {
    // One or more steps need to be included within each condition's block.
  }
}
```
**Où :** sous `pipeline {`, **après** la fermeture de `stages { }`.

- Les conditions sortent dans l'ordre du formulaire (`unstable`, `cleanup`, `success`…). L'ordre d'écriture n'a pas d'importance : Jenkins évalue les conditions dans son propre ordre, `cleanup` toujours en dernier. On peut les réordonner pour la lisibilité (c'est ce que fait le corrigé).
- Un bloc qui ne contient que le commentaire est refusé à la validation : `No steps specified for branch`. Chaque commentaire doit être remplacé par au moins un step.

### 9.2 `httpRequest` en POST (Snippet Generator)

- **Sample Step** `httpRequest` ; **URL** `http://ntfy/inventaire` ; **HTTP mode** `POST`
- **Advanced** → **Request body** `Build OK`
- **Custom headers** → **Add** → **Header** `Title`, **Value** `inventaire-api` (**Mask value** décoché) ; **Add** → **Header** `Tags`, **Value** `white_check_mark`
- **Generate Pipeline Script** →
  ```groovy
  httpRequest customHeaders: [[maskValue: false, name: 'Title', value: 'inventaire-api'], [maskValue: false, name: 'Tags', value: 'white_check_mark']], httpMode: 'POST', requestBody: 'Build OK', responseHandle: 'NONE', url: 'http://ntfy/inventaire', wrapAsMultipart: false
  ```

On rend ensuite le message dynamique **à la main** : guillemets doubles et variables.
```groovy
    success {
      httpRequest customHeaders: [[maskValue: false, name: 'Title', value: "inventaire-api ${env.VERSION} : OK"],
                                  [maskValue: false, name: 'Tags', value: 'white_check_mark']],
                  httpMode: 'POST', requestBody: "${currentBuild.fullDisplayName} reussi : ${env.BUILD_URL}",
                  responseHandle: 'NONE', url: env.NTFY_URL, wrapAsMultipart: false
    }
```
Avec `environment { NTFY_URL = 'http://ntfy/inventaire' }` sous `pipeline` (Directive Generator → `environment: Environment` → **Name** `NTFY_URL`, **Value** `http://ntfy/inventaire` ; il génère `NTFY_URL = "http://ntfy/inventaire"`).

Pour ntfy : l'en-tête `Title` donne le titre, `Tags` un émoji (`white_check_mark` ✅, `warning` ⚠️, `x` ❌, `tada` 🎉), `Priority` l'urgence (`high` pour l'échec).

Les trois autres conditions reprennent le même step (voir `corrige/Jenkinsfile`) ; `failure` ajoute `[maskValue: false, name: 'Priority', value: 'high']` et pointe vers `${env.BUILD_URL}console`.

### 9.3 `cleanWs`

**Sample Step** `cleanWs: Delete workspace when build is done` → **Generate Pipeline Script** sans rien remplir → `cleanWs()`. **Où :** dans `cleanup { }`, qui s'exécute **après** toutes les autres conditions : les notifications ont fini d'utiliser le workspace.

### 9.4 Résultat

Console : `HttpMethod: POST`, `URL: http://ntfy/inventaire`, `Response Code: 200`, puis `[WS-CLEANUP] Deleting project workspace...`, `[WS-CLEANUP] done`.

Messages reçus dans l'onglet ntfy pendant les essais :

| Build | Notification |
|---|---|
| `main` #1 | ✅ `inventaire-api 1.2.0 : OK` — `inventaire-api » main #1 - 1.2.0 reussi : …` |
| `feature/alerte` #1 (test faux) | ❌ `inventaire-api : ECHEC` — `… en echec : …/console` |
| `feature/alerte` #2 (test corrigé) | 🎉 `inventaire-api : repare` **et** ✅ `… reussi` |
| `feature/alerte` #3 (seuil 60 %) | ⚠️ `inventaire-api 1.2.0 : instable` |

`fixed` s'ajoute à `success` : deux messages au retour au vert.

**Réponse.** `httpRequest` s'exécute sur le **controller**. L'URL fonctionne parce que le conteneur Jenkins est lui aussi sur le réseau `ci-formation`, où `ntfy` et `inventaire-recette` sont des noms connus. Un controller hors de ce réseau devrait passer par `localhost:8070`… vu depuis sa propre machine.

---

## Bonus — Production avec validation

### Steps générés

| Sample Step | Champs | Texte généré |
|---|---|---|
| `input: Wait for interactive input` | **Message** `Mettre inventaire-api en production ?` ; **Advanced** → **OK Button Caption** `Deployer` | `input message: 'Mettre inventaire-api en production ?', ok: 'Deployer'` |
| `timeout: Enforce time limit` | **Timeout** `10`, **Unit** `MINUTES` (liste sur `NANOSECONDS` au départ) | `timeout(10) {` … `}` |

Directive : `when` → `branch` → `main`, **Evaluate Before Agent**.

### Stage

Voir `corrige/bonus-production.groovy`, à placer dans `stages { }` après `Deploiement recette`. Le message est rendu dynamique (`"… ${env.VERSION} …"`), et `timeout(10)` est écrit `timeout(time: 10, unit: 'MINUTES')` pour être explicite (équivalent).

### Résultat

```
Timeout set to expire in 10 min
Mettre inventaire-api 1.2.0 en production ?
Deployer or Abort
Approved by admin
URL: http://inventaire-prod:8080/actuator/health
Response Code: 200
```
http://localhost:8098/actuator/health → `{"status":"UP"}`. Sans réponse en 10 minutes : build **ABORTED** (aucune des conditions `success`, `unstable` ou `failure` ne s'exécute ; ajouter `aborted { }` pour en être prévenu).

---

## Jenkinsfile final

`corrige/Jenkinsfile`, exécuté en entier sur un Jenkins de test : SUCCESS sur `main` (déploiement et smoke test), FAILURE puis `fixed` sur une branche, UNSTABLE au seuil de 60 %, et bonus validé.

## Erreurs fréquentes

| Symptôme | Cause |
|---|---|
| `./mvnw: Permission denied` | dépôt poussé sans le bit exécutable : utiliser le script d'init, ou `git update-index --chmod=+x mvnw` |
| `No such DSL method 'readMavenPom'` / `'httpRequest'` | plugin Pipeline Utility Steps / HTTP Request absent (exercice 1) |
| `Unknown stage section "sh"` | step collé directement dans le stage au lieu de `steps { }` |
| Option `buildDiscarder` absente du texte généré | case **Discard old builds** du bloc non cochée |
| `sleep` ou `timeout` sans effet | unité restée sur `NANOSECONDS` |
| Stage `Deploiement recette` toujours grisé sur `main` | `DEPLOYER_RECETTE` décoché au lancement, ou condition `branch` sur un job non Multibranch |
| Smoke test en échec, `Connection refused` | application pas encore démarrée (pas de `retry`/`sleep`), ou conteneur hors du réseau `ci-formation` |
| Aucune notification | URL `http://localhost:8070/...` utilisée depuis Jenkins au lieu de `http://ntfy/...` |
