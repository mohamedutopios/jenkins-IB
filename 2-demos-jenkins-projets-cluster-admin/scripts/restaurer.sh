#!/usr/bin/env bash
# Restaure une archive de sauvegarde dans un NOUVEAU volume et demarre un second Jenkins
# (jenkins-restaure, http://localhost:8085) pour verifier la sauvegarde sans toucher a l'original.
# Usage : ./scripts/restaurer.sh sauvegardes/jenkins-home-AAAAMMJJ-HHMMSS.tgz
set -euo pipefail
ARCHIVE=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
VOLUME=jenkins-formation_jenkins_home_restaure
IMAGE=$(docker inspect --format '{{.Config.Image}}' jenkins)

docker rm -f jenkins-restaure >/dev/null 2>&1 || true
docker volume rm "$VOLUME" >/dev/null 2>&1 || true
docker volume create "$VOLUME" >/dev/null
docker run --rm -v "$VOLUME":/home -v "$ARCHIVE":/archive.tgz:ro alpine:3.20 \
  sh -c 'tar xzf /archive.tgz -C /home && chown -R 1000:1000 /home'
docker run -d --name jenkins-restaure -p 8085:8080 -v "$VOLUME":/var/jenkins_home "$IMAGE" >/dev/null
echo "Demarrage de jenkins-restaure..."
until docker logs jenkins-restaure 2>&1 | grep -q 'Jenkins is fully up and running'; do sleep 3; done
echo "Jenkins restaure : http://localhost:8085 (memes comptes que l'original)"
