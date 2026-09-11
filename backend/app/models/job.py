# ==========================================================================
#  NexusDL 2.0 - Modèle Job
#  Fichier : backend/app/models/job.py
#  Version : 2.0.0
# ==========================================================================

import enum
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    Index,
    Integer,
    String,
    Text,
)

# ⚠️ Import depuis `app.models.base` et NON `app.models` :
#    `app.models.__init__` importe `job.py`, donc importer `Base` depuis
#    `app.models` crée un import circulaire.
from app.models.base import Base


# ==========================================================================
#  Énumérations
# ==========================================================================

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    WAITING = "waiting"


class JobPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class JobType(str, enum.Enum):
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
    Représente un job de téléchargement ou d'analyse.

    Le champ `job_id` (String) est l'identifiant public utilisé partout
    dans l'API et dans `JobManager`. Le champ `id` (Integer) est un
    identifiant interne à la base de données.
    """

    __tablename__ = "jobs"

    # ----------------------------------------------------------------------
    #  Clés
    # ----------------------------------------------------------------------

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    # ----------------------------------------------------------------------
    #  Classification
    # ----------------------------------------------------------------------

    type = Column(
        SQLEnum(JobType, name="job_type"),
        default=JobType.DOWNLOAD,
        nullable=False,
    )
    status = Column(
        SQLEnum(JobStatus, name="job_status"),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )
    priority = Column(
        SQLEnum(JobPriority, name="job_priority"),
        default=JobPriority.NORMAL,
        nullable=False,
    )

    # ----------------------------------------------------------------------
    #  Cible
    # ----------------------------------------------------------------------

    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    provider_id = Column(String(50), nullable=True, index=True)

    # ----------------------------------------------------------------------
    #  Progression
    # ----------------------------------------------------------------------

    total_chapters = Column(Integer, default=0, nullable=False)
    done_chapters = Column(Integer, default=0, nullable=False)
    total_pages = Column(Integer, default=0, nullable=False)
    done_pages = Column(Integer, default=0, nullable=False)
    progress = Column(Float, default=0.0, nullable=False)

    current_chapter = Column(String(200), nullable=True)
    current_chapter_id = Column(String(100), nullable=True)

    # ----------------------------------------------------------------------
    #  Données libres (JSON)
    # ----------------------------------------------------------------------

    data = Column(JSON, nullable=True)
    logs = Column(JSON, default=list, nullable=False)
    errors = Column(JSON, default=list, nullable=False)

    # ----------------------------------------------------------------------
    #  Timestamps
    # ----------------------------------------------------------------------

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # ----------------------------------------------------------------------
    #  Utilisateur / résultat
    # ----------------------------------------------------------------------

    user_id = Column(Integer, nullable=True, index=True)
    result_path = Column(String(500), nullable=True)
    result_size = Column(Integer, nullable=True)

    # ----------------------------------------------------------------------
    #  Index composites
    # ----------------------------------------------------------------------

    __table_args__ = (
        Index("ix_jobs_status_created", "status", "created_at"),
        Index("ix_jobs_user_status", "user_id", "status"),
    )

    # ----------------------------------------------------------------------
    #  Méthodes
    # ----------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Job(job_id={self.job_id!r}, title={self.title!r}, "
            f"status={self.status})>"
        )

    def is_active(self) -> bool:
        """True si le job est en attente, en cours, en pause ou WAITING."""
        return self.status in (
            JobStatus.PENDING,
            JobStatus.RUNNING,
            JobStatus.WAITING,
            JobStatus.PAUSED,
        )

    def is_finished(self) -> bool:
        """True si le job est terminé (succès, échec, annulation)."""
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        )

    def start(self) -> None:
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(
        self,
        result_path: Optional[str] = None,
        result_size: Optional[int] = None,
    ) -> None:
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.progress = 100.0
        if result_path is not None:
            self.result_path = result_path
        if result_size is not None:
            self.result_size = result_size

    def fail(self, error_message: str) -> None:
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if self.errors is None:
            self.errors = []
        self.errors.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "message": error_message,
            }
        )

    def cancel(self) -> None:
        self.status = JobStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_progress(
        self,
        done_chapters: int,
        total_chapters: int,
        current_chapter: Optional[str] = None,
    ) -> None:
        self.done_chapters = done_chapters
        self.total_chapters = total_chapters
        if total_chapters > 0:
            self.progress = (done_chapters / total_chapters) * 100.0
        if current_chapter:
            self.current_chapter = current_chapter
        self.updated_at = datetime.utcnow()

    def add_log(self, message: str, level: str = "info") -> None:
        if self.logs is None:
            self.logs = []
        self.logs.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": message,
            }
        )
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.job_id,
            "job_id": self.job_id,
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
            "current_chapter_id": self.current_chapter_id,
            "data": self.data,
            "logs": self.logs or [],
            "errors": self.errors or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "user_id": self.user_id,
            "result_path": self.result_path,
            "result_size": self.result_size,
        }

    @classmethod
    def from_engine_dict(cls, payload: Dict[str, Any]) -> "Job":
        """
        Construit un Job à partir du dict produit par DownloadEngine.

        Usage :
            job = Job.from_engine_dict({"id": "job_1726...", ...})
        """
        now = datetime.utcnow()
        return cls(
            job_id=payload.get("id") or payload.get("job_id"),
            url=payload.get("url", ""),
            title=payload.get("title", "Sans titre"),
            provider_id=payload.get("provider_id"),
            type=JobType.DOWNLOAD,
            status=JobStatus.PENDING,
            total_chapters=payload.get("total_chapters", 0),
            done_chapters=payload.get("done_chapters", 0),
            progress=payload.get("progress", 0.0),
            current_chapter=payload.get("current_chapter", ""),
            logs=payload.get("logs") or [],
            errors=payload.get("errors") or [],
            created_at=now,
            updated_at=now,
        )


# ==========================================================================
#  Modèle en mémoire (sans SQLAlchemy) pour le JobManager
# ==========================================================================

class JobInMemory:
    """
    Version légère d'un Job, utilisée par le JobManager pour les jobs
    actifs. Aucune dépendance SQLAlchemy.
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
        user_id: Optional[int] = None,
    ) -> None:
        self.id = job_id
        self.job_id = job_id
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
        self.current_chapter_id: Optional[str] = None
        self.data = data or {}
        self.logs: list = []
        self.errors: list = []
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.cancelled_at: Optional[str] = None
        self.user_id = user_id
        self.result_path: Optional[str] = None
        self.result_size: Optional[int] = None
        self.provider_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "title": self.title,
            "url": self.url,
            "type": self.type.value if self.type else None,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "provider_id": self.provider_id,
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

    def update_from_engine(self, payload: Dict[str, Any]) -> None:
        """Met à jour le job depuis le dict produit par DownloadEngine."""
        for key, value in payload.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow().isoformat()
