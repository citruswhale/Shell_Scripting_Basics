# Docker Hello World Applications

This repository contains simple "Hello World" web applications, each containerized with its own `Dockerfile`, plus a multi-stage build example.

## Folder Structure

```
docker-tasks/
├── nodejs-app/       # Node.js (Express) Hello World
├── python-app/       # Python (Flask) Hello World
├── java-app/         # Java Hello World (built with a multi-stage Dockerfile)
├── Apache-app/       # Static Hello World served via Apache HTTP Server
├── React-app/        # React Hello World (built and served via Nginx)
├── nginx-app/        # Static Hello World served via Nginx
└── multistage-app/   # Go Hello World using a multi-stage Dockerfile (port 8080)
```

---

## Build & Run Instructions

Each app folder is self-contained. From inside a given folder, build and run with:

```bash
docker build -t <image-name> .
docker run -d -p <host-port>:<container-port> --name <container-name> <image-name>
```

### 1. Node.js App

```bash
cd nodejs-app
docker build -t nodejs-hello-world .
docker run -d -p 3000:3000 --name nodejs-container nodejs-hello-world
```
Visit: `http://localhost:3000`

### 2. Python App

```bash
cd python-app
docker build -t python-hello-world .
docker run -d -p 5000:5000 --name python-container python-hello-world
```
Visit: `http://localhost:5000`

### 3. Java App

```bash
cd java-app
docker build -t java-hello-world .
docker run -d -p 8000:8000 --name java-container java-hello-world
```
Visit: `http://localhost:8000`

### 4. Apache App

```bash
cd Apache-app
docker build -t apache-hello-world .
docker run -d -p 8081:80 --name apache-container apache-hello-world
```
Visit: `http://localhost:8081`

### 5. React App

```bash
cd React-app
docker build -t react-hello-world .
docker run -d -p 8082:80 --name react-container react-hello-world
```
Visit: `http://localhost:8082`

### 6. Nginx App

```bash
cd nginx-app
docker build -t nginx-hello-world .
docker run -d -p 8083:80 --name nginx-container nginx-hello-world
```
Visit: `http://localhost:8083`

### 7. Multi-Stage Build App (Go)

```bash
cd multistage-app
docker build -t multistage-hello-world .
docker run -d -p 8080:8080 --name multistage-container multistage-hello-world
```
Visit: `http://localhost:8080` — displays: `Hello World from Docker multi-stage build`

See `multistage-app/README.md` for the full documented walkthrough, including `docker ps` verification.

---

## Verifying Everything Is Running

```bash
docker ps
```

This should list all running containers along with their mapped ports, confirming each app is reachable and serving its Hello World page.

---

## Notes

- `java-app` and `React-app` and `multistage-app` all use **multi-stage Dockerfiles** — a build stage compiles/builds the app, and only the compiled output is copied into a minimal final runtime image, keeping image sizes small.
- Port numbers above are just suggestions for running everything side-by-side on one machine — each container's internal port can also be mapped to any free host port.
- At least three distinct application types (Node.js, Python, Java) are included here, satisfying the "deploy at least 3 different types of applications" requirement.
