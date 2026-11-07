# TP — Chaîne CI d'un projet Gradle, notifiée dans Mattermost

> Durée : 3 h · Prérequis : démos 0 à 10 de la partie 1 (Jenkins, agent `linux-1`, Gitea, credential `gitea-token`, webhook Gitea)

## Contexte

L'équipe démarre un nouveau service, **todo-api** : une API REST de gestion de tâches en Java 21 / Spring Boot. Contrairement à `library-api`, il se construit avec **Gradle** (et non Maven), et l'équipe ne lit pas ses mails : elle veut être prévenue dans sa messagerie, **Mattermost**. Les JAR validés doivent être rangés dans le **registre de paquets de Gitea**, sans passer par Nexus.

Votre mission : construire la chaîne CI complète de ce projet, du premier job à la publication.

| Ce que vous avez déjà vu | Ce qui change dans ce TP |
|---|---|
| Maven, `mvn clean verify` | Gradle, via le wrapper `./gradlew` livré dans le projet |
| Rapport de couverture JaCoCo, SonarQube | Couverture **et** analyse statique (Checkstyle, SpotBugs) lues par Jenkins, avec des **seuils** |
| Notification par mail | Notification dans un canal **Mattermost** |
| Publication dans Nexus | Publication dans **Gitea Packages** |

## Ce qui est fourni

Dossier `tp-gradle/` du kit :

| Élément | Rôle |
|---|---|
| `todo-api/` | Le projet : code, tests, `build.gradle`, wrapper Gradle (`gradlew`, `gradle/wrapper/`), règles Checkstyle |
| `docker-compose.yml` | Le service Mattermost, sur le réseau `ci-formation` du kit |
| `init-todo-api.ps1` / `init-todo-api.sh` | Crée le dépôt privé `formation/todo-api` dans Gitea et y pousse le projet |

Adresses : Jenkins http://localhost:8080 · Gitea http://localhost:3000 · Mattermost http://localhost:8065.
Depuis Jenkins (réseau Docker), les mêmes services s'appellent `http://gitea:3000` et `http://mattermost:8065`.

## Règles du jeu

- Chaque exercice donne un **objectif**, des **indices** et le **résultat attendu**. À vous de trouver les écrans et la syntaxe : la page **Pipeline Syntax** (Snippet Generator, Declarative Directive Generator) est votre meilleure alliée.
- Le Jenkinsfile se construit **au fil des exercices** : chaque exercice ajoute un bloc au précédent.
- Ne copiez pas un Jenkinsfile de `library-api` : les chemins des rapports Gradle sont différents.

---

## Exercice 0 — Préparer l'environnement (10 min)

**Objectif :** Mattermost tourne, et le dépôt `formation/todo-api` existe dans Gitea.

1. La stack du kit doit tourner (`docker compose up -d` à la racine du kit).
2. Dans le dossier `tp-gradle`, démarrer Mattermost :
   ```powershell
   docker compose up -d
   ```
3. Toujours dans `tp-gradle`, créer le dépôt Gitea :
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\init-todo-api.ps1
   ```

**Résultat attendu :** `Projet pousse : http://localhost:3000/formation/todo-api`. Le dépôt contient `build.gradle`, `gradlew`, `src/`… mais **pas encore de Jenkinsfile**.

---

## Exercice 1 — Le canal de l'équipe dans Mattermost (15 min)

**Objectif :** un canal `ci` et une adresse (webhook entrant) par laquelle Jenkins pourra y poster.

- Ouvrir http://localhost:8065 → **View in Browser**. Le premier compte créé devient administrateur : `formation` / `formation@example.com` / `Formation-2026`.
- L'assistant demande le nom de l'organisation : `Formation`. Il crée l'équipe et son canal **Town Square**. Les écrans suivants peuvent être passés (**Skip**, **Finish setup**).
- Créer un canal public `ci`.
- Créer un **Incoming Webhook** rattaché au canal `ci`.

**Indices :** les intégrations sont dans le menu des produits (icône en grille, en haut à gauche) → **Integrations**. Titre du webhook : `jenkins`.

**Résultat attendu :** Mattermost affiche une URL du type `http://localhost:8065/hooks/xxxxxxxxxxxxxxxxxxxxxxxxxx`. Notez-la.

> **Question :** cette URL est-elle utilisable telle quelle par Jenkins ? (Où tourne Jenkins ? Que veut dire `localhost` pour lui ?)

---

## Exercice 2 — Plugins et réglages globaux (15 min)

**Objectif :** Jenkins sait construire du Gradle et parler à Mattermost.

1. Vérifier que le plugin **Gradle** est installé (il fait partie des plugins suggérés de la démo 1). Installer le plugin **Mattermost Notification**.
2. Configurer le serveur Mattermost **une seule fois pour toute l'instance** : **Endpoint** (l'URL du webhook, vue depuis Jenkins) et **Channel** `ci`.
3. Créer un credential pour la publication dans Gitea : un **nouveau jeton Gitea** (compte `formation`), dont la seule permission est **package : Read and Write**. ID du credential : `gitea-packages`.

**Indices :** la section Mattermost se trouve dans **Manage Jenkins → System**. Elle a un bouton pour tester la connexion. Pour le jeton : démo 7, mais une autre ligne de permissions.

**Résultat attendu :** le test de connexion répond `Success`, et le canal `ci` reçoit un message de Jenkins : `Mattermost/Jenkins plugin: you're all set!`.

> **Question :** pourquoi ne pas réutiliser `gitea-token` pour publier ?

---

## Exercice 3 — Premier build Gradle en Freestyle (20 min)

**Objectif :** un job Freestyle `todo-api-freestyle` qui clone le dépôt, lance `clean build` et publie les résultats de tests.

- Le job s'exécute sur un agent `linux`, clone `http://gitea:3000/formation/todo-api.git` (branche `main`) avec le credential `gitea-token`.
- Étape de build : **Invoke Gradle script**, avec le **wrapper** du projet (pas une version de Gradle installée par Jenkins).
- Publier les rapports JUnit écrits par Gradle.

**Indices :** Gradle écrit ses rapports JUnit dans `build/test-results/test/`. Pensez à l'option qui rend `gradlew` exécutable.

**Résultat attendu :** build **SUCCESS** ; la console montre `$ .../gradlew clean build`, au premier build le téléchargement `Downloading https://services.gradle.org/distributions/gradle-8.14.3-bin.zip`, puis `BUILD SUCCESSFUL`. La page du job affiche **Test Result** : 6 tests, 0 échec.

> **Questions :** relancez le build : pourquoi est-il plus rapide ? Quel avantage a le wrapper sur une installation de Gradle déclarée dans **Tools** ?

---

## Exercice 4 — Le Jenkinsfile (25 min)

**Objectif :** la même chaîne, écrite en code dans le dépôt.

1. Ajouter un fichier `Jenkinsfile` à la racine du dépôt `todo-api` (directement dans Gitea : **Add File → New File**, ou depuis un clone).
2. Pipeline déclaratif : agent `linux`, un stage `Build & Test` qui lance `./gradlew --no-daemon clean build`, et la publication des résultats de tests **même si un test échoue**.
3. Créer un job **Pipeline** `todo-api-pipeline` qui lit ce Jenkinsfile depuis Gitea.

**Indices :**
- Snippet Generator : `withGradle: WithGradle` (step à bloc, autour du `sh`) et `junit: Archive JUnit-formatted test results`.
- « Même si un test échoue » : un bloc `post` placé **dans le stage**.
- Validez le Jenkinsfile avant de pousser (démo 9, `pipeline-model-converter/validate`).

**Résultat attendu :** **Pipeline Overview** montre les stages `Declarative: Checkout SCM` et `Build & Test`. La console contient `+ ./gradlew --no-daemon clean build`.

---

## Exercice 5 — Multibranch et webhook (25 min)

**Objectif :** chaque branche du dépôt a son job, et un push déclenche le build dans la seconde.

1. Créer un **Multibranch Pipeline** `todo-api` sur le dépôt (credential `gitea-token`).
2. Déclarer un webhook dans les réglages **du dépôt** `formation/todo-api` (pas ceux du compte), vers l'URL `notifyCommit` de Jenkins, avec les événements **Create**, **Delete** et **Push**. Réutiliser le jeton `notifyCommit` de la démo 10.
3. Créer une branche `feature/compteur` depuis Gitea (ou depuis un clone), avec un commit.

**Résultat attendu :** **Test Delivery** du webhook répond en vert avec `Scheduled indexing of todo-api` ; le sous-job `feature/compteur` apparaît et se construit sans action de votre part.

> **Question :** le job `todo-api-pipeline` de l'exercice 4 se déclenche-t-il aussi ? Pourquoi ?

---

## Exercice 6 — Rapports et seuils de qualité (25 min)

**Objectif :** Jenkins ne se contente pas d'afficher les rapports : il **juge** le build.

1. Dans le `post` du stage `Build & Test`, ajouter :
   - la **couverture** JaCoCo (`build/reports/jacoco/test/jacocoTestReport.xml`), avec un seuil : moins de **70 %** de lignes couvertes rend le build **UNSTABLE** ;
   - l'**analyse statique** Checkstyle (`build/reports/checkstyle/*.xml`) et SpotBugs (`build/reports/spotbugs/*.xml`), avec un seuil : plus de **5** alertes au total rend le build **UNSTABLE**.
2. Pousser. Relever dans la console la couverture de lignes et le nombre d'alertes.
3. Sur la branche `feature/compteur`, monter le seuil de couverture à **80 %**. Constater le résultat.
4. Écrire un test qui ramène la couverture au-dessus de 80 % (le contrôleur a des routes non testées).

**Indices :** Snippet Generator : `recordCoverage: Record code coverage results` et `recordIssues: Record compiler warnings and static analysis results`. Dans les deux formulaires, cherchez **Quality Gates**.

**Résultat attendu :**
- étape 2 : `[Coverage] - [Whole project - Line Coverage]: ≪Success≫ - (Actual value: 75.68%, Quality gate: 70.00)`, 1 alerte Checkstyle, 1 alerte SpotBugs ; la page du build affiche les entrées **Coverage**, **CheckStyle Warnings** et **SpotBugs Warnings** dans son menu ;
- étape 3 : build **UNSTABLE** (jaune), `Some quality gates have been missed: overall result is UNSTABLE` ;
- étape 4 : build de nouveau **SUCCESS**.

> **Questions :** pourquoi Gradle ne s'arrête-t-il pas sur les alertes Checkstyle (regardez `build.gradle`) ? Qui décide du statut du build ?

---

## Exercice 7 — Options et paramètres (15 min)

**Objectif :** encadrer le pipeline.

Ajouter, en utilisant le **Declarative Directive Generator** :
- ne garder que les **10** derniers builds ;
- arrêter tout build qui dépasse **20 minutes** ;
- interdire deux builds simultanés de la même branche ;
- horodater la console ;
- un paramètre booléen `PUBLIER` (faux par défaut) qui servira à l'exercice 9 ;
- une variable `APP_VERSION` valant `1.0.<numéro du build>`, passée à Gradle (`-Pversion=...`).

**Résultat attendu :** le menu du job `main` propose **Build with Parameters** (à partir du deuxième build : pourquoi ?). Le JAR produit s'appelle `todo-api-1.0.<n>.jar`.

---

## Exercice 8 — Notifications Mattermost (20 min)

**Objectif :** l'équipe est prévenue dans `#ci` selon le résultat.

| Situation | Couleur | Contenu |
|---|---|---|
| Build réussi | verte (`good`) | nom du job, numéro, lien vers le build |
| Build instable | orange (`warning`) | idem, en précisant qu'un seuil est dépassé |
| Build en échec | rouge (`danger`) | lien vers la **console** |
| Retour au vert après un échec | verte | « la branche est réparée » |

**Indices :** Snippet Generator : `mattermostSend: Send Mattermost message`. Le serveur et le canal sont déjà réglés globalement (exercice 2) : le step n'a besoin que du message et de la couleur. Les conditions `post` de la démo 13 s'appliquent telles quelles. Mattermost comprend les liens Markdown et le format `<url|texte>`.

**Pour tester :** faites échouer un test sur `feature/compteur` (une assertion fausse), poussez, puis corrigez.

**Résultat attendu :** dans `#ci`, un message rouge puis, au build suivant, deux messages verts (réussite et réparation).

> **Question :** pourquoi `${env.JOB_NAME}` affiche-t-il `todo-api/feature%2Fcompteur` ? Que proposer à la place ? (**Global Variables Reference** → `currentBuild`)

---

## Exercice 9 — Publication dans Gitea Packages (20 min)

**Objectif :** sur `main`, et seulement si `PUBLIER` est coché, publier le JAR dans le registre Maven de Gitea.

- Nouveau stage `Publish`, exécuté **uniquement sur `main` et si `PUBLIER` est vrai**.
- La tâche Gradle est `publish` (inutile de relancer les tests). `build.gradle` lit l'identifiant et le jeton dans les variables d'environnement `GITEA_PKG_USR` et `GITEA_PKG_PSW`.
- Le jeton vient du credential `gitea-packages`.

**Indices :** `environment { GITEA_PKG = credentials('gitea-packages') }` crée **trois** variables (démo 14). `when { allOf { ... } }`.

**Résultat attendu :** **Build with Parameters** → cocher `PUBLIER` → **Build** : la console affiche `> Task :publishMavenPublicationToGiteaRepository` ; http://localhost:3000/formation/-/packages liste `fr.utopios:todo-api` dans la version du build. Sur `feature/compteur`, le stage `Publish` est grisé (`skipped due to when conditional`).

---

## Bonus — Validation humaine avant publication (10 min)

**Objectif :** avant de publier, le pipeline poste dans `#ci` un message « en attente de validation » avec un lien, puis attend qu'une personne clique **Publier**. Sans réponse en 15 minutes, il abandonne.

**Indices :** step `input` (démo 9) dans un step `timeout`. Le lien de validation : `${env.BUILD_URL}input/`.

**Résultat attendu :** le message bleu arrive dans `#ci`, le build attend ; après **Publier**, la console affiche `Approved by ...` puis la publication.

---

## Pour aller plus loin

- Remplacer les deux seuils globaux par des seuils **sur le code nouveau** (option **baseline** des quality gates de Coverage).
- Notifier dans un **autre canal** pour la branche `main` uniquement (paramètre `channel` de `mattermostSend`).
- Passer le seuil d'alertes de **UNSTABLE** à **FAILURE** : quel impact sur les notifications ?
