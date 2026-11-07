# TP — Pipeline Maven : de la version au déploiement vérifié (énoncé guidé)

> Durée : 3 h · Prérequis : démos 0 à 10 de la partie 1 (Jenkins, agent `linux-1`, Gitea, credential `gitea-token`)
> Version peu guidée de ce TP : `ENONCE-autonome.md`

## Contexte

L'équipe logistique démarre **inventaire-api**, une API REST de gestion de stock (Java 21, Spring Boot, **Maven**). Vous allez écrire son Jenkinsfile, brique par brique : version lue dans le POM, tests, analyse, déploiement en recette vérifié, notifications sur **ntfy** (un service de notifications push).

**La règle du TP : aucune syntaxe écrite de mémoire.** Chaque step vient du **Snippet Generator**, chaque directive du **Declarative Directive Generator**. Les deux se trouvent dans **Pipeline Syntax** :
- depuis un job Pipeline : menu de gauche → **Pipeline Syntax** ;
- ou directement : http://localhost:8080/pipeline-syntax/ (Snippet Generator) et http://localhost:8080/directive-generator/ (Directive Generator).

Rappel du principe : **Sample Step** (ou **Sample Directive**) → remplir le formulaire → **Generate Pipeline Script** (ou **Generate Declarative Directive**) → copier le texte du cadre → le coller **au bon endroit** du Jenkinsfile. Le générateur ne modifie jamais le job.

| Ce que génère… | Où le coller |
|---|---|
| le **Snippet Generator** (un *step*) | dans `steps { }` d'un stage, ou dans une condition de `post` |
| le **Directive Generator** (une *directive*) | directement sous `pipeline { }`, ou sous un `stage('…') { }` |

## Fourni

Dossier `tp-maven/` du kit :

| Élément | Rôle |
|---|---|
| `inventaire-api/` | Le projet : code, tests unitaires (`*Test.java`) et d'intégration (`*IT.java`), `pom.xml` (JaCoCo, Failsafe, PMD), wrapper `mvnw`, `Dockerfile` |
| `docker-compose.yml` | Le service ntfy, sur le réseau `ci-formation` |
| `init-inventaire-api.ps1` / `.sh` | Crée le dépôt privé `formation/inventaire-api` dans Gitea et y pousse le projet |

| Service | Depuis le poste | Depuis Jenkins |
|---|---|---|
| ntfy (topic `inventaire`) | http://localhost:8070/inventaire | `http://ntfy/inventaire` |
| Recette | http://localhost:8097 | `http://inventaire-recette:8080` |
| Production (bonus) | http://localhost:8098 | `http://inventaire-prod:8080` |

**Conseil :** modifiez le Jenkinsfile directement dans Gitea (fichier → icône crayon **Edit File** → **Commit Changes**), puis lancez **Scan Multibranch Pipeline Now** dans Jenkins (ou configurez le webhook comme à la démo 10). Avant chaque commit, validez le fichier (démo 9, `pipeline-model-converter/validate`).

---

## Exercice 0 — Préparer l'environnement (10 min)

1. La stack du kit tourne (`docker compose up -d` à la racine du kit).
2. Dans un terminal, dans le dossier `tp-maven` :
   ```powershell
   docker compose up -d
   ```
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\init-inventaire-api.ps1
   ```
3. Ouvrir http://localhost:8070/inventaire dans un onglet du navigateur et le laisser ouvert : les notifications y arriveront.

**Résultat attendu :** `Projet pousse : http://localhost:3000/formation/inventaire-api`. Le dépôt contient `pom.xml`, `mvnw`, `Dockerfile`, `src/`… mais pas de `Jenkinsfile`.

---

## Exercice 1 — Installer les plugins (10 min)

1. **Manage Jenkins → Plugins → Installed plugins**. Vérifier la présence de **Lockable Resources plugin** et **Jenkins Workspace Cleanup Plugin** (installés aux démos 1 et 6).
2. **Available plugins** : rechercher et cocher **Pipeline Utility Steps** et **HTTP Request**, puis **Install**.
3. Ouvrir http://localhost:8080/pipeline-syntax/ et dérouler **Sample Step**.

**Résultat attendu :** la liste contient `readMavenPom: Read a maven project file.`, `httpRequest: Perform an HTTP Request and return a response object`, `lock: Lock shared resource` et `cleanWs: Delete workspace when build is done`.

---

## Exercice 2 — Premier Jenkinsfile : build et tests unitaires (25 min)

**Objectif :** un pipeline qui construit le projet, publie les tests et archive le JAR.

1. Dans Gitea, dépôt `formation/inventaire-api` → **Add File → New File** → nom `Jenkinsfile`. Écrire le squelette :
   ```groovy
   pipeline {
     agent { label 'linux' }
     stages {
       stage('Build & tests unitaires') {
         steps {
           // (a) la commande Maven
         }
         post {
           always {
             // (b) publication des rapports de tests
           }
           success {
             // (c) archivage du JAR
           }
         }
       }
     }
   }
   ```
2. **(a)** Snippet Generator → **Sample Step** `sh: Shell Script` → **Shell Script** : `./mvnw -B -ntp clean package` → **Generate Pipeline Script**. Coller le résultat à la place de `// (a)`.
3. **(b)** **Sample Step** `junit: Archive JUnit-formatted test results` → **Test report XMLs** : `target/surefire-reports/*.xml` → **Generate Pipeline Script** → coller à la place de `// (b)`.
4. **(c)** **Sample Step** `archiveArtifacts: Archive the artifacts` → **Files to archive** : `target/*.jar` → **Advanced** → cocher **Fingerprint all archived artifacts** → **Generate Pipeline Script** → coller à la place de `// (c)`.
5. **Commit Changes**.
6. Jenkins → **New Item** → `inventaire-api` → **Multibranch Pipeline** → **Branch Sources** → **Add source** → **Git** : **Project Repository** `http://gitea:3000/formation/inventaire-api.git`, **Credentials** `formation/******` → **Save**.

**Résultat attendu :** le sous-job `main` se construit et passe au vert. Page du build : **Tests** (5 tests, 0 échec), **Build Artifacts** (`inventaire-api-1.2.0.jar`).

> **Questions :** pourquoi `junit` est-il dans `post { always }` et `archiveArtifacts` dans `post { success }` ? Que fait `-ntp` ?

---

## Exercice 3 — La version vient du `pom.xml` (20 min)

**Objectif :** lire la version du projet et l'afficher dans le nom du build.

1. Ajouter **en tête de `stages`** un stage `Version` :
   ```groovy
       stage('Version') {
         steps {
           script {
             def pom = // (d) lecture du pom.xml
             env.VERSION = pom.version
             currentBuild.displayName = "#${env.BUILD_NUMBER} - ${env.VERSION}"
           }
         }
       }
   ```
2. **(d)** Snippet Generator → **Sample Step** `readMavenPom: Read a maven project file.` → **File** : `pom.xml` → **Generate Pipeline Script**. Coller le résultat après `def pom = `.
3. Commit, puis relancer le build.

**Résultat attendu :** l'historique de `main` affiche `#2 - 1.2.0`.

> **Questions :** pourquoi un bloc `script { }` ? Pourquoi écrire `env.VERSION = …` plutôt que `def VERSION = …` ?

---

## Exercice 4 — Tests d'intégration et analyse en parallèle (20 min)

**Objectif :** gagner du temps en lançant deux vérifications indépendantes en même temps.

1. Après le stage `Build & tests unitaires`, ajouter :
   ```groovy
       stage('Verifications') {
         parallel {
           stage('Tests d\'integration') {
             steps {
               // (e) ./mvnw -B -ntp failsafe:integration-test failsafe:verify
             }
             post {
               always {
                 // (f) rapports Failsafe : target/failsafe-reports/*.xml
               }
             }
           }
           stage('Analyse PMD') {
             steps {
               // (g) ./mvnw -B -ntp pmd:pmd pmd:cpd
             }
           }
         }
       }
   ```
2. Générer **(e)** et **(g)** avec `sh`, **(f)** avec `junit`, comme à l'exercice 2.
3. Commit, relancer.

**Résultat attendu :** **Pipeline Overview** montre `Tests d'integration` et `Analyse PMD` côte à côte sous `Verifications`. **Tests** : 7 tests (5 unitaires + 2 d'intégration).

> **Question :** pourquoi ces deux stages peuvent-ils tourner en même temps, mais pas `Build & tests unitaires` avec l'un d'eux ?

---

## Exercice 5 — Seuils de qualité (25 min)

**Objectif :** Jenkins juge le build sur la couverture et les alertes.

1. Après `Verifications`, ajouter un stage `Rapports qualite` avec un bloc `steps { }` vide.
2. **Couverture.** Snippet Generator → **Sample Step** `recordCoverage: Record code coverage results` :
   - **Coverage Parser** : `JaCoCo Coverage Reports` ; **Report File Pattern** : `target/site/jacoco/jacoco.xml` ;
   - **Add Quality Gate** : **Threshold** `50`, **Baseline** `Whole project`, **Metric** `Line Coverage`, **Step or Build Result** `Mark the step and the build as unstable` ;
   - **Generate Pipeline Script** → coller dans `steps`.
3. **Analyse statique.** **Sample Step** `recordIssues: Record compiler warnings and static analysis results` :
   - **Tool** : `PMD`, **Report File Pattern** : `target/pmd.xml` ;
   - **Add Tool** → **Tool** : `CPD`, **Report File Pattern** : `target/cpd.xml` ;
   - **Advanced** (le dernier, en bas du formulaire) → **Add Quality Gate** : **Threshold** `5`, **Type** `Total (any severity)`, **Result** `Mark the step and the build as unstable` ;
   - **Generate Pipeline Script** → coller dans `steps`, sous `recordCoverage`.
4. Commit, relancer. Relever dans la console les lignes `[Coverage]    - [Whole project - Line Coverage]`, `[PMD]    - [Total (any severity)]` et `[CPD]    - [Total (any severity)]`.
5. Créer une branche `feature/seuil` dans Gitea, y passer le seuil de couverture à `60` (les deux nombres de la ligne générée) et observer le build de cette branche.

**Résultat attendu :** sur `main`, `Actual value: 58.33%, Quality gate: 50.00`, 1 alerte PMD, 2 pour CPD ; le menu du build propose **Coverage**, **PMD Warnings** et **CPD Duplications**. Sur `feature/seuil` : build **UNSTABLE** (jaune).

> **Questions :** le texte généré ne contient ni `JACOCO` ni `UNSTABLE`. Pourquoi ? Ouvrez **PMD Warnings** : quelle est l'alerte ?

---

## Exercice 6 — Options et paramètres (15 min)

**Objectif :** encadrer le pipeline et le rendre paramétrable. Cette fois, c'est le **Declarative Directive Generator**.

1. http://localhost:8080/directive-generator/ → **Sample Directive** `options: Options` → **Add** :
   - **buildDiscarder: Discard old builds** → cocher la case **Discard old builds** qui apparaît → **Strategy** `Log Rotation`, **Max # of builds to keep** `10` ;
   - **Add** → **timeout: Enforce time limit** → **Timeout** `20`, **Unit** `MINUTES` ;
   - **Add** → **timestamps: Timestamps** ;
   - **Add** → **disableConcurrentBuilds: Do not allow concurrent builds** → cocher la case **Do not allow concurrent builds** ;
   - **Generate Declarative Directive** → coller **sous `pipeline {`, après `agent`**.
2. **Sample Directive** `parameters: Parameters` → **Add** :
   - **booleanParam: Boolean Parameter** → **Name** `DEPLOYER_RECETTE`, cocher **Set by Default**, **Description** `Deployer en recette apres les tests` ;
   - **Add** → **choice: Choice Parameter** → **Name** `NIVEAU_LOG`, **Choices** `INFO`, `DEBUG`, `WARN` (une valeur par ligne), **Description** `Niveau de log de l application deployee` ;
   - **Generate Declarative Directive** → coller **sous `pipeline {`**, après `options`.
3. Commit, relancer deux fois.

**Résultat attendu :** la console commence par `Timeout set to expire in 20 min` et chaque ligne est horodatée. Le menu de `main` propose **Build with Parameters** avec les deux paramètres.

> **Questions :** que se passe-t-il si l'on oublie de cocher **Discard old builds** dans le bloc ajouté ? Pourquoi **Build with Parameters** n'apparaît-il qu'après un build ?

---

## Exercice 7 — Image Docker et déploiement en recette (25 min)

**Objectif :** déployer la version construite, une seule recette à la fois.

1. Après `Rapports qualite`, ajouter un stage `Image Docker` dont le step (généré avec `sh`) est :
   ```
   docker build --build-arg JAR=target/inventaire-api-$VERSION.jar -t inventaire-api:$VERSION .
   ```
2. Ajouter ensuite un stage `Deploiement recette`. Sa condition : **branche `main`** et **paramètre `DEPLOYER_RECETTE` vrai**.
   - Directive Generator → **Sample Directive** `when: When Condition` → **When Condition** `allOf` → **Add** → `branch` → **Branch pattern** `main` ; cocher **Evaluate Before Agent** → **Generate Declarative Directive**.
   - Coller sous `stage('Deploiement recette') {`, puis **ajouter à la main**, dans `allOf { }`, la ligne `expression { params.DEPLOYER_RECETTE }` (la condition `expression` n'est pas proposée par le générateur).
3. Les steps du stage s'exécutent **sous un verrou**. Snippet Generator → **Sample Step** `lock: Lock shared resource` → **Resource** `recette-inventaire` → **Generate Pipeline Script**. C'est un step à bloc : le coller dans `steps { }` et mettre dans son bloc (à la place de `// some block`) :
   ```groovy
          sh """
            docker rm -f inventaire-recette || true
            docker run -d --name inventaire-recette --network ci-formation -p 8097:8080 \
              -e LOGGING_LEVEL_ROOT=${params.NIVEAU_LOG} inventaire-api:${env.VERSION}
          """
   ```
4. Commit, lancer **Build with Parameters** sur `main`.

**Résultat attendu :** console `Trying to acquire lock on [Resource: recette-inventaire]`, `Lock acquired on [Resource: recette-inventaire]`, puis `Lock released`. http://localhost:8097/actuator/health répond `{"status":"UP"}`. Sur `feature/seuil`, le stage est grisé (`skipped due to when conditional`).

> **Questions :** pourquoi des guillemets **doubles** autour de ce `sh` ? À quoi servirait le verrou si deux branches déployaient sur la même recette ?

---

## Exercice 8 — Smoke test (15 min)

**Objectif :** le pipeline vérifie lui-même que l'application déployée répond.

1. Snippet Generator → **Sample Step** `httpRequest: Perform an HTTP Request and return a response object` :
   - **URL** `http://inventaire-recette:8080/actuator/health` ;
   - **Advanced** → **Response codes expected** `200`, **Response content expected** `UP`, **Response body in console?** `Yes` ;
   - **Generate Pipeline Script**.
2. L'application met quelques secondes à démarrer. Générer aussi :
   - **Sample Step** `retry: Retry the body up to N times` → **Retry Count** `10` ;
   - **Sample Step** `sleep: Sleep` → **Sleep time** `3`, **Unit** `SECONDS` (attention : la liste s'affiche sur `NANOSECONDS`).
3. Dans le bloc du `lock`, après le `sh`, coller le `retry`, et dans son bloc : le `sleep` puis le `httpRequest`.
4. Commit, relancer sur `main`.

**Résultat attendu :** console `Sleeping for 3 sec`, `Response Code: 200`, `{"status":"UP"}`. Testez l’échec : remplacez temporairement l’URL par `http://inventaire-recette:8080/inexistant` ; le build échoue après 10 tentatives (environ 30 s).

---

## Exercice 9 — Notifications ntfy (20 min)

**Objectif :** prévenir l'équipe selon le résultat.

1. Directive Generator → **Sample Directive** `post: Post Stage or Build Conditions` → cocher les cinq conditions suivantes (le formulaire affiche leur description) :
   - `success` : *Run if the build status is "Success" or hasnt been set yet* ;
   - `unstable` : *Run if the build status is "Unstable"* ;
   - `failure` : *Run if the build status is "Failure"* ;
   - `fixed` : *Run if the previous build was not successful and the current builds status is "Success"* ;
   - `cleanup` : *Always run after all other conditions, regardless of build status* ;

   puis **Generate Declarative Directive** → coller **sous `pipeline {`, après le bloc `stages`** (et non dans un stage).
2. Snippet Generator → **Sample Step** `httpRequest` :
   - **URL** `http://ntfy/inventaire`, **HTTP mode** `POST` ;
   - **Advanced** → **Request body** : `Build OK` (à remplacer ensuite) ;
   - **Custom headers** → **Add** : **Header** `Title`, **Value** `inventaire-api` ; **Add** : **Header** `Tags`, **Value** `white_check_mark` ;
   - **Generate Pipeline Script** → coller dans `success { }`.
3. Remplacer la valeur de `requestBody` par `"${currentBuild.fullDisplayName} reussi : ${env.BUILD_URL}"` (guillemets doubles) et le titre par `"inventaire-api ${env.VERSION} : OK"`.
4. Dupliquer pour `unstable` (tag `warning`), `failure` (tag `x`, et un en-tête supplémentaire `Priority` = `high`) et `fixed` (tag `tada`).
5. Dans `cleanup { }` : step `cleanWs: Delete workspace when build is done` (rien à remplir).
6. Commit. Provoquer un échec sur `feature/seuil` (changer un `isEqualTo(3)` en `isEqualTo(4)` dans `StockServiceTest`), puis corriger.

**Résultat attendu :** dans l'onglet ntfy, ✅ à chaque succès, ⚠️ pour l'instable, ❌ pour l'échec, puis 🎉 et ✅ au retour au vert. La console se termine par `[WS-CLEANUP] Deleting project workspace...`.

> **Question :** `httpRequest` s'exécute sur le controller, pas sur l'agent. Pourquoi l'URL `http://ntfy/...` fonctionne-t-elle quand même ?

---

## Bonus — Mise en production avec validation (15 min)

1. Après `Deploiement recette`, un stage `Production` avec `when { branch 'main' }` (Directive Generator).
2. Steps : `input` (Snippet Generator : **Message** `Mettre inventaire-api en production ?`, **Advanced** → **OK Button Caption** `Deployer`) placé dans un `timeout` (**Timeout** `10`, **Unit** `MINUTES`) ; puis le même `docker run` qu'en recette avec le nom `inventaire-prod` et le port `8098` ; puis le smoke test sur `http://inventaire-prod:8080/actuator/health`.

**Résultat attendu :** console `Mettre inventaire-api 1.2.0 en production ?` / `Deployer or Abort`. Après **Deployer** : `Approved by …`, puis `Response Code: 200`. http://localhost:8098/actuator/health répond `UP`.
