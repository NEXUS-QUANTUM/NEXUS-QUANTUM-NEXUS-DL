# ==========================================================================
#  NexusDL 2.0 - Frontend Dockerfile (version complète et finale)
#  Fichier : frontend/Dockerfile
#  Description : Image Docker pour l'interface Vue.js 3 avec Nginx
#  Version : 2.0.0
#  Architecture : Multi-stage (builder Node.js + production Nginx)
#  Licence : GNU GPL v3.0
# ==========================================================================

# --------------------------------------------------------------------------
#  STAGE 1 : BUILDER — Construction de l'application Vue.js
# --------------------------------------------------------------------------

FROM node:20-alpine AS builder

# NODE_ENV=development est indispensable (Vite est une devDependency).
ENV NODE_ENV=development \
    NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_CACHE=/tmp/.npm-cache \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    CI=true

ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown
ARG API_BACKEND_URL=/api

LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Frontend (Builder)" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.description="NexusDL 2.0 - Frontend Vue.js 3 (builder stage)" \
      org.opencontainers.image.licenses="GPL-3.0-only"

RUN apk add --no-cache curl ca-certificates git \
    && rm -rf /var/cache/apk/*

WORKDIR /app

COPY package.json package-lock.json* .npmrc* ./

# `npm install` (et non `npm ci`) car package-lock.json peut être absent.
RUN npm install --no-audit --no-fund --no-progress \
    && npm cache clean --force \
    && rm -rf /tmp/.npm-cache

COPY . .

ENV VITE_API_BASE=/api \
    VITE_APP_VERSION=${VERSION} \
    VITE_API_BACKEND_URL=${API_BACKEND_URL} \
    VITE_BUILD_DATE=${BUILD_DATE}

RUN npm run build

# Nettoyage : sourcemaps et dossiers vides
RUN find dist -name "*.map" -type f -delete 2>/dev/null || true \
    && find dist -type d -empty -delete 2>/dev/null || true

# --------------------------------------------------------------------------
#  STAGE 2 : PRODUCTION — Serveur Nginx
# --------------------------------------------------------------------------

FROM nginx:1.25-alpine AS production

ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown

LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Frontend" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.description="NexusDL 2.0 - Interface Web Vue.js 3 avec Nginx" \
      org.opencontainers.image.licenses="GPL-3.0-only" \
      org.opencontainers.image.source="https://github.com/nexus-dl/nexus-dl"

# curl  : healthcheck
# libcap: pour `setcap` (permet à nginx non-root de binder le port 80)
RUN apk add --no-cache curl libcap \
    && rm -rf /var/cache/apk/*

# Fuseau horaire : copie directe, sans installer/désinstaller tzdata
COPY --from=builder /usr/share/zoneinfo/Europe/Paris /etc/localtime
RUN echo "Europe/Paris" > /etc/timezone

# Autoriser le binaire nginx à binder un port privilégié même lancé en USER nginx
RUN setcap 'cap_net_bind_service=+ep' /usr/sbin/nginx

# NOTE : le user `nginx` (UID 101) existe déjà dans nginx:1.25-alpine.
# Aucun adduser/addgroup nécessaire.

# Configuration Nginx personnalisée
COPY nginx.conf /etc/nginx/nginx.conf

# Fichiers statiques construits
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Dossiers runtime + permissions
# On ne chown PAS /var/run (symlink vers /run) : on chown uniquement le pid file.
RUN mkdir -p /var/cache/nginx /var/log/nginx \
    && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /usr/share/nginx/html \
    && find /usr/share/nginx/html -type d -exec chmod 755 {} + \
    && find /usr/share/nginx/html -type f -exec chmod 644 {} + \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid

# Validation de la config Nginx
RUN nginx -t

# Utilisateur non-root + cap_net_bind_service
USER nginx

EXPOSE 80

HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=15s \
            --retries=5 \
    CMD curl -f http://localhost/nginx-health || exit 1

CMD ["nginx", "-g", "daemon off;"]
