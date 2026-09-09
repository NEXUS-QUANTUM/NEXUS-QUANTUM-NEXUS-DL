# ==========================================================================
#  NexusDL 2.0 - Downloads Endpoints
#  Fichier : backend/app/api/v1/endpoints/downloads.py
# ==========================================================================

import logging
import os
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.engine import DownloadEngine
from app.core.exceptions import ProviderError, DownloadError
from app.providers.registry import ProviderRegistry
from app.workers.job_manager import JobManager, JobStatus
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.deps import get_provider_registry, get_job_manager
from app.models.user import User
from app.schemas.job import JobResponse, JobCreateRequest, JobListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/downloads", tags=["Downloads"])

# ==========================================================================
#  Schémas
# ==========================================================================

class DownloadRequest(BaseModel):
    """Requête pour lancer un téléchargement."""
    url: str = Field(..., description="URL de la série ou du chapitre")
    chapter_ids: List[str] = Field(..., description="Liste des IDs de chapitres à télécharger")
    options: Optional[dict] = Field(None, description="Options supplémentaires (qualité, format, etc.)")

class DownloadResponse(BaseModel):
    """Réponse après lancement d'un téléchargement."""
    job_id: str
    status: str
    title: str
    total_chapters: int
    message: str

class JobStatusResponse(BaseModel):
    """Statut détaillé d'un job."""
    id: str
    status: str
    title: str
    url: str
    total_chapters: int
    done_chapters: int
    progress: float
    current_chapter: str
    logs: List[str]
    created_at: str
    updated_at: str

class CancelResponse(BaseModel):
    """Réponse d'annulation."""
    job_id: str
    cancelled: bool
    message: str

class FileInfo(BaseModel):
    """Informations sur un fichier CBZ téléchargé."""
    id: str
    filename: str
    title: str
    size: int
    created_at: str
    path: str

# ==========================================================================
#  Endpoints
# ==========================================================================

@router.post(
    "/",
    response_model=DownloadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Lance un téléchargement"
)
async def start_download(
    request: DownloadRequest = Body(...),
    engine: DownloadEngine = Depends(),
    current_user: Optional[User] = Depends(get_current_user)
) -> DownloadResponse:
    """
    Analyse une URL, extrait les chapitres et lance le téléchargement de ceux sélectionnés.
    Retourne un ID de job pour suivre l'avancement.
    """
    try:
        # Analyser l'URL pour obtenir les informations
        analysis = await engine.analyze_url(request.url)
        title = analysis.get("title", "Sans titre")
        all_chapters = analysis.get("chapters", [])
        
        # Vérifier que les chapitres demandés existent
        requested_chapters = [c for c in all_chapters if c.get("id") in request.chapter_ids]
        if not requested_chapters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun des chapitres spécifiés n'a été trouvé."
            )
        
        # Démarrer le téléchargement via le moteur
        job_id = await engine.start_download(request.url, request.chapter_ids)
        
        # Récupérer le job pour la réponse
        job_manager = JobManager()
        job = job_manager.get_job(job_id)
        
        return DownloadResponse(
            job_id=job_id,
            status=job.status.value if job else "pending",
            title=title,
            total_chapters=len(request.chapter_ids),
            message="Téléchargement ajouté à la file d'attente."
        )
    except ProviderError as e:
        logger.error(f"Erreur provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erreur lors du lancement du téléchargement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors du démarrage du téléchargement."
        )

@router.get(
    "/jobs",
    response_model=List[JobResponse],
    summary="Liste tous les jobs de téléchargement"
)
async def list_jobs(
    status_filter: Optional[str] = Query(None, description="Filtrer par statut (pending, running, completed, failed, cancelled)"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de jobs à retourner"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    job_manager: JobManager = Depends(get_job_manager),
    current_user: Optional[User] = Depends(get_current_user)
) -> List[JobResponse]:
    """
    Récupère la liste des jobs de téléchargement, avec filtrage et pagination.
    """
    all_jobs = job_manager.get_all_jobs()
    
    # Filtrage
    if status_filter:
        try:
            status_enum = JobStatus(status_filter.lower())
            all_jobs = [j for j in all_jobs if j.status == status_enum]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Statut invalide. Valeurs autorisées: {[s.value for s in JobStatus]}"
            )
    
    # Pagination
    total = len(all_jobs)
    paginated = all_jobs[offset:offset + limit]
    
    return [
        JobResponse(
            id=job.id,
            status=job.status.value,
            title=job.title,
            url=job.url,
            total_chapters=job.total_chapters,
            done_chapters=job.done_chapters,
            progress=job.progress,
            current_chapter=job.current_chapter,
            created_at=job.created_at,
            updated_at=job.updated_at,
            logs=job.logs[-20:] if job.logs else []  # Derniers 20 logs
        )
        for job in paginated
    ]

@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Obtenir les détails d'un job spécifique"
)
async def get_job_status(
    job_id: str = Path(..., description="ID du job"),
    job_manager: JobManager = Depends(get_job_manager),
    current_user: Optional[User] = Depends(get_current_user)
) -> JobStatusResponse:
    """
    Récupère le statut détaillé d'un job de téléchargement.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' non trouvé."
        )
    return JobStatusResponse(
        id=job.id,
        status=job.status.value,
        title=job.title,
        url=job.url,
        total_chapters=job.total_chapters,
        done_chapters=job.done_chapters,
        progress=job.progress,
        current_chapter=job.current_chapter,
        logs=job.logs,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

@router.delete(
    "/jobs/{job_id}",
    response_model=CancelResponse,
    summary="Annule un job en cours"
)
async def cancel_job(
    job_id: str = Path(..., description="ID du job à annuler"),
    job_manager: JobManager = Depends(get_job_manager),
    current_user: Optional[User] = Depends(get_current_user)
) -> CancelResponse:
    """
    Annule un job en cours d'exécution. Si le job est déjà terminé, retourne une erreur.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' non trouvé."
        )
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le job est déjà dans un état terminal ({job.status.value})."
        )
    try:
        cancelled = await job_manager.cancel_job(job_id)
        return CancelResponse(
            job_id=job_id,
            cancelled=cancelled,
            message="Job annulé avec succès." if cancelled else "Échec de l'annulation."
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation du job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de l'annulation."
        )

@router.get(
    "/files",
    response_model=List[FileInfo],
    summary="Liste les fichiers CBZ disponibles"
)
async def list_downloaded_files(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user)
) -> List[FileInfo]:
    """
    Récupère la liste des fichiers CBZ générés par les téléchargements terminés.
    """
    download_path = settings.get_download_path()
    files = []
    try:
        for entry in os.listdir(download_path):
            if entry.endswith(".cbz"):
                file_path = download_path / entry
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append(FileInfo(
                        id=entry,
                        filename=entry,
                        title=entry.replace(".cbz", ""),
                        size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        path=str(file_path)
                    ))
        # Trier par date de création décroissante
        files.sort(key=lambda f: f.created_at, reverse=True)
        # Pagination
        total = len(files)
        paginated = files[offset:offset + limit]
        return paginated
    except Exception as e:
        logger.error(f"Erreur liste fichiers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la lecture des fichiers."
        )

@router.get(
    "/files/{file_id}",
    response_class=FileResponse,
    summary="Télécharge un fichier CBZ"
)
async def download_file(
    file_id: str = Path(..., description="Nom du fichier CBZ"),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Permet de télécharger un fichier CBZ généré par un téléchargement terminé.
    """
    # Sécurisation du nom de fichier
    if ".." in file_id or "/" in file_id or "\\" in file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nom de fichier invalide."
        )
    file_path = settings.get_download_path() / file_id
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier non trouvé."
        )
    if not file_id.endswith(".cbz"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit être au format CBZ."
        )
    return FileResponse(
        path=file_path,
        filename=file_id,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={file_id}"}
    )

@router.delete(
    "/files/{file_id}",
    summary="Supprime un fichier CBZ"
)
async def delete_file(
    file_id: str = Path(..., description="Nom du fichier CBZ à supprimer"),
    current_user: User = Depends(get_current_user)  # Authentification requise
):
    """
    Supprime un fichier CBZ de la bibliothèque.
    (Nécessite d'être connecté)
    """
    if ".." in file_id or "/" in file_id or "\\" in file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nom de fichier invalide."
        )
    file_path = settings.get_download_path() / file_id
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier non trouvé."
        )
    try:
        os.remove(file_path)
        return {"message": f"Fichier '{file_id}' supprimé avec succès."}
    except Exception as e:
        logger.error(f"Erreur suppression fichier {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression."
        )

# ==========================================================================
#  Notes
# ==========================================================================
#  - Les endpoints sont protégés par authentification optionnelle (pour certains,
#    on exige l'authentification pour la suppression).
#  - Le JobManager et DownloadEngine sont injectés via les dépendances.
#  - Les jobs sont stockés en mémoire (non persistants). En production,
#    on pourrait utiliser une base de données.
