# ==========================================================================
#  NexusDL 2.0 - Root Dockerfile (backend + frontend combinés)
#  Fichier : Dockerfile (à la racine du projet)
#  Description : Image unique contenant FastAPI + Vue.js 3 + Nginx
#  Version : 2.0.0
#  Licence : GNU GPL v3.0
# ==========================================================================

# --------------------------------------------------------------------------
#  STAGE 1 : BUILDER — Backend Python
# --------------------------------------------------------------------------

FROM python:3.10-slim AS builder-python

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Dépendances système pour le build
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget gnupg ca-certificates unzip gcc g++ make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Installer les dépendances Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Installer Playwright + Chromium
RUN pip install --no-cache-dir --prefix=/install playwright==1.41.1 \
    && /install/bin/playwright install chromium \
    && /install/bin/playwright install-deps

# --------------------------------------------------------------------------
#  STAGE 2 : BUILDER — Frontend Node.js
# --------------------------------------------------------------------------

FROM node:20-alpine AS builder-node

# ⚠️ IMPORTANT : NODE_ENV=development pour installer les devDependencies
#    (Vite, Rollup, Sass, etc. sont nécessaires au build)
ENV NODE_ENV=development \
    NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false

ARG VERSION=2.0.0
ARG API_BACKEND_URL=/api

WORKDIR /build

# Copier uniquement les fichiers de dépendances (cache Docker)
COPY frontend/package.json ./
COPY frontend/package-lock.json* ./
COPY frontend/.npmrc* ./

# ✅ Utiliser npm install (pas npm ci, car pas de lock file garanti)
RUN npm install --no-audit --no-fund --no-progress --legacy-peer-deps \
    && npm cache clean --force || true

# Copier le reste du frontend
COPY frontend/ .

# Variables d'environnement pour Vite
ENV VITE_API_BASE=/api \
    VITE_APP_VERSION=${VERSION} \
    VITE_API_BACKEND_URL=${API_BACKEND_URL}

# Build de production
RUN npm run build

# --------------------------------------------------------------------------
#  STAGE 3 : PRODUCTION — Image finale
# --------------------------------------------------------------------------

FROM python:3.10-slim AS production

ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0

LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.description="NexusDL 2.0 - Moteur universel de téléchargement de scans" \
      org.opencontainers.image.licenses="GPL-3.0-only"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Europe/Paris \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    ENV=production \
    HOST=0.0.0.0 \
    PORT=8000

# Installer Nginx + Supervisor + dépendances Playwright runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
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
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Créer l'utilisateur non-root
RUN groupadd -r nexusdl \
    && useradd -r -g nexusdl -d /app -s /sbin/nologin nexusdl \
    && mkdir -p /app/data/downloads /app/data/cache /app/data/temp /app/logs \
    && chown -R nexusdl:nexusdl /app

# Copier les dépendances Python
COPY --from=builder-python /install /usr/local
COPY --from=builder-python /root/.cache/ms-playwright /ms-playwright

# Copier le backend
WORKDIR /app
COPY backend/app ./app

# Copier le .env (optionnel)
COPY .env* ./

# Copier le frontend construit
COPY --from=builder-node /build/dist /var/www/html

# ==========================================================================
#  CONFIGURATION NGINX (inline)
# ==========================================================================

RUN mkdir -p /etc/nginx/conf.d /var/log/nginx /var/cache/nginx && \
    rm -f /etc/nginx/sites-enabled/default && \
    cat > /etc/nginx/conf.d/nexusdl.conf << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    root /var/www/html;
    index index.html;

    client_max_body_size 100M;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss image/svg+xml;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location ~* ^/assets/.*\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable, max-age=31536000";
        access_log off;
        try_files $uri =404;
    }

    location = /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    location ^~ /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        proxy_buffering off;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }
    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host $host;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
    }
    location = /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        access_log off;
    }

    location ^~ /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        proxy_buffering off;
    }

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    error_page 404 /index.html;
}
EOF

# ==========================================================================
#  CONFIGURATION SUPERVISOR (inline)
# ==========================================================================

RUN cat > /etc/supervisor/conf.d/nexusdl.conf << 'EOF'
[supervisord]
nodaemon=true
user=root
logfile=/app/logs/supervisord.log
pidfile=/var/run/supervisord.pid
loglevel=info

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
stopasgroup=true
killasgroup=true
priority=10

[program:nginx]
command=nginx -g "daemon off;"
user=root
autostart=true
autorestart=true
stdout_logfile=/app/logs/nginx-out.log
stderr_logfile=/app/logs/nginx-err.log
redirect_stderr=true
stopasgroup=true
killasgroup=true
priority=20
EOF

# Ajuster les permissions
RUN chown -R nexusdl:nexusdl /app /usr/local /ms-playwright \
    && chmod +x /usr/local/bin/playwright \
    && mkdir -p /var/log/supervisor \
    && chown -R nexusdl:nexusdl /var/log/nginx /var/log/supervisor

# Vérifier la config Nginx
RUN nginx -t

# Exposer le port 80
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -fsS http://localhost/nginx-health || exit 1

# Point d'entrée
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
