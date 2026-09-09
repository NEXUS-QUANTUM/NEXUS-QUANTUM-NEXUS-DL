# ==========================================================================
#  NexusDL 2.0 - API Package
#  Fichier : backend/app/api/__init__.py
# ==========================================================================

"""
Package API de NexusDL.

Ce package contient les endpoints REST et WebSocket organisés par version.
La version 1 (v1) est actuellement la seule implémentée.
"""

from app.api.v1 import router as v1_router

# Exposition du routeur principal de l'API
# Pour une utilisation dans main.py : from app.api import router
# puis app.include_router(router, prefix="/api")
router = v1_router

__all__ = [
    "router",
    "v1_router",
]
