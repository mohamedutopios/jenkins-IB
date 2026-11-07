# Démos Jenkins CI — pas à pas dans l'interface

Support associé : `1-formation-jenkins-ci-slides-v1.2.html` (parties 2 et 3).
Fil rouge : **library-api**, API REST Spring Boot 3.5 / Java 21 / Maven, hébergée sur un serveur Git local et construite par Jenkins.

Tout tourne dans des conteneurs Docker sur le poste : Jenkins (controller), un agent SSH, le serveur Git, un serveur SMTP de test, puis Nexus et SonarQube pour les dernières démos.

Versions de référence (celles des libellés de ce document) : Jenkins **2.580.2 LTS** (JDK 21), Gitea **1.24.7**, Maven **3.9.16**, Nexus **3.97.3**, SonarQube Community Build **26.10**. Les interfaces évoluent vite d’une version à l’autre (menus, boîtes de dialogue) : garder les versions figées dans `.env` et `docker-compose.yml` pour que les écrans correspondent.

---

## Sommaire

| Démo | Sujet | Slides | Durée |
|---|---|---|---|
| [0](#démo-0--démarrer-lenvironnement) | Démarrer l'environnement | 40 | 10 min |
| [1](#démo-1--installer-jenkins-et-passer-lassistant) | Installer Jenkins et passer l'assistant | 39 à 42 | 15 min |
| [2](#démo-2--premier-job-freestyle-et-visite-guidée) | Premier job Freestyle et visite guidée | 22, 24, 35 à 37, 42 | 15 min |
| [3](#démo-3--déclencheurs-et-statuts-de-build) | Déclencheurs et statuts de build | 29, 30, 32, 33 | 20 min |
| [4](#démo-4--le-workspace) | Le workspace | 34 | 10 min |
| [5](#démo-5--configuration-system-et-agent-ssh) | Configuration System et agent SSH | 23, 43, 46 | 20 min |
| [6](#démo-6--installer-les-plugins-de-la-partie-3) | Installer les plugins de la partie 3 | 47 à 49 | 10 min |
| [7](#démo-7--tools-et-credentials) | Tools et credentials | 44, 45, 56 | 15 min |
| [8](#démo-8--job-freestyle-library-api) | Job Freestyle library-api | 54, 56, 58 | 20 min |
| [9](#démo-9--job-pipeline-et-jenkinsfile) | Job Pipeline et Jenkinsfile | 26 à 28, 33, 38, 55 | 25 min |
| [10](#démo-10--multibranch-pipeline-et-webhook) | Multibranch Pipeline et webhook | 31, 55 à 57 | 25 min |
| [11](#démo-11--paramétrage-maven-et-build-paramétré) | Paramétrage Maven et build paramétré | 58 à 60 | 15 min |
| [12](#démo-12--rapports-de-tests-et-couverture) | Rapports de tests et couverture | 32, 61 à 63 | 20 min |
| [13](#démo-13--notifications-par-mail) | Notifications par mail | 64 à 66 | 15 min |
| [14](#démo-14--déploiement-automatique) | Déploiement automatique | 67 à 70 | 30 min |
| [15](#démo-15--analyse-qualité-avec-sonarqube) | Analyse qualité avec SonarQube | 71 à 73 | 25 min |
| [16](#démo-16--habilitations) | Habilitations | 74 à 77 | 25 min |
| [17](#démo-17--pipeline-complet-du-fil-rouge) | Pipeline complet du fil rouge | 78, 79 | 20 min |

Les démos s'enchaînent : chacune part de l'état laissé par la précédente.

---

## Contenu du kit

```
1-demos-jenkins-ci/
├── DEMOS.md                  ce document
├── MANAGE-JENKINS.md         visite guidée des pages de Manage Jenkins (démo 2)
├── docker-compose.yml        jenkins, linux-1, gitea, mailpit (+ nexus, sonarqube)
├── .env                      versions, ports, compte Gitea, clé de l'agent
├── agent/                    image de l'agent SSH linux-1 : JDK 21, Git, client Docker
│                             (acces-docker.sh donne à jenkins l'accès à la socket Docker)
├── scripts/
│   ├── preparer.sh           génère la clé SSH controller -> agent
│   └── init-gitea.sh         crée le dépôt privé formation/library-api et y pousse le projet
├── keys/                     clé SSH générée (ne pas versionner)
└── library-api/              projet du fil rouge, poussé dans Gitea
    ├── pom.xml               Spring Boot 3.5.6, JaCoCo, Failsafe, version ${revision}
    ├── Dockerfile            image d'exécution (slide 69)
    ├── Jenkinsfile           pipeline minimal (démos 9 et 10)
    └── ci/                   un Jenkinsfile par démo (parametres, tests, mail, deploiement, qualite, complet)
```

## Adresses de la stack

| Service | Depuis le navigateur | Depuis les conteneurs | Compte |
|---|---|---|---|
| Jenkins | http://localhost:8080 | http://jenkins:8080 | créé à la démo 1 : `admin` / `admin` |
| Gitea (Git) | http://localhost:3000 | http://gitea:3000 | `formation` / `Formation-2026` |
| Mailpit (SMTP de test) | http://localhost:8025 | SMTP `mailpit:1025` | aucun |
| Nexus | http://localhost:8081 | http://nexus:8081 | démo 14 |
| SonarQube | http://localhost:9000 | http://sonarqube:9000 | démo 15 |
| library-api (recette / prod) | http://localhost:8090, http://localhost:8091 | `library-api-recette:8080` | aucun |

Les mots de passe ci-dessus sont des valeurs de formation, propres à cette stack locale.

---

## Démo 0 — Démarrer l'environnement

> Slides : 40 · Durée : 10 min · Prérequis : Docker Desktop (ou Docker Engine + Compose v2), 8 Go de RAM alloués à Docker, accès Internet (images, plugins, dépendances Maven)

**Pourquoi.** Toutes les démos utilisent le même environnement, décrit dans un seul fichier `docker-compose.yml`. Le préparer une fois évite de mélanger l'installation de l'outillage et l'apprentissage de Jenkins. On reprend ici la proposition de la slide 40 (Jenkins en conteneur avec un volume pour `JENKINS_HOME`), complétée par un serveur Git local : sans lui, il faudrait un compte GitHub et un tunnel (ngrok, smee.io) pour que les webhooks atteignent le Jenkins du poste.

**Ce qu'elle montre.** Un Jenkins « nu » (image officielle, aucun plugin préinstallé) qui attend son assistant de premier démarrage, un agent SSH prêt à recevoir des builds, et le dépôt Git privé `formation/library-api` qui contient le projet du fil rouge et ses Jenkinsfiles.

### Étapes

1. Ouvrir un terminal dans le dossier du kit :

   ```bash
   cd 1-demos-jenkins-ci
   ```

2. Vérifier que les ports de `.env` sont libres (8080, 3000, 8025, 8081, 9000). Si l'un d'eux est pris, changer sa valeur dans `.env` (par exemple `SONAR_PORT=9001`) : seules les adresses « depuis le navigateur » changent, les conteneurs continuent de se joindre par leur nom.

   ```bash
   lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8080|3000|8025|8081|9000) '
   ```

3. Générer la clé SSH que le controller utilisera pour se connecter à l'agent (elle est reportée automatiquement dans `.env`) :

   ```bash
   ./scripts/preparer.sh
   ```

   Résultat : `keys/jenkins_agent` (clé privée, à coller dans Jenkins à la démo 5) et `keys/jenkins_agent.pub`.

4. Construire l'image de l'agent et démarrer les quatre services de base :

   ```bash
   docker compose up -d --build
   ```

   ```bash
   docker compose ps
   ```

   Résultat attendu : `jenkins`, `linux-1`, `gitea` et `mailpit` à l'état `running`. Nexus et SonarQube ne démarrent pas encore (profils `deploiement` et `qualite`).

5. Créer le compte Gitea et le dépôt privé, puis y pousser le projet :

   ```bash
   ./scripts/init-gitea.sh
   ```

6. Dans le navigateur, ouvrir **http://localhost:3000**, cliquer **Sign In** (en haut à droite), se connecter avec `formation` / `Formation-2026`, puis ouvrir le dépôt **formation/library-api**.

   Résultat attendu : le dépôt est marqué **Private**, la branche `main` contient `pom.xml`, `Jenkinsfile`, `Dockerfile`, `src/` et `ci/`.

7. Ouvrir **http://localhost:8080** : la page **Débloquer Jenkins** (« Unlock Jenkins ») s'affiche. On s'arrête là ; la démo 1 commence sur cet écran.

> **Point clé.** `docker compose down` arrête la stack sans rien perdre : `JENKINS_HOME`, le dépôt Gitea et le cache Maven sont dans des volumes nommés. Seul `docker compose down -v` efface tout (utile pour rejouer la démo 1 depuis zéro).

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| `Bind for 0.0.0.0:8080 failed: port is already allocated` | Un autre service écoute sur le port | Changer `JENKINS_PORT` dans `.env`, relancer `docker compose up -d` |
| `init-gitea.sh` reste sur « Attente de Gitea » | Gitea démarre encore (première initialisation) | Attendre 30 s ; `docker logs gitea` |
| Le push échoue avec `403` | Le compte existait avec un autre mot de passe | `docker compose down -v` puis reprendre à l'étape 4 |
| `linux-1` redémarre en boucle, `docker logs linux-1` : `exec /usr/local/bin/acces-docker.sh: no such file or directory` | Le script a des fins de ligne Windows (CRLF) : kit récupéré avant l'ajout de `.gitattributes`, ou copié sans Git | `git pull`, puis `docker compose up -d --build linux-1` (le Dockerfile retire aussi les CRLF) |

---

## Démo 1 — Installer Jenkins et passer l'assistant

> Slides : 39 à 42 · Durée : 15 min (plus le téléchargement des plugins) · Prérequis : démo 0

**Pourquoi.** Le premier démarrage fixe trois choses qui conditionnent tout le reste : le compte administrateur, la liste des plugins de départ et l'URL publique de Jenkins (utilisée dans les liens des mails et des webhooks). La slide 42 décrit ces étapes ; les faire une fois en conditions réelles permet de voir où Jenkins range son état (`JENKINS_HOME`) et comment vérifier une installation saine.

**Ce qu'elle montre.** Le déblocage par le mot de passe initial lu dans le conteneur, l'installation des plugins suggérés, la création de l'administrateur, puis les vérifications d'après installation : version, JVM, `JENKINS_HOME` et stratégie d'autorisation par défaut.

### Étapes

> L'assistant s'affiche dans la langue du navigateur. Les libellés sont donnés en français, avec l'anglais entre parenthèses. À la fin de la démo, l'interface est forcée en anglais pour correspondre aux slides.

**Débloquer Jenkins**

1. Lire le mot de passe initial :

   ```bash
   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```

2. Sur http://localhost:8080, écran **Débloquer Jenkins** (*Unlock Jenkins*) : coller la valeur dans **Mot de passe administrateur** (*Administrator password*), puis cliquer **Continuer** (*Continue*) ou appuyer sur Entrée.

**Choisir les plugins**

3. Écran **Personnaliser Jenkins** (*Customize Jenkins*) : cliquer **Sélectionner les plugins à installer** (*Select plugins to install*).

   La liste s'ouvre avec les plugins recommandés déjà cochés (compteur **Sélectionnés (18/52)** en haut à droite).

4. Dans le champ de recherche en haut de la liste, taper `Locale`, puis cocher **Locale** (catégorie *Languages*). Le compteur passe à **19/52**.

5. Cliquer **Installer** (*Install*), en bas à droite.

   Résultat : l'écran **Installation en cours...** affiche une case par plugin ; elle devient verte une fois le plugin installé. Les dépendances apparaissent dans le journal de droite, préfixées par `**`. Une centaine de plugins sont téléchargés (93 avec les dépendances) : compter 5 minutes avec une bonne connexion, beaucoup plus sur un réseau lent (26 minutes mesurées à 60 Ko/s).

> **Point clé.** Les plugins « suggérés » ne contiennent ni Maven Integration, ni Coverage, ni SonarQube : ils seront ajoutés à la démo 6, au moment où la partie 3 en a besoin (slide 42, dernière ligne du cadre). JUnit, lui, arrive comme dépendance du plugin Pipeline.

**Créer l'administrateur et l'URL**

6. Écran **Créer le 1er utilisateur Administrateur** (*Create First Admin User*) :

   | Champ | Valeur |
   |---|---|
   | Nom d'utilisateur (*Username*) | `admin` |
   | Mot de passe (*Password*) | `Formation-2026` |
   | Confirmation du mot de passe (*Confirm password*) | `Formation-2026` |
   | Nom complet (*Full name*) | `Administrateur Jenkins` |
   | Email (*E-mail address*) | `admin@example.com` |

   Cliquer **Sauver et continuer** (*Save and Continue*), en bas à droite. Ne pas utiliser **Continuer en tant qu'Administrateur** : on garderait le compte `admin` avec le mot de passe initial.

7. Écran **Configuration de l'instance** (*Instance Configuration*) : laisser **URL de Jenkins :** (*Jenkins URL*) à `http://localhost:8080/`, cliquer **Sauver et terminer** (*Save and Finish*).
8. Écran **Jenkins est prêt !** (*Jenkins is ready!*) : cliquer **Commencer à utiliser Jenkins** (*Start using Jenkins*).

   Résultat : le tableau de bord vide, titré **Bienvenue sur Jenkins !** (*Welcome to Jenkins!*), avec les raccourcis **Créer un job** et **Mettre en place un agent**.

**Forcer l'interface en anglais**

9. Cliquer l'icône engrenage en haut à droite (**Administrer Jenkins** / *Manage Jenkins*), puis, dans le bloc **Configuration du système**, la tuile **Apparence générale** (*Appearance*).

10. Liste **Default Language** : choisir **English - en** (et non la première entrée, *Use Default Locale*). Cocher **Ignore browser preference and force this language to all users**, puis cliquer **Save**.

    Résultat : toute l'interface passe en anglais, comme dans les slides. Les démos suivantes utilisent ces libellés.

> **Repères de navigation (Jenkins 2.5xx).** Le menu de gauche du tableau de bord ne contient plus que **New Item** et **Build History**. **Manage Jenkins** est l'icône engrenage en haut à droite ; l'icône personnage à côté ouvre le menu de l'utilisateur connecté (**Security**, **Appearance**...) ; la loupe ouvre la recherche.

**Vérifier l'installation (slide 42, cadre « Vérifications après installation »)**

11. **Manage Jenkins → System Information** : relever la version de Jenkins (pied de page, en bas à droite), `java.version` (21) et `JENKINS_HOME` (`/var/jenkins_home`) dans **System Properties** / **Environment Variables**.

12. Revenir sur **Manage Jenkins** et lire les bandeaux du haut (slide 37, *Administration Monitors*) :
    - **Building on the built-in node can be a security issue. You should set up distributed builds.** : attendu, traité à la démo 5 ;
    - **Java 21 end of life in Jenkins** : information sur la fin du support de Java 21 (septembre 2027) ;
    - un message sur la **Content Security Policy**, désactivée par défaut.

    Aucun bandeau ne doit signaler de plugin vulnérable.

13. **Manage Jenkins → Security** : **Security Realm** = **Jenkins' own user database** (avec **Allow users to sign up** décoché) et **Authorization** = **Logged-in users can do anything** (avec **Allow anonymous read access** décoché). C'est le réglage par défaut, durci à la démo 16.

14. Dans le terminal, regarder ce que contient `JENKINS_HOME` :

    ```bash
    docker exec jenkins ls /var/jenkins_home
    ```

    Résultat : `config.xml`, `jobs/`, `plugins/`, `secrets/`, `users/`, `nodes/`... (slide 39). Sauvegarder ce répertoire, c'est sauvegarder Jenkins.

> **À retenir.** L'assistant ne s'affiche qu'une fois : il écrit son état dans `JENKINS_HOME`. Pour le rejouer, il faut repartir d'un volume vide (`docker compose down -v`). En production, on le désactive (`-Djenkins.install.runSetupWizard=false`) et on décrit l'instance en JCasC (slide 42).

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| Un plugin reste en échec (case rouge) | Téléchargement interrompu | Bouton **Réessayer** (*Retry*) en bas de l'écran ; sinon continuer et le réinstaller à la démo 6 |
| « Jenkins est hors ligne » (*This Jenkins instance appears to be offline*) | Pas d'accès à updates.jenkins.io (proxy) | Configurer le proxy à l'écran suivant, ou `docker compose down -v` après correction réseau |
| Mot de passe initial introuvable | Le volume contient déjà une instance configurée | Se connecter avec le compte existant, ou repartir de zéro avec `docker compose down -v` |

---

## Démo 2 — Premier job Freestyle et visite guidée

> Slides : 22, 24, 35 à 37, 42 · Durée : 15 min · Prérequis : démo 1

**Pourquoi.** Avant de construire une application, il faut savoir lire Jenkins : ce qu'est un item, un build, un executor, où se trouve la console, ce que contiennent les variables d'environnement. Un job qui ne fait qu'un `echo` suffit pour parcourir toutes les pages décrites aux slides 35 à 37, sans qu'une erreur de compilation ou de Git vienne brouiller la lecture.

**Ce qu'elle montre.** La création d'un item Freestyle, son exécution sur le node built-in (le controller, qui a encore 2 executors), la page du build, la console, les variables fournies par Jenkins (slide 24), puis le tour de **Manage Jenkins**.

### Étapes

**Créer le job `hello` (slide 42, dernière vérification)**

1. Tableau de bord → menu de gauche **New Item**.
2. **Enter an item name** : `hello`. Choisir **Freestyle project**, cliquer **OK**.
3. Page de configuration, section **General** : **Description** = `Premier job : affiche des variables d'environnement`.
4. Dans le menu de gauche de la page de configuration, cliquer **Build Steps** → bouton **Add build step** → **Execute shell**. Cliquer dans la zone **Command** (le lien **See the list of available environment variables** juste au-dessus ouvre la liste des variables) et coller :

   ```bash
   echo "Hello $BUILD_NUMBER"
   echo "Job       : $JOB_NAME"
   echo "Node      : $NODE_NAME (executor $EXECUTOR_NUMBER)"
   echo "Workspace : $WORKSPACE"
   echo "Build URL : $BUILD_URL"
   hostname
   ```

5. Cliquer **Save**. Jenkins affiche la page du job.

**Lancer et lire un build**

6. Menu du job → **Build Now**. Le build **#1** apparaît dans le cadre **Builds** (colonne de gauche, sous **Today**), avec une coche verte une fois terminé.
7. Cliquer **#1** → **Console Output**.

   Résultat attendu :

   ```
   Started by user Administrateur Jenkins
   Running as SYSTEM
   Building in workspace /var/jenkins_home/workspace/hello
   ...
   Hello 1
   Job       : hello
   Node      : built-in (executor 1)
   ...
   Finished: SUCCESS
   ```

   Le build tourne sur le controller (**built-in**) : il n'y a pas encore d'agent. La démo 5 corrige cela.

8. Relancer deux fois **Build Now**. Revenir sur la page du job : la liste des builds (#3, #2, #1) et la tendance s'affichent.

**Parcourir l'interface (slides 35 à 37)**

9. **Dashboard** (logo Jenkins en haut à gauche) : repérer
   - la liste des jobs avec les colonnes **S** (statut), **W** (météo), **Name**, **Last Success**, **Last Failure**, **Last Duration** et, en bout de ligne, l'icône de lancement ;
   - les cadres repliables **Build Queue** et **Build Executor Status** sous le menu de gauche ; le compteur **0/2** indique 0 executor occupé sur 2 (ceux du **Built-In Node**) ;
   - l'onglet de vue **All** et le **+** pour créer une vue ;
   - le message système, s'il a été défini (démo 5).
10. Page du job `hello`, menu de gauche : **Status**, **Changes**, **Workspace**, **Build Now**, **Delete Project**, **Configure**, **Rename**.
11. Page du build **#3** : menu **Status**, **Changes**, **Console Output**, **Delete build ‘#3’**, **Edit build information** ; dans la page, les boutons **Add description** et **Keep this build forever**. Cliquer **Edit build information**, saisir **Display name** = `premier essai`, **Save** : la liste des builds affiche ce nom à la place de `#3`.
12. Ouvrir **http://localhost:8080/env-vars.html** : liste complète des variables fournies aux builds (slide 24).
13. **Manage Jenkins** (engrenage) : parcourir les blocs de la slide 37
    - **System Configuration** : **System**, **Tools**, **Plugins**, **Nodes**, **Clouds**, **Appearance** ;
    - **Security** : **Security**, **Credentials**, **Credential Providers**, **Users** ;
    - **Status Information** : **System Information**, **Logs** (l'ancien *System Log*), **Load Statistics**, **About Jenkins** ;
    - **Troubleshooting** : **Manage Old Data** ;
    - **Tools and Actions** : **Reload Configuration from Disk**, **Jenkins CLI**, **Script Console**, **Prepare for Shutdown**.

    Le contenu de chaque page (sections, champs, boutons) et la démo où l'on s'en sert sont décrits dans [MANAGE-JENKINS.md](MANAGE-JENKINS.md).
14. **Manage Jenkins → Script Console** : saisir `println Jenkins.instance.numExecutors` puis **Run**. Résultat : `2`. Cette console exécute du Groovy avec tous les droits sur le controller (slide 37) : elle est réservée aux administrateurs.

> **Point clé.** Un job Freestyle est stocké dans `JENKINS_HOME/jobs/hello/config.xml` ; chaque build dans `jobs/hello/builds/<n>/`. Vérification : `docker exec jenkins ls /var/jenkins_home/jobs/hello/builds`.

---

## Démo 3 — Déclencheurs et statuts de build

> Slides : 29, 30, 32, 33 · Durée : 20 min · Prérequis : démo 2

**Pourquoi.** Un serveur d'intégration continue n'a de valeur que s'il construit sans qu'on clique : à heure fixe, sur un événement, à la demande d'un autre outil. Et chaque build doit rendre un verdict lisible. Les slides 29 à 32 listent les déclencheurs et les cinq statuts ; les provoquer volontairement sur un job sans risque permet de reconnaître chaque icône et chaque ligne de console avant d'en rencontrer sur un vrai projet.

**Ce qu'elle montre.** Un déclencheur périodique avec le symbole `H`, un déclenchement à distance par URL et jeton, puis les statuts SUCCESS, FAILURE, UNSTABLE, ABORTED et la météo du job.

### Étapes

**Déclencheur périodique (slide 30)**

1. Job `hello` → **Configure** → section **Triggers** → cocher **Build periodically**.
2. **Schedule** : `H/2 * * * *`. Sous le champ, Jenkins affiche **Would last have run at ... ; would next run at ...** : l'heure exacte est calculée à partir du nom du job (symbole `H`).
3. **Save**. Attendre deux minutes : un build démarre seul. Dans sa console, la première ligne est **Started by timer**.
4. Remplacer par `H H(2-4) * * 1-5` (nightly en semaine), **Save**, et relire le message sous le champ. Puis décocher **Build periodically** et **Save** pour ne pas encombrer la suite.

**Déclenchement à distance par jeton (slide 29)**

5. **Configure** → **Triggers** → cocher **Trigger builds remotely (e.g., from scripts)**. **Authentication Token** : `hello-token`. **Save**.
6. Créer un jeton d'API : icône personnage en haut à droite → **Administrateur Jenkins** → menu de gauche **Security** → bloc **API Token** → **Add new token**. Dans la boîte **Create new API token** : **Name** = `demo-cli`, **Expiration** = `30 Days` → **Generate**. Copier la valeur affichée (bouton copie à droite : *Copy this token now, because it cannot be recovered in the future*), puis **Done**. Le jeton apparaît dans **Current token(s)** avec sa date d'expiration ; il est enregistré immédiatement.
7. Dans un terminal :

   ```bash
   export JENKINS_TOKEN=<valeur copiée>
   curl -X POST -u admin:$JENKINS_TOKEN "http://localhost:8080/job/hello/build?token=hello-token"
   ```

   Résultat : un nouveau build dont la console commence par **Started by remote host 192.168.x.x**. Avec un jeton d'API, aucun crumb CSRF n'est demandé (slide 74).

   Sans `-u admin:$JENKINS_TOKEN`, la même URL répond **403** : le jeton du job (`hello-token`) désigne le job à lancer, mais l'appelant doit quand même avoir le droit de lire Jenkins, et l'utilisateur anonyme ne l'a pas.

**Provoquer chaque statut (slide 32)**

8. **Configure** → **Build Steps** : à la fin de la commande, ajouter la ligne `exit 1`. **Save** → **Build Now**.

   Résultat : boule rouge, console terminée par `Build step 'Execute shell' marked build as failure` puis `Finished: FAILURE`.

9. **Configure** → remplacer `exit 1` par `exit 3`. Dans le step **Execute shell**, cliquer **Advanced** et saisir `3` dans **Exit code to set build unstable**. **Save** → **Build Now**.

   Résultat : boule jaune, `Finished: UNSTABLE`. Le build est allé au bout, mais un indicateur est dégradé.

10. **Configure** → remplacer `exit 3` par `sleep 120`. **Save** → **Build Now**. Pendant l'exécution, cliquer la croix rouge à côté de la barre de progression (dans **Builds** ou dans **Build Executor Status**).

    Résultat : boule grise, `Aborted by Administrateur Jenkins` puis `Finished: ABORTED`.

11. **Configure** → supprimer la ligne `sleep 120` (et vider **Exit code to set build unstable**). **Save** → **Build Now**. Le job repasse en SUCCESS.

12. **Dashboard** : la colonne **W** (météo) du job `hello` reflète les 5 derniers builds. Survoler l'icône : **Build stability: 2 out of the last 5 builds failed.** (le texte dépend de l'historique).

**Historique et rétention (slide 33)**

13. **Configure** → **General** → cocher **Discard old builds** → **Strategy** **Log Rotation**, **Max # of builds to keep** = `5`. **Save** → **Build Now**.

    Résultat : seuls les 5 derniers builds restent dans la liste ; les plus anciens ont été supprimés de `JENKINS_HOME`, sauf ceux marqués **Keep this build forever**.

> **À retenir.** Le statut UNSTABLE n'arrête pas le build : il signale « ça tourne mais un indicateur est rouge ». En partie 3, c'est le step `junit` qui le positionne quand des tests échouent (démo 12).

---

## Démo 4 — Le workspace

> Slides : 34 · Durée : 10 min · Prérequis : démo 3

**Pourquoi.** Le workspace est le répertoire où un build travaille. Il est réutilisé d'un build à l'autre : un fichier oublié par un build précédent peut faire passer (ou casser) le suivant. Comprendre où il se trouve, quand il est réutilisé et comment le nettoyer évite des builds « qui ne marchent que sur Jenkins ».

**Ce qu'elle montre.** Un fichier qui survit d'un build à l'autre, la page **Workspace** du job, le workspace suffixé `@2` d'un build concurrent, puis le nettoyage automatique.

### Étapes

1. **New Item** → `workspace-demo` → **Freestyle project** → **OK**.
2. **Build Steps** → **Add build step** → **Execute shell** :

   ```bash
   echo "Workspace : $WORKSPACE"
   ls -la
   echo "build $BUILD_NUMBER" >> historique.txt
   cat historique.txt
   sleep 20
   ```

3. **Save** → **Build Now**, attendre la fin, puis **Build Now** une seconde fois.

   Résultat dans la console du build #2 : `historique.txt` contient déjà `build 1` puis `build 2`. Le workspace a été réutilisé.

4. Menu du job → **Workspace** : le fichier `historique.txt` est consultable et téléchargeable depuis l'UI.

**Builds concurrents**

5. **Configure** → **General** → cocher **Execute concurrent builds if necessary**. **Save**.
6. Cliquer **Build Now** deux fois de suite.

   Résultat : les deux builds tournent en même temps (deux lignes dans **Build Executor Status**). La console du second affiche `Building in workspace /var/jenkins_home/workspace/workspace-demo@2`.

**Nettoyage (slide 34)**

7. **Configure** → section **Environment** → cocher **Delete workspace before build starts** (plugin Workspace Cleanup, installé avec les plugins suggérés). Décocher **Execute concurrent builds if necessary**. **Save** → **Build Now**.

   Résultat : la console affiche `[WS-CLEANUP] Deleting project workspace...` et `historique.txt` ne contient plus que la ligne du build courant.

8. Dans le même bloc **Environment**, cocher aussi **Add timestamps to the Console Output** (plugin Timestamper). **Save** → **Build Now** : chaque ligne de la console est préfixée par l'heure.

> **Point clé.** Un agent éphémère (conteneur, pod) démarre toujours avec un workspace vide. Sur un agent persistant, on nettoie le workspace et on garde les caches (dépendances Maven) ailleurs, dans `~/.m2` ou un volume (slide 34). C'est le choix fait pour l'agent `linux-1` (volume `m2_cache`).

---

## Démo 5 — Configuration System et agent SSH

> Slides : 23, 43, 46 · Durée : 20 min · Prérequis : démo 4, conteneur `linux-1` démarré (démo 0)

**Pourquoi.** Jusqu'ici, les builds tournent sur le controller. La slide 23 pose la règle inverse : le controller orchestre, les agents exécutent, et le node built-in garde 0 executor. Cette démo met en place cette architecture avec un agent SSH, le mode de connexion le plus courant sous Linux (slide 46), et règle au passage les paramètres globaux de la page **System** (slide 43).

**Ce qu'elle montre.** Un credential de type clé SSH à portée **System**, la création d'un node permanent avec ses labels, le log de connexion où le controller copie `agent.jar`, un job qui s'exécute sur `linux-1` grâce à son label, et ce qui arrive à un job sans label une fois le controller passé à 0 executor.

### Étapes

**Réglages globaux (slide 43)**

1. **Manage Jenkins → System**.
2. Renseigner :

   | Champ | Valeur |
   |---|---|
   | **System Message** | `Jenkins de formation - demos library-api` |
   | **Quiet period** | `5` (valeur par défaut) |
   | **SCM checkout retry count** | `2` |
   | **Jenkins Location → Jenkins URL** | `http://localhost:8080/` |
   | **Jenkins Location → System Admin e-mail address** | `jenkins@example.com` |

3. **Save**. Le message système s'affiche désormais au-dessus de la liste des jobs du tableau de bord.

   Le nombre d'executors du controller ne se règle plus sur cette page : il est dans la configuration du **Built-In Node** (plus bas dans cette démo).

**Déclarer la clé SSH du controller (slide 45)**

4. Afficher la clé privée générée à la démo 0 et la copier en entier (lignes `-----BEGIN` et `-----END` comprises) :

   ```bash
   cat keys/jenkins_agent
   ```

5. **Manage Jenkins → Credentials** → bouton **Add Credentials** (au centre de la page tant qu'aucun credential n'existe, en haut à droite ensuite).
6. Boîte **Add Credentials**, liste **Select a type of credential** : choisir **SSH Username with private key**, puis **Next**.
7. Boîte **Add SSH Username with private key** :

   | Champ | Valeur |
   |---|---|
   | **Scope** | `System (Jenkins and nodes only)` |
   | **ID** | `agent-ssh-key` |
   | **Description** | `Cle du controller pour les agents SSH` |
   | **Username** | `jenkins` (laisser **Treat username as secret** décoché) |
   | **Private Key** | cocher **Enter directly**, cliquer **Add**, coller la clé dans la zone **Enter New Secret Below** |
   | **Passphrase** | vide (clé générée sans passphrase) |

8. **Create**. La liste affiche la ligne `agent-ssh-key` / `jenkins` / store **System**, domaine **Global**.

> **Point clé.** La portée **System** rend la clé utilisable par Jenkins lui-même (connexion aux agents) mais invisible pour les jobs : un Jenkinsfile ne peut pas la récupérer avec `credentials('agent-ssh-key')`.

**Créer le node `linux-1` (slide 46)**

9. **Manage Jenkins → Nodes → New Node**.
10. **Node name** : `linux-1`, **Type** : **Permanent Agent**, **Create**.
11. Renseigner :

    | Champ | Valeur |
    |---|---|
    | **Description** | `Agent Linux JDK 21 (conteneur linux-1)` |
    | **Number of executors** | `2` (la valeur proposée est 1) |
    | **Remote root directory** | `/home/jenkins/agent` |
    | **Labels** | `linux java21 maven` |
    | **Usage** | `Only build jobs with label expressions matching this node` |
    | **Launch method** | `Launch agents via SSH` (les champs SSH apparaissent alors) |
    | **Host** | `linux-1` |
    | **Credentials** | `jenkins (Cle du controller pour les agents SSH)` |
    | **Host Key Verification Strategy** | `Non verifying Verification Strategy` |
    | **Availability** | `Keep this agent online as much as possible` (défaut) |

12. **Save**. La liste des nodes affiche `linux-1` ; cliquer dessus, puis **Log** dans son menu.

    Résultat attendu, en fin de log :

    ```
    [SSH] Opening SSH connection to linux-1:22.
    [SSH] WARNING: SSH Host Keys are not being verified. Man-in-the-middle attacks may be possible against this connection.
    [SSH] Authentication successful.
    ...
    [SSH] Copying latest remoting.jar...
    [SSH] Starting agent process: cd "/home/jenkins/agent" && java  -jar remoting.jar -workDir /home/jenkins/agent ...
    ...
    Agent successfully connected and online
    ```

    Le controller s'est connecté en SSH, a copié `remoting.jar` (l'`agent.jar` de la slide 23) et l'a lancé avec le Java de l'agent.

> **Point clé.** `Non verifying Verification Strategy` accepte n'importe quelle clé d'hôte : acceptable sur un réseau Docker local, à proscrire en production où l'on choisit **Known hosts file** ou **Manually trusted key**.

**Envoyer un build sur l'agent**

13. Job `hello` → **Configure** → **General** → cocher **Restrict where this project can be run** (case visible seulement quand un agent existe) → **Label Expression** : `linux` (l'autocomplétion propose `linux` et `linux-1`). En quittant le champ, Jenkins affiche **Label linux matches 1 node.** **Save** → **Build Now**.

    Résultat dans la console :

    ```
    Building remotely on linux-1 (maven linux java21) in workspace /home/jenkins/agent/workspace/hello
    ...
    Node      : linux-1 (executor 1)
    ...
    linux-1
    ```

**Passer le controller à 0 executor (slide 43)**

14. **Manage Jenkins → Nodes** → cliquer **Built-In Node** → **Configure** → **Number of executors** : `0` → **Save**. Le bandeau *Building on the built-in node can be a security issue* disparaît de **Manage Jenkins**.
15. Lancer **Build Now** sur `workspace-demo` (qui n'a pas de label).

    Résultat : le build reste dans **Build Queue**. Survoler la ligne : **Waiting for next available executor on ‘Built-In Node’**. Le controller n'a plus d'executor et le seul agent n'accepte que les jobs qui demandent son label.

16. Annuler le build en attente (croix rouge dans **Build Queue**), puis dans `workspace-demo` → **Configure** → **Restrict where this project can be run** → `linux` → **Save** → **Build Now** : il part sur `linux-1`.

> **À retenir.** Controller à 0 executor + agents porteurs de labels = le build ne touche jamais `JENKINS_HOME`, et la capacité se gère en ajoutant des agents (slide 23). Tous les Jenkinsfiles du kit demandent `agent { label 'linux' }`.

---

## Démo 6 — Installer les plugins de la partie 3

> Slides : 47 à 49 · Durée : 10 min (plus le téléchargement) · Prérequis : démo 5

**Pourquoi.** Presque tout ce que Jenkins sait faire vient de plugins, y compris la lecture des rapports JUnit. La partie 3 a besoin de plugins absents des suggestions de l'assistant (slide 48). Les installer depuis l'UI montre l'Update Center, la gestion des dépendances et le redémarrage contrôlé ; la slide 47 rappelle qu'en production la même liste vit dans un `plugins.txt` versionné.

**Ce qu'elle montre.** La recherche dans **Available plugins**, l'installation groupée avec redémarrage sûr, puis la vérification dans **Installed plugins** et sur le disque.

### Étapes

1. **Manage Jenkins → Plugins** → menu de gauche **Available plugins**.
2. Dans le champ **Search available plugins**, taper le nom, puis cocher la case de la colonne **Install** sur la bonne ligne. Les plugins déjà cochés restent épinglés en haut de la liste d'une recherche à l'autre ; la colonne **Health** donne un score de santé du projet (slide 49).

   | Plugin à cocher | Sert à | Démo |
   |---|---|---|
   | **Maven Integration** | type de job « Maven project » (variante slide 54) | 8 |
   | **Coverage** | step `recordCoverage`, onglet **Coverage** | 12 |
   | **Config File Provider** | `settings.xml` géré par Jenkins | 14 |
   | **Lockable Resources** | `lock('env-recette')` | 14 |
   | **SonarQube Scanner** | `withSonarQubeEnv`, `waitForQualityGate` | 15 |
   | **Warnings** | `recordIssues` (Warnings Next Generation) | 15 |
   | **Role-based Authorization Strategy** | rôles globaux et par item | 16 |

   En cherchant `Coverage`, ne pas confondre avec **JaCoCo** (marqué *This plugin is deprecated*) ni **Code Coverage** : le plugin à prendre s'appelle simplement **Coverage**. **JUnit** n'est pas dans la liste : il est déjà installé, comme dépendance de Pipeline.

3. Cliquer le bouton bleu **Install** (en haut à droite). La flèche à côté propose **Install after restart**, inutile ici.

   Résultat : la page **Download progress** liste d'abord les plugins déjà présents (**Success**), puis les nouveaux et leurs dépendances (**Pending**, puis **Success**), et se termine par **Loading plugin extensions**.

4. En bas de la page, le message **(you can start using the installed plugins right away)** indique qu'aucun redémarrage n'est nécessaire pour ces plugins. La case **Restart Jenkins when installation is complete and no jobs are running** reste disponible pour les plugins qui l'exigent ; elle redémarre Jenkins proprement (équivalent de `<JENKINS_URL>/safeRestart`, slide 47).

5. **Manage Jenkins → Plugins → Installed plugins** : chercher `junit`. La ligne indique la version, un interrupteur d'activation et un bouton de désinstallation ; le lien du nom ouvre la page du plugin sur plugins.jenkins.io (santé, mainteneurs, dernière version : slide 49).
6. Onglet **Updates** : liste des mises à jour disponibles ; un bandeau signale celles qui corrigent une vulnérabilité.
7. Sur le disque :

   ```bash
   docker exec jenkins sh -c 'ls /var/jenkins_home/plugins/*.jpi | wc -l; ls /var/jenkins_home/plugins | grep -i junit'
   ```

   Un plugin = un fichier `.jpi` (et son répertoire décompressé) dans `JENKINS_HOME/plugins/` (slide 47).

> **Point clé.** La même installation, reproductible, s'écrit dans l'image (slide 47) :
>
> ```dockerfile
> FROM jenkins/jenkins:2.580.2-lts-jdk21
> COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
> RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
> ```
>
> avec dans `plugins.txt` une ligne par plugin (`maven-plugin`, `coverage`, `config-file-provider`, `lockable-resources`, `sonar`, `warnings-ng`, `role-strategy`), idéalement avec version figée (`coverage:3.3499.v910e11c96847`, version relevée dans **Installed plugins**).

---

## Démo 7 — Tools et credentials

> Slides : 44, 45, 56 · Durée : 15 min · Prérequis : démo 6

**Pourquoi.** Un pipeline écrit `tools { jdk 'jdk21'; maven 'maven-3.9' }` et `credentials('gitea-token')` : ces noms doivent exister dans Jenkins avant le premier build Maven. La slide 44 montre l'installation automatique de Maven sur l'agent ; la slide 45 explique pourquoi un secret ne s'écrit jamais dans un job. Le dépôt `library-api` étant privé, Jenkins ne peut pas le cloner sans credential : c'est le cas concret de la slide 56 (HTTPS + jeton d'accès, pas de mot de passe).

**Ce qu'elle montre.** La déclaration de `jdk21` (chemin existant sur l'agent) et `maven-3.9` (téléchargé au premier usage), la création d'un jeton d'accès Gitea en lecture seule, son enregistrement comme credential `gitea-token`, et le masquage d'un secret dans la console.

### Étapes

**Déclarer les outils (slide 44)**

1. **Manage Jenkins → Tools**.
2. Bloc **JDK installations** → **Add JDK** (un seul clic : chaque clic ajoute un bloc) :
   - **Name** : `jdk21`
   - **JAVA_HOME** : `/opt/java/openjdk` (chemin du JDK 21 dans l'image de l'agent)
   - laisser **Install automatically** décoché (c'est la valeur proposée pour un JDK)
3. Bloc **Maven installations** (en bas de la page) → **Add Maven** :
   - **Name** : `maven-3.9`
   - laisser **Install automatically** coché, installateur **Install from Apache**
   - **Version** : choisir **3.9.16** (la plus récente des 3.9.x). Attention, la liste propose par défaut la version la plus récente, **3.10.0**, qui ne correspond pas au nom `maven-3.9`.
4. Bloc **Git installations** : laisser **Name** `Default` / **Path to Git executable** `git`.
5. **Save**.

   Le bloc **Maven Configuration**, en haut de la page, sert à imposer un `settings.xml` à tous les jobs ; on le laisse sur **Use default maven settings** (le `settings.xml` géré arrive à la démo 14).

**Créer un jeton d'accès dans Gitea (slide 56)**

6. Sur http://localhost:3000 (connecté en `formation`) : avatar en haut à droite → **Settings** → menu de gauche **Applications**.

   **Se connecter à Gitea.** Si la page d'accueil n'affiche que le logo et « Git with a cup of tea », on n'est pas connecté :
   1. cliquer **Sign In** en haut à droite (**Connexion** dans un navigateur en français), ou ouvrir directement http://localhost:3000/user/login ;
   2. **Username or Email Address** (*Nom d'utilisateur ou adresse courriel*) : `formation` ;
   3. **Password** (*Mot de passe*) : `Formation-2026` ;
   4. cliquer **Sign In** (*Connexion*). Le tableau de bord de `formation` s'affiche, avec l'avatar en haut à droite ; l'interface passe en anglais (langue enregistrée pour ce compte).

   Ce compte a été créé par `scripts/init-gitea.sh` (ou `scripts/init-gitea.ps1` sous Windows) à la démo 0. La page des jetons s'ouvre aussi directement, une fois connecté : http://localhost:3000/user/settings/applications.
7. Bloc **Manage Access Tokens** → **Generate New Token** (déjà déplié si aucun jeton n'existe) :
   - **Token Name** : `jenkins`
   - **Repository and Organization Access** : **All (public, private, and limited)**
   - dans la liste des permissions, ligne **repository** : choisir **Read** (les autres lignes restent sur **No Access**)
   - cliquer **Generate Token**
8. Le bandeau vert **Your new token has been generated. Copy it now as it will not be shown again.** surmonte un cadre bleu qui contient le jeton : le copier.

**Enregistrer le credential dans Jenkins (slide 45)**

9. **Manage Jenkins → Credentials** → **Add Credentials** → type **Username with password** → **Next**.
10. Boîte **Add Username with password** :

    | Champ | Valeur |
    |---|---|
    | **Scope** | `Global (Jenkins, nodes, items, all child items, etc)` |
    | **Username** | `formation` |
    | **Treat username as secret** | décoché |
    | **Password** | le jeton Gitea |
    | **ID** | `gitea-token` |
    | **Description** | `Gitea - jeton lecture library-api` |

11. **Create**. La liste affiche désormais deux credentials : `agent-ssh-key` (`jenkins`) et `gitea-token` (`formation/******`).

**Vérifier les outils et le masquage des secrets**

12. **New Item** → `outils` → **Freestyle project** → **OK**.
13. **General** → **Restrict where this project can be run** → `linux`.
14. **Environment** → cocher **Use secret text(s) or file(s)** → sous **Bindings**, bouton **Add** → **Username and password (separated)** :
    - **Username Variable** : `GIT_USER`
    - **Password Variable** : `GIT_TOKEN`
    - **Credentials** : `formation/****** (Gitea - jeton lecture library-api)`
15. **Build Steps** → **Add build step** → **Invoke top-level Maven targets** : **Maven Version** `maven-3.9`, **Goals** `-v`.
16. **Add build step** → **Execute shell** :

    ```bash
    java -version
    echo "Utilisateur Git : $GIT_USER"
    echo "Jeton Git       : $GIT_TOKEN"
    git ls-remote "http://$GIT_USER:$GIT_TOKEN@gitea:3000/formation/library-api.git"
    ```

17. **Save** → **Build Now** → **Console Output**.

    Résultat attendu :
    - `Unpacking https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.9.../apache-maven-3.9...-bin.zip to /home/jenkins/agent/tools/hudson.tasks.Maven_MavenInstallation/maven-3.9 on linux-1` : Maven est installé sur l'agent au premier usage ;
    - `Apache Maven 3.9.16` puis `Java version: 21.0.x, vendor: Eclipse Adoptium, runtime: /opt/java/openjdk` ;
    - `Utilisateur Git : formation` en clair (le nom d'utilisateur n'est pas traité comme secret), puis `Jeton Git       : ****` : la valeur du secret est masquée dans le log, y compris dans l'URL de `git ls-remote` (`http://formation:****@gitea:3000/...`) ;
    - `git ls-remote` liste `refs/heads/main` : le jeton donne bien accès au dépôt privé.

18. Relancer **Build Now** : la ligne `Unpacking` a disparu, Maven est déjà dans `/home/jenkins/agent/tools/`.

> **À retenir.** Le masquage ne protège que la valeur exacte : un `echo $GIT_TOKEN | base64` l'afficherait. C'est pour cela que la permission de configurer un job équivaut à pouvoir lire ses credentials (slide 77).

---

## Démo 8 — Job Freestyle library-api

> Slides : 25, 54, 56, 58 · Durée : 20 min · Prérequis : démo 7

**Pourquoi.** La slide 54 construit le fil rouge avec un job Freestyle : chaque brique (source, déclencheur, environnement, step Maven, actions post-build) y est une section visible de l'UI. C'est la meilleure façon de voir physiquement ce qu'un Jenkinsfile exprimera ensuite en quelques lignes. Le job est rangé dans un **Folder** `library` (slide 25), qui servira aussi pour les habilitations.

**Ce qu'elle montre.** Un clone Git authentifié, l'installation de Maven au premier build, la version injectée par Jenkins (`-Drevision`), la publication des rapports Surefire et l'archivage du JAR, puis un build déclenché par **Poll SCM** après une modification faite dans Gitea.

### Étapes

**Créer le dossier `library`**

1. **Dashboard → New Item** → `library` → **Folder** → **OK**. **Display Name** : `library`, **Description** : `Jobs du fil rouge library-api`. **Save**.

**Créer le job**

2. Dans le dossier `library` : **New Item** → `library-api-freestyle` → **Freestyle project** → **OK**.
3. Section **General** :
   - **Description** : `Build Maven de library-api (Freestyle, slide 54)`
   - cocher **Discard old builds** → **Max # of builds to keep** : `20`
   - cocher **Restrict where this project can be run** → **Label Expression** : `linux`

   Il n'y a pas de liste **JDK** dans le job : avec un seul JDK déclaré dans **Tools**, Jenkins ne propose pas de choix et Maven utilise le `JAVA_HOME` de l'agent (le JDK 21 de l'image).
4. Section **Source Code Management** → **Git** :
   - **Repository URL** : `http://gitea:3000/formation/library-api.git`
   - **Credentials** : `formation/****** (Gitea - jeton lecture library-api)`
   - **Branch Specifier** : `*/main`

   Si le champ URL affiche une erreur rouge (`Failed to connect to repository`) avant le choix du credential, c'est attendu : le dépôt est privé. Elle disparaît une fois le credential choisi.

5. Section **Triggers** → cocher **Poll SCM** → **Schedule** : `H/2 * * * *` (en formation ; en production : webhook, démo 10).
6. Section **Environment** : cocher **Delete workspace before build starts** et **Add timestamps to the Console Output**.
7. Section **Build Steps** → **Add build step** → **Invoke top-level Maven targets** :
   - **Maven Version** : `maven-3.9`
   - **Goals** : `-B -ntp clean verify`
   - cliquer **Advanced** sous le step → **Properties** : `revision=1.4.${BUILD_NUMBER}` (slide 58). Le bouton affiche ensuite le badge **Edited**.
8. Section **Post-build Actions** :
   - **Add post-build action** → **Publish JUnit test result report** → **Test report XMLs** : `target/surefire-reports/*.xml`
   - **Add post-build action** → **Archive the artifacts** → **Files to archive** : `target/*.jar` ; **Advanced** → vérifier que **Fingerprint all archived artifacts** est coché
9. **Save** → **Build Now** → **Console Output**.

   Résultat attendu (le premier build est long : téléchargement des dépendances Maven) :

   ```
   Building remotely on linux-1 (maven linux java21) in workspace /home/jenkins/agent/workspace/library/library-api-freestyle
   [WS-CLEANUP] Deleting project workspace...
   The recommended git tool is: NONE
   using credential gitea-token
   Cloning the remote Git repository
   Cloning repository http://gitea:3000/formation/library-api.git
   ...
   using GIT_ASKPASS to set credentials Gitea - jeton lecture library-api
   ...
   [library-api-freestyle] $ /home/jenkins/agent/tools/hudson.tasks.Maven_MavenInstallation/maven-3.9/bin/mvn -Drevision=1.4.1 -B -ntp clean verify
   [INFO] Building library-api 1.4.1
   ...
   [INFO] Tests run: 9, Failures: 0, Errors: 0, Skipped: 0
   [INFO] Building jar: /home/jenkins/agent/workspace/library/library-api-freestyle/target/library-api-1.4.1.jar
   ...
   [INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0      <- tests d'intégration (Failsafe)
   [INFO] BUILD SUCCESS
   Recording test results
   Archiving artifacts
   Recording fingerprints
   Finished: SUCCESS
   ```

   Chaque ligne est préfixée par l'heure (Timestamper). Les tests d'intégration `*IT` tournent aussi (`verify`), mais ne sont pas publiés : le motif ne vise que `surefire-reports`.

10. Page du build **#1** :
    - en-tête : **Took 18 sec on linux-1**, révision Git et dépôt ;
    - cadre **Build Artifacts** : `library-api-1.4.1.jar` (environ 22 Mo, JAR exécutable Spring Boot), téléchargeable ;
    - menu **Tests** : 9 tests, aucun échec ; naviguer par package `fr.utopios.library` → classe `BookServiceTest` → méthodes et durées ;
    - menu **See Fingerprints** : l'empreinte MD5 du JAR (slide 33) ;
    - menu **Git Build Data** : révision et branche construites.
11. Relancer **Build Now** : le build est beaucoup plus rapide (cache `~/.m2` sur le volume de l'agent) et produit `library-api-1.4.2.jar`. La page du job affiche maintenant le graphique **Test Result Trend**.

**Déclenchement par un changement (Poll SCM)**

12. Dans Gitea, dépôt `formation/library-api` → bouton **Add File** → **New File**. Nom du fichier : `README.md`, contenu : `# library-api`. Cliquer **Commit Changes** ; dans la fenêtre qui s'ouvre, laisser **Commit directly to the main branch.** et confirmer par **Commit Changes**.
13. Dans les deux minutes, un build démarre seul. Sa page indique **Started by an SCM change** ; **Changes** liste le commit `Add README.md` avec son auteur ; le menu du job propose **Git Polling Log** (dernier contrôle du dépôt).

> **Point clé.** Le numéro de build devient la version de l'artefact (`library-api-1.4.<n>.jar`) : à partir d'un JAR, on retrouve le build, donc le commit (slide 58). La variante **Maven project** (plugin Maven Integration, slide 54) fait la même chose avec moins de champs, mais elle est considérée comme legacy.

---

## Démo 9 — Job Pipeline et Jenkinsfile

> Slides : 26 à 28, 33, 38, 55 · Durée : 25 min · Prérequis : démo 8

**Pourquoi.** Le Freestyle de la démo 8 tient dans un `config.xml` que personne ne relit. La slide 26 explique pourquoi le standard est le Pipeline : la même chaîne écrite en code, versionnée avec le projet, découpée en stages visibles, reprise après un redémarrage. On commence par un script saisi dans l'UI pour itérer vite, puis on bascule vers le Jenkinsfile du dépôt (slide 55).

**Ce qu'elle montre.** L'éditeur de pipeline, le **Snippet Generator**, la vue graphique des stages, **Replay**, la bascule vers **Pipeline script from SCM**, le comportement de `when { branch 'main' }` dans un job non multibranch, et la validation d'un Jenkinsfile par l'API (slide 38).

### Étapes

**Pipeline saisi dans l'UI**

1. Dossier `library` → **New Item** → `library-api-pipeline` → **Pipeline** → **OK**.
2. Menu de gauche de la configuration → **Pipeline** → **Definition** : **Pipeline script**. Cliquer dans l'éditeur **Script** et coller :

   ```groovy
   pipeline {
     agent { label 'linux' }
     tools { jdk 'jdk21'; maven 'maven-3.9' }
     options { timestamps() }
     stages {
       stage('Checkout') {
         steps {
           git url: 'http://gitea:3000/formation/library-api.git',
               branch: 'main', credentialsId: 'gitea-token'
         }
       }
       stage('Build & Test') {
         steps { sh 'mvn -B -ntp clean verify' }
       }
     }
     post {
       always  { junit 'target/surefire-reports/*.xml' }
       success { archiveArtifacts artifacts: 'target/*.jar', fingerprint: true }
     }
   }
   ```

3. **Save** → **Build Now**.

   Résultat : le menu du job contient maintenant **Stages** (tableau stages × builds, slide 36) et **Pipeline Syntax**. La page du build propose **Pipeline Overview** : un graphe des stages **Declarative: Tool Install**, **Checkout**, **Build & Test**, **Declarative: Post Actions** ; cliquer un stage affiche les logs de ses steps. Les stages préfixés *Declarative:* sont ajoutés par Jenkins (installation des outils de `tools { }`, exécution du bloc `post`).

**Générer un step avec le Snippet Generator (slide 28)**

4. Menu du job → **Pipeline Syntax**.
5. Page **Snippet Generator** → **Sample Step** : `archiveArtifacts: Archive the artifacts`. **Files to archive** : `target/*.jar`. Cliquer **Advanced** → cocher **Fingerprint all archived artifacts**. Cliquer **Generate Pipeline Script**.

   Résultat : `archiveArtifacts artifacts: 'target/*.jar', fingerprint: true`, à copier dans un Jenkinsfile.

6. Menu de gauche de cette page : **Declarative Directive Generator** → **Sample Directive** `options: Options` → bouton **Add** → **timeout: Enforce time limit** (saisir `20`, unité `MINUTES`) → **Generate Declarative Directive**. Puis **Global Variables Reference** : liste de `env`, `params`, `currentBuild`... Les autres entrées (**Steps Reference**, **IntelliJ IDEA GDSL**) documentent tous les steps des plugins installés.

**Rejouer un build modifié (slide 33)**

7. Page du dernier build → **Replay**. Dans l'éditeur, ajouter après le stage `Build & Test` :

   ```groovy
       stage('Infos') {
         steps {
           echo "Build ${env.BUILD_NUMBER} sur ${env.NODE_NAME}, commit ${env.GIT_COMMIT}"
         }
       }
   ```

   (Le script s'édite dans la zone **Main Script** de la page **Replay #n**.) Cliquer **Run**. Le nouveau build contient le stage `Infos` et sa console commence par `Replayed #n` ; la configuration du job, elle, n'a pas changé. **Replay** sert à mettre au point un pipeline sans commit.

**Lire le Jenkinsfile depuis le dépôt (slide 55)**

8. **Configure** → **Pipeline** → **Definition** : **Pipeline script from SCM**.
   - **SCM** : `Git`
   - **Repository URL** : `http://gitea:3000/formation/library-api.git`
   - **Credentials** : `formation/******`
   - **Branch Specifier** : `*/main`
   - **Script Path** : `Jenkinsfile`
   - **Lightweight checkout** : coché
9. **Save** → **Build Now**.

   Résultat : la console commence par `Obtained Jenkinsfile from git http://gitea:3000/formation/library-api.git` et un stage **Declarative: Checkout SCM** apparaît (checkout implicite). Le stage **Package** est grisé, avec dans le log `Stage "Package" skipped due to when conditional` : dans un job Pipeline simple, `BRANCH_NAME` n'existe pas, donc `when { branch 'main' }` est faux. La ligne `Branche : origin/main - commit ...` vient de `GIT_BRANCH`. Ce stage s'exécutera en Multibranch (démo 10).

**Valider un Jenkinsfile sans lancer de build (slide 38)**

10. Dans un terminal, à la racine du kit (jeton d'API créé à la démo 3) :

    ```bash
    curl -s -u admin:$JENKINS_TOKEN -X POST -F "jenkinsfile=<library-api/Jenkinsfile" http://localhost:8080/pipeline-model-converter/validate
    ```

    Résultat : `Jenkinsfile successfully validated.`

11. Introduire une erreur dans une copie et valider :

    ```bash
    sed 's/stages {/stagez {/' library-api/Jenkinsfile > /tmp/Jenkinsfile.ko
    curl -s -u admin:$JENKINS_TOKEN -X POST -F "jenkinsfile=</tmp/Jenkinsfile.ko" http://localhost:8080/pipeline-model-converter/validate
    ```

    Résultat : `Errors encountered validating Jenkinsfile:` suivi de la ligne et de la cause. C'est ce qu'utilisent les extensions d'IDE (Jenkins Pipeline Linter Connector).

> **À retenir.** Même configuration qu'en démo 8, mais tout ce qui compte est dans le dépôt : relu en revue de code, historisé, identique sur toutes les branches. Le job ne contient plus que l'adresse du Jenkinsfile.

---

## Démo 10 — Multibranch Pipeline et webhook

> Slides : 29, 31, 55 à 57 · Durée : 25 min · Prérequis : démo 9

**Pourquoi.** Un dépôt vit avec plusieurs branches. Créer un job par branche à la main ne tient pas ; le **Multibranch Pipeline** (slide 55) scanne le dépôt et crée un sous-job pour chaque branche qui contient un Jenkinsfile. Pour que le feedback soit immédiat sans interroger Git toutes les minutes, le dépôt prévient Jenkins par webhook (slides 29 et 31). Avec Gitea, le webhook appelle l'URL `notifyCommit` du plugin Git, l'équivalent de la case **GitHub hook trigger for GITScm polling**.

**Ce qu'elle montre.** La découverte des branches, l'exécution du stage **Package** sur `main` uniquement, un build qui part dans la seconde après un commit, puis la création et la suppression d'une branche de fonctionnalité.

### Étapes

**Créer le Multibranch Pipeline**

1. Dossier `library` → **New Item** → `library-api` → **Multibranch Pipeline** → **OK**.
2. Section **Branch Sources** → **Add source** → **Git** :
   - **Project Repository** : `http://gitea:3000/formation/library-api.git`
   - **Credentials** : `formation/****** (Gitea - jeton lecture library-api)`
   - **Behaviours** : laisser **Discover branches**
   - **Property strategy** : laisser **All branches get the same properties**
3. **Build Configuration** → **Mode** : `by Jenkinsfile`, **Script Path** : `Jenkinsfile`.
4. **Scan Multibranch Pipeline Triggers** → cocher **Periodically if not otherwise run** → **Interval** : `1 hour` (filet de sécurité si un webhook se perd).
5. **Orphaned Item Strategy** : laisser **Discard old items** coché, **Days to keep old items** : `7`, **Max # of old items to keep** vide.
6. **Save**.

   Résultat : Jenkins affiche **Scan Multibranch Pipeline Log** :

   ```
   Starting branch indexing...
   ...
   Checking branches...
     Checking branch main
         ‘Jenkinsfile’ found
       Met criteria
   Scheduled build for branch: main
   Processed 1 branches
   Finished branch indexing. Indexing took 0.1 sec
   Finished: SUCCESS
   ```

7. Revenir sur `library » library-api` : le sous-job **main** est apparu et se construit. Ouvrir son build : la console commence par **Branch indexing**, affiche `Branche : main - commit ...`, et le stage **Package** est exécuté cette fois (`Archiving artifacts`) ; **Build Artifacts** contient le JAR.

**Autoriser le webhook (jeton notifyCommit)**

8. **Manage Jenkins → Security** → bloc **Git plugin notifyCommit access tokens** → **Add new access token** → champ **Access token name** : `gitea` → **Generate**. Le jeton s'affiche avec le message **Access token will only be displayed once.** : le copier, puis cliquer **Save** en bas de la page.

**Déclarer le webhook dans Gitea (slide 31, côté dépôt)**

9. Gitea → dépôt `formation/library-api` → onglet **Settings** du dépôt → menu de gauche **Webhooks** → **Add Webhook** → **Gitea**.
10. Renseigner :
    - **Target URL** : `http://jenkins:8080/git/notifyCommit?url=http://gitea:3000/formation/library-api.git&token=<jeton>`, en remplaçant `<jeton>` (chevrons compris) par le jeton copié à l'étape 8. Exemple : `...library-api.git&token=11e3f0c2a9...`. Si le jeton a été perdu, il ne peut plus être affiché : le supprimer dans **Manage Jenkins → Security** et en générer un nouveau (étape 8).

      *Lecture de l'URL :* `jenkins:8080` est le nom du conteneur Jenkins sur le réseau Docker, celui que Gitea utilise pour le joindre, et non `localhost`. `url=` indique quel dépôt a changé : Jenkins relance tous les jobs dont le SCM pointe vers cette adresse. `token=` est le laissez-passer qui autorise cet appel sans compte Jenkins.
    - **HTTP Method** : `POST`, **POST Content Type** : `application/json` (valeurs proposées)
    - **Trigger On** : **Custom Events…**, puis cocher **Create**, **Delete** et **Push**
    - **Branch filter** : `*`
    - **Active** : coché

    **Push Events** seul ne suffit pas : la suppression d'une branche est un événement **Delete**, que Jenkins doit recevoir pour marquer le sous-job comme orphelin.

11. **Add Webhook** → bandeau **The webhook has been added.** Cliquer l'URL du webhook pour l'ouvrir, puis **Test Delivery** (bloc **Recent Deliveries**, en bas) : une livraison apparaît, marquée en vert (HTTP 200). Dépliée, sa réponse contient `Scheduled indexing of library » library-api`, et aussi `Scheduled polling of library » library-api-freestyle` : `notifyCommit` déclenche tous les jobs dont le SCM pointe vers cette URL, y compris le Freestyle de la démo 8 qui a **Poll SCM** coché.

    Si la livraison est rouge, sa réponse indique la cause : **HTTP 401** `An access token is required` = le paramètre `&token=` manque dans l'URL ; **HTTP 403** `Invalid access token` = le jeton est faux (chevrons `< >` laissés, jeton mal copié ou supprimé). Corriger la **Target URL** (bouton **Update Webhook**), puis relancer **Test Delivery**.

**Créer une branche de fonctionnalité**

12. Gitea → dépôt → bouton de branche (**main** ▾) → dans **Filter branch**, saisir `feature/isbn` → cliquer **Create branch feature/isbn from 'main'**.

    Résultat dans Jenkins, en quelques secondes : `library » library-api` contient un deuxième sous-job **feature/isbn** (affiché `feature%2Fisbn` dans l'URL) qui se construit. Son stage **Package** est grisé : seule `main` produit l'artefact.

13. Toujours sur la branche `feature/isbn` dans Gitea, ouvrir `src/main/java/fr/utopios/library/Book.java` → icône crayon (**Edit File**) → ajouter une ligne `// TODO : ajouter l'ISBN` → **Commit Changes**, puis confirmer **Commit Changes** dans la fenêtre (commit direct sur `feature/isbn`).

    Résultat : seul **feature/isbn** se reconstruit (build #2, cause **Branch indexing** : le webhook a déclenché un scan, qui a détecté `Changes detected: feature/isbn`). **Changes** liste le commit ; `main` n'a pas bougé.

14. Supprimer la branche : Gitea → dépôt → lien **2 Branches** (au-dessus de la liste des fichiers) → icône corbeille de `feature/isbn` → confirmer.

    Résultat : le webhook (événement **Delete**) relance un scan. Le sous-job `feature/isbn` reste visible mais désactivé (grisé, plus de **Build Now**) ; le **Scan Multibranch Pipeline Log** indique `Evaluating orphaned items in library » library-api` et `Will not remove feature/isbn because it is new` : **Orphaned Item Strategy** le supprimera après 7 jours.

> **Point clé.** Avec une source **Git** générique, Jenkins découvre les branches mais pas les Pull Requests. Les sources **GitHub**, **GitLab** ou **Gitea** (plugins Branch Source) ajoutent **Discover pull requests from origin**, les variables `CHANGE_ID` / `CHANGE_TARGET` et la remontée du statut sur la PR (slides 31 et 57).

---

## Démo 11 — Paramétrage Maven et build paramétré

> Slides : 58 à 60 · Durée : 15 min · Prérequis : démo 10

**Pourquoi.** Le même pipeline doit pouvoir construire une version précise, viser un environnement, sauter une étape longue. Les slides 58 et 60 montrent les deux leviers : variables passées à Maven (`MAVEN_ARGS`, `-Drevision`) et paramètres saisis au lancement. Le piège de la slide 60 (paramètres absents de l'UI avant le premier build) se constate mieux qu'il ne s'explique.

**Ce qu'elle montre.** Un job dont le bouton devient **Build with Parameters** après un premier build, un stage sauté par un booléen, la version de l'artefact calculée à partir d'un paramètre et du numéro de build, et le lancement paramétré par l'API.

### Étapes

1. Dossier `library` → **New Item** → **Enter an item name** : `library-api-parametres`. Au lieu de choisir un type, cliquer la dernière entrée de la liste, **Duplicate an existing item**, puis saisir dans le champ **Type to autocomplete** : `library-api-pipeline` (l'autocomplétion le propose) → **OK**.
2. La configuration copiée s'ouvre. Menu de gauche **Pipeline** → **Script Path** : `ci/Jenkinsfile.parametres` (dépôt, credential et branche sont recopiés de la démo 9). **Save**.

> **Méthode utilisée dans les démos suivantes.** « Dupliquer `library-api-pipeline` et changer le Script Path » désigne toujours ces deux étapes. Le **Save** est indispensable : tant qu'une copie n'a pas été enregistrée, Jenkins refuse de la construire.
3. Le menu du job affiche **Build Now**, pas encore **Build with Parameters** : Jenkins ne connaît pas les paramètres tant qu'il n'a pas lu le Jenkinsfile. Cliquer **Build Now**.

   Résultat : le build #1 tourne avec les valeurs par défaut (`dev`, `1.4`, tests d'intégration activés) ; son nom affiché est `#1 v1.4.1 dev`.

4. Le menu affiche désormais **Build with Parameters**. Cliquer, puis :
   - **TARGET_ENV** : `recette`
   - **VERSION_MINEURE** : `2.0`
   - décocher **RUN_IT**
   - **Build**

   Résultat : build `#2 v2.0.2 recette`. La console montre `+ mvn -B -ntp -Drevision=2.0.2 -DskipITs clean verify`, puis `Stage "Tests d'integration" skipped due to when conditional` ; le stage **Deploy** affiche `Deploiement de library-api 2.0.2 sur recette` et le fichier `target/library-api-2.0.2.jar`.

5. Page du build #2 → menu **Parameters** : les valeurs saisies sont conservées avec le build (traçabilité). Le menu **Delete build ‘#2 v2.0.2 recette’** reprend le nom affiché.
6. Lancer par l'API (slide 60) :

   ```bash
   curl -X POST -u admin:$JENKINS_TOKEN "http://localhost:8080/job/library/job/library-api-parametres/buildWithParameters?TARGET_ENV=prod&VERSION_MINEURE=1.5&RUN_IT=true"
   ```

   Résultat : build `#3 v1.5.3 prod`, **Started by user Administrateur Jenkins** (authentifié par le jeton d'API).

7. Ouvrir la console du build #3 et repérer la commande Maven : `mvn -B -ntp -Drevision=1.5.3 -DskipITs clean verify` puis, dans le stage suivant, `failsafe:integration-test failsafe:verify`.

> **Point clé.** Les paramètres déclarés dans le Jenkinsfile remplacent à chaque build ceux de la configuration du job : modifier un paramètre dans l'UI d'un job piloté par Jenkinsfile est perdu au build suivant.

---

## Démo 12 — Rapports de tests et couverture

> Slides : 32, 61 à 63 · Durée : 20 min · Prérequis : démo 11

**Pourquoi.** Un pipeline qui exécute `mvn test` sans publier les rapports ne dit que « ça casse » ; avec `junit` et `recordCoverage`, il dit quel test, depuis quand, et quelle part du code est exercée. La slide 62 insiste sur la différence entre FAILURE (« ça ne compile pas ») et UNSTABLE (« ça ne passe pas ») : elle se provoque en deux commits.

**Ce qu'elle montre.** L'onglet **Test Result** et sa tendance, un test cassé qui rend le build UNSTABLE avec sa stack trace, une erreur de compilation qui le rend FAILURE, l'onglet **Coverage** et un seuil de couverture qui dégrade le build.

### Étapes

**Le job de tests**

1. Dossier `library` → **New Item** → `library-api-tests` → **Duplicate an existing item** → `library-api-pipeline` → **OK**.
2. **Script Path** : `ci/Jenkinsfile.tests` → **Save** → **Build Now**.

   Résultat : build vert. La console contient le bilan JaCoCo lu par le plugin Coverage :

   ```
   [Coverage] Line Coverage: 83.78% (31/37)
   [Coverage] Branch Coverage: 100.00% (2/2)
   ...
   [Coverage] -> All quality gates have been passed
   [Coverage]    - [Whole project - Line Coverage]: ≪Success≫ - (Actual value: 83.78%, Quality gate: 80.00)
   ```

   Page du build :
   - menu **Tests** : 11 tests (9 unitaires + 2 d'intégration), 0 échec ;
   - menu **Coverage** : pourcentages par métrique (ligne, branche, méthode, instruction), arborescence par package et fichier, code source coloré ligne par ligne.
   La page du job gagne elle aussi une entrée **Coverage** (tendance).

**Un test qui échoue : UNSTABLE**

3. Gitea → `src/test/java/fr/utopios/library/BookServiceTest.java` sur `main` → **Edit File**. Dans `shouldDecrementCopiesOnLoan`, remplacer `b.copies() == 2` par `b.copies() == 1`. **Commit Changes** avec le message `test volontairement faux`.
4. Jenkins → `library-api-tests` → **Build Now**.

   Résultat :
   - boule jaune, **UNSTABLE** ; la console contient `[ERROR] Tests run: 4, Failures: 1` puis `BUILD SUCCESS` côté Maven (grâce à `-Dmaven.test.failure.ignore=true`) ;
   - page du build → menu **Tests** : **1 failure** → cliquer `shouldDecrementCopiesOnLoan` : message `Wanted but not invoked: repository.save(<custom argument matcher>)`, suivi des interactions réellement observées (`repository.save(Book[id=1, title=DDD, copies=2])`) et de la stack trace ; **Age** = 1 ;
   - le multibranch `library » library-api » main` (démo 10) s'est reconstruit tout seul grâce au webhook, mais il est **rouge** (FAILURE) : son Jenkinsfile lance `mvn verify` sans `-Dmaven.test.failure.ignore` (slide 32).

**Une erreur de compilation : FAILURE**

5. Gitea → `src/main/java/fr/utopios/library/Book.java` → **Edit File** → supprimer le `;` à la fin de la ligne `return new Book(id, title, newCopies);` → **Commit Changes**.
6. `library-api-tests` → **Build Now**.

   Résultat : boule rouge, **FAILURE**. La console contient `[ERROR] COMPILATION ERROR :` puis `Book.java:[7,46] ';' expected`. Aucun test n'a tourné : le step `junit` du bloc `post` signale `No test report files were found. Configuration error?`.

7. Corriger les deux fichiers dans Gitea (remettre le `;` et `== 2`), **Build Now** : le build repasse au vert. Sur la page du job, **Test Result Trend** montre le creux.

**Seuil de couverture (slide 63)**

8. Page du dernier build → **Replay**. Dans `qualityGates`, remplacer `threshold: 80.0` par `threshold: 90.0` → **Run**.

   Résultat : **UNSTABLE** sans aucun test rouge. La console indique :

   ```
   [Coverage] -> Some quality gates have been missed: overall result is UNSTABLE
   [Coverage]    - [Whole project - Line Coverage]: ≪Unstable≫ - (Actual value: 83.78%, Quality gate: 90.00)
   ```

> **À retenir.** Le seuil de couverture est porté par Jenkins (UNSTABLE) et non par `jacoco:check` dans le POM (FAILURE) : une seule porte, sinon deux outils se contredisent (slide 63).

---

## Démo 13 — Notifications par mail

> Slides : 64 à 66 · Durée : 15 min · Prérequis : démo 12

**Pourquoi.** Un build cassé que personne ne voit ne sert à rien. La slide 66 recommande de notifier les changements d'état (cassé, instable, réparé) plutôt que chaque build. Mailpit joue le rôle de MailHog (slide 64) : il accepte tous les mails sur le port 1025 et les affiche dans une interface web, sans rien envoyer à l'extérieur.

**Ce qu'elle montre.** La configuration SMTP des deux plugins (Mailer et Email Extension), le mail de test, puis les mails `unstable` et `fixed` émis par `emailext` depuis le `post` du pipeline.

### Étapes

**Configurer le SMTP (slide 64)**

1. **Manage Jenkins → System**.
2. Bloc **Jenkins Location** : **System Admin e-mail address** = `jenkins@example.com` (déjà fait en démo 5 ; c'est l'expéditeur).
3. Bloc **Extended E-mail Notification** :
   - **SMTP server** : `mailpit`
   - **SMTP Port** : `1025`
   - **Default Content Type** : `HTML (text/html)`
   - **Default Recipients** : `dev-team@example.com`
4. Bloc **E-mail Notification** (plugin Mailer, tout en bas) :
   - **SMTP server** : `mailpit`
   - cliquer **Advanced** → **SMTP Port** : `1025`
   - cocher **Test configuration by sending test e-mail** → **Test e-mail recipient** : `admin@example.com` → **Test configuration**

   Résultat : **Email was successfully sent**.

5. **Save**. Ouvrir **http://localhost:8025** : le mail **Test email #1** est arrivé.

**Mails depuis le pipeline (slide 65)**

6. Dossier `library` → **New Item** → `library-api-mail` → **Duplicate an existing item** → `library-api-pipeline` → **OK** → **Script Path** : `ci/Jenkinsfile.mail` → **Save** → **Build Now**.

   Résultat : build vert, aucun mail (le pipeline ne notifie que les changements d'état).

7. Gitea → casser à nouveau le test (`b.copies() == 1` dans `BookServiceTest`, démo 12) → **Commit Changes** → `library-api-mail` → **Build Now**.

   Résultat : UNSTABLE et, dans Mailpit, **[Jenkins] INSTABLE library/library-api-mail #2**, expédié par `jenkins@example.com` à `dev-team@example.com`. Le corps indique `Tests en echec : 1 sur 9`, puis le nom du test et le message d'erreur. La console contient :

   ```
   Not sending mail to unregistered user (id: formation, email: formation@example.com) because your SCM claimed this was associated with a user ID 'formation' which your security realm does not recognize ...
   Sending email to: dev-team@example.com
   ```

8. Gitea → remettre `== 2` → **Commit Changes** → **Build Now**.

   Résultat : SUCCESS et un mail **[Jenkins] REPARE library/library-api-mail #3** : la condition `fixed` ne se déclenche que lors du retour au vert.

9. Variante Freestyle (slide 65, dernière ligne) : `library-api-freestyle` → **Configure** → **Post-build Actions** → **Add post-build action** → **Editable Email Notification** → **Advanced Settings** → **Triggers** : liste des déclencheurs (**Failure - Any**, **Unstable (Test Failures)**, **Fixed**...). Ne pas enregistrer.

> **Point clé.** `culprits()` et `developers()` ajoutent les auteurs des commits seulement si Jenkins les reconnaît comme utilisateurs : ici l'auteur Git `formation@example.com` n'a pas de compte Jenkins, d'où le message *Not sending mail to unregistered user*. Deux solutions : relier les comptes (annuaire LDAP, ou utilisateurs Jenkins portant la même adresse, slide 64), ou cocher **Allow sending to unregistered users** dans **Extended E-mail Notification** (bouton **Advanced** du bloc).

---

## Démo 14 — Déploiement automatique

> Slides : 67 à 70 · Durée : 30 min · Prérequis : démo 13

**Pourquoi.** La slide 67 pose le principe : on publie d'abord l'artefact dans un dépôt immuable, on déploie ensuite une version, puis on vérifie qu'elle répond. La production attend une approbation humaine (slide 70). Kubernetes n'étant pas dans la stack, la recette et la production sont deux conteneurs lancés sur le Docker du poste ; la mécanique Jenkins (credentials, `settings.xml` géré, verrou, `input`) est la même.

**Ce qu'elle montre.** Nexus et son utilisateur technique, un credential injecté dans Maven par un `settings.xml` géré (Config File Provider), le JAR `1.4.<n>` publié dans `maven-releases`, une image Docker construite et lancée en recette, un smoke test sur `/actuator/health`, puis un build en pause jusqu'au clic **Deployer**.

### Étapes

**Démarrer et préparer Nexus (slide 68, côté Nexus)**

1. Démarrer Nexus (version de référence : **Nexus Repository Community Edition 3.97**) et attendre qu'il réponde (une trentaine de secondes à quelques minutes) :

   ```bash
   docker compose up -d nexus
   ```

   ```bash
   until curl -sf http://localhost:8081/service/rest/v1/status; do sleep 5; done; echo Nexus pret
   ```

2. Lire le mot de passe initial :

   ```bash
   docker exec nexus cat /nexus-data/admin.password
   ```

3. http://localhost:8081 affiche directement la page de connexion : **Username** `admin`, **Password** = ce mot de passe → **Log in**. La boîte **Let's Get You Set Up** s'ouvre → **Get Started** :
   - **Set an admin password** : **New password** et **Confirm password** `Formation-2026` → **Next**. Nexus déconnecte alors la session (*User signed out*) : se reconnecter avec le nouveau mot de passe, l'assistant reprend (**Get Started**) ;
   - **Welcome to Nexus Repository Community Edition** → **Next** ;
   - **End User License Agreement** : cocher **I accept the terms and conditions** → **Next** ;
   - **Configure Anonymous Access** : laisser **Disable anonymous access** (présélectionné) → **Next** ;
   - **Required base telemetry** : Nexus Community Edition envoie chaque jour des données d'usage à Sonatype, et passe en lecture seule après 10 jours sans envoi. Cocher **I understand this requirement and its impact** → **Finish**.
4. Créer un rôle de publication : icône roue dentée dans la barre de gauche (administration) → **Security → Roles** → **Create Role** → **Type** : **Nexus role** :
   - **Role ID** : `deploy-maven`, **Role Name** : `deploy-maven`
   - **Modify Applied Privileges** → boîte **Privileges Selection** : dans **Filter**, taper `nx-repository-view-maven2-*-` puis cocher `nx-repository-view-maven2-*-add`, `-browse`, `-edit` et `-read` (pas `-*` ni `-delete`) → **Confirm**
   - **Save**
5. Créer l'utilisateur technique : **Security → Users** → **Create local user** :
   - **ID** `jenkins`, **First name** `Jenkins`, **Last name** `CI`, **Email** `jenkins@example.com`
   - **Password** / **Confirm password** : `Jenkins-2026`
   - **Status** : **Active**
   - **Roles** : dans **Available**, sélectionner `deploy-maven`, puis la flèche **>** pour le passer dans **Granted**
   - bouton **Create local user** (en bas du formulaire)
6. **Repository → Repositories** : vérifier la présence de `maven-releases` (hosted, **Deployment policy** : *Disable redeploy*), `maven-snapshots` (hosted) et `maven-public` (group, qui regroupe aussi le proxy `maven-central`).

**Credentials et settings.xml géré (slides 53 et 68)**

7. Jenkins → **Manage Jenkins → Credentials** → **Add Credentials** → **Username with password** → **Next** :
   - **Scope** `Global (Jenkins, nodes, items, all child items, etc)` (valeur par défaut : c'est un pipeline qui utilise ce credential, comme `gitea-token` à la démo 7), **Username** `jenkins`, **Password** `Jenkins-2026`, **ID** `nexus-deploy`, **Description** `Nexus - publication Maven` → **Create**
8. **Manage Jenkins** → bloc **System Configuration** → **Managed files** (ajouté par Config File Provider) → **Add a new Config**. Page **New configuration** : **Type** = **Maven settings.xml** (pas *Global Maven settings.xml*) ; le champ **ID of the config file** est prérempli avec un identifiant aléatoire : le remplacer par `nexus-settings` → **Next**.
9. Page **Edit Configuration File** : **Name** `MySettings` → `nexus-settings` ; laisser **Comment**, **Replace All** et **Server Credentials** tels quels. Le **Content** contient un `settings.xml` d'exemple complet (plus de 100 lignes) : cliquer dans l'éditeur, tout sélectionner (Cmd+A / Ctrl+A), effacer, puis coller le contenu de `library-api/ci/settings-nexus.xml` :

   ```xml
   <settings>
     <servers>
       <server>
         <id>nexus-releases</id>
         <username>${env.NEXUS_USR}</username>
         <password>${env.NEXUS_PSW}</password>
       </server>
       <server>
         <id>nexus-snapshots</id>
         <username>${env.NEXUS_USR}</username>
         <password>${env.NEXUS_PSW}</password>
       </server>
     </servers>
   </settings>
   ```

   **Submit**. La page **Config File Management** liste `nexus-settings` sous **Maven settings.xml**. Aucun mot de passe n'est écrit dans le fichier : `NEXUS_USR` et `NEXUS_PSW` viennent de `credentials('nexus-deploy')` au moment du build (slide 45). (Le bloc **Server Credentials** permettrait l'inverse : laisser Jenkins injecter un credential pour un `<server>` donné.)

**Le job de déploiement**

10. Dossier `library` → **New Item** → `library-api-deploiement` → **Duplicate an existing item** → `library-api-pipeline` → **OK** → **Script Path** : `ci/Jenkinsfile.deploiement` → **Save** → **Build Now**.
11. Suivre les stages dans **Pipeline Overview** :
    - **Publish to Nexus** : console `+ mvn -B -ntp -s /home/jenkins/agent/workspace/library/library-api-deploiement@tmp/config...tmp -Drevision=1.4.1 -DskipTests deploy` (le `settings.xml` géré est copié dans un fichier temporaire), puis `--- deploy:3.1.4:deploy (default-deploy) @ library-api ---` et `BUILD SUCCESS`. L'option `-ntp` masque le détail des transferts ;
    - **Docker image** : `naming to docker.io/library/library-api:1.4.1 done` ;
    - **Deploy recette** : `Trying to acquire lock on [Resource: env-recette]`, `Lock acquired on [Resource: env-recette]`, puis `{"status":"UP"}` (smoke test réussi) ;
    - **Approve production** : le build se met en pause, état **Paused for Input**.

12. Vérifier la recette pendant la pause : http://localhost:8090/api/books renvoie les trois livres ; http://localhost:8090/actuator/info affiche `"version":"1.4.1"`.
13. Vérifier Nexus : icône **Browse** (barre de gauche) → `maven-releases` → `fr` → `utopios` → `library-api` → `1.4.1` : `library-api-1.4.1.jar`, `library-api-1.4.1.pom` et leurs empreintes `.md5` / `.sha1`. Le POM publié porte `<version>1.4.1</version>` grâce au flatten-maven-plugin (sinon il contiendrait `${revision}`).
14. Approuver : la console se termine par **Input requested** (lien), et la page du build propose l'entrée **Paused for Input**. La page de saisie affiche **Deployer 1.4.1 en production ?**, le champ **TICKET** (`CHG-0001`) et les boutons **Deployer** / **Abort**. Cliquer **Deployer**.

    Résultat : la console affiche `Approved by Administrateur Jenkins`, puis le stage **Deploy production** écrit `Approuve par admin (CHG-0001)` ; http://localhost:8091/actuator/info renvoie `{"app":{"version":"1.4.1"}}` et la description du build devient `v1.4.1 en production (admin, CHG-0001)`.

15. Relancer **Build Now** et cette fois cliquer **Abort** à l'étape d'approbation : la console affiche `Rejected by Administrateur Jenkins` et le build se termine **ABORTED**. La recette porte `1.4.2` (http://localhost:8090/actuator/info), la production reste en `1.4.1` (http://localhost:8091/actuator/info).

16. **Manage Jenkins → Lockable Resources** (tuile du bloc **System Configuration**, aussi accessible par le menu ☰ **More actions** de l'en-tête). Pendant un build, la ressource `env-recette` (puis `env-production`) apparaît, verrouillée par ce build. Une fois le build terminé, la page affiche **No resources configured** : `lock('env-recette')` crée une ressource *éphémère*, supprimée dès qu'elle est libérée. Le bouton **Add Resource** sert à déclarer des ressources permanentes (avec labels).

> **À retenir.** La version déployée en production (`1.4.1`) est celle qui a été testée en recette et publiée dans Nexus : on ne reconstruit jamais pour la prod (slide 67). Rejouer la publication d'une même version échouerait : `maven-releases` interdit le redéploiement.

---

## Démo 15 — Analyse qualité avec SonarQube

> Slides : 71 à 73 · Durée : 25 min · Prérequis : démo 14

**Pourquoi.** Les tests disent si le code fait ce qu'on attend ; l'analyse statique dit s'il est maintenable et sûr. La slide 72 enchaîne `mvn verify`, `mvn sonar:sonar` et `waitForQualityGate` : SonarQube rend son verdict par webhook et Jenkins arrête le pipeline si la Quality Gate est rouge. Le réglage croise trois écrans (SonarQube, credentials, System), d'où l'intérêt de le dérouler une fois en entier.

**Ce qu'elle montre.** La génération d'un token SonarQube, le webhook vers Jenkins, la déclaration du serveur dans Jenkins, une analyse dont le lien s'affiche sur le build, puis une Quality Gate durcie qui fait échouer le pipeline. En bonus, l'onglet Warnings NG (slide 73).

### Étapes

**Démarrer SonarQube (slide 71)**

1. Démarrer le service (2 Go de RAM environ, 1 à 2 minutes) et attendre l'état `UP` :

   ```bash
   docker compose up -d sonarqube
   ```

   ```bash
   until curl -s http://localhost:9000/api/system/status | grep -q '"status":"UP"'; do sleep 5; done; echo SonarQube pret
   ```

   Version de référence : **SonarQube Community Build 26.10**. Si le port 9000 est déjà pris sur le poste (php-fpm l'utilise souvent sur macOS), mettre `SONAR_PORT=9001` dans `.env` et remplacer `localhost:9000` par `localhost:9001` dans cette démo ; l'adresse vue depuis Jenkins reste `http://sonarqube:9000`.

2. http://localhost:9000 → `admin` / `admin` → **Log in**. Page **Update your password** : **Old Password** `admin`, **Password** et **Confirm Password** `Formation-2026!` (un caractère spécial est exigé) → **Update**. SonarQube ouvre **How do you want to create your project?** : ne rien choisir, le projet sera créé par la première analyse.
3. Avatar **A** en haut à droite → **My Account** → onglet **Security** → bloc **Generate Tokens** :
   - **Name** : `jenkins`
   - **Type** : **Global Analysis Token** (liste *Select Token Type*)
   - **Expires in** : **30 days**
   - **Generate**. Le message *New token "jenkins" has been created. Make sure you copy it now* affiche le jeton `sqa_...` : le copier.
4. Autoriser les webhooks vers le réseau Docker : **Administration** → **Configuration** → **General Settings** → catégorie **Security** → interrupteur **Enable local webhooks validation** sur *off* → **Save**.

   Sans ce réglage, l'étape suivante échoue avec *Invalid URL: loopback, wildcard, link-local, site-local, multicast, cloud metadata addresses and addresses of the SonarQube server itself are not allowed for webhooks* : `jenkins` a une adresse privée du réseau Docker. Ce réglage n'a de sens que sur une instance de formation ; en production, Jenkins a une adresse publique ou passe par un reverse proxy.

5. **Administration** → **Configuration** → **Webhooks** → **Create** :
   - **Name** : `jenkins`
   - **URL** : `http://jenkins:8080/sonarqube-webhook/`
   - **Secret** : vide
   - **Create**. La ligne `jenkins` apparaît avec **Last delivery** *Never*.

**Déclarer SonarQube dans Jenkins (slide 71)**

6. **Manage Jenkins → Credentials** → **Add Credentials** → **Secret text** → **Next** :
   - **Secret** : le jeton `sqa_...`, **ID** `sonar-token`, **Description** `SonarQube - analyse` → **Create**
7. **Manage Jenkins → System** → bloc **SonarQube servers** :
   - cocher **Environment variables**
   - sous **SonarQube installations**, **Add SonarQube** → **Name** `sonarqube`, **Server URL** `http://sonarqube:9000` (le champ propose `http://localhost:9000` par défaut : à remplacer), **Server authentication token** `SonarQube - analyse`
   - **Save**

**Le job qualité (slide 72)**

8. Dossier `library` → **New Item** → `library-api-qualite` → **Duplicate an existing item** → `library-api-pipeline` → **OK** → **Script Path** `ci/Jenkinsfile.qualite` → **Save** → **Build Now**.

   Résultat :
   - stage **SonarQube analysis** : `ANALYSIS SUCCESSFUL, you can find the results at: http://sonarqube:9000/dashboard?id=fr.utopios%3Alibrary-api` ;
   - stage **Quality Gate** : `Checking status of SonarQube task '...' on server 'sonarqube'`, `status is 'PENDING'`, puis `status is 'SUCCESS'` et `completed. Quality gate is 'OK'` ;
   - page du job : cadre **SonarQube Quality Gate** → `library-api` **Passed** ;
   - page du build : menus **Java Compiler Warnings** et **Maven Warnings** (Warnings NG, 0 alerte ici).

   Dans SonarQube, **Administration → Webhooks** : la colonne **Last delivery** du webhook `jenkins` est passée au vert.

9. Dans SonarQube → **Projects** → `library-api` : 0 bug, 0 vulnérabilité, 1 problème de maintenabilité, couverture 84,6 % (lue dans le rapport JaCoCo), 0 % de duplication.

   L'URL du lien dans la console contient `sonarqube:9000` : depuis le navigateur, remplacer par `localhost:9000`.

**Faire échouer la Quality Gate**

10. SonarQube → **Quality gates** → **Create** → **Name** `formation-stricte` → **Create**. La nouvelle gate reprend les quatre conditions recommandées sur le nouveau code (*This quality gate has all of the conditions recommended by Sonar*). Ajouter une condition sur l'ensemble du code :
    - **Add Condition** → **Where?** : **On Overall Code** ; **Quality gate fails when** : taper puis choisir **Coverage** ; l'opérateur affiché est **is less than** ; **Value** `90` → **Add Condition** ;
    - bouton **Actions** (en haut à droite de la gate) → **Set as Default**.
11. Jenkins → `library-api-qualite` → **Build Now**.

    Résultat : build **FAILURE**, avec dans la console `Quality gate is 'ERROR'` puis `ERROR: Pipeline aborted due to quality gate failure: ERROR` (`abortPipeline: true`). Dans SonarQube, le projet affiche **Failed** et la condition non respectée (84,6 % < 90 %).

12. Remettre **Sonar way** par défaut (**Quality gates** → **Sonar way** → **Actions** → **Set as Default**), relancer : le build repasse au vert.

> **Point clé.** Sans le webhook de l'étape 5, `waitForQualityGate` attend jusqu'au `timeout` (10 minutes) : c'est la première chose à vérifier quand ce stage ne se termine pas. La livraison du webhook se lit dans SonarQube (**Administration → Webhooks**, colonne **Last delivery**).

### En cas de problème

| Symptôme | Cause probable | Correction |
|---|---|---|
| http://localhost:9000 affiche autre chose que SonarQube | Un autre service occupe déjà le port 9000 sur le poste | `SONAR_PORT=9001` dans `.env`, puis `docker compose up -d sonarqube` |
| SonarQube ne passe jamais `UP`, les logs parlent de *high disk watermark* | Le disque de la VM Docker est presque plein | Déjà neutralisé dans `docker-compose.yml` (`SONAR_SEARCH_JAVAADDITIONALOPTS`) ; sinon libérer de la place (`docker system df`) |
| *Invalid URL ... site-local ... not allowed for webhooks* | Validation des webhooks locaux active | Étape 4 de cette démo |
| `waitForQualityGate` ne se termine pas | Webhook absent ou en échec | **Administration → Webhooks** : vérifier l'URL et **Last delivery** |

---

## Démo 16 — Habilitations

> Slides : 74 à 77 · Durée : 25 min · Prérequis : démo 15

**Pourquoi.** Depuis la démo 1, tout utilisateur connecté peut tout faire (**Logged-in users can do anything**). La slide 74 sépare deux questions : qui êtes-vous (security realm) et que pouvez-vous faire (authorization strategy). Les slides 75 et 76 proposent deux réponses, la matrice et les rôles ; la slide 77 détaille ce qu'un rôle permet réellement. Le vérifier avec de vrais comptes, dans une fenêtre de navigation privée, rend visibles des comportements peu intuitifs (un job invisible, un menu absent, un bouton **Build** qui disparaît).

**Ce qu'elle montre.** La création de trois comptes, une matrice globale, puis la stratégie par rôles avec des rôles d'item appliqués au dossier `library/` par expression régulière, et l'effet de chaque rôle vu par l'utilisateur concerné.

### Étapes

**Créer les comptes (slide 74, security realm « Jenkins' own user database »)**

1. **Manage Jenkins → Security** : vérifier **Security Realm** = **Jenkins' own user database** et **Allow users to sign up** décoché.
2. **Manage Jenkins → Users** → **Create User**, trois fois (formulaire **Username**, **Password**, **Confirm password**, **Full name**, **Email**, bouton **Create User**) :

   | Username | Password | Full name | Email |
   |---|---|---|---|
   | `viewer1` | `Viewer-2026` | `Stagiaire lecture` | `viewer1@example.com` |
   | `dev1` | `Dev-2026` | `Developpeuse library` | `dev1@example.com` |
   | `release1` | `Release-2026` | `Release manager` | `release1@example.com` |

**Matrice globale (slide 75) : lecture de l'écran**

3. **Manage Jenkins → Security** → **Authorization** : choisir **Matrix-based security**. Sous la liste apparaissent un champ **Filter users and groups**, les boutons **Add user** et **Add group**, et deux lignes **Anonymous** et **Authenticated Users** marquées *No permissions granted*.
4. Cliquer **Add user** → boîte **Add user**, champ **Username:** `admin` → **OK**. La ligne **Administrateur Jenkins** s'ajoute, dépliée : les permissions sont rangées par catégorie (**Overall**, **Credentials**, **Agent**, **Job**, **Run**, **View**, **SCM**, **Lockable Resources**), avec les noms de la slide 75. Les icônes à droite de chaque ligne accordent ou retirent toutes les permissions d'un coup ; le chevron replie la ligne.

   Ne pas enregistrer : cette démo continue avec la stratégie par rôles.

> **Point clé.** Avant tout **Save** d'une matrice, vérifier qu'un compte garde **Overall/Administer**. Sinon, on se verrouille hors de Jenkins ; la seule sortie est de passer `<useSecurity>false</useSecurity>` dans `JENKINS_HOME/config.xml` et de redémarrer (slide 75).

**Rôles (slide 76)**

5. Toujours dans **Authorization**, choisir **Role-Based Strategy** (ajouté par le plugin de la démo 6) → **Save**. Le compte connecté reçoit automatiquement le rôle global `admin`.

   **Manage Jenkins** affiche un bandeau *The Restrict project naming configuration is not set to the Role-based Strategy* : il signale que des utilisateurs pouvant créer des jobs pourraient leur donner un nom hors de leurs motifs. On peut l'ignorer ici (personne n'a **Job/Create**).

6. **Manage Jenkins → Role Management** (bloc **Security**) : la page **Assign Roles** s'ouvre. Cliquer le lien **Manage Roles** pour arriver sur la page **Roles**, avec trois onglets **Global roles**, **Item roles**, **Agent roles**.
7. Onglet **Global roles** → bouton **Add Role** → boîte **Add global role** : **Name** `reader`, cocher **Overall → Read** → **Add**. La ligne `reader` / *Overall/Read* apparaît ; elle est enregistrée immédiatement (pas de bouton **Save** sur cette page).
8. Onglet **Item roles** → **Add Role** → boîte **Add item role**, deux fois :

   | Name | Pattern | Permissions à cocher |
   |---|---|---|
   | `library-dev` | `library(/.*)?` | Job : **Build**, **Cancel**, **Configure**, **Read**, **Workspace** ; Run : **Replay** |
   | `library-release` | `library(/(library-api-deploiement\|deploy-.*))?` | Job : **Build**, **Read** |

   Cocher les cases en cliquant dessus (la liste défile dans la boîte ; le champ **Filter permissions** aide à les retrouver), puis **Add**.

   Le résumé d'une ligne n'affiche que les permissions de base : **Discover** (impliquée par **Read**) et **Replay** (impliquée par **Configure**) n'y apparaissent pas. Cliquer le motif d'un rôle (bouton `library(/.*)?`) liste les items qu'il couvre.

> **Point clé : le motif doit couvrir le dossier.** La slide 76 écrit `library/.*`. Ce motif couvre les jobs *dans* le dossier, mais pas le dossier `library` lui-même : sans droit de lecture sur le dossier, `dev1` ne voit rien du tout (vérifié). `library(/.*)?` couvre à la fois `library` et `library/...`.

9. Lien **Assign Roles** (fil d'Ariane **Role Management**) :
   - onglet **Global roles** : sur la ligne **authenticated** (*Built-in*), bouton **Edit roles** → boîte **Edit roles: authenticated** → cocher **reader** → **Save**. Tout utilisateur connecté peut désormais ouvrir Jenkins ;
   - onglet **Item roles** → **Add User or Group** → boîte **Add user or group** : **Type** *User*, **User ID** `dev1`, cocher **library-dev** → **Add** ;
   - recommencer avec **User ID** `release1` et **library-release**.

**Vérifier chaque profil (slide 77)**

10. Ouvrir une fenêtre de navigation privée sur http://localhost:8080 et se connecter en `viewer1` : le tableau de bord est vide (le rôle `reader` ne donne que **Overall/Read**, aucun **Job/Read**) ; **Manage Jenkins** est absent.
11. Se déconnecter (icône personnage → **Sign out**) et se reconnecter en `dev1` :
    - seul le dossier `library` est visible ; `hello`, `workspace-demo` et `outils` (à la racine) ne le sont pas ;
    - dans `library`, tous les jobs sont visibles ; sur `library-api-tests`, **Build Now** et **Configure** sont présents, et la page d'un build propose **Replay** ;
    - **Manage Jenkins** n'apparaît pas (une URL `/manage/` tapée à la main répond **403**).
12. Se reconnecter en `release1` :
    - le dossier `library` ne contient que `library-api-deploiement` (et `deploy-prod` à la démo 17) ;
    - **Build Now** est présent, **Configure** absent (l'URL `/configure` répond **403**) ;
    - lancer un build : à l'étape **Approve production**, `release1` peut cliquer **Deployer**, et la description du build se termine par `(release1)`.

> **À retenir.** `dev1` a **Job/Configure** sur le dossier : il peut modifier un pipeline et lui faire afficher n'importe quel credential accessible au job (slide 77). Les credentials de production vont donc dans un dossier où les développeurs n'ont pas **Configure**, et le Jenkinsfile vient du dépôt, relu en revue.

---

## Démo 17 — Pipeline complet du fil rouge

> Slides : 78, 79 · Durée : 20 min · Prérequis : démos 10 à 16 (credentials `gitea-token`, `nexus-deploy`, `sonar-token`, fichier `nexus-settings`, serveurs SonarQube et SMTP)

**Pourquoi.** Chaque démo a isolé une brique. La slide 78 les assemble dans un seul Jenkinsfile, exécuté par le Multibranch Pipeline : c'est la forme qu'a la CI d'un vrai projet. Le dérouler en entier vérifie que toute la configuration des démos précédentes est cohérente, et montre l'organisation recommandée en slide 70 : un pipeline CI par dépôt et un job CD paramétré qui déploie une version.

**Ce qu'elle montre.** Sur `main` : build et tests, couverture, Quality Gate, publication Nexus, image Docker, recette avec verrou et smoke test, approbation, puis délégation au job `deploy-prod`. Sur une autre branche : les mêmes vérifications, sans publication ni déploiement.

### Étapes

**Le job CD `deploy-prod`**

1. Dossier `library` → **New Item** → `deploy-prod` → **Duplicate an existing item** → `library-api-pipeline` → **OK** → **Script Path** `ci/Jenkinsfile.deploy-prod` → **Save** → **Build Now**.

   Ce premier build échoue volontairement (`ERROR: ARTIFACT_VERSION est obligatoire`) : il sert à enregistrer le paramètre. Le menu affiche ensuite **Build with Parameters** ; un lancement avec `ARTIFACT_VERSION` = une version déjà construite (par exemple `1.4.1`) redéploie la production sans rien reconstruire : c'est le rollback de la slide 67.

**Basculer le Multibranch sur le pipeline complet**

2. `library » library-api` → **Configure** → **Build Configuration** → **Script Path** : `ci/Jenkinsfile.complet` → **Save**. Jenkins relance un scan, mais ne reconstruit pas `main` (le code n'a pas changé) : ouvrir le sous-job **main** et cliquer **Build Now**.
3. Suivre `main` dans **Pipeline Overview** :

   | Stage | Ce qu'on vérifie |
   |---|---|
   | **Checkout** | nom du build `#n <sha court>` (par exemple `#10 3991b6c`) |
   | **Build & Unit tests** | onglets **Tests** et **Coverage** |
   | **Quality** | `Quality gate is 'OK'` |
   | **Publish** | `library-api-1.4.<n>` dans `maven-releases`, image `library-api:1.4.<n>` |
   | **Deploy recette** | `lock` sur `env-recette`, smoke test `UP` sur http://localhost:8090 |
   | **Production** | pause : la console affiche `Deployer 1.4.<n> en production ?` puis `Deployer or Abort` |

4. Connecté en `admin`, ouvrir **Paused for Input** sur la page du build et cliquer **Deployer**. La console affiche `Approved by Administrateur Jenkins`, `Starting building: library » deploy-prod #<m>` puis `Build library » deploy-prod #<m> v1.4.<n> completed: SUCCESS`. Le stage **Production** lance `library » deploy-prod` avec `ARTIFACT_VERSION=1.4.<n>` (`build job: 'library/deploy-prod'` : chemin complet, car le pipeline s'exécute dans `library » library-api » main`) ; un nouveau build de `deploy-prod` apparaît, nommé `#<m> v1.4.<n>`, et http://localhost:8091/actuator/info affiche la nouvelle version.

   `release1` figure dans `submitter`, mais son rôle de la démo 16 ne couvre pas `library/library-api` : pour qu'il puisse approuver ici, il faudrait étendre le motif de `library-release` à ce job.

**Comportement sur une branche**

5. Gitea → créer la branche `feature/demo-finale` depuis `main`.

   Résultat : le sous-job `feature/demo-finale` exécute **Checkout**, **Build & Unit tests** et **Quality** ; **Publish**, **Deploy recette** et **Production** sont grisés (`when { branch 'main' }`). Rien n'est publié ni déployé.

6. Revenir sur `library » library-api` : la page liste les deux branches, leur météo et leur dernier statut.

**Relecture (slide 79)**

7. Ouvrir `library-api/ci/Jenkinsfile.complet` et relier chaque bloc à la démo qui l'a introduit :

   | Bloc | Démo |
   |---|---|
   | `agent { label 'linux' }`, `tools` | 5, 7 |
   | `options`, `buildDiscarder`, `timestamps` | 3, 4 |
   | `triggers { cron(...) }` + webhook | 3, 10 |
   | `junit`, `recordCoverage` | 12 |
   | `withSonarQubeEnv`, `waitForQualityGate` | 15 |
   | `configFileProvider`, `credentials('nexus-deploy')` | 14 |
   | `lock`, `input`, `build job:` | 14, 16 |
   | `post { failure / unstable / fixed }`, `emailext` | 13 |

> **Écarts avec la slide 78.** Kubernetes est remplacé par un conteneur Docker (`library-api-recette`), Slack par un mail `fixed`, le registry par une image locale ; `submitter: 'admin,release1'` remplace le groupe `release-managers`, qu'une base d'utilisateurs Jenkins ne sait pas définir (un annuaire LDAP ou un SSO le fournirait).

---

## Remise à zéro

| Besoin | Commande |
|---|---|
| Arrêter la stack en gardant tout | `docker compose --profile deploiement --profile qualite down` |
| Supprimer les conteneurs déployés par les démos | `docker rm -f library-api-recette library-api-prod` |
| Tout effacer (Jenkins, Gitea, Nexus, SonarQube, cache Maven) | `docker compose --profile deploiement --profile qualite down -v` |
| Rejouer seulement la démo 1 | `docker compose down` puis `docker volume rm jenkins-formation_jenkins_home` puis `docker compose up -d` |
