# Image d'agent ephemere pour le plugin Docker (slide 31) : agent Jenkins + JDK 21 + Maven
FROM jenkins/agent:jdk21
USER root
ARG MAVEN_VERSION=3.9.16
RUN curl -fsSL https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz \
      | tar -xz -C /opt \
 && ln -s /opt/apache-maven-${MAVEN_VERSION}/bin/mvn /usr/local/bin/mvn
USER jenkins
ENV MAVEN_OPTS="-Dmaven.repo.local=/home/jenkins/.m2/repository"
