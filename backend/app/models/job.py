# ==========================================================================
#  NexusDL 2.0 - Modèle Job
#  Fichier : backend/app/models/job.py
# ==========================================================================

import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models import Base


# ==========================================================================
#  Énumérations
# ==========================================================================

class JobStatus(str, enum.Enum):
    """Statuts possibles d'un job de téléchargement."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    WAITING = "waiting"

class JobPriority(str, enum.Enum):
    """Priorités d'un job."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class JobType(str, enum.Enum):
    """Types de jobs."""
    DOWNLOAD = "download"
    ANALYZE = "analyze"
    EXTRACT = "extract"
    CONVERT = "convert"
    CLEANUP = "cleanup"


# ==========================================================================
#  Modèle SQLAlchemy
# ==========================================================================

class Job(Base):
    """
    Modèle représentant un job de téléchargement ou d'analyse.
    Stocké en base de données pour la persistance.
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, nullable=False, index=True)  # ID externe (ex: job_1234567890)
    type = Column(SQLEnum(JobType), default=JobType.DOWNLOAD, nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    priority = Column(SQLEnum(JobPriority), default=JobPriority.NORMAL, nullable=False)

    # Informations sur la série
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    provider_id = Column(String(50), nullable=False)

    # Progression
    total_chapters = Column(Integer, default=0, nullable=False)
    done_chapters = Column(Integer, default=0, nullable=False)
    total_pages = Column(Integer, default=0, nullable=False)
    done_pages = Column(Integer, default=0, nullable=False)
    progress = Column(Float, default=0.0, nullable=False)

    # Détails du chapitre en cours
    current_chapter = Column(String(100), nullable=True)
    current_chapter_id = Column(String(100), nullable=True)

    # Données du job (sérialisées)
    data = Column(JSON, nullable=True)  # Contient les infos des chapitres, options, etc.
    logs = Column(JSON, default=list)  # Liste des messages de log
    errors = Column(JSON, default=list)  # Liste des erreurs rencontrées

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Utilisateur associé (optionnel)
    user_id = Column(Integer, nullable=True, index=True)

    # Résultat (chemin du fichier CBZ généré)
    result_path = Column(String(500), nullable=True)
    result_size = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<Job(job_id='{self.job_id}', title='{self.title}', status={self.status})>"

    def is_active(self) -> bool:
        """Vérifie si le job est en cours d'exécution ou en attente."""
        return self.status in (JobStatus.PENDING, JobStatus.RUNNING, JobStatus.WAITING, JobStatus.PAUSED)

    def is_finished(self) -> bool:
        """Vérifie si le job est terminé (succès, échec ou annulation)."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)

    def start(self):
        """Marque le job comme démarré."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, result_path: Optional[str] = None, result_size: Optional[int] = None):
        """Marque le job comme terminé avec succès."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.progress = 100.0
        if result_path:
            self.result_path = result_path
        if result_size:
            self.result_size = result_size

    def fail(self, error_message: str):
        """Marque le job comme échoué."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if self.errors is None:
            self.errors = []
        self.errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": error_message
        })

    def cancel(self):
        """Annule le job."""
        self.status = JobStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_progress(self, done_chapters: int, total_chapters: int, current_chapter: str = None):
        """Met à jour la progression du job."""
        self.done_chapters = done_chapters
        self.total_chapters = total_chapters
        if total_chapters > 0:
            self.progress = (done_chapters / total_chapters) * 100
        if current_chapter:
            self.current_chapter = current_chapter
        self.updated_at = datetime.utcnow()

    def add_log(self, message: str, level: str = "info"):
        """Ajoute un message de log au job."""
        if self.logs is None:
            self.logs = []
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message
        })
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convertit le job en dictionnaire pour les API."""
        return {
            "id": self.job_id,
            "type": self.type.value if self.type else None,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "title": self.title,
            "url": self.url,
            "provider_id": self.provider_id,
            "total_chapters": self.total_chapters,
            "done_chapters": self.done_chapters,
            "total_pages": self.total_pages,
            "done_pages": self.done_pages,
            "progress": self.progress,
            "current_chapter": self.current_chapter,
            "data": self.data,
            "logs": self.logs,
            "errors": self.errors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "user_id": self.user_id,
            "result_path": self.result_path,
            "result_size": self.result_size,
        }


# ==========================================================================
#  Modèles auxiliaires pour la gestion des jobs en mémoire
# ==========================================================================

class JobInMemory:
    """
    Version simplifiée du job pour une utilisation en mémoire (sans SQLAlchemy).
    Utilisée par le JobManager pour les jobs actifs.
    """
    def __init__(
        self,
        job_id: str,
        title: str = "",
        url: str = "",
        type: JobType = JobType.DOWNLOAD,
        priority: JobPriority = JobPriority.NORMAL,
        total_chapters: int = 0,
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ):
        self.id = job_id
        self.title = title
        self.url = url
        self.type = type
        self.priority = priority
        self.status = JobStatus.PENDING
        self.total_chapters = total_chapters
        self.done_chapters = 0
        self.total_pages = 0
        self.done_pages = 0
        self.progress = 0.0
        self.current_chapter = ""
        self.current_chapter_id = None
        self.data = data or {}
        self.logs = []
        self.errors = []
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at
        self.started_at = None
        self.completed_at = None
        self.cancelled_at = None
        self.user_id = user_id
        self.result_path = None
        self.result_size = None
        self.provider_id = None

    def to_dict(self) -> dict:
        """Convertit le job en dictionnaire pour les API."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "type": self.type.value if self.type else None,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "total_chapters": self.total_chapters,
            "done_chapters": self.done_chapters,
            "total_pages": self.total_pages,
            "done_pages": self.done_pages,
            "progress": self.progress,
            "current_chapter": self.current_chapter,
            "logs": self.logs,
            "errors": self.errors,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
            "user_id": self.user_id,
            "result_path": self.result_path,
            "result_size": self.result_size,
        }

    def update_from_engine(self, job_dict: Dict[str, Any]):
        """Met à jour le job à partir des données du moteur."""
        for key, value in job_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow().isoformat()
