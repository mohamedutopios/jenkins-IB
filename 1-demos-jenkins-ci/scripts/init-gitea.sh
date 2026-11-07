#!/usr/bin/env bash
# Cree le compte Gitea, le depot prive formation/library-api et y pousse le projet
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a

GITEA="http://localhost:${GITEA_PORT}"
AUTH="${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}"

echo "Attente de Gitea sur ${GITEA}..."
until curl -sf "${GITEA}/api/healthz" >/dev/null; do sleep 2; done

if ! curl -sf -u "${AUTH}" "${GITEA}/api/v1/user" >/dev/null; then
  docker exec -u git gitea gitea admin user create --admin \
    --username "${GITEA_ADMIN_USER}" --password "${GITEA_ADMIN_PASSWORD}" \
    --email "${GITEA_ADMIN_EMAIL}" --must-change-password=false
fi

# Interface Gitea en anglais pour ce compte (les libelles de DEMOS.md sont en anglais)
curl -sf -u "${AUTH}" -X PATCH -H 'Content-Type: application/json' \
  -d '{"language":"en-US"}' "${GITEA}/api/v1/user/settings" >/dev/null

if ! curl -sf -u "${AUTH}" "${GITEA}/api/v1/repos/${GITEA_ADMIN_USER}/library-api" >/dev/null; then
  curl -sf -u "${AUTH}" -H 'Content-Type: application/json' \
    -d '{"name":"library-api","private":true,"default_branch":"main","description":"API REST de gestion de bibliotheque (fil rouge Jenkins)"}' \
    "${GITEA}/api/v1/user/repos" >/dev/null
  echo "Depot ${GITEA_ADMIN_USER}/library-api cree (prive)"
fi

# Copie de travail temporaire : le dossier library-api/ du kit reste intact
WORK=$(mktemp -d)
cp -R library-api/. "${WORK}/"
cd "${WORK}"
git init -q -b main
git -c user.name="Formation" -c user.email="${GITEA_ADMIN_EMAIL}" add .
git -c user.name="Formation" -c user.email="${GITEA_ADMIN_EMAIL}" commit -q -m "library-api : version initiale"
git push -q --force "http://${AUTH}@localhost:${GITEA_PORT}/${GITEA_ADMIN_USER}/library-api.git" main
cd - >/dev/null
rm -rf "${WORK}"
echo "Projet pousse : ${GITEA}/${GITEA_ADMIN_USER}/library-api"
