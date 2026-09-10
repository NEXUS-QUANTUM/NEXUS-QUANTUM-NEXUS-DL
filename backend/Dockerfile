# ==========================================================================
#  NexusDL 2.0 - Backend Dockerfile (version complète et corrigée)
#  Fichier : backend/Dockerfile
#  Description : Image Docker pour le backend FastAPI seul, prête pour Render
#  Version : 2.0.0
#  Architecture : Multi-stage (builder + playwright + production)
# ==========================================================================

# --------------------------------------------------------------------------
#  STAGE 1 : BUILDER - Installation des dépendances Python
# --------------------------------------------------------------------------

FROM python:3.10-slim AS builder

# --- Configuration de l'environnement ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# --- Arguments de build ---
ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown

# --- Métadonnées de l'image (builder) ---
LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Backend (Builder)" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.description="NexusDL 2.0 - Backend FastAPI (builder stage)" \
      org.opencontainers.image.licenses="GPL-3.0-only"

# --- Installation des dépendances système nécessaires au build ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

# --- Définir le répertoire de travail ---
WORKDIR /build

# --- Copier uniquement requirements.txt (pour le cache Docker) ---
COPY requirements.txt .

# --- Installer les dépendances Python dans /install ---
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --------------------------------------------------------------------------
#  STAGE 2 : PLAYWRIGHT - Installation du navigateur Chromium
# --------------------------------------------------------------------------

FROM builder AS playwright-installer

# --- Installer Playwright et Chromium ---
RUN pip install --no-cache-dir --prefix=/install playwright==1.41.1 \
    && /install/bin/playwright install chromium \
    && /install/bin/playwright install-deps

# --------------------------------------------------------------------------
#  STAGE 3 : PRODUCTION - Image finale légère et sécurisée
# --------------------------------------------------------------------------

FROM python:3.10-slim AS production

# --- Configuration de l'environnement ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Europe/Paris \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    ENV=production \
    HOST=0.0.0.0 \
    PORT=8000

# --- Arguments de build ---
ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown

# --- Métadonnées de l'image finale ---
LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Backend" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.description="NexusDL 2.0 - Backend FastAPI (production)" \
      org.opencontainers.image.licenses="GPL-3.0-only"

# --- Création d'un utilisateur non-root ---
RUN groupadd -r nexusdl && useradd -r -g nexusdl nexusdl \
    && mkdir -p /app/data/downloads /app/data/cache /app/data/temp /app/logs \
    && chown -R nexusdl:nexusdl /app

# --- Installation des dépendances système minimales pour le runtime ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
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
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

# --- Copier les dépendances Python depuis le builder ---
COPY --from=playwright-installer /install /usr/local
COPY --from=playwright-installer /root/.cache/ms-playwright /ms-playwright

# --- Copier le code source de l'application ---
WORKDIR /app
COPY ./app ./app
COPY .env .env

# --- Ajuster les permissions ---
RUN chown -R nexusdl:nexusdl /app /usr/local /ms-playwright \
    && chmod +x /usr/local/bin/playwright

# --- Utilisateur non-root ---
USER nexusdl

# --- Exposer le port ---
EXPOSE 8000

# --- Healthcheck ---
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=45s \
            --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# --- Point d'entrée ---
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
