#!/usr/bin/env bash
# Cree dans le Gitea de la partie 1 le depot prive formation/library-api-devsecops
# et y pousse le projet library-api/ du kit (sans Jenkinsfile : il s'ecrit pendant les demos).
# Attention : push force. Ne pas relancer en cours de session (efface les commits faits dans Gitea).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ../1-demos-jenkins-ci/.env; set +a

GITEA="http://localhost:${GITEA_PORT}"
AUTH="${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}"
DEPOT=library-api-devsecops

if ! curl -sf -u "${AUTH}" "${GITEA}/api/v1/user" >/dev/null; then
  echo "Gitea ne repond pas sur ${GITEA} avec le compte ${GITEA_ADMIN_USER} : la stack de la partie 1 tourne-t-elle ?" >&2
  exit 1
fi

if ! curl -sf -u "${AUTH}" "${GITEA}/api/v1/repos/${GITEA_ADMIN_USER}/${DEPOT}" >/dev/null; then
  curl -sf -u "${AUTH}" -H 'Content-Type: application/json' \
    -d "{\"name\":\"${DEPOT}\",\"private\":true,\"default_branch\":\"main\",\"description\":\"library-api : demos Jenkinsfile DevSecOps\"}" \
    "${GITEA}/api/v1/user/repos" >/dev/null
  echo "Depot ${GITEA_ADMIN_USER}/${DEPOT} cree (prive)"
fi

# Copie de travail temporaire : le dossier library-api/ du kit reste intact
WORK=$(mktemp -d)
cp -R library-api/. "${WORK}/"
cd "${WORK}"
git init -q -b main
git -c user.name="Formation" -c user.email="${GITEA_ADMIN_EMAIL}" add .
git -c user.name="Formation" -c user.email="${GITEA_ADMIN_EMAIL}" commit -q -m "library-api : version initiale (demos DevSecOps)"
git push -q --force "http://${AUTH}@localhost:${GITEA_PORT}/${GITEA_ADMIN_USER}/${DEPOT}.git" main
cd - >/dev/null
rm -rf "${WORK}"
echo "Projet pousse : ${GITEA}/${GITEA_ADMIN_USER}/${DEPOT}"
