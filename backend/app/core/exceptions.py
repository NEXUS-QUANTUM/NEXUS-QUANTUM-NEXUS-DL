# ==========================================================================
#  NexusDL 2.0 - Exceptions personnalisées
#  Fichier : backend/app/core/exceptions.py
# ==========================================================================

"""
Ce module définit toutes les exceptions personnalisées utilisées dans NexusDL.
Elles permettent une gestion d'erreur granulaire et cohérente dans toute l'application.
"""


class NexusDLError(Exception):
    """
    Exception de base pour toutes les erreurs spécifiques à NexusDL.
    Toutes les autres exceptions héritent de celle-ci.
    """
    def __init__(self, message: str = "Une erreur est survenue dans NexusDL", *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)


class ProviderError(NexusDLError):
    """
    Erreur liée à un provider (site de scan).
    Peut être levée lors de l'analyse, de la récupération des chapitres ou des images.
    """
    def __init__(self, message: str = "Erreur du provider", provider_id: str = None, *args, **kwargs):
        self.provider_id = provider_id
        if provider_id:
            message = f"[{provider_id}] {message}"
        super().__init__(message, *args, **kwargs)


class ProviderNotFoundError(ProviderError):
    """Erreur lorsqu'un provider n'est pas trouvé dans le registre."""
    def __init__(self, provider_id: str = None, message: str = "Provider non trouvé", *args, **kwargs):
        super().__init__(message, provider_id, *args, **kwargs)


class ProviderConfigurationError(ProviderError):
    """Erreur de configuration d'un provider (ex: paramètres manquants)."""
    def __init__(self, provider_id: str = None, message: str = "Configuration du provider invalide", *args, **kwargs):
        super().__init__(message, provider_id, *args, **kwargs)


class DownloadError(NexusDLError):
    """Erreur lors du téléchargement des images ou des fichiers."""
    def __init__(self, message: str = "Erreur de téléchargement", url: str = None, *args, **kwargs):
        self.url = url
        if url:
            message = f"{message} (URL: {url})"
        super().__init__(message, *args, **kwargs)


class DownloadTimeoutError(DownloadError):
    """Erreur de timeout lors d'un téléchargement."""
    def __init__(self, message: str = "Timeout de téléchargement", url: str = None, *args, **kwargs):
        super().__init__(message, url, *args, **kwargs)


class CbzBuildError(NexusDLError):
    """Erreur lors de la construction du fichier CBZ."""
    def __init__(self, message: str = "Erreur lors de la construction du CBZ", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class CbzExtractionError(NexusDLError):
    """Erreur lors de l'extraction ou lecture d'un fichier CBZ."""
    def __init__(self, message: str = "Erreur lors de l'extraction du CBZ", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class AuthenticationError(NexusDLError):
    """Erreur d'authentification (JWT, mot de passe, etc.)."""
    def __init__(self, message: str = "Erreur d'authentification", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class AuthorizationError(NexusDLError):
    """Erreur d'autorisation (permissions insuffisantes)."""
    def __init__(self, message: str = "Permissions insuffisantes", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class RateLimitError(NexusDLError):
    """Erreur de limitation de débit (rate limiting)."""
    def __init__(self, message: str = "Limite de taux atteinte", retry_after: int = None, *args, **kwargs):
        self.retry_after = retry_after
        if retry_after:
            message = f"{message} (réessayer dans {retry_after} secondes)"
        super().__init__(message, *args, **kwargs)


class JobNotFoundError(NexusDLError):
    """Erreur lorsqu'un job de téléchargement n'est pas trouvé."""
    def __init__(self, job_id: str = None, message: str = "Job non trouvé", *args, **kwargs):
        self.job_id = job_id
        if job_id:
            message = f"{message} (ID: {job_id})"
        super().__init__(message, *args, **kwargs)


class JobCancelError(NexusDLError):
    """Erreur lors de l'annulation d'un job."""
    def __init__(self, job_id: str = None, message: str = "Impossible d'annuler le job", *args, **kwargs):
        self.job_id = job_id
        if job_id:
            message = f"{message} (ID: {job_id})"
        super().__init__(message, *args, **kwargs)


class FileOperationError(NexusDLError):
    """Erreur lors d'une opération sur un fichier (lecture, écriture, suppression)."""
    def __init__(self, message: str = "Erreur d'opération sur le fichier", path: str = None, *args, **kwargs):
        self.path = path
        if path:
            message = f"{message} (Chemin: {path})"
        super().__init__(message, *args, **kwargs)


class FileNotFoundError(FileOperationError):
    """Erreur lorsqu'un fichier n'est pas trouvé."""
    def __init__(self, path: str = None, message: str = "Fichier non trouvé", *args, **kwargs):
        super().__init__(message, path, *args, **kwargs)


class CacheError(NexusDLError):
    """Erreur lors d'une opération sur le cache."""
    def __init__(self, message: str = "Erreur de cache", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class DatabaseError(NexusDLError):
    """Erreur lors d'une opération sur la base de données."""
    def __init__(self, message: str = "Erreur de base de données", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class ValidationError(NexusDLError):
    """Erreur de validation des données (schémas, paramètres)."""
    def __init__(self, message: str = "Erreur de validation", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class WebSocketError(NexusDLError):
    """Erreur liée aux WebSockets."""
    def __init__(self, message: str = "Erreur WebSocket", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


# ==========================================================================
#  Mappage des erreurs pour la conversion en HTTP status codes
# ==========================================================================

HTTP_ERROR_MAP = {
    AuthenticationError: 401,
    AuthorizationError: 403,
    ProviderNotFoundError: 404,
    JobNotFoundError: 404,
    FileNotFoundError: 404,
    RateLimitError: 429,
    ValidationError: 400,
    DownloadTimeoutError: 408,
}

def get_http_status_for_exception(exc: Exception) -> int:
    """
    Retourne le code HTTP approprié pour une exception donnée.
    Si l'exception n'est pas dans la map, retourne 500.
    """
    for exc_type, status in HTTP_ERROR_MAP.items():
        if isinstance(exc, exc_type):
            return status
    return 500


# ==========================================================================
#  Notes
# ==========================================================================
#  - Cette hiérarchie d'exceptions permet une gestion fine des erreurs
#    dans toute l'application.
#  - La fonction `get_http_status_for_exception` est utilisée dans les
#    gestionnaires d'exceptions globales pour transformer les exceptions
#    en réponses HTTP appropriées.
#  - Toutes les exceptions héritent de NexusDLError, ce qui permet de
#    capturer toutes les erreurs applicatives avec un seul `except`.
