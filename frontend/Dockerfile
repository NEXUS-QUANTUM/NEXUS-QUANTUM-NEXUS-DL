# ==========================================================================
#  NexusDL 2.0 - Frontend Dockerfile (corrigé)
#  Fichier : frontend/Dockerfile
#  Description : Image Docker pour l'interface Vue.js 3 avec Nginx
#  Version : 2.0.0
#  Architecture : Multi-stage (builder Node.js + production Nginx)
#  Corrections : utilisation de npm install (pas de package-lock.json)
# ==========================================================================

# --------------------------------------------------------------------------
#  STAGE 1 : BUILDER - Construction de l'application Vue.js
# --------------------------------------------------------------------------

FROM node:20-alpine AS builder

# --- Configuration pour optimiser les builds ---
ENV NODE_ENV=production \
    NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_CACHE=/tmp/.npm-cache \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false

# --- Arguments de build ---
ARG BUILD_DATE=2025-01-15T00:00:00Z
ARG VERSION=2.0.0
ARG GIT_COMMIT=unknown
ARG API_BACKEND_URL=http://backend:8000

# --- Métadonnées de l'image (builder) ---
LABEL maintainer="NexusDL Community <nexusdl@example.com>" \
      org.opencontainers.image.title="NexusDL Frontend (Builder)" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.build-date="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.description="NexusDL 2.0 - Frontend Vue.js 3 (builder stage)" \
      org.opencontainers.image.licenses="GPL-3.0-only"

# --- Définir le répertoire de travail ---
WORKDIR /app

# --- Copier les fichiers de dépendances (pour profiter du cache Docker) ---
COPY package*.json ./
COPY .npmrc ./

# --- Installer les dépendances avec npm install (pas de package-lock.json) ---
# On utilise `npm install --omit=dev` pour n'installer que les dépendances de production.
# L'option `--omit=dev` est l'équivalent moderne de `--only=production`.
RUN npm install --omit=dev --no-audit --no-fund --no-progress \
    && npm cache clean --force \
    && rm -rf /tmp/.npm-cache

# --- Copier le reste du code source ---
COPY . .

# --- Définir les variables d'environnement pour la construction ---
ENV VITE_API_BASE=/api \
    VITE_APP_VERSION=${VERSION} \
    VITE_API_BACKEND_URL=${API_BACKEND_URL} \
    VITE_BUILD_DATE=${BUILD_DATE}

# --- Construire l'application avec Vite ---
RUN npm run build

# --- Nettoyer les fichiers inutiles pour réduire la taille ---
RUN find dist -name "*.map" -type f -delete \
    && rm -rf dist/assets/*.br dist/assets/*.gz \
    && find dist -type d -empty -delete

# --------------------------------------------------------------------------
#  STAGE 2 : PRODUCTION - Serveur Nginx
# --------------------------------------------------------------------------

FROM nginx:alpine AS production

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
      org.opencontainers.image.licenses="GPL-3.0-only"

# --- Installation d'utilitaires supplémentaires ---
RUN apk add --no-cache \
    curl \
    tzdata \
    && cp /usr/share/zoneinfo/Europe/Paris /etc/localtime \
    && echo "Europe/Paris" > /etc/timezone \
    && apk del tzdata

# --- Créer un utilisateur non-root pour Nginx ---
RUN addgroup -g 101 -S nginx && adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx nginx

# --- Copier la configuration Nginx personnalisée ---
COPY nginx.conf /etc/nginx/nginx.conf

# --- Copier les fichiers construits depuis le builder ---
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# --- Créer les dossiers nécessaires et ajuster les permissions ---
RUN mkdir -p /var/cache/nginx /var/log/nginx /usr/share/nginx/html/static /usr/share/nginx/html/icons \
    && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /usr/share/nginx/html \
    && chmod -R 755 /var/cache/nginx /var/log/nginx \
    && chmod -R 755 /usr/share/nginx/html \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid

# --- Vérifier que la configuration Nginx est valide ---
RUN nginx -t

# --- Utilisateur non-root ---
USER nginx

# --- Exposer les ports ---
EXPOSE 80 443

# --- Healthcheck pour Docker ---
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=15s \
            --retries=5 \
    CMD curl -f http://localhost/nginx-health || exit 1

# --- Point d'entrée ---
CMD ["nginx", "-g", "daemon off;"]
