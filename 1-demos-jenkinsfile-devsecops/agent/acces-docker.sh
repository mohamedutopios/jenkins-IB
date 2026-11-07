#!/bin/bash
# Donne a l'utilisateur jenkins l'acces a la socket Docker montee depuis l'hote.
# Les sessions SSH ouvertes par le controller ne recoivent pas le "group_add" de Compose :
# il faut que jenkins appartienne au groupe proprietaire de la socket dans /etc/group.
set -e
SOCK=/var/run/docker.sock
if [ -S "$SOCK" ]; then
  GID=$(stat -c %g "$SOCK")
  GROUP=$(getent group "$GID" | cut -d: -f1)
  if [ -z "$GROUP" ]; then
    groupadd -g "$GID" docker-hote
    GROUP=docker-hote
  fi
  usermod -aG "$GROUP" jenkins
fi
exec setup-sshd "$@"
