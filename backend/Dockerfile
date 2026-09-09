# ==========================================================================
#  NexusDL 2.0 - Backend Dockerfile (pour Render)
#  Fichier : backend/Dockerfile
#  Description : Version optimisée pour Render avec contexte racine
# ==========================================================================

FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget gnupg ca-certificates unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# ✅ CORRECTION : Copier depuis le sous-dossier backend/
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM builder AS playwright-installer
RUN pip install --no-cache-dir --prefix=/install playwright==1.41.1 \
    && /install/bin/playwright install chromium \
    && /install/bin/playwright install-deps

FROM python:3.10-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 \
    libpango-1.0-0 libcairo2 libatspi2.0-0 libx11-6 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libasound2 curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd -r nexusdl && useradd -r -g nexusdl nexusdl \
    && mkdir -p /app/data/downloads /app/data/cache /app/data/temp /app/logs \
    && chown -R nexusdl:nexusdl /app

COPY --from=playwright-installer /install /usr/local
COPY --from=playwright-installer /root/.cache/ms-playwright /ms-playwright

WORKDIR /app

# ✅ CORRECTION : Copier depuis le sous-dossier backend/
COPY backend/app ./app
COPY .env .env

RUN chown -R nexusdl:nexusdl /app /usr/local /ms-playwright \
    && chmod +x /usr/local/bin/playwright

USER nexusdl

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
