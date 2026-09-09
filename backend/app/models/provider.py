# ==========================================================================
#  NexusDL 2.0 - Modèle Provider
#  Fichier : backend/app/models/provider.py
# ==========================================================================

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON

from app.models import Base


class Provider(Base):
    """
    Modèle pour stocker les informations sur les providers (sites de scan).
    Permet de gérer l'activation/désactivation, les préférences, et les métadonnées.
    """
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(String(50), unique=True, nullable=False, index=True)  # Identifiant unique (ex: sushiscan)
    name = Column(String(100), nullable=False)  # Nom affiché
    base_url = Column(String(200), nullable=False)  # URL de base du site
    enabled = Column(Boolean, default=True, nullable=False)  # Activé ou désactivé
    nsfw = Column(Boolean, default=False, nullable=False)  # Contenu pour adultes
    languages = Column(JSON, default=list)  # Langues supportées (ex: ["fr", "en"])
    version = Column(String(20), default="1.0.0")  # Version du provider
    description = Column(Text, nullable=True)  # Description
    config = Column(JSON, nullable=True)  # Configuration spécifique (headers, timeout, etc.)
    priority = Column(Integer, default=0)  # Ordre de priorité (plus élevé = plus prioritaire)
    last_used = Column(DateTime, nullable=True)  # Dernière utilisation
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Provider(provider_id='{self.provider_id}', name='{self.name}', enabled={self.enabled})>"

    def is_available(self) -> bool:
        """Vérifie si le provider est disponible (activé)."""
        return self.enabled

    def supports_language(self, lang: str) -> bool:
        """Vérifie si le provider supporte une langue donnée."""
        if not self.languages:
            return False
        return lang in self.languages

    def to_dict(self) -> dict:
        """Convertit le provider en dictionnaire."""
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "name": self.name,
            "base_url": self.base_url,
            "enabled": self.enabled,
            "nsfw": self.nsfw,
            "languages": self.languages,
            "version": self.version,
            "description": self.description,
            "config": self.config,
            "priority": self.priority,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_provider_instance(cls, provider_id: str, provider_instance) -> "Provider":
        """
        Crée une instance Provider à partir d'une instance de provider concret.
        Permet de synchroniser les providers en base avec ceux du registre.
        """
        return cls(
            provider_id=provider_id,
            name=provider_instance.name,
            base_url=provider_instance.base_url,
            nsfw=getattr(provider_instance, 'nsfw', False),
            languages=getattr(provider_instance, 'supported_languages', []),
            version=getattr(provider_instance, 'version', '1.0.0'),
            description=getattr(provider_instance, 'description', ''),
            enabled=getattr(provider_instance, 'enabled', True),
        )

    @classmethod
    def get_enabled_providers(cls, session, include_nsfw: bool = False):
        """
        Récupère la liste des providers activés, optionnellement filtrés par NSFW.
        """
        query = session.query(cls).filter(cls.enabled == True)
        if not include_nsfw:
            query = query.filter(cls.nsfw == False)
        return query.order_by(cls.priority.desc(), cls.name).all()
