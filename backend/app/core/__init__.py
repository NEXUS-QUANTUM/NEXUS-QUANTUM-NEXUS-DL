# ==========================================================================
#  NexusDL 2.0 - Package Core
#  Fichier : backend/app/core/__init__.py
# ==========================================================================

"""
Package core contenant les composants fondamentaux de NexusDL.

Ce package expose :
- Configuration (settings)
- Gestionnaire de téléchargement (Downloader)
- Moteur de téléchargement (DownloadEngine)
- Constructeur CBZ (CbzBuilder)
- Exceptions personnalisées
"""

from app.core.config import settings
from app.core.downloader import Downloader
from app.core.engine import DownloadEngine
from app.core.cbz_builder import CbzBuilder
from app.core.exceptions import (
    NexusDLError,
    ProviderError,
    ProviderNotFoundError,
    DownloadError,
    DownloadTimeoutError,
    CbzBuildError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    JobNotFoundError,
    FileOperationError,
    FileNotFoundError,
    CacheError,
    DatabaseError,
    ValidationError,
)

__all__ = [
    "settings",
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
]
