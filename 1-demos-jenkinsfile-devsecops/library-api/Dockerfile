FROM eclipse-temurin:21-jre-alpine
RUN apk add curl
ADD target/*.jar /app/app.jar
EXPOSE 8080
ENTRYPOINT java -jar /app/app.jar
