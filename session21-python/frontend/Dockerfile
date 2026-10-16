# ---- build stage: compile the React app ----
FROM node:24-alpine AS build
WORKDIR /app

# Copy the lock file too, so npm ci installs exactly the tested versions
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
RUN npm run build

# ---- runtime stage: nginx running as a non-root user on port 8080 ----
FROM nginxinc/nginx-unprivileged:1.30-alpine

# Defaults for docker compose; override them in Kubernetes
ENV BACKEND_UPSTREAM=backend:8000 \
    NGINX_RESOLVER=127.0.0.11

COPY --chown=101:101 nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build --chown=101:101 /app/dist /usr/share/nginx/html

USER 101
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
