# ==========================================================================
#  NexusDL 2.0 - System Endpoints
#  Fichier : backend/app/api/v1/endpoints/system.py
# ==========================================================================

import os
import sys
import platform
import logging
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
import psutil

from app.core.config import settings
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.deps import get_system_info
from app.models.user import User, UserRole
from app.core.exceptions import NexusDLError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["System"])

# ==========================================================================
#  Schémas
# ==========================================================================

class SystemInfo(BaseModel):
    """Informations générales sur le système."""
    app_name: str
    app_version: str
    build_date: str
    python_version: str
    platform: str
    os_name: str
    os_version: str
    architecture: str
    hostname: str
    environment: str
    debug_mode: bool
    uptime_seconds: float
    server_time: str

class SystemMetrics(BaseModel):
    """Métriques système en temps réel."""
    # CPU
    cpu_percent: float
    cpu_cores: int
    cpu_freq_current: float
    cpu_freq_min: float
    cpu_freq_max: float
    
    # Mémoire
    memory_total: int
    memory_available: int
    memory_used: int
    memory_percent: float
    
    # Disque
    disk_total: int
    disk_used: int
    disk_free: int
    disk_percent: float
    
    # Processus
    process_memory: int
    process_cpu_percent: float
    process_threads: int
    process_open_files: int
    
    # Réseau
    connections_count: int

class DatabaseStatus(BaseModel):
    """Statut de la base de données."""
    connected: bool
    engine: str
    url: str
    size_bytes: Optional[int] = None
    size_formatted: Optional[str] = None

class EnvironmentVariable(BaseModel):
    """Variable d'environnement."""
    key: str
    value: str

class EnvironmentInfo(BaseModel):
    """Informations sur l'environnement d'exécution."""
    variables: List[EnvironmentVariable]
    python_path: List[str]
    sys_path: List[str]

class LogLevelUpdate(BaseModel):
    """Mise à jour du niveau de log."""
    level: str = Field(..., description="Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)")

class LogLevelResponse(BaseModel):
    """Réponse après mise à jour du niveau de log."""
    old_level: str
    new_level: str
    success: bool
    message: str

class SystemHealthCheck(BaseModel):
    """Résultat du healthcheck détaillé."""
    status: str
    timestamp: str
    checks: Dict[str, Any]

class ResourceLimit(BaseModel):
    """Limites de ressources."""
    cpu_limit: Optional[float]
    memory_limit: Optional[int]
    disk_limit: Optional[int]

# ==========================================================================
#  Fonctions utilitaires
# ==========================================================================

def format_size(size_bytes: int) -> str:
    """Formate une taille en octets en chaîne lisible."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def get_uptime() -> float:
    """Retourne l'uptime du système en secondes."""
    try:
        boot_time = psutil.boot_time()
        return time.time() - boot_time
    except Exception:
        return 0.0

def get_database_size() -> Optional[int]:
    """Retourne la taille du fichier de base de données en octets."""
    try:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            return None
        return os.path.getsize(db_path)
    except Exception:
        return None

# ==========================================================================
#  Endpoints publics (sans authentification)
# ==========================================================================

@router.get(
    "/info",
    response_model=SystemInfo,
    summary="Informations système (public)"
)
async def get_system_info_public():
    """
    Retourne des informations générales sur le système et l'application.
    Accessible sans authentification pour les healthchecks et les agents de monitoring.
    """
    start_time = time.time()
    try:
        return SystemInfo(
            app_name=settings.APP_NAME,
            app_version=settings.APP_VERSION,
            build_date=settings.BUILD_DATE,
            python_version=sys.version,
            platform=platform.platform(),
            os_name=platform.system(),
            os_version=platform.version(),
            architecture=platform.machine(),
            hostname=platform.node(),
            environment=settings.ENV,
            debug_mode=settings.DEBUG,
            uptime_seconds=get_uptime(),
            server_time=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos système: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des informations système."
        )

@router.get(
    "/health",
    response_model=SystemHealthCheck,
    summary="Healthcheck détaillé (public)"
)
async def health_check():
    """
    Effectue un healthcheck complet du système.
    Vérifie la base de données, le disque, la mémoire, etc.
    Accessible sans authentification pour les orchestrateurs.
    """
    checks = {}
    
    # Vérification de la base de données
    try:
        db_size = get_database_size()
        db_connected = True
        checks["database"] = {
            "status": "ok",
            "connected": True,
            "size_bytes": db_size,
            "size_formatted": format_size(db_size) if db_size else "N/A"
        }
    except Exception as e:
        checks["database"] = {
            "status": "error",
            "connected": False,
            "error": str(e)
        }
        db_connected = False
    
    # Vérification du disque
    try:
        download_path = settings.get_download_path()
        disk_usage = psutil.disk_usage(download_path)
        checks["disk"] = {
            "status": "ok",
            "total_bytes": disk_usage.total,
            "used_bytes": disk_usage.used,
            "free_bytes": disk_usage.free,
            "percent": disk_usage.percent,
            "path": str(download_path)
        }
    except Exception as e:
        checks["disk"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Vérification de la mémoire
    try:
        memory = psutil.virtual_memory()
        checks["memory"] = {
            "status": "ok",
            "total_bytes": memory.total,
            "available_bytes": memory.available,
            "used_bytes": memory.used,
            "percent": memory.percent
        }
    except Exception as e:
        checks["memory"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Vérification du provider registry
    try:
        from app.providers.registry import ProviderRegistry
        registry = ProviderRegistry()
        provider_count = len(registry.get_all_providers())
        checks["providers"] = {
            "status": "ok",
            "count": provider_count,
            "enabled_count": len([p for p in registry.get_all_providers().values() if getattr(p, 'enabled', True)])
        }
    except Exception as e:
        checks["providers"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Status global
    global_status = "healthy"
    for check_name, check_data in checks.items():
        if check_data.get("status") == "error":
            global_status = "unhealthy"
            break
    if not db_connected:
        global_status = "unhealthy"
    
    return SystemHealthCheck(
        status=global_status,
        timestamp=datetime.now().isoformat(),
        checks=checks
    )

@router.get(
    "/metrics",
    response_model=SystemMetrics,
    summary="Métriques système (public)"
)
async def get_system_metrics():
    """
    Retourne des métriques système en temps réel (CPU, mémoire, disque, etc.).
    Accessible sans authentification pour le monitoring.
    """
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_freq = psutil.cpu_freq()
        cpu_cores = psutil.cpu_count()
        
        # Mémoire
        memory = psutil.virtual_memory()
        
        # Disque
        disk = psutil.disk_usage(settings.get_download_path())
        
        # Processus
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss
        process_cpu = process.cpu_percent(interval=0.5)
        process_threads = process.num_threads()
        process_open_files = len(process.open_files())
        
        # Réseau
        connections = psutil.net_connections()
        connections_count = len(connections)
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            cpu_cores=cpu_cores,
            cpu_freq_current=cpu_freq.current if cpu_freq else 0.0,
            cpu_freq_min=cpu_freq.min if cpu_freq else 0.0,
            cpu_freq_max=cpu_freq.max if cpu_freq else 0.0,
            memory_total=memory.total,
            memory_available=memory.available,
            memory_used=memory.used,
            memory_percent=memory.percent,
            disk_total=disk.total,
            disk_used=disk.used,
            disk_free=disk.free,
            disk_percent=disk.percent,
            process_memory=process_memory,
            process_cpu_percent=process_cpu,
            process_threads=process_threads,
            process_open_files=process_open_files,
            connections_count=connections_count
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des métriques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des métriques."
        )

# ==========================================================================
#  Endpoints protégés (authentification requise)
# ==========================================================================

@router.get(
    "/environment",
    response_model=EnvironmentInfo,
    summary="Variables d'environnement (admin uniquement)"
)
async def get_environment_info(
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les variables d'environnement et les chemins système.
    Nécessite d'être authentifié.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs."
        )
    
    # Ne pas exposer les variables sensibles
    sensitive_keys = {'SECRET_KEY', 'DATABASE_URL', 'PASSWORD', 'TOKEN', 'KEY'}
    variables = []
    for key, value in os.environ.items():
        if any(sensitive in key.upper() for sensitive in sensitive_keys):
            value = '***REDACTED***'
        # Filtrer les variables trop longues
        if len(value) > 200:
            value = value[:200] + '...'
        variables.append(EnvironmentVariable(key=key, value=value))
    
    return EnvironmentInfo(
        variables=variables,
        python_path=sys.path,
        sys_path=sys.path
    )

@router.post(
    "/logs/level",
    response_model=LogLevelResponse,
    summary="Change le niveau de log (admin uniquement)"
)
async def set_log_level(
    log_data: LogLevelUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Modifie le niveau de log du serveur en temps réel.
    Nécessite d'être administrateur.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs."
        )
    
    level = log_data.level.upper()
    if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niveau invalide. Valeurs autorisées: DEBUG, INFO, WARNING, ERROR, CRITICAL"
        )
    
    try:
        # Changer le niveau de log
        old_level = logging.getLevelName(logging.getLogger().getEffectiveLevel())
        logging.getLogger().setLevel(getattr(logging, level))
        
        # Aussi pour le logger de l'application
        logger.setLevel(getattr(logging, level))
        
        return LogLevelResponse(
            old_level=old_level,
            new_level=level,
            success=True,
            message=f"Niveau de log changé de {old_level} à {level}."
        )
    except Exception as e:
        logger.error(f"Erreur lors du changement de niveau de log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du changement de niveau de log."
        )

@router.get(
    "/logs",
    summary="Récupère les logs système"
)
async def get_logs(
    lines: int = Query(100, ge=1, le=10000, description="Nombre de lignes à récupérer"),
    level_filter: Optional[str] = Query(None, description="Filtrer par niveau (INFO, WARNING, ERROR, DEBUG)"),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les dernières lignes du fichier de logs.
    Nécessite d'être authentifié.
    """
    log_file = "logs/nexusdl.log"
    if not os.path.exists(log_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier de logs non trouvé."
        )
    
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
        
        # Filtrer par niveau si spécifié
        if level_filter:
            level_upper = level_filter.upper()
            all_lines = [line for line in all_lines if f"[{level_upper}]" in line]
        
        # Prendre les dernières lignes
        last_lines = all_lines[-lines:] if lines else all_lines
        
        return {
            "total_lines": len(last_lines),
            "lines": last_lines,
            "filter": level_filter,
            "file": log_file
        }
    except Exception as e:
        logger.error(f"Erreur lecture logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la lecture des logs."
        )

@router.get(
    "/resources",
    response_model=ResourceLimit,
    summary="Limites de ressources (admin uniquement)"
)
async def get_resource_limits(
    current_user: User = Depends(get_current_user)
):
    """
    Retourne les limites de ressources du conteneur/du système.
    Nécessite d'être administrateur.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs."
        )
    
    try:
        # Essayer de détecter les limites Docker/container
        memory_limit = None
        cpu_limit = None
        disk_limit = None
        
        # Lire les limites du cgroup (si en container)
        try:
            with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
                memory_limit = int(f.read().strip())
                if memory_limit > 2**63:  # Signifie pas de limite
                    memory_limit = None
        except:
            pass
        
        # Limite CPU via cgroup
        try:
            with open('/sys/fs/cgroup/cpu,cpuacct/cpu.cfs_quota_us', 'r') as f:
                cpu_quota = int(f.read().strip())
            with open('/sys/fs/cgroup/cpu,cpuacct/cpu.cfs_period_us', 'r') as f:
                cpu_period = int(f.read().strip())
            if cpu_quota > 0 and cpu_period > 0:
                cpu_limit = cpu_quota / cpu_period
        except:
            pass
        
        # Pas de limite de disque facile à détecter
        # Utiliser la taille du disque comme limite de fait
        disk = psutil.disk_usage(settings.get_download_path())
        disk_limit = disk.total
        
        return ResourceLimit(
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
            disk_limit=disk_limit
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des limites de ressources: {e}")
        return ResourceLimit(cpu_limit=None, memory_limit=None, disk_limit=None)

@router.get(
    "/database",
    response_model=DatabaseStatus,
    summary="Statut de la base de données"
)
async def get_database_status(
    current_user: User = Depends(get_current_user)
):
    """
    Retourne le statut de la base de données.
    Nécessite d'être authentifié.
    """
    try:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        exists = os.path.exists(db_path)
        size_bytes = os.path.getsize(db_path) if exists else None
        
        # Tester la connexion
        connected = False
        try:
            from sqlalchemy import create_engine
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                conn.execute("SELECT 1")
                connected = True
        except Exception as e:
            logger.warning(f"Erreur de connexion DB: {e}")
            connected = False
        
        return DatabaseStatus(
            connected=connected,
            engine="SQLite",
            url=settings.DATABASE_URL,
            size_bytes=size_bytes,
            size_formatted=format_size(size_bytes) if size_bytes else None
        )
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la vérification de la base de données."
        )

# ==========================================================================
#  Notes
# ==========================================================================
#  - Les endpoints publics sont accessibles sans authentification pour
#    permettre le monitoring et les healthchecks.
#  - Les endpoints sensibles (environment, logs, etc.) nécessitent
#    le rôle ADMIN.
#  - Les métriques système utilisent psutil pour une récupération en
#    temps réel des données.
