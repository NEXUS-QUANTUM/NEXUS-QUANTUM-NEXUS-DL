# ==========================================================================
#  NexusDL 2.0 - Schémas Utilisateur
#  Fichier : backend/app/schemas/user.py
# ==========================================================================

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict

from app.models.user import UserRole, UserStatus


# ==========================================================================
#  Schémas de base
# ==========================================================================

class UserBase(BaseModel):
    """Schéma de base pour un utilisateur."""
    username: str = Field(..., min_length=3, max_length=50, description="Nom d'utilisateur")
    email: EmailStr = Field(..., description="Adresse email")
    full_name: Optional[str] = Field(None, max_length=100, description="Nom complet")
    role: UserRole = Field(default=UserRole.USER, description="Rôle")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Statut")
    avatar_url: Optional[str] = Field(None, max_length=200, description="URL de l'avatar")
    preferences: Optional[str] = Field(None, description="Préférences utilisateur (JSON)")


class UserCreate(BaseModel):
    """Schéma pour la création d'un utilisateur."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=6, description="Mot de passe")
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = Field(default=UserRole.USER)

    @field_validator('password')
    def validate_password(cls, v):
        """Valide la force du mot de passe."""
        if len(v) < 6:
            raise ValueError('Le mot de passe doit contenir au moins 6 caractères')
        if not any(c.isdigit() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        if not any(c.isupper() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        return v


class UserUpdate(BaseModel):
    """Schéma pour la mise à jour d'un utilisateur."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=200)
    preferences: Optional[str] = None


class UserStatusUpdate(BaseModel):
    """Schéma pour la mise à jour du statut d'un utilisateur."""
    status: UserStatus = Field(..., description="Nouveau statut")


class UserRoleUpdate(BaseModel):
    """Schéma pour la mise à jour du rôle d'un utilisateur."""
    role: UserRole = Field(..., description="Nouveau rôle")


# ==========================================================================
#  Schémas d'authentification
# ==========================================================================

class UserLogin(BaseModel):
    """Schéma pour la connexion d'un utilisateur."""
    username: str = Field(..., description="Nom d'utilisateur")
    password: str = Field(..., description="Mot de passe")


class UserLoginResponse(BaseModel):
    """Schéma pour la réponse de connexion."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class TokenRefresh(BaseModel):
    """Schéma pour le rafraîchissement du token."""
    refresh_token: str = Field(..., description="Token de rafraîchissement")


class TokenResponse(BaseModel):
    """Schéma pour la réponse avec tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordChange(BaseModel):
    """Schéma pour le changement de mot de passe."""
    old_password: str = Field(..., description="Ancien mot de passe")
    new_password: str = Field(..., min_length=6, description="Nouveau mot de passe")

    @field_validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('Le mot de passe doit contenir au moins 6 caractères')
        if not any(c.isdigit() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        if not any(c.isupper() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        return v


class PasswordResetRequest(BaseModel):
    """Schéma pour la demande de réinitialisation de mot de passe."""
    email: EmailStr = Field(..., description="Adresse email")


class PasswordResetConfirm(BaseModel):
    """Schéma pour la confirmation de réinitialisation de mot de passe."""
    token: str = Field(..., description="Token de réinitialisation")
    new_password: str = Field(..., min_length=6, description="Nouveau mot de passe")

    @field_validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('Le mot de passe doit contenir au moins 6 caractères')
        return v


# ==========================================================================
#  Schémas de réponse
# ==========================================================================

class UserResponse(BaseModel):
    """Schéma pour la réponse d'un utilisateur (lecture publique)."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    status: str
    avatar_url: Optional[str] = None
    created_at: str
    updated_at: str
    last_login: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserWithPreferences(UserResponse):
    """Schéma pour la réponse d'un utilisateur avec ses préférences."""
    preferences: Optional[str] = None


class UserListResponse(BaseModel):
    """Schéma pour une liste paginée d'utilisateurs."""
    items: List[UserResponse]
    total: int
    offset: int
    limit: int


# ==========================================================================
#  Schémas pour les sessions
# ==========================================================================

class SessionResponse(BaseModel):
    """Schéma pour une session utilisateur."""
    id: int
    user_id: int
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    expires_at: str
    created_at: str
    is_revoked: bool

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    """Schéma pour une liste de sessions."""
    sessions: List[SessionResponse]
    total: int


# ==========================================================================
#  Schémas pour l'administration
# ==========================================================================

class UserSearchFilters(BaseModel):
    """Filtres de recherche pour les utilisateurs (admin)."""
    search: Optional[str] = Field(None, description="Recherche textuelle (username, email)")
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_by: str = Field("created_at", description="Champ de tri")
    sort_order: str = Field("desc", description="Ordre de tri (asc, desc)")


class AdminUserCreate(BaseModel):
    """Schéma pour la création d'un utilisateur par un administrateur."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = Field(default=UserRole.USER)
    status: UserStatus = Field(default=UserStatus.ACTIVE)


class AdminUserUpdate(UserUpdate):
    """Schéma pour la mise à jour d'un utilisateur par un administrateur."""
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


# ==========================================================================
#  Notes
# ==========================================================================
#  - Les schémas utilisent Pydantic V2 avec `model_config = ConfigDict(from_attributes=True)`
#    pour la conversion automatique depuis les modèles SQLAlchemy.
#  - Les validateurs assurent la qualité des données (email, mot de passe, etc.).
#  - Les réponses n'incluent jamais le mot de passe haché.
#  - La séparation entre UserResponse et UserWithPreferences permet de contrôler
#    les données exposées selon le contexte (public vs privé).
