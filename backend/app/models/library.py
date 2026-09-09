# ==========================================================================
#  NexusDL 2.0 - Modèle Bibliothèque
#  Fichier : backend/app/models/library.py
# ==========================================================================

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, JSON, Boolean
from sqlalchemy.orm import relationship

from app.models import Base
from app.core.exceptions import FileNotFoundError


class LibraryItem(Base):
    """
    Modèle représentant un élément de la bibliothèque (fichier CBZ).
    Stocke les métadonnées extraites du fichier ComicInfo.xml.
    """
    __tablename__ = "library_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    filename = Column(String(200), unique=True, nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_read = Column(DateTime, nullable=True)
    read_count = Column(Integer, default=0, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    rating = Column(Integer, default=0, nullable=False)  # 0-10

    # Métadonnées extraites (sérialisées en JSON)
    metadata = Column(JSON, nullable=True)  # Contient les champs: author, series, genre, description, etc.

    # Tags (liste de chaînes)
    tags = Column(JSON, default=list)

    # Couverture (chemin vers une miniature)
    cover_path = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<LibraryItem(id={self.id}, title='{self.title}', filename='{self.filename}')>"

    def get_metadata(self) -> Dict[str, Any]:
        """Retourne les métadonnées sous forme de dictionnaire."""
        return self.metadata or {}

    def get_tags(self) -> List[str]:
        """Retourne la liste des tags."""
        return self.tags or []

    def add_tag(self, tag: str):
        """Ajoute un tag à l'élément."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Supprime un tag de l'élément."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def toggle_favorite(self):
        """Bascule l'état favori."""
        self.is_favorite = not self.is_favorite

    def record_read(self):
        """Enregistre une lecture."""
        self.last_read = datetime.utcnow()
        self.read_count += 1

    def set_rating(self, rating: int):
        """Définit la note (0-10)."""
        if 0 <= rating <= 10:
            self.rating = rating
        else:
            raise ValueError("La note doit être comprise entre 0 et 10.")

    def update_metadata(self, new_metadata: Dict[str, Any]):
        """Met à jour les métadonnées en fusionnant avec les existantes."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata.update(new_metadata)

    def get_size_formatted(self) -> str:
        """Retourne la taille formatée."""
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def to_dict(self) -> dict:
        """Convertit l'élément en dictionnaire."""
        return {
            "id": self.id,
            "title": self.title,
            "filename": self.filename,
            "file_path": self.file_path,
            "size_bytes": self.size_bytes,
            "size_formatted": self.get_size_formatted(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_read": self.last_read.isoformat() if self.last_read else None,
            "read_count": self.read_count,
            "is_favorite": self.is_favorite,
            "rating": self.rating,
            "metadata": self.metadata,
            "tags": self.tags,
            "cover_path": self.cover_path,
        }

    @classmethod
    def from_cbz(cls, file_path: str, title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> "LibraryItem":
        """
        Crée une instance de LibraryItem à partir d'un fichier CBZ.
        Extrait automatiquement les métadonnées si disponibles.
        """
        import os
        from app.core.cbz_builder import CbzBuilder

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")

        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        base_title = title or os.path.splitext(filename)[0]

        # Extraire les métadonnées du CBZ
        cbz_builder = CbzBuilder()
        extracted_metadata = cbz_builder.extract_metadata(file_path)
        if metadata:
            if extracted_metadata:
                extracted_metadata.update(metadata)
            else:
                extracted_metadata = metadata

        return cls(
            title=base_title,
            filename=filename,
            file_path=file_path,
            size_bytes=size,
            metadata=extracted_metadata,
            tags=[]
        )
