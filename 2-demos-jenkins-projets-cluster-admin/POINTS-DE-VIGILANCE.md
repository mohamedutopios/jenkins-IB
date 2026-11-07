# Points de vigilance — démos Jenkins partie 2

Complément de `DEMOS.md`. Ces points ont été relevés en déroulant les démos 0 à 17 sur un poste réel (Jenkins 2.580.2, Nexus 3.97.3, WildFly 42, Docker Desktop sur macOS arm64).

---

## Avant la session

### Le kit de la partie 1 est indispensable

`etat-partie1.sh` et `init-depots.sh` lisent `../1-demos-jenkins-ci/.env` et lancent la stack de la partie 1. Les deux kits doivent être côte à côte, avec ces noms de dossier.

### Contrat de licence Nexus

Un Nexus neuf refuse toute publication (HTTP 403) tant que le contrat de licence de la Community Edition n'est pas accepté. `etat-partie1.sh` ne l'accepte pas à la place de l'utilisateur : il s'arrête avec un message, sauf s'il est lancé avec `ACCEPTER_EULA_NEXUS=oui`. Accepter le contrat engage aussi sur la télémétrie obligatoire de la Community Edition (voir les points de vigilance de la partie 1).

### Télécharger à l'avance

Sur un poste neuf, plusieurs démos téléchargent pendant leur premier build :

| Démo | Téléchargement |
|---|---|
| 0 | plugins de la partie 1 et de la partie 2 ; image `maven:3.9-eclipse-temurin-21` (publication de `library-api` 1.4.0 et 1.4.1) |
| 1, 2, 3 | Maven 3.9.16 (outil) et dépendances Maven, dont l'API Jakarta EE (démo 3) |
| 4 | Ant 1.10.15 depuis archive.apache.org |
| 6 | Node.js 22.12.0 depuis nodejs.org ; image `nginx:1.27-alpine` |
| 8 | image `eclipse-temurin:21-jre-alpine` |
| 10 | dépendances Maven **à chaque build** (conteneur neuf, pas de cache) |

Passer une première fois les démos 0 à 10 la veille sur le poste de présentation. Les images de base se préchargent :

```bash
docker pull quay.io/wildfly/wildfly:42.0.0.Final-jdk21
```

```bash
docker pull eclipse-temurin:21-jre-alpine
```

```bash
docker pull nginx:1.27-alpine
```

### Ports utilisés

En plus de ceux de la partie 1 (8080, 50000, 3000, 8025, 8081) :

| Port | Service |
|---|---|
| 8180, 9990 | WildFly (application, console d'administration) |
| 9091 | Prometheus |
| 3001 | Grafana |
| 8092, 8093, 8094 | library-api dev, recette, prod (démo 8) |
| 8085 | Jenkins restauré (démo 15) |
| 17170 | LLDAP, interface d'administration de l'annuaire (démo 18) |

```bash
lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8180|9990|9091|3001|8092|8093|8094|8085|17170) '
```

Les ports 8092 à 8094 sont écrits dans `ci/deploy.Jenkinsfile` (dépôt `library-ops`), le port 8085 dans `scripts/restaurer.sh`.

### Versions figées

Les images sont figées dans `docker-compose.yml` (WildFly 42.0.0.Final, Prometheus v3.15.1, Grafana 13.3.0), sauf `jenkins/inbound-agent:jdk21` et `alpine/socat:latest`. La première suit les versions de l'agent Jenkins, compatibles avec le controller ; la seconde ne sert que de relais TCP.

Les versions d'outils proposées par défaut dans **Tools** sont les plus récentes (Ant 1.10.18, Node.js 26.x au moment des essais). Choisir celles de `DEMOS.md` (Ant **1.10.15**, **NodeJS 22.12.0**) pour que les sorties correspondent.

---

## Pendant la session

### Ordre des démos

Les démos dépendent les unes des autres :

| Démo | A besoin de |
|---|---|
| 3 (Jakarta EE) | 2 : la SNAPSHOT de `library-core` doit être dans Nexus |
| 5 (orchestrateur) | 2, 3 et 4 : `library-core/main`, `library-portal/main`, `library-legacy` |
| 10 (agents Docker) | image `formation/jenkins-agent-maven:jdk21` (démo 0, étape 5) |
| 11 (cluster) | 9 et 10 : `linux-2` et le cloud `docker-local` |
| 14 (supervision) | 9 : `linux-2` |
| 17 (CLI) | un jeton d'API (démo 14) |

### Ne pas relancer `init-depots.sh`

Le script fait un **push forcé** de `projets/` sur la branche `main` de chaque dépôt Gitea. Relancé en cours de session, il remplace l'historique de `main` et efface tout commit fait dans Gitea depuis (le tag `v2.3.0` de la démo 2 reste, mais pointe alors vers un commit qui n'est plus sur `main`). Les Multibranch voient un nouveau commit et reconstruisent `main`.

### Écarts entre les slides et la plate-forme

| Slide | Ce qu'elle dit | Ce que montre Jenkins 2.580.2 |
|---|---|---|
| 4 | La page du job affiche **Upstream Projects** / **Downstream Projects** | Vrai entre jobs Freestyle (démo 1). Un job Pipeline déclenché par **Build other projects** démarre bien mais n'apparaît pas dans ces sections |
| 40 | Regex `library-.*` pour la vue Library | Avec **Recurse in subfolders**, la regex porte sur le nom complet (`library/library-core`) : `library-.*` ne trouve que `library-dsl/...`. Utiliser `library/library-.*` |
| 48, 49 | Métrique `jenkins_queue_size_value` | Absente avec le plugin Prometheus metrics installé : utiliser `default_jenkins_executors_queue_length` ou `jenkins_queue_buildable_value` |
| 57 | `alias jcli='java -jar ~/jenkins-cli.jar -webSocket'` | Depuis le Mac vers le conteneur, le mode WebSocket (aussi mode par défaut) reste bloqué sans message. Utiliser `-http` |

### Choix à ne pas manquer dans l'interface

| Démo | Piège | Bon choix |
|---|---|---|
| 0 | Recherche `docker` dans les plugins : plusieurs résultats | **Docker** (Docker plugin), pas Docker Pipeline ni Docker Commons |
| 1 | Lancer `library-api-aval` à la main | Toujours par le build de `library-core-freestyle` (sinon `Unable to find a build for artifact copy`) |
| 2 | **Behaviours** du Multibranch | Ajouter **Discover tags**, sinon le tag `v2.3.0` n'est jamais vu |
| 2 | Attendre que le tag se construise seul | Il ne se construit pas (`No automatic build triggered for v2.3.0`) : **Build Now** sur l'onglet **Tags** |
| 8 | Premier build du job `deploy` | Échoue sur `CHANGE_REF obligatoire` : normal, les paramètres n'apparaissent qu'ensuite |
| 8 | Promotions concurrentes | Approuver d'abord la plus récente pour voir `Superseded by` sur l'autre |
| 9 | Secret de `linux-2` | Le recopier dans `.env` **avant** `docker compose --profile cluster up -d linux-2` |
| 10 | **Pull strategy** | **Never pull** : l'image n'existe que sur le poste |
| 10 | **Network** du template | `ci-formation`, sinon le conteneur ne joint pas Jenkins |
| 16 | Premier passage du seed | Échec `script not yet approved for use` : approuver dans **In-process Script Approval**, relancer |

### Labels et capacités des agents

`linux-2` (image `jenkins/inbound-agent`) porte le label `linux` mais n'a ni client Docker ni Maven préinstallé. Tout stage qui lance `docker` doit demander `linux && docker` (seul `linux-1` porte `docker`) ; c'est le cas dans `deploy.Jenkinsfile` et `multi-outils.Jenkinsfile`. Un nouveau Jenkinsfile écrit avec `label 'linux'` et une commande `docker` échouera une fois sur deux (`docker: not found`), selon l'agent choisi.

### Téléchargement concurrent de Maven

Quand deux builds installent l'outil `maven-3.9` en même temps sur un agent neuf, l'un des deux peut échouer pendant l'extraction (rencontré au premier build de `library-portal`). Relancer le build suffit.

### Le pipeline de promotion

- Pas de `disableConcurrentBuilds()` avec `milestone` : il empêcherait les deux promotions d'attendre ensemble l'approbation, et la démonstration de `Superseded by` deviendrait impossible.
- Au premier build, `params.VERSION` existe mais la variable d'environnement `VERSION` non : les blocs `sh` utilisent `APP_VERSION`, défini dans `environment { }`.
- `docker cp` vers un chemin dont le répertoire parent n'existe pas échoue : le JAR est copié en `/app.jar`, à la racine du conteneur.

### WildFly 42 et CDI

Une ressource JAX-RS qui injecte un EJB doit avoir une portée CDI (`@RequestScoped`) et le module web un `beans.xml`. Sans cela, l'application se déploie mais `/library/api/health` répond une erreur (`WELD-001303 No active contexts for RequestScoped` dans `docker logs wildfly`). Le kit est déjà corrigé.

---

## Sécurité : réglages propres à la formation

| Réglage | Pourquoi il est acceptable ici | En production |
|---|---|---|
| `docker-proxy` expose la socket Docker du poste en TCP sans authentification | Réseau Docker local, poste de formation | Hôte Docker dédié aux agents, API en TLS avec certificat client |
| `/prometheus/` lisible sans authentification | Prometheus local | Cocher **Enable authentication for prometheus end-point** ou filtrer par le réseau |
| Script Job DSL approuvé hors sandbox | Script relu, dépôt local | Seed en sandbox (`sandbox: true`) sous un utilisateur dédié, ou revue obligatoire du dépôt |
| Shared Library globale de confiance | Dépôt local | Dépôt protégé, revue obligatoire (elle s'exécute hors sandbox) |
| Secret de `linux-2` dans `.env` | Valeur de test | Fichier lisible par le seul compte de l'agent (`-secret @secret-file`) |
| Jetons d'API d'`admin` (CLI, supervision, sauvegarde) | Compte de formation | Un compte technique par usage, avec les seuls droits nécessaires |
| Annuaire en `ldap://` sans chiffrement, mots de passe des personnes dans `annuaire/utilisateurs/*.json` (démo 18) | Annuaire local de test | `ldaps://` ou StartTLS ; comptes gérés par le service informatique, jamais dans un dépôt |
| Secret du compte `jenkins-bind` écrit à la main dans `/run/secrets` (démo 18) | Conteneur de formation | Secret fourni par l'orchestrateur (secrets Docker ou Kubernetes) ou un coffre-fort |

### Démo 18 : comptes Jenkins indisponibles pendant la démo

Entre les étapes 9 et 19, le compte local `admin` et ses jetons d'API sont refusés : la CLI, le job de supervision et `sauvegarde.sh` (démos 14 à 17) ne fonctionnent plus. Faire la démo 18 en dernier, et ne pas oublier l'étape 19 avant de rendre la plate-forme.

---

## Distribuer le kit

`.env` contient la ligne `JENKINS_SECRET_LINUX2` remplie lors des essais. Ce secret ne vaut que pour le Jenkins qui l'a généré ; le vider avant de distribuer le kit :

```bash
sed -i.bak 's/^JENKINS_SECRET_LINUX2=.*/JENKINS_SECRET_LINUX2=/' .env && rm .env.bak
```

---

## Après la session

Arrêter et supprimer les conteneurs de la partie 2 (les volumes de la partie 1 restent) :

```bash
docker compose --profile cluster --profile monitoring --profile annuaire down
```

```bash
docker rm -f library-api-dev library-api-recette library-api-prod jenkins-restaure
```

`docker compose down` ne supprime pas les conteneurs lancés par les pipelines (démo 8) ni le Jenkins restauré (démo 15), d'où la seconde commande. Pour repartir de zéro, voir **Remise à zéro** à la fin de `DEMOS.md`.
