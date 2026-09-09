# ==========================================================================
#  NexusDL 2.0 - Backend Dockerfile
#  Fichier : backend/Dockerfile
#  Description : Image Docker pour le backend FastAPI de NexusDL
#
#  Architecture : Multi-stage
#    - builder : construction et installation des dépendances
#    - production : image finale légère
# ==========================================================================

# ==========================================================================
#  STAGE 1 : BUILDER - Installation des dépendances
# ==========================================================================

FROM python:3.10-slim AS builder

# --- Configuration ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# --- Arguments de build ---
ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown

# --- Métadonnées de l'image ---
LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Backend" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.description="NexusDL 2.0 - Moteur universel de téléchargement de scans" \
      org.opencontainers.image.licenses="GPL-3.0-only"

# --- Dépendances système ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Pour Playwright et la compilation de certains packages
    curl \
    wget \
    gnupg \
    ca-certificates \
    # Utilitaires système
    unzip \
    # Nettoyage
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

# --- Installer Python Poetry (optionnel) ou utiliser pip ---
# Ici on utilise pip directement avec requirements.txt pour simplicité
WORKDIR /build

# Copier uniquement requirements.txt pour profiter du cache Docker
COPY requirements.txt .

# Installer les dépendances Python dans un dossier dédié
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==========================================================================
#  STAGE 2 : PLAYWRIGHT - Installation du navigateur
# ==========================================================================

FROM builder AS playwright-installer

# Installer Playwright et Chromium
RUN pip install --no-cache-dir --prefix=/install playwright==1.41.1 \
    && /install/bin/playwright install chromium \
    && /install/bin/playwright install-deps

# ==========================================================================
#  STAGE 3 : PRODUCTION - Image finale légère
# ==========================================================================

FROM python:3.10-slim AS production

# --- Configuration ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Europe/Paris \
    # Désactiver le prompt de Playwright
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    # Pour éviter les erreurs de mémoire
    PYTHONMALLOC=debug

# --- Variables d'environnement pour l'application ---
ENV ENV=production \
    HOST=0.0.0.0 \
    PORT=8000

# --- Création d'un utilisateur non-root ---
RUN groupadd -r nexusdl && useradd -r -g nexusdl nexusdl \
    && mkdir -p /app/data/downloads /app/data/cache /app/data/temp /app/logs \
    && chown -R nexusdl:nexusdl /app

# --- Métadonnées de l'image (héritées) ---
ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown
LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Backend" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}"

# --- Dépendances système minimales pour le runtime ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Pour Playwright (dépendances de base)
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
    # Utilitaires
    curl \
    # Nettoyage
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

# --- Copier les dépendances depuis le builder ---
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
