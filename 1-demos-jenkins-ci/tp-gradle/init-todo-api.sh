#!/usr/bin/env bash
# Cree le depot prive formation/todo-api dans Gitea et y pousse le projet du TP.
# Le compte Gitea est celui du kit (cree par ../scripts/init-gitea.sh a la demo 0).
set -euo pipefail
cd "$(dirname "$0")"
set -a; . ../.env; set +a

GITEA="${GITEA_URL:-http://localhost:${GITEA_PORT}}"
AUTH="${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}"
HOSTPORT="${GITEA#http://}"

if ! curl -sf -u "${AUTH}" "${GITEA}/api/v1/user" >/dev/null; then
  echo "Compte ${GITEA_ADMIN_USER} refuse par ${GITEA} : lancer d'abord ../scripts/init-gitea.sh" >&2
  exit 1
fi

if ! curl -sf -u "${AUTH}" "${GITEA}/api/v1/repos/${GITEA_ADMIN_USER}/todo-api" >/dev/null; then
  curl -sf -u "${AUTH}" -H 'Content-Type: application/json' \
    -d '{"name":"todo-api","private":true,"default_branch":"main","description":"API de taches (TP Jenkins Gradle)"}' \
    "${GITEA}/api/v1/user/repos" >/dev/null
  echo "Depot ${GITEA_ADMIN_USER}/todo-api cree (prive)"
fi

# Copie de travail temporaire : le dossier todo-api/ du kit reste intact
WORK=$(mktemp -d)
cp -R todo-api/. "${WORK}/"
cd "${WORK}"
git init -q -b main
git -c core.autocrlf=false add .
# gradlew doit etre executable sur l'agent Linux, meme depuis un poste Windows
git update-index --chmod=+x gradlew
git -c user.name="Formation" -c user.email="${GITEA_ADMIN_EMAIL}" commit -q -m "todo-api : version initiale"
git push -q --force "http://${AUTH}@${HOSTPORT}/${GITEA_ADMIN_USER}/todo-api.git" main
cd - >/dev/null
rm -rf "${WORK}"
echo "Projet pousse : ${GITEA}/${GITEA_ADMIN_USER}/todo-api"
