#!/usr/bin/env bash
# Genere la paire de cles SSH controller -> agent et la reporte dans .env
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f keys/jenkins_agent ]; then
  ssh-keygen -t ed25519 -N "" -C "jenkins-controller" -f keys/jenkins_agent >/dev/null
  echo "Cle generee : keys/jenkins_agent (privee) et keys/jenkins_agent.pub"
fi

PUB=$(cat keys/jenkins_agent.pub)
# Remplace la ligne JENKINS_AGENT_SSH_PUBKEY= (sed portable macOS / Linux)
grep -v '^JENKINS_AGENT_SSH_PUBKEY=' .env > .env.tmp
echo "JENKINS_AGENT_SSH_PUBKEY=\"${PUB}\"" >> .env.tmp
mv .env.tmp .env
echo "Cle publique reportee dans .env"
