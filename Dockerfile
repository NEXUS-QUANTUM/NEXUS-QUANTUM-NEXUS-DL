# ==========================================================================
#  NexusDL 2.0 - Dockerfile (version robuste avec fichiers de config)
#  Fichier : Dockerfile
#  Description : Image unique backend + frontend pour Render.com
#  Version : 2.0.0
# ==========================================================================

# --------------------------------------------------------------------------
#  STAGE 1 : BUILDER - Python (backend)
# --------------------------------------------------------------------------

FROM python:3.10-slim AS builder-python

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0

LABEL maintainer="NexusDL Community <drxenon487@gmail.com>" \
      org.opencontainers.image.title="NexusDL" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}"

# Dépendances système pour Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    unzip \
    libnss3 \
    libatk-bridge2.0-0 \
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
    && pip install --no-cache-dir --prefix=/install playwright==1.41.1 \
    && /install/bin/playwright install chromium \
    && /install/bin/playwright install-deps

# --------------------------------------------------------------------------
#  STAGE 2 : BUILDER - Node.js (frontend)
# --------------------------------------------------------------------------

FROM node:20-alpine AS builder-node

ARG VERSION=2.0.0
ARG API_BACKEND_URL=http://localhost:8000

WORKDIR /build
COPY frontend/package*.json ./

# ✅ Utilisation de npm install (pas de package-lock.json)
RUN npm install --omit=dev --no-audit --no-fund --no-progress && npm cache clean --force

COPY frontend/ .
ENV VITE_API_BASE=/api \
    VITE_APP_VERSION=${VERSION} \
    VITE_API_BACKEND_URL=${API_BACKEND_URL}
RUN npm run build

# --------------------------------------------------------------------------
#  STAGE 3 : PRODUCTION - Image finale
# --------------------------------------------------------------------------

FROM python:3.10-slim AS production

ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0

LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Europe/Paris \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    ENV=production \
    HOST=0.0.0.0 \
    PORT=8000

# Installation de Nginx, Supervisor et outils
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur non-root
RUN groupadd -r nexusdl && useradd -r -g nexusdl nexusdl \
    && mkdir -p /app/data/downloads /app/data/cache /app/data/temp /app/logs \
    && chown -R nexusdl:nexusdl /app

# Copie des dépendances Python
COPY --from=builder-python /install /usr/local
COPY --from=builder-python /root/.cache/ms-playwright /ms-playwright

# Copie du backend
WORKDIR /app
COPY backend/app ./app
COPY .env .env

# Copie du frontend construit
COPY --from=builder-node /build/dist /var/www/html

# Copie des fichiers de configuration Nginx et Supervisor
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/nexusdl.conf

# Suppression du site par défaut et vérification Nginx
RUN rm -f /etc/nginx/sites-enabled/default && nginx -t

# Permissions finales
RUN chown -R nexusdl:nexusdl /app /var/www/html /ms-playwright /usr/local \
    && chmod +x /usr/local/bin/playwright \
    && mkdir -p /var/log/nginx /var/log/supervisor \
    && chown -R nexusdl:nexusdl /var/log/nginx /var/log/supervisor /var/run

USER nexusdl

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost/nginx-health || exit 1

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
