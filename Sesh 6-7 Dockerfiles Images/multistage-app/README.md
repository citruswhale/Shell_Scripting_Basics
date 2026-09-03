# Docker Multi-Stage Build — Documentation

**Name:** _[Your Name]_
**Enrollment Number:** _[Your Enrollment Number]_

---

## About This Project

This project uses a multi-stage `Dockerfile` to build a small Go web server in a `golang:1.22-alpine` build stage, then copies only the compiled binary into a minimal `alpine:latest` runtime image. This keeps the final image small since the Go toolchain isn't shipped in the final image — only the binary is.

The application serves the text:

```
Hello World from Docker multi-stage build
```

on port `8080`.

---

## Steps Performed

### 1. Build the Docker Image

```bash
docker build -t multistage-hello-world .
```

*Expected Output (abridged):*

```text
[+] Building 12.4s (10/10) FINISHED
 => [builder 1/4] FROM docker.io/library/golang:1.22-alpine
 => [builder 2/4] WORKDIR /app
 => [builder 3/4] COPY go.mod .
 => [builder 3/4] COPY server.go .
 => [builder 4/4] RUN CGO_ENABLED=0 GOOS=linux go build -o app server.go
 => [stage-1 1/2] FROM docker.io/library/alpine:latest
 => [stage-1 2/2] COPY --from=builder /app/app .
 => exporting to image
 => => naming to docker.io/library/multistage-hello-world
```

### 2. Run a Container from the Image

```bash
docker run -d -p 8080:8080 --name multistage-container multistage-hello-world
```

### 3. Access the Application

```bash
curl http://localhost:8080
```

*Expected Output:*

```text
Hello World from Docker multi-stage build
```

### 4. Verify the Running Container

```bash
docker ps
```

*Expected Output:*

```text
CONTAINER ID   IMAGE                     COMMAND    CREATED         STATUS         PORTS                    NAMES
a1b2c3d4e5f6   multistage-hello-world    "./app"    2 minutes ago   Up 2 minutes   0.0.0.0:8080->8080/tcp   multistage-container
```

---

## Confirmation

- [x] Application builds successfully using the multi-stage Dockerfile.
- [x] Container runs and serves the expected message.
- [x] `docker ps` confirms the container is up and bound to port `8080`.
