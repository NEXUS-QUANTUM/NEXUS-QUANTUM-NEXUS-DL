# ==========================================================================
#  NexusDL 2.0 - Main Application
#  Fichier : backend/app/main.py
#  Version : 2.0.0-final
# ==========================================================================

import logging
import sys
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
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
log_dir.mkdir(parents=True, exist_ok=True)

# getattr avec fallback sur Settings : si LOG_LEVEL n'existe pas, on prend "INFO"
_log_level_name = getattr(settings, "LOG_LEVEL", "INFO")
if not isinstance(_log_level_name, str):
    _log_level_name = "INFO"
log_level = getattr(logging, _log_level_name.upper(), logging.INFO)

log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

handlers = [
    logging.StreamHandler(sys.stdout),
    RotatingFileHandler(
        log_dir / "nexusdl.log",
        maxBytes=10_485_760,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    ),
]

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt=date_format,
    handlers=handlers,
)

logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("playwright").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ==========================================================================
#  Helper : lecture de settings avec fallback (au cas où un attribut manque)
# ==========================================================================

def _s(name, default):
    """Lecture défensive d'un attribut de settings."""
    value = getattr(settings, name, default)
    return default if value is None else value

APP_NAME = _s("APP_NAME", "NexusDL")
APP_VERSION = _s("APP_VERSION", "2.0.0")
APP_DESCRIPTION = _s("APP_DESCRIPTION", "Moteur universel de téléchargement")
ENV = _s("ENV", "production")
DEBUG = bool(_s("DEBUG", False))
DATABASE_URL = _s("DATABASE_URL", "sqlite:///./data/nexus.db")
HOST = _s("HOST", "0.0.0.0")
PORT = int(_s("PORT", 8000))
CORS_ORIGINS = _s("CORS_ORIGINS_LIST", None) or _s("CORS_ORIGINS", ["*"])

# ==========================================================================
#  Middleware : Temps de réponse
# ==========================================================================

class TimingMiddleware(BaseHTTPMiddleware):
    """Mesure le temps de réponse et ajoute un header X-Response-Time."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        response.headers["X-Response-Time"] = f"{process_time:.4f}s"

        if process_time > 5.0:
            logger.warning(
                f"⏱️ Requête lente : {request.method} {request.url.path} - {process_time:.2f}s"
            )

        return response

# ==========================================================================
#  Cycle de vie (lifespan)
# ==========================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info(f"🚀 Démarrage de {APP_NAME} v{APP_VERSION}")
    logger.info(f"📂 Environnement : {ENV} | Mode debug : {DEBUG}")
    logger.info(f"🗄️ Base de données : {DATABASE_URL}")

    registry = None

    try:
        init_services()
        logger.info("✅ Services initialisés")

        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables SQLAlchemy créées/vérifiées")

        registry = ProviderRegistry.get_instance()
        providers = registry.get_all_providers()
        logger.info(f"✅ {len(providers)} providers chargés")

    except Exception as e:
        logger.error(f"❌ Échec de l'initialisation : {e}", exc_info=True)
        raise

    yield

    # --- SHUTDOWN ---
    logger.info("🛑 Arrêt de l'application...")

    if registry is not None:
        try:
            for provider in registry.get_all_providers().values():
                try:
                    close = getattr(provider, "close", None)
                    if callable(close):
                        await close()
                except Exception as e:
                    logger.warning(f"⚠️ Fermeture provider échouée : {e}")
            logger.info("✅ Providers fermés")
        except Exception as e:
            logger.warning(f"⚠️ Erreur fermeture providers : {e}")

    try:
        get_instance = getattr(DownloadEngine, "get_instance", None)
        instance = get_instance() if callable(get_instance) else None
        if instance is not None and hasattr(instance, "close"):
            await instance.close()
            logger.info("✅ DownloadEngine fermé")
    except Exception as e:
        logger.warning(f"⚠️ Erreur fermeture DownloadEngine : {e}")

    try:
        engine.dispose()
        logger.info("✅ Base de données fermée")
    except Exception as e:
        logger.warning(f"⚠️ Erreur fermeture DB : {e}")

    logger.info("✅ Application arrêtée proprement")

# ==========================================================================
#  Application FastAPI
# ==========================================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    openapi_url="/openapi.json" if DEBUG else None,
    lifespan=lifespan,
    contact={
        "name": "NexusDL Community",
        "url": "https://github.com/nexus-dl/nexus-dl",
        "email": "nexusdl@example.com",
    },
    license_info={
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
)

# ==========================================================================
#  Middleware
# ==========================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if isinstance(CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Response-Time"],
)

app.add_middleware(TimingMiddleware)

# ==========================================================================
#  Routes
# ==========================================================================

app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/", tags=["System"])
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "environment": ENV,
        "debug": DEBUG,
        "docs": "/docs" if DEBUG else None,
        "api": "/api/v1",
    }

@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy", "app": APP_NAME, "version": APP_VERSION}

# ==========================================================================
#  Gestionnaires d'exceptions
# ==========================================================================

@app.exception_handler(NexusDLError)
async def nexusdl_exception_handler(request: Request, exc: NexusDLError):
    status_code = get_http_status_for_exception(exc)
    logger.warning(f"⚠️ {exc.__class__.__name__}: {exc.message}")
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "detail": exc.message, "type": exc.__class__.__name__},
    )

@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    logger.warning(f"🔐 Auth error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
        content={"error": True, "detail": exc.message, "type": "AuthenticationError"},
    )

@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    headers = {}
    if getattr(exc, "retry_after", None):
        headers["Retry-After"] = str(exc.retry_after)
    logger.warning(f"🚦 Rate limit: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers=headers,
        content={
            "error": True,
            "detail": exc.message,
            "retry_after": getattr(exc, "retry_after", None),
            "type": "RateLimitError",
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"❌ Exception non gérée sur {request.method} {request.url.path}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "detail": "Internal server error",
            "type": "InternalServerError",
        },
    )

# ==========================================================================
#  Point d'entrée direct
# ==========================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level=_log_level_name.lower(),
    )
