#!/usr/bin/env bash
# Met la stack dans l'etat "fin de partie 1" a partir d'un Jenkins vierge :
# plugins, administrateur, agent linux-1, outils, credentials, SMTP, settings Nexus,
# depot Gitea library-api, Nexus (mot de passe, role, utilisateur jenkins, releases 1.4.0 et 1.4.1 de library-api).
# Ne remplace pas la partie 1 : il evite seulement de la rejouer avant la partie 2.
set -euo pipefail
cd "$(dirname "$0")/.."
P2=$(pwd)
P1="$P2/../1-demos-jenkins-ci"
ETAT="$P2/scripts/etat"

cd "$P1"
set -a; . ./.env; set +a
./scripts/preparer.sh
docker compose up -d
docker compose up -d nexus
./scripts/init-gitea.sh

echo "== Jenkins : plugins de la partie 1"
until docker exec jenkins test -f /var/jenkins_home/secrets/initialAdminPassword; do sleep 3; done
if docker exec jenkins test -f /var/jenkins_home/etat-partie1.ok; then
  echo "Jenkins deja mis en etat : rien a faire (docker compose down -v pour repartir de zero)"
else
  docker cp "$ETAT/plugins-partie1.txt" jenkins:/tmp/plugins.txt
  docker exec jenkins jenkins-plugin-cli --plugin-download-directory /var/jenkins_home/plugins --plugin-file /tmp/plugins.txt

  echo "== Gitea : jeton d'acces en lecture pour Jenkins"
  TOKEN=$(curl -sf -u "$GITEA_ADMIN_USER:$GITEA_ADMIN_PASSWORD" -H 'Content-Type: application/json' \
    -d "{\"name\":\"jenkins-$(date +%s)\",\"scopes\":[\"read:repository\"]}" \
    "http://localhost:$GITEA_PORT/api/v1/users/$GITEA_ADMIN_USER/tokens" | python3 -c 'import sys,json; print(json.load(sys.stdin)["sha1"])')

  echo "== Jenkins : configuration par init.groovy.d"
  VERSION=$(docker exec jenkins sh -c 'echo $JENKINS_VERSION')
  docker exec jenkins mkdir -p /var/jenkins_home/etat-partie1 /var/jenkins_home/init.groovy.d
  docker cp keys/jenkins_agent jenkins:/var/jenkins_home/etat-partie1/jenkins_agent
  printf '%s' "$TOKEN" > /tmp/etat-gitea-token.$$ && docker cp /tmp/etat-gitea-token.$$ jenkins:/var/jenkins_home/etat-partie1/gitea-token && rm -f /tmp/etat-gitea-token.$$
  docker cp "$ETAT/etat-partie1.groovy" jenkins:/var/jenkins_home/init.groovy.d/etat-partie1.groovy
  # Assistant de premier demarrage considere comme deja passe
  docker exec jenkins sh -c "echo $VERSION > /var/jenkins_home/jenkins.install.UpgradeWizard.state; echo $VERSION > /var/jenkins_home/jenkins.install.InstallUtil.lastExecVersion"
  docker exec -u root jenkins chown -R jenkins:jenkins /var/jenkins_home/etat-partie1 /var/jenkins_home/init.groovy.d
  DEBUT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  docker restart jenkins >/dev/null
  until docker logs --since "$DEBUT" jenkins 2>&1 | grep -q 'Jenkins is fully up and running'; do sleep 3; done
  docker exec jenkins sh -c 'rm -rf /var/jenkins_home/etat-partie1 /var/jenkins_home/init.groovy.d/etat-partie1.groovy'
  if docker logs jenkins 2>&1 | grep -q 'etat-partie1 : configuration appliquee'; then
    docker exec jenkins touch /var/jenkins_home/etat-partie1.ok
  else
    docker logs jenkins 2>&1 | grep -A3 'Failed to run script' | tail -4
    echo "ECHEC de la configuration Jenkins : voir docker logs jenkins" >&2
    exit 1
  fi
fi

echo "== Nexus : mot de passe admin, role deploy-maven, utilisateur jenkins"
until curl -sf http://localhost:$NEXUS_PORT/service/rest/v1/status >/dev/null; do sleep 5; done
NX="http://localhost:$NEXUS_PORT/service/rest/v1"
if docker exec nexus test -f /nexus-data/admin.password; then
  INIT=$(docker exec nexus cat /nexus-data/admin.password)
  curl -sf -u "admin:$INIT" -X PUT -H 'Content-Type: text/plain' -d 'Formation-2026' "$NX/security/users/admin/change-password"
fi
# Un Nexus neuf refuse toute ecriture (403) tant que son contrat de licence n'est pas accepte.
if curl -sf -u admin:Formation-2026 "$NX/system/eula" | grep -q '"accepted" : false'; then
  if [ "${ACCEPTER_EULA_NEXUS:-non}" = "oui" ]; then
    DISCLAIMER=$(curl -sf -u admin:Formation-2026 "$NX/system/eula" | python3 -c 'import sys,json; print(json.load(sys.stdin)["disclaimer"])')
    python3 -c 'import json,sys; print(json.dumps({"accepted": True, "disclaimer": sys.argv[1]}))' "$DISCLAIMER" \
      | curl -sf -u admin:Formation-2026 -H 'Content-Type: application/json' -X POST "$NX/system/eula" -d @-
    echo "Contrat de licence Nexus accepte (ACCEPTER_EULA_NEXUS=oui)"
  else
    echo "Le contrat de licence Nexus Community Edition n'est pas accepte : Nexus refuse les publications." >&2
    echo "Lire https://links.sonatype.com/products/nxrm/ce-eula puis, au choix :" >&2
    echo "  - l'accepter dans l'assistant de http://localhost:$NEXUS_PORT (admin / Formation-2026) et relancer ce script ;" >&2
    echo "  - relancer ce script avec ACCEPTER_EULA_NEXUS=oui ./scripts/etat-partie1.sh" >&2
    exit 1
  fi
fi
curl -s -o /dev/null -u admin:Formation-2026 -H 'Content-Type: application/json' -X POST "$NX/security/roles" -d '{"id":"deploy-maven","name":"deploy-maven","description":"","privileges":["nx-repository-view-maven2-*-add","nx-repository-view-maven2-*-browse","nx-repository-view-maven2-*-edit","nx-repository-view-maven2-*-read"],"roles":[]}'
curl -s -o /dev/null -u admin:Formation-2026 -H 'Content-Type: application/json' -X POST "$NX/security/users" -d '{"userId":"jenkins","firstName":"Jenkins","lastName":"CI","emailAddress":"jenkins@example.com","password":"Jenkins-2026","status":"active","roles":["deploy-maven"]}'

echo "== Nexus : releases 1.4.0 et 1.4.1 de library-api (entree de la demo de promotion)"
SETTINGS=$(mktemp)
cat > "$SETTINGS" <<XML
<settings><servers><server><id>nexus-releases</id><username>jenkins</username><password>Jenkins-2026</password></server></servers></settings>
XML
for V in 1.4.0 1.4.1; do
  if ! curl -sf -o /dev/null -u jenkins:Jenkins-2026 "http://localhost:$NEXUS_PORT/repository/maven-releases/fr/utopios/library-api/$V/library-api-$V.pom"; then
    docker run --rm --network ci-formation -v "$P1/library-api":/src:ro -v "$SETTINGS":/settings.xml:ro -v etat-m2:/root/.m2 \
      maven:3.9-eclipse-temurin-21 sh -c "cp -R /src /tmp/b && cd /tmp/b && mvn -B -ntp -q -s /settings.xml -Drevision=$V -DskipTests deploy"
  fi
done
rm -f "$SETTINGS"

echo "Etat fin de partie 1 pret : http://localhost:$JENKINS_PORT (admin / Formation-2026)"
