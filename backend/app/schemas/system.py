# ==========================================================================
#  NexusDL 2.0 - Schémas Système
#  Fichier : backend/app/schemas/system.py
# ==========================================================================

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==========================================================================
#  Schémas d'information système
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


class ResourceLimit(BaseModel):
    """Limites de ressources."""
    cpu_limit: Optional[float] = None
    memory_limit: Optional[int] = None
    disk_limit: Optional[int] = None


# ==========================================================================
#  Schémas pour l'environnement
# ==========================================================================

class EnvironmentVariable(BaseModel):
    """Variable d'environnement."""
    key: str
    value: str


class EnvironmentInfo(BaseModel):
    """Informations sur l'environnement d'exécution."""
    variables: List[EnvironmentVariable]
    python_path: List[str]
    sys_path: List[str]


# ==========================================================================
#  Schémas pour les logs
# ==========================================================================

class LogLevelUpdate(BaseModel):
    """Mise à jour du niveau de log."""
    level: str = Field(..., description="Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)")


class LogLevelResponse(BaseModel):
    """Réponse après mise à jour du niveau de log."""
    old_level: str
    new_level: str
    success: bool
    message: str


class LogEntry(BaseModel):
    """Entrée de log."""
    timestamp: str
    level: str
    message: str


class LogListResponse(BaseModel):
    """Réponse avec une liste de logs."""
    total_lines: int
    lines: List[str]
    filter: Optional[str] = None
    file: str


# ==========================================================================
#  Schémas de healthcheck
# ==========================================================================

class SystemHealthCheck(BaseModel):
    """Résultat du healthcheck détaillé."""
    status: str  # "healthy" ou "unhealthy"
    timestamp: str
    checks: Dict[str, Any]


# ==========================================================================
#  Schémas pour les opérations système
# ==========================================================================

class SystemOperationResponse(BaseModel):
    """Réponse générique pour une opération système."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class CacheClearResponse(BaseModel):
    """Réponse après vidage du cache."""
    success: bool
    cleared_count: int
    message: str


# ==========================================================================
#  Notes
# ==========================================================================
#  - Ces schémas sont utilisés par les endpoints du module system.
#  - Ils définissent la structure des réponses pour les informations système,
#    métriques, logs, healthcheck, etc.
#  - La plupart sont utilisés par les endpoints publics et protégés.
