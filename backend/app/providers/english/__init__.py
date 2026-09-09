# ==========================================================================
#  NexusDL 2.0 - Providers English Package
#  Fichier : backend/app/providers/english/__init__.py
# ==========================================================================

"""
Package contenant les providers pour les sites de scan en anglais.

Providers inclus :
- AsuraScansProvider : Asura Scans (asurascans.com)
- MangaDexProvider : MangaDex (mangadex.org) - API officielle
"""

from app.providers.english.asurascans import AsuraScansProvider
from app.providers.english.mangadex import MangaDexProvider

__all__ = [
    "AsuraScansProvider",
    "MangaDexProvider",
]
