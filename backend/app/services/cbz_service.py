# ==========================================================================
#  NexusDL 2.0 - Service CBZ
#  Fichier : backend/app/services/cbz_service.py
# ==========================================================================

import os
import zipfile
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import xml.etree.ElementTree as ET
import asyncio
from PIL import Image

from app.core.config import settings
from app.core.cbz_builder import CbzBuilder
from app.core.exceptions import CbzBuildError, FileNotFoundError, CbzExtractionError
from app.models.library import LibraryItem

logger = logging.getLogger(__name__)


class CbzService:
    """
    Service de gestion des fichiers CBZ.
    Fournit des opérations de haut niveau pour la manipulation des CBZ :
    extraction de métadonnées, génération de miniatures, gestion de la bibliothèque.
    """

    def __init__(self):
        self.builder = CbzBuilder()
        self.download_path = settings.get_download_path()
        self.cover_cache_dir = settings.get_temp_path() / "covers"
        self.cover_cache_dir.mkdir(parents=True, exist_ok=True)

    async def extract_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extrait les métadonnées d'un fichier CBZ.
        Utilise le builder pour l'extraction.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")
        return self.builder.extract_metadata(file_path)

    async def get_cover_image(self, file_path: Path, size: tuple = (200, 300)) -> Optional[Path]:
        """
        Extrait la première image du CBZ et la redimensionne pour en faire une miniature.
        Met en cache la miniature générée.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")

        # Générer un nom de cache basé sur le fichier et la taille
        cache_name = f"{file_path.stem}_{size[0]}x{size[1]}.jpg"
        cache_path = self.cover_cache_dir / cache_name

        if cache_path.exists():
            return cache_path

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Trouver la première image (ordre alphabétique)
                image_files = [name for name in zf.namelist()
                               if name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))
                               and not name.lower().startswith('__')]  # ignorer les fichiers système

                if not image_files:
                    return None

                # Trier pour obtenir la première image
                image_files.sort()
                first_image = image_files[0]

                with zf.open(first_image) as img_file:
                    from PIL import Image
                    img = Image.open(img_file)
                    # Redimensionner en conservant le ratio
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                    # Convertir en RGB si nécessaire (pour les images avec transparence)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    img.save(cache_path, 'JPEG', quality=85)
                    return cache_path

        except Exception as e:
            logger.error(f"Erreur extraction couverture de {file_path}: {e}")
            return None

    async def get_metadata_from_cbz(self, file_path: Path) -> Dict[str, Any]:
        """
        Récupère les métadonnées structurées d'un CBZ.
        Retourne un dictionnaire avec les champs standard.
        """
        metadata = await self.extract_metadata(file_path)
        if not metadata:
            return {}
        # Ajouter des champs dérivés si nécessaire
        return metadata

    async def get_comic_info_xml(self, file_path: Path) -> Optional[str]:
        """
        Extrait le contenu brut de ComicInfo.xml du CBZ.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                for name in zf.namelist():
                    if name.lower().endswith('comicinfo.xml'):
                        with zf.open(name) as f:
                            return f.read().decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Erreur extraction ComicInfo.xml de {file_path}: {e}")
            raise CbzExtractionError(f"Impossible d'extraire ComicInfo.xml : {e}")

    async def rebuild_metadata(self, file_path: Path, new_metadata: Dict[str, Any]) -> bool:
        """
        Met à jour les métadonnées d'un fichier CBZ en régénérant ComicInfo.xml.
        Crée une copie du fichier original et remplace le fichier.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")

        temp_path = file_path.parent / f"{file_path.stem}_temp{file_path.suffix}"
        try:
            # Copier le fichier original
            shutil.copy2(file_path, temp_path)

            # Supprimer l'ancien ComicInfo.xml et ajouter le nouveau
            with zipfile.ZipFile(temp_path, 'a') as zf:
                # Supprimer l'ancien ComicInfo.xml s'il existe
                for name in zf.namelist():
                    if name.lower().endswith('comicinfo.xml'):
                        zf.remove(name)
                        break

                # Ajouter le nouveau ComicInfo.xml
                # Utiliser le builder pour générer le XML
                xml_content = self.builder._generate_comicinfo_xml(
                    title=new_metadata.get("title", file_path.stem),
                    chapters=[],
                    metadata=new_metadata,
                    total_pages=0
                )
                zf.writestr("ComicInfo.xml", xml_content.encode('utf-8'))

            # Remplacer l'original par le nouveau
            shutil.move(temp_path, file_path)
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour métadonnées {file_path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise CbzBuildError(f"Échec de la mise à jour des métadonnées : {e}")

    async def get_cbz_pages_count(self, file_path: Path) -> int:
        """
        Retourne le nombre de pages (images) dans un fichier CBZ.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                image_count = sum(1 for name in zf.namelist()
                                  if name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))
                                  and not name.lower().startswith('__'))
                return image_count
        except Exception as e:
            logger.error(f"Erreur comptage pages {file_path}: {e}")
            raise CbzExtractionError(f"Impossible de compter les pages : {e}")

    async def get_cbz_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Récupère toutes les informations disponibles sur un CBZ :
        métadonnées, nombre de pages, taille, date, etc.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")

        stat = file_path.stat()
        metadata = await self.extract_metadata(file_path)
        pages = await self.get_cbz_pages_count(file_path)

        return {
            "filename": file_path.name,
            "path": str(file_path),
            "size_bytes": stat.st_size,
            "size_formatted": self._format_size(stat.st_size),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "pages": pages,
            "metadata": metadata or {}
        }

    def _format_size(self, size_bytes: int) -> str:
        """Formate une taille en octets."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    async def delete_cbz(self, file_path: Path) -> bool:
        """
        Supprime définitivement un fichier CBZ.
        Supprime également la miniature en cache.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")

        # Supprimer les miniatures en cache associées
        for cache_file in self.cover_cache_dir.glob(f"{file_path.stem}_*.jpg"):
            cache_file.unlink()

        file_path.unlink()
        return True

    async def create_library_item_from_cbz(self, file_path: Path) -> LibraryItem:
        """
        Crée un objet LibraryItem à partir d'un fichier CBZ.
        Utilisé lors de l'importation de fichiers dans la bibliothèque.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {file_path}")

        metadata = await self.extract_metadata(file_path)
        title = metadata.get("title", file_path.stem) if metadata else file_path.stem

        item = LibraryItem.from_cbz(
            file_path=str(file_path),
            title=title,
            metadata=metadata
        )
        return item

    async def scan_directory(self, directory: Path) -> List[Path]:
        """
        Scanne un dossier et retourne la liste des fichiers CBZ trouvés.
        """
        if not directory.exists():
            raise FileNotFoundError(f"Dossier introuvable : {directory}")

        cbz_files = list(directory.glob("*.cbz"))
        return cbz_files
