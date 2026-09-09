# ==========================================================================
#  NexusDL 2.0 - Package Principal de l'Application
#  Fichier : backend/app/__init__.py
# ==========================================================================

"""
Package racine de l'application NexusDL.

Ce package contient tous les composants de l'application :
- API (FastAPI)
- Modèles de données (SQLAlchemy)
- Providers (sites de scan)
- Services (cache, fichiers, CBZ)
- Workers (gestion des jobs)
- Utilitaires et configuration

Le package est organisé pour faciliter l'importation des composants principaux
et pour fournir une interface propre pour l'initialisation de l'application.

Exports principaux :
- main : l'application FastAPI (app)
- settings : configuration globale
- Base : base déclarative SQLAlchemy
- ProviderRegistry : registre des providers
- JobManager : gestionnaire de jobs
- CbzBuilder : constructeur de fichiers CBZ
- exceptions : toutes les exceptions personnalisées
"""

# ==========================================================================
#  Imports des sous-packages pour les rendre disponibles au niveau racine
# ==========================================================================

from app.core import settings
from app.core.config import Settings
from app.core.exceptions import *
from app.core.downloader import Downloader
from app.core.engine import DownloadEngine
from app.core.cbz_builder import CbzBuilder

from app.models import Base
from app.models.user import User, UserRole, UserStatus
from app.models.job import Job, JobStatus, JobPriority, JobType
from app.models.settings import Setting
from app.models.session import Session
from app.models.provider import Provider
from app.models.library import LibraryItem

from app.providers import BaseProvider, ProviderRegistry, register_provider, get_registry
from app.providers.themes import MadaraProvider
from app.providers.french import SushiScanProvider, HentaizoneProvider
from app.providers.english import AsuraScansProvider, MangaDexProvider
from app.providers.nsfw import NHentaiProvider

from app.services import CacheService, CbzService, FileService

from app.workers import JobManager

from app.api import router as api_router
from app.api.v1 import router as v1_router

from app.main import app

# ==========================================================================
#  Liste des éléments exportés (pour `from app import *`)
# ==========================================================================

__all__ = [
    # Application
    "app",
    
    # Configuration
    "settings",
    "Settings",
    
    # Core
    "Downloader",
    "DownloadEngine",
    "CbzBuilder",
    
    # Exceptions
    "NexusDLError",
    "ProviderError",
    "ProviderNotFoundError",
    "DownloadError",
    "DownloadTimeoutError",
    "CbzBuildError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "JobNotFoundError",
    "FileOperationError",
    "FileNotFoundError",
    "CacheError",
    "DatabaseError",
    "ValidationError",
    
    # Modèles (Base et modèles)
    "Base",
    "User",
    "UserRole",
    "UserStatus",
    "Job",
    "JobStatus",
    "JobPriority",
    "JobType",
    "Setting",
    "Session",
    "Provider",
    "LibraryItem",
    
    # Providers
    "BaseProvider",
    "ProviderRegistry",
    "register_provider",
    "get_registry",
    "MadaraProvider",
    "SushiScanProvider",
    "HentaizoneProvider",
    "AsuraScansProvider",
    "MangaDexProvider",
    "NHentaiProvider",
    
    # Services
    "CacheService",
    "CbzService",
    "FileService",
    
    # Workers
    "JobManager",
    
    # API
    "api_router",
    "v1_router",
]

# ==========================================================================
#  Fonction d'initialisation de l'application
# ==========================================================================

def init_app():
    """
    Initialise tous les services et composants de l'application.
    Appelée au démarrage de l'application (dans main.py ou via un event handler).
    """
    import logging
    from app.api.deps import init_services
    from app.core.config import settings
    
    logger = logging.getLogger(__name__)
    logger.info(f"🧬 Initialisation de {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialiser les services (registre providers, job manager, etc.)
    init_services()
    
    # Créer les dossiers nécessaires
    settings.get_download_path()
    settings.get_temp_path()
    
    # Initialiser le gestionnaire WebSocket (optionnel, via websocket.init)
    try:
        from app.api.v1.endpoints import websocket
        websocket.init_websocket_manager()
    except Exception as e:
        logger.warning(f"WebSocket non initialisé: {e}")
    
    logger.info("✅ Application initialisée")
    return True

# ==========================================================================
#  Note sur l'importation dans main.py
# ==========================================================================
#  Dans main.py, on peut utiliser :
#  from app import app, init_app
#  init_app()  # appelé après la création de l'application FastAPI
