# ==========================================================================
#  NexusDL 2.0 - Dépendances globales
#  Fichier : backend/app/api/deps.py
# ==========================================================================

import logging
from typing import Optional, Dict, Any, Generator
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
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

# Création de l'engine SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dépendance pour obtenir une session de base de données.
    S'assure de fermer la session après utilisation.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================================================
#  Utilisateurs (stockage temporaire en mémoire)
# ==========================================================================

# Simuler une base de données utilisateurs en mémoire
# Pour un vrai projet, utiliser une table SQL
users_db: Dict[str, User] = {}

def get_user_by_username(username: str) -> Optional[User]:
    """Récupère un utilisateur par son nom d'utilisateur."""
    return users_db.get(username)

def get_user_by_id(user_id: int) -> Optional[User]:
    """Récupère un utilisateur par son ID."""
    for user in users_db.values():
        if user.id == user_id:
            return user
    return None

def create_user(user_data: dict) -> User:
    """Crée un nouvel utilisateur en mémoire."""
    new_id = max([u.id for u in users_db.values()] + [0]) + 1
    user = User(
        id=new_id,
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=user_data["hashed_password"],
        role=user_data.get("role", UserRole.USER),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    users_db[user.username] = user
    return user

def seed_default_admin():
    """Crée un admin par défaut si aucun utilisateur n'existe."""
    if not users_db:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        admin_user = {
            "username": "admin",
            "email": "admin@nexusdl.local",
            "hashed_password": pwd_context.hash("admin123"),
            "role": UserRole.ADMIN
        }
        create_user(admin_user)
        logger.info("✅ Utilisateur admin créé par défaut (mot de passe: admin123)")

# ==========================================================================
#  Authentification JWT
# ==========================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dépendance pour récupérer l'utilisateur courant à partir du token JWT.
    Lève une exception HTTP 401 si le token est invalide.
    """
    try:
        from app.api.v1.endpoints.auth import decode_token
        payload = decode_token(token)
        username = payload.get("sub")
        if username is None:
            raise AuthenticationError("Token invalide: utilisateur manquant")
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
        logger.error(f"Erreur d'authentification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Vérifie que l'utilisateur est actif."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisateur inactif"
        )
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Vérifie que l'utilisateur a le rôle ADMIN."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privilèges d'administrateur requis"
        )
    return current_user

# ==========================================================================
#  Services (singletons)
# ==========================================================================

# Instances globales
_provider_registry: Optional[ProviderRegistry] = None
_job_manager: Optional[JobManager] = None
_file_service: Optional[FileService] = None
_cache_service: Optional[CacheService] = None

def get_provider_registry() -> ProviderRegistry:
    """
    Dépendance pour obtenir le registre des providers.
    Crée l'instance si elle n'existe pas.
    """
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = ProviderRegistry()
        # Initialiser les providers (charge la liste)
        try:
            _provider_registry.initialize()
        except Exception as e:
            logger.error(f"Erreur initialisation providers: {e}")
            raise
    return _provider_registry

def get_job_manager() -> JobManager:
    """
    Dépendance pour obtenir le gestionnaire de jobs.
    Crée l'instance si elle n'existe pas.
    """
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
        try:
            _job_manager.start()
        except Exception as e:
            logger.error(f"Erreur démarrage JobManager: {e}")
            raise
    return _job_manager

def get_file_service() -> FileService:
    """
    Dépendance pour obtenir le service de gestion de fichiers.
    """
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service

def get_cache_service() -> CacheService:
    """
    Dépendance pour obtenir le service de cache.
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

# ==========================================================================
#  Initialisation des services au démarrage
# ==========================================================================

def init_services():
    """Initialise tous les services (à appeler au démarrage de l'application)."""
    logger.info("🚀 Initialisation des services NexusDL...")
    
    # Créer un admin par défaut
    seed_default_admin()
    
    # Forcer l'initialisation des singletons
    try:
        get_provider_registry()
        get_job_manager()
        get_file_service()
        get_cache_service()
        logger.info("✅ Services initialisés avec succès")
    except Exception as e:
        logger.error(f"❌ Échec de l'initialisation des services: {e}")
        raise

# ==========================================================================
#  Notes
# ==========================================================================
#  - Les singletons sont créés au premier appel et réutilisés.
#  - Les sessions de base de données sont créées à chaque requête.
#  - Le registre des providers charge tous les providers lors de l'initialisation.
#  - La gestion des utilisateurs en mémoire est temporaire; utiliser une base
#    de données en production.
#  - Les dépendances sont utilisées dans les endpoints via `Depends(...)`.
#  - Appeler `init_services()` dans `main.py` au démarrage de l'application.
