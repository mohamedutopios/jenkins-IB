# Agent SSH "linux-1" (slide 46) : JDK 21 + Git (image officielle) + client Docker
FROM jenkins/ssh-agent:jdk21

# Client Docker et buildx, utilises par la demo de deploiement (socket de l'hote montee)
COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:27-cli /usr/local/libexec/docker/cli-plugins/docker-buildx /usr/local/libexec/docker/cli-plugins/docker-buildx

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /home/jenkins/.m2 \
 && chown -R jenkins:jenkins /home/jenkins/.m2

# Au demarrage : ajoute jenkins au groupe de la socket Docker, puis lance sshd
COPY acces-docker.sh /usr/local/bin/acces-docker.sh
# Retire d'eventuels CRLF (kit copie sous Windows sans Git) : sinon "exec ...: no such file or directory"
RUN sed -i 's/\r$//' /usr/local/bin/acces-docker.sh \
 && chmod +x /usr/local/bin/acces-docker.sh
ENTRYPOINT ["/usr/local/bin/acces-docker.sh"]
