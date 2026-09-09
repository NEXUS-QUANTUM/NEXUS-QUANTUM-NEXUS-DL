# ==========================================================================
#  NexusDL 2.0 - Schémas Provider
#  Fichier : backend/app/schemas/provider.py
# ==========================================================================

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==========================================================================
#  Schémas de base - Provider
# ==========================================================================

class ProviderInfo(BaseModel):
    """Informations sur un provider."""
    id: str = Field(..., description="Identifiant unique du provider")
    name: str = Field(..., description="Nom affiché")
    base_url: str = Field(..., description="URL de base")
    languages: List[str] = Field(default_factory=list, description="Langues supportées")
    nsfw: bool = Field(False, description="Contenu pour adultes")
    version: str = Field("1.0.0", description="Version du provider")
    description: Optional[str] = Field(None, description="Description")
    enabled: bool = Field(True, description="Provider activé")
    priority: int = Field(0, description="Priorité (plus élevé = plus prioritaire)")

class ProviderListResponse(BaseModel):
    """Réponse pour la liste des providers."""
    providers: List[ProviderInfo]
    total: int


# ==========================================================================
#  Schémas pour l'analyse et la recherche
# ==========================================================================

class ChapterInfo(BaseModel):
    """Informations sur un chapitre."""
    id: str = Field(..., description="Identifiant unique du chapitre")
    title: str = Field(..., description="Titre du chapitre")
    number: Optional[float] = Field(None, description="Numéro du chapitre")
    volume: Optional[float] = Field(None, description="Numéro du volume")
    release_date: Optional[str] = Field(None, description="Date de publication")
    url: Optional[str] = Field(None, description="URL du chapitre")
    page_count: Optional[int] = Field(None, description="Nombre de pages")
    language: Optional[str] = Field(None, description="Langue du chapitre")
    is_available: bool = Field(True, description="Disponible au téléchargement")

class SeriesInfo(BaseModel):
    """Informations sur une série."""
    id: str = Field(..., description="Identifiant unique de la série")
    title: str = Field(..., description="Titre de la série")
    alt_titles: List[str] = Field(default_factory=list, description="Titres alternatifs")
    author: Optional[str] = Field(None, description="Auteur")
    artist: Optional[str] = Field(None, description="Artiste")
    description: Optional[str] = Field(None, description="Description")
    genre: List[str] = Field(default_factory=list, description="Genres")
    status: Optional[str] = Field(None, description="Statut (ongoing, completed, hiatus)")
    cover_url: Optional[str] = Field(None, description="URL de la couverture")
    url: str = Field(..., description="URL de la série")
    provider_id: str = Field(..., description="ID du provider")
    chapters: Optional[List[ChapterInfo]] = Field(None, description="Chapitres disponibles")
    total_chapters: Optional[int] = Field(None, description="Nombre total de chapitres")
    language: Optional[str] = Field(None, description="Langue")
    nsfw: bool = Field(False, description="Contenu pour adultes")
    year: Optional[int] = Field(None, description="Année de publication")
    rating: Optional[float] = Field(None, description="Note moyenne")

class SearchResult(BaseModel):
    """Résultat d'une recherche."""
    series_id: str = Field(..., description="ID de la série")
    title: str = Field(..., description="Titre")
    alt_titles: List[str] = Field(default_factory=list)
    author: Optional[str] = None
    cover_url: Optional[str] = None
    url: str = Field(..., description="URL de la série")
    provider_id: str = Field(..., description="ID du provider")
    provider_name: str = Field(..., description="Nom du provider")
    genre: List[str] = Field(default_factory=list)
    status: Optional[str] = None
    nsfw: bool = Field(False)
    language: Optional[str] = None

class SearchResponse(BaseModel):
    """Réponse pour une recherche."""
    query: str = Field(..., description="Terme recherché")
    results: List[SearchResult] = Field(default_factory=list)
    total: int = 0
    provider_id: Optional[str] = Field(None, description="Provider utilisé (ou 'all')")

class AnalysisResult(BaseModel):
    """Résultat de l'analyse d'une URL."""
    title: str = Field(..., description="Titre de la série")
    url: str = Field(..., description="URL analysée")
    provider_id: str = Field(..., description="ID du provider")
    chapters: List[ChapterInfo] = Field(default_factory=list)
    author: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    genre: List[str] = Field(default_factory=list)
    total_chapters: int = 0
    language: Optional[str] = None
    nsfw: bool = Field(False)


# ==========================================================================
#  Schémas pour la configuration des providers
# ==========================================================================

class ProviderConfig(BaseModel):
    """Configuration d'un provider."""
    enabled: bool = Field(True, description="Activer/désactiver")
    timeout: Optional[int] = Field(30, description="Timeout en secondes")
    headers: Dict[str, str] = Field(default_factory=dict, description="Headers personnalisés")
    proxy: Optional[str] = Field(None, description="Proxy à utiliser")
    rate_limit: Optional[int] = Field(None, description="Limite de requêtes par minute")
    max_retries: Optional[int] = Field(3, description="Nombre de tentatives max")
    language_filter: Optional[List[str]] = Field(None, description="Langues autorisées")

class ProviderConfigUpdate(BaseModel):
    """Mise à jour de la configuration d'un provider."""
    enabled: Optional[bool] = None
    timeout: Optional[int] = Field(None, ge=5, le=120)
    headers: Optional[Dict[str, str]] = None
    proxy: Optional[str] = None
    rate_limit: Optional[int] = Field(None, ge=1)
    max_retries: Optional[int] = Field(None, ge=1, le=10)
    language_filter: Optional[List[str]] = None


# ==========================================================================
#  Schémas pour les erreurs provider
# ==========================================================================

class ProviderErrorResponse(BaseModel):
    """Réponse d'erreur pour un provider."""
    provider_id: str
    error: str
    details: Optional[str] = None
    retryable: bool = Field(True)

# ==========================================================================
#  Notes
# ==========================================================================
#  - Ces schémas sont utilisés par les endpoints de browse et de downloads.
#  - Ils définissent la structure des données échangées avec le frontend.
#  - Les champs optionnels permettent de gérer les différences entre providers.
