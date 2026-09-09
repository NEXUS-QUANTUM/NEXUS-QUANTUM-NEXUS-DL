# ==========================================================================
#  NexusDL 2.0 - Modèle Utilisateur
#  Fichier : backend/app/models/user.py
# ==========================================================================

import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import declarative_base

from app.models import Base

# ==========================================================================
#  Énumérations
# ==========================================================================

class UserRole(str, enum.Enum):
    """Rôles utilisateur."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserStatus(str, enum.Enum):
    """Statut de l'utilisateur."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    PENDING = "pending"

# ==========================================================================
#  Modèle SQLAlchemy
# ==========================================================================

class User(Base):
    """Modèle utilisateur pour la base de données."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(200), nullable=True)
    preferences = Column(String(500), nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role={self.role})>"

    def is_active(self) -> bool:
        """Vérifie si l'utilisateur est actif."""
        return self.status == UserStatus.ACTIVE

    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur est administrateur."""
        return self.role == UserRole.ADMIN

    def to_dict(self) -> dict:
        """Convertit l'utilisateur en dictionnaire (sans le mot de passe)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value if self.role else None,
            "status": self.status.value if self.status else None,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

# ==========================================================================
#  Modèles Pydantic pour la sérialisation
#  (Utilisés dans les endpoints mais définis ailleurs - ici pour référence)
# ==========================================================================

# Note: Les schémas Pydantic sont définis dans app/schemas/user.py
# mais on peut ajouter des méthodes de conversion ici.

# ==========================================================================
#  Notes
# ==========================================================================
#  - Le modèle utilise SQLAlchemy avec déclarative_base définie dans
#    app/models/__init__.py.
#  - Les champs preferences stockent un JSON string pour les paramètres
#    utilisateur (thème, notifications, etc.).
#  - Les énumérations UserRole et UserStatus sont définies pour une
#    cohérence dans toute l'application.
#  - Les méthodes is_active et is_admin simplifient les vérifications.
