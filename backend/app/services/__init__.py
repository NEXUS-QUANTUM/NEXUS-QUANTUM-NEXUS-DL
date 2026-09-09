# ==========================================================================
#  NexusDL 2.0 - Package Services
#  Fichier : backend/app/services/__init__.py
# ==========================================================================

"""
Package contenant les services de NexusDL.

Ce package expose :
- CacheService : Gestion du cache mémoire/disque
- CbzService : Gestion des fichiers CBZ (extraction, métadonnées, miniatures)
- FileService : Gestion de la bibliothèque et des fichiers
"""

from app.services.cache_service import CacheService
from app.services.cbz_service import CbzService
from app.services.file_service import FileService

__all__ = [
    "CacheService",
    "CbzService",
    "FileService",
]
