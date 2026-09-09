# ==========================================================================
#  NexusDL 2.0 - Service de gestion des fichiers
#  Fichier : backend/app/services/file_service.py
# ==========================================================================

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.core.exceptions import FileOperationError, FileNotFoundError
from app.models.library import LibraryItem
from app.services.cbz_service import CbzService

logger = logging.getLogger(__name__)


class FileService:
    """
    Service de gestion des fichiers et de la bibliothèque.
    Gère les opérations sur les fichiers CBZ, l'indexation, la recherche,
    l'import/export et la maintenance de la bibliothèque.
    """

    def __init__(self):
        self.download_path = settings.get_download_path()
        self.temp_path = settings.get_temp_path()
        self.cbz_service = CbzService()
        # Cache en mémoire pour les éléments de la bibliothèque (simplifié)
        self._library_cache: Dict[str, LibraryItem] = {}
        self._cache_loaded = False
        self._executor = ThreadPoolExecutor(max_workers=4)

    # ==========================================================================
    #  Gestion de la bibliothèque
    # ==========================================================================

    def _get_library_files(self) -> List[Path]:
        """Récupère la liste de tous les fichiers CBZ dans le dossier de téléchargement."""
        return list(self.download_path.glob("*.cbz"))

    def _load_library_cache(self):
        """Charge tous les éléments de la bibliothèque dans le cache."""
        if self._cache_loaded:
            return
        self._library_cache.clear()
        for file_path in self._get_library_files():
            try:
                # Créer un LibraryItem à partir du fichier
                item = self._create_library_item_from_path(file_path)
                self._library_cache[item.filename] = item
            except Exception as e:
                logger.error(f"Erreur chargement {file_path}: {e}")
        self._cache_loaded = True
        logger.info(f"Cache bibliothèque chargé : {len(self._library_cache)} éléments")

    def _create_library_item_from_path(self, file_path: Path) -> LibraryItem:
        """Crée un LibraryItem à partir d'un chemin de fichier (synchrone)."""
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")

        # Extraire les métadonnées (synchrone)
        metadata = self.cbz_service.builder.extract_metadata(file_path)
        title = metadata.get("title", file_path.stem) if metadata else file_path.stem

        item = LibraryItem(
            title=title,
            filename=file_path.name,
            file_path=str(file_path),
            size_bytes=file_path.stat().st_size,
            metadata=metadata,
            tags=[]
        )
        return item

    async def get_library_items(
        self,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        author: Optional[str] = None,
        tag: Optional[str] = None,
        favorite: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Récupère les éléments de la bibliothèque avec filtres et pagination.
        """
        # Charger le cache si nécessaire
        if not self._cache_loaded:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._load_library_cache
            )

        items = list(self._library_cache.values())

        # Appliquer les filtres
        if search:
            search_lower = search.lower()
            items = [
                item for item in items
                if search_lower in item.title.lower()
                or (item.metadata and search_lower in item.metadata.get("author", "").lower())
            ]
        if genre and items:
            items = [
                item for item in items
                if item.metadata and genre.lower() in item.metadata.get("genre", "").lower()
            ]
        if author and items:
            items = [
                item for item in items
                if item.metadata and author.lower() in item.metadata.get("author", "").lower()
            ]
        if tag and items:
            items = [item for item in items if tag in (item.tags or [])]
        if favorite is not None:
            items = [item for item in items if item.is_favorite == favorite]

        # Trier
        if sort_by == "title":
            items.sort(key=lambda x: x.title.lower(), reverse=(sort_order == "desc"))
        elif sort_by == "size":
            items.sort(key=lambda x: x.size_bytes, reverse=(sort_order == "desc"))
        elif sort_by == "rating":
            items.sort(key=lambda x: x.rating, reverse=(sort_order == "desc"))
        elif sort_by == "last_read":
            items.sort(
                key=lambda x: x.last_read or datetime.min,
                reverse=(sort_order == "desc")
            )
        elif sort_by == "read_count":
            items.sort(key=lambda x: x.read_count, reverse=(sort_order == "desc"))
        else:  # created_at par défaut
            items.sort(
                key=lambda x: x.created_at,
                reverse=(sort_order == "desc")
            )

        total = len(items)
        paginated = items[offset:offset + limit]

        return {
            "items": [item.to_dict() for item in paginated],
            "total": total,
            "offset": offset,
            "limit": limit
        }

    async def get_library_item(self, filename: str) -> Optional[LibraryItem]:
        """Récupère un élément spécifique par son nom de fichier."""
        if not self._cache_loaded:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._load_library_cache
            )
        return self._library_cache.get(filename)

    async def get_library_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques de la bibliothèque."""
        if not self._cache_loaded:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._load_library_cache
            )

        items = list(self._library_cache.values())
        total = len(items)
        total_size = sum(item.size_bytes for item in items)
        favorites = sum(1 for item in items if item.is_favorite)
        genres = set()
        authors = set()
        tags = set()

        for item in items:
            if item.metadata:
                if item.metadata.get("genre"):
                    genres.update([g.strip() for g in item.metadata["genre"].split(",")])
                if item.metadata.get("author"):
                    authors.add(item.metadata["author"])
            if item.tags:
                tags.update(item.tags)

        return {
            "total_items": total,
            "total_size_bytes": total_size,
            "total_size_formatted": self._format_size(total_size),
            "favorites_count": favorites,
            "genres": sorted(genres),
            "authors": sorted(authors),
            "tags": sorted(tags),
            "oldest_item": min((item.created_at for item in items), default=None),
            "newest_item": max((item.created_at for item in items), default=None),
        }

    # ==========================================================================
    #  Opérations sur les éléments
    # ==========================================================================

    async def update_library_item(
        self,
        filename: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_favorite: Optional[bool] = None,
        rating: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Met à jour les propriétés d'un élément de la bibliothèque.
        """
        item = await self.get_library_item(filename)
        if not item:
            return False

        if title:
            item.title = title
        if tags is not None:
            item.tags = tags
        if is_favorite is not None:
            item.is_favorite = is_favorite
        if rating is not None:
            item.set_rating(rating)
        if metadata:
            item.update_metadata(metadata)

        # Mettre à jour le cache
        self._library_cache[filename] = item
        return True

    async def delete_library_item(self, filename: str) -> bool:
        """
        Supprime un élément de la bibliothèque (fichier et cache).
        """
        item = await self.get_library_item(filename)
        if not item:
            return False

        file_path = Path(item.file_path)
        if file_path.exists():
            # Supprimer le fichier
            await asyncio.get_event_loop().run_in_executor(
                self._executor, file_path.unlink
            )
            # Supprimer les miniatures associées
            for cache_file in self.cbz_service.cover_cache_dir.glob(f"{file_path.stem}_*.jpg"):
                cache_file.unlink()

        # Supprimer du cache
        self._library_cache.pop(filename, None)
        return True

    async def add_library_item(self, file_path: Path) -> Optional[LibraryItem]:
        """
        Ajoute un fichier CBZ à la bibliothèque (importation).
        Déplace le fichier dans le dossier de téléchargement s'il n'y est pas déjà.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")

        # Si le fichier n'est pas dans le dossier de téléchargement, le déplacer
        if file_path.parent != self.download_path:
            new_path = self.download_path / file_path.name
            # Éviter les conflits de noms
            counter = 1
            while new_path.exists():
                stem = file_path.stem
                new_path = self.download_path / f"{stem}_{counter}{file_path.suffix}"
                counter += 1
            shutil.move(str(file_path), str(new_path))
            file_path = new_path

        # Créer l'élément
        item = self._create_library_item_from_path(file_path)
        self._library_cache[item.filename] = item
        logger.info(f"📚 Élément ajouté à la bibliothèque : {item.title}")
        return item

    # ==========================================================================
    #  Utilitaires
    # ==========================================================================

    def _format_size(self, size_bytes: int) -> str:
        """Formate une taille en octets."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    async def refresh_cache(self):
        """Recharge le cache de la bibliothèque."""
        self._cache_loaded = False
        await asyncio.get_event_loop().run_in_executor(
            self._executor, self._load_library_cache
        )

    async def get_cover_path(self, filename: str, size: tuple = (200, 300)) -> Optional[str]:
        """
        Récupère le chemin de la miniature pour un élément de la bibliothèque.
        """
        item = await self.get_library_item(filename)
        if not item:
            return None
        file_path = Path(item.file_path)
        if not file_path.exists():
            return None
        cover_path = await self.cbz_service.get_cover_image(file_path, size)
        return str(cover_path) if cover_path else None

    # ==========================================================================
    #  Opérations de maintenance
    # ==========================================================================

    async def clean_temp_files(self):
        """Supprime les fichiers temporaires inutilisés."""
        temp_files = list(self.temp_path.glob("*"))
        deleted = 0
        for item in temp_files:
            if item.is_file():
                item.unlink()
                deleted += 1
            elif item.is_dir():
                shutil.rmtree(item)
                deleted += 1
        logger.info(f"Nettoyage temp : {deleted} fichiers supprimés")
        return deleted

    async def get_disk_usage(self) -> Dict[str, Any]:
        """Retourne l'utilisation du disque pour les dossiers de l'application."""
        download_usage = sum(f.stat().st_size for f in self.download_path.rglob("*") if f.is_file())
        temp_usage = sum(f.stat().st_size for f in self.temp_path.rglob("*") if f.is_file())
        return {
            "download_path": {
                "path": str(self.download_path),
                "size_bytes": download_usage,
                "size_formatted": self._format_size(download_usage)
            },
            "temp_path": {
                "path": str(self.temp_path),
                "size_bytes": temp_usage,
                "size_formatted": self._format_size(temp_usage)
            }
        }
