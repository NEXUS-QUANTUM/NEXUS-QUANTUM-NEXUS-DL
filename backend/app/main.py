# ==========================================================================
#  NexusDL 2.0 - Main Application
#  Fichier : backend/app/main.py
# ==========================================================================

import logging
import sys
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn

from app.core.config import settings
from app.core.exceptions import (
    NexusDLError,
    get_http_status_for_exception,
    AuthenticationError,
    RateLimitError,
)
from app.api.v1.router import router as api_v1_router
from app.models import Base
from app.api.deps import engine, init_services
from app.core.engine import DownloadEngine
from app.providers.registry import ProviderRegistry

# ==========================================================================
#  Configuration des logs
# ==========================================================================

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Niveau de log
log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)

# Format des logs
log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# Configuration des handlers
handlers = [
    logging.StreamHandler(sys.stdout),
    RotatingFileHandler(
        log_dir / "nexusdl.log",
        maxBytes=10_485_760,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
]

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt=date_format,
    handlers=handlers
)

# Désactiver les logs trop verboux des bibliothèques tierces
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("playwright").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ==========================================================================
#  Middleware personnalisé : Temps de réponse
# ==========================================================================

class TimingMiddleware:
    """
    Middleware pour mesurer le temps de réponse des requêtes.
    Ajoute un header X-Response-Time.
    """
    async def __call__(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Response-Time"] = f"{process_time:.4f}s"
        # Log des requêtes lentes (plus de 5 secondes)
        if process_time > 5.0:
            logger.warning(
                f"⏱️ Requête lente : {request.method} {request.url.path} - {process_time:.2f}s"
            )
        return response

# ==========================================================================
#  Cycle de vie de l'application (async context manager)
# ==========================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application (startup / shutdown).
    Utilise le nouveau mécanisme de lifespan de FastAPI (>= 0.93).
    """
    # --- STARTUP ---
    logger.info(f"🚀 Démarrage de {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📂 Environnement : {settings.ENV} | Mode debug : {settings.DEBUG}")
    logger.info(f"🗄️ Base de données : {settings.DATABASE_URL}")

    try:
        # 1. Initialiser les services (providers, job manager, cache, etc.)
        init_services()

        # 2. Créer les tables SQLAlchemy si elles n'existent pas
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables SQLAlchemy créées/vérifiées")

        # 3. Vérifier que les providers sont chargés
        registry = ProviderRegistry.get_instance()
        provider_count = len(registry.get_all_providers())
        logger.info(f"✅ {provider_count} providers chargés")

    except Exception as e:
        logger.error(f"❌ Échec de l'initialisation : {e}", exc_info=True)
        raise

    yield  # L'application tourne ici

    # --- SHUTDOWN ---
    logger.info("🛑 Arrêt de l'application...")

    # 1. Fermer le DownloadEngine si actif
    try:
        engine_instance = DownloadEngine()
        await engine_instance.close()
        logger.info("✅ DownloadEngine fermé")
    except Exception as e:
        logger.warning(f"⚠️ Erreur fermeture DownloadEngine : {e}")

    # 2. Fermer les sessions des providers
    try:
        for provider in registry.get_all_providers().values():
            try:
                await provider.close()
            except Exception as e:
                logger.warning(f"⚠️ Erreur fermeture provider {provider.id} : {e}")
        logger.info("✅ Providers fermés")
    except Exception as e:
        logger.warning(f"⚠️ Erreur fermeture providers : {e}")

    # 3. Fermer la base de données
    try:
        engine.dispose()
        logger.info("✅ Base de données fermée")
    except Exception as e:
        logger.warning(f"⚠️ Erreur fermeture DB : {e}")

    logger.info("✅ Application arrêtée proprement")

# ==========================================================================
#  Création de l'application FastAPI
# ==========================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
    contact={
        "name": "NexusDL Community",
        "url": "https://github.com/nexus-dl/nexus-dl",
        "email": "nexusdl@example.com",
    },
    license_info={
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    }
)

# ==========================================================================
#  Middleware
# ==========================================================================

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Response-Time"],
)

# --- Timing ---
app.add_middleware(TimingMiddleware)

# ==========================================================================
#  Routes
# ==========================================================================

# Versionnage de l'API : toutes les routes sont préfixées par /api/v1
app.include_router(api_v1_router, prefix="/api/v1")

# ==========================================================================
#  Endpoints racine et healthcheck
# ==========================================================================

@app.get("/", tags=["System"])
async def root():
    """
    Point d'entrée racine.
    Retourne les informations de base de l'application.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "environment": settings.ENV,
        "debug": settings.DEBUG,
        "docs": "/docs" if settings.DEBUG else None,
        "api": "/api/v1",
    }

@app.get("/health", tags=["System"])
async def health():
    """
    Healthcheck simple pour les orchestrateurs (Docker, Kubernetes, etc.).
    Retourne le statut de l'application.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

# ==========================================================================
#  Gestionnaire d'exceptions global
# ==========================================================================

@app.exception_handler(NexusDLError)
async def nexusdl_exception_handler(request: Request, exc: NexusDLError):
    """
    Gère toutes les exceptions personnalisées de NexusDL.
    """
    status_code = get_http_status_for_exception(exc)
    logger.warning(f"⚠️ {exc.__class__.__name__}: {exc.message}")
    return JSONResponse(
        status_code=status_code,
        content={
            "error": True,
            "detail": exc.message,
            "type": exc.__class__.__name__,
        }
    )

@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    """
    Gère les erreurs d'authentification avec le header WWW-Authenticate.
    """
    logger.warning(f"🔐 Auth error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
        content={
            "error": True,
            "detail": exc.message,
            "type": "AuthenticationError",
        }
    )

@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    """
    Gère les erreurs de rate limiting avec le header Retry-After.
    """
    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    logger.warning(f"🚦 Rate limit: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers=headers,
        content={
            "error": True,
            "detail": exc.message,
            "retry_after": exc.retry_after,
            "type": "RateLimitError",
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Gestionnaire de dernier recours pour toutes les autres exceptions.
    """
    logger.error(
        f"❌ Exception non gérée sur {request.method} {request.url.path}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "detail": "Internal server error",
            "type": "InternalServerError",
        }
    )

# ==========================================================================
#  Point d'entrée pour l'exécution directe
# ==========================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
