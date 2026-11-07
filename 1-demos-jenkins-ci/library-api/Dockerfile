FROM eclipse-temurin:21-jre-alpine
ARG JAR
COPY ${JAR} /app/app.jar
EXPOSE 8080
ENTRYPOINT ["java","-jar","/app/app.jar"]
