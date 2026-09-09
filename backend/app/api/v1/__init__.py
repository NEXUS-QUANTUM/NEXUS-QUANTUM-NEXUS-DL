# ==========================================================================
#  NexusDL 2.0 - API v1 Package
#  Fichier : backend/app/api/v1/__init__.py
# ==========================================================================

"""
Package de l'API version 1 (v1) de NexusDL.

Ce package contient tous les endpoints REST et WebSocket organisés par
domaine fonctionnel : authentification, administration, navigation,
téléchargements, bibliothèque et système.
"""

from app.api.v1.router import router

# Exposition du routeur principal pour faciliter les imports
__all__ = [
    "router",
]
