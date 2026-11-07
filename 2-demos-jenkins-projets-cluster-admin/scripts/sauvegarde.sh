#!/usr/bin/env bash
# Sauvegarde de JENKINS_HOME (slide 51), adaptee au volume Docker de la formation.
# Usage : JENKINS_TOKEN=<jeton d'API de admin> ./scripts/sauvegarde.sh [repertoire]
set -euo pipefail
JENKINS_URL=${JENKINS_URL:-http://localhost:8080}
AUTH="admin:${JENKINS_TOKEN:?Definir JENKINS_TOKEN (jeton d API du compte admin)}"
VOLUME=${VOLUME:-jenkins-formation_jenkins_home}
DEST=$(cd "${1:-./sauvegardes}" 2>/dev/null || mkdir -p "${1:-./sauvegardes}" && cd "${1:-./sauvegardes}"; pwd)
TS=$(date +%Y%m%d-%H%M%S)

# 1. Mise au repos : plus de nouveaux builds, attente de la fin des builds en cours
curl -sf -X POST -u "$AUTH" "$JENKINS_URL/quietDown" >/dev/null
trap 'curl -sf -X POST -u "$AUTH" "$JENKINS_URL/cancelQuietDown" >/dev/null; echo "Jenkins remis en service"' EXIT
echo "Jenkins en mise au repos, attente de la fin des builds..."
until [ "$(curl -sf -u "$AUTH" "$JENKINS_URL/computer/api/json?tree=busyExecutors" | python3 -c 'import sys,json; print(json.load(sys.stdin)["busyExecutors"])')" = 0 ]; do sleep 5; done

# 2. Archive du volume, sans ce qui se reconstruit (war, caches, workspaces, plugins decompresses, logs)
docker run --rm -v "$VOLUME":/home:ro -v "$DEST":/backup alpine:3.20 \
  tar czf "/backup/jenkins-home-$TS.tgz" \
    --exclude=./war --exclude=./updates --exclude=./caches --exclude=./workspace \
    --exclude='./plugins/*/*' --exclude=./logs -C /home .

# 3. Liste des plugins avec versions (reconstruction possible avec jenkins-plugin-cli)
curl -sfg -u "$AUTH" "$JENKINS_URL/pluginManager/api/json?depth=1&tree=plugins[shortName,version]" \
  | python3 -c 'import sys,json; [print(p["shortName"] + ":" + p["version"]) for p in sorted(json.load(sys.stdin)["plugins"], key=lambda p: p["shortName"])]' \
  > "$DEST/plugins-$TS.txt"

ls -lh "$DEST/jenkins-home-$TS.tgz" "$DEST/plugins-$TS.txt"
