# ==========================================================================
#  NexusDL 2.0 - Modèle LibraryItem
#  Fichier : backend/app/models/library.py
#  Description : Table SQLAlchemy pour les éléments de bibliothèque
#  Version : 2.0.0
# ==========================================================================

"""
Modèle LibraryItem : représente un fichier téléchargé (typiquement un CBZ)
stocké dans la bibliothèque de l'utilisateur.

⚠️ IMPORTANT :
   La colonne de métadonnées s'appelle `extra_metadata` et NON `metadata`.
   `metadata` est un attribut réservé par SQLAlchemy (Declarative API).
   Toute tentative de définir `metadata = Column(...)` lève :
     sqlalchemy.exc.InvalidRequestError:
       Attribute name 'metadata' is reserved when using the Declarative API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

# ⚠️ Adapte cet import à l'emplacement réel de `Base` dans ton projet.
#    Si `Base` est défini dans `app/models/__init__.py`, importe-le depuis
#    un module `app.models.base` pour éviter un import circulaire.
from app.models.base import Base


class LibraryItem(Base):
    """
    Un élément de bibliothèque (CBZ, dossier d'images, etc.).
    """

    __tablename__ = "library_items"

    # ----------------------------------------------------------------------
    #  Colonnes
    # ----------------------------------------------------------------------

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Métadonnées principales
    title = Column(String(500), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    path = Column(String(1000), nullable=False, unique=True)

    # Informations fichier
    size_bytes = Column(BigInteger, default=0, nullable=False)
    page_count = Column(Integer, default=0, nullable=False)
    chapter_count = Column(Integer, default=0, nullable=False)

    # Métadonnées éditoriales
    author = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    language = Column(String(10), nullable=True, index=True)
    provider_id = Column(String(100), nullable=True, index=True)
    source_url = Column(String(1000), nullable=True)
    cover_path = Column(String(1000), nullable=True)

    # État utilisateur
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    is_favorite = Column(Boolean, default=False, nullable=False, index=True)
    reading_progress = Column(Float, default=0.0, nullable=False)

    # ⚠️ Colonne de métadonnées libres.
    #    NE PAS renommer en `metadata` — conflit avec SQLAlchemy.
    extra_metadata = Column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    last_read_at = Column(DateTime, nullable=True)

    # ----------------------------------------------------------------------
    #  Contraintes et index
    # ----------------------------------------------------------------------

    __table_args__ = (
        UniqueConstraint("path", name="uq_library_items_path"),
        Index("ix_library_items_created_desc", created_at.desc()),
        Index("ix_library_items_title_lower", title),
    )

    # ----------------------------------------------------------------------
    #  Méthodes utilitaires
    # ----------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<LibraryItem(id={self.id}, title={self.title!r}, "
            f"filename={self.filename!r})>"
        )

    @property
    def size_human(self) -> str:
        """Taille lisible (ex: '15.3 Mo')."""
        n = float(self.size_bytes or 0)
        for unit in ("o", "Ko", "Mo", "Go", "To"):
            if n < 1024.0:
                return f"{n:.1f} {unit}"
            n /= 1024.0
        return f"{n:.1f} Po"

    @property
    def progress_percent(self) -> float:
        """Progression de lecture en pourcentage (0–100)."""
        return max(0.0, min(100.0, (self.reading_progress or 0.0) * 100.0))

    def to_dict(self) -> Dict[str, Any]:
        """Sérialisation pour l'API."""
        return {
            "id": self.id,
            "title": self.title,
            "filename": self.filename,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "size_human": self.size_human,
            "page_count": self.page_count,
            "chapter_count": self.chapter_count,
            "author": self.author,
            "description": self.description,
            "language": self.language,
            "provider_id": self.provider_id,
            "source_url": self.source_url,
            "cover_path": self.cover_path,
            "is_read": self.is_read,
            "is_favorite": self.is_favorite,
            "reading_progress": self.reading_progress,
            "extra_metadata": self.extra_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_read_at": self.last_read_at.isoformat() if self.last_read_at else None,
        }

    # ----------------------------------------------------------------------
    #  Constructeur de commodité
    # ----------------------------------------------------------------------

    @classmethod
    def from_file(
        cls,
        *,
        title: str,
        filename: str,
        path: str,
        size_bytes: int = 0,
        extra_metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "LibraryItem":
        """
        Crée un LibraryItem à partir des informations d'un fichier.

        Utilisation typique dans engine.py :
            item = LibraryItem.from_file(
                title=analysis["title"],
                filename=cbz_path.name,
                path=str(cbz_path),
                size_bytes=cbz_path.stat().st_size,
                extra_metadata={"author": ..., "chapters": [...]},
            )
        """
        return cls(
            title=title,
            filename=filename,
            path=path,
            size_bytes=size_bytes,
            extra_metadata=extra_metadata or {},
            **kwargs,
        )


# ==========================================================================
#  NOTE pour le reste du code
# ==========================================================================
#
#  Partout où tu écrivais :
#
#      LibraryItem(..., metadata={...})
#      item.metadata
#      item.metadata["key"]
#
#  Remplace par :
#
#      LibraryItem(..., extra_metadata={...})
#      item.extra_metadata
#      item.extra_metadata["key"]
#
#  Fichiers typiquement concernés :
#    - backend/app/core/engine.py  (création d'items)
#    - backend/app/schemas/library.py  (schéma Pydantic)
#    - backend/app/api/v1/endpoints/library.py  (lecture/écriture)
#    - frontend/src/stores/library.js  (si le front lit `metadata`)
#
# ==========================================================================
