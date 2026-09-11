# ==========================================================================
#  NexusDL 2.0 - Provider Registry
#  Fichier : backend/app/providers/registry.py
#  Version : 2.0.0-final
# ==========================================================================

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type
from urllib.parse import urlparse

from app.providers.base import BaseProvider
from app.core.exceptions import ProviderError, ProviderNotFoundError

logger = logging.getLogger(__name__)


# ==========================================================================
#  Décorateur d'enregistrement
# ==========================================================================

def register_provider(cls: Type[BaseProvider]) -> Type[BaseProvider]:
    """
    Décorateur qui enregistre une classe de provider dans le registre.
    """
    if not issubclass(cls, BaseProvider):
        raise TypeError(f"La classe {cls.__name__} doit hériter de BaseProvider")
    if not getattr(cls, "id", None):
        raise ValueError(f"La classe {cls.__name__} doit définir un attribut 'id'")

    registry = ProviderRegistry.get_instance()
    registry.register(cls)
    return cls


# ==========================================================================
#  Provider Registry (singleton)
# ==========================================================================

class ProviderRegistry:
    """
    Singleton responsable de l'enregistrement et de la gestion des providers.

    Le pattern est volontairement placé dans __new__ pour éviter le piège
    classique du `_initialized` d'instance.
    """

    _instance: Optional["ProviderRegistry"] = None

    def __new__(cls) -> "ProviderRegistry":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._providers: Dict[str, Type[BaseProvider]] = {}
            instance._provider_instances: Dict[str, BaseProvider] = {}
            instance._loaded: bool = False
            cls._instance = instance
        return cls._instance

    def __init__(self) -> None:
        # No-op : tout est fait dans __new__ pour garantir l'unicité.
        pass

    @classmethod
    def get_instance(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ----------------------------------------------------------------------
    #  Enregistrement
    # ----------------------------------------------------------------------

    def register(self, provider_class: Type[BaseProvider]) -> None:
        provider_id = provider_class.id
        if provider_id in self._providers:
            logger.warning(f"Provider {provider_id} déjà enregistré, remplacement.")
        self._providers[provider_id] = provider_class
        logger.debug(f"Provider enregistré : {provider_id} ({provider_class.__name__})")

    def initialize(self) -> None:
        if self._loaded:
            return
        self._discover_providers()
        self._loaded = True
        logger.info(f"✅ {len(self._providers)} providers chargés")

    def _discover_providers(self) -> None:
        provider_packages = [
            "app.providers.themes",
            "app.providers.french",
            "app.providers.english",
            "app.providers.nsfw",
        ]

        for package_name in provider_packages:
            try:
                package = importlib.import_module(package_name)
            except ImportError as e:
                logger.warning(f"Package {package_name} non trouvé : {e}")
                continue
            except Exception as e:
                logger.error(f"Erreur import package {package_name} : {e}", exc_info=True)
                continue

            try:
                package_path = Path(package.__file__).parent
                for module_info in pkgutil.iter_modules([str(package_path)]):
                    if module_info.ispkg:
                        continue
                    module_name = f"{package_name}.{module_info.name}"
                    try:
                        importlib.import_module(module_name)
                        logger.debug(f"Module importé : {module_name}")
                    except Exception as e:
                        logger.warning(f"Erreur importation {module_name} : {e}")
            except Exception as e:
                logger.error(f"Erreur discovery {package_name} : {e}", exc_info=True)

    # ----------------------------------------------------------------------
    #  Accès aux providers
    # ----------------------------------------------------------------------

    def get_all_providers(self) -> Dict[str, BaseProvider]:
        self.initialize()
        result: Dict[str, BaseProvider] = {}
        # list() pour éviter toute mutation pendant l'itération
        for provider_id, provider_class in list(self._providers.items()):
            try:
                instance = self._get_or_create_instance(provider_id)
                if getattr(instance, "enabled", True):
                    result[provider_id] = instance
            except Exception as e:
                logger.error(f"Erreur instanciation provider {provider_id} : {e}")
        return result

    def get_provider(self, provider_id: str) -> Optional[BaseProvider]:
        self.initialize()
        if provider_id not in self._providers:
            return None
        try:
            return self._get_or_create_instance(provider_id)
        except Exception as e:
            logger.error(f"Erreur instanciation provider {provider_id} : {e}")
            return None

    def _get_or_create_instance(self, provider_id: str) -> BaseProvider:
        if provider_id in self._provider_instances:
            return self._provider_instances[provider_id]

        provider_class = self._providers.get(provider_id)
        if not provider_class:
            raise ProviderNotFoundError(f"Provider {provider_id} non trouvé")

        try:
            instance = provider_class()
        except Exception as e:
            logger.error(f"Erreur instantiation {provider_id} : {e}", exc_info=True)
            raise ProviderError(
                f"Impossible d'instancier le provider {provider_id} : {e}"
            )

        self._provider_instances[provider_id] = instance
        return instance

    # ----------------------------------------------------------------------
    #  Recherche
    # ----------------------------------------------------------------------

    def get_provider_for_url(self, url: str) -> Optional[BaseProvider]:
        self.initialize()
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        for instance in self.get_all_providers().values():
            if not getattr(instance, "enabled", True):
                continue
            provider_domain = urlparse(instance.base_url).netloc.lower()
            if provider_domain.startswith("www."):
                provider_domain = provider_domain[4:]
            if domain == provider_domain or domain.endswith(f".{provider_domain}"):
                return instance

        return None

    def get_providers_by_language(self, language: str) -> List[BaseProvider]:
        self.initialize()
        return [
            instance
            for instance in self.get_all_providers().values()
            if language in getattr(instance, "supported_languages", [])
        ]

    def get_providers_by_nsfw(self, include_nsfw: bool = False) -> List[BaseProvider]:
        self.initialize()
        return [
            instance
            for instance in self.get_all_providers().values()
            if include_nsfw or not getattr(instance, "nsfw", False)
        ]

    def get_enabled_providers(self) -> List[BaseProvider]:
        self.initialize()
        return [
            instance
            for instance in self.get_all_providers().values()
            if getattr(instance, "enabled", True)
        ]

    def get_priority_providers(self) -> List[BaseProvider]:
        providers = self.get_enabled_providers()
        providers.sort(key=lambda p: getattr(p, "priority", 0), reverse=True)
        return providers

    # ----------------------------------------------------------------------
    #  Mutation
    # ----------------------------------------------------------------------

    def save_provider_state(self, provider_id: str, enabled: bool) -> None:
        instance = self.get_provider(provider_id)
        if instance:
            instance.enabled = enabled
            logger.info(f"Provider {provider_id} {'activé' if enabled else 'désactivé'}")

    def reload(self) -> None:
        self._provider_instances.clear()
        self._providers.clear()
        self._loaded = False
        self.initialize()
        logger.info("Providers rechargés")

    def __repr__(self) -> str:
        return f"<ProviderRegistry(providers={len(self._providers)})>"


# ==========================================================================
#  Compat
# ==========================================================================

def get_registry() -> ProviderRegistry:
    return ProviderRegistry.get_instance()
