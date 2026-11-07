# Démos Jenkinsfile DevSecOps

### Construire un pipeline pas à pas avec les générateurs de Jenkins

> **Version 2 — même contenu que `DEMOS.md`, mise en page aérée.**
> Une démo = une fiche, des étapes numérotées, un encadré par résultat attendu.

---

## En bref

| | |
|---|---|
| **Point de départ** | Jenkins à la fin de `../1-demos-jenkins-ci/DEMOS-v2.md` (démo 17 terminée) |
| **Ce qu'on construit** | un pipeline DevSecOps complet, écrit de zéro, puis une pipeline de déploiement qu'il appelle |
| **Comment** | avec le **Snippet Generator** (les *steps*) et le **Declarative Directive Generator** (les *directives*) |
| **Projet** | `library-api-devsecops` : une copie de l'API Spring Boot de la partie 1, avec des défauts volontaires |
| **Durée totale** | environ 5 h |

### Les défauts que la chaîne doit trouver

| Défaut volontaire | Outil | Démo |
|---|---|---|
| Un jeton GitHub poussé dans le dépôt (ajouté pendant la démo) | **Gitleaks** — secrets | 6 |
| `commons-text` 1.9 (Text4Shell) et Spring Boot 3.5.6 vulnérable | **Trivy** — dépendances (SCA) | 7 |
| Une empreinte calculée en MD5 | **Semgrep** — analyse du code (SAST) | 8 |
| Couverture et maintenabilité | **SonarQube** + Coverage | 9 |
| Un Dockerfile mal écrit | **Hadolint** | 11 |
| L'image construite | **Trivy** (image) + SBOM | 11 |

### Versions de référence

| Composant | Version |
|---|---|
| Jenkins | 2.580.2 LTS |
| Gitea | 1.24.7 |
| SonarQube Community Build | 26.10 |
| Maven | 3.9.16 |
| Plugins Warnings / Coverage / SonarQube Scanner | 13.10345 / 4.3547 / 2.19.0 |
| Trivy / Gitleaks / Hadolint / Semgrep (dans l'agent du kit) | 0.76.2 / 8.30.1 / 2.15.1 / 1.184.0 |

---

## Avant de commencer

### 1. Ce que l'on reprend de la partie 1

Rien n'est réinstallé. Le pipeline s'appuie sur ce que DEMOS-v2 a mis en place :

| Élément | Créé à la démo… (partie 1) | Sert ici à… |
|---|---|---|
| Compte `admin` / `Formation-2026`, interface en anglais | 1 | tout |
| Built-In Node à 0 executor, agent `linux-1`, credential `agent-ssh-key` | 5 | créer l'agent outillé par copie (démo 0) |
| Plugins **Warnings**, **Coverage**, **SonarQube Scanner** | 6 | `recordIssues`, `recordCoverage`, `withSonarQubeEnv` |
| Outils `jdk21`, `maven-3.9` ; credential `gitea-token` | 7 | `tools { }`, step `git` |
| Serveur `sonarqube`, credential `sonar-token`, webhook vers Jenkins | 15 | démo 9 |
| Stratégie par rôles (`admin` a tous les droits) | 16 | créer et lancer les jobs |

Le kit **ajoute seulement** :

- un agent outillé **`devsecops-1`** (Trivy, Gitleaks, Hadolint, Semgrep) ;
- un dépôt Gitea séparé, **`formation/library-api-devsecops`** ;
- un dossier Jenkins **`devsecops`** pour ranger les jobs.

Les jobs de la partie 1 (dossier `library`, dépôt `library-api` et son webhook) ne sont pas touchés.

---

### 2. Deux fichiers `docker-compose.yml`, deux rôles

| Compose | Dossier | Contenu | Quand on s'en sert |
|---|---|---|---|
| Partie 1 | `1-demos-jenkins-ci` | jenkins, linux-1, gitea, mailpit (+ sonarqube) | déjà démarré ; on démarre seulement SonarQube à la démo 9 |
| Ce kit | `1-demos-jenkinsfile-devsecops` | **devsecops-1 uniquement** | une fois, à la démo 0 |

Le compose du kit ne recrée ni Jenkins, ni Gitea : il ajoute **un conteneur d'agent**, branché sur le réseau `ci-formation` de la partie 1, avec la même clé SSH que `linux-1`.

---

### 3. Deux façons de fournir un outil au build

| | **Tools Jenkins** (Maven, JDK) | **Outils de l'agent** (Trivy, Semgrep…) |
|---|---|---|
| Où c'est déclaré | **Manage Jenkins → Tools** + directive `tools { }` | `agent/Dockerfile` du kit |
| Installation | Jenkins télécharge Maven sur l'agent au premier build | présents dès le démarrage du conteneur |
| Ce que le Jenkinsfile référence | un **nom** d'outil (`maven-3.9`) | un **label** d'agent (`devsecops`) |
| Plugin Jenkins nécessaire | non (installateur intégré) | non : lancés avec `sh` |

Les plugins **Warnings**, **Coverage** et **SonarQube Scanner** ne lancent pas les outils : ils **lisent leurs rapports** après coup et les affichent dans Jenkins.

---

### 4. Comment on remplit le Jenkinsfile

Les générateurs **n'écrivent jamais dans le Jenkinsfile** : ils affichent du texte, qu'on copie puis qu'on colle.

```
 ┌──────────────────────────────┐        ┌─────────────────────────────────────┐
 │  Onglet 1 : Pipeline Syntax  │        │  Onglet 2 : le script du pipeline    │
 │  (menu du job)               │        │                                     │
 │                              │ copier │  démos 1 à 4 : job → Configure →    │
 │  1. remplir le formulaire    │ ─────► │     Pipeline → zone Script          │
 │  2. Generate...              │ coller │                                     │
 │  3. sélectionner le texte    │        │  démo 5 et suivantes : Gitea →      │
 │                              │        │     Jenkinsfile → Edit File         │
 └──────────────────────────────┘        └─────────────────────────────────────┘
                                                        │
                                                        ▼
                                          Save (ou Commit Changes) → Build
```

**Où coller ?** Une seule règle :

| Ce qu'on a généré | Où on le colle |
|---|---|
| une **directive** (`agent`, `tools`, `options`, `environment`, `parameters`, `triggers`, `when`, `input`, `post`) | directement sous `pipeline {` — ou sous `stage('…') {` pour `when`, `input`, `post`, `options`, `agent` |
| un **stage** | dans `stages { }` |
| un **step** (`sh`, `git`, `junit`, `recordIssues`…) | dans `steps { }` ou dans un bloc de `post` (`always { }`, `success { }`…) |

> 💡 **À retenir** — Le générateur de directives ne propose jamais `sh` ; celui de steps ne propose jamais `agent`. Se tromper de générateur, c'est se tromper d'emplacement.

À chaque démo, le Jenkinsfile complet attendu est dans **`solutions/NN-….Jenkinsfile`** : pour comparer, ou pour rattraper un retard en le recopiant.

La page **Pipeline Syntax** est décrite en détail dans `../1-demos-jenkins-ci/PIPELINE-SYNTAX.md`.

---

## Sommaire

| Démo | Sujet | Générateurs utilisés | Durée |
|:---:|---|---|:---:|
| **0** | Vérifier l'état de départ, ajouter l'agent outillé | — | 15 min |
| **1** | Le squelette | `agent`, `stage` · `git`, `sh` | 20 min |
| **2** | Build, tests et rapports | `tools`, `post` · `junit`, `recordCoverage`, `archiveArtifacts` | 20 min |
| **3** | Options, environnement, déclencheur | `options`, `environment`, `triggers` | 15 min |
| **4** | Paramètres | `parameters` | 15 min |
| **5** | Le Jenkinsfile dans le dépôt | — | 15 min |
| **6** | Secrets : Gitleaks | `recordIssues` | 25 min |
| **7** | Dépendances vulnérables : Trivy | `recordIssues` | 25 min |
| **8** | SAST : Semgrep | `catchError` | 15 min |
| **9** | Qualité : SonarQube et Quality Gate | `when` · `withSonarQubeEnv`, `waitForQualityGate`, `timeout` | 20 min |
| **10** | Analyses en parallèle | `stage` (Parallel Stages) | 15 min |
| **11** | Dockerfile, image et SBOM | `recordIssues` (quality gate) | 25 min |
| **12** | Multibranch et conditions | `when` (anyOf, branch, changeset), `post` | 25 min |
| **13** | Une pipeline qui en appelle une autre | `input` · `build`, `unstable` | 30 min |
| **14** | Relecture du Jenkinsfile final | — | 10 min |

Les démos s'enchaînent : chacune part de l'état laissé par la précédente.

---

## Contenu du kit

```
1-demos-jenkinsfile-devsecops/
├── DEMOS.md / DEMOS-v2.md      ce document (deux mises en page)
├── POINTS-DE-VIGILANCE.md      pièges relevés en déroulant les démos
├── docker-compose.yml          agent devsecops-1, sur le réseau ci-formation de la partie 1
├── agent/                      image de l'agent : JDK 21, Git, Docker, Trivy, Gitleaks, Hadolint, Semgrep
├── scripts/
│   └── init-depot.sh / .ps1    crée le dépôt formation/library-api-devsecops et y pousse le projet
├── library-api/                le projet, SANS Jenkinsfile (on l'écrit)
└── solutions/
    ├── 01-squelette.Jenkinsfile … 13-appel-deploiement.Jenkinsfile
    ├── 13-ci-Jenkinsfile.deploy    la pipeline de déploiement
    └── fichiers/                   pom-corrige.xml, .trivyignore, Checksums-corrige.java,
                                    Dockerfile-corrige, application-notif.yml, gitleaksignore-exemple
```

Le kit de la partie 1 doit se trouver à côté, dans `../1-demos-jenkins-ci`.

## Adresses

Celles de la partie 1 (Jenkins http://localhost:8080, Gitea http://localhost:3000, SonarQube http://localhost:9000), plus :

| Service | Navigateur | Depuis les conteneurs |
|---|---|---|
| library-api-devsecops en **recette** (démo 13) | http://localhost:8092 | `library-api-devsecops-recette:8080` |
| library-api-devsecops en **production** (démo 13) | http://localhost:8093 | `library-api-devsecops-production:8080` |

Les ports 8090 et 8091 restent ceux de `library-api-recette` et `library-api-prod`, déployés par les démos 14 et 17 de la partie 1.

---
---

## Démo 0 — Vérifier l'état de départ et ajouter l'agent outillé

| | |
|---|---|
| **Objectif** | Avoir tout ce que le Jenkinsfile va nommer : outils, credentials, SonarQube, et un agent qui porte les outils de sécurité |
| **Durée** | 15 min (+ construction de l'image de l'agent) |
| **Prérequis** | partie 1 terminée, sa stack démarrée, 6 Go libres dans Docker |

### Pourquoi

Un Jenkinsfile ne contient que des **noms** : `label 'devsecops'`, `jdk 'jdk21'`, `credentialsId: 'gitea-token'`, `withSonarQubeEnv('sonarqube')`. Ils doivent exister avant le premier build.

La plupart viennent de la partie 1 : on **vérifie**. Il manque un agent qui porte les outils de sécurité : on le **crée par copie** de `linux-1`.

### Ce que vous allez obtenir

- les prérequis de la partie 1 contrôlés ;
- un node `devsecops-1` en ligne, avec le label `devsecops` ;
- le dépôt `library-api-devsecops` et le dossier Jenkins `devsecops`.

---

### Étape 1 — La stack de la partie 1 tourne

Dans `../1-demos-jenkins-ci` :

```bash
docker ps --format '{{.Names}}'
```

> ✅ **Résultat attendu** — `jenkins`, `linux-1`, `gitea`, `mailpit` (et `sonarqube` s'il est déjà démarré ; sinon il le sera à la démo 9).

---

### Étape 2 — Contrôler Jenkins

Se connecter sur http://localhost:8080 (`admin` / `Formation-2026`), puis vérifier :

| Où | Attendu | Si absent, voir |
|---|---|---|
| **Manage Jenkins → Nodes** | `linux-1` en ligne · **Built-In Node** à 0 executor | démo 5 de la partie 1 |
| **Manage Jenkins → Plugins → Installed plugins** | `Warnings`, `Coverage`, `SonarQube Scanner` | démo 6 de la partie 1 |
| **Manage Jenkins → Tools** | JDK `jdk21` · Maven `maven-3.9` | démo 7 de la partie 1 |
| **Manage Jenkins → Credentials** | `agent-ssh-key`, `gitea-token`, `sonar-token` | démos 5, 7 et 15 de la partie 1 |
| **Manage Jenkins → System → SonarQube servers** | `sonarqube` → `http://sonarqube:9000` | démo 15 de la partie 1 |

*Pourquoi :* une démo qui casse sur un credential manquant fait perdre le fil du Jenkinsfile. Mieux vaut le voir maintenant.

---

### Étape 3 — Démarrer l'agent outillé

```bash
cd 1-demos-jenkinsfile-devsecops
```

```bash
docker compose up -d --build
```

La première construction prend plusieurs minutes (Semgrep s'installe par pip). Le conteneur `devsecops-1` rejoint le réseau `ci-formation` et reçoit la clé publique de `../1-demos-jenkins-ci/.env`.

Vérifier les outils :

```bash
docker exec devsecops-1 sh -c 'trivy --version | head -1; gitleaks version; hadolint --version; semgrep --version'
```

> ✅ **Résultat attendu** — `Version: 0.76.2` · `v8.30.1` · `Haskell Dockerfile Linter 2.15.1` · `1.184.0`

---

### Étape 4 — Créer le node par copie de `linux-1`

**Manage Jenkins → Nodes → New Node** :

| Champ | Valeur |
|---|---|
| **Node name** | `devsecops-1` |
| **Type** | **Copy Existing Node** |
| champ qui apparaît (*Type for suggestions*) | taper `linux`, choisir `linux-1` |

Cliquer **Create**.

---

### Étape 5 — Adapter la copie

Le formulaire s'ouvre, prérempli avec la configuration de `linux-1`. Modifier **seulement** :

| Champ | Valeur |
|---|---|
| **Description** | `Agent outille DevSecOps (conteneur devsecops-1)` |
| **Number of executors** | `2` (valeur reprise de `linux-1` : la garder) |
| **Labels** | `devsecops docker java21 maven` |
| **Launch method → Host** | `devsecops-1` |

Laisser tels quels les champs repris de `linux-1` :

| Champ | Valeur reprise |
|---|---|
| **Remote root directory** | `/home/jenkins/agent` |
| **Usage** | `Only build jobs with label expressions matching this node` |
| **Credentials** | `jenkins (Cle du controller pour les agents SSH)` |
| **Host Key Verification Strategy** | `Non verifying Verification Strategy` |

Cliquer **Save**.

> ✅ **Résultat attendu** — En quelques secondes, `devsecops-1` passe en ligne (journal du node : `Agent successfully connected and online`). Une copie n'est connectée qu'après son premier **Save**.

*Pourquoi un label `devsecops`, sans `linux` :* les jobs de la partie 1 demandent `linux` et restent sur `linux-1`. Les pipelines de cette série demandent `devsecops`, le seul agent qui a les outils.

*Pourquoi 2 executors :* à la démo 13, la pipeline principale garde un executor pendant qu'elle attend la pipeline de déploiement, qui a besoin du second.

---

### Étape 6 — Créer le dépôt Gitea

macOS / Linux :

```bash
./scripts/init-depot.sh
```

Windows :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\init-depot.ps1
```

> ✅ **Résultat attendu** — `Projet pousse : http://localhost:3000/formation/library-api-devsecops`. Dans Gitea, le dépôt est **Private** et ne contient **pas** de `Jenkinsfile`.

*Pourquoi un dépôt séparé :* le dépôt `library-api` de la partie 1 a déjà un Jenkinsfile, un Multibranch et un webhook. Y écrire un nouveau pipeline relancerait les jobs de la partie 1 à chaque commit. Le jeton `gitea-token` donne accès à tous les dépôts du compte `formation` : rien à reconfigurer.

---

### Étape 7 — Créer le dossier `devsecops`

**Dashboard → New Item** → `devsecops` → **Folder** → **OK** → **Description** `Pipeline DevSecOps construit pas a pas` → **Save**.

Tous les jobs de la série vont dans ce dossier.

> 💡 **Si la partie 1 n'a pas été jouée sur ce poste** — `../2-demos-jenkins-projets-cluster-admin/scripts/etat-partie1.sh` reconstruit l'essentiel (plugins, `linux-1`, outils, `agent-ssh-key`, `gitea-token`). Il s'arrête à l'étape Nexus tant que la licence de Nexus n'est pas acceptée, sans gêner cette série. La configuration SonarQube (démo 15 de la partie 1, étapes 1 à 7) reste à faire à la main.

---
---

## Démo 1 — Le squelette

| | |
|---|---|
| **Objectif** | Écrire le premier pipeline, sans rien taper de mémoire |
| **Durée** | 20 min |
| **Prérequis** | démo 0 |
| **Solution** | `solutions/01-squelette.Jenkinsfile` |
| **Générateurs** | Directive : `agent`, `stage` · Snippet : `git`, `sh` |

### Pourquoi

Un pipeline déclaratif a toujours la même ossature :

```
pipeline → agent → stages → stage → steps
```

Plutôt que de la recopier, on la fait générer. On travaille d'abord dans un job dont le script est saisi dans l'UI : on itère en quelques secondes, sans commit.

### Ce que vous allez obtenir

- la page **Pipeline Syntax** et ses deux générateurs ;
- un premier build vert, avec un stage **Checkout** dans la vue graphique.

---

### Étape 1 — Créer le job

1. Dossier `devsecops` → **New Item** → `library-api-devsecops` → **Pipeline** → **OK**.
2. **Save** tout de suite (script vide).

> ✅ **Résultat attendu** — Le menu du job contient maintenant **Pipeline Syntax**.

*Pourquoi ouvrir les générateurs depuis le job :* leurs listes (credentials, outils) contiennent alors aussi ce qui est défini dans le dossier du job. Depuis http://localhost:8080/pipeline-syntax/, on ne voit que le global.

---

### Étape 2 — Générer la directive `agent`

**Où :** menu du job → **Pipeline Syntax** → menu de gauche **Declarative Directive Generator**.

| Champ | Valeur |
|---|---|
| **Sample Directive** | `agent: Agent` |
| **Agent** | `label: Run on an agent matching a label` |
| **Label** | `devsecops` |

Cliquer **Generate Declarative Directive**.

**Code obtenu :**

```groovy
agent {
  label 'devsecops'
}
```

**Où le coller :** directement sous `pipeline {`.

La liste **Sample Directive** contient 13 directives : `agent`, `environment`, `input`, `matrix`, `options`, `parameters`, `post`, `libraries`, `stage`, `stages`, `tools`, `triggers`, `when`. Elles serviront toutes, sauf `matrix` et `libraries`.

**Les options du formulaire `agent`**

| Champ | Ce qu'il fait | Choix ici |
|---|---|---|
| **Agent** | `any` : n'importe quel agent disponible · `label` : un agent qui porte ce label · `none` : pas d'agent pour tout le pipeline, chaque stage déclare le sien | `label` |
| **Label** | une expression de labels : un nom (`devsecops`) ou une combinaison (`linux && docker`, `linux \|\| macos`) | `devsecops` |
| **Retry Count** | au-delà de 1, Jenkins relance le bloc sur un autre agent quand l'agent est perdu en cours de route (agent déconnecté, controller redémarré) ; ce n'est pas une relance en cas d'échec d'une commande | vide |

---

### Étape 3 — Générer un `stage`

**Où :** Declarative Directive Generator.

| Champ | Valeur |
|---|---|
| **Sample Directive** | `stage: Stage` |
| **Name** | `Checkout` |
| **This stage will contain...** | `Steps` |

Cliquer **Generate Declarative Directive**.

**Code obtenu :**

```groovy
stage('Checkout') {
  steps {
    // One or more steps need to be included within the steps block.
  }
}
```

**Où le coller :** dans un bloc `stages { }`.

Les autres choix de **This stage will contain...** : `Parallel Stages` (démo 10), `Sequential Stages`, `Matrix`. Le bouton **Add** du formulaire ajoute au stage ses propres directives : **Agent**, **Input**, **Environment**, **Options**, **When Condition**, **Tools**, **Post Stage or Build Conditions**.

**Les choix de *This stage will contain...***

| Choix | Le stage contient… | Exemple |
|---|---|---|
| `Steps` | un bloc `steps { }` : les actions du stage | presque tous les stages |
| `Parallel Stages` | des stages qui s'exécutent **en même temps** | démo 10 |
| `Sequential Stages` | des sous-stages exécutés **l'un après l'autre**, dans le même stage (pratique pour leur donner un agent ou une condition commune) | non utilisé |
| `Matrix` | le même contenu joué pour **chaque combinaison** de valeurs (par exemple JDK 17 et JDK 21) | non utilisé |

---

### Étape 4 — Générer le step `git`

**Où :** menu de gauche **Snippet Generator**.

| Champ | Valeur |
|---|---|
| **Sample Step** | `git: Git` |
| **Repository URL** | `http://gitea:3000/formation/library-api-devsecops.git` |
| **Branch** | `main` |
| **Credentials** | `formation/****** (Gitea - jeton lecture library-api)` |

Cliquer **Generate Pipeline Script**.

**Code obtenu :**

```groovy
git branch: 'main', credentialsId: 'gitea-token', url: 'http://gitea:3000/formation/library-api-devsecops.git'
```

**Où le coller :** dans `steps { }` du stage `Checkout`, à la place du commentaire.

> ⚠️ **Piège** — Le champ **Branch** vaut `master` par défaut. Le remplacer par `main`, sinon le clone échoue.

*Pourquoi le générateur :* l'ID `gitea-token` vient de la liste, impossible de se tromper d'une lettre. Les cases **Include in polling?** et **Include in changelog?**, laissées cochées, n'apparaissent pas : le générateur n'écrit que ce qui diffère des valeurs par défaut.

**Les options du formulaire `git`**

| Champ | Ce qu'il fait | Choix ici |
|---|---|---|
| **Repository URL** | l'adresse du dépôt ; jamais de mot de passe dans l'URL (il serait visible), on passe par **Credentials** | l'URL Gitea vue depuis les conteneurs |
| **Branch** | la branche à cloner (nom local, pas `origin/main`, ni tag, ni SHA) ; défaut `master` | `main` |
| **Credentials** | le secret d'accès : *Username with password* (ou jeton) en HTTPS, clé privée en SSH | `gitea-token` |
| **Include in polling?** | décoché : ce dépôt n'est plus surveillé par `pollSCM` (démo 3) ; défaut coché | coché |
| **Include in changelog?** | décoché : ses commits n'apparaissent plus dans la page **Changes** du build ; défaut coché | coché |

---

### Étape 5 — Générer le step `sh`

| Champ | Valeur |
|---|---|
| **Sample Step** | `sh: Shell Script` |
| **Shell Script** | `ls -la` |

**Code obtenu :** `sh 'ls -la'` — à coller sous le step `git`.

**Les options du formulaire `sh`**

| Champ (paramètre) | Ce qu'il fait | Choix ici |
|---|---|---|
| **Shell Script** (`script`) | la ou les commandes ; plusieurs lignes acceptées. Jenkins les lance avec `sh -xe` : chaque commande est affichée précédée de `+`, et **la première commande qui sort avec un code non nul arrête le script** et fait échouer le stage | `ls -la` |
| **Return standard output** (`returnStdout`) | la sortie de la commande est renvoyée comme valeur (à ranger dans une variable, dans un bloc `script`) au lieu d'être écrite dans la console | décoché |
| **Encoding of standard output** (`encoding`) | l'encodage de la sortie ; vide = celui de l'agent | vide |
| **Return exit status** (`returnStatus`) | le code retour est renvoyé comme valeur au lieu de faire échouer le step : à tester soi-même (`if (code != 0) ...`) | décoché |
| **Label** (`label`) | le nom affiché pour ce step dans la vue graphique, à la place de « Shell Script » | vide |

> ⚠️ **Piège** — Une faute dans la commande fait échouer tout le pipeline. Par exemple `sh 'ls la'` (sans le tiret) affiche `ls: cannot access 'la': No such file or directory`, puis `ERROR: script returned exit code 2` : les stages suivants sont sautés (`skipped due to earlier failure(s)`).

---

### Étape 6 — Assembler et lancer

Job → **Configure** → **Pipeline** → **Definition** `Pipeline script` → zone **Script**. Écrire `pipeline { }` et coller dedans les blocs générés :

```groovy
pipeline {
  agent {                                   // ← étape 2
    label 'devsecops'
  }
  stages {
    stage('Checkout') {                     // ← étape 3
      steps {
        git branch: 'main', credentialsId: 'gitea-token', url: 'http://gitea:3000/formation/library-api-devsecops.git'   // ← étape 4
        sh 'ls -la'                         // ← étape 5
      }
    }
  }
}
```

Laisser **Use Groovy Sandbox** coché. **Save** → **Build Now**.

> ✅ **Résultat attendu** — Build vert, un stage **Checkout** dans la vue graphique. Console : `Running on devsecops-1`, le clone, puis la liste des fichiers (`.git`, `Dockerfile`, `pom.xml`, `src`).

> 💡 **À retenir** — Directive = **structure** (sous `pipeline` ou sous `stage`). Step = **action** (dans `steps` ou dans `post`).

---
---

## Démo 2 — Build, tests et rapports

| | |
|---|---|
| **Objectif** | Compiler, tester, et faire lire les résultats par Jenkins |
| **Durée** | 20 min |
| **Prérequis** | démo 1 |
| **Solution** | `solutions/02-build-tests.Jenkinsfile` |
| **Générateurs** | Directive : `tools`, `post` · Snippet : `junit`, `recordCoverage`, `archiveArtifacts` |

### Pourquoi

Un build qui compile ne suffit pas. Jenkins doit :

- **lire les tests**, pour afficher les échecs et passer le build en **UNSTABLE** ;
- **lire la couverture**, pour la suivre dans le temps ;
- **garder le JAR** produit.

Chaque rapport a son step. Ces steps vont dans `post`, pour s'exécuter même quand Maven échoue.

### Ce que vous allez obtenir

- Maven installé automatiquement sur l'agent ;
- 14 tests publiés, une couverture avec seuil, le JAR archivé.

---

### Étape 1 — Générer `tools`

**Où :** Declarative Directive Generator.

| Champ | Valeur |
|---|---|
| **Sample Directive** | `tools: Tools` |
| **Add** → `jdk: JDK` → **Version** | `jdk21` |
| **Add** → `maven: Maven` → **Version** | `maven-3.9` |

**Code obtenu :**

```groovy
tools {
  jdk 'jdk21'
  maven 'maven-3.9'
}
```

**Où le coller :** sous `pipeline`, après `agent`.

*Pourquoi :* `tools` installe Maven 3.9.16 sur l'agent au premier build et met `JAVA_HOME` et `mvn` dans le `PATH` de tous les stages. Sans lui, `mvn: not found`.

**Les options du formulaire `tools`**

| Champ | Ce qu'il fait |
|---|---|
| **Add** | une ligne par type d'outil : `git: Git`, `jdk: JDK`, `maven: Maven` (et Node.js, Gradle… si leurs plugins sont installés) |
| **Version** | la liste des **noms** déclarés dans **Manage Jenkins → Tools** : `jdk21`, `maven-3.9`. Ce n'est pas un numéro de version : c'est le nom choisi à la démo 7 de la partie 1 |

---

### Étape 2 — Ajouter le stage de build

Générer un stage **Build & tests** (comme à la démo 1), avec le step :

```groovy
sh 'mvn -B -ntp clean verify'
```

**Où le coller :** dans `stages`, après `stage('Checkout')`.

---

### Étape 3 — Générer le bloc `post` du stage

**Où :** Declarative Directive Generator.

| Champ | Valeur |
|---|---|
| **Sample Directive** | `post: Post Stage or Build Conditions` |
| cases à cocher | **Always run, regardless of build status** · **Run if the build status is "Success" or hasnt been set yet** |

**Code obtenu :**

```groovy
post {
  always {
    // One or more steps need to be included within each condition's block.
  }
  success {
    // One or more steps need to be included within each condition's block.
  }
}
```

**Où le coller :** dans le stage **Build & tests**, après son bloc `steps`. Un `post` placé là ne concerne que ce stage.

**Les conditions du formulaire `post`**

| Case à cocher | Bloc généré | S'exécute quand… |
|---|---|---|
| Always run, regardless of build status | `always` | toujours |
| Run if the build status is "Success" or hasnt been set yet | `success` | le build est vert |
| Run if the build status is "Unstable" | `unstable` | le build est jaune (tests en échec, seuil manqué) |
| Run if the build status is "Failure" | `failure` | le build est rouge |
| Run when the build status is "Aborted" | `aborted` | le build a été interrompu (bouton stop, `timeout`) |
| Run if the build status is "Not Built" | `notBuilt` | le build n'a rien exécuté |
| Run if the current builds status is "Aborted", "Failure" or "Unstable" | `unsuccessful` | tout résultat autre que vert |
| Run if the previous build was not successful and the current builds status is "Success" | `fixed` | le build repasse au vert après un échec |
| Run if the current builds status is worse than the previous builds status | `regression` | le résultat se dégrade |
| Run if the current builds status is different than the previous builds status | `changed` | le résultat change, dans un sens ou dans l'autre |
| Always run after all other conditions, regardless of build status | `cleanup` | toujours, **en dernier** (nettoyage) |

Quel que soit l'ordre dans le fichier, Jenkins exécute les blocs dans cet ordre : `always`, `changed`, `fixed`, `regression`, `aborted`, `failure`, `success`, `unstable`, `unsuccessful`, puis `cleanup`.

---

### Étape 4 — Les tests : `junit`

**Où :** Snippet Generator.

| Champ | Valeur |
|---|---|
| **Sample Step** | `junit: Archive JUnit-formatted test results` |
| **Test report XMLs** | `target/surefire-reports/*.xml, target/failsafe-reports/*.xml` |

**Code obtenu :**

```groovy
junit 'target/surefire-reports/*.xml, target/failsafe-reports/*.xml'
```

**Où le coller :** dans `always { }`.

*Pourquoi deux dossiers :* Surefire = tests unitaires (`*Test`), Failsafe = tests d'intégration (`*IT`).

**Les options du formulaire `junit`**

| Champ | Ce qu'il fait | Choix ici |
|---|---|---|
| **Test report XMLs** | le ou les motifs des rapports, séparés par des virgules | Surefire + Failsafe |
| **Test output retention** | garder la sortie console des tests : `None`, `All tests`, `Failed tests only` (`stdioRetention`) | défaut |
| **keep all the properties** | conserver les propriétés écrites dans les rapports | décoché |
| **Health report amplification factor** | poids des tests en échec dans la « météo » du job : 1.0 par défaut, 0 pour ne pas en tenir compte | défaut |
| **Allow empty results** | ne pas échouer quand aucun rapport n'est trouvé ; pratique, mais masque un job mal configuré | décoché |
| **Skip publishing checks** | ne pas publier les résultats vers GitHub ou GitLab (Checks API) | décoché |
| **Skip marking build as unstable on test failure** | un test en échec ne rend plus le **build** UNSTABLE (le stage, si) | décoché |
| **Skip marking stage as unstable on test failure** | ni le stage ni le build ne deviennent UNSTABLE ; les échecs restent affichés | décoché |
| **Skip report files older than build start** | ignorer les rapports laissés par un build précédent dans le workspace | décoché |

---

### Étape 5 — La couverture : `recordCoverage`

**Où :** Snippet Generator.

| Champ | Valeur |
|---|---|
| **Sample Step** | `recordCoverage: Record code coverage results` |
| **Code Coverage Tools → Coverage Parser** | `JaCoCo Coverage Reports` |
| **Report File Pattern** | `target/site/jacoco/jacoco.xml` |
| **Add Quality Gate → Threshold** | `80` |
| **Metric** | `Line Coverage` |
| **Step or Build Result** | `Mark the step and the build as unstable` |

**Code obtenu :**

```groovy
recordCoverage qualityGates: [[integerThreshold: 80, metric: 'LINE', threshold: 80.0]], tools: [[pattern: 'target/site/jacoco/jacoco.xml']]
```

**Où le coller :** dans `always { }`. JaCoCo étant l'analyseur par défaut, il n'apparaît pas dans le code.

**Les options du formulaire `recordCoverage`**

| Champ | Ce qu'il fait | Choix ici |
|---|---|---|
| **Coverage Parser** | le format du rapport : JaCoCo, Cobertura, PIT, LCOV… (`parser`) | `JaCoCo Coverage Reports` (le défaut : il n'est pas écrit) |
| **Report File Pattern** | le fichier de rapport produit par le build | `target/site/jacoco/jacoco.xml` |
| **Add Quality Gate** | une règle « la couverture doit atteindre N » ; plusieurs règles possibles | une règle |
| **Threshold** | la valeur à atteindre (ici un pourcentage) | `80` |
| **Baseline** | sur quoi on mesure : `Whole project` (tout le projet), `Modified files` / `Modified code lines` (seulement ce que le commit a touché), et leurs variantes *difference to reference job* (« ne pas faire baisser ») | `Whole project` (défaut) |
| **Metric** | ce qu'on mesure : lignes, branches, méthodes, classes, instructions… | `Line Coverage` |
| **Aggregation** | `Overall` (valeur globale), `Maximum`, `Minimum` (valeur extrême d'un élément) | `Overall` (défaut) |
| **Step or Build Result** | la conséquence si le seuil n'est pas atteint (voir ci-dessous) | `Mark the step and the build as unstable` |

Les quatre conséquences possibles :

| Libellé | Valeur écrite | Effet si le seuil est manqué |
|---|---|---|
| Mark the step as unstable | `criticality: 'NOTE'` | seul le **stage** devient jaune ; le **build** reste vert |
| Mark the step and the build as unstable | *(rien : c'est le défaut du step)* | le stage **et** le build deviennent jaunes ; le pipeline continue |
| Fail the step but not the build | `criticality: 'ERROR'` | le stage devient rouge, le build garde son résultat |
| Fail the step and the build | `criticality: 'FAILURE'` | le stage et le build deviennent rouges |

> ⚠️ **Piège** — Le formulaire présélectionne **Mark the step as unstable** (`NOTE`) : sans changer ce choix, un seuil manqué ne se voit que sur le stage, le build reste vert. Le code généré écrit `integerThreshold: 80` **et** `threshold: 80.0` : c'est la même valeur, sous forme entière et décimale.

---

### Étape 6 — Le JAR : `archiveArtifacts`

**Où :** Snippet Generator.

| Champ | Valeur |
|---|---|
| **Sample Step** | `archiveArtifacts: Archive the artifacts` |
| **Files to archive** | `target/*.jar` |
| **Advanced → Fingerprint all archived artifacts** | coché |

**Code obtenu :**

```groovy
archiveArtifacts artifacts: 'target/*.jar', fingerprint: true, followSymlinks: false
```

**Où le coller :** dans `success { }` (on n'archive pas le JAR d'un build raté).

**Les options du formulaire `archiveArtifacts`**

| Champ (paramètre) | Ce qu'il fait | Choix ici |
|---|---|---|
| **Files to archive** (`artifacts`) | le ou les motifs des fichiers à garder, relatifs au workspace | `target/*.jar` |
| **Excludes** (`excludes`) | des motifs à exclure malgré **Files to archive** | vide |
| **Do not fail build if archiving returns nothing** (`allowEmptyArchive`) | si aucun fichier ne correspond, avertir au lieu de faire échouer le build | décoché |
| **Archive artifacts only if build is successful** (`onlyIfSuccessful`) | ne rien archiver si le build n'est pas vert ; même effet que de placer le step dans `success` | décoché (on est déjà dans `success`) |
| **Fingerprint all archived artifacts** (`fingerprint`) | calcule une empreinte de chaque fichier : Jenkins peut ensuite dire quel build a produit un JAR et quels jobs l'ont utilisé | coché |
| **Use default excludes** (`defaultExcludes`) | exclut d'office `.git`, `.svn`, `.DS_Store`… | coché |
| **Treat include and exclude patterns as case sensitive** (`caseSensitive`) | décoché : `*.JAR` trouverait aussi `x.jar` | coché |
| **Follow symbolic links** (`followSymlinks`) | décoché : les liens symboliques du workspace sont **ignorés** | décoché |

> ⚠️ **Pourquoi `followSymlinks: false` apparaît** — Le step suit les liens symboliques par défaut, mais le formulaire présente la case **décochée**. Le générateur écrit donc la différence : `followSymlinks: false`. Retirer ce paramètre n'est pas neutre : on revient au défaut du step, qui **suit** les liens. Ici, `target/` ne contient aucun lien, le résultat est le même ; sur un projet où un lien pointe hors du workspace, `false` évite d'archiver un fichier qu'on n'avait pas prévu.

---

### Étape 7 — Assembler et lancer

Le stage complet :

```groovy
stage('Build & tests') {
  steps {
    sh 'mvn -B -ntp clean verify'
  }
  post {
    always {
      junit 'target/surefire-reports/*.xml, target/failsafe-reports/*.xml'
      recordCoverage qualityGates: [[integerThreshold: 80, metric: 'LINE', threshold: 80.0]], tools: [[pattern: 'target/site/jacoco/jacoco.xml']]
    }
    success {
      archiveArtifacts artifacts: 'target/*.jar', fingerprint: true
    }
  }
}
```

Script complet : `solutions/02-build-tests.Jenkinsfile`. **Save** → **Build Now**.

> ✅ **Résultat attendu**
> - console : `Unpacking https://repo.maven.apache.org/.../apache-maven-3.9.16-bin.zip ... on devsecops-1` (premier build seulement), `Tests run: 12` puis `Tests run: 2`, `BUILD SUCCESS` ;
> - `[Coverage] - [Whole project - Line Coverage]: ≪Success≫ - (Actual value: 81.82%, Quality gate: 80.00)` ;
> - page du build : **Tests** (14), **Coverage Report**, **Build Artifacts** `library-api-1.4.0-SNAPSHOT.jar`.

*Que faire de l'info :* avec un seuil à `90`, la même ligne signalerait l'écart (81,82 % < 90) et le build passerait **UNSTABLE**, sans être arrêté. Le seuil se règle sur la couverture réelle, puis on le remonte.

> ⚠️ **Piège** — `ERROR: Failed to download ... from agent; will retry from controller` : Maven Central a coupé la connexion. Jenkins réessaie depuis le controller ; si cela échoue aussi, relancer le build.

---
---

## Démo 3 — Options, environnement, déclencheur

| | |
|---|---|
| **Objectif** | Régler le comportement du job sans toucher aux stages |
| **Durée** | 15 min |
| **Prérequis** | démo 2 |
| **Solution** | `solutions/03-options-environnement.Jenkinsfile` |
| **Générateurs** | Directive : `options`, `environment`, `triggers` |

### Pourquoi

Trois directives, trois rôles :

| Directive | Rôle |
|---|---|
| `options` | durée maximale, historique conservé, builds simultanés |
| `environment` | variables communes à tous les stages (ici, la version calculée) |
| `triggers` | quand lancer le build sans clic |

### Ce que vous allez obtenir

- une console horodatée, un build limité à 20 minutes, 20 builds conservés ;
- un JAR versionné `1.4.<numéro du build>` ;
- un build déclenché par un commit dans les 5 minutes.

---

### Étape 1 — Générer `options`

**Où :** Declarative Directive Generator → **Sample Directive** `options: Options` → bouton **Add** (22 options proposées).

| Option à ajouter (**Add**) | Réglage |
|---|---|
| `buildDiscarder: Discard old builds` | **cocher la case *Discard old builds*** qui apparaît → **Strategy** `Log Rotation` → **Max # of builds to keep** `20` |
| `disableConcurrentBuilds: Do not allow concurrent builds` | **cocher la case *Do not allow concurrent builds*** |
| `timeout: Enforce time limit` | **Timeout** `20` · **Unit** `MINUTES` |
| `timestamps: Timestamps` | rien |

Cliquer **Generate Declarative Directive**.

**Code obtenu :**

```groovy
options {
  buildDiscarder logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '', numToKeepStr: '20')
  disableConcurrentBuilds()
  timeout(20)
  timestamps
}
```

**Où le coller :** sous `pipeline`, avant `stages`.

> ⚠️ **Piège** — Après **Add**, `buildDiscarder` et `disableConcurrentBuilds` affichent une case à cocher du même nom. **Tant qu'elle n'est pas cochée, l'option n'est pas générée.** De même, **Unit** peut s'afficher sur `NANOSECONDS` : vérifier `MINUTES`.

La ligne `buildDiscarder` peut se simplifier en `buildDiscarder logRotator(numToKeepStr: '20')` (forme de la solution). `timestamps` et `timestamps()` sont équivalents.

**Les options du formulaire `options` utilisées ici**

| Option | Champ | Ce qu'il fait | Choix ici |
|---|---|---|---|
| `buildDiscarder` | **Strategy** | `Log Rotation` : supprimer les anciens builds selon une durée ou un nombre | `Log Rotation` |
| | **Days to keep builds** (`daysToKeepStr`) | âge maximum d'un build, en jours | vide = pas de limite |
| | **Max # of builds to keep** (`numToKeepStr`) | nombre maximum de builds conservés | `20` |
| | **Days to keep artifacts** (`artifactDaysToKeepStr`, bouton **Advanced**) | âge maximum des **artefacts** ; le build reste, ses fichiers archivés sont supprimés | vide |
| | **Max # of builds to keep with artifacts** (`artifactNumToKeepStr`) | nombre de builds qui gardent leurs artefacts | vide |
| | **Remove last build** | `Yes` : autoriser la suppression du dernier build réussi ou stable (par défaut, Jenkins le garde toujours) | défaut |
| `disableConcurrentBuilds` | **Do not allow concurrent builds** | un seul build du job à la fois ; les suivants attendent dans la file | coché |
| | **Abort previous builds** (`abortPrevious`) | au lieu d'attendre, le nouveau build **interrompt** celui qui tourne (utile pour ne pas tester un commit déjà dépassé) | décoché |
| `timeout` | **Timeout** / **Unit** | durée maximale ; au-delà, le build est interrompu (**ABORTED**) | `20` / `MINUTES` |
| | **Timeout after inactivity** (`activity`) | la limite porte sur la durée **sans nouvelle ligne de console**, pas sur la durée totale | décoché |
| `timestamps` | — | affiche l'heure devant chaque ligne de la console | — |

Les chaînes vides générées (`artifactDaysToKeepStr: ''`…) signifient « pas de limite » : on peut les retirer sans rien changer, d'où la forme courte `buildDiscarder logRotator(numToKeepStr: '20')`. Les 22 options de la liste sont décrites dans `../1-demos-jenkins-ci/PIPELINE-SYNTAX.md`.

---

### Étape 2 — Générer `environment`

**Où :** Declarative Directive Generator.

| Champ | Valeur |
|---|---|
| **Sample Directive** | `environment: Environment` |
| **Add** → **Name** | `APP_VERSION` |
| **Value** | `1.4.${BUILD_NUMBER}` |

**Code obtenu :**

```groovy
environment {
  APP_VERSION = "1.4.${BUILD_NUMBER}"
}
```

**Où le coller :** sous `pipeline`.

> ⚠️ **Pièges du formulaire**
> - Chaque clic sur **Add** ajoute une ligne. Une ligne laissée vide produit ` = ""`, qui fait échouer le pipeline : la supprimer avec **Delete**.
> - La valeur est **toujours** mise entre guillemets. `credentials('sonar-token')` deviendrait la chaîne `"credentials('sonar-token')"` : retirer les guillemets à la main.

**Les champs du formulaire `environment`**

| Champ | Ce qu'il fait |
|---|---|
| **Name** | le nom de la variable ; elle sera lisible par `$NOM` dans un `sh` et par `env.NOM` en Groovy |
| **Value** | sa valeur, écrite entre guillemets doubles : Groovy y remplace `${...}` (ici `${BUILD_NUMBER}`) au moment où la variable est définie |

---

### Étape 3 — Utiliser la variable

Dans le stage **Build & tests**, remplacer la commande par :

```groovy
sh 'mvn -B -ntp -Drevision=$APP_VERSION clean verify'
```

*Pourquoi des apostrophes :* `$APP_VERSION` est alors lu par le shell de l'agent. Avec des guillemets doubles, Groovy remplacerait la valeur avant d'exécuter le shell : même résultat ici, mais pour un secret, ce serait une fuite dans le script.

---

### Étape 4 — Générer `triggers`

**Où :** Declarative Directive Generator.

| Champ | Valeur |
|---|---|
| **Sample Directive** | `triggers: Triggers` |
| **Add** → `pollSCM: Poll SCM` → **Schedule** | `H/5 * * * *` |

Sous le champ, Jenkins valide l'expression en direct : `Would last have run at ...; would next run at ...`.

**Code obtenu :**

```groovy
triggers {
  pollSCM 'H/5 * * * *'
}
```

**Où le coller :** sous `pipeline`.

Autres déclencheurs proposés : `cron: Build periodically`, `githubPush: GitHub hook trigger for GITScm polling`, `upstream: Build after other projects are built`.

**Les options du formulaire `triggers`**

| Champ | Ce qu'il fait | Choix ici |
|---|---|---|
| **Schedule** | une expression cron à 5 champs : `MINUTE HEURE JOUR MOIS JOUR_SEMAINE`. `H` remplace un nombre fixe par une valeur dérivée du nom du job : les jobs ne démarrent pas tous à la même minute. `H/5` = toutes les 5 minutes, avec un décalage propre au job | `H/5 * * * *` |
| **Ignore post-commit hooks** | ne pas réagir aux notifications envoyées par le serveur Git (webhook), seulement au calendrier | décoché |

| Déclencheur | Lance le build… |
|---|---|
| `pollSCM: Poll SCM` | au calendrier, **seulement s'il y a un nouveau commit** |
| `cron: Build periodically` | au calendrier, **toujours** (même sans commit) |
| `githubPush: GitHub hook trigger for GITScm polling` | quand un webhook prévient Jenkins d'un push |
| `upstream: Build after other projects are built` | à la fin d'un autre job |

---

### Étape 5 — Lancer

Où se placent les trois directives :

```groovy
pipeline {
  agent { ... }
  tools { ... }
  options { ... }          // ← étape 1
  environment { ... }      // ← étape 2
  triggers { ... }         // ← étape 4
  stages { ... }
}
```

**Save** → **Build Now**.

> ✅ **Résultat attendu** — Chaque ligne de la console est horodatée ; le JAR s'appelle `library-api-1.4.<numéro du build>.jar`. Un commit dans Gitea déclenchera un build dans les 5 minutes.

> 💡 **À retenir** — Les options, triggers et paramètres d'un Jenkinsfile ne sont appliqués au job **qu'après un build**. Le menu du job (**Build with Parameters**, page **Configure**) ne les reflète qu'à partir de là.

---
---

## Démo 4 — Paramètres

| | |
|---|---|
| **Objectif** | Laisser choisir, au lancement, la version, le seuil de vulnérabilité et l'analyse SonarQube |
| **Durée** | 15 min |
| **Prérequis** | démo 3 |
| **Solution** | `solutions/04-parametres.Jenkinsfile` |
| **Générateurs** | Directive : `parameters` |

### Pourquoi

Les démos suivantes ont besoin de choix faits au lancement :

| Paramètre | Sert à | Démo |
|---|---|---|
| `VERSION_BASE` | la version majeure.mineure | maintenant |
| `SEUIL_BLOQUANT` | les sévérités qui bloquent le pipeline | 7 et 11 |
| `ANALYSE_SONAR` | lancer ou sauter SonarQube | 9 |

Les déclarer dans le Jenkinsfile les rend versionnés et identiques pour tout le monde.

### Ce que vous allez obtenir

- le bouton **Build with Parameters** ;
- le piège du premier build, constaté.

---

### Étape 1 — Générer `parameters`

**Où :** Declarative Directive Generator → **Sample Directive** `parameters: Parameters` → **Add** (types : `booleanParam`, `choice`, `credentials`, `file`, `password`, `run`, `string`, `text`).

| Type ajouté | Name | Valeur par défaut | Description |
|---|---|---|---|
| `string: String Parameter` | `VERSION_BASE` | **Default Value** `1.4` | `Version majeure.mineure ; le numero de build complete la version` |
| `choice: Choice Parameter` | `SEUIL_BLOQUANT` | **Choices**, une valeur par ligne : `CRITICAL` puis `HIGH,CRITICAL` | `Severites de vulnerabilite qui bloquent le pipeline` |
| `booleanParam: Boolean Parameter` | `ANALYSE_SONAR` | cocher **Set by Default** | `Lancer l analyse SonarQube` |

**Code obtenu :**

```groovy
parameters {
  string defaultValue: '1.4', description: 'Version majeure.mineure ; le numero de build complete la version', name: 'VERSION_BASE'
  choice choices: ['CRITICAL', 'HIGH,CRITICAL'], description: 'Severites de vulnerabilite qui bloquent le pipeline', name: 'SEUIL_BLOQUANT'
  booleanParam defaultValue: true, description: 'Lancer l analyse SonarQube', name: 'ANALYSE_SONAR'
}
```

**Où le coller :** sous `pipeline`.

La solution écrit les mêmes lignes avec des parenthèses (`string(name: ..., ...)`) : les deux formes sont équivalentes. Le premier choix d'une liste `choice` est sa valeur par défaut.

**Les types et les champs du formulaire `parameters`**

| Type | Saisie au lancement | Exemple d'usage |
|---|---|---|
| `string` | une ligne de texte | une version, un nom d'image |
| `text` | un texte sur plusieurs lignes | des notes de version |
| `booleanParam` | une case à cocher | activer ou sauter un stage |
| `choice` | une liste ; la première valeur est le défaut | un environnement, un seuil |
| `password` | un texte masqué | à éviter : préférer `credentials` |
| `credentials` | un credential Jenkins choisi dans une liste | le compte de déploiement |
| `file` | un fichier envoyé | un fichier de configuration |
| `run` | un build d'un autre job | promouvoir un build précis |

| Champ | Ce qu'il fait |
|---|---|
| **Name** | le nom lu par `params.NOM` |
| **Default Value** / **Set by Default** / **Choices** | la valeur utilisée quand personne ne la saisit : premier build, build déclenché par un commit ou par un autre job |
| **Description** | le texte affiché sous le champ dans **Build with Parameters** |
| **Trim the string** (`string`) | retire les espaces au début et à la fin de la saisie |

---

### Étape 2 — Utiliser le paramètre

Dans `environment`, remplacer la ligne par :

```groovy
APP_VERSION = "${params.VERSION_BASE}.${BUILD_NUMBER}"
```

---

### Étape 3 — Ajouter un stage `Contexte`

Générer un stage **Contexte**, placé **avant** **Build & tests**, avec ces deux steps :

```groovy
echo "Version : ${env.APP_VERSION} - seuil bloquant : ${params.SEUIL_BLOQUANT} - SonarQube : ${params.ANALYSE_SONAR}"
sh 'echo "Variable shell : VERSION_BASE=$VERSION_BASE"'
```

---

### Étape 4 — Premier build

**Save** → **Build Now** (le bouton n'a pas encore changé).

> ✅ **Résultat attendu**
> ```
> Version : 1.4.3 - seuil bloquant : CRITICAL - SonarQube : true
> + echo Variable shell : VERSION_BASE=
> ```
> Au premier build, `params.VERSION_BASE` vaut déjà `1.4`, mais la **variable shell** `VERSION_BASE` est **vide** : le job ne connaissait pas encore ce paramètre au lancement.

---

### Étape 5 — Build avec paramètres

Le bouton est devenu **Build with Parameters**. Lancer avec :

| Paramètre | Valeur |
|---|---|
| `VERSION_BASE` | `2.0` |
| `SEUIL_BLOQUANT` | `HIGH,CRITICAL` |
| `ANALYSE_SONAR` | décoché |

> ✅ **Résultat attendu**
> ```
> Version : 2.0.4 - seuil bloquant : HIGH,CRITICAL - SonarQube : false
> + echo Variable shell : VERSION_BASE=2.0
> ```

> 💡 **À retenir** — Lire un paramètre par **`params.NOM`** (Groovy), jamais par `$NOM` ou `env.NOM` : c'est la seule forme fiable dès le premier build. Pour le passer au shell, passer par `environment { }`, comme `APP_VERSION`.

---
---

## Démo 5 — Le Jenkinsfile dans le dépôt

| | |
|---|---|
| **Objectif** | Versionner le pipeline à côté du code |
| **Durée** | 15 min |
| **Prérequis** | démo 4 |
| **Solution** | `solutions/05-jenkinsfile-scm.Jenkinsfile` |
| **Générateurs** | — |

### Pourquoi

Tant que le script est dans le job, il n'est ni versionné, ni relu, ni partagé entre branches. On le déplace dans le dépôt. Jenkins lit alors le Jenkinsfile du commit qu'il construit, et **clone le dépôt tout seul** : le stage **Checkout** devient inutile.

### Ce que vous allez obtenir

- un fichier `Jenkinsfile` dans Gitea ;
- le stage automatique **Declarative: Checkout SCM** ;
- la façon de travailler des démos suivantes.

---

### Étape 1 — Préparer le script

Partir du script de la démo 4 et :

- **supprimer** le stage **Checkout** (le dépôt sera cloné automatiquement) ;
- **supprimer** la ligne `sh 'echo "Variable shell : ..."'`, qui a servi à la démonstration.

Résultat : le contenu de `solutions/05-jenkinsfile-scm.Jenkinsfile`.

---

### Étape 2 — Créer le fichier dans Gitea

Gitea → dépôt `formation/library-api-devsecops` → **Add File** ▾ → **New File** :

| Champ | Valeur |
|---|---|
| nom du fichier | `Jenkinsfile` |
| contenu | le script de l'étape 1 |

Cliquer **Commit Changes** (commit direct sur `main`).

---

### Étape 3 — Faire lire le fichier par le job

Job → **Configure** → **Pipeline** → **Definition** : **Pipeline script from SCM**

| Champ | Valeur |
|---|---|
| **SCM** | `Git` |
| **Repository URL** | `http://gitea:3000/formation/library-api-devsecops.git` |
| **Credentials** | `formation/****** (Gitea - jeton lecture library-api)` |
| **Branch Specifier** | `*/main` |
| **Script Path** | `Jenkinsfile` |
| **Lightweight checkout** | coché |

**Deux champs à comprendre**

| Champ | Ce qu'il fait |
|---|---|
| **Branch Specifier** | la branche dont Jenkins lit le Jenkinsfile et qu'il construit ; `*/main` = la branche `main`, quel que soit le nom du dépôt distant |
| **Lightweight checkout** | pour **lire** le Jenkinsfile, Jenkins ne récupère que ce fichier, sans cloner tout le dépôt. Le clone complet a lieu ensuite, dans le stage **Declarative: Checkout SCM** |

**Save** → **Build with Parameters** → **Build**.

> ✅ **Résultat attendu** — La console commence par `Obtained Jenkinsfile from git http://gitea:3000/formation/library-api-devsecops.git`. La vue graphique montre un stage **Declarative: Checkout SCM** avant **Contexte**.

---

### Désormais : la boucle de travail

```
1. Pipeline Syntax (menu du job)  →  générer le bloc, le copier
2. Gitea → Jenkinsfile → crayon « Edit File »  →  coller au bon endroit
3. Commit Changes
4. Jenkins → Build with Parameters   (ou attendre le pollSCM, 5 min au plus)
```

Pour **essayer sans commit** : menu d'un build → **Replay**. On modifie le script d'un build déjà fait et on le relance.

*Pourquoi garder les générateurs :* le menu **Pipeline Syntax** reste disponible sur le job, même quand le script vient du dépôt.

---
---

## Démo 6 — Secrets : Gitleaks

| | |
|---|---|
| **Objectif** | Bloquer tout commit qui contient un secret, et apprendre la bonne correction |
| **Durée** | 25 min |
| **Prérequis** | démo 5 |
| **Solution** | `solutions/06-secrets.Jenkinsfile` |
| **Générateurs** | Snippet : `recordIssues` |

### Pourquoi

Un mot de passe ou un jeton poussé dans Git est **compromis**, même supprimé au commit suivant : il reste dans l'historique, que tout développeur clone. Gitleaks parcourt **tout l'historique**. C'est le premier stage du pipeline : inutile de compiler un commit qui contient un secret.

### Ce que vous allez obtenir

- un stage qui lance un outil avec `sh` ;
- son rapport publié dans Jenkins par `recordIssues` ;
- la détection d'un faux jeton, puis la seule bonne correction : **révoquer, puis ignorer l'empreinte**.

---

### Étape 1 — Ajouter le stage

Générer un stage **Secrets (Gitleaks)**, placé **avant** **Build & tests**, avec le step :

```groovy
sh 'gitleaks git --no-banner --no-color --redact --verbose --report-format sarif --report-path gitleaks.sarif'
```

| Option | Rôle |
|---|---|
| `git` | analyse les commits, pas seulement les fichiers présents |
| `--redact` | le secret n'est jamais affiché en clair dans la console |
| `--report-format sarif` | format standard des rapports d'analyse, lu par le plugin Warnings |

---

### Étape 2 — Publier le rapport : `recordIssues`

**Où :** Snippet Generator.

| Champ | Valeur |
|---|---|
| **Sample Step** | `recordIssues: Record compiler warnings and static analysis results` |
| **Static Analysis Tools → Tool** | `SARIF` (139 outils proposés) |
| **Report File Pattern** | `gitleaks.sarif` |
| **Custom ID** | `gitleaks` |
| **Custom Name** | `Gitleaks` |
| **Advanced** (du step) → **Enable recording for failed builds** | coché |

**Code obtenu :**

```groovy
recordIssues enabledForFailure: true, sourceCodeRetention: 'LAST_BUILD', tools: [sarif(id: 'gitleaks', name: 'Gitleaks', pattern: 'gitleaks.sarif')]
```

Pour Gitleaks, changer **Source Code Retention Strategy** en **Never store source code** : le code devient `sourceCodeRetention: 'NEVER'` (voir les options ci-dessous).

**Les options du formulaire `recordIssues`**

Bloc de l'outil (**Static Analysis Tools**) :

| Champ | Ce qu'il fait | Choix ici |
|---|---|---|
| **Tool** | l'analyseur qui lit le rapport (139 formats : SARIF, Aquasec Trivy, HadoLint, Checkstyle…) | `SARIF` |
| **Report File Pattern** | le fichier produit par l'outil | `gitleaks.sarif` |
| **Skip symbolic links when searching for files** | ne pas suivre les liens pendant la recherche des rapports | décoché |
| **Encoding of Report Files** | l'encodage des rapports (UTF-8…) ; vide = celui du système | vide |
| **Configure the context lines** | nombre de lignes autour d'un constat utilisées pour le reconnaître d'un build à l'autre (défaut 3) | défaut |
| **Custom ID** | l'identifiant de l'onglet dans l'URL du build (`.../gitleaks/`) ; obligatoire dès que deux `recordIssues` utilisent le même outil (ici : SARIF pour Gitleaks **et** Semgrep) | `gitleaks` |
| **Custom Name** | le nom affiché de l'onglet | `Gitleaks` |
| **Custom Icon** | l'icône de l'onglet | vide |

Bouton **Advanced** du step (les plus utiles) :

| Champ (paramètre) | Ce qu'il fait | Choix ici |
|---|---|---|
| **Enable recording for failed builds** (`enabledForFailure`) | publier aussi quand le build est en **FAILURE** | **coché** |
| **Aggregate results of all tools into a single result** (`aggregatingResults`) | un seul onglet pour tous les outils au lieu d'un par outil | décoché |
| **Do not write logging messages to the console log** (`quiet`) | console plus courte ; les messages restent dans l'onglet | décoché |
| **Disable retrieval of blame information** (`skipBlames`) | ne pas chercher l'auteur de chaque ligne en cause (le plugin *git-forensics*, non installé ici, le ferait) | décoché |
| **Source Code Retention Strategy** (`sourceCodeRetention`) | copier ou non dans Jenkins les fichiers source concernés, pour les afficher (voir ci-dessous) | `Store source code of the last build only` |
| **Fail the build if errors have been reported during the execution** (`failOnError`) | échouer si le plugin lui-même a eu un problème (rapport introuvable…) | décoché |
| **Stop the build if a quality gate is missed** (`stopBuild`) | arrêter le pipeline quand une quality gate est en échec | décoché |
| **Trend Chart Type and Position** (`trendChartType`) | position du graphique de tendance sur la page du job | défaut |
| **Quality gates** | des seuils sur le nombre de constats (démo 11) | aucun |
| **Healthy Threshold** / **Unhealthy Threshold** | nombre de constats pour une météo à 100 % ou à 0 % | vide |

Les quatre valeurs de **Source Code Retention Strategy** :

| Libellé | Valeur écrite | Effet |
|---|---|---|
| Never store source code | `sourceCodeRetention: 'NEVER'` | aucune copie : on voit le constat, pas le fichier |
| Store source code of the last build only | `sourceCodeRetention: 'LAST_BUILD'` | copie conservée pour le dernier build seulement |
| Store source code of every build | *(rien : c'est le défaut du step)* | copie conservée pour **chaque** build |
| Store source code of modified files only | `sourceCodeRetention: 'MODIFIED'` | copie des seuls fichiers modifiés |

> ⚠️ **Piège** — Le formulaire présélectionne **last build only**, alors que le défaut du step est **every build**. Retirer `sourceCodeRetention: 'LAST_BUILD'` n'est donc pas neutre : chaque build garderait une copie des fichiers en cause. Pour Gitleaks, choisir **Never store source code** (`'NEVER'`) : Jenkins ne garde alors aucune copie du fichier qui contient le secret (c'est ce que fait la solution).

**Où le coller :** dans un `post { always { } }` du stage **Secrets** (générer le `post` comme à la démo 2) :

```groovy
stage('Secrets (Gitleaks)') {
  steps {
    sh 'gitleaks git ...'
  }
  post {
    always {
      recordIssues enabledForFailure: true, sourceCodeRetention: 'NEVER', tools: [sarif(id: 'gitleaks', name: 'Gitleaks', pattern: 'gitleaks.sarif')]
    }
  }
}
```

> ⚠️ **Piège** — Sans **Enable recording for failed builds**, `recordIssues` ne publie **rien** sur un build en échec (`[analysis] Skipping execution of recorder since overall result is 'FAILURE'`). Or Gitleaks met le build en échec quand il trouve un secret : on saurait qu'il y en a un, sans pouvoir le voir.

---

### Étape 3 — Premier passage

Commit du Jenkinsfile, build.

> ✅ **Résultat attendu** — `no leaks found` ; onglet **Gitleaks** sur le build (0 issue).

---

### Étape 4 — Pousser un secret

Gitea → **Add File** → **New File** → `src/main/resources/application-notif.yml` (faux jeton, fourni dans `solutions/fichiers/application-notif.yml`) :

```yaml
notification:
  github:
    # jeton du compte de service qui commente les PR
    token: ghp_huG8GP38g4o5MNJAYKJ1UXXFWXLCpaNfhs0g
```

**Commit Changes**, puis build.

> ✅ **Résultat attendu** — **FAILURE**. Console :
> ```
> Finding:     REDACTED
> Secret:      REDACTED
> RuleID:      github-pat
> File:        src/main/resources/application-notif.yml
> Line:        4
> Commit:      7ff3bab2...
> Fingerprint: 7ff3bab2...:src/main/resources/application-notif.yml:github-pat:4
> WRN leaks found: 1
> Stage "Build & tests" skipped due to earlier failure(s)
> ```
> Onglet **Gitleaks** : 1 issue, le fichier et la ligne. Les stages suivants ne s'exécutent pas.

> ⚠️ **Piège** — Le jeton est masqué dans la console. Avec `sourceCodeRetention: 'NEVER'` (étape 2), Jenkins ne garde aucune copie du fichier : l'onglet montre le constat, pas le jeton. Avec la présélection `LAST_BUILD`, le fichier serait copié dans le build, et le jeton y serait **lisible**.

---

### Étape 5 — La mauvaise correction : supprimer le fichier

Gitea → ouvrir `application-notif.yml` → icône corbeille → **Commit Changes**, puis build.

> ✅ **Résultat attendu** — Toujours **FAILURE**, même `Fingerprint`. Le jeton est dans un commit de l'historique : supprimer le fichier ne le rend pas secret à nouveau.

---

### Étape 6 — La bonne correction

1. **Révoquer** le jeton chez son émetteur (ici, il est faux : l'étape est symbolique). C'est la seule action qui supprime le risque.
2. **Déclarer l'empreinte comme traitée** : Gitea → **New File** → `.gitleaksignore` (modèle : `solutions/fichiers/gitleaksignore-exemple`) :

   ```
   # Jeton GitHub pousse par erreur le 5/11/2026, REVOQUE le meme jour (ticket SEC-142).
   # Il reste dans l historique Git : empreinte ignoree apres revocation.
   7ff3bab2f02aa0ec699dd17cee069f21b30bc71b:src/main/resources/application-notif.yml:github-pat:4
   ```

   Copier **sa propre empreinte** depuis la ligne `Fingerprint:` de la console : le commit diffère pour chacun.
3. **Commit Changes**, build.

> ✅ **Résultat attendu** — **SUCCESS**, `no leaks found`, puis le build Maven reprend.

> 🏭 **En production** — On réécrit parfois l'historique (`git filter-repo`), mais tous les clones existants gardent le secret : la révocation reste obligatoire. Le contrôle le plus efficace se fait **avant le push**, sur le poste du développeur (`gitleaks git --pre-commit` en hook) ; le pipeline est le filet de sécurité.

---
---

## Démo 7 — Dépendances vulnérables : Trivy

| | |
|---|---|
| **Objectif** | Trouver les dépendances vulnérables, bloquer selon un seuil, remédier |
| **Durée** | 25 min |
| **Prérequis** | démo 6 |
| **Solution** | `solutions/07-dependances.Jenkinsfile` |
| **Générateurs** | Snippet : `recordIssues` |

### Pourquoi

L'essentiel du code exécuté par une application Spring Boot vient de ses **dépendances**. Un scan de composition logicielle (SCA) compare leurs versions aux bases de vulnérabilités publiques. Le paramètre `SEUIL_BLOQUANT` (démo 4) décide de ce qui arrête le pipeline ; le reste reste visible sans bloquer.

### Ce que vous allez obtenir

- deux appels de Trivy : un rapport complet, un contrôle bloquant ;
- 67 vulnérabilités lues dans Jenkins ;
- la remédiation en deux temps : **mettre à jour**, puis **documenter l'exception**.

---

### Étape 1 — Ajouter le stage

Générer un stage **Dependances (Trivy)**, placé **après** **Build & tests**, avec deux steps :

```groovy
sh 'trivy fs --scanners vuln --offline-scan --no-progress --format json --output trivy-fs.json pom.xml'
sh "trivy fs --scanners vuln --offline-scan --no-progress --severity ${params.SEUIL_BLOQUANT} --exit-code 1 pom.xml"
```

| Appel | Rôle |
|---|---|
| premier | rapport JSON complet (toutes sévérités), pour Jenkins |
| second | tableau des seules sévérités du seuil ; code retour 1 s'il en trouve → le stage échoue |

| Option | Rôle |
|---|---|
| `--offline-scan` | lit les dépendances dans le cache Maven (`~/.m2`, rempli par **Build & tests**) au lieu d'interroger Maven Central — d'où la place du stage, **après** le build |
| `--exit-code 1` | fait échouer la commande si une vulnérabilité du seuil est trouvée |

*Pourquoi des guillemets doubles sur le second :* `${params.SEUIL_BLOQUANT}` est remplacé par Groovy avant l'exécution. Ce n'est pas un secret : on peut l'interpoler sans risque.

---

### Étape 2 — Publier le rapport

**Où :** Snippet Generator.

| Champ | Valeur |
|---|---|
| **Sample Step** | `recordIssues` |
| **Tool** | `Aquasec Trivy` |
| **Report File Pattern** | `trivy-fs.json` |
| **Custom ID** | `trivy-fs` |
| **Custom Name** | `Trivy - dependances` |
| **Advanced → Enable recording for failed builds** | coché |

**Code obtenu :**

```groovy
recordIssues enabledForFailure: true, sourceCodeRetention: 'LAST_BUILD', tools: [trivy(id: 'trivy-fs', name: 'Trivy - dependances', pattern: 'trivy-fs.json')]
```

Les champs sont ceux décrits à la démo 6. Seuls changent **Tool** (`Aquasec Trivy`) et le nom du rapport. **Source Code Retention Strategy** garde sa présélection, `Store source code of the last build only` (`sourceCodeRetention: 'LAST_BUILD'`, à conserver dans le code).

**Où le coller :** dans un `post { always { } }` du stage.

> ⚠️ **Piège** — Les champs **Custom ID** et **Custom Name** existent deux fois : dans le bloc de l'outil et dans **Advanced**. Ne remplir que ceux de l'outil ; sinon le générateur les répète au niveau du step.

---

### Étape 3 — Lancer

Commit, build. Le premier passage télécharge la base de vulnérabilités (`Downloading vulnerability DB... 132 MiB`), gardée ensuite en cache sur l'agent.

> ✅ **Résultat attendu** (scan du 5 novembre 2026 ; les chiffres évoluent chaque jour) — **FAILURE** au stage **Dependances (Trivy)** :
> ```
> pom.xml (pom)
> Total: 10 (CRITICAL: 10)
> │ org.apache.commons:commons-text │ CVE-2022-42889 │ CRITICAL │ fixed │ 1.9 │ 1.10.0 │ apache-commons-text: variable interpolation RCE │
> │ org.apache.tomcat.embed:tomcat-embed-core │ CVE-2026-... │ CRITICAL │ ...
> │ org.springframework:spring-webmvc │ CVE-2026-47884 │ CRITICAL │ ... │ 7.0.9 │ ...
> ```
> Onglet **Trivy - dependances** : **67** vulnérabilités, triables par paquet ou par CVE.

Correspondance des sévérités dans Jenkins :

| Trivy | Jenkins (Warnings) |
|---|---|
| CRITICAL | **Error** |
| HIGH | **High** |
| MEDIUM | **Normal** |
| LOW | **Low** |

---

### Étape 4 — Remédier : mettre à jour ce qui dépend du projet

Gitea → `pom.xml` → **Edit File**, appliquer les changements de `solutions/fichiers/pom-corrige.xml` :

| Changement | Pourquoi |
|---|---|
| parent Spring Boot `3.5.6` → `3.5.16` | dernière 3.5.x |
| `commons-text` `1.9` → `1.15.0` | corrige Text4Shell |
| `<tomcat.version>10.1.59</tomcat.version>` (dans `<properties>`) | correctif pas encore intégré à la 3.5.16 |
| `<jackson-bom.version>2.21.7</jackson-bom.version>` (dans `<properties>`) | idem |

**Commit Changes**, build.

> ✅ **Résultat attendu** — Encore **FAILURE**, mais `Total: 2 (CRITICAL: 2)` : deux CVE de `spring-webmvc`, corrigées seulement en 7.0.9, c'est-à-dire Spring Boot 4. Jenkins n'affiche plus que **4** vulnérabilités au total.

---

### Étape 5 — Remédier : documenter l'exception

Une migration vers Spring Boot 4 ne se fait pas dans la journée. Après analyse (l'application n'utilise ni `XsltView` ni les Server-Sent Events), l'équipe accepte le risque **pour une durée limitée**.

Gitea → **New File** → `.trivyignore` (modèle : `solutions/fichiers/.trivyignore`) :

```
# spring-webmvc 6.2.x : corrige seulement en 7.0.9 (Spring Boot 4). L'application n'utilise
# ni XsltView ni Server-Sent Events. Migration Spring Boot 4 planifiee (ticket ARCH-77).
CVE-2026-47884 exp:2027-03-31
CVE-2026-47890 exp:2027-03-31
```

`exp:` : à cette date, l'exception tombe d'elle-même et le pipeline bloque à nouveau.

**Commit Changes**, build.

> ✅ **Résultat attendu** — **SUCCESS**, `Some vulnerabilities have been ignored/suppressed`, tableau à `0`. L'onglet Trivy montre encore les vulnérabilités MEDIUM : visibles, sans bloquer.

---

### Étape 6 — Essayer le seuil

**Build with Parameters** → `SEUIL_BLOQUANT` = `HIGH,CRITICAL`. Le contrôle bloquant porte alors aussi sur les HIGH.

> 💡 **Si la base a changé** — De nouvelles CVE apparaissent chaque jour : les numéros et versions ci-dessus ne seront pas exactement les vôtres. La démarche ne change pas : mettre à jour ce qui peut l'être (`Fixed Version` de la console), documenter le reste dans `.trivyignore` avec une justification et une date.

---
---

## Démo 8 — SAST : Semgrep

| | |
|---|---|
| **Objectif** | Analyser le code source, signaler sans bloquer |
| **Durée** | 15 min |
| **Prérequis** | démo 7 |
| **Solution** | `solutions/08-sast.Jenkinsfile` |
| **Générateurs** | Snippet : `catchError` |

### Pourquoi

L'analyse statique de sécurité (SAST) lit le code à la recherche de constructions dangereuses : injection SQL, chiffrement faible, désérialisation… Ses constats sont souvent **à interpréter** (faux positifs, contexte). On veut qu'ils **signalent**, pas qu'ils bloquent comme un secret. Le step `catchError` transforme l'échec de l'outil en build **UNSTABLE**.

### Ce que vous allez obtenir

- un build jaune (UNSTABLE) au lieu de rouge ;
- l'usage de MD5 trouvé, puis corrigé.

---

### Étape 1 — Générer `catchError`

**Où :** Snippet Generator.

| Champ | Valeur |
|---|---|
| **Sample Step** | `catchError: Catch error and set build result to failure` |
| **Build result on error** | `UNSTABLE` |
| **Stage result on error** | `UNSTABLE` |

**Code obtenu :**

```groovy
catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
    // some block
}
```

C'est un **step à bloc** : on remplace `// some block` par le step qui peut échouer.

**Les options du formulaire `catchError`**

| Champ | Ce qu'il fait | Choix ici |
|---|---|---|
| **Message** | un message écrit dans la console quand une erreur est attrapée (affiché aussi sur le stage) | vide |
| **Build result on error** | le résultat donné au **build** : `SUCCESS`, `UNSTABLE`, `FAILURE`, `NOT_BUILT`, `ABORTED`. Un résultat ne peut que se dégrader : on ne repasse pas un build UNSTABLE en SUCCESS | `UNSTABLE` |
| **Stage result on error** | le résultat donné au **stage** (couleur dans la vue graphique) | `UNSTABLE` |
| **Catch Pipeline interruptions** | attraper aussi les interruptions (bouton stop, `timeout`) ; décoché, elles arrêtent le pipeline comme d'habitude | décoché |

Deux steps voisins : `warnError` (équivalent de `catchError` avec UNSTABLE partout) et `unstable` (démo 13 : passe le stage en UNSTABLE avec un message, sans erreur à attraper).

---

### Étape 2 — Ajouter le stage

Générer un stage **SAST (Semgrep)**, placé **après** **Dependances (Trivy)**. Dans son bloc `steps`, coller le `catchError`, avec à l'intérieur :

```groovy
sh 'semgrep scan --config p/java --metrics=off --error --sarif --output semgrep.sarif --exclude target .'
```

| Option | Rôle |
|---|---|
| `--config p/java` | jeu de règles public pour Java, téléchargé du registre Semgrep (60 règles) |
| `--error` | code retour 1 s'il y a un constat |
| `--metrics=off` | aucune donnée d'usage envoyée |

---

### Étape 3 — Publier le rapport

Dans un `post { always { } }` du stage : `recordIssues` (Snippet Generator) avec

| Champ | Valeur |
|---|---|
| **Tool** | `SARIF` |
| **Report File Pattern** | `semgrep.sarif` |
| **Custom ID** | `semgrep` |
| **Custom Name** | `Semgrep` |
| **Advanced → Enable recording for failed builds** | coché |

Le stage complet :

```groovy
stage('SAST (Semgrep)') {
  steps {
    catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
      sh 'semgrep scan --config p/java --metrics=off --error --sarif --output semgrep.sarif --exclude target .'
    }
  }
  post {
    always {
      recordIssues enabledForFailure: true, sourceCodeRetention: 'LAST_BUILD', tools: [sarif(id: 'semgrep', name: 'Semgrep', pattern: 'semgrep.sarif')]
    }
  }
}
```

---

### Étape 4 — Lancer

Commit, build.

> ✅ **Résultat attendu** — **UNSTABLE** (jaune) ; stage **SAST (Semgrep)** jaune, les autres verts.
> ```
> Findings: 1 (1 blocking)
> Ran 60 rules on 10 files: 1 finding.
> ERROR: script returned exit code 1
> Setting overall build result to UNSTABLE
> ```
> Onglet **Semgrep** : `java.lang.security.audit.crypto.use-of-md5.use-of-md5` sur `Checksums.java`, ligne 17 — *Detected MD5 hash algorithm which is considered insecure*.

---

### Étape 5 — Corriger

Gitea → `src/main/java/fr/utopios/library/Checksums.java` → **Edit File** :

- `MessageDigest.getInstance("MD5")` devient `MessageDigest.getInstance("SHA-256")` ;
- retirer le commentaire au-dessus.

Modèle : `solutions/fichiers/Checksums-corrige.java`. Commit, build.

> ✅ **Résultat attendu** — **SUCCESS**, `Findings: 0 (0 blocking)`. Les tests `ChecksumsTest` passent toujours : l'empreinte change de valeur, pas de comportement.

> 💡 **À retenir** — `catchError` ne s'applique qu'à ce qu'il englobe. Sans lui, la même commande donnerait **FAILURE** et arrêterait le pipeline, comme Gitleaks. Pour chaque outil, choisir : **bloquer** (secret, vulnérabilité critique) ou **signaler** (SAST, style).

---
---

## Démo 9 — Qualité : SonarQube et Quality Gate

| | |
|---|---|
| **Objectif** | Faire juger la qualité par SonarQube et arrêter le pipeline si la Quality Gate est rouge |
| **Durée** | 20 min |
| **Prérequis** | démo 8 |
| **Solution** | `solutions/09-qualite.Jenkinsfile` |
| **Générateurs** | Directive : `when` · Snippet : `withSonarQubeEnv`, `waitForQualityGate`, `timeout` |

### Pourquoi

SonarQube juge maintenabilité, fiabilité, sécurité et couverture, et rend un verdict : la **Quality Gate**. Le calcul se fait **après** l'envoi des données, de façon asynchrone : Jenkins attend le verdict, que SonarQube lui renvoie par **webhook**. Le paramètre `ANALYSE_SONAR` permet de sauter ces deux stages.

### Ce que vous allez obtenir

- une analyse SonarQube et son verdict dans Jenkins ;
- une condition `when { expression }`, écrite à la main ;
- deux steps que le générateur ne sait pas remplir entièrement.

---

### Étape 1 — Démarrer SonarQube

Dans le kit de la partie 1 (2 Go de RAM, 1 à 2 minutes) :

```bash
docker compose -f ../1-demos-jenkins-ci/docker-compose.yml --profile qualite up -d sonarqube
```

```bash
until curl -s http://localhost:9000/api/system/status | grep -q '"status":"UP"'; do sleep 5; done; echo SonarQube pret
```

---

### Étape 2 — Rien à configurer, une vérification

Le serveur `sonarqube`, le credential `sonar-token` (jeton **Global Analysis Token**, valable pour tout projet) et le webhook `http://jenkins:8080/sonarqube-webhook/` viennent de la démo 15 de la partie 1, vérifiés à la démo 0.

Vérifier seulement, dans SonarQube (`admin` / `Formation-2026!`) → **Quality gates** : **Sonar way** porte la mention **Default**.

*Pourquoi une clé de projet à part :* le `pom.xml` de ce dépôt déclare `sonar.projectKey` = `fr.utopios:library-api-devsecops`. Avec la clé de la partie 1, l'analyse écraserait l'historique du projet SonarQube de la partie 1.

---

### Étape 3 — Générer `withSonarQubeEnv`

**Où :** Snippet Generator → **Sample Step** `withSonarQubeEnv: Prepare SonarQube Scanner environment` → **Generate Pipeline Script**.

**Code obtenu :**

```groovy
withSonarQubeEnv {
    // some block
}
```

> ⚠️ **Piège** — Le formulaire ne propose que **Server authentication token**, pas le nom du serveur. Écrire `withSonarQubeEnv('sonarqube')` pour rendre le choix explicite (**Steps Reference**, menu de gauche, documente ce paramètre `installationName`).

À l'intérieur du bloc :

```groovy
sh 'mvn -B -ntp sonar:sonar -Dsonar.projectName=library-api-devsecops'
```

---

### Étape 4 — Générer `timeout` et `waitForQualityGate`

**Où :** Snippet Generator.

| Sample Step | Réglage | Code obtenu |
|---|---|---|
| `timeout: Enforce time limit` | **Timeout** `5`, **Unit** `MINUTES` | `timeout(5) { ... }` |
| `waitForQualityGate: Wait for SonarQube analysis to be completed and return quality gate status` | rien à régler | `waitForQualityGate false` |

> ⚠️ **Piège** — `waitForQualityGate false` attend le verdict **sans jamais bloquer**. Écrire à la place, dans le bloc du `timeout` :
> ```groovy
> waitForQualityGate abortPipeline: true
> ```

**Les options des steps SonarQube et `timeout`**

| Step | Champ | Ce qu'il fait |
|---|---|---|
| `withSonarQubeEnv` | **Server authentication token** | un autre jeton que celui de **Manage Jenkins → System** ; vide = le jeton du serveur (`sonar-token`) |
| | `installationName` (pas dans le formulaire) | le nom du serveur déclaré dans **System** : `'sonarqube'` |
| `waitForQualityGate` | **Server authentication token** | idem |
| | `abortPipeline` (pas dans le formulaire) | `true` : gate rouge = pipeline en **FAILURE** ; `false` : on attend le verdict sans bloquer |
| `timeout` | **Timeout** / **Unit** | durée maximale du bloc ; au-delà, le build est interrompu (**ABORTED**) |
| | **Timeout after inactivity** | la limite porte sur l'absence de nouvelles lignes de console |

---

### Étape 5 — La condition, écrite à la main

Le formulaire `when` du Directive Generator propose `allOf`, `anyOf`, `branch`, `buildingTag`, `changeRequest`, `changelog`, `changeset`, `environment`, `isRestartedRun`, `not`, `tag`, `triggeredBy` — mais **pas** `expression`, qui contient du code Groovy.

À écrire sous le nom du stage, avant `steps` :

```groovy
when {
  expression { params.ANALYSE_SONAR }
}
```

---

### Étape 6 — Assembler les deux stages

Après **SAST (Semgrep)** :

```groovy
stage('Qualite (SonarQube)') {
  when { expression { params.ANALYSE_SONAR } }
  steps {
    withSonarQubeEnv('sonarqube') {
      sh 'mvn -B -ntp sonar:sonar -Dsonar.projectName=library-api-devsecops'
    }
  }
}
stage('Quality Gate') {
  when { expression { params.ANALYSE_SONAR } }
  steps {
    timeout(time: 5, unit: 'MINUTES') {
      waitForQualityGate abortPipeline: true
    }
  }
}
```

---

### Étape 7 — Lancer

Commit, build.

> ✅ **Résultat attendu**
> ```
> ANALYSIS SUCCESSFUL, you can find the results at: http://sonarqube:9000/dashboard?id=fr.utopios%3Alibrary-api-devsecops
> Checking status of SonarQube task '...' on server 'sonarqube'
> SonarQube task '...' status is 'PENDING'
> SonarQube task '...' completed. Quality gate is 'OK'
> ```
> La page du job affiche le cadre **SonarQube Quality Gate**. Dans SonarQube (http://localhost:9000 — remplacer `sonarqube:9000` dans le lien), le projet `library-api-devsecops` est **Passed**.

---

### Étape 8 — Sauter l'analyse

**Build with Parameters** → décocher `ANALYSE_SONAR` → **Build**.

> ✅ **Résultat attendu** — `Stage "Qualite (SonarQube)" skipped due to when conditional` et `Stage "Quality Gate" skipped due to when conditional` ; les deux stages sont grisés.

> 💡 **À retenir** — Le jeton SonarQube n'apparaît nulle part dans le Jenkinsfile : `withSonarQubeEnv` le lit dans **System** et l'injecte, masqué, dans l'environnement de Maven. Si `waitForQualityGate` ne se termine pas : vérifier le webhook (SonarQube → **Administration → Webhooks** → colonne **Last delivery**).

---
---

## Démo 10 — Analyses en parallèle

| | |
|---|---|
| **Objectif** | Lancer Trivy, Semgrep et SonarQube en même temps |
| **Durée** | 15 min |
| **Prérequis** | démo 9 |
| **Solution** | `solutions/10-parallele.Jenkinsfile` |
| **Générateurs** | Directive : `stage` (Parallel Stages) |

### Pourquoi

Les trois analyses ne dépendent pas les unes des autres : seul le build Maven doit être fini avant elles. Les lancer ensemble raccourcit le pipeline : c'est la différence entre un pipeline qu'on regarde et un pipeline qu'on oublie.

### Ce que vous allez obtenir

- un stage **Analyses** à trois branches ;
- un build d'environ 20 s au lieu de 30.

---

### Étape 1 — Générer le stage parallèle

**Où :** Declarative Directive Generator.

| Champ | Valeur |
|---|---|
| **Sample Directive** | `stage: Stage` |
| **Name** | `Analyses` |
| **This stage will contain...** | `Parallel Stages` |

**Code obtenu :**

```groovy
stage('Analyses') {
  parallel {
    // One or more stages need to be included within the parallel block.
  }
}
```

    **Options liées au parallélisme**

    | Où | Option | Ce qu'elle fait |
    |---|---|---|
    | dans le stage parallèle | `failFast true` | la première branche en échec interrompt les autres |
    | dans `options` du pipeline | `parallelsAlwaysFailFast()` | le même comportement pour **tous** les `parallel` du pipeline |

---

### Étape 2 — Déplacer les trois stages dedans

```groovy
stage('Analyses') {
  parallel {
    stage('Dependances (Trivy)') { ... }    // ← déplacé, avec son post
    stage('SAST (Semgrep)') { ... }         // ← déplacé, avec son post
    stage('Qualite (SonarQube)') { ... }    // ← déplacé, avec son when
  }
}
stage('Quality Gate') { ... }               // ← reste dehors : il attend le verdict
```

---

### Étape 3 — Lancer

Commit, build.

> ✅ **Résultat attendu** — La vue graphique affiche **Analyses** avec trois branches côte à côte. Durée relevée : environ **30 s** en séquence (démo 9), **19 à 20 s** en parallèle.

> 💡 **À retenir** — Par défaut, l'échec d'une branche **n'interrompt pas** les autres : on obtient tous les rapports d'un coup (démo 11). L'option `parallelsAlwaysFailFast()` (liste **options** : *Parallel stages always fail fast*) fait l'inverse. Les branches partagent ici le même agent et le même workspace : chaque outil écrit son propre rapport, sans conflit.

---
---

## Démo 11 — Dockerfile, image et SBOM

| | |
|---|---|
| **Objectif** | Contrôler le Dockerfile, construire l'image, la scanner, archiver son inventaire |
| **Durée** | 25 min |
| **Prérequis** | démo 10 |
| **Solution** | `solutions/11-image.Jenkinsfile` |
| **Générateurs** | Snippet : `recordIssues` (avec quality gate) |

### Pourquoi

- Le **Dockerfile** est du code, avec ses erreurs : Hadolint les trouve.
- L'**image** embarque un système d'exploitation, avec ses propres vulnérabilités : Trivy les scanne.
- Le **SBOM** (*Software Bill of Materials*) est l'inventaire des composants livrés : quand une CVE sort, il dit en une recherche si la version en production est touchée.

### Ce que vous allez obtenir

- Hadolint en quatrième branche parallèle ;
- une image `library-api-devsecops:1.4.<n>` sans vulnérabilité système ;
- un SBOM CycloneDX archivé avec le build.

---

### Étape 1 — Ajouter Hadolint

Dans le bloc `parallel`, ajouter un stage **Dockerfile (Hadolint)** :

```groovy
sh 'hadolint --format json --failure-threshold error Dockerfile > hadolint.json'
```

`--failure-threshold error` : seules les règles de niveau *error* font échouer la commande ; *warning* et *info* sont publiés sans bloquer.

---

### Étape 2 — Publier, avec une quality gate

**Où :** Snippet Generator.

| Champ | Valeur |
|---|---|
| **Sample Step** | `recordIssues` |
| **Tool** | `HadoLint` |
| **Report File Pattern** | `hadolint.json` |
| **Advanced → Enable recording for failed builds** | coché |
| **Add Quality Gate → Threshold** | `1` |
| **Type** | `Total (errors only)` |
| **Result** | `Mark the step and the build as unstable` |

**Code obtenu :**

```groovy
recordIssues enabledForFailure: true, qualityGates: [[integerThreshold: 1, threshold: 1.0, type: 'TOTAL_ERROR']], sourceCodeRetention: 'LAST_BUILD', tools: [hadoLint(pattern: 'hadolint.json')]
```

**Où le coller :** dans un `post { always { } }` du stage.

La liste **Type** permet aussi de viser les **New** (apparus depuis le build de référence) ou les **Delta** : utile pour « ne pas aggraver » un projet qui a déjà des alertes. La solution garde la forme simple, sans quality gate.

**Les options d'une quality gate `recordIssues`**

| Champ | Ce qu'il fait | Choix ici |
|---|---|---|
| **Threshold** | le nombre de constats à partir duquel la gate est manquée | `1` |
| **Type** | ce qu'on compte : `Total` (tous les constats), `New` (apparus depuis le build de référence), `Delta` (écart avec le build de référence), décliné par sévérité (`errors only`, `severity high only`…) ou `in modified code` | `Total (errors only)` |
| **Result** | la conséquence, mêmes quatre choix que pour la couverture (démo 2) : `NOTE` (stage seulement), `UNSTABLE` (stage et build, le défaut du step), `ERROR` (stage en échec), `FAILURE` (stage et build en échec) | `Mark the step and the build as unstable` |

> ⚠️ **Piège** — Ici aussi, **Result** présélectionne **Mark the step as unstable** (`criticality: 'NOTE'`) : le build resterait vert. Le code généré écrit le seuil deux fois (`integerThreshold: 1, threshold: 1.0`), c'est la même valeur.

---

### Étape 3 — Ajouter le stage Image

Après **Quality Gate**, un stage **Image** :

```groovy
stage('Image') {
  steps {
    sh 'docker build -t library-api-devsecops:$APP_VERSION .'
    sh "trivy image --scanners vuln --pkg-types os --ignore-unfixed --no-progress --severity ${params.SEUIL_BLOQUANT} --exit-code 1 library-api-devsecops:${env.APP_VERSION}"
    sh 'trivy fs --format cyclonedx --offline-scan --output sbom.cdx.json pom.xml'
    archiveArtifacts artifacts: 'sbom.cdx.json', fingerprint: true
  }
}
```

| Commande / option | Rôle |
|---|---|
| `docker build` | l'agent pilote le Docker du poste par sa socket ; image construite à partir du JAR de `target/` |
| `--pkg-types os` | seule la couche système est scannée (les dépendances Java l'ont été à la démo 7) |
| `--ignore-unfixed` | une vulnérabilité sans correctif publié ne bloque pas |
| `--format cyclonedx` | produit le SBOM au format standard CycloneDX |

---

### Étape 4 — Lancer avec le Dockerfile d'origine

Commit, build.

> ✅ **Résultat attendu** — **FAILURE**. Branche **Dockerfile (Hadolint)** en échec ; les trois autres branches vont au bout ; **Quality Gate** et **Image** sont sautés (`skipped due to earlier failure(s)`).

Onglet **HadoLint** :

| Sévérité | Ligne | Règle |
|---|:---:|---|
| High | 2 | Pin versions in apk add (DL3018) |
| Normal | 2 | Use the `--no-cache` switch (DL3019) |
| **Error** | 3 | Use COPY instead of ADD for files and folders (DL3020) |
| High | 5 | Use arguments JSON notation for CMD and ENTRYPOINT arguments (DL3025) |

---

### Étape 5 — Corriger le Dockerfile

Gitea → `Dockerfile` → **Edit File** → contenu de `solutions/fichiers/Dockerfile-corrige` :

```dockerfile
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
# Utilisateur dedie, avec un UID numerique : l'application ne tourne pas en root
RUN addgroup -S -g 10001 app && adduser -S -u 10001 -G app app
COPY target/library-api-*.jar app.jar
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD ["wget", "-qO-", "http://localhost:8080/actuator/health"]
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

*Pourquoi un UID numérique et un HEALTHCHECK en JSON :* avec `USER app` et `CMD wget ...`, Hadolint signale encore DL3066 (*Non-numeric user-id*) et DL3025. On corrige jusqu'à zéro, pas seulement jusqu'à « plus d'erreur ».

Commit, build.

> ✅ **Résultat attendu** — **SUCCESS**. Stage **Image** :
> ```
> #9 naming to docker.io/library/library-api-devsecops:1.4.17 done
> INFO Detected OS family="alpine" version="3.24.3"
> │ library-api-devsecops:1.4.17 (alpine 3.24.3) │ alpine │ 0 │
> ```
> **Build Artifacts** : `library-api-1.4.17.jar` et `sbom.cdx.json`. L'image est visible sur le poste : `docker image ls library-api-devsecops`.

---
---

## Démo 12 — Multibranch et conditions

| | |
|---|---|
| **Objectif** | Un seul Jenkinsfile pour toutes les branches, qui adapte son comportement |
| **Durée** | 25 min |
| **Prérequis** | démo 11 |
| **Solution** | `solutions/12-multibranch-conditions.Jenkinsfile` |
| **Générateurs** | Directive : `when` (anyOf, branch, changeset), `post` |

### Pourquoi

Toutes les branches passent les contrôles de sécurité, mais **seule `main` produit une image**. Un job **Multibranch** crée un sous-job par branche et fournit `BRANCH_NAME` : les conditions `branch` et `changeset` deviennent utilisables.

### Ce que vous allez obtenir

- des conditions composées, générées ;
- un `post` au niveau du pipeline ;
- une branche de fonctionnalité qui saute Hadolint et Image.

---

### Étape 1 — Générer une condition composée

**Où :** Declarative Directive Generator.

| Champ | Valeur |
|---|---|
| **Sample Directive** | `when: When Condition` |
| **When Condition** | `anyOf: Execute the stage if any of the nested conditions are true` |
| dans le bloc imbriqué : **Add** → `branch` → **Branch pattern** | `main` |
| **Add** → `changeset` → **File/path pattern to match against changeset** | `Dockerfile` |

**Code obtenu :**

```groovy
when {
  anyOf {
    branch 'main'
    changeset 'Dockerfile'
  }
}
```

**Où le coller :** dans le stage **Dockerfile (Hadolint)**, avant `steps`. Hadolint ne tourne que sur `main`, ou quand le commit modifie le Dockerfile.

---

### Étape 2 — Réserver l'image à `main`

Générer de même `when { branch 'main' }` (**When Condition** : `branch`) et le coller dans le stage **Image**.

Les cases **Evaluate Before Options**, **Evaluate Before Input**, **Evaluate Before Agent** règlent le moment où la condition est évaluée (démo 13).

**Les conditions du formulaire `when`**

| Condition | Le stage s'exécute si… |
|---|---|
| `branch` | la branche construite correspond au motif (`main`, `release/*`) — Multibranch seulement |
| `changeset` | un fichier modifié par le commit correspond au motif (`Dockerfile`, `src/**`) |
| `changelog` | un message de commit correspond à une expression régulière |
| `changeRequest` | le build porte sur une pull request (sources GitHub, GitLab, Gitea) |
| `buildingTag` | le build porte sur un tag |
| `tag` | le build porte sur un tag qui correspond au motif (`v*`) |
| `environment` | une variable d'environnement a une valeur donnée |
| `triggeredBy` | le build a été lancé par une cause donnée (utilisateur, timer, autre job) |
| `isRestartedRun` | le build a été relancé depuis un stage (**Restart from Stage**) |
| `allOf` / `anyOf` / `not` | toutes / au moins une / aucune des conditions imbriquées |
| `expression` *(absente du formulaire, démo 9)* | le code Groovy entre accolades renvoie vrai |

| Case | Effet |
|---|---|
| **Evaluate Before Agent** (`beforeAgent true`) | la condition est évaluée **avant** de réserver l'agent du stage : un stage sauté ne mobilise pas d'agent |
| **Evaluate Before Input** (`beforeInput true`) | évaluée **avant** l'approbation `input` (démo 13) |
| **Evaluate Before Options** (`beforeOptions true`) | évaluée **avant** les `options` du stage (un `timeout`, un verrou…) |
| **Case-sensitive path/file matching only for the GLOB comparator** (`changeset`) | respecter les majuscules dans le motif (`Dockerfile` ≠ `dockerfile`) |

---

### Étape 3 — Générer le `post` du pipeline

**Où :** Declarative Directive Generator → `post`. Cocher :

- **Always run, regardless of build status**
- **Run if the build status is "Unstable"**
- **Run if the build status is "Failure"**
- **Run if the previous build was not successful and the current builds status is "Success"**

**Code obtenu :**

```groovy
post {
  always { ... }
  unstable { ... }
  failure { ... }
  fixed { ... }
}
```

**Où le coller :** directement sous `pipeline`, **après `stages`** (pas dans un stage). Le remplir comme dans la solution : `currentBuild.description` dans `always` (dans un bloc `script`), des `echo` dans les autres. `fixed` ne s'exécute qu'au premier succès après un échec.

---

### Étape 4 — Désactiver l'ancien job

Commit du Jenkinsfile. Puis : `library-api-devsecops` → **Configure** → en haut de **General**, interrupteur **Enabled** sur **Disabled** → **Save**.

> ✅ **Résultat attendu** — La page du job affiche *This project is currently disabled* et un bouton **Enable**.

*Pourquoi :* sinon les deux jobs se déclenchent à chaque commit.

---

### Étape 5 — Créer le Multibranch

Dossier `devsecops` → **New Item** → `library-api` → **Multibranch Pipeline** → **OK** → **Branch Sources** → **Add source** → **Git** :

| Champ | Valeur |
|---|---|
| **Project Repository** | `http://gitea:3000/formation/library-api-devsecops.git` |
| **Credentials** | `formation/****** (Gitea - jeton lecture library-api)` |

**Save**.

> ✅ **Résultat attendu** — Le scan trouve `main` et le construit. Tous les stages s'exécutent ; description du build `v1.4.1 - main` (le numéro de build repart à 1 dans le nouveau job).

---

### Étape 6 — Une branche de fonctionnalité

1. Gitea → bouton de branche (**main** ▾) → **Filter branch** `feature/messages` → **Create branch feature/messages from 'main'**.
2. Jenkins → `devsecops » library-api` → **Scan Multibranch Pipeline Now**.

> ✅ **Résultat attendu** — `devsecops » library-api » feature/messages` #1 : **SUCCESS**, avec
> ```
> Stage "Dockerfile (Hadolint)" skipped due to when conditional
> Stage "Image" skipped due to when conditional
> ```
> Gitleaks, build, Trivy, Semgrep et SonarQube ont tourné : la branche est contrôlée comme `main`, mais ne produit pas d'image.

---

### Étape 7 — Modifier le Dockerfile sur la branche

Sur `feature/messages`, modifier le `Dockerfile` (par exemple `--interval=30s` → `--interval=20s`), **Commit Changes** sur cette branche, puis scan.

> ✅ **Résultat attendu** — Build #2 : Hadolint s'exécute (`+ hadolint --format json ...`), **Image** reste sautée.

> 💡 **À retenir**
> - `changeset` compare au build précédent **de la même branche**. Au premier build d'une branche, il n'y a pas de changeset : la condition est fausse.
> - `branch` n'a de sens qu'en Multibranch : dans un job Pipeline simple, `BRANCH_NAME` n'existe pas et `branch 'main'` est toujours faux.

---
---

## Démo 13 — Une pipeline qui en appelle une autre

| | |
|---|---|
| **Objectif** | Isoler le déploiement dans sa propre pipeline, et l'appeler depuis le pipeline principal |
| **Durée** | 30 min |
| **Prérequis** | démo 12 |
| **Solutions** | `solutions/13-ci-Jenkinsfile.deploy` (pipeline appelée) · `solutions/13-appel-deploiement.Jenkinsfile` (pipeline appelante) |
| **Générateurs** | Directive : `input`, `when` · Snippet : `build`, `unstable` |

### Pourquoi

Le déploiement n'a pas le rythme de l'intégration continue : on déploie une image **déjà construite et contrôlée**, parfois plusieurs fois, parfois à la main, dans plusieurs environnements. On l'isole donc dans **sa propre pipeline**, paramétrée :

```
devsecops » library-api » main                 devsecops/library-api-deploy
┌────────────────────────────────┐            ┌──────────────────────────────┐
│ ... Image                      │            │ Controles                    │
│ Deploiement recette ───────────┼── build ──►│ Validation production (input)│
│   lit result + URL_DEPLOYEE ◄──┼────────────┤ Deploiement → URL_DEPLOYEE   │
└────────────────────────────────┘            └──────────────────────────────┘
```

### Ce que vous allez obtenir

- une pipeline de déploiement, avec approbation pour la production ;
- un appel généré par le Snippet Generator, et ses deux pièges ;
- la lecture du résultat et d'une valeur produite par la pipeline appelée.

---

### Partie A — La pipeline appelée : `library-api-deploy`

#### Étape 1 — Lire la solution

`solutions/13-ci-Jenkinsfile.deploy` :

| Bloc | Rôle |
|---|---|
| `agent { label 'devsecops' }` + `disableConcurrentBuilds()` | deux déploiements ne se croisent jamais |
| paramètres `IMAGE` (string) et `ENVIRONNEMENT` (choice `recette` / `production`) | ce qu'on déploie, et où |
| stage **Controles** | refuse un `IMAGE` vide, vérifie que l'image existe (`docker image inspect`) |
| stage **Validation production** | approbation humaine, seulement pour la production |
| stage **Deploiement** | recrée le conteneur `library-api-devsecops-<environnement>` (port 8092 ou 8093), attend `/actuator/health`, puis `env.URL_DEPLOYEE = "http://localhost:8092"` |

---

#### Étape 2 — Générer la directive `input`

**Où :** Declarative Directive Generator.

| Champ | Valeur |
|---|---|
| **Sample Directive** | `input: Input` |
| **Message** | `Deployer en production ?` |
| **Advanced → OK Button Caption** | `Deployer` |
| **Advanced → Allowed Submitter** | `admin` |

**Code obtenu :**

```groovy
input {
  message 'Deployer en production ?'
  ok 'Deployer'
  submitter 'admin'
}
```

**Où le coller :** dans le stage **Validation production**, avant `steps` (directive de stage).

**Les options du formulaire `input`**

| Champ | Ce qu'il fait | Choix ici |
|---|---|---|
| **Message** | la question affichée | `Deployer en production ?` |
| **Custom ID** | l'identifiant de la question (utile pour y répondre par l'API) ; vide = calculé par Jenkins | vide |
| **OK Button Caption** | le texte du bouton qui valide (défaut `Proceed`) | `Deployer` |
| **Cancel Button Caption** | le texte du bouton qui refuse (défaut `Abort`) | vide |
| **Allowed Submitter** | les comptes ou groupes autorisés à valider, séparés par des virgules. Les administrateurs Jenkins peuvent toujours répondre, et toute personne qui a la permission *Job/Cancel* peut toujours cliquer **Abort** | `admin` |
| **Parameter to store the approving submitter** | le nom d'une variable qui recevra l'identifiant de la personne qui a validé | vide |
| **Parameters** | des champs à saisir au moment de valider (un numéro de ticket, un choix) | aucun |

Pendant l'attente, l'executor reste occupé : l'agent est déclaré pour tout le pipeline (`agent { label 'devsecops' }`). Quand un stage déclare **son propre** agent, la directive `input` est posée avant de réserver cet agent, ce qui évite de bloquer un executor pendant des heures.

---

#### Étape 3 — La condition du stage

**Où :** Declarative Directive Generator → `when` → cocher **Evaluate Before Input**, générer, puis écrire la condition à la main (pas d'`expression` dans la liste, démo 9) :

```groovy
when {
  beforeInput true
  expression { params.ENVIRONNEMENT == 'production' }
}
```

> ⚠️ **Piège** — Par défaut, Jenkins pose la question de l'`input` **avant** d'évaluer le `when`. Sans `beforeInput true`, la pipeline demande « Deployer en production ? » **même pour la recette** (vérifié : `Deployer en production ?` / `Proceed or Abort` sur un build `recette`).

---

#### Étape 4 — Créer le fichier et le job

1. Gitea → **New File** → `ci/Jenkinsfile.deploy` → contenu de la solution → **Commit Changes**.
2. Dossier `devsecops` → **New Item** → `library-api-deploy` → **Pipeline** → **OK** → **Pipeline script from SCM** :

| Champ | Valeur |
|---|---|
| **Repository URL** / **Credentials** | les mêmes qu'à la démo 5 |
| **Branch Specifier** | `*/main` |
| **Script Path** | `ci/Jenkinsfile.deploy` |

**Save** → **Build Now**.

> ✅ **Résultat attendu** — **FAILURE**, `ERROR: Parametre IMAGE obligatoire`. C'est **attendu et utile** : ce premier build enregistre les paramètres dans le job. Sans lui, le générateur de l'étape 7 ne pourrait pas les proposer.

---

#### Étape 5 — Déployer en recette, à la main

**Build with Parameters** :

| Paramètre | Valeur |
|---|---|
| **IMAGE** | `library-api-devsecops:1.4.17` (une image de la démo 11 : `docker image ls library-api-devsecops`) |
| **ENVIRONNEMENT** | `recette` |

> ✅ **Résultat attendu**
> ```
> Image trouvee : sha256:...
> Stage "Validation production" skipped due to when conditional
> {"status":"UP"}
> library-api-devsecops:1.4.17 deploye en recette : http://localhost:8092
> ```
> http://localhost:8092/actuator/health répond `{"status":"UP"}`.

---

#### Étape 6 — Déployer en production, avec approbation

Même chose avec **ENVIRONNEMENT** `production`. Le build s'arrête sur **Validation production**.

Menu du build → **Paused for Input** → page `Deployer en production ?`, boutons **Deployer** et **Abort** → **Deployer**.

> ✅ **Résultat attendu** — Console : `Approved by Administrateur Jenkins`, puis le déploiement sur le port 8093.

---

### Partie B — La pipeline appelante

#### Étape 7 — Générer l'appel : `build`

**Où :** job `devsecops » library-api » main` → **Pipeline Syntax** → **Snippet Generator**.

| Champ | Valeur |
|---|---|
| **Sample Step** | `build: Build a job` |
| **Project to Build** | `devsecops/library-api-deploy` |
| **Parameters → IMAGE** (apparaît quand le job est reconnu) | `library-api-devsecops:${env.APP_VERSION}` |
| **Parameters → ENVIRONNEMENT** | `recette` |
| **Wait for completion** | coché (défaut) |
| **Propagate errors** | **décoché** |

**Code obtenu :**

```groovy
build propagate: false, job: 'devsecops/library-api-deploy', parameters: [string(name: 'IMAGE', value: 'library-api-devsecops:${env.APP_VERSION}'), string(name: 'ENVIRONNEMENT', value: 'recette')]
```

> ⚠️ **Piège n° 1 — le chemin** — Écrire le chemin complet `devsecops/library-api-deploy`. Un nom relatif serait cherché à côté de la branche, **dans le Multibranch**, et ne serait pas trouvé.

> ⚠️ **Piège n° 2 — les apostrophes** — La valeur est générée entre **apostrophes**. Groovy ne remplace pas `${env.APP_VERSION}` dans une chaîne entre apostrophes : la pipeline appelée recevrait littéralement `library-api-devsecops:${env.APP_VERSION}`. Passer en **guillemets doubles** : `value: "library-api-devsecops:${env.APP_VERSION}"`.

**Les options du formulaire `build`**

| Champ | Ce qu'il fait | Choix ici |
|---|---|---|
| **Project to Build** | le job à lancer : un nom simple s'il est dans le même dossier, un chemin relatif (`../dossier/job`) ou absolu (`dossier/job`) sinon | `devsecops/library-api-deploy` |
| **Wait for completion** (`wait`) | attendre la fin du build appelé ; le step renvoie alors son résultat (`.result`, `.number`, `.buildVariables`…) | coché |
| **Wait until the build starts** (`waitForStart`) | attendre seulement son démarrage, puis continuer | décoché |
| **Propagate errors** (`propagate`) | coché : le résultat du build appelé devient celui du step (un échec fait échouer l'appelant) ; décoché : le step réussit toujours, on lit `.result` soi-même | **décoché** |
| **Quiet period** | délai, en secondes, avant le démarrage du build appelé | vide |
| **Parameters** | les paramètres du job appelé, affichés dès que le job est reconnu ; un paramètre non renseigné prend sa valeur par défaut | `IMAGE`, `ENVIRONNEMENT` |

Pour passer un secret à un job appelé, utiliser un paramètre de type `credentials`, jamais `password` ni une chaîne.

---

#### Étape 8 — Lire le résultat

`build` renvoie un objet qui décrit le build lancé : on le range dans une variable, ce qui impose un bloc `script`.

Générer aussi `unstable: Set stage result to unstable` → **Message** `Deploiement en recette en echec` → `unstable 'Deploiement en recette en echec'`.

Ajouter un paramètre `DEPLOYER_RECETTE` (booleanParam, coché par défaut), puis assembler le stage, **après Image** :

```groovy
stage('Deploiement recette') {
  when {
    allOf {
      branch 'main'
      expression { params.DEPLOYER_RECETTE }
    }
  }
  steps {
    script {
      def deploiement = build job: 'devsecops/library-api-deploy', parameters: [string(name: 'IMAGE', value: "library-api-devsecops:${env.APP_VERSION}"), string(name: 'ENVIRONNEMENT', value: 'recette')], propagate: false
      echo "library-api-deploy #${deploiement.number} : ${deploiement.result}"
      if (deploiement.result == 'SUCCESS') {
        echo "Recette : ${deploiement.buildVariables.URL_DEPLOYEE}"
      } else {
        unstable("Deploiement en recette en ${deploiement.result}")
      }
    }
  }
}
```

| Élément | Rôle |
|---|---|
| `propagate: false` | un échec du déploiement ne fait pas échouer l'appelant d'office : on lit `deploiement.result` et on décide (ici : **UNSTABLE**) |
| `deploiement.buildVariables.URL_DEPLOYEE` | les variables `env.` posées par la pipeline appelée sont lisibles par l'appelant |
| `allOf` | condition composée, mi-générée (`branch`), mi-écrite (`expression`) |

---

#### Étape 9 — Lancer

Commit du Jenkinsfile (solution `13-appel-deploiement.Jenkinsfile`), puis **Build with Parameters** sur `devsecops » library-api » main`.

> ✅ **Résultat attendu** — Console de l'appelant :
> ```
> Scheduling project: devsecops » library-api-deploy
> Starting building: devsecops » library-api-deploy #3
> Build devsecops » library-api-deploy #3 completed: SUCCESS
> library-api-deploy #3 : SUCCESS
> Recette : http://localhost:8092
> ```
> Console de `library-api-deploy` #3 : `Started by upstream project "devsecops/library-api/main" build number 2`. La ligne **Starting building** est un lien vers le build appelé.

---

#### Étape 10 — Vérifier le déploiement

- http://localhost:8092/actuator/health répond `{"status":"UP"}` ;
- `docker ps` montre `library-api-devsecops-recette` avec l'image `library-api-devsecops:1.4.<n>` du build.

> 💡 **À retenir** — Pendant l'appel, la pipeline principale **garde son executor** sur `devsecops-1` et attend ; la pipeline de déploiement prend le second (démo 0, étape 5). Avec un seul executor, les deux s'attendraient sans fin. Pour un appel « on lance et on continue », cocher **Wait until the build starts** ou décocher **Wait for completion** (`wait: false`).

---
---

## Démo 14 — Relecture du Jenkinsfile final

| | |
|---|---|
| **Objectif** | Relier chaque bloc du Jenkinsfile à l'outil qui l'a produit |
| **Durée** | 10 min |
| **Fichier** | `solutions/13-appel-deploiement.Jenkinsfile` |

### Qui a écrit quoi

| Bloc | Produit par | Écrit à la main | Démo |
|---|---|---|:---:|
| `agent { label 'devsecops' }` | Directive Generator | | 1 |
| `tools { jdk ...; maven ... }` | Directive Generator | | 2 |
| `options { ... }` | Directive Generator (case à cocher après **Add**) | simplification de `logRotator` | 3 |
| `parameters { ... }` | Directive Generator | | 4, 13 |
| `environment { APP_VERSION = ... }` | Directive Generator | `params.VERSION_BASE` | 3, 4 |
| `triggers { pollSCM ... }` | Directive Generator | | 3 |
| `stage(...) { steps { } }`, `stage(...) { parallel { } }` | Directive Generator | | 1, 10 |
| `post { always / success / unstable / failure / fixed }` | Directive Generator | contenu des blocs | 2, 12 |
| `when { anyOf { branch; changeset } }`, `when { branch 'main' }` | Directive Generator | | 12 |
| `when { expression { ... } }`, `beforeInput true` | | **entièrement** (absent du générateur) | 9, 13 |
| `input { ... }` | Directive Generator | | 13 |
| `git`, `sh`, `junit`, `archiveArtifacts`, `recordCoverage` | Snippet Generator | | 1, 2 |
| `recordIssues` (SARIF, Trivy, HadoLint) | Snippet Generator (**Advanced** → *Enable recording for failed builds*) | | 6 à 11 |
| `catchError`, `timeout`, `unstable` | Snippet Generator | | 8, 9, 13 |
| `withSonarQubeEnv('sonarqube')`, `waitForQualityGate abortPipeline: true` | Snippet Generator (incomplet) | nom du serveur, `abortPipeline` | 9 |
| `build job: ..., parameters: [...]` | Snippet Generator | guillemets doubles, `script`, lecture du résultat | 13 |
| commandes `gitleaks`, `trivy`, `semgrep`, `hadolint`, `docker` | | **entièrement** (commandes shell) | 6 à 11 |

### Ce qui bloque, et ce qui signale

| Stage | Bloque si… | Sinon |
|---|---|---|
| Secrets (Gitleaks) | un secret est trouvé dans l'historique → **FAILURE** | — |
| Build & tests | compilation → **FAILURE** ; test en échec → **UNSTABLE** | couverture < 80 % → **UNSTABLE** |
| Dependances (Trivy) | une vulnérabilité du seuil `SEUIL_BLOQUANT` → **FAILURE** | les autres sont publiées |
| SAST (Semgrep) | — | constat → **UNSTABLE** (`catchError`) |
| Dockerfile (Hadolint) | une règle *error* → **FAILURE** | *warning* / *info* publiés |
| Qualite + Quality Gate | gate rouge → **FAILURE** (`abortPipeline: true`) | sautés si `ANALYSE_SONAR` décoché |
| Image | vulnérabilité système corrigeable du seuil → **FAILURE** | SBOM archivé |
| Deploiement recette | — | échec du déploiement → **UNSTABLE** |

---
---

## Remise à zéro

Ces commandes ne touchent qu'à ce que ce kit a ajouté ; la stack et les jobs de la partie 1 restent en place.

| Besoin | Commande |
|---|---|
| Arrêter l'agent outillé en gardant ses caches | `docker compose down` |
| Supprimer les conteneurs déployés par la démo 13 | `docker rm -f library-api-devsecops-recette library-api-devsecops-production` |
| Supprimer les images construites par la démo 11 | `docker image ls library-api-devsecops --format '{{.Repository}}:{{.Tag}}' \| xargs docker rmi` |
| Supprimer l'agent et ses caches (Maven, base Trivy) | `docker compose down -v` |
| Rejouer la série depuis le début | Jenkins : supprimer le dossier `devsecops` et le node `devsecops-1` · Gitea : supprimer le dépôt `library-api-devsecops` · puis démo 0 |
