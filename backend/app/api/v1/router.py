# ==========================================================================
#  NexusDL 2.0 - Routeur principal API v1
#  Fichier : backend/app/api/v1/router.py
# ==========================================================================

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    admin,
    browse,
    downloads,
    library,
    system,
    websocket
)

# ==========================================================================
#  Routeur principal
# ==========================================================================

router = APIRouter()

# --------------------------------------------------------------------------
#  Inclure les sous-routeurs avec leurs préfixes respectifs
# --------------------------------------------------------------------------

# Authentification
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Administration (protégé par rôle ADMIN)
router.include_router(admin.router, prefix="/admin", tags=["Administration"])

# Navigation et recherche
router.include_router(browse.router, prefix="/browse", tags=["Browse"])

# Téléchargements et jobs
router.include_router(downloads.router, prefix="/downloads", tags=["Downloads"])

# Bibliothèque
router.include_router(library.router, prefix="/library", tags=["Library"])

# Système
router.include_router(system.router, prefix="/system", tags=["System"])

# WebSocket (géré séparément, mais on inclut pour la documentation)
router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

# ==========================================================================
#  Export du routeur
# ==========================================================================

# Dans main.py, on utilisera:
# app.include_router(router, prefix="/api/v1")
