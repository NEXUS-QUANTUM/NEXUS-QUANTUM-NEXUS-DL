# ==========================================================================
#  NexusDL 2.0 - Provider Registry
#  Fichier : backend/app/providers/registry.py
# ==========================================================================

"""
Registre des providers de NexusDL.

Ce module gère l'enregistrement, la découverte et l'accès à tous les providers
disponibles. Il permet :
- L'enregistrement automatique via le décorateur @register_provider
- Le chargement dynamique de tous les providers depuis les sous-packages
- La récupération d'un provider par ID ou par correspondance d'URL
- Le filtrage des providers (langue, NSFW, activation)
- La gestion des priorités

Le registre est un singleton accessible via `ProviderRegistry.get_instance()`.
"""

import importlib
import logging
import inspect
from typing import Dict, List, Optional, Type, Any, Callable, Union
from pathlib import Path
from urllib.parse import urlparse
import pkgutil

from app.providers.base import BaseProvider
from app.core.exceptions import ProviderError, ProviderNotFoundError

logger = logging.getLogger(__name__)


# ==========================================================================
#  Décorateur d'enregistrement
# ==========================================================================

_registry = None


def register_provider(cls: Type[BaseProvider]) -> Type[BaseProvider]:
    """
    Décorateur pour enregistrer une classe de provider dans le registre.
    La classe doit hériter de BaseProvider et définir un attribut 'id'.

    Exemple :
    @register_provider
    class MyProvider(BaseProvider):
        id = "myprovider"
        ...
    """
    if not issubclass(cls, BaseProvider):
        raise TypeError(f"La classe {cls.__name__} doit hériter de BaseProvider")
    if not hasattr(cls, 'id') or not cls.id:
        raise ValueError(f"La classe {cls.__name__} doit définir un attribut 'id'")

    # Enregistrer dans le registre (si initialisé)
    registry = ProviderRegistry.get_instance()
    registry.register(cls)
    return cls


# ==========================================================================
#  Provider Registry
# ==========================================================================

class ProviderRegistry:
    """
    Singleton responsable de l'enregistrement et de la gestion des providers.
    """

    _instance: Optional['ProviderRegistry'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not ProviderRegistry._initialized:
            self._providers: Dict[str, Type[BaseProvider]] = {}
            self._provider_instances: Dict[str, BaseProvider] = {}
            self._initialized = True
            # Charger les providers découverts (lazy)
            self._loaded = False
            ProviderRegistry._instance = self

    @classmethod
    def get_instance(cls) -> 'ProviderRegistry':
        """Retourne l'instance unique du registre."""
        if cls._instance is None:
            cls._instance = ProviderRegistry()
        return cls._instance

    def register(self, provider_class: Type[BaseProvider]) -> None:
        """
        Enregistre une classe de provider.
        """
        provider_id = provider_class.id
        if provider_id in self._providers:
            logger.warning(f"Provider {provider_id} déjà enregistré, remplacement.")
        self._providers[provider_id] = provider_class
        logger.debug(f"Provider enregistré: {provider_id} ({provider_class.__name__})")

    def initialize(self) -> None:
        """
        Initialise le registre : charge tous les providers depuis les sous-packages.
        Cette méthode est appelée automatiquement au démarrage.
        """
        if self._loaded:
            return
        self._discover_providers()
        self._loaded = True
        logger.info(f"✅ {len(self._providers)} providers chargés")

    def _discover_providers(self) -> None:
        """
        Parcourt les sous-packages de 'app.providers' pour importer automatiquement
        tous les modules et déclencher l'enregistrement via le décorateur.
        """
        # Packages à explorer (tous les sous-dossiers de providers)
        provider_packages = [
            'app.providers.themes',
            'app.providers.french',
            'app.providers.english',
            'app.providers.nsfw',
        ]

        for package_name in provider_packages:
            try:
                package = importlib.import_module(package_name)
                # Importer tous les sous-modules du package
                package_path = Path(package.__file__).parent
                for module_info in pkgutil.iter_modules([str(package_path)]):
                    if not module_info.ispkg:
                        module_name = f"{package_name}.{module_info.name}"
                        try:
                            importlib.import_module(module_name)
                            logger.debug(f"Module importé: {module_name}")
                        except Exception as e:
                            logger.warning(f"Erreur importation {module_name}: {e}")
            except ImportError as e:
                logger.warning(f"Package {package_name} non trouvé: {e}")

        # Forcer le chargement du provider madara (s'il n'a pas été importé)
        # normalement il est dans themes
        # Pas besoin, car themes est inclus dans la liste.

    def get_all_providers(self) -> Dict[str, BaseProvider]:
        """
        Retourne un dictionnaire de tous les providers instanciés (ID -> instance).
        Si un provider n'est pas encore instancié, il le sera.
        """
        self.initialize()
        result = {}
        for provider_id, provider_class in self._providers.items():
            try:
                instance = self._get_or_create_instance(provider_id)
                if instance.enabled:
                    result[provider_id] = instance
            except Exception as e:
                logger.error(f"Erreur instanciation provider {provider_id}: {e}")
        return result

    def get_provider(self, provider_id: str) -> Optional[BaseProvider]:
        """
        Retourne l'instance d'un provider par son ID, ou None si non trouvé.
        """
        self.initialize()
        if provider_id not in self._providers:
            return None
        try:
            return self._get_or_create_instance(provider_id)
        except Exception as e:
            logger.error(f"Erreur instanciation provider {provider_id}: {e}")
            return None

    def _get_or_create_instance(self, provider_id: str) -> BaseProvider:
        """
        Crée une instance du provider si elle n'existe pas encore, puis la retourne.
        """
        if provider_id in self._provider_instances:
            return self._provider_instances[provider_id]

        provider_class = self._providers.get(provider_id)
        if not provider_class:
            raise ProviderNotFoundError(f"Provider {provider_id} non trouvé")

        # Instancier le provider
        try:
            instance = provider_class()
            self._provider_instances[provider_id] = instance
            return instance
        except Exception as e:
            logger.error(f"Erreur instantiation {provider_id}: {e}")
            raise ProviderError(f"Impossible d'instancier le provider {provider_id}: {e}")

    def get_provider_for_url(self, url: str) -> Optional[BaseProvider]:
        """
        Trouve le provider le plus approprié pour une URL donnée,
        en fonction de la correspondance du domaine (base_url).
        Retourne None si aucun provider ne correspond.
        """
        self.initialize()
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Essayer de trouver un provider dont le domaine correspond exactement
        for provider_id, instance in self.get_all_providers().items():
            if not instance.enabled:
                continue
            # Comparer les domaines (supprimer le www. si présent)
            provider_domain = urlparse(instance.base_url).netloc.lower()
            if provider_domain.startswith('www.'):
                provider_domain = provider_domain[4:]
            if domain.startswith('www.'):
                domain_clean = domain[4:]
            else:
                domain_clean = domain
            if domain_clean == provider_domain:
                return instance
            # Vérifier si le domaine est un sous-domaine
            if domain_clean.endswith(f".{provider_domain}"):
                return instance

        # Si aucun match exact, on essaie de trouver un provider générique (Madara)
        # mais on ne le fait pas ici, car Madara est utilisé par défaut si besoin
        # On pourrait ajouter un fallback

        return None

    def get_providers_by_language(self, language: str) -> List[BaseProvider]:
        """
        Retourne les providers qui supportent une langue donnée.
        """
        self.initialize()
        result = []
        for provider_id, instance in self.get_all_providers().items():
            if language in instance.supported_languages:
                result.append(instance)
        return result

    def get_providers_by_nsfw(self, include_nsfw: bool = False) -> List[BaseProvider]:
        """
        Retourne les providers en fonction du contenu NSFW.
        """
        self.initialize()
        result = []
        for provider_id, instance in self.get_all_providers().items():
            if include_nsfw or not instance.nsfw:
                result.append(instance)
        return result

    def get_enabled_providers(self) -> List[BaseProvider]:
        """
        Retourne tous les providers activés.
        """
        self.initialize()
        return [instance for instance in self.get_all_providers().values() if instance.enabled]

    def get_priority_providers(self) -> List[BaseProvider]:
        """
        Retourne les providers triés par priorité (descendant).
        """
        providers = self.get_enabled_providers()
        providers.sort(key=lambda p: getattr(p, 'priority', 0), reverse=True)
        return providers

    def save_provider_state(self, provider_id: str, enabled: bool) -> None:
        """
        Persiste l'état activé/désactivé d'un provider (en mémoire pour l'instant).
        Note: pour une persistance réelle, il faudrait stocker en base de données.
        """
        instance = self.get_provider(provider_id)
        if instance:
            instance.enabled = enabled
            # On pourrait aussi sauvegarder dans un fichier de config ou DB
            logger.info(f"Provider {provider_id} {'activé' if enabled else 'désactivé'}")

    def reload(self) -> None:
        """
        Recharge tous les providers (réinitialise le cache et recharge les modules).
        Utile pour le développement.
        """
        self._provider_instances.clear()
        self._providers.clear()
        self._loaded = False
        self.initialize()
        logger.info("Providers rechargés")

    def __repr__(self) -> str:
        return f"<ProviderRegistry(providers={len(self._providers)})>"


# ==========================================================================
#  Fonction utilitaire pour la compatibilité
# ==========================================================================

def get_registry() -> ProviderRegistry:
    """
    Fonction utilitaire pour obtenir l'instance du registre.
    """
    return ProviderRegistry.get_instance()
