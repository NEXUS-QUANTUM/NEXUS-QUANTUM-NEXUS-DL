# ==========================================================================
#  NexusDL 2.0 - Modèle Session
#  Fichier : backend/app/models/session.py
# ==========================================================================

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.models import Base
from app.core.config import settings


class Session(Base):
    """
    Modèle pour stocker les sessions utilisateur (tokens de rafraîchissement).
    Permet la gestion des sessions actives et l'invalidation des tokens.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=False, index=True)
    user_agent = Column(String(200), nullable=True)
    ip_address = Column(String(45), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    # Relations
    user = relationship("User", backref="sessions")

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    def is_expired(self) -> bool:
        """Vérifie si la session a expiré."""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Vérifie si la session est valide (non expirée et non révoquée)."""
        return not self.is_revoked and not self.is_expired()

    def revoke(self):
        """Révoque la session."""
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()

    def extend(self, days: Optional[int] = None):
        """Prolonge la durée de vie de la session."""
        if days is None:
            days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convertit la session en dictionnaire."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "refresh_token": self.refresh_token,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_revoked": self.is_revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }

    @classmethod
    def create_from_refresh_token(
        cls,
        user_id: int,
        refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        expires_days: Optional[int] = None
    ) -> "Session":
        """
        Crée une nouvelle session à partir d'un refresh token.
        """
        if expires_days is None:
            expires_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        return cls(
            user_id=user_id,
            refresh_token=refresh_token,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at
        )

    @classmethod
    def get_valid_session(cls, session, refresh_token: str):
        """
        Récupère une session valide (non révoquée et non expirée) depuis la base.
        Retourne l'objet Session ou None.
        """
        query = session.query(cls).filter(
            cls.refresh_token == refresh_token,
            cls.is_revoked == False,
            cls.expires_at > datetime.utcnow()
        )
        return query.first()

    @classmethod
    def revoke_all_user_sessions(cls, session, user_id: int):
        """
        Révoque toutes les sessions actives d'un utilisateur.
        """
        sessions = session.query(cls).filter(
            cls.user_id == user_id,
            cls.is_revoked == False
        ).all()
        for s in sessions:
            s.revoke()
        session.commit()
        return len(sessions)
