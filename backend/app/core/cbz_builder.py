# ==========================================================================
#  NexusDL 2.0 - CBZ Builder
#  Fichier : backend/app/core/cbz_builder.py
# ==========================================================================

import os
import zipfile
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from PIL import Image
import shutil

from app.core.config import settings
from app.core.exceptions import CbzBuildError

logger = logging.getLogger(__name__)


class CbzBuilder:
    """
    Constructeur de fichiers CBZ (Comic Book Zip).
    Génère un fichier ZIP avec les images et un fichier ComicInfo.xml
    contenant les métadonnées.
    """

    def __init__(self):
        self.temp_dir = settings.get_temp_path()
        self.output_dir = settings.get_download_path()
        self.max_image_dimension = 4000  # Redimensionnement si nécessaire

    async def build(
        self,
        title: str,
        chapters: List[Dict[str, Any]],
        output_dir: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Construit un fichier CBZ à partir d'une liste de chapitres contenant des images.

        Args:
            title (str): Titre du manga/manhwa.
            chapters (List[Dict[str, Any]]): Liste des chapitres.
                Chaque chapitre est un dict avec :
                    - "chapter_title": str (titre du chapitre)
                    - "images": List[Path] (chemins des images)
            output_dir (Optional[Path]): Dossier de sortie (par défaut DOWNLOAD_PATH).
            metadata (Optional[Dict[str, Any]]): Métadonnées supplémentaires.

        Returns:
            Path: Chemin du fichier CBZ créé.

        Raises:
            CbzBuildError: Si une erreur survient lors de la construction.
        """
        output_dir = output_dir or self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Nettoyer le titre pour le nom de fichier
        safe_title = self._sanitize_filename(title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cbz_filename = f"{safe_title}_{timestamp}.cbz"
        cbz_path = output_dir / cbz_filename

        # Dossier temporaire pour cette construction
        work_dir = self.temp_dir / f"cbz_build_{timestamp}"
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Étape 1: Organiser les images par chapitre et numéroter
            all_images = []
            for idx, chapter in enumerate(chapters, start=1):
                chapter_title = chapter.get("chapter_title", f"Chapter_{idx}")
                image_paths = chapter.get("images", [])
                if not image_paths:
                    logger.warning(f"Chapitre {chapter_title} sans images, ignoré.")
                    continue

                # Copier les images dans le dossier de travail avec un préfixe de chapitre
                for img_idx, img_path in enumerate(image_paths, start=1):
                    if not img_path.exists():
                        logger.warning(f"Image introuvable: {img_path}, ignorée")
                        continue
                    # Créer un nom de fichier avec numéro de chapitre et numéro d'image
                    # Exemple: 01_001.jpg, 01_002.jpg, 02_001.jpg...
                    new_filename = f"{idx:02d}_{img_idx:03d}{img_path.suffix}"
                    dest_path = work_dir / new_filename
                    # Copier ou déplacer
                    shutil.copy2(img_path, dest_path)
                    # Optionnel: redimensionner les très grandes images
                    if self._should_resize(dest_path):
                        self._resize_image(dest_path)
                    all_images.append(dest_path)

            if not all_images:
                raise CbzBuildError("Aucune image valide à inclure dans le CBZ.")

            # Étape 2: Générer ComicInfo.xml
            comic_info = self._generate_comicinfo_xml(
                title=title,
                chapters=chapters,
                metadata=metadata,
                total_pages=len(all_images)
            )
            info_path = work_dir / "ComicInfo.xml"
            with open(info_path, "w", encoding="utf-8") as f:
                f.write(comic_info)

            # Étape 3: Créer le fichier ZIP (CBZ)
            with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Ajouter toutes les images
                for img_path in sorted(work_dir.glob("*.jpg")) + sorted(work_dir.glob("*.jpeg")) + \
                                  sorted(work_dir.glob("*.png")) + sorted(work_dir.glob("*.webp")) + \
                                  sorted(work_dir.glob("*.gif")):
                    zf.write(img_path, img_path.name)
                # Ajouter ComicInfo.xml
                zf.write(info_path, "ComicInfo.xml")

            logger.info(f"✅ CBZ créé: {cbz_path} ({len(all_images)} pages)")

            return cbz_path

        except Exception as e:
            logger.error(f"Erreur lors de la construction du CBZ: {e}")
            raise CbzBuildError(f"Échec de la construction du CBZ: {e}")
        finally:
            # Nettoyer le dossier temporaire
            if work_dir.exists():
                shutil.rmtree(work_dir, ignore_errors=True)

    def _sanitize_filename(self, name: str) -> str:
        """Nettoie une chaîne pour en faire un nom de fichier valide."""
        # Remplacer les caractères problématiques
        invalid_chars = r'<>:"/\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        # Limiter la longueur
        if len(name) > 200:
            name = name[:200]
        return name.strip()

    def _should_resize(self, image_path: Path) -> bool:
        """Détermine si l'image doit être redimensionnée."""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                return width > self.max_image_dimension or height > self.max_image_dimension
        except Exception:
            return False

    def _resize_image(self, image_path: Path):
        """Redimensionne une image pour la réduire si elle est trop grande."""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                if width > self.max_image_dimension or height > self.max_image_dimension:
                    ratio = min(self.max_image_dimension / width, self.max_image_dimension / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img.thumbnail(new_size, Image.Resampling.LANCZOS)
                    img.save(image_path, quality=85, optimize=True)
                    logger.debug(f"Image redimensionnée: {image_path.name} ({width}x{height} -> {new_size[0]}x{new_size[1]})")
        except Exception as e:
            logger.warning(f"Impossible de redimensionner {image_path.name}: {e}")

    def _generate_comicinfo_xml(
        self,
        title: str,
        chapters: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        total_pages: int = 0
    ) -> str:
        """
        Génère le contenu du fichier ComicInfo.xml selon le schéma standard.

        Référence: https://github.com/anansi-project/comicinfo
        """
        metadata = metadata or {}
        root = ET.Element("ComicInfo")
        root.set("xmlns", "http://www.denki.ne.jp/~chizu/ComicInfo.xml")

        # Informations de base
        self._add_element(root, "Title", title or metadata.get("title", "Unknown"))
        self._add_element(root, "Series", metadata.get("series") or title)
        self._add_element(root, "Writer", metadata.get("author") or "")
        self._add_element(root, "Artist", metadata.get("artist") or metadata.get("author") or "")
        self._add_element(root, "Publisher", metadata.get("publisher") or "NexusDL")
        self._add_element(root, "Genre", metadata.get("genre") or "")
        self._add_element(root, "Summary", metadata.get("description") or "")
        self._add_element(root, "Volume", metadata.get("volume") or "")
        self._add_element(root, "Year", str(metadata.get("year", datetime.now().year)))
        self._add_element(root, "Language", metadata.get("language") or "fr")
        self._add_element(root, "PageCount", str(total_pages))

        # Informations sur les chapitres
        chapter_titles = [ch.get("chapter_title", f"Chapitre {i+1}") for i, ch in enumerate(chapters)]
        self._add_element(root, "Chapters", ", ".join(chapter_titles))

        # Date de création
        self._add_element(root, "Manga", "Yes")  # Indiquer que c'est un manga

        # Tags supplémentaires si présents
        for key, value in metadata.items():
            if key not in ["title", "series", "author", "artist", "publisher", "genre",
                           "description", "volume", "year", "language", "chapters"]:
                self._add_element(root, key.capitalize(), str(value))

        # Ajout des pages (si on connaît les numéros de page, on peut les lister)
        # Pour simplifier, on ne les ajoute pas ici.

        # Conversion en XML formaté
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_str += ET.tostring(root, encoding="unicode", method="xml")
        return xml_str

    def _add_element(self, parent: ET.Element, tag: str, text: str):
        """Ajoute un élément enfant avec un texte, si le texte n'est pas vide."""
        if text:
            elem = ET.SubElement(parent, tag)
            elem.text = text

    def extract_metadata(self, cbz_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extrait les métadonnées d'un fichier CBZ existant.
        Retourne un dictionnaire ou None si le fichier n'existe pas ou est invalide.
        """
        if not cbz_path.exists():
            return None
        try:
            with zipfile.ZipFile(cbz_path, 'r') as zf:
                # Chercher ComicInfo.xml
                for name in zf.namelist():
                    if name.lower().endswith('comicinfo.xml'):
                        with zf.open(name) as f:
                            tree = ET.parse(f)
                            root = tree.getroot()
                            ns = {'comic': 'http://www.denki.ne.jp/~chizu/ComicInfo.xml'}
                            def get_text(tag):
                                elem = root.find(f'.//comic:{tag}', ns)
                                if elem is None:
                                    elem = root.find(f'.//{tag}')
                                return elem.text.strip() if elem is not None and elem.text else None
                            return {
                                'title': get_text('Title'),
                                'series': get_text('Series'),
                                'author': get_text('Writer') or get_text('Artist'),
                                'publisher': get_text('Publisher'),
                                'genre': get_text('Genre'),
                                'description': get_text('Summary'),
                                'volume': get_text('Volume'),
                                'year': get_text('Year'),
                                'language': get_text('Language'),
                                'pages': int(get_text('PageCount') or 0)
                            }
            return None
        except Exception as e:
            logger.warning(f"Impossible d'extraire les métadonnées de {cbz_path}: {e}")
            return None
