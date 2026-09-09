# ==========================================================================
#  NexusDL 2.0 - Configuration
#  Fichier : backend/app/core/config.py
# ==========================================================================

import os
import json
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Application
    APP_NAME: str = "NexusDL"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Moteur universel de téléchargement de scans"
    BUILD_DATE: str = "2025-01-15T00:00:00Z"
    
    # Environnement
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Serveur
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Base de données
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/nexus.db")
    
    # Sécurité
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS
    CORS_ORIGINS: List[str] = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:5173","http://localhost:80"]'))
    
    # Téléchargements
    MAX_THREADS: int = int(os.getenv("MAX_THREADS", "10"))
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "30"))
    DOWNLOAD_RETRY: int = int(os.getenv("DOWNLOAD_RETRY", "3"))
    DOWNLOAD_PATH: str = os.getenv("DOWNLOAD_PATH", "./data/downloads")
    TEMP_PATH: str = os.getenv("TEMP_PATH", "./data/temp")
    
    # Cache
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "500"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_MAX: int = int(os.getenv("RATE_LIMIT_MAX", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return self.CORS_ORIGINS
    
    def get_download_path(self) -> Path:
        path = Path(self.DOWNLOAD_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_temp_path(self) -> Path:
        path = Path(self.TEMP_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "app_name": self.APP_NAME,
            "app_version": self.APP_VERSION,
            "env": self.ENV,
            "debug": self.DEBUG,
            "max_threads": self.MAX_THREADS,
            "cache_enabled": self.CACHE_ENABLED,
            "rate_limit_enabled": self.RATE_LIMIT_ENABLED
        }

settings = Settings()
