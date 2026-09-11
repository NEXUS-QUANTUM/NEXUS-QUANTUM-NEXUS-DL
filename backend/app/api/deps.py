# ==========================================================================
#  NexusDL 2.0 - Dépendances globales
#  Fichier : backend/app/api/deps.py
#  Version : 2.0.0-final
# ==========================================================================

import inspect
import logging
from typing import Optional, Dict, Generator
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.providers.registry import ProviderRegistry
from app.workers.job_manager import JobManager
from app.services.file_service import FileService
from app.services.cache_service import CacheService
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

# ==========================================================================
#  Base de données
# ==========================================================================

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.DATABASE_URL
    else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dépendance : session SQLAlchemy par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================================
#  Utilisateurs (stockage en mémoire pour l'instant)
# ==========================================================================

users_db: Dict[str, User] = {}


def get_user_by_username(username: str) -> Optional[User]:
    return users_db.get(username)


def get_user_by_id(user_id: int) -> Optional[User]:
    for user in users_db.values():
        if user.id == user_id:
            return user
    return None


def create_user(user_data: dict) -> User:
    new_id = max([u.id for u in users_db.values()] + [0]) + 1
    now = datetime.utcnow()
    user = User(
        id=new_id,
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=user_data["hashed_password"],
        role=user_data.get("role", UserRole.USER),
        created_at=now,
        updated_at=now,
    )
    users_db[user.username] = user
    return user


def seed_default_admin() -> None:
    if users_db:
        return
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    create_user(
        {
            "username": "admin",
            "email": "admin@nexusdl.local",
            "hashed_password": pwd_context.hash("admin123"),
            "role": UserRole.ADMIN,
        }
    )
    logger.info("✅ Utilisateur admin par défaut créé (admin / admin123)")


# ==========================================================================
#  Authentification JWT
# ==========================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        # Import différé pour éviter les cycles
        from app.api.v1.endpoints.auth import decode_token

        payload = decode_token(token)
        username = payload.get("sub")
        if username is None:
            raise AuthenticationError("Token invalide : utilisateur manquant")

        user = get_user_by_username(username)
        if user is None:
            raise AuthenticationError("Utilisateur non trouvé")
        return user

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Erreur d'authentification : {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    is_active = getattr(current_user, "is_active", True)
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur inactif"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privilèges d'administrateur requis",
        )
    return current_user


# ==========================================================================
#  Services (singletons module-level)
# ==========================================================================

_provider_registry: Optional[ProviderRegistry] = None
_job_manager: Optional[JobManager] = None
_file_service: Optional[FileService] = None
_cache_service: Optional[CacheService] = None


def _acquire_provider_registry() -> ProviderRegistry:
    """
    Retourne l'instance unique de ProviderRegistry, en respectant le
    pattern singleton du registre s'il en expose un.

    Priorité :
      1. ProviderRegistry.get_instance()  (si classmethod présent)
      2. ProviderRegistry()               (fallback)
    """
    get_instance = getattr(ProviderRegistry, "get_instance", None)
    if callable(get_instance):
        instance = get_instance()
        if instance is not None:
            return instance
    return ProviderRegistry()


def get_provider_registry() -> ProviderRegistry:
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = _acquire_provider_registry()
        # Initialiser si la méthode existe
        initialize = getattr(_provider_registry, "initialize", None)
        if callable(initialize):
            try:
                initialize()
            except Exception as e:
                logger.error(f"❌ Échec initialize providers : {e}", exc_info=True)
                raise
    return _provider_registry


def get_job_manager() -> JobManager:
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()

        start = getattr(_job_manager, "start", None)
        if callable(start):
            try:
                result = start()
                # Si start() est async, on prévient (impossible à awaited ici)
                if inspect.iscoroutine(result):
                    logger.warning(
                        "⚠️ JobManager.start() est async mais appelé en contexte sync. "
                        "Utilisez `await get_job_manager().start()` dans le lifespan "
                        "ou faites de start() une méthode sync qui planifie la tâche."
                    )
                    result.close()
            except Exception as e:
                logger.error(f"❌ Échec démarrage JobManager : {e}", exc_info=True)
                raise
    return _job_manager


def get_file_service() -> FileService:
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service


def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# ==========================================================================
#  Initialisation globale (appelée dans main.lifespan startup)
# ==========================================================================

def init_services() -> None:
    """Initialise tous les singletons. Idempotent."""
    logger.info("🚀 Initialisation des services NexusDL...")

    seed_default_admin()

    try:
        get_provider_registry()
        get_job_manager()
        get_file_service()
        get_cache_service()
        logger.info("✅ Services initialisés avec succès")
    except Exception as e:
        logger.error(f"❌ Échec init_services : {e}", exc_info=True)
        raise
