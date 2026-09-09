# ==========================================================================
#  NexusDL 2.0 - Schémas Job
#  Fichier : backend/app/schemas/job.py
# ==========================================================================

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models.job import JobStatus, JobPriority, JobType


# ==========================================================================
#  Schémas de base
# ==========================================================================

class JobBase(BaseModel):
    """Schéma de base pour un job."""
    title: str = Field(..., description="Titre de la série")
    url: str = Field(..., description="URL de la série ou du chapitre")
    provider_id: Optional[str] = Field(None, description="ID du provider")
    type: JobType = Field(default=JobType.DOWNLOAD, description="Type de job")
    priority: JobPriority = Field(default=JobPriority.NORMAL, description="Priorité")
    total_chapters: int = Field(default=0, description="Nombre total de chapitres")
    data: Optional[Dict[str, Any]] = Field(None, description="Données supplémentaires")

class JobCreate(JobBase):
    """Schéma pour la création d'un job."""
    chapter_ids: List[str] = Field(..., description="Liste des IDs de chapitres à télécharger")
    options: Optional[Dict[str, Any]] = Field(None, description="Options de téléchargement")

class JobUpdate(BaseModel):
    """Schéma pour la mise à jour d'un job (progression, statut, logs)."""
    status: Optional[JobStatus] = None
    progress: Optional[float] = Field(None, ge=0, le=100)
    done_chapters: Optional[int] = None
    current_chapter: Optional[str] = None
    logs: Optional[List[Dict[str, Any]]] = None
    result_path: Optional[str] = None
    result_size: Optional[int] = None
    errors: Optional[List[Dict[str, Any]]] = None

class JobResponse(BaseModel):
    """Schéma pour la réponse d'un job (lecture)."""
    id: str = Field(..., description="ID du job")
    title: str = Field(..., description="Titre de la série")
    url: str = Field(..., description="URL de la série")
    provider_id: Optional[str] = Field(None, description="ID du provider")
    type: JobType = Field(default=JobType.DOWNLOAD, description="Type de job")
    priority: JobPriority = Field(default=JobPriority.NORMAL, description="Priorité")
    status: JobStatus = Field(..., description="Statut actuel")
    total_chapters: int = Field(default=0, description="Nombre total de chapitres")
    done_chapters: int = Field(default=0, description="Chapitres terminés")
    total_pages: Optional[int] = Field(0, description="Nombre total de pages")
    done_pages: Optional[int] = Field(0, description="Pages terminées")
    progress: float = Field(0.0, description="Progression en pourcentage")
    current_chapter: Optional[str] = Field("", description="Chapitre en cours")
    created_at: str = Field(..., description="Date de création")
    updated_at: str = Field(..., description="Date de dernière mise à jour")
    started_at: Optional[str] = Field(None, description="Date de début")
    completed_at: Optional[str] = Field(None, description="Date de fin")
    cancelled_at: Optional[str] = Field(None, description="Date d'annulation")
    logs: List[Dict[str, Any]] = Field(default_factory=list, description="Logs du job")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Erreurs rencontrées")
    user_id: Optional[int] = Field(None, description="ID de l'utilisateur associé")
    result_path: Optional[str] = Field(None, description="Chemin du fichier CBZ généré")
    result_size: Optional[int] = Field(None, description="Taille du fichier CBZ")

    class Config:
        from_attributes = True

class JobListResponse(BaseModel):
    """Schéma pour une liste paginée de jobs."""
    items: List[JobResponse] = Field(..., description="Liste des jobs")
    total: int = Field(..., description="Nombre total de jobs")
    offset: int = Field(0, description="Décalage")
    limit: int = Field(20, description="Limite par page")

class JobStatusUpdate(BaseModel):
    """Schéma pour la mise à jour du statut d'un job (par WebSocket)."""
    event: str = Field(..., description="Type d'événement (job_updated, job_started, job_finished)")
    job_id: str = Field(..., description="ID du job")
    data: Dict[str, Any] = Field(..., description="Données du job")

# ==========================================================================
#  Schémas pour les requêtes d'action
# ==========================================================================

class JobCancelRequest(BaseModel):
    """Schéma pour annuler un job."""
    job_id: str = Field(..., description="ID du job à annuler")
    force: bool = Field(False, description="Forcer l'annulation même si le job est en cours")

class JobRetryRequest(BaseModel):
    """Schéma pour relancer un job échoué."""
    job_id: str = Field(..., description="ID du job à relancer")
    skip_done: bool = Field(True, description="Ignorer les chapitres déjà téléchargés")

# ==========================================================================
#  Validateurs personnalisés
# ==========================================================================

class JobFilters(BaseModel):
    """Schéma pour les filtres de liste des jobs."""
    status: Optional[JobStatus] = None
    type: Optional[JobType] = None
    priority: Optional[JobPriority] = None
    title_contains: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

    @field_validator('status', mode='before')
    def validate_status(cls, v):
        if v is not None:
            try:
                return JobStatus(v)
            except ValueError:
                raise ValueError(f"Statut invalide: {v}")
        return v

    @field_validator('type', mode='before')
    def validate_type(cls, v):
        if v is not None:
            try:
                return JobType(v)
            except ValueError:
                raise ValueError(f"Type invalide: {v}")
        return v

    @field_validator('priority', mode='before')
    def validate_priority(cls, v):
        if v is not None:
            try:
                return JobPriority(v)
            except ValueError:
                raise ValueError(f"Priorité invalide: {v}")
        return v
