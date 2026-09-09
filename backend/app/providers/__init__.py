# ==========================================================================
#  NexusDL 2.0 - Providers Package
#  Fichier : backend/app/providers/__init__.py
# ==========================================================================

"""
Package des providers de NexusDL.

Ce package contient tous les providers de sites de scan, organisés par thème et par langue.

Structure :
- base.py : Classe de base abstraite BaseProvider
- registry.py : Registre des providers (ProviderRegistry)
- themes/ : Providers basés sur des thèmes (ex: Madara)
- french/ : Providers pour les sites français
- english/ : Providers pour les sites anglais
- nsfw/ : Providers pour les sites de contenu adulte

Exporte :
- BaseProvider : Classe de base à étendre
- ProviderRegistry : Singleton pour gérer les providers
- register_provider : Décorateur pour enregistrer automatiquement un provider
- get_registry : Fonction utilitaire pour obtenir l'instance du registre
"""

from app.providers.base import BaseProvider
from app.providers.registry import ProviderRegistry, register_provider, get_registry

# Importer les sous-packages pour déclencher l'enregistrement automatique
# (même si cela est déjà fait dans registry.initialize, on les importe pour être sûr)
from app.providers import themes
from app.providers import french
from app.providers import english
from app.providers import nsfw

__all__ = [
    "BaseProvider",
    "ProviderRegistry",
    "register_provider",
    "get_registry",
]
