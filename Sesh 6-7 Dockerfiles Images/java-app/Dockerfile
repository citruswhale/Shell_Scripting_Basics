# Java Hello World Dockerfile (multi-stage: compile then run)
FROM eclipse-temurin:21-jdk-alpine AS build

WORKDIR /app
COPY HelloWorld.java .
RUN javac HelloWorld.java

FROM eclipse-temurin:21-jre-alpine

WORKDIR /app
COPY --from=build /app/HelloWorld.class .

EXPOSE 8000

CMD ["java", "HelloWorld"]
