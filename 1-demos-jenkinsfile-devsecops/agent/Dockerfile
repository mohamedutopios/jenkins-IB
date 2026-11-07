# Agent SSH "linux-1" outille pour la chaine DevSecOps :
# JDK 21 + Git (image officielle), client Docker, Trivy, Gitleaks, Hadolint, Semgrep.
# Les versions sont figees : les sorties citees dans DEMOS.md correspondent a celles-ci.
FROM aquasec/trivy:0.76.2 AS trivy
FROM zricethezav/gitleaks:v8.30.1 AS gitleaks
FROM hadolint/hadolint:v2.15.1 AS hadolint
FROM docker:27-cli AS docker

FROM jenkins/ssh-agent:jdk21

COPY --from=docker /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker /usr/local/libexec/docker/cli-plugins/docker-buildx /usr/local/libexec/docker/cli-plugins/docker-buildx
COPY --from=trivy /usr/local/bin/trivy /usr/local/bin/trivy
COPY --from=gitleaks /usr/bin/gitleaks /usr/local/bin/gitleaks
COPY --from=hadolint /bin/hadolint /usr/local/bin/hadolint

# Semgrep (SAST) est un outil Python : installe dans un environnement virtuel dedie
ARG SEMGREP_VERSION=1.184.0
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl python3 python3-venv \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv /opt/semgrep \
 && /opt/semgrep/bin/pip install --no-cache-dir "semgrep==${SEMGREP_VERSION}" \
 && ln -s /opt/semgrep/bin/semgrep /usr/local/bin/semgrep \
 && mkdir -p /home/jenkins/.m2 /home/jenkins/.cache \
 && chown -R jenkins:jenkins /home/jenkins/.m2 /home/jenkins/.cache

# Au demarrage : ajoute jenkins au groupe de la socket Docker, puis lance sshd
COPY acces-docker.sh /usr/local/bin/acces-docker.sh
# Retire d'eventuels CRLF (kit copie sous Windows sans Git) : sinon "exec ...: no such file or directory"
RUN sed -i 's/\r$//' /usr/local/bin/acces-docker.sh \
 && chmod +x /usr/local/bin/acces-docker.sh
ENTRYPOINT ["/usr/local/bin/acces-docker.sh"]
