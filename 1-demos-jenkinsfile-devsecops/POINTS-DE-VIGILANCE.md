# Points de vigilance — démos Jenkinsfile DevSecOps

Complément de `DEMOS.md`. Ces points ont été relevés en déroulant les démos 0 à 14 sur un poste réel (Jenkins 2.580.2, Docker Desktop sur macOS arm64), le 5 novembre 2026, à partir d'un Jenkins dans l'état de fin de `../1-demos-jenkins-ci/DEMOS-v2.md`.

---

## Avant la session

### Le point de départ est la fin de la partie 1

Le kit ne contient ni Jenkins, ni Gitea, ni SonarQube : il s'ajoute à la stack de `../1-demos-jenkins-ci`, qui doit tourner, avec sa configuration de fin de DEMOS-v2 (démo 0, étape 2 : liste des vérifications et démo de la partie 1 qui crée chaque élément). Ne pas lancer `docker compose down -v` dans le dossier de la partie 1 entre les deux séries : cela effacerait Jenkins, Gitea et SonarQube.

### Ce qui pourrait entrer en collision avec la partie 1

| Élément | Partie 1 | Ce kit |
|---|---|---|
| Dépôt Gitea | `formation/library-api` (Multibranch + webhook) | `formation/library-api-devsecops` (aucun webhook) |
| Dossier Jenkins | `library` | `devsecops` |
| Agent | `linux-1`, label `linux` | `devsecops-1`, label `devsecops` |
| Projet SonarQube | `fr.utopios:library-api` | `fr.utopios:library-api-devsecops` |
| Conteneurs déployés | `library-api-recette` (8090), `library-api-prod` (8091) | `library-api-devsecops-recette` (8092), `library-api-devsecops-production` (8093) |
| Images | `library-api:*` | `library-api-devsecops:*` |

Écrire le nouveau pipeline dans le dépôt `library-api` de la partie 1 déclencherait son Multibranch et son pipeline complet (déploiement en recette, Nexus) à chaque commit.

### Ne pas relancer `init-depot` en cours de session

Le script pousse le projet par un **push forcé** : relancé après la démo 5, il efface le Jenkinsfile et tous les commits faits dans Gitea pendant les démos.

### Espace disque

Prévoir **6 Go libres** dans la VM Docker, en plus de la stack de la partie 1 :

| Élément | Taille |
|---|---|
| Image de l'agent (Trivy, Gitleaks, Hadolint, Semgrep) | 1,2 Go |
| Caches de l'agent (base Trivy, règles Semgrep) | 1,7 Go |
| Cache Maven de l'agent (deux versions de Spring Boot) | 0,4 Go |
| Images `library-api-devsecops:*` (une par build de `main`) | ~0,3 Go chacune, couches partagées |

Au-delà de 90 % de disque occupé, Elasticsearch (dans SonarQube) se bloque ; le `docker-compose.yml` neutralise ce seuil, mais les builds d'image échoueront faute de place.

```bash
docker system df
```

### Télécharger à l'avance

Le jour J, tout ce qui suit dépend d'Internet. Le faire passer une fois la veille sur le poste de présentation :

| Téléchargement | Quand | Volume |
|---|---|---|
| Construction de l'image de l'agent | démo 0 | ~1 Go (dont Semgrep via pip) |
| Maven 3.9.16 sur le nouvel agent, puis les dépendances (Spring Boot 3.5.6 puis 3.5.16) | démos 2 et 7 | ~0,4 Go |
| Base de vulnérabilités Trivy | démo 7 | 132 Mo, mise à jour toutes les 12 h |
| Règles Semgrep `p/java` | démo 8, à chaque build | quelques Ko (registre semgrep.dev) |

### Maven Central limite les accès répétés

Pendant les essais, Maven Central a répondu deux fois de façon anormale :
- `SSL peer shut down incorrectly` au téléchargement de Maven par l'outil `maven-3.9` : Jenkins a réessayé depuis le controller avec succès ; sinon, relancer le build ;
- `429 Too Many Requests ... Retry-After: 1800` quand Trivy résolvait lui-même les POM : c'est la raison de l'option `--offline-scan` (Trivy lit le cache Maven de l'agent, rempli par le stage **Build & tests**). Ne pas retirer cette option, et garder le stage Trivy **après** le build.

### Port 9000 sur macOS

Comme en partie 1 : si php-fpm occupe `127.0.0.1:9000`, SonarQube tourne avec `SONAR_PORT=9001` (`.env` de la partie 1) et s'ouvre sur `localhost:9001` ; l'adresse vue par Jenkins reste `http://sonarqube:9000`.

### Faux secret et dépôts hébergés

`DEMOS.md` (démo 6) et `solutions/fichiers/application-notif.yml` contiennent un faux jeton GitHub (`ghp_...`). Si le kit est poussé sur GitHub ou GitLab, leur détection de secrets peut bloquer le push ou ouvrir une alerte : c'est le comportement attendu, le jeton est inventé.

---

## Pendant la session

### Les résultats des scanners évoluent chaque jour

Les nombres cités dans `DEMOS.md` (67 vulnérabilités, 10 CRITICAL, puis 2 après correction) datent du 5 novembre 2026. La base Trivy change tous les jours, et les règles Semgrep évoluent aussi : les chiffres seront différents. La démarche reste la même (lire `Fixed Version`, mettre à jour, documenter l'exception), mais **rejouer les démos 7 et 8 la veille** pour connaître les chiffres du jour et, si besoin, adapter `pom-corrige.xml` et `.trivyignore`.

### Pièges des générateurs

| Générateur | Formulaire | Piège | Correction |
|---|---|---|---|
| Snippet | `git` | **Branch** vaut `master` par défaut | Saisir `main` |
| Directive | `options` | Après **Add**, `buildDiscarder` et `disableConcurrentBuilds` affichent une case du même nom, décochée : l'option n'est pas générée | Cocher la case |
| Directive | `options` → `timeout` | **Unit** peut afficher `NANOSECONDS` | Choisir `MINUTES` |
| Directive | `environment` | Une ligne vide produit ` = ""` (pipeline invalide) ; une valeur est toujours mise entre guillemets (`"credentials('x')"`) | Supprimer les lignes vides ; retirer les guillemets autour d'un appel |
| Directive | `when` | Pas de condition `expression` | L'écrire à la main |
| Snippet | `recordIssues` | Sans **Enable recording for failed builds**, rien n'est publié sur un build en FAILURE | Cocher l'option (bloc **Advanced**) |
| Snippet | `recordIssues` | **Source Code Retention Strategy** présélectionne *last build only*, mais le défaut du step est *every build* : retirer `sourceCodeRetention: 'LAST_BUILD'` du code fait garder une copie des sources à chaque build | Garder le paramètre ; `'NEVER'` pour Gitleaks |
| Snippet | `recordCoverage`, `recordIssues` (quality gate) | **Result** présélectionne *Mark the step as unstable* (`NOTE`) : un seuil manqué ne colore que le stage, le build reste vert | Choisir *Mark the step and the build as unstable* |
| Snippet | `archiveArtifacts` | La case **Follow symbolic links** est décochée dans le formulaire, alors que le step suit les liens par défaut : d'où `followSymlinks: false`, qui n'est pas neutre à retirer | Garder la ligne si le workspace peut contenir des liens |
| Snippet | `recordIssues` | Les champs **Custom ID** / **Custom Name** existent deux fois (outil et **Advanced**) | Ne remplir que ceux de l'outil |
| Snippet | `withSonarQubeEnv` | Pas de champ pour le nom du serveur | Écrire `withSonarQubeEnv('sonarqube')` |
| Snippet | `waitForQualityGate` | Génère `waitForQualityGate false` : n'arrête jamais le pipeline | Écrire `waitForQualityGate abortPipeline: true` |
| Snippet | `build` | Un nom relatif (`library-api-deploy`) appelé depuis une branche Multibranch est cherché à l'intérieur du Multibranch (`devsecops/library-api/...`) : le job n'est pas trouvé | Écrire le chemin complet `devsecops/library-api-deploy` |
| Snippet | `build` | Les valeurs de paramètres sont entre apostrophes : `'library-api:${env.APP_VERSION}'` n'est pas interpolé | Passer en guillemets doubles |
| Snippet | `build` | Le bloc **Parameters** ne liste les paramètres du job appelé qu'après un premier build de celui-ci | Lancer une fois `library-api-deploy` (échec attendu, démo 13 étape 5) |

### Pièges du Jenkinsfile

| Démo | Piège | Ce qu'il faut savoir |
|---|---|---|
| 4 | `$VERSION_BASE` vide au premier build | Lire `params.VERSION_BASE` ; passer au shell par `environment { }` |
| 6 | Supprimer le fichier qui contient le secret ne corrige rien | Gitleaks lit l'historique : révoquer le jeton, puis ignorer l'empreinte dans `.gitleaksignore` |
| 6 | Le secret détecté est masqué dans la console (`--redact`), mais Warnings NG copie par défaut le fichier source dans le build : le jeton y devient **lisible** | `sourceCodeRetention: 'NEVER'` sur le `recordIssues` de Gitleaks (c'est le cas de la solution) ; sinon supprimer le build concerné (**Delete build**) |
| 7 | Le stage Trivy avant le build | `--offline-scan` ne trouve pas les dépendances (cache Maven vide) |
| 12 | `changeset 'Dockerfile'` faux au premier build d'une branche | Le changeset compare au build précédent de la même branche |
| 12 | `branch 'main'` toujours faux dans le job Pipeline simple | `BRANCH_NAME` n'existe qu'en Multibranch |
| 13 | `input` demandé même en recette | Ajouter `beforeInput true` dans le `when` du stage |
| 13 | Pipeline appelante bloquée | Il faut 2 executors sur `devsecops-1` : l'appelante en garde un pendant l'appel |

### Numéros de version identiques entre branches

`APP_VERSION` vaut `1.4.<BUILD_NUMBER>` : chaque branche d'un Multibranch a ses propres numéros de build, donc `main` et `feature/messages` produisent toutes deux une version `1.4.1`. Sans conséquence ici (seule `main` construit une image) ; en production, la version d'une branche porte le nom de la branche ou un suffixe `-SNAPSHOT`.

### Deux jobs pour le même dépôt

Après la démo 12, désactiver `devsecops/library-api-devsecops` : sinon chaque commit déclenche un build dans ce job et dans `devsecops » library-api » main` (`pollSCM` des deux côtés).

---

## Sécurité : réglages propres à la formation

| Réglage | Pourquoi il est acceptable ici | En production |
|---|---|---|
| Agent avec la socket Docker du poste | Construire et lancer des images depuis le pipeline | Agent dédié au build d'images, ou construction sans démon (Kaniko, Buildah) |
| `Non verifying Verification Strategy` pour l'agent SSH | Réseau Docker local | Clé d'hôte vérifiée (**Known hosts** ou **Manually provided key**) |
| `.trivyignore` et `.gitleaksignore` modifiables par tout développeur | Démonstration | Revue obligatoire (CODEOWNERS) sur ces fichiers : ils désactivent un contrôle |
| Webhook SonarQube sans validation des adresses locales | Jenkins a une adresse privée Docker | Adresse publique ou reverse proxy |
| Règles Semgrep téléchargées à chaque build | Simplicité | Règles figées et versionnées, ou miroir interne |

---

## Après la session

```bash
docker rm -f library-api-devsecops-recette library-api-devsecops-production
```

```bash
docker compose down -v
```

La seconde commande, lancée dans le dossier de ce kit, supprime l'agent `devsecops-1` et ses caches ; elle ne touche pas à la stack de la partie 1. `docker compose down` ne supprime pas les conteneurs lancés par la pipeline de déploiement (démo 13), ni les images `library-api-devsecops:*` construites à la démo 11 (`docker image ls library-api-devsecops`). Dans Jenkins, le node `devsecops-1` reste déclaré (hors ligne) : le supprimer, ainsi que le dossier `devsecops`, pour revenir exactement à l'état de fin de partie 1.
