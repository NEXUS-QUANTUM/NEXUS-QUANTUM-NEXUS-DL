# ==========================================================================
#  NexusDL 2.0 - Authentication Endpoints
#  Fichier : backend/app/api/v1/endpoints/auth.py
# ==========================================================================

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole, UserCreate, UserInDB, Token, TokenData
from app.api.v1.endpoints.deps import get_db
from app.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# ==========================================================================
#  Configuration
# ==========================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ==========================================================================
#  Schémas
# ==========================================================================

class LoginRequest(BaseModel):
    username: str = Field(..., description="Nom d'utilisateur ou email")
    password: str = Field(..., description="Mot de passe")

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER

class RefreshRequest(BaseModel):
    refresh_token: str = Field(...)

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

# ==========================================================================
#  Fonctions utilitaires
# ==========================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe en clair contre un hachage."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hache un mot de passe."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token d'accès JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Crée un token de rafraîchissement JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Décode et valide un token JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise AuthenticationError(f"Token invalide: {str(e)}")

def get_user(db: Session, username: str) -> Optional[User]:
    """Récupère un utilisateur par son nom d'utilisateur."""
    # Simuler une requête DB - à remplacer par une vraie requête SQLAlchemy
    # Pour l'instant, on utilise un dictionnaire en mémoire.
    # Nous définirons une fonction de stockage plus tard.
    from app.api.v1.endpoints.deps import users_db
    return users_db.get(username)

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authentifie un utilisateur par nom d'utilisateur et mot de passe."""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# ==========================================================================
#  Endpoints
# ==========================================================================

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Inscription d'un nouvel utilisateur.
    Le rôle par défaut est 'user'.
    """
    # Vérifier si l'utilisateur existe déjà
    existing = get_user(db, user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur est déjà pris."
        )
    # Vérifier si l'email est déjà utilisé
    for u in users_db.values():
        if u.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet email est déjà utilisé."
            )
    # Créer l'utilisateur
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        id=len(users_db) + 1,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    users_db[user_data.username] = new_user
    
    # Générer les tokens
    access_token = create_access_token(data={"sub": new_user.username})
    refresh_token = create_refresh_token(data={"sub": new_user.username})
    
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role.value,
            "created_at": new_user.created_at.isoformat()
        }
    )

@router.post("/login", response_model=AuthResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Connexion avec nom d'utilisateur et mot de passe.
    Retourne un access_token et un refresh_token.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat()
        }
    )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    refresh_data: RefreshRequest = Body(...)
):
    """
    Rafraîchit le token d'accès en utilisant le refresh_token.
    """
    try:
        payload = decode_token(refresh_data.refresh_token)
        token_type = payload.get("type")
        if token_type != "refresh":
            raise AuthenticationError("Token invalide: type attendu 'refresh'")
        
        username = payload.get("sub")
        if not username:
            raise AuthenticationError("Token invalide: utilisateur manquant")
        
        # Vérifier que l'utilisateur existe toujours
        user = users_db.get(username)
        if not user:
            raise AuthenticationError("Utilisateur non trouvé")
        
        # Créer un nouveau access token
        new_access_token = create_access_token(data={"sub": username})
        new_refresh_token = create_refresh_token(data={"sub": username})
        
        return AuthResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "created_at": user.created_at.isoformat()
            }
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Erreur lors du rafraîchissement: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de rafraîchissement invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/me", response_model=dict)
async def get_current_user_info(
    token: str = Depends(oauth2_scheme)
):
    """
    Récupère les informations de l'utilisateur connecté.
    """
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise AuthenticationError("Utilisateur manquant dans le token")
        user = users_db.get(username)
        if not user:
            raise AuthenticationError("Utilisateur non trouvé")
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat()
        }
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme)
):
    """
    Déconnexion (invalide le token côté serveur). 
    Note: Pour une API stateless, le client doit simplement supprimer le token localement.
    On peut implémenter une blacklist si nécessaire.
    """
    # Pour une API stateless, on ne fait rien de spécial côté serveur.
    # Le client est responsable de supprimer son token.
    return {"message": "Déconnexion réussie. Supprimez le token côté client."}

# ==========================================================================
#  Notes
# ==========================================================================
#  - Les utilisateurs sont stockés dans un dictionnaire en mémoire (users_db),
#    importé depuis deps. Ce n'est pas persistant. En production, utilisez
#    une base de données (SQLAlchemy).
#  - Les tokens JWT sont signés avec la clé secrète définie dans settings.
#  - La sécurité des mots de passe est assurée par bcrypt.
#  - Le rôle ADMIN permet d'accéder aux endpoints d'administration.
