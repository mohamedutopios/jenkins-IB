#!/usr/bin/env python3
"""Genere un schema HTML par demo de DEMOS-v2.md (schemas/demo-00.html ... demo-17.html + index.html).

Les textes "Pourquoi", "Ce qu'elle montre" et "A retenir" sont lus dans DEMOS-v2.md ;
la carte de la stack, l'etat de Jenkins, le deroule et les pipelines sont decrits ci-dessous.
Relancer apres toute modification de DEMOS-v2.md :  python3 schemas/generer-schemas.py
"""
import html
import re
from pathlib import Path

ICI = Path(__file__).resolve().parent
SOURCE = ICI.parent / "DEMOS-v2.md"

# ---------------------------------------------------------------------------
# Carte de la stack : composants (x, y, largeur, hauteur) et liaisons
# ---------------------------------------------------------------------------

COMPOSANTS = {
    "poste":    dict(titre="Poste du stagiaire", box=(20, 30, 180, 340)),
    "nav":      dict(titre="Navigateur", box=(35, 75, 150, 70)),
    "term":     dict(titre="Terminal", box=(35, 255, 150, 70)),
    "internet": dict(titre="Internet", box=(20, 420, 180, 120)),
    "gitea":    dict(titre="Gitea (serveur Git)", box=(260, 55, 210, 125)),
    "jenkins":  dict(titre="Jenkins (controller)", box=(520, 50, 290, 180)),
    "mailpit":  dict(titre="Mailpit (SMTP de test)", box=(870, 50, 220, 85)),
    "nexus":    dict(titre="Nexus", box=(870, 175, 220, 90)),
    "sonar":    dict(titre="SonarQube", box=(870, 300, 220, 90)),
    "linux1":   dict(titre="linux-1 (agent SSH)", box=(520, 320, 290, 170)),
    "docker":   dict(titre="Docker du poste", box=(260, 400, 210, 110)),
    "recette":  dict(titre="recette", box=(870, 430, 105, 90)),
    "prod":     dict(titre="production", box=(985, 430, 105, 90)),
}
# Composants dessines comme boites de service (les autres sont des cadres)
SERVICES = ["internet", "gitea", "jenkins", "mailpit", "nexus", "sonar", "linux1", "docker", "recette", "prod"]

# Liaisons : points de la ligne brisee, libelle du protocole
LIAISONS = {
    "jenkins>linux1":   ([(640, 230), (640, 320)], "SSH"),
    "linux1>gitea":     ([(560, 320), (560, 285), (380, 285), (380, 180)], "git clone"),
    "gitea>jenkins":    ([(470, 85), (520, 85)], "webhook"),
    "jenkins>gitea":    ([(520, 140), (470, 140)], "lecture Git"),
    "jenkins>mailpit":  ([(810, 92), (870, 92)], "SMTP"),
    "linux1>nexus":     ([(810, 340), (840, 340), (840, 235), (870, 235)], "mvn deploy"),
    "linux1>sonar":     ([(810, 365), (870, 365)], "analyse"),
    "sonar>jenkins":    ([(1090, 330), (1108, 330), (1108, 155), (810, 155)], "webhook"),
    "linux1>docker":    ([(520, 455), (470, 455)], "docker"),
    "docker>recette":   ([(430, 510), (430, 560), (922, 560), (922, 520)], "docker run"),
    "docker>prod":      ([(400, 510), (400, 582), (1037, 582), (1037, 520)], "docker run"),
    "linux1>recette":   ([(810, 470), (870, 470)], "smoke test"),
    "jenkins>internet": ([(520, 205), (215, 205), (215, 470), (200, 470)], "HTTPS"),
    "linux1>internet":  ([(520, 478), (490, 478), (490, 535), (200, 535)], "HTTPS"),
}

# ---------------------------------------------------------------------------
# Description des demos
#   etat      : operations sur l'etat de Jenkins et des services
#               ("+", categorie, cle, texte) ajout ; ("~", categorie, cle, texte) modification
#   lignes    : texte des boites de la carte (conserve d'une demo a la suivante)
#   nouveaux  : composants crees ou configures dans la demo (orange)
#   flux      : actions numerotees ; ("nav"|"term"|"int", composant, texte) ou ("lien", liaison, texte)
#   deroule   : etapes (titre, detail)
#   pipelines : (legende, [stages], post) ; stage = (nom, [lignes], condition ou None)
# ---------------------------------------------------------------------------

CATEGORIES = [
    ("jobs", "Jobs et dossiers"),
    ("nodes", "Nodes"),
    ("creds", "Credentials"),
    ("tools", "Tools"),
    ("plugins", "Plugins"),
    ("system", "Configuration System"),
    ("secu", "Sécurité et comptes"),
    ("gitea", "Gitea"),
    ("nexus", "Nexus"),
    ("sonar", "SonarQube"),
    ("apps", "Conteneurs de library-api"),
]

LIGNES_INITIALES = {
    "poste": [],
    "nav": ["localhost:8080, :3000…"],
    "term": ["docker, curl, scripts/"],
    "internet": ["updates.jenkins.io", "Maven Central, images"],
    "mailpit": ["SMTP mailpit:1025", "boîte web localhost:8025"],
    "nexus": ["dépôt d'artefacts Maven", "localhost:8081 · nexus:8081"],
    "sonar": ["analyse statique du code", "localhost:9000 · sonarqube:9000"],
    "docker": ["moteur Docker du poste", "socket /var/run/docker.sock"],
    "recette": ["library-api", "port 8090"],
    "prod": ["library-api", "port 8091"],
}

# Premiere demo ou le composant existe (avant : dessine en pointille)
APPARITION = {"nexus": 14, "sonar": 15, "recette": 14, "prod": 14}

DEMOS = {
    0: dict(
        nouveaux=["jenkins", "linux1", "gitea", "mailpit", "docker"],
        lignes={
            "jenkins": ["2.580.2 LTS · JDK 21", "volume JENKINS_HOME", "assistant de démarrage en attente"],
            "linux1": ["JDK 21, Git, client Docker", "clé publique du controller installée", "pas encore déclaré dans Jenkins"],
            "gitea": ["formation/library-api (privé)", "localhost:3000 · gitea:3000"],
        },
        etat=[
            ("+", "secu", "jenkins", "Jenkins démarré, assistant non passé (Unlock Jenkins)"),
            ("+", "gitea", "compte", "compte formation / Formation-2026"),
            ("+", "gitea", "depot", "dépôt privé formation/library-api, branche main"),
        ],
        flux=[
            ("term", "linux1", "scripts/preparer.sh génère la paire de clés keys/jenkins_agent et reporte la clé publique dans .env"),
            ("term", "docker", "docker compose up -d --build : construit l'image de linux-1 et démarre jenkins, linux-1, gitea et mailpit"),
            ("term", "gitea", "scripts/init-gitea.sh crée le compte formation et le dépôt privé, puis y pousse library-api"),
            ("nav", "gitea", "connexion à Gitea : le dépôt est Private et contient pom.xml, Jenkinsfile, Dockerfile, src/, ci/"),
            ("nav", "jenkins", "http://localhost:8080 affiche « Unlock Jenkins » : la démo 1 commence là"),
        ],
        deroule=[
            ("Ports libres", "8080, 3000, 8025, 8081, 9000 ; sinon changer .env"),
            ("Clé SSH", "preparer.sh : clé privée pour Jenkins, clé publique pour l'agent"),
            ("Démarrage", "docker compose up -d --build : 4 services running"),
            ("Dépôt Git", "init-gitea.sh : compte, dépôt privé, push du projet"),
            ("Vérifications", "dépôt Private dans Gitea, écran Unlock Jenkins"),
        ],
    ),
    1: dict(
        nouveaux=["jenkins"],
        lignes={"jenkins": ["2.580.2 LTS · JDK 21", "admin · plugins suggérés + Locale", "built-in : 2 executors", "interface forcée en anglais"]},
        etat=[
            ("~", "secu", "jenkins", "compte admin / Formation-2026 (Jenkins' own user database)"),
            ("+", "secu", "authz", "Logged-in users can do anything ; inscription et lecture anonyme fermées"),
            ("+", "plugins", "suggeres", "plugins suggérés (93 avec les dépendances)"),
            ("+", "plugins", "locale", "Locale"),
            ("+", "system", "url", "Jenkins URL : http://localhost:8080/"),
            ("+", "system", "langue", "langue forcée : English"),
            ("+", "nodes", "builtin", "Built-In Node : 2 executors"),
        ],
        flux=[
            ("term", "jenkins", "docker exec jenkins cat …/initialAdminPassword : le mot de passe initial"),
            ("nav", "jenkins", "Unlock Jenkins, puis Select plugins to install : suggestions + Locale"),
            ("lien", "jenkins>internet", "Jenkins télécharge une centaine de plugins depuis updates.jenkins.io"),
            ("nav", "jenkins", "création de admin, Jenkins URL, puis Appearance : English forcé"),
            ("nav", "jenkins", "vérifications : System Information, bandeaux de Manage Jenkins, Security"),
            ("term", "jenkins", "docker exec jenkins ls /var/jenkins_home : tout l'état de Jenkins est là"),
        ],
        deroule=[
            ("Débloquer", "mot de passe initial lu dans le conteneur"),
            ("Plugins", "suggérés + Locale, environ 93 téléchargés"),
            ("Administrateur", "admin / Formation-2026, URL http://localhost:8080/"),
            ("Anglais", "Default Language English, forcé pour tous"),
            ("Vérifier", "version, java.version, JENKINS_HOME, bandeaux, Security"),
        ],
    ),
    2: dict(
        nouveaux=[],
        etat=[("+", "jobs", "hello", "hello (Freestyle : echo des variables, hostname)")],
        flux=[
            ("nav", "jenkins", "New Item → hello (Freestyle project) → Execute shell avec des echo de variables"),
            ("int", "jenkins", "Build Now : le build tourne sur le controller (Node : built-in, executor 1)"),
            ("nav", "jenkins", "lecture : Console Output, liste des builds, nom affiché « premier essai », env-vars.html"),
            ("nav", "jenkins", "tour de Manage Jenkins, puis Script Console : numExecutors = 2"),
        ],
        deroule=[
            ("Créer hello", "Freestyle, un Execute shell qui affiche les variables"),
            ("Lancer", "Build Now : #1 sur built-in"),
            ("Lire", "Console Output de bas en haut, cause et statut"),
            ("Parcourir", "Dashboard, page du job, page du build"),
            ("Manage Jenkins", "situer les pages des démos suivantes, Script Console"),
        ],
    ),
    3: dict(
        nouveaux=[],
        etat=[
            ("~", "jobs", "hello", "hello (Freestyle) : jeton distant hello-token, 5 derniers builds gardés"),
            ("+", "secu", "apitoken", "jeton d'API de admin : demo-cli (30 jours)"),
        ],
        flux=[
            ("nav", "jenkins", "Build periodically H/2 * * * * : un build démarre seul (Started by timer), puis on décoche"),
            ("nav", "jenkins", "Trigger builds remotely : jeton du job hello-token ; jeton d'API demo-cli créé sur le compte admin"),
            ("term", "jenkins", "curl -X POST -u admin:$JENKINS_TOKEN …/job/hello/build?token=hello-token (sans -u : 403)"),
            ("nav", "jenkins", "exit 1, exit 3 (unstable), sleep 120 annulé : FAILURE, UNSTABLE, ABORTED, puis SUCCESS"),
            ("nav", "jenkins", "Discard old builds : Log Rotation, 5 builds gardés"),
        ],
        deroule=[
            ("Timer", "H/2 * * * *, puis H H(2-4) * * 1-5"),
            ("À distance", "jeton du job + jeton d'API de l'appelant"),
            ("Statuts", "provoquer FAILURE, UNSTABLE, ABORTED"),
            ("Météo", "la colonne W résume les 5 derniers builds"),
            ("Rétention", "Discard old builds : 5"),
        ],
        bande=("Les statuts provoqués sur hello", [
            ("SUCCESS", "ok", "exit 0"),
            ("FAILURE", "ko", "exit 1"),
            ("UNSTABLE", "warn", "exit 3 + Exit code to set build unstable = 3"),
            ("ABORTED", "gris", "sleep 120 annulé par la croix rouge"),
            ("SUCCESS", "ok", "lignes retirées : le job repasse au vert"),
        ]),
    ),
    4: dict(
        nouveaux=[],
        etat=[("+", "jobs", "workspace-demo", "workspace-demo (Freestyle : nettoyage du workspace, horodatage)")],
        flux=[
            ("nav", "jenkins", "New Item → workspace-demo, Execute shell qui ajoute une ligne à historique.txt"),
            ("int", "jenkins", "deux builds : historique.txt contient « build 1 » et « build 2 », le workspace est réutilisé"),
            ("nav", "jenkins", "Execute concurrent builds : le second build travaille dans workspace-demo@2"),
            ("nav", "jenkins", "Delete workspace before build starts + timestamps : le fichier ne contient plus qu'une ligne"),
        ],
        deroule=[
            ("Réutilisation", "un fichier survit d'un build à l'autre"),
            ("Page Workspace", "consulter et télécharger les fichiers depuis l'UI"),
            ("Concurrence", "deux builds simultanés : @2"),
            ("Nettoyage", "WS-CLEANUP avant chaque build"),
            ("Horodatage", "chaque ligne de console datée"),
        ],
        bande=("Le workspace de workspace-demo, build après build", [
            ("build #1", "gris", "historique.txt : build 1"),
            ("build #2", "warn", "historique.txt : build 1, build 2 (réutilisé)"),
            ("builds concurrents", "warn", "…/workspace-demo et …/workspace-demo@2"),
            ("nettoyage", "ok", "historique.txt : une seule ligne"),
        ]),
    ),
    5: dict(
        nouveaux=["jenkins", "linux1"],
        lignes={
            "jenkins": ["2.580.2 LTS · JDK 21", "built-in : 0 executor", "credential agent-ssh-key (System)", "message système"],
            "linux1": ["JDK 21, Git, client Docker", "labels : linux java21 maven", "2 executors · /home/jenkins/agent"],
        },
        etat=[
            ("+", "system", "message", "message système, SCM checkout retry count 2, e-mail jenkins@example.com"),
            ("+", "creds", "agent", "agent-ssh-key : SSH Username with private key, portée System"),
            ("+", "nodes", "linux1", "linux-1 : SSH, 2 executors, labels linux java21 maven"),
            ("~", "nodes", "builtin", "Built-In Node : 0 executor"),
            ("~", "jobs", "hello", "hello (Freestyle) : jeton hello-token, 5 builds gardés, label linux"),
            ("~", "jobs", "workspace-demo", "workspace-demo (Freestyle : nettoyage du workspace, horodatage), label linux"),
        ],
        flux=[
            ("nav", "jenkins", "Manage Jenkins → System : message système, retry, adresse de l'administrateur"),
            ("term", "jenkins", "cat keys/jenkins_agent, puis credential agent-ssh-key (portée System)"),
            ("nav", "jenkins", "New Node linux-1 : 2 executors, labels, Launch agents via SSH"),
            ("lien", "jenkins>linux1", "le controller ouvre la session SSH, copie remoting.jar et lance l'agent"),
            ("lien", "jenkins>linux1", "hello avec le label linux : le build part sur linux-1"),
            ("nav", "jenkins", "built-in à 0 executor : workspace-demo sans label reste en file, on lui ajoute le label"),
        ],
        deroule=[
            ("System", "réglages globaux"),
            ("Credential", "clé privée du controller, portée System"),
            ("Node linux-1", "SSH, labels, Only build jobs with label…"),
            ("Connexion", "log : Agent successfully connected"),
            ("Labels", "hello part sur linux-1"),
            ("0 executor", "le controller n'exécute plus rien"),
        ],
    ),
    6: dict(
        nouveaux=["jenkins"],
        lignes={"jenkins": ["2.580.2 LTS · JDK 21", "built-in : 0 executor", "+ 7 plugins de la partie 3", "message système"]},
        etat=[("+", "plugins", "partie3", "Maven Integration, Coverage, Config File Provider, Lockable Resources, SonarQube Scanner, Warnings, Role-based Authorization Strategy")],
        flux=[
            ("nav", "jenkins", "Plugins → Available plugins : cocher les 7 plugins de la partie 3"),
            ("lien", "jenkins>internet", "téléchargement des plugins et de leurs dépendances"),
            ("nav", "jenkins", "Installed plugins (junit, santé) et onglet Updates"),
            ("term", "jenkins", "docker exec jenkins ls /var/jenkins_home/plugins : un .jpi par plugin"),
        ],
        deroule=[
            ("Chercher", "Available plugins, colonne Health"),
            ("Installer", "un seul Install pour les 7"),
            ("Vérifier", "Installed plugins, Updates"),
            ("Sur le disque", "JENKINS_HOME/plugins ; en prod : plugins.txt"),
        ],
    ),
    7: dict(
        nouveaux=["jenkins", "gitea", "linux1"],
        lignes={
            "jenkins": ["2.580.2 LTS · JDK 21", "built-in : 0 executor", "tools : jdk21, maven-3.9", "credentials : agent-ssh-key, gitea-token"],
            "linux1": ["JDK 21, Git, client Docker", "labels : linux java21 maven", "2 executors · /home/jenkins/agent", "tools/ : Maven 3.9.16"],
            "gitea": ["formation/library-api (privé)", "jeton jenkins (lecture)"],
        },
        etat=[
            ("+", "tools", "jdk", "jdk21 → /opt/java/openjdk (déjà dans l'image de l'agent)"),
            ("+", "tools", "maven", "maven-3.9 : 3.9.16, installé au premier usage"),
            ("+", "tools", "git", "Git : Default"),
            ("+", "gitea", "token", "jeton d'accès jenkins (repository : Read)"),
            ("+", "creds", "gitea", "gitea-token : formation + jeton Gitea, portée Global"),
            ("+", "jobs", "outils", "outils (Freestyle : mvn -v, secret masqué)"),
        ],
        flux=[
            ("nav", "jenkins", "Manage Jenkins → Tools : jdk21 (chemin), maven-3.9 (installation automatique)"),
            ("nav", "gitea", "Settings → Applications : jeton jenkins en lecture seule sur les dépôts"),
            ("nav", "jenkins", "credential gitea-token (Username with password, portée Global)"),
            ("lien", "jenkins>linux1", "job outils lancé sur linux-1"),
            ("lien", "linux1>internet", "premier build : Maven 3.9.16 téléchargé dans /home/jenkins/agent/tools"),
            ("int", "jenkins", "la console affiche le secret sous la forme ****"),
        ],
        deroule=[
            ("Tools", "jdk21, maven-3.9, Git"),
            ("Jeton Gitea", "lecture seule, copié une fois"),
            ("Credential", "gitea-token, portée Global"),
            ("Job outils", "mvn -v + secret lié en variables"),
            ("Constat", "Unpacking au 1er build, **** dans la console"),
        ],
    ),
    8: dict(
        nouveaux=["jenkins"],
        lignes={"linux1": ["JDK 21, Git, client Docker", "labels : linux java21 maven", "2 executors · /home/jenkins/agent", "cache ~/.m2 (volume m2_cache)"]},
        etat=[
            ("+", "jobs", "library", "dossier library"),
            ("+", "jobs", "freestyle", "library/library-api-freestyle (Git, Poll SCM H/2, Maven -Drevision=1.4.${BUILD_NUMBER}, JUnit, archive du JAR)"),
            ("+", "gitea", "readme", "commit README.md sur main"),
        ],
        flux=[
            ("nav", "jenkins", "dossier library, puis job library-api-freestyle : Git, Poll SCM, Maven, post-build"),
            ("lien", "jenkins>linux1", "Build Now : le build part sur linux-1"),
            ("lien", "linux1>gitea", "clone authentifié par gitea-token"),
            ("lien", "linux1>internet", "premier build : dépendances Maven téléchargées puis gardées dans ~/.m2"),
            ("int", "jenkins", "rapports Surefire publiés, library-api-1.4.<n>.jar archivé avec empreinte"),
            ("nav", "gitea", "ajout de README.md sur main"),
            ("lien", "jenkins>gitea", "Poll SCM voit le commit : Started by an SCM change"),
        ],
        deroule=[
            ("Folder", "library"),
            ("Source", "Git + gitea-token"),
            ("Déclencheur", "Poll SCM H/2"),
            ("Build", "maven-3.9, revision=1.4.${BUILD_NUMBER}"),
            ("Post-build", "JUnit + archive du JAR"),
            ("Changement", "commit dans Gitea → build"),
        ],
    ),
    9: dict(
        nouveaux=["jenkins"],
        etat=[("+", "jobs", "pipeline", "library/library-api-pipeline (Pipeline script from SCM : Jenkinsfile)")],
        flux=[
            ("nav", "jenkins", "job library-api-pipeline, Definition : Pipeline script collé dans l'éditeur"),
            ("lien", "jenkins>linux1", "le pipeline s'exécute sur linux-1 (agent { label 'linux' })"),
            ("lien", "linux1>gitea", "stage Checkout : git avec credentialsId gitea-token"),
            ("nav", "jenkins", "Pipeline Syntax : Snippet Generator (archiveArtifacts) et Declarative Directive Generator (timeout)"),
            ("nav", "jenkins", "Replay : un stage ajouté sans toucher la configuration"),
            ("lien", "jenkins>gitea", "Pipeline script from SCM : Jenkins lit le Jenkinsfile du dépôt"),
            ("term", "jenkins", "curl …/pipeline-model-converter/validate : Jenkinsfile validé sans build"),
        ],
        deroule=[
            ("Script dans l'UI", "itérer vite"),
            ("Générateurs", "Snippet et Directive"),
            ("Replay", "essayer une modification"),
            ("from SCM", "le Jenkinsfile vient du dépôt"),
            ("Valider", "API de validation, erreur de syntaxe"),
        ],
        pipelines=[
            ("Pipeline script saisi dans l'UI", [
                ("Declarative: Tool Install", ["jdk21, maven-3.9"], None),
                ("Checkout", ["git … gitea-token"], None),
                ("Build & Test", ["mvn -B -ntp clean verify"], None),
            ], ["always : junit", "success : archiveArtifacts"]),
            ("Jenkinsfile du dépôt (Pipeline script from SCM)", [
                ("Build & Test", ["mvn -B -ntp clean verify"], None),
                ("Package", ["archiveArtifacts *.jar"], "branch 'main' (sauté ici)"),
            ], ["always : junit"]),
        ],
    ),
    10: dict(
        nouveaux=["jenkins", "gitea"],
        lignes={"gitea": ["formation/library-api (privé)", "jeton jenkins · webhook → Jenkins"]},
        etat=[
            ("+", "jobs", "multibranch", "library/library-api (Multibranch : Jenkinsfile, scan toutes les heures)"),
            ("+", "secu", "notify", "jeton notifyCommit « gitea »"),
            ("+", "gitea", "webhook", "webhook → jenkins:8080/git/notifyCommit (Create, Delete, Push)"),
        ],
        flux=[
            ("nav", "jenkins", "New Item → library-api (Multibranch Pipeline), source Git + gitea-token"),
            ("lien", "jenkins>gitea", "scan du dépôt : un sous-job par branche qui contient un Jenkinsfile"),
            ("lien", "jenkins>linux1", "sous-job main : Build & Test puis Package (cette fois exécuté)"),
            ("nav", "jenkins", "Security → jeton notifyCommit « gitea »"),
            ("nav", "gitea", "webhook vers http://jenkins:8080/git/notifyCommit?url=…&token=…"),
            ("lien", "gitea>jenkins", "commit, création ou suppression de branche : Jenkins relance l'indexation dans la seconde"),
            ("nav", "gitea", "branche feature/isbn créée (sous-job, Package sauté) puis supprimée (sous-job orphelin)"),
        ],
        deroule=[
            ("Multibranch", "source Git, by Jenkinsfile"),
            ("Indexation", "sous-job main"),
            ("Jeton", "notifyCommit"),
            ("Webhook", "Create, Delete, Push"),
            ("Branche", "feature/isbn créée puis supprimée"),
        ],
        pipelines=[
            ("Jenkinsfile, sous-job main et sous-job feature/isbn", [
                ("Build & Test", ["mvn -B -ntp clean verify", "toutes les branches"], None),
                ("Package", ["archiveArtifacts *.jar"], "branch 'main'"),
            ], ["always : junit"]),
        ],
    ),
    11: dict(
        nouveaux=["jenkins"],
        etat=[("+", "jobs", "parametres", "library/library-api-parametres (ci/Jenkinsfile.parametres : TARGET_ENV, VERSION_MINEURE, RUN_IT)")],
        flux=[
            ("nav", "jenkins", "Duplicate library-api-pipeline, Script Path ci/Jenkinsfile.parametres"),
            ("lien", "jenkins>linux1", "premier Build Now : valeurs par défaut, Jenkins enregistre les paramètres"),
            ("nav", "jenkins", "Build with Parameters : recette, 2.0, RUN_IT décoché → #2 v2.0.2 recette"),
            ("term", "jenkins", "curl …/buildWithParameters?TARGET_ENV=prod&VERSION_MINEURE=1.5&RUN_IT=true"),
        ],
        deroule=[
            ("Dupliquer", "changer le Script Path"),
            ("Build Now", "le bouton n'a pas encore de paramètres"),
            ("Paramètres", "un stage sauté par RUN_IT"),
            ("API", "buildWithParameters"),
        ],
        pipelines=[
            ("ci/Jenkinsfile.parametres", [
                ("Build", ["-Drevision=<mineure>.<build>", "-DskipITs clean verify"], None),
                ("Tests d'integration", ["failsafe:integration-test"], "params.RUN_IT"),
                ("Deploy", ["echo … sur $TARGET_ENV"], None),
            ], []),
        ],
    ),
    12: dict(
        nouveaux=["jenkins", "gitea"],
        etat=[("+", "jobs", "tests", "library/library-api-tests (ci/Jenkinsfile.tests : junit, recordCoverage, seuil 80 %)")],
        flux=[
            ("nav", "jenkins", "Duplicate library-api-pipeline, Script Path ci/Jenkinsfile.tests, Build Now : vert, couverture 83,78 %"),
            ("nav", "gitea", "BookServiceTest : == 2 remplacé par == 1"),
            ("lien", "jenkins>linux1", "le test échoue : UNSTABLE, stack trace dans Test Result"),
            ("nav", "gitea", "Book.java : un ; supprimé"),
            ("lien", "jenkins>linux1", "erreur de compilation : FAILURE, pas de rapport"),
            ("nav", "jenkins", "les deux fichiers corrigés, puis Replay avec un seuil à 90 % : UNSTABLE"),
        ],
        deroule=[
            ("Job de tests", "Test Result et Coverage"),
            ("Test faux", "UNSTABLE"),
            ("Compilation cassée", "FAILURE"),
            ("Correction", "retour au vert"),
            ("Seuil 90 %", "Replay : UNSTABLE"),
        ],
        pipelines=[
            ("ci/Jenkinsfile.tests", [
                ("Build & Tests", ["mvn … clean verify", "test.failure.ignore=true"], None),
            ], ["always (stage) : junit", "recordCoverage", "seuil 80 % → UNSTABLE"]),
        ],
        bande=("Trois builds, trois verdicts", [
            ("SUCCESS", "ok", "tests verts, couverture ≥ 80 %"),
            ("UNSTABLE", "warn", "un test faux : ça compile, ça ne passe pas"),
            ("FAILURE", "ko", "un ; manquant : ça ne compile pas"),
            ("UNSTABLE", "warn", "seuil de couverture porté à 90 %"),
        ]),
    ),
    13: dict(
        nouveaux=["jenkins", "mailpit"],
        lignes={"mailpit": ["SMTP mailpit:1025", "mails de Jenkins à lire sur :8025"]},
        etat=[
            ("+", "system", "mail", "SMTP mailpit:1025 (Mailer et Email Extension), destinataires dev-team@example.com"),
            ("+", "jobs", "mail", "library/library-api-mail (ci/Jenkinsfile.mail : emailext dans post)"),
        ],
        flux=[
            ("nav", "jenkins", "System : Extended E-mail Notification et E-mail Notification sur mailpit:1025"),
            ("lien", "jenkins>mailpit", "mail de test, puis mails émis par emailext"),
            ("nav", "mailpit", "http://localhost:8025 : Test email #1"),
            ("nav", "gitea", "test cassé : build UNSTABLE, mail « instable »"),
            ("nav", "gitea", "test réparé : build SUCCESS, mail « réparé » (fixed)"),
        ],
        deroule=[
            ("SMTP", "deux plugins, un même serveur"),
            ("Test", "mail visible dans Mailpit"),
            ("Job mail", "Jenkinsfile.mail"),
            ("Changements d'état", "unstable, puis fixed"),
            ("Freestyle", "Editable Email Notification (lecture)"),
        ],
        pipelines=[
            ("ci/Jenkinsfile.mail", [
                ("Build & Tests", ["mvn … clean verify", "always : junit"], None),
            ], ["failure : emailext", "unstable : emailext", "fixed : emailext"]),
        ],
    ),
    14: dict(
        nouveaux=["nexus", "jenkins", "docker", "recette", "prod"],
        lignes={
            "jenkins": ["2.580.2 LTS · JDK 21", "built-in : 0 executor", "credential nexus-deploy", "fichier géré nexus-settings"],
            "nexus": ["maven-releases : library-api 1.4.x", "utilisateur jenkins (deploy-maven)"],
            "docker": ["image library-api:1.4.x", "socket /var/run/docker.sock"],
        },
        etat=[
            ("+", "nexus", "depart", "Nexus démarré : admin / Formation-2026, accès anonyme fermé"),
            ("+", "nexus", "role", "rôle deploy-maven (add, browse, edit, read)"),
            ("+", "nexus", "user", "utilisateur technique jenkins"),
            ("+", "creds", "nexus", "nexus-deploy : utilisateur jenkins de Nexus, portée Global"),
            ("+", "system", "managed", "fichier géré nexus-settings (Maven settings.xml)"),
            ("+", "jobs", "deploiement", "library/library-api-deploiement (ci/Jenkinsfile.deploiement)"),
            ("+", "nexus", "artefact", "maven-releases : library-api 1.4.1"),
            ("+", "apps", "recette", "library-api-recette sur :8090"),
            ("+", "apps", "prod", "library-api-prod sur :8091"),
        ],
        flux=[
            ("term", "nexus", "docker compose --profile deploiement up -d nexus, mot de passe initial"),
            ("nav", "nexus", "assistant, rôle deploy-maven, utilisateur jenkins, maven-releases sans redéploiement"),
            ("nav", "jenkins", "credential nexus-deploy et fichier géré nexus-settings (settings.xml)"),
            ("lien", "jenkins>linux1", "job library-api-deploiement lancé sur linux-1"),
            ("lien", "linux1>nexus", "Publish to Nexus : mvn deploy de library-api 1.4.1"),
            ("lien", "linux1>docker", "Docker image : library-api:1.4.1"),
            ("lien", "docker>recette", "Deploy recette (lock env-recette) : conteneur sur :8090"),
            ("lien", "linux1>recette", "smoke test : /actuator/health répond UP"),
            ("nav", "jenkins", "Approve production : TICKET CHG-0001, bouton Deployer"),
            ("lien", "docker>prod", "Deploy production (lock env-production) : conteneur sur :8091"),
        ],
        deroule=[
            ("Nexus", "démarrage et assistant"),
            ("Compte technique", "rôle deploy-maven, utilisateur jenkins"),
            ("Jenkins", "credential + settings.xml géré"),
            ("Publier", "JAR immuable dans maven-releases"),
            ("Recette", "image, conteneur, smoke test"),
            ("Production", "approbation, même version"),
        ],
        pipelines=[
            ("ci/Jenkinsfile.deploiement", [
                ("Build & Tests", ["clean verify", "junit"], None),
                ("Publish to Nexus", ["mvn -s $SETTINGS deploy"], None),
                ("Docker image", ["docker build", "library-api:1.4.<n>"], None),
                ("Deploy recette", ["lock env-recette", "docker run + smoke test"], None),
                ("Approve production", ["input : TICKET", "Deployer / Abort"], None),
                ("Deploy production", ["lock env-production", "docker run :8091"], None),
            ], []),
        ],
    ),
    15: dict(
        nouveaux=["sonar", "jenkins"],
        lignes={
            "jenkins": ["2.580.2 LTS · JDK 21", "built-in : 0 executor", "serveur SonarQube « sonarqube »", "credential sonar-token"],
            "sonar": ["projet library-api", "webhook → jenkins:8080"],
        },
        etat=[
            ("+", "sonar", "depart", "SonarQube démarré : admin / Formation-2026!"),
            ("+", "sonar", "token", "jeton d'analyse globale jenkins (30 jours)"),
            ("+", "sonar", "webhook", "webhook jenkins → http://jenkins:8080/sonarqube-webhook/"),
            ("+", "sonar", "projet", "projet library-api, Quality Gate Sonar way"),
            ("+", "creds", "sonar", "sonar-token : Secret text"),
            ("+", "system", "sonar", "serveur SonarQube sonarqube → http://sonarqube:9000"),
            ("+", "jobs", "qualite", "library/library-api-qualite (ci/Jenkinsfile.qualite)"),
        ],
        flux=[
            ("term", "sonar", "docker compose up -d sonarqube, attente de l'état UP"),
            ("nav", "sonar", "mot de passe, jeton d'analyse, webhooks locaux autorisés, webhook vers Jenkins"),
            ("nav", "jenkins", "credential sonar-token, puis System → SonarQube servers"),
            ("lien", "jenkins>linux1", "job library-api-qualite lancé sur linux-1"),
            ("lien", "linux1>sonar", "mvn sonar:sonar dans withSonarQubeEnv"),
            ("lien", "sonar>jenkins", "verdict de la Quality Gate envoyé par webhook : waitForQualityGate se termine"),
            ("nav", "sonar", "Quality Gate formation-stricte par défaut : FAILURE, puis retour à Sonar way"),
        ],
        deroule=[
            ("SonarQube", "démarrage, mot de passe"),
            ("Jeton", "Global Analysis Token"),
            ("Webhook", "vers jenkins:8080"),
            ("Jenkins", "credential + serveur"),
            ("Analyse", "lien SonarQube sur le build"),
            ("Gate stricte", "le pipeline échoue"),
        ],
        pipelines=[
            ("ci/Jenkinsfile.qualite", [
                ("Build & Tests", ["clean verify", "junit, recordIssues"], None),
                ("SonarQube analysis", ["withSonarQubeEnv(…)", "mvn sonar:sonar"], None),
                ("Quality Gate", ["waitForQualityGate", "abortPipeline: true"], None),
            ], []),
        ],
    ),
    16: dict(
        nouveaux=["jenkins"],
        lignes={"jenkins": ["2.580.2 LTS · JDK 21", "built-in : 0 executor", "Role-Based Strategy", "comptes viewer1, dev1, release1"]},
        etat=[
            ("+", "secu", "users", "comptes viewer1, dev1, release1"),
            ("~", "secu", "authz", "Role-Based Strategy (la matrice a seulement été lue)"),
            ("+", "secu", "roles", "rôles reader (global), library-dev et library-release (items du dossier library)"),
        ],
        flux=[
            ("nav", "jenkins", "Users → Create User : viewer1, dev1, release1"),
            ("nav", "jenkins", "Authorization → Matrix-based security : lecture des permissions, sans enregistrer"),
            ("nav", "jenkins", "Role-Based Strategy : rôle global reader, rôles d'item library-dev et library-release"),
            ("nav", "jenkins", "Assign Roles : chaque compte reçoit ses rôles"),
            ("nav", "jenkins", "navigation privée : ce que voit et peut faire chaque compte"),
        ],
        deroule=[
            ("Comptes", "trois profils"),
            ("Matrice", "lire les permissions"),
            ("Rôles", "global + items par motif"),
            ("Affectation", "Assign Roles"),
            ("Vérifier", "se connecter avec chaque compte"),
        ],
        roles=[
            ("viewer1", "reader", "Overall/Read seul : tableau de bord vide, pas de Manage Jenkins"),
            ("dev1", "reader + library-dev", "motif library(/.*)? : Build, Cancel, Configure, Read, Workspace, Replay"),
            ("release1", "reader + library-release", "motif library(/(library-api-deploiement|deploy-.*))? : Build, Read"),
            ("admin", "admin", "tous les droits, dont Overall/Administer"),
        ],
    ),
    17: dict(
        nouveaux=["jenkins", "linux1", "nexus", "sonar", "docker", "recette", "prod"],
        etat=[
            ("+", "jobs", "deployprod", "library/deploy-prod (ci/Jenkinsfile.deploy-prod, paramètre ARTIFACT_VERSION)"),
            ("~", "jobs", "multibranch", "library/library-api (Multibranch) : Script Path ci/Jenkinsfile.complet"),
            ("+", "gitea", "branche", "branche feature/demo-finale"),
        ],
        flux=[
            ("nav", "jenkins", "job deploy-prod : premier build en échec volontaire, le paramètre est enregistré"),
            ("nav", "jenkins", "Multibranch library-api : Script Path ci/Jenkinsfile.complet, Build Now sur main"),
            ("lien", "jenkins>linux1", "le pipeline complet tourne sur linux-1"),
            ("lien", "linux1>gitea", "Checkout : checkout scm, nom du build = commit court"),
            ("lien", "linux1>sonar", "Quality : analyse SonarQube"),
            ("lien", "sonar>jenkins", "verdict de la Quality Gate par webhook"),
            ("lien", "linux1>nexus", "Publish : JAR dans maven-releases"),
            ("lien", "linux1>docker", "Publish : image library-api:1.4.<n>"),
            ("lien", "docker>recette", "Deploy recette : lock, docker run"),
            ("lien", "linux1>recette", "smoke test UP"),
            ("nav", "jenkins", "Production : input, clic Deployer, puis build job library/deploy-prod"),
            ("lien", "docker>prod", "deploy-prod déploie la même version sur :8091"),
            ("nav", "gitea", "branche feature/demo-finale : seuls Checkout, Build et Quality s'exécutent"),
        ],
        retenir=("Un seul Jenkinsfile assemble les briques des démos précédentes. Sur <code>main</code>, il va du commit "
                 "jusqu'à la production, en passant par la recette et une approbation ; sur une autre branche, il s'arrête aux "
                 "vérifications. La production ne reconstruit rien : <code>deploy-prod</code> déploie la version déjà publiée "
                 "dans Nexus et testée en recette."),
        deroule=[
            ("Job CD", "deploy-prod paramétré"),
            ("Pipeline complet", "Script Path du Multibranch"),
            ("main", "du commit à la recette"),
            ("Approbation", "puis délégation à deploy-prod"),
            ("Branche", "vérifications seules"),
            ("Relecture", "chaque bloc et sa démo"),
        ],
        pipelines=[
            ("ci/Jenkinsfile.complet (Multibranch library/library-api)", [
                ("Checkout", ["checkout scm", "nom = commit court"], None),
                ("Build & Unit tests", ["clean verify", "junit, recordCoverage"], None),
                ("Quality", ["sonar:sonar", "waitForQualityGate"], "not changeRequest()"),
                ("Publish", ["mvn deploy (Nexus)", "docker build"], "branch 'main'"),
                ("Deploy recette", ["lock env-recette", "docker run + smoke test"], "branch 'main'"),
                ("Production", ["input Deployer", "build job deploy-prod"], "branch 'main'"),
            ], ["failure : emailext", "unstable : emailext", "fixed : emailext"]),
            ("ci/Jenkinsfile.deploy-prod (job library/deploy-prod)", [
                ("Deploy production", ["lock env-production", "docker run :8091", "smoke test"], None),
            ], []),
        ],
    ),
}

# ---------------------------------------------------------------------------
# Lecture de DEMOS-v2.md
# ---------------------------------------------------------------------------

def md_inline(texte):
    t = html.escape(texte, quote=False)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", t)
    return t


def citation_html(lignes):
    """Lignes d'une citation Markdown (sans le >) -> paragraphes et blocs de code HTML."""
    out, para, code, dans_code = [], [], [], False
    for l in lignes:
        l = l[1:] if l.startswith(" ") else l
        if l.strip().startswith("```"):
            if dans_code:
                out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code = []
            elif para:
                out.append("<p>" + md_inline(" ".join(para)) + "</p>")
                para = []
            dans_code = not dans_code
        elif dans_code:
            code.append(l)
        elif l.strip():
            para.append(l.strip())
        elif para:
            out.append("<p>" + md_inline(" ".join(para)) + "</p>")
            para = []
    if para:
        out.append("<p>" + md_inline(" ".join(para)) + "</p>")
    return "".join(out)


def lire_demos():
    texte = SOURCE.read_text(encoding="utf-8")
    sections = re.split(r"^## (?=Démo \d+ — )", texte, flags=re.M)[1:]
    infos = {}
    for sec in sections:
        sec = re.split(r"^## (?!Démo)", sec, flags=re.M)[0]
        m = re.match(r"Démo (\d+) — (.+)", sec)
        n, titre = int(m.group(1)), m.group(2).strip()
        meta = re.search(r"^> (Slides.+)$", sec, re.M)
        pourquoi = re.search(r"^\*\*Pourquoi\.\*\* (.+)$", sec, re.M)
        montre = re.search(r"^\*\*Ce qu'elle montre\.\*\* (.+)$", sec, re.M)
        retenir = None
        for bloc in re.findall(r"^(> \*\*(?:À retenir|Point clé)[^\n]*(?:\n>[^\n]*)*)", sec, re.M):
            corps = citation_html([l[1:] for l in bloc.splitlines()])
            if bloc.startswith("> **À retenir"):
                retenir = corps
                break
            retenir = retenir or corps
        infos[n] = dict(
            titre=titre,
            meta=meta.group(1) if meta else "",
            pourquoi=pourquoi.group(1) if pourquoi else "",
            montre=montre.group(1) if montre else "",
            retenir=retenir or "<p>" + DEMOS.get(n, {}).get("retenir", "") + "</p>",
        )
    return infos

# ---------------------------------------------------------------------------
# Etat cumule
# ---------------------------------------------------------------------------

def etats():
    """Pour chaque demo : (etat avant, etat apres, cles ajoutees, cles modifiees, lignes des boites)."""
    courant = {c: {} for c, _ in CATEGORIES}
    lignes = dict(LIGNES_INITIALES)
    liaisons_vues = set()
    res = {}
    for n in sorted(DEMOS):
        d = DEMOS[n]
        avant = {c: dict(v) for c, v in courant.items()}
        ajouts, modifs = set(), set()
        for op, cat, cle, txt in d["etat"]:
            if op == "+":
                ajouts.add((cat, cle))
            elif (cat, cle) in {(c, k) for c in avant for k in avant[c]}:
                modifs.add((cat, cle))
            else:
                ajouts.add((cat, cle))
            courant[cat][cle] = txt
        lignes.update(d.get("lignes", {}))
        apres = {c: dict(v) for c, v in courant.items()}
        res[n] = dict(avant=avant, apres=apres, ajouts=ajouts, modifs=modifs,
                      lignes=dict(lignes), liaisons_avant=set(liaisons_vues))
        for f in d["flux"]:
            if f[0] == "lien":
                liaisons_vues.add(f[1])
    return res

# ---------------------------------------------------------------------------
# SVG
# ---------------------------------------------------------------------------

def esc(t):
    return html.escape(t, quote=True)


def statut(comp, n, d):
    if APPARITION.get(comp, 0) > n:
        return "absent"
    if comp in d["nouveaux"]:
        return "nouveau"
    utilises = {f[1] for f in d["flux"] if f[0] != "lien"}
    for f in d["flux"]:
        if f[0] == "lien":
            utilises.update(f[1].split(">"))
    if comp in utilises:
        return "utilise"
    return "inchange"


def milieu(points):
    meilleur, lg = None, -1
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        l = abs(x2 - x1) + abs(y2 - y1)
        if l > lg:
            meilleur, lg = ((x1 + x2) / 2, (y1 + y2) / 2, x1 == x2), l
    return meilleur


def carte(n, d, et):
    W, H = 1130, 610
    s = [f'<svg viewBox="0 0 {W} {H}" class="carte" role="img" aria-label="Carte de la stack, démo {n}" xmlns="http://www.w3.org/2000/svg">',
         '<defs>'
         '<marker id="fl" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="tete"/></marker>'
         '<marker id="flg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="tete-g"/></marker>'
         '</defs>']
    # Reseau Docker
    s.append('<rect x="230" y="20" width="890" height="580" rx="16" class="reseau"/>')
    s.append('<text x="1110" y="594" class="reseau-t" text-anchor="end">réseau Docker ci-formation</text>')
    # Poste
    x, y, w, h = COMPOSANTS["poste"]["box"]
    s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" class="poste"/>')
    s.append(f'<text x="{x + w / 2}" y="{y + 24}" class="poste-t" text-anchor="middle">Poste du stagiaire</text>')

    # Liaisons deja etablies (grises), puis celles de la demo
    actives = [f[1] for f in d["flux"] if f[0] == "lien"]
    for cle in sorted(et["liaisons_avant"] - set(actives)):
        pts, _ = LIAISONS[cle]
        if any(APPARITION.get(c, 0) > n for c in cle.split(">")):
            continue
        s.append(f'<polyline points="{" ".join(f"{a},{b}" for a, b in pts)}" class="lien-ancien" marker-end="url(#flg)"/>')
    for cle in dict.fromkeys(actives):
        pts, _ = LIAISONS[cle]
        s.append(f'<polyline points="{" ".join(f"{a},{b}" for a, b in pts)}" class="lien" marker-end="url(#fl)"/>')

    # Boites
    for comp in ["nav", "term"] + SERVICES:
        x, y, w, h = COMPOSANTS[comp]["box"]
        st = statut(comp, n, d) if comp not in ("nav", "term") else ("utilise" if any(f[0] == comp for f in d["flux"]) else "inchange")
        s.append(f'<g class="comp st-{st}">')
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>')
        cx = x + w / 2
        s.append(f'<text x="{cx}" y="{y + 22}" class="c-t" text-anchor="middle">{esc(COMPOSANTS[comp]["titre"])}</text>')
        lignes = et["lignes"].get(comp, [])
        if st == "absent":
            lignes = ["pas démarré", f"(démo {APPARITION[comp]})"] if w < 150 else [f"démarré à la démo {APPARITION[comp]}"]
        for i, l in enumerate(lignes):
            s.append(f'<text x="{cx}" y="{y + 42 + i * 17}" class="c-l" text-anchor="middle">{esc(l)}</text>')
        s.append('</g>')

    # Numeros : badges sur les boites, pastilles sur les liaisons
    par_comp = {}
    deja = {}
    for i, f in enumerate(d["flux"], 1):
        genre, cible = f[0], f[1]
        if genre == "lien":
            pts, proto = LIAISONS[cible]
            mx, my, vertical = milieu(pts)
            k = deja.get(cible, 0)
            deja[cible] = k + 1
            if vertical:
                my += k * 24
            else:
                mx += k * 24
            s.append(f'<g class="num num-lien"><circle cx="{mx}" cy="{my}" r="10"/><text x="{mx}" y="{my + 4}" text-anchor="middle">{i}</text></g>')
            if k == 0:
                if vertical:
                    s.append(f'<text x="{mx + 14}" y="{my + 4}" class="proto">{esc(proto)}</text>')
                else:
                    s.append(f'<text x="{mx}" y="{my - 14}" class="proto" text-anchor="middle">{esc(proto)}</text>')
        else:
            par_comp.setdefault(cible, []).append((i, genre))
    for comp, nums in par_comp.items():
        x, y, w, h = COMPOSANTS[comp]["box"]
        for k, (i, genre) in enumerate(nums):
            bx = x + w - 12 - (len(nums) - 1 - k) * 23
            s.append(f'<g class="num num-{genre}"><circle cx="{bx}" cy="{y}" r="10"/><text x="{bx}" y="{y + 4}" text-anchor="middle">{i}</text></g>')
    s.append('</svg>')
    return "\n".join(s)


def pipeline_svg(legende, stages, post):
    """Stages en rangees de 4 cases (le bloc post occupe une case), relies en serpentin."""
    bw, gap, x0, hb, pas_y = 200, 26, 10, 108, 168
    par_rangee = 4
    cases = [("stage", st) for st in stages] + ([("post", post)] if post else [])
    rangees = (len(cases) + par_rangee - 1) // par_rangee
    largeur = x0 * 2 + min(len(cases), par_rangee) * bw + (min(len(cases), par_rangee) - 1) * gap
    hauteur = 10 + (rangees - 1) * pas_y + hb + 34
    s = [f'<svg viewBox="0 0 {largeur} {hauteur}" width="{largeur}" class="pipe" role="img" aria-label="{esc(legende)}" xmlns="http://www.w3.org/2000/svg">',
         '<defs><marker id="pf" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="tete-g"/></marker></defs>']
    pos = []
    for i, (genre, contenu) in enumerate(cases):
        r, c = divmod(i, par_rangee)
        x, y = x0 + c * (bw + gap), 10 + r * pas_y
        pos.append((x, y))
        if genre == "post":
            s.append(f'<g class="post"><rect x="{x}" y="{y}" width="{bw}" height="{hb}" rx="10"/>')
            s.append(f'<text x="{x + bw / 2}" y="{y + 24}" class="s-t" text-anchor="middle">post</text>')
            for k, l in enumerate(contenu):
                s.append(f'<text x="{x + bw / 2}" y="{y + 46 + k * 17}" class="s-l" text-anchor="middle">{esc(l)}</text>')
            s.append('</g>')
            continue
        nom, lignes, cond = contenu
        s.append(f'<g class="{"stage cond" if cond else "stage"}"><rect x="{x}" y="{y}" width="{bw}" height="{hb}" rx="10"/>')
        s.append(f'<text x="{x + bw / 2}" y="{y + 24}" class="s-t" text-anchor="middle">{esc(nom)}</text>')
        for k, l in enumerate(lignes):
            s.append(f'<text x="{x + bw / 2}" y="{y + 46 + k * 17}" class="s-l" text-anchor="middle">{esc(l)}</text>')
        if cond:
            s.append(f'<text x="{x + bw / 2}" y="{y + hb + 20}" class="s-c" text-anchor="middle">when : {esc(cond)}</text>')
        s.append('</g>')
    for i in range(len(stages) - 1):
        (xa, ya), (xb, yb) = pos[i], pos[i + 1]
        if ya == yb:
            s.append(f'<line x1="{xa + bw + 2}" y1="{ya + hb / 2}" x2="{xb - 3}" y2="{yb + hb / 2}" class="fleche" marker-end="url(#pf)"/>')
        else:
            ym = ya + hb + 30
            s.append(f'<polyline points="{xa + bw / 2},{ya + hb + 2} {xa + bw / 2},{ym} {xb + bw / 2},{ym} {xb + bw / 2},{yb - 3}" class="fleche" fill="none" marker-end="url(#pf)"/>')
    s.append('</svg>')
    return "\n".join(s)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

CSS = """
:root{--fond:#f7f6f2;--surface:#ffffff;--texte:#1f2328;--doux:#5b636e;--ligne:#d5d8dc;
--orange:#c2571a;--orange-f:#fbe8db;--bleu:#2a62b8;--bleu-f:#e3ecf9;--gris:#8a929b;--gris-f:#f1f2f4;
--vert:#2f7d43;--vert-f:#dff1e3;--rouge:#b3261e;--rouge-f:#f8dedc;--jaune:#9a6b00;--jaune-f:#fbefc9;--code:#eef0f3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--fond:#16181c;--surface:#1f2228;--texte:#e6e8eb;--doux:#a2a9b3;--ligne:#3a3f47;
--orange:#f0904f;--orange-f:#3f2616;--bleu:#7aa7ec;--bleu-f:#1b2a42;--gris:#8d949d;--gris-f:#262a31;
--vert:#6cc283;--vert-f:#1b3323;--rouge:#f08a82;--rouge-f:#3d1e1c;--jaune:#e6be5a;--jaune-f:#3a3016;--code:#2a2e35}}
:root[data-theme="dark"]{--fond:#16181c;--surface:#1f2228;--texte:#e6e8eb;--doux:#a2a9b3;--ligne:#3a3f47;
--orange:#f0904f;--orange-f:#3f2616;--bleu:#7aa7ec;--bleu-f:#1b2a42;--gris:#8d949d;--gris-f:#262a31;
--vert:#6cc283;--vert-f:#1b3323;--rouge:#f08a82;--rouge-f:#3d1e1c;--jaune:#e6be5a;--jaune-f:#3a3016;--code:#2a2e35}
*{box-sizing:border-box}
body{margin:0;background:var(--fond);color:var(--texte);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 64px}
a{color:var(--bleu)}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:.9em}
.fil{font-size:.9rem;color:var(--doux);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
h1{font-size:1.8rem;margin:.3em 0 .1em}
.meta{color:var(--doux);margin:0 0 1.2em}
h2{font-size:1.25rem;margin:2em 0 .6em;padding-bottom:.3em;border-bottom:1px solid var(--ligne)}
.duo{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.carton{background:var(--surface);border:1px solid var(--ligne);border-radius:12px;padding:14px 18px}
.carton h3{margin:0 0 .4em;font-size:1rem}
.carton p{margin:0}
.figure{background:var(--surface);border:1px solid var(--ligne);border-radius:12px;padding:12px;overflow-x:auto}
svg.carte{width:100%;min-width:760px;height:auto;display:block}
svg text{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.reseau{fill:none;stroke:var(--ligne);stroke-width:1.5;stroke-dasharray:6 5}
.reseau-t{fill:var(--doux);font-size:12px}
.poste{fill:none;stroke:var(--ligne);stroke-width:1.5}
.poste-t{fill:var(--doux);font-size:13px;font-weight:600}
.comp rect{stroke-width:1.6}
.comp .c-t{font-size:14px;font-weight:700;fill:var(--texte)}
.comp .c-l{font-size:12px;fill:var(--doux)}
.st-nouveau rect{fill:var(--orange-f);stroke:var(--orange);stroke-width:2.4}
.st-utilise rect{fill:var(--bleu-f);stroke:var(--bleu)}
.st-inchange rect{fill:var(--gris-f);stroke:var(--gris)}
.st-absent rect{fill:none;stroke:var(--gris);stroke-dasharray:5 4}
.st-absent text{opacity:.6}
.lien{fill:none;stroke:var(--orange);stroke-width:2.2}
.lien-ancien{fill:none;stroke:var(--gris);stroke-width:1.2;stroke-dasharray:4 4;opacity:.75}
.tete{fill:var(--orange)} .tete-g{fill:var(--gris)}
.proto{font-size:11.5px;fill:var(--orange);font-weight:600;paint-order:stroke;stroke:var(--surface);stroke-width:4px}
.num circle{stroke:var(--surface);stroke-width:2}
.num text{font-size:12px;font-weight:700;fill:#fff}
.num-lien circle,.num-int circle{fill:var(--orange)}
.num-nav circle{fill:var(--bleu)}
.num-term circle{fill:#3d434b}
.legende{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:.88rem;color:var(--doux);margin:10px 4px 0}
.legende span{display:inline-flex;align-items:center;gap:6px}
.pastille{width:14px;height:14px;border-radius:4px;border:2px solid;display:inline-block}
.p-nouveau{background:var(--orange-f);border-color:var(--orange)}
.p-utilise{background:var(--bleu-f);border-color:var(--bleu)}
.p-inchange{background:var(--gris-f);border-color:var(--gris)}
.pastille.p-absent,.d.p-absent{border-style:dashed;border-color:var(--gris)}
.rond{width:18px;height:18px;border-radius:50%;color:#fff;font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;flex:none}
.r-nav{background:var(--bleu)} .r-term{background:#3d434b} .r-lien,.r-int{background:var(--orange)}
ol.flux{list-style:none;padding:0;margin:14px 0 0;display:grid;gap:6px}
ol.flux li{display:flex;gap:10px;align-items:flex-start;background:var(--surface);border:1px solid var(--ligne);border-radius:8px;padding:7px 12px}
ol.flux .rond{margin-top:3px}
ol.flux .ou{color:var(--doux);font-size:.85rem;white-space:nowrap;min-width:150px}
.etat{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.etat .carton h3{display:flex;justify-content:space-between}
.cat{margin:.6em 0 .2em;font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;color:var(--doux)}
.cat:first-of-type{margin-top:0}
.item{font-size:.9rem;padding:3px 8px;border-radius:6px;margin:2px 0;border-left:3px solid var(--gris);background:var(--gris-f)}
.item.nouveau{border-left-color:var(--orange);background:var(--orange-f)}
.item.modifie{border-left-color:var(--bleu);background:var(--bleu-f)}
.item .tag{font-size:.72rem;font-weight:700;color:var(--orange);margin-left:6px;text-transform:uppercase}
.item.modifie .tag{color:var(--bleu)}
.vide{color:var(--doux);font-style:italic;font-size:.9rem}
ol.deroule{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;counter-reset:d}
ol.deroule li{counter-increment:d;background:var(--surface);border:1px solid var(--ligne);border-radius:10px;padding:10px 12px;position:relative}
ol.deroule li::before{content:counter(d);position:absolute;top:-10px;left:10px;background:var(--texte);color:var(--fond);border-radius:10px;font-size:.75rem;font-weight:700;padding:0 7px}
ol.deroule b{display:block;margin-top:4px}
ol.deroule span{font-size:.88rem;color:var(--doux)}
svg.pipe{height:auto;display:block;max-width:100%}
.pipe .stage rect{fill:var(--bleu-f);stroke:var(--bleu);stroke-width:1.6}
.pipe .stage.cond rect{fill:var(--surface);stroke-dasharray:6 4}
.pipe .post rect{fill:var(--gris-f);stroke:var(--gris);stroke-width:1.4}
.pipe .s-t{font-size:13.5px;font-weight:700;fill:var(--texte)}
.pipe .s-l{font-size:11.5px;fill:var(--doux);font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.pipe .s-c{font-size:11.5px;fill:var(--orange);font-weight:600}
.pipe .fleche{stroke:var(--gris);stroke-width:1.6}
.legende-pipe{font-size:.9rem;color:var(--doux);margin:0 0 6px}
.bande{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch}
.bande .b{flex:1 1 150px;border-radius:10px;padding:10px 12px;border:1.6px solid}
.bande .b b{display:block}
.bande .b span{font-size:.88rem}
.b.ok{background:var(--vert-f);border-color:var(--vert)} .b.ko{background:var(--rouge-f);border-color:var(--rouge)}
.b.warn{background:var(--jaune-f);border-color:var(--jaune)} .b.gris{background:var(--gris-f);border-color:var(--gris)}
table{border-collapse:collapse;width:100%;background:var(--surface);border:1px solid var(--ligne);border-radius:10px;overflow:hidden;font-size:.92rem}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--ligne);vertical-align:top}
th{background:var(--gris-f)}
blockquote p{margin:.3em 0}
blockquote pre{background:var(--code);padding:10px 12px;border-radius:6px;overflow-x:auto;font-size:.85rem}
blockquote{margin:0;background:var(--surface);border:1px solid var(--ligne);border-left:4px solid var(--orange);border-radius:8px;padding:12px 16px}
.nav-bas{display:flex;justify-content:space-between;margin-top:36px;gap:12px;flex-wrap:wrap}
.grille{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.grille a{text-decoration:none;color:inherit}
.grille .carton:hover{border-color:var(--bleu)}
.grille .n{font-size:.8rem;color:var(--doux)}
.matrice td.c{text-align:center}
.d{display:inline-block;width:14px;height:14px;border-radius:4px;border-width:2px;border-style:solid}
@media (max-width:760px){.duo,.etat{grid-template-columns:1fr}h1{font-size:1.45rem}ol.flux .ou{min-width:0}ol.flux li{flex-wrap:wrap}}
"""

OU = {"nav": "navigateur →", "term": "terminal →", "int": "dans", "lien": ""}


def nom_comp(c):
    return COMPOSANTS[c]["titre"]


def page_demo(n, info, et, total):
    d = DEMOS[n]
    titre = f"Démo {n} — {info['titre']}"
    flux_html = []
    for i, f in enumerate(d["flux"], 1):
        genre, cible, txt = f
        if genre == "lien":
            a, b = cible.split(">")
            ou = f"{nom_comp(a).split(' (')[0]} → {nom_comp(b).split(' (')[0]}"
        else:
            ou = f"{OU[genre]} {nom_comp(cible).split(' (')[0]}"
        flux_html.append(f'<li><span class="rond r-{genre}">{i}</span><span class="ou">{esc(ou)}</span><span>{esc(txt)}</span></li>')

    def colonne(etat, marque):
        out = []
        for cat, lib in CATEGORIES:
            items = etat[cat]
            if not items:
                continue
            out.append(f'<div class="cat">{esc(lib)}</div>')
            for cle, txt in items.items():
                cls, tag = "", ""
                if marque and (cat, cle) in et["ajouts"]:
                    cls, tag = " nouveau", '<span class="tag">nouveau</span>'
                elif marque and (cat, cle) in et["modifs"]:
                    cls, tag = " modifie", '<span class="tag">modifié</span>'
                out.append(f'<div class="item{cls}">{esc(txt)}{tag}</div>')
        return "\n".join(out) or '<p class="vide">rien encore : Jenkins n\'est pas démarré</p>'

    pipes = ""
    if d.get("pipelines"):
        blocs = []
        for leg, stages, post in d["pipelines"]:
            blocs.append(f'<p class="legende-pipe">{esc(leg)}</p><div class="figure">{pipeline_svg(leg, stages, post)}</div>')
        pipes = ('<h2>Le pipeline</h2>' + "\n".join(blocs) +
                 '<p class="legende"><span><span class="pastille p-utilise"></span>stage exécuté</span>'
                 '<span><span class="pastille p-absent"></span>stage conditionnel (when)</span>'
                 '<span><span class="pastille p-inchange"></span>bloc post</span></p>')
    bande = ""
    if d.get("bande"):
        leg, cases = d["bande"]
        bande = (f'<h2>{esc(leg)}</h2><div class="bande">' +
                 "".join(f'<div class="b {c}"><b>{esc(t)}</b><span>{esc(x)}</span></div>' for t, c, x in cases) + '</div>')
    roles = ""
    if d.get("roles"):
        roles = ('<h2>Qui peut faire quoi à la fin de la démo</h2><table><tr><th>Compte</th><th>Rôles</th><th>Effet</th></tr>' +
                 "".join(f'<tr><td><code>{esc(u)}</code></td><td>{esc(r)}</td><td>{esc(e)}</td></tr>' for u, r, e in d["roles"]) +
                 '</table>')

    prec = f'<a href="demo-{n - 1:02d}.html">← Démo {n - 1}</a>' if n > 0 else "<span></span>"
    suiv = f'<a href="demo-{n + 1:02d}.html">Démo {n + 1} →</a>' if n < total - 1 else "<span></span>"
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Démo {n} : schéma</title><style>{CSS}</style></head>
<body><main>
<div class="fil"><a href="index.html">Démos Jenkins CI · schémas</a><span>{prec} · {suiv}</span></div>
<h1>{esc(titre)}</h1>
<p class="meta">{md_inline(info['meta'])}</p>

<div class="duo">
<div class="carton"><h3>Pourquoi cette démo</h3><p>{md_inline(info['pourquoi'])}</p></div>
<div class="carton"><h3>Ce qu'elle montre</h3><p>{md_inline(info['montre'])}</p></div>
</div>

<h2>Vue d'ensemble : ce qui bouge dans la stack</h2>
<div class="figure">{carte(n, d, et)}</div>
<p class="legende">
<span><span class="pastille p-nouveau"></span>créé ou configuré dans cette démo</span>
<span><span class="pastille p-utilise"></span>utilisé</span>
<span><span class="pastille p-inchange"></span>inchangé</span>
<span><span class="pastille p-absent"></span>pas encore démarré</span>
<span><span class="rond r-nav">1</span>action dans le navigateur</span>
<span><span class="rond r-term">1</span>commande dans le terminal</span>
<span><span class="rond r-lien">1</span>échange entre conteneurs (en gris pointillé : liaisons des démos précédentes)</span>
</p>
<ol class="flux">
{chr(10).join(flux_html)}
</ol>

<h2>Avant / après : l'état de Jenkins et des services</h2>
<div class="etat">
<div class="carton"><h3>Avant la démo</h3>{colonne(et['avant'], False)}</div>
<div class="carton"><h3>Après la démo</h3>{colonne(et['apres'], True)}</div>
</div>

<h2>Le déroulé</h2>
<ol class="deroule">
{''.join(f'<li><b>{esc(t)}</b><span>{esc(x)}</span></li>' for t, x in d['deroule'])}
</ol>
{pipes}
{bande}
{roles}
<h2>À retenir</h2>
<blockquote>{info['retenir']}</blockquote>

<div class="nav-bas">{prec}<a href="../DEMOS-v2.md">Pas à pas complet : DEMOS-v2.md</a>{suiv}</div>
</main></body></html>
"""


def page_index(infos, tous):
    cartes = []
    for n in sorted(infos):
        cartes.append(f'<a href="demo-{n:02d}.html"><div class="carton"><div class="n">Démo {n}</div><b>{esc(infos[n]["titre"])}</b>'
                      f'<p style="font-size:.88rem;color:var(--doux);margin-top:.4em">{md_inline(infos[n]["meta"])}</p></div></a>')
    comps = ["gitea", "jenkins", "linux1", "mailpit", "nexus", "sonar", "docker", "recette", "prod"]
    lignes = []
    couleurs = {"nouveau": "p-nouveau", "utilise": "p-utilise", "inchange": "p-inchange", "absent": "p-absent"}
    for n in sorted(DEMOS):
        cells = "".join(f'<td class="c"><span class="d {couleurs[statut(c, n, DEMOS[n])]}"></span></td>' for c in comps)
        lignes.append(f'<tr><td><a href="demo-{n:02d}.html">{n}. {esc(infos[n]["titre"])}</a></td>{cells}</tr>')
    entetes = "".join(f'<th class="c">{esc(COMPOSANTS[c]["titre"].split(" (")[0])}</th>' for c in comps)
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Schémas des démos Jenkins</title><style>{CSS}</style></head>
<body><main>
<div class="fil"><span>Kit 1-demos-jenkins-ci</span><a href="../DEMOS-v2.md">DEMOS-v2.md</a></div>
<h1>Démos Jenkins CI : un schéma par démo</h1>
<p class="meta">Chaque page reprend le « pourquoi » de la démo, montre sur la carte de la stack ce qui est créé et ce qui communique, compare l'état de Jenkins avant et après, puis résume le déroulé et le pipeline.</p>
<div class="grille">{''.join(cartes)}</div>
<h2>Ce que chaque démo touche dans la stack</h2>
<div class="figure"><table class="matrice"><tr><th>Démo</th>{entetes}</tr>{''.join(lignes)}</table></div>
<p class="legende">
<span><span class="pastille p-nouveau"></span>créé ou configuré</span>
<span><span class="pastille p-utilise"></span>utilisé</span>
<span><span class="pastille p-inchange"></span>inchangé</span>
<span><span class="pastille p-absent"></span>pas encore démarré</span>
</p>
</main></body></html>
"""


def main():
    infos = lire_demos()
    manquantes = sorted(set(infos) ^ set(DEMOS))
    if manquantes:
        raise SystemExit(f"Démos décrites d'un seul côté (DEMOS-v2.md / générateur) : {manquantes}")
    tous = etats()
    for n in sorted(DEMOS):
        (ICI / f"demo-{n:02d}.html").write_text(page_demo(n, infos[n], tous[n], len(DEMOS)), encoding="utf-8")
    (ICI / "index.html").write_text(page_index(infos, tous), encoding="utf-8")
    print(f"{len(DEMOS)} pages + index.html écrites dans {ICI}")


if __name__ == "__main__":
    main()
