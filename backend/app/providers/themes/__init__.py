# ==========================================================================
#  NexusDL 2.0 - Providers Themes Package
#  Fichier : backend/app/providers/themes/__init__.py
# ==========================================================================

"""
Package contenant les providers basés sur des thèmes de sites de scan.

Ce package fournit des classes génériques qui implémentent les mécanismes
communs à plusieurs sites utilisant le même thème (ex: WordPress Madara).

Thèmes supportés :
- MadaraProvider : Provider générique pour les sites utilisant le thème Madara
  (https://wordpress.org/themes/madara/)

Ces providers sont destinés à être hérités par des providers spécifiques
qui peuvent surcharger les sélecteurs CSS ou certains comportements.
"""

from app.providers.themes.madara import MadaraProvider

__all__ = [
    "MadaraProvider",
]
