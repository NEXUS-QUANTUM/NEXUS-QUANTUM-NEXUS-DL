# ==========================================================================
#  NexusDL 2.0 - Package Modèles
#  Fichier : backend/app/models/__init__.py
# ==========================================================================

"""
Package contenant tous les modèles SQLAlchemy de NexusDL.

Ce package expose :
- La base déclarative SQLAlchemy (Base)
- Tous les modèles : User, Setting, Session, Provider, LibraryItem, Job
- Les énumérations utilisées par les modèles
"""

from sqlalchemy.ext.declarative import declarative_base

# ==========================================================================
#  Base déclarative
# ==========================================================================

Base = declarative_base()

# ==========================================================================
#  Importer tous les modèles (pour que SQLAlchemy les découvre)
# ==========================================================================

from app.models.user import User, UserRole, UserStatus
from app.models.settings import Setting
from app.models.session import Session
from app.models.provider import Provider
from app.models.library import LibraryItem
from app.models.job import Job, JobStatus, JobPriority, JobType

# ==========================================================================
#  Exports
# ==========================================================================

__all__ = [
    # Base
    "Base",

    # Modèles
    "User",
    "Setting",
    "Session",
    "Provider",
    "LibraryItem",
    "Job",

    # Énumérations
    "UserRole",
    "UserStatus",
    "JobStatus",
    "JobPriority",
    "JobType",
]
