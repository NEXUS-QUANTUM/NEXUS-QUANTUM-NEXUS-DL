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

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget gnupg ca-certificates unzip gcc g++ make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN PYTHONPATH=/install/lib/python3.10/site-packages \
    python -m playwright install chromium

# --------------------------------------------------------------------------
#  STAGE 2 : BUILDER — Frontend Node.js
# --------------------------------------------------------------------------

FROM node:20-alpine AS builder-node

ENV NODE_ENV=development \
    NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false

ARG VERSION=2.0.0
ARG API_BACKEND_URL=/api

WORKDIR /build

COPY frontend/package.json ./
COPY frontend/package-lock.json* ./
COPY frontend/.npmrc* ./

RUN npm install --no-audit --no-fund --no-progress --legacy-peer-deps \
    && npm cache clean --force || true

COPY frontend/ .

ENV VITE_API_BASE=/api \
    VITE_APP_VERSION=${VERSION} \
    VITE_API_BACKEND_URL=${API_BACKEND_URL}

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

RUN groupadd -r nexusdl \
    && useradd -r -g nexusdl -d /app -s /sbin/nologin nexusdl \
    && mkdir -p /app/data/downloads /app/data/cache /app/data/temp /app/logs \
    && chown -R nexusdl:nexusdl /app

COPY --from=builder-python /install /usr/local
COPY --from=builder-python /ms-playwright /ms-playwright

WORKDIR /app
COPY backend/app ./app

COPY .env* ./

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
#  CONFIGURATION SUPERVISOR (inline, conservée pour référence)
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
redirect_stderr=true
stopasgroup=true
killasgroup=true
priority=20
EOF

RUN chown -R nexusdl:nexusdl /app /usr/local /ms-playwright \
    && mkdir -p /var/log/supervisor \
    && chown -R nexusdl:nexusdl /var/log/nginx /var/log/supervisor

RUN nginx -t

EXPOSE 8000

# ⚠️ TEMPORAIRE — MODE DEBUG
# On court-circuite supervisor pour voir la stacktrace dans les logs Render.
# Uvicorn démarre directement et toute erreur Python remonte dans stdout.
# Une fois le bug identifié, on remettra la ligne CMD supervisor d'origine.
CMD ["sh", "-c", "cd /app && uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug"]
