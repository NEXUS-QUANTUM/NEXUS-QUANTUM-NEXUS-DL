# --------------------------------------------------------------------------
#  STAGE 2 : BUILDER - Node.js (frontend)
# --------------------------------------------------------------------------

FROM node:20-alpine AS builder-node

# ✅ IMPORTANT : ne PAS mettre NODE_ENV=production ici
ENV NODE_ENV=development

ARG VERSION=2.0.0
ARG API_BACKEND_URL=http://localhost:8000

WORKDIR /build
COPY frontend/package*.json ./

# ✅ Installer TOUTES les dépendances (y compris devDependencies)
RUN npm install --no-audit --no-fund --no-progress && npm cache clean --force

COPY frontend/ .
ENV VITE_API_BASE=/api \
    VITE_APP_VERSION=${VERSION} \
    VITE_API_BACKEND_URL=${API_BACKEND_URL}
RUN npm run build
