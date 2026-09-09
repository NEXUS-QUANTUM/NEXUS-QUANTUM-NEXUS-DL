# ==========================================================================
#  NexusDL 2.0 - Root Dockerfile (Combined Image)
#  Fichier : Dockerfile
#  Description : Image Docker unique contenant le backend FastAPI et le
#                frontend Vue.js 3 avec Nginx, pour un déploiement simplifié.
#  Architecture : Multi-stage (builder-python, builder-node, production)
#  Version : 2.0.0
# ==========================================================================

# --------------------------------------------------------------------------
#  STAGE 1 : BUILDER - Python (backend)
# --------------------------------------------------------------------------

FROM python:3.10-slim AS builder-python

# Configuration de l'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Arguments de build
ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0

# Métadonnées
LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL (Combined)" \
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

# Arguments de build
ARG VERSION=2.0.0
ARG API_BACKEND_URL=http://localhost:8000

WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --only=production --no-audit --no-fund --no-progress && npm cache clean --force

COPY frontend/ .
ENV VITE_API_BASE=/api \
    VITE_APP_VERSION=${VERSION} \
    VITE_API_BACKEND_URL=${API_BACKEND_URL}
RUN npm run build

# --------------------------------------------------------------------------
#  STAGE 3 : PRODUCTION - Image finale avec Python + Nginx
# --------------------------------------------------------------------------

FROM python:3.10-slim AS production

# Arguments de build
ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0

# Métadonnées
LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.description="NexusDL 2.0 - Moteur universel de téléchargement de scans (image combinée)" \
      org.opencontainers.image.licenses="GPL-3.0-only"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Europe/Paris \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    ENV=production \
    HOST=0.0.0.0 \
    PORT=8000

# Installation de Nginx et supervisord
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Création d'un utilisateur non-root
RUN groupadd -r nexusdl && useradd -r -g nexusdl nexusdl \
    && mkdir -p /app/data/downloads /app/data/cache /app/data/temp /app/logs \
    && chown -R nexusdl:nexusdl /app

# Copier les dépendances Python
COPY --from=builder-python /install /usr/local
COPY --from=builder-python /root/.cache/ms-playwright /ms-playwright

# Copier le backend
WORKDIR /app
COPY backend/app ./app
COPY .env .env

# Copier le frontend construit
COPY --from=builder-node /build/dist /var/www/html

# Configuration Nginx
RUN rm /etc/nginx/sites-enabled/default
COPY <<EOF /etc/nginx/sites-available/nexusdl
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    root /var/www/html;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        proxy_buffering off;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host \$host;
    }
    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host \$host;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host \$host;
    }
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        proxy_buffering off;
    }

    location /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
EOF
RUN ln -s /etc/nginx/sites-available/nexusdl /etc/nginx/sites-enabled/ \
    && rm -f /etc/nginx/sites-enabled/default \
    && nginx -t

# Configuration supervisord
COPY <<EOF /etc/supervisor/conf.d/nexusdl.conf
[supervisord]
nodaemon=true
user=nexusdl
logfile=/app/logs/supervisord.log
pidfile=/var/run/supervisord.pid

[program:backend]
command=uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/app
environment=PYTHONPATH="/app",TZ="Europe/Paris"
user=nexusdl
autostart=true
autorestart=true
stdout_logfile=/app/logs/backend-out.log
stderr_logfile=/app/logs/backend-err.log
redirect_stderr=true

[program:nginx]
command=nginx -g "daemon off;"
user=root
autostart=true
autorestart=true
stdout_logfile=/app/logs/nginx-out.log
stderr_logfile=/app/logs/nginx-err.log
redirect_stderr=true
EOF

# Permissions finales
RUN chown -R nexusdl:nexusdl /app /var/www/html /ms-playwright /usr/local \
    && chmod +x /usr/local/bin/playwright \
    && mkdir -p /var/log/nginx /var/log/supervisor \
    && chown -R nexusdl:nexusdl /var/log/nginx /var/log/supervisor /var/run

# Utilisateur non-root
USER nexusdl

# Ports exposés
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost/nginx-health || exit 1

# Point d'entrée
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
