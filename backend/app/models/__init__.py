# ==========================================================================
#  NexusDL 2.0 - Package Modèles
#  Fichier : backend/app/models/__init__.py
#  Version : 2.0.0
# ==========================================================================

"""
Package contenant tous les modèles SQLAlchemy de NexusDL.

Expose :
- `Base` : instance déclarative unique, définie dans `app.models.base`
- Tous les modèles : User, Setting, Session, Provider, LibraryItem, Job
- Les énumérations utilisées par les modèles
"""

# ==========================================================================
#  Base déclarative
# ==========================================================================
# ⚠️ `Base` vient de `app.models.base`, PAS défini ici.
#    Si on le définit dans `__init__.py`, on obtient un import circulaire
#    (les modèles importent `Base` depuis `app.models`, qui importe les
#    modèles juste après → cycle) et deux objets `Base` différents.
from app.models.base import Base

# ==========================================================================
#  Importer tous les modèles (SQLAlchemy les découvre via ces imports)
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
