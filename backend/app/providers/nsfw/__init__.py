# ==========================================================================
#  NexusDL 2.0 - Providers NSFW Package
#  Fichier : backend/app/providers/nsfw/__init__.py
# ==========================================================================

"""
Package contenant les providers pour les sites de contenu pour adultes (NSFW).

Providers inclus :
- NHentaiProvider : nHentai (nhentai.net) - Doujinshi et hentai
- PururinProvider : Pururin (pururin.com) - Madara + Playwright (à implémenter ultérieurement)
"""

from app.providers.nsfw.nhentai import NHentaiProvider

__all__ = [
    "NHentaiProvider",
]
