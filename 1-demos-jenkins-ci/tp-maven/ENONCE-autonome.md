# TP — Pipeline Maven : de la version au déploiement vérifié (énoncé autonome)

> Durée : 3 h · Prérequis : démos 0 à 10 de la partie 1 (Jenkins, agent `linux-1`, Gitea, credential `gitea-token`)
> Version guidée de ce TP : `ENONCE-guide.md`

## Contexte

L'équipe logistique démarre **inventaire-api**, une API REST de gestion de stock (Java 21, Spring Boot, **Maven**). Vous devez écrire son Jenkinsfile. La chaîne attendue :

1. lire la version **dans le `pom.xml`** (pas de version calculée à la main) ;
2. construire, lancer les tests unitaires, archiver le JAR ;
3. lancer **en même temps** les tests d'intégration et l'analyse statique ;
4. juger la qualité : couverture et alertes PMD / CPD avec des **seuils** ;
5. construire l'image Docker, la **déployer en recette** sans que deux builds ne s'y marchent dessus, puis **vérifier** qu'elle répond ;
6. prévenir l'équipe sur **ntfy** selon le résultat.

Contrainte : **aucune syntaxe écrite de mémoire**. Chaque step et chaque directive doit sortir de la page **Pipeline Syntax** (Snippet Generator, Declarative Directive Generator).

## Fourni

`tp-maven/` : `inventaire-api/` (projet, wrapper `mvnw`, `Dockerfile`), `docker-compose.yml` (ntfy), `init-inventaire-api.ps1` / `.sh` (crée le dépôt Gitea `formation/inventaire-api`).

| Service | Depuis le poste | Depuis Jenkins |
|---|---|---|
| ntfy | http://localhost:8070/inventaire | `http://ntfy/inventaire` |
| Recette | http://localhost:8097 | `http://inventaire-recette:8080` |
| Production (bonus) | http://localhost:8098 | `http://inventaire-prod:8080` |

Rapports produits par Maven : `target/surefire-reports/`, `target/failsafe-reports/`, `target/site/jacoco/jacoco.xml`, `target/pmd.xml`, `target/cpd.xml`.

---

## Exercice 0 — Préparer (10 min)

Démarrer ntfy (`docker compose up -d` dans `tp-maven`), créer le dépôt avec le script d'init, ouvrir http://localhost:8070/inventaire dans un onglet.

**Attendu :** dépôt `formation/inventaire-api` dans Gitea, sans Jenkinsfile.

## Exercice 1 — Plugins (10 min)

Le TP utilise `readMavenPom`, `httpRequest`, `lock` et `cleanWs`. Vérifier quels plugins les fournissent, installer ceux qui manquent.

**Attendu :** les quatre steps apparaissent dans **Sample Step** du Snippet Generator.

## Exercice 2 — Premier Jenkinsfile (25 min)

Job **Multibranch Pipeline** `inventaire-api`. Jenkinsfile : agent `linux`, un stage qui lance `./mvnw -B -ntp clean package`, publication des rapports Surefire **même en cas d'échec**, archivage du JAR avec empreinte **seulement en cas de succès**.

**Attendu :** build vert, **Tests** : 5 tests, **Build Artifacts** : `inventaire-api-1.2.0.jar`.

## Exercice 3 — La version vient du POM (20 min)

Lire la version du `pom.xml` dans une variable d'environnement `VERSION`, et nommer chaque build `#<numéro> - <version>`.

**Attendu :** l'historique affiche `#2 - 1.2.0`.

## Exercice 4 — Tests d'intégration et analyse en parallèle (20 min)

Un stage `Verifications` contenant deux stages simultanés : tests d'intégration Failsafe (`failsafe:integration-test failsafe:verify`, rapports publiés) et analyse `pmd:pmd pmd:cpd`.

**Attendu :** **Pipeline Overview** montre les deux branches côte à côte ; **Tests** : 7 tests.

## Exercice 5 — Seuils de qualité (25 min)

Couverture JaCoCo : moins de **50 %** de lignes → UNSTABLE. PMD + CPD : plus de **5** alertes au total → UNSTABLE. Relever les valeurs, puis monter le seuil de couverture à **60 %** sur une branche et constater.

**Attendu :** 58,33 % de lignes, 1 alerte PMD, 2 blocs dupliqués CPD ; à 60 % : build **UNSTABLE**.

## Exercice 6 — Options et paramètres (15 min)

Garder 10 builds, timeout de 20 minutes, horodatage, pas de builds simultanés. Paramètres : `DEPLOYER_RECETTE` (booléen, vrai par défaut) et `NIVEAU_LOG` (`INFO`, `DEBUG`, `WARN`).

**Attendu :** **Build with Parameters** propose les deux paramètres.

## Exercice 7 — Image et déploiement en recette (25 min)

Construire `inventaire-api:<version>`. Sur `main` seulement, et si `DEPLOYER_RECETTE` est vrai : remplacer le conteneur `inventaire-recette` (réseau `ci-formation`, port 8097, `LOGGING_LEVEL_ROOT` = `NIVEAU_LOG`). Le déploiement se fait **sous un verrou** `recette-inventaire`.

**Attendu :** `Lock acquired on [Resource: recette-inventaire]`, puis http://localhost:8097/actuator/health répond `{"status":"UP"}`. Sur une autre branche, le stage est grisé.

## Exercice 8 — Smoke test (15 min)

Après le `docker run`, le pipeline vérifie lui-même que `/actuator/health` répond **200** avec `UP`. L'application met quelques secondes à démarrer : prévoir plusieurs tentatives espacées.

**Attendu :** `Response Code: 200` et `{"status":"UP"}` dans la console ; si l'application ne démarre pas, le build échoue.

## Exercice 9 — Notifications ntfy (20 min)

Envoyer un `POST` à ntfy en fin de build : titre, message avec lien, tag d'émoji (`white_check_mark`, `warning`, `x`, `tada`) selon que le build réussit, est instable, échoue ou est réparé. Priorité haute en cas d'échec. Nettoyer le workspace en tout dernier.

**Attendu :** les notifications arrivent dans l'onglet ntfy ; `[WS-CLEANUP] Deleting project workspace...` termine chaque build.

## Bonus — Production avec validation (15 min)

Sur `main`, après la recette : attendre une validation humaine (au plus 10 minutes), puis déployer `inventaire-prod` sur le port 8098 et le vérifier.

**Attendu :** `Deployer or Abort` dans la console ; après validation, http://localhost:8098/actuator/health répond `UP`.
