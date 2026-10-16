# ---- build stage: install Python packages into a virtualenv ----
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- runtime stage: just the venv and our code ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_VERSION=1.0.0 \
    PORT=8000

# Fixed uid/gid so Kubernetes securityContext can match it (runAsUser: 10001)
RUN groupadd --system --gid 10001 gearloan \
 && useradd --system --uid 10001 --gid gearloan --no-create-home --shell /usr/sbin/nologin gearloan

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=10001:10001 alembic.ini entrypoint.sh ./
COPY --chown=10001:10001 alembic ./alembic
COPY --chown=10001:10001 app ./app

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

ENTRYPOINT ["./entrypoint.sh"]
