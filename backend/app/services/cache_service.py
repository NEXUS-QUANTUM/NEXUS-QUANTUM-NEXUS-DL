# ==========================================================================
#  NexusDL 2.0 - Service de Cache
#  Fichier : backend/app/services/cache_service.py
# ==========================================================================

import time
import logging
import hashlib
import json
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import asyncio
from collections import OrderedDict

from app.core.config import settings
from app.core.exceptions import CacheError

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service de cache simple en mémoire avec persistance optionnelle sur disque.
    Supporte les TTL, l'invalidation et les statistiques.
    """

    def __init__(self):
        self.enabled = settings.CACHE_ENABLED
        self.max_size = settings.CACHE_MAX_SIZE
        self.default_ttl = settings.CACHE_TTL
        self.cache_dir = settings.get_temp_path() / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache en mémoire : OrderedDict pour implémenter LRU
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._locks: Dict[str, asyncio.Lock] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_entries": 0,
            "memory_usage": 0
        }

        # Nettoyer périodiquement le cache obsolète
        self._cleanup_task = None

    async def start(self):
        """Démarre le service de cache (nettoyage automatique)."""
        if self.enabled:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("✅ Service de cache démarré")

    async def stop(self):
        """Arrête le service de cache."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        logger.info("✅ Service de cache arrêté")

    def _get_cache_key(self, key: str) -> str:
        """Génère une clé de cache unique à partir d'une chaîne."""
        return hashlib.sha256(key.encode()).hexdigest()

    async def _get_lock(self, key: str) -> asyncio.Lock:
        """Retourne un verrou pour une clé donnée."""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        Retourne `default` si la clé n'existe pas ou est expirée.
        """
        if not self.enabled:
            return default

        cache_key = self._get_cache_key(key)
        lock = await self._get_lock(cache_key)

        async with lock:
            if cache_key not in self._cache:
                self._stats["misses"] += 1
                return default

            entry = self._cache[cache_key]
            # Vérifier l'expiration
            if entry["expires_at"] and time.time() > entry["expires_at"]:
                del self._cache[cache_key]
                self._stats["misses"] += 1
                self._stats["total_entries"] -= 1
                return default

            # Mettre à jour l'ordre LRU
            self._cache.move_to_end(cache_key)
            self._stats["hits"] += 1
            return entry["value"]

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        persist: bool = False
    ) -> bool:
        """
        Stocke une valeur dans le cache.
        - ttl: durée de vie en secondes (None pour utiliser la valeur par défaut)
        - persist: sauvegarder sur disque (expérimental)
        """
        if not self.enabled:
            return False

        cache_key = self._get_cache_key(key)
        lock = await self._get_lock(cache_key)

        async with lock:
            # Nettoyer si le cache est plein
            if len(self._cache) >= self.max_size:
                self._evict_one()

            expires_at = None
            if ttl is None:
                ttl = self.default_ttl
            if ttl > 0:
                expires_at = time.time() + ttl

            entry = {
                "key": key,
                "value": value,
                "created_at": time.time(),
                "expires_at": expires_at,
                "size": len(json.dumps(value)) if isinstance(value, (dict, list)) else len(str(value))
            }

            self._cache[cache_key] = entry
            self._stats["total_entries"] += 1
            self._stats["memory_usage"] += entry["size"]

            # Persistance sur disque (optionnel)
            if persist:
                await self._persist(cache_key, entry)

            return True

    async def delete(self, key: str) -> bool:
        """Supprime une entrée du cache."""
        if not self.enabled:
            return False

        cache_key = self._get_cache_key(key)
        lock = await self._get_lock(cache_key)

        async with lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                self._stats["memory_usage"] -= entry["size"]
                del self._cache[cache_key]
                self._stats["total_entries"] -= 1
                # Supprimer également le fichier persistant
                await self._delete_persisted(cache_key)
                return True
            return False

    async def clear(self) -> int:
        """Vide entièrement le cache."""
        if not self.enabled:
            return 0

        count = len(self._cache)
        self._cache.clear()
        self._stats["total_entries"] = 0
        self._stats["memory_usage"] = 0

        # Supprimer les fichiers persistants
        for file in self.cache_dir.glob("*.cache"):
            try:
                file.unlink()
            except Exception as e:
                logger.warning(f"Impossible de supprimer {file}: {e}")

        logger.info(f"Cache vidé : {count} entrées supprimées")
        return count

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalide toutes les clés correspondant à un motif.
        (Implémentation simple : recherche partielle dans les clés)
        """
        if not self.enabled:
            return 0

        keys_to_delete = []
        for cache_key, entry in self._cache.items():
            if pattern in entry["key"]:
                keys_to_delete.append(cache_key)

        for cache_key in keys_to_delete:
            del self._cache[cache_key]

        self._stats["total_entries"] -= len(keys_to_delete)
        return len(keys_to_delete)

    def _evict_one(self):
        """Évite une entrée selon la politique LRU."""
        if not self._cache:
            return
        # Le premier élément est le plus ancien (LRU)
        cache_key, entry = self._cache.popitem(last=False)
        self._stats["memory_usage"] -= entry["size"]
        self._stats["total_entries"] -= 1
        self._stats["evictions"] += 1
        logger.debug(f"Éviction du cache : {entry['key']}")

    async def _persist(self, cache_key: str, entry: Dict[str, Any]):
        """Sauvegarde une entrée sur disque."""
        try:
            file_path = self.cache_dir / f"{cache_key}.cache"
            data = {
                "key": entry["key"],
                "value": entry["value"],
                "created_at": entry["created_at"],
                "expires_at": entry["expires_at"]
            }
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Erreur persistance cache {cache_key}: {e}")

    async def _delete_persisted(self, cache_key: str):
        """Supprime le fichier persistant d'une entrée."""
        try:
            file_path = self.cache_dir / f"{cache_key}.cache"
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Erreur suppression persistance {cache_key}: {e}")

    async def _load_from_disk(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Charge une entrée depuis le disque."""
        try:
            file_path = self.cache_dir / f"{cache_key}.cache"
            if not file_path.exists():
                return None
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                data = await f.read()
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Erreur chargement cache disque {cache_key}: {e}")
            return None

    async def _periodic_cleanup(self):
        """Nettoye périodiquement les entrées expirées."""
        while True:
            try:
                await asyncio.sleep(60)  # Nettoyer toutes les minutes
                if not self.enabled:
                    continue

                now = time.time()
                to_delete = []
                for cache_key, entry in self._cache.items():
                    if entry["expires_at"] and entry["expires_at"] < now:
                        to_delete.append(cache_key)

                for cache_key in to_delete:
                    lock = await self._get_lock(cache_key)
                    async with lock:
                        if cache_key in self._cache:
                            entry = self._cache[cache_key]
                            del self._cache[cache_key]
                            self._stats["memory_usage"] -= entry["size"]
                            self._stats["total_entries"] -= 1

                if to_delete:
                    logger.debug(f"Nettoyage cache : {len(to_delete)} entrées expirées")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur nettoyage cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache."""
        return {
            **self._stats,
            "size": len(self._cache),
            "max_size": self.max_size,
            "enabled": self.enabled,
            "hit_rate": (
                self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
                if (self._stats["hits"] + self._stats["misses"]) > 0 else 0
            )
        }

    def size(self) -> int:
        """Retourne le nombre d'éléments dans le cache."""
        return len(self._cache)
