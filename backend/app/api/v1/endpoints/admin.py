# ==========================================================================
#  NexusDL 2.0 - Admin Endpoints
#  Fichier : backend/app/api/v1/endpoints/admin.py
# ==========================================================================

import logging
import os
import shutil
import psutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import NexusDLError
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User, UserRole
from app.providers.registry import ProviderRegistry
from app.workers.job_manager import JobManager
from app.services.cache_service import CacheService
from app.services.file_service import FileService
from app.models.job import JobStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Administration"])

# ==========================================================================
#  Schémas
# ==========================================================================

class ProviderStatus(BaseModel):
    id: str
    name: str
    enabled: bool
    supported_languages: List[str]
    nsfw: bool
    version: Optional[str]
    last_check: Optional[datetime]

class ProviderToggleRequest(BaseModel):
    enabled: bool = Field(..., description="Activer ou désactiver le provider")

class SystemStats(BaseModel):
    cpu_percent: float
    memory_used: int
    memory_total: int
    disk_used: int
    disk_total: int
    uptime_seconds: float
    active_jobs: int
    total_jobs: int
    cache_size: int
    library_count: int

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str

class CacheClearResponse(BaseModel):
    success: bool
    cleared_count: int
    message: str

# ==========================================================================
#  Dépendances
# ==========================================================================

async def get_admin_user(current_user: User = Depends(get_current_user)):
    """Vérifie que l'utilisateur a le rôle admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs."
        )
    return current_user

# ==========================================================================
#  Endpoints
# ==========================================================================

@router.get(
    "/providers",
    response_model=List[ProviderStatus],
    summary="Liste tous les providers avec leur statut"
)
async def get_providers(
    include_disabled: bool = Query(False, description="Inclure les providers désactivés"),
    admin: User = Depends(get_admin_user)
):
    """
    Récupère la liste de tous les providers enregistrés, avec leur statut
    (activé/désactivé) et leurs métadonnées.
    """
    registry = ProviderRegistry()
    providers = registry.get_all_providers()
    
    result = []
    for provider_id, provider in providers.items():
        if not include_disabled and not provider.enabled:
            continue
        result.append(ProviderStatus(
            id=provider_id,
            name=provider.name,
            enabled=provider.enabled,
            supported_languages=provider.supported_languages,
            nsfw=provider.nsfw,
            version=getattr(provider, "version", "1.0.0"),
            last_check=datetime.now()  # À améliorer avec un vrai suivi
        ))
    return result

@router.patch(
    "/providers/{provider_id}",
    response_model=ProviderStatus,
    summary="Active ou désactive un provider"
)
async def toggle_provider(
    provider_id: str,
    payload: ProviderToggleRequest = Body(...),
    admin: User = Depends(get_admin_user)
):
    """
    Active ou désactive un provider spécifique. Les providers désactivés ne
    seront pas utilisés pour l'analyse ou le téléchargement.
    """
    registry = ProviderRegistry()
    try:
        provider = registry.get_provider(provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider_id}' non trouvé."
            )
        provider.enabled = payload.enabled
        # Persister l'état (par ex. dans un fichier de config ou DB)
        # Pour l'instant, on le stocke en mémoire
        registry.save_provider_state(provider_id, payload.enabled)
        return ProviderStatus(
            id=provider_id,
            name=provider.name,
            enabled=provider.enabled,
            supported_languages=provider.supported_languages,
            nsfw=provider.nsfw,
            version=getattr(provider, "version", "1.0.0"),
            last_check=datetime.now()
        )
    except NexusDLError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/stats",
    response_model=SystemStats,
    summary="Statistiques système"
)
async def get_system_stats(
    admin: User = Depends(get_admin_user)
):
    """Retourne des statistiques sur l'état du système (CPU, RAM, disque, jobs, etc.)."""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.5)
    # Mémoire
    mem = psutil.virtual_memory()
    # Disque
    disk = psutil.disk_usage(settings.get_download_path())
    # Uptime
    boot_time = psutil.boot_time()
    uptime = datetime.now().timestamp() - boot_time
    
    # Jobs
    job_manager = JobManager()
    active_jobs = len(job_manager.get_active_jobs())
    total_jobs = len(job_manager.get_all_jobs())
    
    # Cache
    cache_service = CacheService()
    cache_size = cache_service.size()
    
    # Bibliothèque
    from app.services.file_service import FileService
    library_items = FileService.get_library_items()
    library_count = len(library_items)
    
    return SystemStats(
        cpu_percent=cpu_percent,
        memory_used=mem.used,
        memory_total=mem.total,
        disk_used=disk.used,
        disk_total=disk.total,
        uptime_seconds=uptime,
        active_jobs=active_jobs,
        total_jobs=total_jobs,
        cache_size=cache_size,
        library_count=library_count
    )

@router.get(
    "/logs",
    response_model=List[LogEntry],
    summary="Récupère les logs système"
)
async def get_system_logs(
    lines: int = Query(100, ge=1, le=10000, description="Nombre de lignes à récupérer"),
    level: Optional[str] = Query(None, description="Filtrer par niveau (INFO, WARNING, ERROR, DEBUG)"),
    admin: User = Depends(get_admin_user)
):
    """
    Récupère les dernières lignes du fichier de logs.
    """
    log_file = "logs/nexusdl.log"
    if not os.path.exists(log_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier de logs non trouvé."
        )
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        
        # Filtrer par niveau si spécifié
        if level:
            level_upper = level.upper()
            all_lines = [line for line in all_lines if f"[{level_upper}]" in line]
        
        # Prendre les dernières lignes
        last_lines = all_lines[-lines:] if lines else all_lines
        
        entries = []
        for line in last_lines:
            # Tentative de parsing basique
            try:
                # Format: [timestamp] [LEVEL] [module] message
                parts = line.split("] [", 2)
                if len(parts) >= 3:
                    timestamp_str = parts[0].replace("[", "")
                    level_str = parts[1]
                    message = parts[2].strip()
                    # Convertir timestamp
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    except:
                        timestamp = datetime.now()
                    entries.append(LogEntry(
                        timestamp=timestamp,
                        level=level_str,
                        message=message
                    ))
                else:
                    # Fallback
                    entries.append(LogEntry(
                        timestamp=datetime.now(),
                        level="INFO",
                        message=line.strip()
                    ))
            except Exception:
                entries.append(LogEntry(
                    timestamp=datetime.now(),
                    level="INFO",
                    message=line.strip()
                ))
        
        return entries
    except Exception as e:
        logger.error(f"Erreur lecture logs: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la lecture des logs")

@router.delete(
    "/cache",
    response_model=CacheClearResponse,
    summary="Vide le cache"
)
async def clear_cache(
    admin: User = Depends(get_admin_user)
):
    """
    Supprime tous les éléments du cache (pages HTML, images, etc.).
    """
    cache_service = CacheService()
    try:
        cleared = cache_service.clear()
        return CacheClearResponse(
            success=True,
            cleared_count=cleared,
            message=f"{cleared} éléments supprimés du cache."
        )
    except Exception as e:
        logger.error(f"Erreur vidage cache: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du vidage du cache")

@router.delete(
    "/downloads",
    summary="Supprime tous les fichiers de téléchargement (hors bibliothèque)"
)
async def clear_downloads(
    confirm: bool = Query(..., description="Doit être true pour confirmer"),
    admin: User = Depends(get_admin_user)
):
    """
    Supprime tous les fichiers temporaires et les téléchargements incomplets.
    N'affecte pas la bibliothèque.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le paramètre 'confirm' doit être 'true' pour effectuer cette opération."
        )
    try:
        download_path = settings.get_download_path()
        temp_path = settings.get_temp_path()
        deleted_count = 0
        
        # Supprimer les fichiers temporaires
        if temp_path.exists():
            for item in temp_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                deleted_count += 1
        
        # Supprimer les téléchargements incomplets (pas dans library)
        # Pour simplifier, on ne supprime que ce qui n'est pas dans la bibliothèque
        # On pourrait implémenter une vérification plus fine.
        
        return JSONResponse({
            "success": True,
            "message": f"{deleted_count} éléments supprimés."
        })
    except Exception as e:
        logger.error(f"Erreur suppression downloads: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression")

@router.post(
    "/restart",
    summary="Redémarre le serveur (mode développement uniquement)"
)
async def restart_server(
    admin: User = Depends(get_admin_user)
):
    """
    Redémarre le serveur. Uniquement disponible en mode développement.
    En production, utilisez `docker-compose restart` à la place.
    """
    if settings.ENV == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Redémarrage non autorisé en production."
        )
    # Redémarrer via uvicorn (simple) - en pratique, on lance un nouveau processus
    # Ici, on lève une exception pour forcer le serveur à s'arrêter,
    # et on compte sur le gestionnaire de processus pour redémarrer (ex: uvicorn --reload)
    import sys
    logger.warning("⚠️ Redémarrage du serveur demandé.")
    sys.exit(0)

@router.get(
    "/downloads/{filename}",
    response_class=FileResponse,
    summary="Télécharge un fichier depuis le serveur (admin uniquement)"
)
async def download_file(
    filename: str,
    admin: User = Depends(get_admin_user)
):
    """
    Permet à l'administrateur de télécharger un fichier depuis le serveur
    (utile pour récupérer les logs ou les CBZ).
    """
    # Sécurisation : vérifier que le fichier est dans un dossier autorisé
    safe_path = os.path.abspath(os.path.join(settings.get_download_path(), filename))
    if not safe_path.startswith(os.path.abspath(settings.get_download_path())):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès interdit en dehors du dossier de téléchargement."
        )
    if not os.path.exists(safe_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier non trouvé."
        )
    return FileResponse(safe_path, filename=filename)

# ==========================================================================
#  Notes
# ==========================================================================
#  - Les endpoints sont protégés par le rôle ADMIN.
#  - La gestion des providers en mémoire est simplifiée; une persistance
#    (base de données) serait préférable pour un usage réel.
#  - Les logs sont lus directement depuis le fichier, ce qui peut être lourd
#    en production; on pourrait utiliser une base de données de logs.
