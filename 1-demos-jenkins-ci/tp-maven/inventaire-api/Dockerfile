# Image de l'application : le JAR est construit par Jenkins (mvn package), puis copie ici
FROM eclipse-temurin:21-jre-alpine
ARG JAR
COPY ${JAR} /app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar"]
