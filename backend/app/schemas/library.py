# ==========================================================================
#  NexusDL 2.0 - Schémas Bibliothèque
#  Fichier : backend/app/schemas/library.py
# ==========================================================================

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ==========================================================================
#  Schémas de base
# ==========================================================================

class LibraryMetadata(BaseModel):
    """Métadonnées extraites d'un fichier CBZ."""
    title: Optional[str] = None
    series: Optional[str] = None
    author: Optional[str] = None
    artist: Optional[str] = None
    publisher: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    volume: Optional[str] = None
    chapters: Optional[int] = None
    pages: Optional[int] = None
    year: Optional[int] = None
    language: Optional[str] = None
    manga: Optional[str] = None  # "Yes" ou "No"

class LibraryItemBase(BaseModel):
    """Schéma de base pour un élément de bibliothèque."""
    title: str = Field(..., description="Titre de l'œuvre", max_length=200)
    filename: str = Field(..., description="Nom du fichier", max_length=200)
    file_path: str = Field(..., description="Chemin du fichier", max_length=500)
    size_bytes: int = Field(..., description="Taille en octets")
    metadata: Optional[LibraryMetadata] = Field(None, description="Métadonnées extraites")
    tags: List[str] = Field(default_factory=list, description="Tags")
    is_favorite: bool = Field(False, description="Favori")
    rating: int = Field(0, description="Note (0-10)")
    cover_path: Optional[str] = Field(None, description="Chemin de la miniature")

class LibraryItemCreate(LibraryItemBase):
    """Schéma pour la création d'un élément de bibliothèque (ajout automatique)."""
    pass

class LibraryItemUpdate(BaseModel):
    """Schéma pour la mise à jour d'un élément de bibliothèque (tags, favori, note)."""
    title: Optional[str] = Field(None, max_length=200)
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    rating: Optional[int] = Field(None, ge=0, le=10)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 10):
            raise ValueError('La note doit être comprise entre 0 et 10')
        return v

class LibraryItemResponse(LibraryItemBase):
    """Schéma pour la réponse d'un élément de bibliothèque."""
    id: int
    created_at: str
    updated_at: str
    last_read: Optional[str] = None
    read_count: int = 0
    size_formatted: str = Field("", description="Taille formatée")

    class Config:
        from_attributes = True

class LibraryListResponse(BaseModel):
    """Schéma pour une liste paginée d'éléments de bibliothèque."""
    items: List[LibraryItemResponse]
    total: int
    offset: int
    limit: int

# ==========================================================================
#  Schémas pour les statistiques et filtres
# ==========================================================================

class LibraryStats(BaseModel):
    """Statistiques de la bibliothèque."""
    total_items: int
    total_size_bytes: int
    total_size_formatted: str
    oldest_item: Optional[str] = None  # date ISO
    newest_item: Optional[str] = None
    average_size_bytes: Optional[float] = None
    genres: List[str] = Field(default_factory=list)
    authors: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    favorites_count: int = 0
    unread_count: int = 0

class LibrarySearchFilters(BaseModel):
    """Filtres de recherche pour la bibliothèque."""
    search: Optional[str] = Field(None, description="Recherche textuelle (titre, auteur)")
    genre: Optional[str] = None
    author: Optional[str] = None
    tag: Optional[str] = None
    favorite: Optional[bool] = None
    min_rating: Optional[int] = Field(None, ge=0, le=10)
    max_rating: Optional[int] = Field(None, ge=0, le=10)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_by: str = Field("created_at", description="Champ de tri (title, created_at, size, rating, last_read)")
    sort_order: str = Field("desc", description="Ordre de tri (asc, desc)")

    @field_validator('sort_by')
    def validate_sort_by(cls, v):
        allowed = ['title', 'created_at', 'size', 'rating', 'last_read', 'read_count']
        if v not in allowed:
            raise ValueError(f"sort_by doit être parmi {allowed}")
        return v

    @field_validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError("sort_order doit être 'asc' ou 'desc'")
        return v

# ==========================================================================
#  Schémas pour les actions
# ==========================================================================

class LibraryActionResponse(BaseModel):
    """Réponse générique pour les actions sur la bibliothèque."""
    success: bool
    message: str
    item_id: Optional[int] = None
