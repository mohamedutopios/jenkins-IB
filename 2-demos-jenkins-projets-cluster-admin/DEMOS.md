# Démos Jenkins — projets complexes, cluster et administration

Support associé : `2-formation-jenkins-projets-cluster-admin-slides-v1_4.html` (parties 4, 5 et 6).
Fil rouge : la **suite Library**. `library-core` (bibliothèque Maven partagée), `library-portal` (application Jakarta EE en EAR), `library-legacy` (projet Ant), `library-web` (front npm) et `library-api` (l'API de la partie 1), avec les Jenkinsfiles transverses de `library-ops`.

Tout tourne dans des conteneurs Docker sur le poste. La stack de la partie 1 (Jenkins, agent SSH `linux-1`, Gitea, Mailpit, Nexus) est réutilisée telle quelle ; ce kit y ajoute WildFly, un deuxième agent (inbound), un accès Docker pour les agents éphémères, Prometheus et Grafana.

Versions de référence (celles des libellés de ce document) : Jenkins **2.580.2 LTS** (JDK 21), Gitea **1.24.7**, Nexus **3.97.3**, Maven **3.9.16**, WildFly **42.0.0.Final**, Ant **1.10.15**, Node.js **22.12.0**, Prometheus **3.15.1**, Grafana **13.3.0**.

Non démontré, faute de plate-forme dans la stack : les agents **Windows** (slides 29 et 30), l'agent **macOS** sous launchd (slide 42) et le **Kubernetes plugin** (slide 32). La démo 11 montre seulement ce que voit Jenkins quand un label n'est servi par aucun agent.

---

## Sommaire

| Démo | Sujet | Slides | Durée |
|---|---|---|---|
| [0](#démo-0--mettre-la-stack-en-état--fin-de-partie-1-) | Mettre la stack en état « fin de partie 1 » | — | 20 min |
| [1](#démo-1--enchaîner-deux-jobs-freestyle) | Enchaîner deux jobs Freestyle | 4 | 15 min |
| [2](#démo-2--snapshot-release-et-tag-git) | SNAPSHOT, release et tag Git | 6, 16, 18 | 25 min |
| [3](#démo-3--application-jakarta-ee-déployée-sur-wildfly) | Application Jakarta EE déployée sur WildFly | 7 à 9 | 20 min |
| [4](#démo-4--projet-ant) | Projet Ant | 10, 11 | 10 min |
| [5](#démo-5--pipeline-orchestrateur) | Pipeline orchestrateur | 5 | 15 min |
| [6](#démo-6--pipeline-multi-outils-maven--npm--docker) | Pipeline multi-outils Maven + npm + Docker | 12 à 14 | 20 min |
| [7](#démo-7--shared-library) | Shared Library | 15 | 15 min |
| [8](#démo-8--chaîne-de-promotion-cd) | Chaîne de promotion CD | 19 à 22 | 30 min |
| [9](#démo-9--agent-inbound-en-websocket) | Agent inbound en WebSocket | 25 à 28 | 15 min |
| [10](#démo-10--agents-docker-éphémères) | Agents Docker éphémères | 31 | 20 min |
| [11](#démo-11--labels-parallélisme-et-file-dattente) | Labels, parallélisme et file d'attente | 33 à 35 | 15 min |
| [12](#démo-12--vues) | Vues | 40, 41 | 15 min |
| [13](#démo-13--visite-de-jenkins_home) | Visite de JENKINS_HOME | 44 à 46 | 15 min |
| [14](#démo-14--supervision--prometheus-grafana-job-de-supervision) | Supervision : Prometheus, Grafana, job de supervision | 47 à 49 | 25 min |
| [15](#démo-15--sauvegarde-et-restauration) | Sauvegarde et restauration | 50 à 52 | 15 min |
| [16](#démo-16--groovy--script-console-initgroovyd-job-dsl) | Groovy : Script Console, init.groovy.d, Job DSL | 53 à 56 | 25 min |
| [17](#démo-17--cli-api-rest-et-configuration-as-code) | CLI, API REST et Configuration as Code | 57 à 60 | 20 min |
| [18](#démo-18--annuaire-ldap--les-comptes-hors-de-jenkins) | Annuaire LDAP : les comptes hors de Jenkins | — | 30 min |

Les démos s'enchaînent : chacune part de l'état laissé par la précédente. Les démos 1 à 8 correspondent à la partie 4 du support, 9 à 11 à la partie 5, 12 à 17 à la partie 6. La démo 18 complète la partie 6 ; elle n'a pas de slide.

---

## Contenu du kit

```
2-demos-jenkins-projets-cluster-admin/
├── DEMOS.md                    ce document
├── POINTS-DE-VIGILANCE.md      pièges relevés en déroulant les démos
├── docker-compose.yml          wildfly ; linux-2 et docker-proxy (profil cluster) ;
│                               prometheus et grafana (profil monitoring) ; lldap (profil annuaire)
├── .env                        ports, compte WildFly, secret de l'agent linux-2, compte de l'annuaire
├── annuaire/                   démo 18 : personnes et groupes de l'annuaire (utilisateurs/, groupes/),
│                               jenkins-ldap.yaml et retour-base-locale.yaml (JCasC)
├── agent-docker-maven/         image des agents éphémères : jenkins/agent + Maven 3.9.16
├── prometheus/prometheus.yml   collecte de http://jenkins:8080/prometheus/
├── scripts/
│   ├── etat-partie1.sh         met un Jenkins vierge dans l'état « fin de partie 1 »
│   ├── etat/                   plugins et script Groovy utilisés par etat-partie1.sh
│   ├── init-depots.sh          crée les 6 dépôts Gitea de la partie 2 et y pousse projets/
│   ├── sauvegarde.sh           sauvegarde de JENKINS_HOME (démo 15)
│   ├── restaurer.sh            restauration dans un second Jenkins (démo 15)
│   └── init.groovy.d/          script de démarrage d'exemple (démo 16)
└── projets/
    ├── library-core/           JAR Maven, version ${revision}, publié dans Nexus
    ├── library-portal/         EAR Jakarta EE 10 : portal-ejb, portal-web, portal-ear
    ├── library-legacy/         projet Ant (build.xml, lib/ JUnit 4)
    ├── library-web/            front Node.js sans dépendance (node --test)
    ├── jenkins-shared-lib/     Shared Library utopios-ci (vars/ et src/)
    └── library-ops/            Jenkinsfiles transverses (ci/) et seed Job DSL (seed/)
```

Le kit de la partie 1 doit se trouver à côté, dans `../1-demos-jenkins-ci` : `etat-partie1.sh` et `init-depots.sh` lisent son `.env` et lancent sa stack.

## Adresses de la stack

| Service | Depuis le navigateur | Depuis les conteneurs | Compte |
|---|---|---|---|
| Jenkins | http://localhost:8080 | http://jenkins:8080 | `admin` / `Formation-2026` |
| Gitea | http://localhost:3000 | http://gitea:3000 | `formation` / `Formation-2026` |
| Mailpit | http://localhost:8025 | SMTP `mailpit:1025` | aucun |
| Nexus | http://localhost:8081 | http://nexus:8081 | `admin` / `Formation-2026` ; `jenkins` / `Jenkins-2026` (publication) |
| WildFly (application) | http://localhost:8180 | http://wildfly:8080 | aucun |
| WildFly (console d'administration) | http://localhost:9990 | http://wildfly:9990 | `admin` / `Formation-2026` |
| Prometheus | http://localhost:9091 | http://prometheus:9090 | aucun |
| Grafana | http://localhost:3001 | http://grafana:3000 | `admin` / `Formation-2026` |
| library-api dev / recette / prod (démo 8) | http://localhost:8092, 8093, 8094 | `library-api-dev:8080`… | aucun |
| LLDAP (annuaire, démo 18) | http://localhost:17170 | LDAP `ldap://lldap:3890` | `annuaire-admin` / `Annuaire-2026` ; personnes : voir démo 18 |

Ces mots de passe sont des valeurs de formation, propres à cette stack locale.

---

## Démo 0 — Mettre la stack en état « fin de partie 1 »

> Durée : 20 min (plus les téléchargements) · Prérequis : kit de la partie 1 dans `../1-demos-jenkins-ci`, Docker Desktop avec 8 Go de RAM, accès Internet (plugins, dépendances Maven, Node.js, Ant)

**Pourquoi.** La partie 2 suppose un Jenkins déjà configuré : administrateur, agent SSH, Maven, credentials Gitea et Nexus, SMTP, `settings.xml` géré. Rejouer les 18 démos de la partie 1 avant chaque session n'a pas de sens ; `etat-partie1.sh` reproduit cet état en une commande, à partir d'un Jenkins vierge. Les projets de la partie 2 sont ensuite poussés dans Gitea, et les plugins propres à la partie 2 s'installent depuis l'UI.

**Ce qu'elle montre.** Une plate-forme prête : Jenkins configuré, six dépôts privés dans Gitea, Nexus qui contient déjà deux releases de `library-api` (entrée de la démo 8), WildFly démarré, et les plugins de la partie 2 installés.

### Étapes

1. Ouvrir un terminal dans le dossier du kit :

   ```bash
   cd 2-demos-jenkins-projets-cluster-admin
   ```

2. Vérifier que les ports sont libres (ceux de la partie 1 et ceux de ce kit) :

   ```bash
   lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8080|3000|8025|8081|8180|9990|9091|3001|8092|8093|8094) '
   ```

   Les ports 8180, 9990, 9091 et 3001 se changent dans `.env` ; ceux de la partie 1 dans `../1-demos-jenkins-ci/.env`.

3. Lancer la mise en état :

   ```bash
   ./scripts/etat-partie1.sh
   ```

   Le script démarre la stack de la partie 1 (Jenkins, linux-1, Gitea, Mailpit, Nexus), crée le dépôt `library-api`, installe les plugins de la partie 1, applique la configuration par un script `init.groovy.d` (voir démo 16), puis configure Nexus.

   **Contrat de licence Nexus.** Un Nexus neuf refuse toute publication (HTTP 403) tant que le contrat de licence de la Community Edition n'est pas accepté. Le script s'arrête alors avec le message `Le contrat de licence Nexus Community Edition n'est pas accepte`. Deux possibilités, après lecture du contrat (https://links.sonatype.com/products/nxrm/ce-eula) :
   - l'accepter dans l'assistant de http://localhost:8081 (compte `admin` / `Formation-2026`), puis relancer `./scripts/etat-partie1.sh` ;
   - ou relancer le script en l'acceptant explicitement :

     ```bash
     ACCEPTER_EULA_NEXUS=oui ./scripts/etat-partie1.sh
     ```

   Résultat attendu, en fin de script : `Etat fin de partie 1 pret : http://localhost:8080 (admin / Formation-2026)`. Relancé, le script ne retouche pas Jenkins (`Jenkins deja mis en etat : rien a faire`).

4. Créer les dépôts de la partie 2 dans Gitea :

   ```bash
   ./scripts/init-depots.sh
   ```

   Résultat : six lignes `Depot pousse : http://localhost:3000/formation/<dépôt>` pour `library-core`, `library-portal`, `library-legacy`, `library-web`, `jenkins-shared-lib` et `library-ops`.

5. Démarrer WildFly et construire l'image des agents éphémères (utilisée à la démo 10) :

   ```bash
   docker compose up -d wildfly
   ```

   ```bash
   docker build -t formation/jenkins-agent-maven:jdk21 agent-docker-maven
   ```

6. Ouvrir **http://localhost:8080** et se connecter en `admin` / `Formation-2026`. Contrôler l'état :
   - le bandeau **Jenkins de formation - demos library (partie 2)** s'affiche en haut du tableau de bord ;
   - **Manage Jenkins → Nodes** : **Built-In Node** (0 executor) et **linux-1** en ligne ;
   - **Manage Jenkins → Credentials** : `agent-ssh-key`, `gitea-token` (`formation/****** (Gitea - jeton lecture)`) et `nexus-deploy` (`jenkins/****** (Nexus - publication Maven)`) ;
   - **Manage Jenkins → Managed files** : `nexus-settings` sous **Maven settings.xml**.

**Plugins de la partie 2**

7. **Manage Jenkins → Plugins → Available plugins**. Pour chaque ligne du tableau, saisir le nom dans **Search available plugins** puis cocher la case **Install** de la ligne exacte :

   | Plugin à cocher | Sert à | Démo |
   |---|---|---|
   | **Copy Artifact** | build step **Copy artifacts from another project**, step `copyArtifacts` | 1, 5 |
   | **NodeJS** | outil `nodejs 'node-22'` | 6 |
   | **Docker** | cloud d'agents Docker éphémères | 10 |
   | **Build Monitor View** | vue « radiateur » | 12 |
   | **Prometheus metrics** | endpoint `/prometheus/` | 14 |
   | **Job DSL** | seed job | 16 |
   | **Configuration as Code** | export YAML de la configuration | 17 |

   La recherche `docker` renvoie plusieurs plugins : prendre celui qui s'appelle simplement **Docker** (Docker plugin), pas **Docker Pipeline** ni **Docker Commons**.

8. Cliquer **Install**. Attendre la fin de **Download progress** (tous les plugins en **Success**). Si la page propose un redémarrage, cocher **Restart Jenkins when installation is complete and no jobs are running**.

**Dossier des jobs**

9. **Dashboard → New Item** → `library` → **Folder** → **OK** → **Description** : `Suite Library (partie 2)` → **Save**. Tous les jobs des démos 1 à 11 sont créés dans ce dossier.

> **Point clé.** `etat-partie1.sh` ne remplace pas la partie 1 : il produit le même état final, sans l'historique (pas de jobs `library-api`, pas de rôles). La configuration qu'il applique est lisible dans `scripts/etat/etat-partie1.groovy` : c'est un exemple concret de configuration de Jenkins par script (slide 55).

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| Le script s'arrête sur le contrat de licence Nexus | EULA non acceptée (comportement normal) | Voir l'étape 3 |
| `ECHEC de la configuration Jenkins` | Plugin absent ou téléchargement interrompu | `docker logs jenkins \| grep -A5 'Failed to run script'` ; `docker compose down -v` dans `../1-demos-jenkins-ci` puis relancer |
| L'installation des plugins reste bloquée sur un téléchargement | Réseau lent ou coupé | Attendre, sinon relancer le script : les plugins déjà présents ne sont pas retéléchargés |
| `init-depots.sh` échoue en `401` | Gitea pas encore initialisé par `etat-partie1.sh` | Relancer après la fin de `etat-partie1.sh` |

---

## Démo 1 — Enchaîner deux jobs Freestyle

> Slides : 4 · Durée : 15 min · Prérequis : démo 0

**Pourquoi.** Quand `library-core` change, ce qui en dépend doit être reconstruit. Le mécanisme le plus ancien de Jenkins est l'enchaînement de jobs Freestyle : un job amont déclenche un job aval (slide 4). On le monte ici avec un job aval qui récupère le JAR produit par le job amont : c'est la situation où Jenkins sait relier précisément « quel build amont a servi à quel build aval ».

**Ce qu'elle montre.** **Build other projects**, la cause `Started by upstream project`, la copie d'artefact entre jobs, les sections **Upstream Projects** / **Downstream Projects** de la page d'un job et la page **Project Relationship**.

### Étapes

**Job amont**

1. Dossier `library` → **New Item** → `library-core-freestyle` → **Freestyle project** → **OK**.
2. **General** :
   - **Description** : `library-core en Freestyle (projet amont)`
   - cocher **Restrict where this project can be run** → **Label Expression** : `linux`
3. **Source Code Management** → **Git** :
   - **Repository URL** : `http://gitea:3000/formation/library-core.git`
   - **Credentials** : `formation/****** (Gitea - jeton lecture)`
   - **Branch Specifier** : `*/main`
4. **Build Steps** → **Add build step** → **Invoke top-level Maven targets** → **Maven Version** : `maven-3.9`, **Goals** : `-B -ntp clean verify`.
5. **Post-build Actions** :
   - **Add post-build action** → **Publish JUnit test result report** → **Test report XMLs** : `target/surefire-reports/*.xml`
   - **Add post-build action** → **Archive the artifacts** → **Files to archive** : `target/*.jar`
6. **Save** → **Build Now**. Le premier build télécharge les dépendances Maven (quelques dizaines de secondes). Résultat : build #1 vert, **Build Artifacts** contient `library-core-2.3.0-SNAPSHOT.jar`.

**Job aval**

7. Dossier `library` → **New Item** → `library-api-aval` → **Freestyle project** → **OK**.
8. **General** → cocher **Restrict where this project can be run** → **Label Expression** : `linux`.
9. **Build Steps** → **Add build step** → **Copy artifacts from another project** :
   - **Project name** : `library-core-freestyle`
   - **Which build** : `Upstream build that triggered this job`
   - **Artifacts to copy** : `target/*.jar`
   - **Target directory** : `libs`
   - cocher **Flatten directories** (laisser **Fingerprint Artifacts** coché)
10. **Add build step** → **Execute shell** → **Command** : `ls -l libs/`
11. **Save**. Ne pas lancer ce job à la main : sans build amont déclencheur, **Upstream build that triggered this job** ne trouve rien à copier.

**Relier les deux jobs (côté amont)**

12. `library » library-core-freestyle` → **Configure** :
    - **General** → cocher **Permission to Copy Artifact** → **Projects to allow copy artifacts** : `library-api-aval`
    - **Post-build Actions** → **Add post-build action** → **Build other projects** → **Projects to build** : `library-api-aval`, laisser **Trigger only if build is stable**

    **Save**.

**Déclencher et observer**

13. `library-core-freestyle` → **Build Now**.

    Résultat dans la console du job amont : `Archiving artifacts`, puis `Triggering a new build of library » library-api-aval`, puis `Finished: SUCCESS`.

14. Ouvrir le build #1 de `library-api-aval` → **Console Output** :

    ```
    Started by upstream project "library/library-core-freestyle" build number 2
    originally caused by:
     Started by user Administrateur Jenkins
    ...
    Copied 1 artifact from "library » library-core-freestyle" build number 2
    + ls -l libs/
    -rw-rw-r-- 1 jenkins jenkins 2891 ... library-core-2.3.0-SNAPSHOT.jar
    Finished: SUCCESS
    ```

15. Page du job `library-core-freestyle` : une section **Downstream Projects** liste `library » library-api-aval`. Page de `library-api-aval` : section **Upstream Projects** avec `library » library-core-freestyle`. Page du build #1 de `library-api-aval` : bloc **Upstream Builds** → `library-core-freestyle #2`.
16. Tableau de bord → menu de gauche **Project Relationship** → **upstream project** : `library/library-core-freestyle`, **downstream project** : `library/library-api-aval` → **Compare**. Le tableau associe le build amont #2 au build aval #1 qui a utilisé son JAR. Cette correspondance repose sur les empreintes (*fingerprints*) prises lors de la copie.

> **Point clé.** L'autre sens de configuration existe : côté aval, **Triggers → Build after other projects are built** → **Projects to watch** : `library-core-freestyle`. L'effet est le même ; le lien est simplement déclaré dans l'autre job. Dans les deux cas la logique est dispersée dans les configurations : au-delà de trois ou quatre jobs, un pipeline orchestrateur (démo 5) est plus lisible.

> **À retenir.** Les sections **Upstream Projects** / **Downstream Projects** ne connaissent que les liens entre jobs Freestyle (ou Maven project). Un job Pipeline déclenché par **Build other projects** démarre bien (cause `Started by upstream project`), mais n'apparaît pas dans ces sections.

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| `Unable to find project for artifact copy: library-core-freestyle` | Permission de copie absente côté amont | Cocher **Permission to Copy Artifact** dans `library-core-freestyle` (étape 12) |
| `ERROR: Unable to find a build for artifact copy from: library-core-freestyle` | `library-api-aval` lancé à la main : aucun build amont déclencheur | Le lancer par `library-core-freestyle` (étape 13) |

---

## Démo 2 — SNAPSHOT, release et tag Git

> Slides : 6, 16, 18 · Durée : 25 min · Prérequis : démo 0

**Pourquoi.** `library-core` est consommée par d'autres projets : elle doit être publiée dans un dépôt d'artefacts, pas copiée de workspace en workspace (slide 5, encadré « Préférer le dépôt d'artefacts »). La slide 16 distingue la **SNAPSHOT** (version en cours, republiable à volonté) de la **release** (immuable). Avec les versions CI-friendly (`${revision}`), c'est le pipeline qui choisit la version : SNAPSHOT depuis `main`, release depuis un tag Git `v2.3.0`.

**Ce qu'elle montre.** Un Multibranch qui découvre branches **et** tags, la SNAPSHOT horodatée dans `maven-snapshots`, un tag qui n'est pas construit automatiquement, la release dans `maven-releases`, et le refus de Nexus quand on republie une release.

### Étapes

1. Lire `projets/library-core/Jenkinsfile` :
   - `env.REVISION = env.TAG_NAME ? env.TAG_NAME.replaceFirst(/^v/, '') : '2.3.0-SNAPSHOT'` : un build de tag `v2.3.0` publie `2.3.0`, un build de branche publie `2.3.0-SNAPSHOT` ;
   - stage **Publish** : `when { anyOf { branch 'main'; buildingTag() } }`, puis `mvn deploy` avec le `settings.xml` géré `nexus-settings` et le credential `nexus-deploy` ;
   - `options { copyArtifactPermission('library/*') }` : autorise les jobs du dossier `library` à copier ses artefacts (utilisé à la démo 5).

**Créer le Multibranch**

2. Dossier `library` → **New Item** → `library-core` → **Multibranch Pipeline** → **OK**.
3. **Branch Sources** → **Add source** → **Git** :
   - **Project Repository** : `http://gitea:3000/formation/library-core.git`
   - **Credentials** : `formation/****** (Gitea - jeton lecture)`
   - **Behaviours** : **Discover branches** est déjà présent ; cliquer **Add** → **Discover tags**
4. **Build Configuration** → **Mode** : `by Jenkinsfile`, **Script Path** : `Jenkinsfile` → **Save**.

   Résultat : le **Scan Multibranch Pipeline Log** trouve `main`, le sous-job **main** se construit.

5. Ouvrir `library » library-core » main` → dernier build : il s'affiche `#1 2.3.0-SNAPSHOT` (nom posé par `currentBuild.displayName`) ; les stages **Version**, **Build & Test** et **Publish** sont verts.

**La SNAPSHOT dans Nexus**

6. http://localhost:8081 → se connecter (`admin` / `Formation-2026`) → **Browse** → `maven-snapshots` → `fr` → `utopios` → `library-core` → `2.3.0-SNAPSHOT`. Le JAR est stocké sous un nom horodaté, par exemple `library-core-2.3.0-20261101.113828-1.jar`, accompagné de `maven-metadata.xml`. Relancer **Build Now** sur `main` : un second fichier `...-2.jar` apparaît. Une SNAPSHOT se republie autant de fois qu'on veut ; les consommateurs reçoivent la plus récente.

**Le tag de release**

7. Gitea → dépôt `formation/library-core` → bouton de branche (**main** ▾) → onglet **Tags** → dans le champ de filtre, saisir `v2.3.0` → cliquer **Create tag v2.3.0** (*from "main"*).
8. Jenkins → `library » library-core` → **Scan Multibranch Pipeline Now** → **Scan Multibranch Pipeline Log** :

   ```
   Checking tags...
     Checking tag v2.3.0
   No automatic build triggered for v2.3.0
   Processed 1 tags
   ```

   Un onglet **Tags** apparaît à côté de **Branches**. Le tag est découvert mais **pas construit** : Jenkins évite de lancer d'un coup tous les tags anciens d'un dépôt. La release est un acte volontaire.

9. Onglet **Tags** → `v2.3.0` → **Build Now**. Le build s'affiche `#1 2.3.0`.

   Résultat dans Nexus : `maven-releases` → `fr/utopios/library-core/2.3.0/library-core-2.3.0.jar` (nom sans horodatage).

10. Relancer **Build Now** sur `v2.3.0`. Le build échoue au stage **Publish** :

    ```
    [ERROR] Failed to execute goal org.apache.maven.plugins:maven-deploy-plugin:3.1.4:deploy (default-deploy) on project library-core:
    Failed to deploy artifacts: Could not transfer artifact fr.utopios:library-core:pom:2.3.0 from/to nexus-releases (...):
    status code: 409, reason phrase: ... cannot be updated as asset already exists and redeploy is not allowed (409)
    ```

    C'est la politique **Deployment policy : Disable redeploy** du dépôt `maven-releases` (slide 18) : une release publiée ne change plus.

> **Point clé.** La slide 17 présente `maven-release-plugin`, qui modifie le POM, commite et pose le tag depuis Jenkins. Les versions CI-friendly montrées ici évitent ces commits techniques : le tag est posé par une personne (ou un outil de release), et le pipeline en déduit la version.

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| Pas d'onglet **Tags** après le scan | **Discover tags** non ajouté | **Configure** → **Behaviours** → **Add** → **Discover tags** → **Save** → nouveau scan |
| `status code: 403` au stage **Publish** | Contrat de licence Nexus non accepté | Démo 0, étape 3 |
| `status code: 401` | Credential `nexus-deploy` erroné | Vérifier `jenkins` / `Jenkins-2026` dans **Manage Jenkins → Credentials** |

---

## Démo 3 — Application Jakarta EE déployée sur WildFly

> Slides : 7 à 9 · Durée : 20 min · Prérequis : démo 2 (SNAPSHOT de `library-core` dans Nexus), WildFly démarré (démo 0, étape 5)

**Pourquoi.** Une application Jakarta EE complète se livre en **EAR** : un module EJB (métier), un module WAR (web), assemblés par un module EAR (slide 7). Maven construit les trois dans l'ordre grâce au *reactor* (slide 8), et le plugin `wildfly-maven-plugin` déploie l'EAR sur le serveur (slide 9). `library-portal` dépend de `library-core` : la SNAPSHOT publiée à la démo 2 est lue dans Nexus.

**Ce qu'elle montre.** Le *Reactor Summary* sur quatre modules, la dépendance SNAPSHOT résolue par Nexus, un déploiement par l'API de management de WildFly avec un credential Jenkins, et un test de fumée après déploiement.

### Étapes

1. Parcourir `projets/library-portal/` :
   - `pom.xml` (parent, `packaging pom`) : modules `portal-ejb`, `portal-web`, `portal-ear` ; dépôt `nexus-public` pour lire les SNAPSHOT ; `jakarta.jakartaee-api` 10.0.0 en `provided` ;
   - `portal-ejb` : `LoanServiceBean` (`@Stateless`) délègue à `LoanRules` de `library-core` ;
   - `portal-web` : `PortalResource` (JAX-RS) expose `/api/health` et `/api/loans/check` ;
   - `portal-ear/pom.xml` : `contextRoot` `/library`, `library-core` dans `lib/`, `wildfly-maven-plugin` 6.2.0.Final avec `${env.WF_USR}` / `${env.WF_PSW}`.

**Credential WildFly**

2. **Manage Jenkins → Credentials** → **Add Credentials** → **Username with password** → **Next** :

   | Champ | Valeur |
   |---|---|
   | **Username** | `admin` |
   | **Password** | `Formation-2026` |
   | **ID** | `wildfly-admin` |
   | **Description** | `WildFly - management` |

   **Create**.

**Job Multibranch**

3. Dossier `library` → **New Item** → `library-portal` → **Multibranch Pipeline** → **OK** → **Branch Sources** → **Add source** → **Git** → **Project Repository** : `http://gitea:3000/formation/library-portal.git`, **Credentials** : `formation/****** (Gitea - jeton lecture)` → **Save**.
4. Le sous-job **main** se construit. Console du stage **Build EAR** :

   ```
   [INFO] Reactor Summary for library-portal 1.0.0-SNAPSHOT:
   [INFO] library-portal ..................................... SUCCESS
   [INFO] portal-ejb ......................................... SUCCESS
   [INFO] portal-web ......................................... SUCCESS
   [INFO] portal-ear ......................................... SUCCESS
   [INFO] BUILD SUCCESS
   ```

   Le stage **Deploy recette** lance `mvn ... -pl portal-ear wildfly:deploy` (`--- wildfly:6.2.0.Final:deploy (default-cli) @ portal-ear ---`), puis le test de fumée affiche `{"status":"UP"}`.

5. Page du build : **Build Artifacts** contient `portal-ear-1.0.0-SNAPSHOT.ear` ; **Tests** : les tests de `portal-ejb`.

**Vérifier le déploiement**

6. Dans le navigateur :
   - http://localhost:8180/library/api/health → `{"status":"UP"}`
   - http://localhost:8180/library/api/loans/check?current=2&copies=1 → `{"canBorrow":true}`
   - http://localhost:8180/library/api/loans/check?current=6&copies=1 → `{"canBorrow":false}` (règle `MAX_LOANS = 5` de `library-core`)
7. Console WildFly http://localhost:9990 (`admin` / `Formation-2026`) → **Deployments** : `library-portal.ear` est actif.

> **Point clé.** Le mot de passe de management n'apparaît ni dans le POM ni dans le Jenkinsfile : `environment { WF = credentials('wildfly-admin') }` crée `WF_USR` et `WF_PSW`, que le POM lit par `${env.WF_USR}`. La slide 9 mentionne aussi les tests d'intégration avec Testcontainers ; ils ne sont pas joués ici (il faudrait un Docker accessible depuis le conteneur de build Maven).

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| `Could not find artifact fr.utopios:library-core:jar:2.3.0-SNAPSHOT` | Démo 2 non faite (rien dans `maven-snapshots`) | Construire `library » library-core » main` |
| `WFLYCTL0216` ou `Connection refused` sur 9990 | WildFly arrêté | `docker compose up -d wildfly` |
| Le test de fumée échoue, `docker logs wildfly` montre `WELD-001303 No active contexts for RequestScoped` | Ressource JAX-RS sans portée CDI | Garder `@RequestScoped` sur `PortalResource` et `beans.xml` dans `WEB-INF` (déjà le cas dans le kit) |
| Le premier build échoue au téléchargement de Maven (`ERROR: ... apache-maven-3.9.16-bin.zip`) | Deux builds installent Maven en même temps sur un agent neuf | Relancer le build |

---

## Démo 4 — Projet Ant

> Slides : 10, 11 · Durée : 10 min · Prérequis : démo 0

**Pourquoi.** Beaucoup de projets anciens se construisent encore avec Ant : pas de gestion de dépendances, des JAR versionnés dans `lib/`, des cibles écrites à la main (slide 10). Jenkins s'en accommode comme de Maven : un outil déclaré dans **Tools**, installé automatiquement sur l'agent, et des rapports JUnit XML (slide 11).

**Ce qu'elle montre.** L'installation automatique d'Ant depuis Apache, `tools { ant 'ant-1.10' }`, et la publication des tests et du JAR d'un build Ant.

### Étapes

1. Lire `projets/library-legacy/build.xml` : cibles `clean`, `compile`, `test` (JUnit 4, rapport XML dans `build/test-reports`) et `dist` (JAR `dist/library-legacy-${version}.jar`). Les bibliothèques de test sont versionnées dans `lib/`.
2. **Manage Jenkins → Tools** → section **Ant installations** → **Add Ant** :
   - **Name** : `ant-1.10`
   - **Install automatically** coché → **Install from Apache** → **Version** : `1.10.15`

   **Save**. (La liste propose d'abord la version la plus récente ; les libellés ci-dessous correspondent à 1.10.15.)

3. Dossier `library` → **New Item** → `library-legacy` → **Pipeline** → **OK** → **Pipeline** → **Definition** : **Pipeline script from SCM** :
   - **SCM** : `Git`
   - **Repository URL** : `http://gitea:3000/formation/library-legacy.git`
   - **Credentials** : `formation/****** (Gitea - jeton lecture)`
   - **Branch Specifier** : `*/main`
   - **Script Path** : `Jenkinsfile`

   **Save** → **Build Now**.

4. Console :

   ```
   Unpacking https://archive.apache.org/dist/ant/binaries/apache-ant-1.10.15-bin.zip to /home/jenkins/agent/tools/hudson.tasks.Ant_AntInstallation/ant-1.10 on linux-1
   + ant -version
   Apache Ant(TM) version 1.10.15 compiled on August 25 2024
   ...
       [junit] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
         [jar] Building jar: .../dist/library-legacy-1.0.1.jar
   BUILD SUCCESSFUL
   ```

   La ligne `Unpacking` n'apparaît qu'au premier build sur un agent donné. La page du build affiche **Tests** (3 tests) et **Build Artifacts** (`library-legacy-1.0.1.jar` : la version vient de `LEGACY_VERSION = "1.0.${BUILD_NUMBER}"`).

> **Point clé.** Publier ce JAR dans Nexus (slide 11 : Nexus Uploader ou `mvn deploy:deploy-file`) suit la même logique qu'à la démo 2. La migration progressive consiste à ajouter un `pom.xml` à côté du `build.xml`, sans tout réécrire d'un coup.

---

## Démo 5 — Pipeline orchestrateur

> Slides : 5 · Durée : 15 min · Prérequis : démos 2, 3 et 4

**Pourquoi.** Les liens Freestyle de la démo 1 sont dispersés dans chaque job. La slide 5 les remplace par un pipeline orchestrateur : un seul Jenkinsfile décide de l'ordre, du parallélisme et de la conduite à tenir quand un projet échoue, avec le step `build job:`.

**Ce qu'elle montre.** `build job:` sur un sous-job Multibranch (`library/library-core/main`), `parallel`, `propagate: false` pour décider soi-même, `copyArtifacts` d'un build précis, et `agent none` pour ne pas occuper d'executor pendant l'attente.

### Étapes

1. Lire `projets/library-ops/ci/orchestrateur.Jenkinsfile` :
   - stage **Suite Library** en `parallel` : **core** lance `library/library-core/main` (`wait: true, propagate: true`) et mémorise son numéro dans `env.CORE_BUILD` ; **legacy** lance `library/library-legacy` avec `propagate: false` et passe le pipeline en `UNSTABLE` si le résultat n'est pas `SUCCESS` ;
   - stage **Fetch core jar** : `copyArtifacts` du build `specific("${env.CORE_BUILD}")` ;
   - stage **Portal** : `build job: 'library/library-portal/main'`.
2. Dossier `library` → **New Item** → `orchestrateur` → **Pipeline** → **OK** → **Pipeline script from SCM** : dépôt `http://gitea:3000/formation/library-ops.git`, **Credentials** `formation/****** (Gitea - jeton lecture)`, **Branch Specifier** `*/main`, **Script Path** `ci/orchestrateur.Jenkinsfile` → **Save** → **Build Now**.
3. Console de l'orchestrateur :

   ```
   Scheduling project: library » library-core » main
   Scheduling project: library » library-legacy
   Starting building: library » library-legacy #2
   Starting building: library » library-core » main #3
   Build library » library-legacy #2 completed: SUCCESS
   library-legacy #2 : SUCCESS
   library-core #3 : SUCCESS
   Copied 1 artifact from "library » library-core » main" build number 3
   + ls -l libs/
   ...
   Scheduling project: library » library-portal » main
   Starting building: library » library-portal » main #2
   Finished: SUCCESS
   ```

   Les numéros de build dépendent des démos précédentes, et l'ordre des lignes des deux branches parallèles peut varier. Les lignes **Starting building** sont des liens vers les builds lancés.

4. Ouvrir le build de `library » library-core » main` lancé par l'orchestrateur : sa cause est `Started by upstream project "library/orchestrateur" build number 1`.
5. Vue graphique du build de l'orchestrateur (**Pipeline Overview**) : les branches **core** et **legacy** côte à côte, puis **Fetch core jar** et **Portal**.

> **Point clé.** Le JAR copié vient du build exact lancé quelques secondes plus tôt (`specific(...)`), pas du « dernier build réussi », qui aurait pu être produit entre-temps par un autre déclenchement. Entre projets Maven, la règle de la slide 5 reste valable : `library-portal` lit `library-core` dans Nexus ; la copie d'artefacts sert aux cas sans dépôt (scripts, rapports, binaires non Maven).

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| `ERROR: Unable to find project for artifact copy: library/library-core/main` | Le build de `main` date d'avant `copyArtifactPermission` | Relancer `library » library-core » main` une fois, puis l'orchestrateur |
| `No item named library/library-portal/main found` | Démo 3 non faite | Créer le Multibranch `library-portal` |

---

## Démo 6 — Pipeline multi-outils Maven + npm + Docker

> Slides : 12 à 14 · Durée : 20 min · Prérequis : démo 0

**Pourquoi.** Une application réelle mêle plusieurs écosystèmes : un back Maven, un front npm, une image Docker (slide 12). Chaque partie a son outil, sa version, son rapport de tests. Le pipeline les fait tourner en parallèle et transmet les fichiers d'un stage à l'autre par `stash` / `unstash` (slides 13 et 14).

**Ce qu'elle montre.** L'outil NodeJS installé à la demande, deux stages parallèles sur des agents choisis par label, des rapports JUnit venant de Maven et de Node, et la construction d'une image Docker à partir des fichiers du front.

### Étapes

1. **Manage Jenkins → Tools** → section **NodeJS installations** → **Add NodeJS** :
   - **Name** : `node-22`
   - **Install automatically** coché → **Install from nodejs.org** → **Version** : `NodeJS 22.12.0`
   - laisser **Global npm packages to install** vide

   **Save**.

2. Lire `projets/library-ops/ci/multi-outils.Jenkinsfile` :
   - **Backend (Maven)** : `agent { label 'linux && maven' }`, `mvn -Drevision=$APP_VERSION clean verify` ;
   - **Frontend (npm)** : `tools { nodejs 'node-22' }`, `npm ci`, `npm run lint`, `npm test` (rapport JUnit écrit par `node --test`), `npm run build`, puis `stash name: 'web'` ;
   - **Image Docker** : `agent { label 'linux && docker' }`, `unstash 'web'`, `docker build -t library-web:$APP_VERSION .`.
3. Dossier `library` → **New Item** → `multi-outils` → **Pipeline** → **OK** → **Pipeline script from SCM** : dépôt `library-ops`, **Script Path** `ci/multi-outils.Jenkinsfile` (mêmes **Repository URL**, **Credentials** et **Branch Specifier** qu'à la démo 5) → **Save** → **Build Now**.
4. Console, branche **Frontend (npm)** :

   ```
   Unpacking https://nodejs.org/dist/v22.12.0/node-v22.12.0-linux-arm64.tar.gz to ... on linux-1
   + node -v
   v22.12.0
   + npm -v
   10.9.0
   ...
   ℹ tests 3
   ℹ pass 3
   ```

   (`linux-arm64` ou `linux-x64` selon le processeur du poste.) Stage **Image Docker** :

   ```
   #7 naming to docker.io/library/library-web:2.0.1 done
   + docker image ls library-web
   library-web   2.0.1   ...   49.7MB
   ```

5. Page du build → **Tests** : 4 tests JUnit Maven (`fr.utopios.library.core.LoanRulesTest`) et 3 tests Node (`catalogue`) dans le même rapport.

> **Point clé.** La slide 13 fait tourner chaque stage dans un conteneur dédié (`agent { docker { image 'node:22' } }`). Ici, l'outil est installé par Jenkins sur l'agent : le Jenkinsfile reste le même quel que soit l'agent, et aucun accès Docker n'est nécessaire pour les stages Maven et npm. Seul le stage **Image Docker** exige un agent avec Docker, d'où le label `linux && docker`.

---

## Démo 7 — Shared Library

> Slides : 15 · Durée : 15 min · Prérequis : démo 2

**Pourquoi.** Trente Jenkinsfiles qui recopient le même bloc Maven deviennent impossibles à faire évoluer. Une **Shared Library** (slide 15) met ce code commun dans un dépôt Git versionné : `vars/` pour les steps globaux, `src/` pour les classes Groovy. Un Jenkinsfile de service tient alors en deux lignes.

**Ce qu'elle montre.** La déclaration d'une bibliothèque de confiance au niveau global, son chargement (`Loading library utopios-ci@main`), un step global (`mavenBuild`), un pipeline complet paramétré (`javaServicePipeline`) et une classe de `src/`.

### Étapes

1. Parcourir `projets/jenkins-shared-lib/` :
   - `vars/mavenBuild.groovy` : step `mavenBuild(goals: 'clean verify')` qui résout Maven et le JDK par `tool`, puis publie les rapports JUnit ;
   - `vars/notifyTeam.groovy` : mail `emailext` ;
   - `vars/javaServicePipeline.groovy` : un `pipeline { }` déclaratif complet, paramétré par une `Map` ;
   - `src/fr/utopios/ci/Versioning.groovy` : `Versioning.fromBuild(42, '2.3')` renvoie `2.3.42`.
2. **Manage Jenkins → System** → section **Global Trusted Pipeline Libraries** → **Add** :
   - **Name** : `utopios-ci`
   - **Default version** : `main`
   - **Load implicitly** : décoché ; **Allow default version to be overridden** : coché
   - **Retrieval method** : **Modern SCM** → **Source Code Management** : **Git**
   - **Project Repository** : `http://gitea:3000/formation/jenkins-shared-lib.git`
   - **Credentials** : `formation/****** (Gitea - jeton lecture)`

   **Save**.

3. Lire `projets/library-core/ci/Jenkinsfile.shared-lib` :

   ```groovy
   @Library('utopios-ci') _
   javaServicePipeline(base: '2.3', mail: 'dev-team@example.com')
   ```

4. Dossier `library` → **New Item** → `library-core-shared-lib` → **Pipeline** → **OK** → **Pipeline script from SCM** : dépôt `http://gitea:3000/formation/library-core.git`, **Credentials** `formation/****** (Gitea - jeton lecture)`, **Branch Specifier** `*/main`, **Script Path** `ci/Jenkinsfile.shared-lib` → **Save** → **Build Now**.
5. Console :

   ```
   Loading library utopios-ci@main
   Attempting to resolve main from remote references...
   ...
   + mvn -B -ntp clean verify
   ...
   Version calculee : 2.3.1
   Finished: SUCCESS
   ```

   Les stages **Build** et **Version** viennent de `javaServicePipeline` ; `2.3.1` vient de la classe `Versioning` (base `2.3`, build n° 1).

> **Point clé.** Une bibliothèque déclarée dans **Global Trusted Pipeline Libraries** s'exécute hors sandbox : son dépôt doit être protégé et relu (slide 15). Une bibliothèque déclarée au niveau d'un Folder reste soumise au sandbox. `@Library('utopios-ci@v1.2') _` épingle une version précise, ce que permet **Allow default version to be overridden**.

---

## Démo 8 — Chaîne de promotion CD

> Slides : 19 à 22 · Durée : 30 min · Prérequis : démo 0 (releases `1.4.0` et `1.4.1` de `library-api` dans Nexus)

**Pourquoi.** Le déploiement continu ne reconstruit rien : une version déjà publiée traverse les environnements, de dev à la production (slide 19). Le pipeline de promotion (slides 21 et 22) assemble les mécanismes de contrôle : paramètres, refus des SNAPSHOT, verrou par environnement (`lock`), approbation humaine (`input`), arbitrage entre promotions concurrentes (`milestone`) et conservation de la trace de mise en production.

**Ce qu'elle montre.** Une version téléchargée depuis `maven-releases` et déployée sur trois conteneurs (dev, recette, prod), le refus sans référence de change, l'approbation, l'annulation d'une promotion dépassée par une plus récente, et le build de production conservé.

### Étapes

1. Lire `projets/library-ops/ci/deploy.Jenkinsfile` :
   - paramètres `VERSION` (défaut `1.4.1`) et `CHANGE_REF` ;
   - **Validate** refuse une version `-SNAPSHOT` ;
   - **Fetch** télécharge `library-api-$APP_VERSION.jar` depuis `maven-releases` avec `nexus-deploy`, puis `stash` ;
   - **Dev**, **Recette** (`lock('env-recette')`) et **Prod** (`lock('env-production')`) appellent `deployTo(env, port)`, qui recrée le conteneur `library-api-<env>` et attend `/actuator/health` ;
   - **Approbation prod** : `CHANGE_REF` obligatoire, `input` d'une heure au plus, puis `milestone 1` ;
   - **Prod** pose une description et `currentBuild.keepLog = true`.
2. Dossier `library` → **New Item** → `deploy` → **Pipeline** → **OK** → **Pipeline script from SCM** : dépôt `library-ops`, **Script Path** `ci/deploy.Jenkinsfile` → **Save**.

**Premier build : sans référence de change**

3. **Build Now** (le job ne connaît pas encore ses paramètres : ils sont déclarés dans le Jenkinsfile et enregistrés au premier build). Le build déploie dev et recette avec les valeurs par défaut, puis échoue :

   ```
   ERROR: CHANGE_REF obligatoire pour la production
   Finished: FAILURE
   ```

   Le build s'appelle `#1 v1.4.1`. Le bouton du job devient **Build with Parameters**.

4. Vérifier les deux environnements :

   ```bash
   docker ps --filter name=library-api- --format '{{.Names}}  {{.Ports}}'
   ```

   ```bash
   curl -s http://localhost:8093/actuator/health
   ```

   Résultat : `library-api-dev` (8092) et `library-api-recette` (8093) tournent ; la recette répond `"status":"UP"`.

**Promotion approuvée**

5. **Build with Parameters** → **VERSION** : `1.4.1`, **CHANGE_REF** : `CHG-0001` → **Build**.
6. Le build s'arrête au stage **Approbation prod**. Dans la vue graphique ou la console : `Promouvoir 1.4.1 en production (CHG-0001) ?` avec les boutons **Promouvoir** et **Abort** (menu du build : **Paused for Input**). Cliquer **Promouvoir**.

   Résultat : stage **Prod** vert, description du build `v1.4.1 en production (CHG-0001)`, et le build est marqué **Keep this build forever** (cadenas dans l'historique). `curl -s http://localhost:8094/actuator/health` répond `"status":"UP"`.

**Deux promotions concurrentes**

7. Lancer coup sur coup deux builds : **VERSION** `1.4.0` / **CHANGE_REF** `CHG-0002`, puis **VERSION** `1.4.1` / **CHANGE_REF** `CHG-0003`. Les deux s'arrêtent à **Approbation prod**.
8. Approuver d'abord le **plus récent** (`v1.4.1`, CHG-0003). Dès qu'il franchit `milestone 1`, le plus ancien se termine seul :

   ```
   Superseded by library/deploy#4
   Finished: NOT_BUILT
   ```

   La production ne peut pas recevoir une version plus ancienne après une plus récente. Il n'y a pas de `disableConcurrentBuilds` dans ce pipeline : c'est le `milestone` qui arbitre, et les deux promotions ont pu avancer en parallèle jusqu'à l'approbation.

> **Point clé.** `params.VERSION` existe dès le premier build ; la variable d'environnement `VERSION`, elle, n'existe qu'une fois le paramètre enregistré dans le job. D'où `environment { APP_VERSION = "${params.VERSION}" }`, utilisé dans les blocs `sh`. Les stratégies rolling, blue-green et canary (slide 20) se jouent au niveau de la plate-forme (Kubernetes, load balancer) ; le pipeline, lui, reste celui-ci.

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| `curl: (22) The requested URL returned error: 404` au stage **Fetch** | Version absente de `maven-releases` | Relancer `./scripts/etat-partie1.sh` (publie 1.4.0 et 1.4.1) |
| `docker: not found` | Stage parti sur un agent sans Docker | Les stages **Dev**, **Recette** et **Prod** demandent `linux && docker` : seul `linux-1` porte le label `docker` |
| Port 8092, 8093 ou 8094 déjà pris | Autre service local | Changer le port dans les appels `deployTo(...)` du Jenkinsfile (dépôt Gitea `library-ops`) |

---

## Démo 9 — Agent inbound en WebSocket

> Slides : 25 à 28 · Durée : 15 min · Prérequis : démo 0

**Pourquoi.** `linux-1` est un agent **SSH** : c'est le controller qui se connecte à l'agent. Quand l'agent est derrière un pare-feu ou un NAT, on inverse le sens : l'agent **inbound** se connecte lui-même au controller (slides 25 et 28). En WebSocket, il passe par le port HTTP de Jenkins (8080), sans ouvrir le port TCP 50000.

**Ce qu'elle montre.** La création d'un node inbound, le secret qui l'authentifie, les commandes de lancement proposées par Jenkins, et un agent en conteneur (`jenkins/inbound-agent`) qui se connecte par WebSocket.

### Étapes

1. **Manage Jenkins → Nodes** → **New Node** → **Node name** : `linux-2`, **Type** : **Permanent Agent** → **Create**.
2. Renseigner :

   | Champ | Valeur |
   |---|---|
   | **Description** | `Agent inbound (conteneur linux-2)` |
   | **Number of executors** | `1` |
   | **Remote root directory** | `/home/jenkins/agent` |
   | **Labels** | `linux java21` |
   | **Usage** | `Only build jobs with label expressions matching this node` |
   | **Launch method** | `Launch agent by connecting it to the controller` |
   | **Use WebSocket** | coché |
   | **Availability** | `Keep this agent online as much as possible` |

   **Save**.

3. Ouvrir le node `linux-2` : la page affiche **Run from agent command line: (Unix)**, **(Windows)** et la variante avec le secret dans un fichier :

   ```
   curl -sO http://localhost:8080/jnlpJars/agent.jar
   java -jar agent.jar -url http://localhost:8080/ -secret <secret> -name "linux-2" -webSocket -workDir "/home/jenkins/agent"
   ```

   Copier la valeur de `-secret` (64 caractères hexadécimaux).

4. Dans `.env` du kit, coller le secret :

   ```
   JENKINS_SECRET_LINUX2=<secret copié>
   ```

5. Démarrer l'agent (profil `cluster` du `docker-compose.yml` : variables `JENKINS_URL`, `JENKINS_AGENT_NAME`, `JENKINS_SECRET`, `JENKINS_WEB_SOCKET=true`) :

   ```bash
   docker compose --profile cluster up -d linux-2
   ```

   ```bash
   docker logs linux-2 2>&1 | grep -E 'WebSocket|Connected'
   ```

   Résultat : `WebSocket connection open` puis `Connected`. Dans Jenkins, `linux-2` passe en ligne ; **Build Executor Status** affiche `linux-2  0/1`.

> **Point clé.** En production, l'agent inbound tourne en service systemd (slide 28) avec le secret dans un fichier lisible par le seul compte `jenkins` (`-secret @secret-file`). Le secret est lié au nom du node : le connaître suffit pour se faire passer pour l'agent. Il se traite comme un mot de passe.

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| `docker logs linux-2` : `Failed to connect ... 403` ou `Handshake error` | Secret absent ou d'un autre node | Recopier le secret de la page du node dans `.env`, puis `docker compose --profile cluster up -d linux-2` |
| `linux-2` en ligne mais jamais utilisé | Mode **Only build jobs with label expressions matching this node** | Comportement voulu : seuls les jobs qui demandent `linux` ou `java21` y vont |

---

## Démo 10 — Agents Docker éphémères

> Slides : 31 · Durée : 20 min · Prérequis : démo 0 (image `formation/jenkins-agent-maven:jdk21` construite à l'étape 5)

**Pourquoi.** Un agent permanent accumule des outils, des caches et des restes de builds : il dérive. Un agent **éphémère** est un conteneur créé pour un build et détruit ensuite (slide 31) : environnement identique à chaque fois, capacité qui suit la demande. Le plugin **Docker** crée ces conteneurs à la volée à partir d'un modèle (*template*) associé à un label.

**Ce qu'elle montre.** La déclaration d'un cloud Docker, un template lié au label `docker-maven`, un node qui apparaît pour un build puis disparaît avec son conteneur.

### Étapes

1. Lire `agent-docker-maven/Dockerfile` : `FROM jenkins/agent:jdk21` (Java et l'agent Jenkins), plus Maven 3.9.16 dans `/opt` et dans le `PATH`.
2. Démarrer le relais vers le Docker du poste :

   ```bash
   docker compose --profile cluster up -d docker-proxy
   ```

   `docker-proxy` expose la socket Docker du poste en TCP (`tcp://docker-proxy:2375`) sur le réseau `ci-formation`. C'est donner à Jenkins le contrôle complet du Docker du poste : acceptable pour une formation, pas en production (voir **Point clé**).

3. **Manage Jenkins → Clouds** → **New cloud** → **Cloud name** : `docker-local`, **Type** : **Docker** → **Create**.
4. Section **Docker Cloud details** (la déplier) :
   - **Docker Host URI** : `tcp://docker-proxy:2375`
   - cliquer **Test Connection** → `Version = 27.4.0, API Version = 1.47` (les numéros sont ceux du Docker du poste)
   - **Enabled** : coché
5. Section **Docker Agent templates** → **Add Docker Template** :

   | Champ | Valeur |
   |---|---|
   | **Labels** | `docker-maven` |
   | **Enabled** | coché |
   | **Name** | `docker-maven` |
   | **Docker Image** | `formation/jenkins-agent-maven:jdk21` |
   | **Container settings** → **Network** | `ci-formation` |
   | **Instance Capacity** | `3` |
   | **Remote File System Root** | `/home/jenkins/agent` |
   | **Usage** | `Only build jobs with label expressions matching this node` |
   | **Connect method** | `Attach Docker container`, **User** : `jenkins` |
   | **Pull strategy** | `Never pull` (l'image n'existe que sur le poste) |

   **Save**.

6. Dossier `library` → **New Item** → `agent-ephemere` → **Pipeline** → **OK** → **Definition** : **Pipeline script**, **Script** :

   ```groovy
   pipeline {
     agent { label 'docker-maven' }
     stages {
       stage('Build') {
         steps {
           sh 'echo "node=$NODE_NAME"; hostname; mvn -v | head -1'
           git url: 'http://gitea:3000/formation/library-core.git', branch: 'main', credentialsId: 'gitea-token'
           sh 'mvn -B -ntp -Drevision=2.3.0-SNAPSHOT clean verify'
         }
       }
     }
   }
   ```

   **Save** → **Build Now**.

7. Pendant le build, dans un terminal :

   ```bash
   docker ps --format '{{.Names}}  {{.Image}}  {{.Status}}' | grep jenkins-agent-maven
   ```

   Résultat : un conteneur `formation/jenkins-agent-maven:jdk21` créé quelques secondes plus tôt. Dans Jenkins, **Build Executor Status** affiche un node `docker-maven-0000…` ; la console indique :

   ```
   Running on docker-maven-0000256rh89in on docker-local in /home/jenkins/agent/workspace/library/agent-ephemere
   + echo node=docker-maven-0000256rh89in
   Apache Maven 3.9.16 (...)
   [INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
   [INFO] BUILD SUCCESS
   Finished: SUCCESS
   ```

8. Une fois le build terminé, relancer la commande `docker ps` : le conteneur a disparu, et le node aussi. Le tableau de bord affiche **Cloud Statistics** (`docker-local`, taux de réussite des provisionnements).

> **Point clé.** Chaque conteneur part de zéro : les dépendances Maven sont téléchargées à chaque build (pas de `~/.m2` partagé). En production, on monte un cache ou on passe par le proxy Nexus. Sur l'accès à Docker : en production, le controller parle à un hôte Docker dédié, en TLS (**Server credentials** : certificat client), jamais à la socket de sa propre machine (slide 37).

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| **Test Connection** : `UnknownHostException: docker-proxy` | Relais non démarré | `docker compose --profile cluster up -d docker-proxy` |
| Build bloqué sur `Waiting for next available executor on ‘docker-maven’` puis erreurs `No such image` dans **Manage Jenkins → System Log** | Image non construite et **Never pull** | `docker build -t formation/jenkins-agent-maven:jdk21 agent-docker-maven` |
| Le conteneur démarre puis le node reste hors ligne | **Network** absent : le conteneur ne joint pas `jenkins` | **Container settings** → **Network** : `ci-formation` |

---

## Démo 11 — Labels, parallélisme et file d'attente

> Slides : 33 à 35 · Durée : 15 min · Prérequis : démos 9 et 10

**Pourquoi.** Avec trois types d'agents, la question devient « quel build va où ». Les labels décrivent les capacités d'un agent ; un Jenkinsfile exprime un besoin (`label 'linux && docker'`), pas un nom de machine (slide 33). Un pipeline peut répartir ses stages sur plusieurs agents en parallèle (slide 34). Et quand un build ne part pas, la file d'attente en donne la raison (slide 35).

**Ce qu'elle montre.** Un pipeline dont trois stages tournent en même temps sur un agent SSH, un agent inbound et un agent éphémère ; les labels automatiques (nom du node) ; la raison d'attente d'un build dont le label n'est servi par personne.

### Étapes

1. **Manage Jenkins → Nodes** : relever les labels.
   - `linux-1` : `linux java21 maven docker` ;
   - `linux-2` : `linux java21` ;
   - le template Docker : `docker-maven`.

   Chaque node porte aussi un label à son nom. Cliquer un label sur la page d'un node (par exemple `linux`) ouvre la page du label : nodes qui le portent, executors, jobs qui le demandent.

2. Lire `projets/library-ops/ci/cluster.Jenkinsfile` : `agent none`, puis trois stages `parallel` sur `label 'linux-1'`, `label 'linux-2'` et `label 'docker-maven'`.
3. Dossier `library` → **New Item** → `cluster` → **Pipeline** → **OK** → **Pipeline script from SCM** : dépôt `library-ops`, **Script Path** `ci/cluster.Jenkinsfile` → **Save** → **Build Now**.
4. Console (les lignes des trois branches s'entremêlent) :

   ```
   Running on linux-1 in /home/jenkins/agent/workspace/library/cluster
   Running on linux-2 in /home/jenkins/agent/workspace/library/cluster
   Running on docker-maven-00001j49o7zdf on docker-local in /home/jenkins/agent/workspace/library/cluster
   node=linux-1 labels=maven linux linux-1 java21 docker
   node=linux-2 labels=linux linux-2 java21
   node=docker-maven-00001j49o7zdf labels=docker-maven docker-maven-00001j49o7zdf
   Apache Maven 3.9.16 (...)
   Finished: SUCCESS
   ```

   La vue graphique montre les trois stages côte à côte sous **Plates-formes**.

**Un label que personne ne sert**

5. Dossier `library` → **New Item** → `attente-macos` → **Pipeline** → **OK** → **Pipeline script** :

   ```groovy
   pipeline {
     agent { label 'macos' }
     stages {
       stage('Signature iOS') { steps { sh 'sw_vers' } }
     }
   }
   ```

   **Save** → **Build Now**.

6. Le build reste en attente. Console :

   ```
   Still waiting to schedule task
   There are no nodes with the label ‘macos’
   ```

   Le panneau **Build Queue** (à gauche) liste `part of library » attente-macos #1` ; le survol de la ligne affiche la même raison. Arrêter le build (croix rouge de la file ou du build) : il se termine en `ABORTED`.

> **Point clé.** Les raisons d'attente les plus fréquentes (slide 35) : `There are no nodes with the label ‘x’` (aucun agent ne porte le label), `‘linux-1’ is offline` (l'agent existe mais est déconnecté), `Waiting for next available executor on ‘x’` (agents occupés : manque de capacité). Seule la dernière se règle en ajoutant des executors.

---

## Démo 12 — Vues

> Slides : 40, 41 · Durée : 15 min · Prérequis : démos 1 à 8 (des jobs à afficher), plugin Build Monitor View (démo 0)

**Pourquoi.** Avec une vingtaine de jobs dans des dossiers, l'onglet **All** ne suffit plus. Une vue est un filtre d'affichage (slide 40) : elle ne contient pas les jobs, elle les montre. Les équipes ont aussi besoin d'un « radiateur » affiché sur un écran : la Build Monitor View (slide 41).

**Ce qu'elle montre.** Une List View filtrée par expression régulière, le piège des jobs rangés dans un dossier, la vue par défaut, et un radiateur Build Monitor.

### Étapes

**List View « Library »**

1. Tableau de bord → onglet **+** (à droite des onglets de vues) → **Name** : `Library`, **Type** : **List View** → **Create**.
2. Page **Edit View**, section **Jobs** :
   - cocher **Recurse in subfolders** (sans cela, seuls les éléments de premier niveau sont proposés) ;
   - cocher **Use a regular expression to include jobs into the view** → **Regular expression** : `library-.*` (valeur de la slide 40)

   **Save**.

3. Résultat : la vue ne montre aucun job du dossier `library`. Avec **Recurse in subfolders**, l'expression est comparée au nom **complet** du job (`library/library-core`), qui commence par `library/` : `library-.*` ne correspond pas.
4. **Edit View** → **Regular expression** : `library/library-.*` → **Save**.

   Résultat : `library » library-api-aval`, `library » library-core` et ses sous-jobs `main` et `v2.3.0`, `library-core-freestyle`, `library-core-shared-lib`, `library-legacy`, `library-portal` et `library » library-portal » main`. Les jobs sans préfixe `library-` (`orchestrateur`, `deploy`, `cluster`...) n'y sont pas. Les colonnes par défaut sont **S** (statut), **W** (météo), **Name**, **Last Success**, **Last Failure**, **Last Duration** (plus les colonnes ajoutées par les plugins installés, ici **Coverage** et **# Issues**).

**Vue par défaut**

5. **Manage Jenkins → System** → **Default view** : `Library` → **Save**.
6. Revenir sur **http://localhost:8080** : le tableau de bord s'ouvre sur l'onglet **Library**. La vue **All** reste accessible par son onglet.

**Radiateur Build Monitor**

7. Onglet **+** → **Name** : `Radiateur`, **Type** : **Build Monitor View** → **Create**.
8. **Edit View** :
   - **Recurse in subfolders** : coché
   - **Use a regular expression to include jobs into the view** → **Regular expression** : `library/.*/main`
   - section **Build Monitor** → **Ordered by** : `Status`

   **Save**.

9. Résultat : une page plein écran avec une tuile verte par branche `main` : `library » library-core » main` (`#2 2.3.0-SNAPSHOT`) et `library » library-portal » main`. Une tuile passe au rouge quand le dernier build échoue et au jaune pour `UNSTABLE`. Le menu **⋯** (en haut à droite) règle la taille du texte et le nombre de colonnes pour l'écran utilisé.

> **Point clé.** Une vue ne protège rien (slide 40) : un utilisateur qui a **Job/Read** ouvre le job par son URL même s'il n'est dans aucune vue. Les vues créées à la main disparaissent si le controller est reconstruit : la slide 41 les déclare en JCasC ou en Job DSL (la vue `Library DSL` de la démo 16 en est un exemple).

---

## Démo 13 — Visite de JENKINS_HOME

> Slides : 44 à 46 · Durée : 15 min · Prérequis : démos précédentes (un historique de builds)

**Pourquoi.** Toute la configuration et tout l'historique de Jenkins sont des fichiers dans `JENKINS_HOME` (slide 44) : pas de base de données. Savoir ce qui s'y trouve permet de comprendre ce qu'il faut sauvegarder (démo 15), ce qui grossit, et comment réparer à la main en dernier recours (slide 45).

**Ce qu'elle montre.** L'arborescence, un job et ses builds sur le disque, la répartition de la place, et la rétention des builds dans l'UI.

### Étapes

1. Le chemin est rappelé dans **Manage Jenkins → System** → **Home directory** : `/var/jenkins_home`.
2. Racine :

   ```bash
   docker exec jenkins ls /var/jenkins_home
   ```

   Repérer :
   - `config.xml` (configuration globale), `credentials.xml` (credentials chiffrés) ;
   - un fichier XML par plugin configuré (`hudson.tasks.Maven.xml`, `jenkins.plugins.nodejs.tools.NodeJSInstallation.xml`...) ;
   - `secrets/` (clés de chiffrement) ;
   - `jobs/`, `nodes/` (`linux-1`, `linux-2`), `users/` ;
   - `plugins/`, `war/`, `caches/`, `workspace/`, `logs/`, `fingerprints/`.

3. Un job et ses builds :

   ```bash
   docker exec jenkins ls /var/jenkins_home/jobs/library/jobs/library-legacy /var/jenkins_home/jobs/library/jobs/library-legacy/builds/1
   ```

   Résultat : `config.xml`, `nextBuildNumber` et `builds/` ; dans un build, `build.xml` (résultat, durée, cause), `log` (console), `junitResult.xml` (tests), `archive/` (artefacts archivés), `changelog*.xml`. Un dossier Jenkins (`library`) devient un répertoire `jobs/library/jobs/`.

4. La place occupée :

   ```bash
   docker exec jenkins sh -c 'cd /var/jenkins_home && du -sh jobs plugins war caches workspace fingerprints logs users nodes'
   ```

   Ordre de grandeur relevé après les démos : `plugins` 322 Mo, `war` 66 Mo, `caches` 54 Mo (clones Git des Multibranch), `jobs` 4 Mo, `workspace` 324 Ko. Le controller a 0 executor : son `workspace/` ne contient presque rien, les builds tournent sur les agents.

5. Lire la configuration d'un job depuis le navigateur : http://localhost:8080/job/library/job/library-legacy/config.xml (le même XML que sur le disque ; c'est aussi ce que renvoie la commande CLI `get-job`, démo 17).

**Rétention des builds**

6. `library » library-legacy` → **Configure** → **General** → cocher **Discard old builds** : **Strategy** `Log Rotation`, champs **Days to keep builds** et **Max # of builds to keep** (bouton **Advanced** : même chose pour les artefacts). Saisir **Max # of builds to keep** : `10` → **Save**.

   Les builds au-delà des 10 derniers seront supprimés à la fin du prochain build. Un build marqué **Keep this build forever** (démo 8) n'est jamais supprimé.

7. **Manage Jenkins → System** → section **Global Build Discarders** : **Project Build Discarder** applique la politique de chaque job périodiquement, même sans nouveau build.

> **Point clé.** `secrets/` et `credentials.xml` vont ensemble : `credentials.xml` est chiffré par les clés de `secrets/`. Restaurer l'un sans l'autre rend tous les secrets illisibles (slide 45).

---

## Démo 14 — Supervision : Prometheus, Grafana, job de supervision

> Slides : 47 à 49 · Durée : 25 min · Prérequis : plugin Prometheus metrics (démo 0), démo 9 (`linux-2`)

**Pourquoi.** Un Jenkins saturé, un agent tombé ou un Nexus injoignable se découvrent trop tard si l'on attend les plaintes. La slide 47 liste ce qu'il faut surveiller (système, JVM, Jenkins, métier). Le plugin Prometheus metrics expose ces indicateurs, Prometheus les collecte, Grafana les affiche (slide 48). Un job de supervision interne vérifie en plus la chaîne réelle : services et agents (slide 49).

**Ce qu'elle montre.** L'endpoint `/prometheus/`, sa collecte par Prometheus, une requête dans Grafana, et un job planifié qui échoue et envoie un mail quand un agent tombe.

### Étapes

**Exposer les métriques**

1. **Manage Jenkins → System** → section **Prometheus** : **Path** `prometheus` (valeur par défaut), **Collecting metrics period in seconds**, cases **Count duration of successful builds**, **Collect disk usage**, **Collect node status**... et **Enable authentication for prometheus end-point**, décochée par défaut. Ne rien changer.
2. Dans un terminal :

   ```bash
   curl -s http://localhost:8080/prometheus/ | grep -E '^default_jenkins_nodes_online|^jenkins_executor_in_use_value|^vm_memory_heap_usage '
   ```

   Résultat (sans authentification) :

   ```
   default_jenkins_nodes_online{node="linux-1",} 1.0
   default_jenkins_nodes_online{node="linux-2",} 1.0
   jenkins_executor_in_use_value 0.0
   vm_memory_heap_usage 0.105...
   ```

   L'endpoint est lisible par tout le monde, même si Jenkins exige une connexion pour le reste. En production : cocher **Enable authentication for prometheus end-point** (et donner un compte à Prometheus) ou filtrer l'accès par le réseau.

**Prometheus et Grafana**

3. Démarrer les deux services (profil `monitoring`) :

   ```bash
   docker compose --profile monitoring up -d
   ```

   `prometheus/prometheus.yml` interroge `http://jenkins:8080/prometheus/` toutes les 30 secondes.

4. http://localhost:9091 → **Status** → **Target health** : la cible `jenkins` est **UP**. Onglet **Query** → `default_jenkins_nodes_online` → **Execute** : une série par agent.
5. http://localhost:3001 → se connecter en `admin` / `Formation-2026` → **Connections** → **Data sources** → **Add new data source** → **Prometheus** → **Prometheus server URL** : `http://prometheus:9090` → **Save & test** (en bas de page) → message `Successfully queried the Prometheus API.`
6. **Explore** → source `Prometheus` → requête `default_jenkins_executors_available` → **Run query** : une courbe par label (`linux`, `docker`, `linux-1`...).

   Les noms de la slide 48 ne sont pas tous exposés par la version du plugin utilisée ici : `jenkins_queue_size_value` n'existe pas ; la file d'attente se lit dans `default_jenkins_executors_queue_length` ou `jenkins_queue_buildable_value`.

**Job de supervision**

7. Créer un jeton d'API pour le job : menu utilisateur (icône personnage en haut à droite) → **Security** → **API Token** → **Add new token** → boîte **Create new API token** : **Name** `supervision`, **Expiration** `30 Days` → **Generate**. Le jeton s'affiche une seule fois (*Copy this token now, because it cannot be recovered in the future.*) : le copier → **Done**.
8. **Manage Jenkins → Credentials** → **Add Credentials** → **Username with password** → **Next** : **Username** `admin`, **Password** le jeton, **ID** `jenkins-api`, **Description** `Jenkins - API (supervision)` → **Create**.
9. Lire `projets/library-ops/ci/supervision.Jenkinsfile` : `cron('H/30 * * * *')`, stage **Services** (`curl -sf` sur Jenkins, Nexus et Gitea), stage **Agents** (API `computer/api/json` avec `jenkins-api`, échec si un agent est `"offline":true`), mail en cas d'échec.
10. Dossier `library` → **New Item** → `supervision` → **Pipeline** → **OK** → **Pipeline script from SCM** : dépôt `library-ops`, **Script Path** `ci/supervision.Jenkinsfile` → **Save** → **Build Now**.

    Résultat : `jenkins OK`, `nexus OK`, `gitea OK`, la liste des nodes (tous `"offline":false`), `Finished: SUCCESS`. Le mot de passe est masqué dans la console (`curl -sfg -u admin:****`).

11. Simuler une panne d'agent :

    ```bash
    docker stop linux-2
    ```

    Attendre que `linux-2` apparaisse hors ligne dans **Build Executor Status**, puis **Build Now** sur `supervision`. Résultat :

    ```
    {"displayName":"linux-2","offline":true}
    Sending email to: admin@example.com
    ERROR: script returned exit code 1
    Finished: FAILURE
    ```

    Mailpit (http://localhost:8025) reçoit `[Jenkins] Supervision en echec`.

12. Remettre l'agent en service :

    ```bash
    docker start linux-2
    ```

    Il se reconnecte seul en quelques secondes (agent inbound).

> **Point clé.** La plupart des « pannes Jenkins » sont des pannes de ce qui l'entoure : Git, Nexus, DNS (slide 49). C'est pourquoi le job teste les services autant que les agents. **Manage Jenkins** donne aussi des outils intégrés : **System Information**, **System Log**, **Load Statistics** (slide 47).

---

## Démo 15 — Sauvegarde et restauration

> Slides : 50 à 52 · Durée : 15 min · Prérequis : démo 13

**Pourquoi.** Une sauvegarde qui n'a jamais été restaurée n'est pas une sauvegarde (slide 51). La démo applique le script de la slide 51 au volume Docker de la formation, puis restaure l'archive dans un **second** Jenkins, sans toucher à l'original.

**Ce qu'elle montre.** La mise au repos (`quietDown`) le temps de la copie, une archive sélective (sans ce qui se reconstruit), la liste des plugins avec leurs versions, et une restauration vérifiée : comptes, jobs, historique.

### Étapes

1. Lire `scripts/sauvegarde.sh` :
   - `POST /quietDown`, puis attente que `busyExecutors` vaille 0 ; un `trap` relance Jenkins (`/cancelQuietDown`) même si une étape échoue ;
   - archive du volume `jenkins-formation_jenkins_home` par un conteneur `alpine`, en excluant `war`, `updates`, `caches`, `workspace`, `plugins/*/*` (plugins décompressés, les `.jpi` restent) et `logs` ;
   - `plugins-<date>.txt` au format `nom:version`, lisible par `jenkins-plugin-cli`.
2. Utiliser le jeton d'API créé à la démo 14 (ou en créer un), puis lancer :

   ```bash
   JENKINS_TOKEN=<jeton> ./scripts/sauvegarde.sh
   ```

   Résultat :

   ```
   Jenkins en mise au repos, attente de la fin des builds...
   -rw-r--r--  1 ...  138M ... sauvegardes/jenkins-home-20261101-131045.tgz
   -rw-r--r--  1 ...  4.2K ... sauvegardes/plugins-20261101-131045.txt
   Jenkins remis en service
   ```

   Pendant la mise au repos, Jenkins termine les builds en cours mais n'en démarre plus de nouveaux : un build lancé à ce moment attend dans la file.

3. Contenu de l'archive :

   ```bash
   tar tzf sauvegardes/jenkins-home-*.tgz | awk -F/ '{print $2}' | sort | uniq -c | sort -rn | head
   ```

   On y trouve `jobs`, `plugins` (les `.jpi`), `secrets`, `users`, `nodes`, `credentials.xml`, `config.xml`... et aucun `war/` ni `workspace/`.

4. Restaurer dans un Jenkins jetable :

   ```bash
   ./scripts/restaurer.sh sauvegardes/jenkins-home-<date>.tgz
   ```

   Le script crée le volume `jenkins-formation_jenkins_home_restaure`, y extrait l'archive, rend les fichiers à l'utilisateur `jenkins` (uid 1000) et démarre `jenkins-restaure` sur le port **8085**, avec la même image que l'original.

5. Ouvrir **http://localhost:8085** : la connexion `admin` / `Formation-2026` fonctionne, le dossier `library` contient les mêmes jobs, et l'historique est là (`library-legacy` : mêmes numéros de builds). **Manage Jenkins → Nodes** : `linux-1` et `linux-2` sont hors ligne. C'est voulu : le Jenkins restauré tourne sur le réseau Docker par défaut et ne peut pas prendre les agents de l'original.
6. Supprimer le Jenkins restauré :

   ```bash
   docker rm -f jenkins-restaure
   ```

   ```bash
   docker volume rm jenkins-formation_jenkins_home_restaure
   ```

> **Point clé.** Restaurer un controller sur le même réseau que l'original donnerait deux Jenkins qui se disputent les agents et lancent deux fois les jobs planifiés. Une restauration de test se fait toujours isolée. Les approches de la slide 50 (snapshot de volume, plugin ThinBackup, configuration as code) ne dispensent pas de ce test.

---

## Démo 16 — Groovy : Script Console, init.groovy.d, Job DSL

> Slides : 53 à 56 · Durée : 25 min · Prérequis : plugin Job DSL (démo 0)

**Pourquoi.** Le Groovy est la langue d'administration de Jenkins. La **Script Console** exécute du code dans la JVM du controller, avec tous les droits (slide 53) : utile pour l'inventaire et les opérations de masse (slide 54). Les scripts **init.groovy.d** s'exécutent à chaque démarrage (slide 55). **Job DSL** décrit les jobs et les vues en code, appliqué par un *seed job* (slide 56).

**Ce qu'elle montre.** Trois scripts d'inventaire en lecture seule, un script de démarrage idempotent, et la génération de jobs par un seed, avec l'approbation de script que Jenkins exige au premier passage.

### Étapes

**Script Console**

1. **Manage Jenkins → Script Console**. Le texte d'accueil précise que `jenkins.*`, `jenkins.model.*`, `hudson.*` et `hudson.model.*` sont importés automatiquement et que la sortie passe par `println`.
2. Coller dans la zone **Console** puis cliquer **Run** :

   ```groovy
   Jenkins.get().computers.each { c ->
     println "${c.displayName} offline=${c.offline} executors=${c.numExecutors} labels=${c.node?.labelString}"
   }
   null
   ```

   Résultat :

   ```
   Built-In Node offline=false executors=0 labels=
   linux-1 offline=false executors=2 labels=linux java21 maven docker
   linux-2 offline=false executors=1 labels=linux java21
   ```

   Le `null` final évite la ligne `Result: [...]`, que la console ajoute avec la valeur de la dernière expression.

3. Jobs sans politique de rétention (slide 53) :

   ```groovy
   Jenkins.get().getAllItems(Job).findAll { it.buildDiscarder == null }.each { println it.fullName }
   null
   ```

   Résultat : la liste des jobs, sous-jobs Multibranch compris, sauf `library/library-legacy` si sa rétention a été réglée à la démo 13.

4. Credentials : identifiants et types, jamais les valeurs :

   ```groovy
   import com.cloudbees.plugins.credentials.CredentialsProvider
   import com.cloudbees.plugins.credentials.common.StandardCredentials
   import hudson.security.ACL
   CredentialsProvider.lookupCredentialsInItemGroup(StandardCredentials, Jenkins.get(), ACL.SYSTEM2, [])
     .each { println "${it.id}  (${it.class.simpleName})" }
   null
   ```

   Résultat : `agent-ssh-key  (BasicSSHUserPrivateKey)`, `gitea-token  (UsernamePasswordCredentialsImpl)`, `nexus-deploy`, `wildfly-admin`, `jenkins-api`.

**init.groovy.d**

5. Lire `scripts/init.groovy.d/10-message-systeme.groovy` : il pose le message système s'il n'est pas déjà en place, et le dit dans le journal (idempotent).
6. Le copier dans `JENKINS_HOME/init.groovy.d/` et redémarrer proprement :

   ```bash
   docker cp scripts/init.groovy.d/10-message-systeme.groovy jenkins:/var/jenkins_home/init.groovy.d/
   ```

   ```bash
   docker exec -u root jenkins chown jenkins:jenkins /var/jenkins_home/init.groovy.d/10-message-systeme.groovy
   ```

   Dans le navigateur : **http://localhost:8080/safeRestart** → **Yes**. Puis :

   ```bash
   docker logs jenkins 2>&1 | grep -E 'init.groovy.d|\[init\]'
   ```

   Résultat :

   ```
   INFO  j.util.groovy.GroovyHookScript#execute: Executing /var/jenkins_home/init.groovy.d/10-message-systeme.groovy
   [init] message systeme mis a jour
   ```

   Le bandeau du tableau de bord devient `... - configure par init.groovy.d`. Au redémarrage suivant, le journal affiche `[init] message systeme deja en place`. Les agents se reconnectent seuls après le redémarrage.

**Job DSL et seed job**

7. Lire `projets/library-ops/seed/jobs.groovy` : un dossier `library-dsl`, deux `pipelineJob` (`library-core`, `library-legacy`, Jenkinsfile lu dans Gitea) et une `listView('Library DSL')`. `seed/Jenkinsfile` applique ce fichier avec `jobDsl targets: 'seed/jobs.groovy', removedJobAction: 'DELETE', removedViewAction: 'DELETE'`.
8. **Dashboard → New Item** → `seed` → **Pipeline** → **OK** → **Pipeline script from SCM** : dépôt `library-ops`, **Script Path** `seed/Jenkinsfile` → **Save** → **Build Now**.

   Résultat : échec.

   ```
   ERROR: script not yet approved for use
   Finished: FAILURE
   ```

   Le script DSL n'est pas exécuté en sandbox : un administrateur doit l'approuver.

9. **Manage Jenkins → In-process Script Approval** : le script `jobs.groovy` est listé en attente, avec son contenu. Le relire, puis **Approve**.
10. **Build Now** sur `seed`. Console :

    ```
    Processing DSL script seed/jobs.groovy
    Added items:
        GeneratedJob{name='library-dsl/library-legacy'}
        GeneratedJob{name='library-dsl/library-core'}
        GeneratedJob{name='library-dsl'}
    Added views:
        GeneratedView{name='Library DSL'}
    Finished: SUCCESS
    ```

    Le tableau de bord affiche le dossier `library-dsl` et un onglet **Library DSL**. Les deux jobs générés n'ont encore jamais tourné : ils se lancent comme n'importe quel job Pipeline.

> **Point clé.** Toute modification de `jobs.groovy` suivie d'un passage du seed régénère les jobs ; un job retiré du fichier est supprimé (`removedJobAction: 'DELETE'`). Chaque nouvelle version du script doit être réapprouvée, sauf à le faire tourner en sandbox (`sandbox: true`, slide 56), ce qui impose de lancer le seed sous un utilisateur précis (plugin Authorize Project).

---

## Démo 17 — CLI, API REST et Configuration as Code

> Slides : 57 à 60 · Durée : 20 min · Prérequis : un jeton d'API (démo 14), Java 17 ou plus récent sur le poste, plugin Configuration as Code (démo 0)

**Pourquoi.** Ce qui se fait dans l'UI se fait aussi en ligne de commande : la CLI Jenkins pour l'exploitation (slides 57 et 58), l'API REST pour l'intégration dans d'autres outils (slide 59). Et la configuration du controller s'exporte en YAML : c'est le point de départ de « Jenkins as Code » (slide 60).

**Ce qu'elle montre.** `jenkins-cli.jar` servi par le controller, l'authentification par jeton, un build lancé et suivi depuis le terminal, l'API JSON avec `tree=`, la différence jeton / mot de passe pour les requêtes POST, et l'export JCasC.

### Étapes

**CLI**

1. Télécharger le client (même version que le controller) et préparer l'environnement :

   ```bash
   curl -sO http://localhost:8080/jnlpJars/jenkins-cli.jar
   ```

   ```bash
   export JENKINS_URL=http://localhost:8080/ JENKINS_USER_ID=admin JENKINS_API_TOKEN=<jeton>
   ```

   ```bash
   alias jcli='java -jar jenkins-cli.jar -http'
   ```

   L'option `-http` est nécessaire ici : sans elle, la CLI utilise WebSocket (mode par défaut de cette version) et, depuis le poste vers le conteneur, la commande reste bloquée sans message.

2. Découverte :

   ```bash
   jcli who-am-i
   ```

   ```bash
   jcli version
   ```

   ```bash
   jcli list-jobs library
   ```

   Résultat : `Authenticated as: admin` (avec `Authorities: authenticated`), `2.580.2`, puis les jobs du dossier (`agent-ephemere`, `attente-macos`, `cluster`, `deploy`, `library-api-aval`, `library-core`, ...).

3. Lancer un build, attendre et afficher sa console :

   ```bash
   jcli build library/library-legacy -s -v
   ```

   Résultat : la console du build défile dans le terminal et se termine par `Finished: SUCCESS` puis `Completed library » library-legacy #N : SUCCESS`. Le code retour vaut 0 ; il serait différent de 0 en cas d'échec (`-s`), ce qui permet d'enchaîner dans un script.

4. Configuration d'un job (le `config.xml` vu à la démo 13) et liste des plugins :

   ```bash
   jcli get-job library/library-legacy | head -5
   ```

   ```bash
   jcli list-plugins | head -5
   ```

   ```bash
   jcli help
   ```

   `help` liste toutes les commandes : `build`, `quiet-down`, `safe-restart`, `offline-node`, `online-node`, `install-plugin`, `groovy`...

**API REST**

5. Lecture, avec `tree=` pour ne demander que les champs utiles :

   ```bash
   curl -sg -u admin:$JENKINS_API_TOKEN 'http://localhost:8080/job/library/api/json?tree=jobs[name,color]' | python3 -m json.tool | head -12
   ```

   ```bash
   curl -sg -u admin:$JENKINS_API_TOKEN 'http://localhost:8080/computer/api/json?tree=computer[displayName,offline]'
   ```

   `color` vaut `blue` (succès), `red` (échec), `notbuilt`..., suffixé `_anime` pendant un build. Toute page de Jenkins a son API : ajouter `/api/json` à son URL (ou ouvrir le lien **REST API** en bas de page).

6. Écriture : lancer un build.

   ```bash
   curl -s -i -X POST -u admin:$JENKINS_API_TOKEN http://localhost:8080/job/library/job/library-legacy/build | grep -iE '^(HTTP|Location)'
   ```

   Résultat : `HTTP/1.1 201 Created` et `Location: http://localhost:8080/queue/item/<n>/` (l'élément de file d'attente, qui donnera le numéro de build).

7. La même requête avec le mot de passe au lieu du jeton :

   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' -X POST -u admin:Formation-2026 http://localhost:8080/job/library/job/library-legacy/build
   ```

   Résultat : `403`. Avec un mot de passe, un POST doit fournir un *crumb* (protection CSRF, slide 59) ; un jeton d'API en dispense. Pour l'automatisation, toujours un jeton.

**Configuration as Code**

8. **Manage Jenkins → Configuration as Code** : boutons **Apply configuration** et **Export configuration**. Cliquer **Export configuration**.

   La page **Export configuration** affiche le YAML de la configuration actuelle (sections `credentials`, `jenkins`, `appearance`, `security`, `unclassified`, `tool`), avec le bandeau *Export may not offer a directly usable jenkins.yaml configuration*. Le bouton **Download** l'enregistre.

9. Dans la section `credentials`, les secrets apparaissent chiffrés : `privateKey: "{AQAAABAAAAGg...}"`, `password: "{AQAAABAAAAAw...}"`. Ces valeurs ne se déchiffrent qu'avec les clés de `secrets/` de **ce** controller : copiées sur un autre Jenkins, elles ne servent à rien. Dans un `jenkins.yaml` versionné, on les remplace par des variables (`${NEXUS_PASSWORD}`) résolues au démarrage (slide 60).
10. Repérer dans la section `jenkins` : `nodes` (`linux-1`, `linux-2`), `clouds` (`docker-local` et son template), `primaryView` (`Library`, démo 12), `systemMessage` (démo 16). Tout ce qui a été configuré à la main pendant ces démos s'y retrouve.

> **Point clé.** L'export sert de point de départ, pas de fichier final : on en garde les sections utiles, on remplace les secrets par des variables, et le fichier rejoint le dépôt `jenkins-platform` avec le `Dockerfile`, le `plugins.txt` et le seed Job DSL (slide 60). Un controller se reconstruit alors depuis Git ; seuls `secrets/`, les comptes et l'historique des builds relèvent encore de la sauvegarde (démo 15). Avec un annuaire d'entreprise, les comptes eux-mêmes sortent de Jenkins (démo 18).

---

## Démo 18 — Annuaire LDAP : les comptes hors de Jenkins

> Slides : — (complément des habilitations de la partie 1 et de la démo 17) · Durée : 30 min · Prérequis : démo 17 (plugin Configuration as Code) ; plugins **LDAP** et **Role-based Authorization Strategy** (installés par `etat-partie1.sh`)

**Pourquoi.** Depuis le début, les comptes Jenkins sont stockés dans Jenkins (**Jenkins' own user database**) : un fichier par compte dans `JENKINS_HOME/users/`, avec le hash du mot de passe. C'est simple, mais en production cela pose trois problèmes :

- **les départs** : quand une personne quitte l'entreprise, il faut penser à supprimer son compte dans Jenkins, et dans chaque outil qui a sa propre base. Un oubli laisse un accès ouvert ;
- **les groupes** : une base interne ne connaît pas de groupes. On attribue les rôles personne par personne, et `submitter: 'release-managers'` est impossible (écart noté à la démo 17 de la partie 1) ;
- **les mots de passe** : Jenkins a sa propre politique, sans MFA, différente de celle de l'entreprise.

En production, les comptes vivent donc dans l'**annuaire de l'entreprise** (LDAP, Active Directory, ou un SSO OIDC/SAML comme Keycloak ou Entra ID), géré par le service informatique. Jenkins ne fait que le consulter : il vérifie le mot de passe et lit les groupes. Les droits Jenkins sont donnés aux **groupes** de l'annuaire, jamais aux personnes.

La stack utilise **LLDAP**, un serveur LDAP léger avec une interface web. Les réglages Jenkins sont les mêmes qu'avec OpenLDAP ; avec Active Directory, seuls les noms d'attributs changent (`sAMAccountName` au lieu de `uid`, par exemple).

**Ce qu'elle montre.** Un annuaire avec des personnes et des groupes, le test de la connexion LDAP depuis Jenkins avant d'enregistrer, la bascule de l'authentification et des rôles en une seule opération JCasC, l'effet du retrait d'un groupe dans l'annuaire, ce qui reste dans `JENKINS_HOME`, et le retour arrière.

### Étapes

**Démarrer et remplir l'annuaire**

1. Démarrer LLDAP :

   ```bash
   docker compose --profile annuaire up -d lldap
   ```

2. Créer les comptes et les groupes décrits dans `annuaire/` :

   ```bash
   docker exec lldap /app/bootstrap.sh
   ```

   Sous Windows avec Git Bash, préfixer par `MSYS_NO_PATHCONV=1` (sinon `/app/bootstrap.sh` est transformé en chemin Windows). Résultat : `Group "jenkins-admins" (4) successfully created`..., puis pour chaque personne `User "alice.martin" successfully created` et `successfully added to the group`. Relancé, le script ne recrée rien et remet les appartenances aux groupes décrites dans les fichiers.

3. Ouvrir **http://localhost:17170** et se connecter en `annuaire-admin` / `Annuaire-2026`. La page **Users** liste les comptes, **Groups** les groupes :

   | Compte | Mot de passe | Groupe | Rôle visé dans Jenkins |
   |---|---|---|---|
   | `alice.martin` | `Alice-2026` | `jenkins-admins` | administratrice |
   | `bruno.petit` | `Bruno-2026` | `library-dev` | développeur du dossier `library` |
   | `chloe.durand` | `Chloe-2026` | `release-managers` | lance le job `library/deploy` |
   | `david.leroy` | `David-2026` | aucun | lecture seule |
   | `jenkins-bind` | `Bind-2026-lecture` | `lldap_strict_readonly` | compte de service de Jenkins |

   *Pourquoi on regarde cet écran :* ce n'est pas l'écran de l'administrateur Jenkins, c'est celui du service informatique. Créer, désactiver une personne ou changer ses groupes se fait **ici**, une seule fois pour tous les outils de l'entreprise. L'administrateur Jenkins, lui, décide seulement quels droits donne chaque groupe.

   *Pourquoi un compte `jenkins-bind` :* pour retrouver un utilisateur et ses groupes, Jenkins doit interroger l'annuaire avant même que la personne soit connectée. Il utilise pour cela un compte de service, limité à la lecture (`lldap_strict_readonly`) : même volé, son mot de passe ne permet de rien modifier.

   L'administrateur de l'annuaire s'appelle volontairement `annuaire-admin`, et pas `admin` : sinon, il existerait dans l'annuaire un `admin` sans rapport avec celui de Jenkins, ce qui rendrait la démo confuse.

**Tester la connexion LDAP sans rien enregistrer**

4. Jenkins, connecté en `admin` : **Manage Jenkins → Security** → **Security Realm** : choisir **LDAP**. Renseigner (cliquer **Advanced Server Configuration** pour afficher les champs qui n'apparaissent pas) :

   | Champ | Valeur | Rôle |
   |---|---|---|
   | **Server** | `ldap://lldap:3890` | adresse de l'annuaire, vue depuis le conteneur Jenkins |
   | **root DN** | `dc=formation,dc=local` | racine de l'arbre de l'annuaire |
   | **User search base** | `ou=people` | branche où sont rangées les personnes |
   | **User search filter** | `uid={0}` | `{0}` est remplacé par l'identifiant saisi à la connexion |
   | **Group search base** | `ou=groups` | branche des groupes |
   | **Group search filter** | `(&(objectClass=groupOfUniqueNames)(cn={0}))` | comment reconnaître un groupe |
   | **Group membership** | **Search for LDAP groups containing user**, filtre `(member={0})` | comment trouver les groupes d'une personne |
   | **Manager DN** | `uid=jenkins-bind,ou=people,dc=formation,dc=local` | le compte de service |
   | **Manager Password** | `Bind-2026-lecture` | |
   | **Display Name LDAP attribute** | `cn` | nom affiché en haut à droite |
   | **Email Address LDAP attribute** | `mail` | adresse utilisée par les notifications (`culprits()`, partie 1 démo 13) |

5. Cliquer **Test LDAP settings**, saisir **User** `alice.martin`, **Password** `Alice-2026`, puis **Test**.

   Résultat attendu : une liste de contrôles, dont `Authentication: successful`, `User lookup: successful`, `User Display Name: Alice Martin`, `User email: alice.martin@formation.local`, `LDAP Group membership:` avec `jenkins-admins`, et `LDAP Group lookup: successful (1 group)`.

   *Pourquoi tester avant d'enregistrer :* une erreur dans ces champs (filtre faux, mot de passe du compte de service erroné) empêcherait **tout le monde** de se connecter dès l'enregistrement, administrateur compris. Le bouton de test valide la configuration sans l'appliquer. On teste avec un compte qui appartient à un groupe, sinon la recherche des groupes n'est pas vérifiée.

6. **Ne pas cliquer Save.** Quitter la page (logo Jenkins), et confirmer l'abandon des modifications si le navigateur le demande.

   *Pourquoi ne pas enregistrer ici :* l'autorisation est toujours **Logged-in users can do anything** (partie 1, démo 1). Enregistrer maintenant ferait de **toute personne de l'annuaire** un administrateur de Jenkins, `david.leroy` compris. Il faut changer l'authentification et l'autorisation **en même temps** : c'est ce que fait l'étape suivante.

**Basculer l'authentification et les rôles en une seule opération (JCasC)**

7. Lire `annuaire/jenkins-ldap.yaml` :
   - `securityRealm.ldap` reprend les champs de l'étape 4 ;
   - `authorizationStrategy.roleBased` définit les rôles de la partie 1 (démo 16), mais les attribue à des **groupes** : `admin` → `jenkins-admins`, `reader` → `authenticated`, `library-dev` → `library-dev`, `library-release` → `release-managers` (motif `library(/deploy)?`) ;
   - le mot de passe du compte de service n'y figure pas : `managerPasswordSecret: "${LDAP_BIND_PASSWORD}"`.

   *Pourquoi JCasC plutôt que l'écran Security :* le fichier change les deux réglages d'un coup. Il n'y a pas d'instant où Jenkins a un annuaire mais pas encore de rôles. Le fichier se relit en revue de code et se versionne dans le dépôt `jenkins-platform` (démo 17), et on peut le réappliquer à l'identique sur un autre controller.

8. Déposer le secret et le fichier dans le conteneur Jenkins :

   ```bash
   docker exec -u root jenkins sh -c 'mkdir -p /run/secrets && printf %s "Bind-2026-lecture" > /run/secrets/LDAP_BIND_PASSWORD && chown jenkins /run/secrets/LDAP_BIND_PASSWORD && chmod 400 /run/secrets/LDAP_BIND_PASSWORD'
   ```

   ```bash
   docker exec jenkins mkdir -p /var/jenkins_home/casc
   ```

   ```bash
   docker cp annuaire/jenkins-ldap.yaml jenkins:/var/jenkins_home/casc/jenkins-ldap.yaml
   ```

   *Pourquoi `/run/secrets` :* c'est l'emplacement où Docker (secrets Compose ou Swarm) et Kubernetes montent les secrets. JCasC y cherche un fichier du nom de la variable (`LDAP_BIND_PASSWORD`) et en lit la valeur au moment de l'application. Le secret reste ainsi hors du fichier YAML versionné. Ici on l'écrit à la main ; en production, il est fourni par l'orchestrateur ou un coffre-fort (Vault).

9. **Manage Jenkins → Configuration as Code** → bouton **Apply configuration**. Boîte **Apply Configuration as Code file**, champ **Path or URL** : `/var/jenkins_home/casc/jenkins-ldap.yaml` → **Apply configuration**.

   Résultat : la page affiche **Access Denied**, `admin is missing a permission, one of Overall/Manage, Overall/Administer is required`.

   *Pourquoi c'est le résultat attendu :* la session ouverte est celle du compte **local** `admin`. Pour la nouvelle configuration, `admin` n'appartient à aucun groupe de l'annuaire : il ne garde que le rôle `reader` des connectés. Le reste de la configuration (agents, outils, credentials, message système) n'a pas changé : JCasC ne touche qu'aux sections présentes dans le fichier.

10. Se déconnecter (icône personnage → **Sign out**), puis essayer `admin` / `Formation-2026` : **refusé**. Le compte local existe toujours dans `JENKINS_HOME/users/`, mais Jenkins ne le consulte plus : seul l'annuaire fait foi.

    Les jetons d'API d'`admin` (CLI, supervision, sauvegarde : démos 14 à 17) sont refusés eux aussi pendant toute la démo. Ils fonctionneront de nouveau après le retour arrière (étape 19).

11. Se connecter en `alice.martin` / `Alice-2026` :
    - en haut à droite s'affiche **Alice Martin** (attribut `cn`), et **Manage Jenkins** est accessible ;
    - ouvrir **http://localhost:8080/whoAmI/** : **Authorities** liste `"jenkins-admins"`, `"authenticated"` et `"ROLE_JENKINS-ADMINS"`. Ce sont les groupes lus dans l'annuaire ; le préfixe `ROLE_` est une copie en majuscules ajoutée par le plugin LDAP ;
    - **Manage Jenkins → Role Management** (page **Assign Roles**), onglet **Global roles** : la ligne **authenticated** porte `reader`, et une ligne **jenkins-admins** porte `admin`. Aucune personne n'y figure.

**Vérifier chaque profil**

12. Dans une fenêtre de navigation privée, se connecter successivement avec chaque compte (icône personnage → **Sign out** entre deux) :

    | Compte | Ce qu'on constate |
    |---|---|
    | `bruno.petit` | seul le dossier `library` est visible ; dedans, tous les jobs, avec **Build Now** et **Configure** ; **Manage Jenkins** absent |
    | `chloe.durand` | le dossier `library` ne contient que `deploy` ; **Build with Parameters** présent, **Configure** absent |
    | `david.leroy` | tableau de bord vide : il est connecté (rôle `reader` via `authenticated`) mais n'a aucun droit sur les jobs |

    *Pourquoi :* les rôles sont exactement ceux de la partie 1, mais aucun n'est attribué à une personne. Pour donner les droits de développeur à quelqu'un, on l'ajoute au groupe `library-dev` dans l'annuaire, sans toucher à Jenkins.

**Le départ d'un développeur**

13. Fenêtre privée : se connecter en `bruno.petit` et ouvrir le dossier `library`.
14. Fenêtre normale, LLDAP (http://localhost:17170) → **Users** → `bruno.petit` → bloc **Group memberships** : supprimer la ligne `library-dev` (icône corbeille au bout de la ligne).
15. Dans la fenêtre de Bruno, recharger la page : **le dossier est toujours visible**, et http://localhost:8080/whoAmI/ affiche encore `"library-dev"`.

    *Pourquoi :* Jenkins lit les groupes d'une personne **à sa connexion** et les garde dans sa session. Un retrait de groupe ne s'applique qu'à la connexion suivante. C'est un point important lors d'un départ : retirer le compte de l'annuaire ne coupe pas une session déjà ouverte.

16. Fenêtre normale, Jenkins en `alice.martin` : ouvrir **http://localhost:8080/user/bruno.petit/security/** → bloc **Session Termination** → **Terminate All Sessions** → confirmer.

    Avec un annuaire, **Manage Jenkins** n'a plus d'entrée **Users** : elle ne sert qu'à gérer la base interne. La page d'une personne s'ouvre par son URL `/user/<identifiant>/`, ou en cliquant son nom dans l'historique d'un build qu'elle a lancé.

    Dans la fenêtre de Bruno, recharger : il n'est plus connecté. S'il se reconnecte, le dossier `library` répond **Not Found** : il n'a plus que le rôle `reader`.

    *Que retenir pour un départ :* l'annuaire retire les droits ; **Terminate All Sessions** les retire immédiatement. Les **jetons d'API** n'ont pas ce délai : à chaque appel, Jenkins relit les groupes dans l'annuaire, et un jeton dont le compte a été supprimé de l'annuaire est refusé.

17. Remettre Bruno dans son groupe : relancer `docker exec lldap /app/bootstrap.sh` (ou, dans LLDAP, **Add to group** → `library-dev` sur la page de `bruno.petit`).

**Ce qui reste dans JENKINS_HOME**

18. Lister les comptes connus de Jenkins, puis ceux qui ont encore un mot de passe stocké :

    ```bash
    docker exec jenkins ls /var/jenkins_home/users
    ```

    ```bash
    docker exec jenkins sh -c 'grep -l passwordHash /var/jenkins_home/users/*/config.xml'
    ```

    Résultat : un répertoire par personne qui s'est connectée (`alicemartin_...`, `brunopetit_...`, ...) à côté de `admin_...`, mais seul `admin` a un `passwordHash`.

    *Que faire de l'info :* c'est la réponse à « où vivent les comptes en production » :

    | Donnée | Où elle vit | Comment on la protège |
    |---|---|---|
    | Identité, mot de passe, groupes | l'annuaire de l'entreprise | sauvegarde et politique du service informatique |
    | Réglages LDAP et rôles | `jenkins-ldap.yaml` dans le dépôt `jenkins-platform` | Git, revue de code (démo 17) |
    | Mot de passe du compte de service | coffre-fort ou secret de l'orchestrateur ; copie chiffrée dans `config.xml` | `secrets/` (démo 15) |
    | Jetons d'API, préférences, vues personnelles | `JENKINS_HOME/users/` | sauvegarde de `JENKINS_HOME` (démo 15) |

    `users/` reste donc dans la sauvegarde, mais il ne contient plus de mots de passe : perdre ce répertoire coûte des jetons à régénérer, pas des comptes à recréer.

**Revenir à la base locale**

19. Appliquer le fichier de retour, toujours connecté en `alice.martin` :

    ```bash
    docker cp annuaire/retour-base-locale.yaml jenkins:/var/jenkins_home/casc/retour-base-locale.yaml
    ```

    **Manage Jenkins → Configuration as Code → Apply configuration** → **Path or URL** : `/var/jenkins_home/casc/retour-base-locale.yaml` → **Apply configuration**. Se déconnecter : `admin` / `Formation-2026` fonctionne de nouveau, `alice.martin` est refusée.

    *Pourquoi ce retour fonctionne :* le compte local `admin` n'a jamais été supprimé (étape 18). Ce fichier est aussi la **procédure de secours** : si l'annuaire tombe en panne ou si un réglage erroné bloque tout le monde, réappliquer une configuration connue rend la main. Sans accès à l'interface, on passe par le disque, comme à la démo 16 de la partie 1 (`<useSecurity>false</useSecurity>` dans `config.xml`).

20. Arrêter l'annuaire :

    ```bash
    docker compose --profile annuaire stop lldap
    ```

> **Point clé.** En production, trois réglages changent par rapport à cette démo : `ldaps://` (ou StartTLS) au lieu de `ldap://`, car le mot de passe de chaque personne transite à la connexion ; un **compte de secours** documenté, pour le jour où l'annuaire est injoignable ; et des noms de groupes qui suivent la convention de l'annuaire de l'entreprise (`GG-Jenkins-Admins`, par exemple). Avec un SSO (plugin **OpenId Connect Authentication**), la mécanique est identique : Jenkins délègue la connexion et reçoit les groupes dans le jeton, et les rôles s'attribuent toujours à ces groupes. Le groupe `release-managers` devient alors utilisable dans `input submitter: 'release-managers'`.

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| `exec: "C:/Program Files/Git/app/bootstrap.sh": ... no such file` | Git Bash convertit le chemin | `MSYS_NO_PATHCONV=1 docker exec lldap /app/bootstrap.sh` |
| **Test LDAP settings** : `Authentication: failed` | Mot de passe de la personne erroné, ou mauvais **User search base** / **User search filter** | Vérifier le compte dans LLDAP, puis les champs de l'étape 4 |
| Connexion acceptée mais aucun groupe dans **whoAmI** | Filtre de groupe erroné, ou personne sans groupe | Refaire le test de l'étape 5 avec `alice.martin` |
| Après l'étape 9, aucun compte de l'annuaire ne peut se connecter | Fichier `/run/secrets/LDAP_BIND_PASSWORD` absent (conteneur Jenkins recréé) ou contenu faux : Jenkins ne peut plus interroger l'annuaire | Refaire l'étape 8, puis réappliquer le fichier (étape 9) en passant par l'étape 19 si plus personne n'est administrateur |
| Plus personne ne peut se connecter | Annuaire arrêté ou configuration erronée | `docker compose --profile annuaire up -d lldap` ; sinon étape 19 en passant par `config.xml` |

---

## Remise à zéro

| Besoin | Commande |
|---|---|
| Arrêter les services de la partie 2 en gardant tout | `docker compose --profile cluster --profile monitoring down` |
| Supprimer les conteneurs déployés par la démo 8 | `docker rm -f library-api-dev library-api-recette library-api-prod` |
| Supprimer le Jenkins de test de la démo 15 | `docker rm -f jenkins-restaure` puis `docker volume rm jenkins-formation_jenkins_home_restaure` |
| Repartir d'un Jenkins vierge (partie 1 et partie 2) | dans `../1-demos-jenkins-ci` : `docker compose --profile deploiement --profile qualite down -v`, puis démo 0 de ce document |
| Supprimer le cache Maven du script de mise en état | `docker volume rm etat-m2` |
| Revenir aux comptes locaux après la démo 18 | étape 19 de la démo 18 (`annuaire/retour-base-locale.yaml`) |
| Supprimer l'annuaire et ses comptes | `docker compose --profile annuaire down` puis `docker volume rm jenkins-formation-p2_lldap_data` |
