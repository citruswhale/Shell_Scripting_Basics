# Multi-Stage Dockerfile
# Stage 1: Build the Go binary
FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod .
COPY server.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o app server.go

# Stage 2: Copy only the compiled binary into a minimal runtime image
FROM alpine:latest

WORKDIR /app
COPY --from=builder /app/app .

EXPOSE 8080

CMD ["./app"]
