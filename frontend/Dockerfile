# ==========================================================================
#  NexusDL 2.0 - Frontend Dockerfile (version complète et finale)
#  Fichier : frontend/Dockerfile
#  Description : Image Docker pour l'interface Vue.js 3 avec Nginx
#  Version : 2.0.0
#  Architecture : Multi-stage (builder Node.js + production Nginx)
#  Licence : GNU GPL v3.0
#
#  ⚠️ IMPORTANT :
#  - Ce Dockerfile nécessite le fichier `nginx.conf` dans le même dossier.
#  - Vite est une devDependency, il faut donc installer TOUTES les
#    dépendances dans le builder (PAS de --omit=dev).
#  - Ne pas utiliser `npm ci` si `package-lock.json` est absent.
# ==========================================================================

# --------------------------------------------------------------------------
#  STAGE 1 : BUILDER — Construction de l'application Vue.js
# --------------------------------------------------------------------------

FROM node:20-alpine AS builder

# --- Configuration de l'environnement ---
# ⚠️ NODE_ENV=development : indispensable car Vite est une devDependency.
#    Si on met NODE_ENV=production, npm ignore les devDependencies.
ENV NODE_ENV=development \
    NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_CACHE=/tmp/.npm-cache \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    CI=true

# --- Arguments de build ---
ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown
ARG API_BACKEND_URL=/api

# --- Métadonnées de l'image (builder) ---
LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Frontend (Builder)" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.description="NexusDL 2.0 - Frontend Vue.js 3 (builder stage)" \
      org.opencontainers.image.licenses="GPL-3.0-only"

# --- Installation des dépendances système minimales ---
RUN apk add --no-cache \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/cache/apk/*

# --- Définir le répertoire de travail ---
WORKDIR /app

# --- Copier les fichiers de dépendances (cache Docker optimisé) ---
COPY package.json package-lock.json* .npmrc* ./

# --- Installer TOUTES les dépendances (prod + dev) ---
# ✅ Utilisation de `npm install` (et non `npm ci`) car package-lock.json
#    peut ne pas être présent dans le dépôt.
RUN npm install --no-audit --no-fund --no-progress \
    && npm cache clean --force \
    && rm -rf /tmp/.npm-cache

# --- Copier le reste du code source ---
COPY . .

# --- Variables d'environnement pour le build Vite ---
ENV VITE_API_BASE=/api \
    VITE_APP_VERSION=${VERSION} \
    VITE_API_BACKEND_URL=${API_BACKEND_URL} \
    VITE_BUILD_DATE=${BUILD_DATE}

# --- Construire l'application ---
RUN npm run build

# --- Nettoyer les fichiers inutiles pour réduire la taille ---
RUN find dist -name "*.map" -type f -delete 2>/dev/null || true \
    && find dist -type d -empty -delete 2>/dev/null || true

# --------------------------------------------------------------------------
#  STAGE 2 : PRODUCTION — Serveur Nginx
# --------------------------------------------------------------------------

FROM nginx:1.25-alpine AS production

# --- Arguments de build ---
ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown

# --- Métadonnées de l'image finale ---
LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Frontend" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.description="NexusDL 2.0 - Interface Web Vue.js 3 avec Nginx" \
      org.opencontainers.image.licenses="GPL-3.0-only" \
      org.opencontainers.image.source="https://github.com/nexus-dl/nexus-dl"

# --- Installation des utilitaires supplémentaires ---
RUN apk add --no-cache \
    curl \
    tzdata \
    && cp /usr/share/zoneinfo/Europe/Paris /etc/localtime \
    && echo "Europe/Paris" > /etc/timezone \
    && apk del tzdata

# --- Créer un utilisateur non-root pour Nginx ---
RUN addgroup -g 101 -S nginx 2>/dev/null || true \
    && adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx nginx 2>/dev/null || true

# --- Copier la configuration Nginx personnalisée ---
COPY nginx.conf /etc/nginx/nginx.conf

# --- Copier les fichiers construits depuis le builder ---
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# --- Créer les dossiers nécessaires et ajuster les permissions ---
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run \
    && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /var/run \
    && chmod -R 755 /var/cache/nginx /var/log/nginx \
    && chmod -R 755 /usr/share/nginx/html \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid

# --- Vérifier que la configuration Nginx est valide ---
RUN nginx -t

# --- Utilisateur non-root ---
USER nginx

# --- Exposer les ports ---
EXPOSE 80

# --- Healthcheck pour Docker ---
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=15s \
            --retries=5 \
    CMD curl -f http://localhost/nginx-health || exit 1

# --- Point d'entrée ---
CMD ["nginx", "-g", "daemon off;"]
