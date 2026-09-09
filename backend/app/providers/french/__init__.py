# ==========================================================================
#  NexusDL 2.0 - Providers French Package
#  Fichier : backend/app/providers/french/__init__.py
# ==========================================================================

"""
Package contenant les providers pour les sites de scan en français.

Providers inclus :
- HentaizoneProvider : Hentaizone (hentaizone.xyz) - Contenu NSFW
- SushiScanProvider : SushiScan (sushiscan.net)
"""

from app.providers.french.hentaizone import HentaizoneProvider
from app.providers.french.sushiscan import SushiScanProvider

__all__ = [
    "HentaizoneProvider",
    "SushiScanProvider",
]
