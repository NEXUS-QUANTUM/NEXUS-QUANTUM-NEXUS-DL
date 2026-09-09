# ==========================================================================
#  NexusDL 2.0 - Dockerfile (corrigé, sans dépendances externes)
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

LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget gnupg ca-certificates unzip \
    libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 \
    libpango-1.0-0 libcairo2 libatspi2.0-0 libx11-6 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libasound2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

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
    nginx supervisor curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

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

# ----------------------------------------------------------------
# ✅ CRÉATION DES FICHIERS DE CONFIGURATION DIRECTEMENT DANS LE DOCKERFILE
# ----------------------------------------------------------------

# Création de nginx.conf
RUN echo 'worker_processes auto;' > /etc/nginx/nginx.conf && \
    echo 'error_log /var/log/nginx/error.log warn;' >> /etc/nginx/nginx.conf && \
    echo 'pid /var/run/nginx.pid;' >> /etc/nginx/nginx.conf && \
    echo '' >> /etc/nginx/nginx.conf && \
    echo 'events {' >> /etc/nginx/nginx.conf && \
    echo '    worker_connections 1024;' >> /etc/nginx/nginx.conf && \
    echo '    multi_accept on;' >> /etc/nginx/nginx.conf && \
    echo '}' >> /etc/nginx/nginx.conf && \
    echo '' >> /etc/nginx/nginx.conf && \
    echo 'http {' >> /etc/nginx/nginx.conf && \
    echo '    include /etc/nginx/mime.types;' >> /etc/nginx/nginx.conf && \
    echo '    default_type application/octet-stream;' >> /etc/nginx/nginx.conf && \
    echo '    sendfile on;' >> /etc/nginx/nginx.conf && \
    echo '    tcp_nopush on;' >> /etc/nginx/nginx.conf && \
    echo '    tcp_nodelay on;' >> /etc/nginx/nginx.conf && \
    echo '    keepalive_timeout 65;' >> /etc/nginx/nginx.conf && \
    echo '    client_max_body_size 100M;' >> /etc/nginx/nginx.conf && \
    echo '    server_tokens off;' >> /etc/nginx/nginx.conf && \
    echo '    gzip on;' >> /etc/nginx/nginx.conf && \
    echo '    gzip_vary on;' >> /etc/nginx/nginx.conf && \
    echo '    gzip_proxied any;' >> /etc/nginx/nginx.conf && \
    echo '    gzip_comp_level 6;' >> /etc/nginx/nginx.conf && \
    echo '    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss image/svg+xml;' >> /etc/nginx/nginx.conf && \
    echo '    server {' >> /etc/nginx/nginx.conf && \
    echo '        listen 80 default_server;' >> /etc/nginx/nginx.conf && \
    echo '        listen [::]:80 default_server;' >> /etc/nginx/nginx.conf && \
    echo '        server_name _;' >> /etc/nginx/nginx.conf && \
    echo '        root /var/www/html;' >> /etc/nginx/nginx.conf && \
    echo '        index index.html;' >> /etc/nginx/nginx.conf && \
    echo '        location /api/ {' >> /etc/nginx/nginx.conf && \
    echo '            proxy_pass http://127.0.0.1:8000/;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_http_version 1.1;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Upgrade \$http_upgrade;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Connection "upgrade";' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Host \$host;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header X-Real-IP \$remote_addr;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header X-Forwarded-Proto \$scheme;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_connect_timeout 600s;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_send_timeout 600s;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_read_timeout 600s;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_buffering off;' >> /etc/nginx/nginx.conf && \
    echo '        }' >> /etc/nginx/nginx.conf && \
    echo '        location /docs {' >> /etc/nginx/nginx.conf && \
    echo '            proxy_pass http://127.0.0.1:8000/docs;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Host \$host;' >> /etc/nginx/nginx.conf && \
    echo '        }' >> /etc/nginx/nginx.conf && \
    echo '        location /redoc {' >> /etc/nginx/nginx.conf && \
    echo '            proxy_pass http://127.0.0.1:8000/redoc;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Host \$host;' >> /etc/nginx/nginx.conf && \
    echo '        }' >> /etc/nginx/nginx.conf && \
    echo '        location /openapi.json {' >> /etc/nginx/nginx.conf && \
    echo '            proxy_pass http://127.0.0.1:8000/openapi.json;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Host \$host;' >> /etc/nginx/nginx.conf && \
    echo '        }' >> /etc/nginx/nginx.conf && \
    echo '        location /ws/ {' >> /etc/nginx/nginx.conf && \
    echo '            proxy_pass http://127.0.0.1:8000/ws/;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_http_version 1.1;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Upgrade \$http_upgrade;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Connection "upgrade";' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header Host \$host;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header X-Real-IP \$remote_addr;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_set_header X-Forwarded-Proto \$scheme;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_connect_timeout 600s;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_send_timeout 600s;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_read_timeout 600s;' >> /etc/nginx/nginx.conf && \
    echo '            proxy_buffering off;' >> /etc/nginx/nginx.conf && \
    echo '        }' >> /etc/nginx/nginx.conf && \
    echo '        location /nginx-health {' >> /etc/nginx/nginx.conf && \
    echo '            access_log off;' >> /etc/nginx/nginx.conf && \
    echo '            return 200 "healthy\\n";' >> /etc/nginx/nginx.conf && \
    echo '            add_header Content-Type text/plain;' >> /etc/nginx/nginx.conf && \
    echo '        }' >> /etc/nginx/nginx.conf && \
    echo '        location / {' >> /etc/nginx/nginx.conf && \
    echo '            try_files \$uri \$uri/ /index.html;' >> /etc/nginx/nginx.conf && \
    echo '            add_header Cache-Control "no-cache, no-store, must-revalidate";' >> /etc/nginx/nginx.conf && \
    echo '        }' >> /etc/nginx/nginx.conf && \
    echo '        error_page 404 /index.html;' >> /etc/nginx/nginx.conf && \
    echo '        error_page 500 502 503 504 /50x.html;' >> /etc/nginx/nginx.conf && \
    echo '        location = /50x.html {' >> /etc/nginx/nginx.conf && \
    echo '            root /usr/share/nginx/html;' >> /etc/nginx/nginx.conf && \
    echo '        }' >> /etc/nginx/nginx.conf && \
    echo '    }' >> /etc/nginx/nginx.conf && \
    echo '}' >> /etc/nginx/nginx.conf

# Création de supervisord.conf
RUN echo '[supervisord]' > /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'user=nexusdl' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'logfile=/app/logs/supervisord.log' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'pidfile=/var/run/supervisord.pid' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'loglevel=info' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo '' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo '[program:backend]' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'command=uvicorn app.main:app --host 0.0.0.0 --port 8000' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'directory=/app' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'environment=PYTHONPATH="/app",TZ="Europe/Paris"' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'user=nexusdl' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'stdout_logfile=/app/logs/backend-out.log' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'stderr_logfile=/app/logs/backend-err.log' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'redirect_stderr=true' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'stopasgroup=true' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'killasgroup=true' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo '' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo '[program:nginx]' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'command=nginx -g "daemon off;"' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'user=root' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'stdout_logfile=/app/logs/nginx-out.log' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'stderr_logfile=/app/logs/nginx-err.log' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'redirect_stderr=true' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'stopasgroup=true' >> /etc/supervisor/conf.d/nexusdl.conf && \
    echo 'killasgroup=true' >> /etc/supervisor/conf.d/nexusdl.conf

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
