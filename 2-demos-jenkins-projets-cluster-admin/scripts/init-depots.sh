#!/usr/bin/env bash
# Cree dans Gitea les depots prives de la partie 2 et y pousse les projets de projets/
# (library-core, library-portal, library-legacy, library-web, jenkins-shared-lib, library-ops).
# Attention : push force. Ne pas relancer en cours de formation (efface les commits faits dans Gitea).
set -euo pipefail
cd "$(dirname "$0")/.."
P2=$(pwd)
set -a; . ../1-demos-jenkins-ci/.env; set +a
GITEA="http://localhost:${GITEA_PORT}"
AUTH="${GITEA_ADMIN_USER}:${GITEA_ADMIN_PASSWORD}"

for REPO in library-core library-portal library-legacy library-web jenkins-shared-lib library-ops; do
  if ! curl -sf -u "$AUTH" "$GITEA/api/v1/repos/$GITEA_ADMIN_USER/$REPO" >/dev/null; then
    curl -sf -u "$AUTH" -H 'Content-Type: application/json' \
      -d "{\"name\":\"$REPO\",\"private\":true,\"default_branch\":\"main\"}" "$GITEA/api/v1/user/repos" >/dev/null
  fi
  WORK=$(mktemp -d)
  cp -R "$P2/projets/$REPO/." "$WORK/"
  (cd "$WORK" && git init -q -b main \
    && git -c user.name=Formation -c user.email="$GITEA_ADMIN_EMAIL" add . \
    && git -c user.name=Formation -c user.email="$GITEA_ADMIN_EMAIL" commit -q -m "$REPO : version initiale" \
    && git push -q --force "http://$AUTH@localhost:$GITEA_PORT/$GITEA_ADMIN_USER/$REPO.git" main)
  rm -rf "$WORK"
  echo "Depot pousse : $GITEA/$GITEA_ADMIN_USER/$REPO"
done
