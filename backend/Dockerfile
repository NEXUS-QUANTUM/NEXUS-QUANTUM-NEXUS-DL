# ==========================================================================
#  NexusDL 2.0 - Backend Dockerfile
#  Fichier : backend/Dockerfile
#  Description : Image Docker pour le backend FastAPI de NexusDL
#  Version : 2.0.0
#  Architecture : Multi-stage (builder + playwright + production)
#  Licence : GNU GPL v3.0
# ==========================================================================

# --------------------------------------------------------------------------
#  STAGE 1 : BUILDER — Installation des dépendances Python
# --------------------------------------------------------------------------

FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    DEBIAN_FRONTEND=noninteractive

ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown

LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Backend (Builder)" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.description="NexusDL 2.0 - Backend FastAPI (builder)" \
      org.opencontainers.image.licenses="GPL-3.0-only"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    unzip \
    gcc \
    g++ \
    make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --------------------------------------------------------------------------
#  STAGE 2 : PLAYWRIGHT — Téléchargement de Chromium
# --------------------------------------------------------------------------

FROM builder AS playwright-installer

# Playwright est déjà dans requirements.txt → présent dans /install.
# On utilise `python -m playwright` car le binaire /install/bin/playwright
# a un shebang qui pointe vers le python système, lequel ne voit pas
# /install/lib/python3.10/site-packages (piège classique de `pip --prefix`).
# PLAYWRIGHT_BROWSERS_PATH fixe le chemin des navigateurs, copié ensuite.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN PYTHONPATH=/install/lib/python3.10/site-packages \
    python -m playwright install chromium

# --------------------------------------------------------------------------
#  STAGE 3 : PRODUCTION — Image finale
# --------------------------------------------------------------------------

FROM python:3.10-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Europe/Paris \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    ENV=production \
    HOST=0.0.0.0 \
    PORT=8000 \
    DEBIAN_FRONTEND=noninteractive

ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown

LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Backend" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.description="NexusDL 2.0 - Backend FastAPI (production)" \
      org.opencontainers.image.licenses="GPL-3.0-only" \
      org.opencontainers.image.source="https://github.com/nexus-dl/nexus-dl"

RUN groupadd -r nexusdl \
    && useradd -r -g nexusdl -d /app -s /sbin/nologin nexusdl \
    && mkdir -p /app/data/downloads /app/data/cache /app/data/temp /app/logs \
    && chown -R nexusdl:nexusdl /app

# Dépendances runtime Chromium (liste explicite — inclut nspr4/atk1.0/cups2
# qui manquaient dans la version initiale et font planter Chromium).
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libasound2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

COPY --from=playwright-installer /install /usr/local
COPY --from=playwright-installer /ms-playwright /ms-playwright

WORKDIR /app
COPY --chown=nexusdl:nexusdl ./app ./app

# NOTE : la ligne `COPY .env* ./` a été retirée car elle fait échouer le
# build quand aucun fichier .env n'existe à la racine. Les variables
# d'environnement sont fournies par l'orchestrateur (docker-compose, Render…).

RUN chown -R nexusdl:nexusdl /app /usr/local /ms-playwright

USER nexusdl

EXPOSE 8000

HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=60s \
            --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Mode debug temporaire : uvicorn directement, sans supervisor.
# Pour repasser en prod, remplacer par :
#   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# ou par supervisor si tu en ajoutes un.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level debug"]
