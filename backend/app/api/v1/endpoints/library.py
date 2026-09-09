# ==========================================================================
#  NexusDL 2.0 - Library Endpoints
#  Fichier : backend/app/api/v1/endpoints/library.py
# ==========================================================================

import os
import logging
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.file_service import FileService
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.deps import get_file_service
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/library", tags=["Library"])

# ==========================================================================
#  Schémas
# ==========================================================================

class LibraryMetadata(BaseModel):
    """Métadonnées extraites d'un fichier CBZ."""
    title: str
    series: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    volume: Optional[str] = None
    chapters: Optional[int] = None
    pages: Optional[int] = None
    year: Optional[int] = None
    language: Optional[str] = None

class LibraryItem(BaseModel):
    """Élément de la bibliothèque (fichier CBZ)."""
    id: str  # Nom du fichier
    filename: str
    title: str
    size_bytes: int
    size_formatted: str
    created_at: str
    modified_at: str
    metadata: Optional[LibraryMetadata] = None
    cover_url: Optional[str] = None  # Pour afficher une miniature

class LibraryListResponse(BaseModel):
    """Réponse paginée de la bibliothèque."""
    items: List[LibraryItem]
    total: int
    offset: int
    limit: int

class LibraryStats(BaseModel):
    """Statistiques de la bibliothèque."""
    total_items: int
    total_size_bytes: int
    total_size_formatted: str
    oldest_item: Optional[str]
    newest_item: Optional[str]
    average_size_bytes: Optional[float]
    genres: List[str]
    authors: List[str]

class DeleteResponse(BaseModel):
    """Réponse après suppression."""
    success: bool
    message: str

# ==========================================================================
#  Fonctions utilitaires
# ==========================================================================

def extract_metadata_from_cbz(file_path: str) -> Optional[LibraryMetadata]:
    """
    Extrait les métadonnées ComicInfo.xml d'un fichier CBZ.
    Retourne un objet LibraryMetadata ou None si le fichier n'existe pas ou
    ne contient pas de métadonnées.
    """
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            # Chercher ComicInfo.xml (insensible à la casse)
            comic_info_files = [name for name in zf.namelist() if name.lower() == 'comicinfo.xml']
            if not comic_info_files:
                # Essayer de trouver dans un dossier
                comic_info_files = [name for name in zf.namelist() if 'comicinfo.xml' in name.lower()]
            if not comic_info_files:
                return None
            with zf.open(comic_info_files[0]) as f:
                tree = ET.parse(f)
                root = tree.getroot()
                ns = {'comic': 'http://www.denki.ne.jp/~chizu/ComicInfo.xml'}
                # On essaye avec namespace, sinon sans
                def get_text(tag):
                    elem = root.find(f'.//comic:{tag}', ns)
                    if elem is None:
                        elem = root.find(f'.//{tag}')
                    return elem.text.strip() if elem is not None and elem.text else None
                
                return LibraryMetadata(
                    title=get_text('Title') or os.path.splitext(os.path.basename(file_path))[0],
                    series=get_text('Series'),
                    author=get_text('Writer') or get_text('Author'),
                    publisher=get_text('Publisher'),
                    genre=get_text('Genre'),
                    description=get_text('Summary') or get_text('Description'),
                    volume=get_text('Volume'),
                    chapters=int(get_text('Chapter') or 0) if get_text('Chapter') else None,
                    pages=int(get_text('PageCount') or 0) if get_text('PageCount') else None,
                    year=int(get_text('Year') or 0) if get_text('Year') else None,
                    language=get_text('Language')
                )
    except Exception as e:
        logger.warning(f"Impossible d'extraire les métadonnées de {file_path}: {e}")
        return None

def format_size(size_bytes: int) -> str:
    """Formate une taille en octets en chaîne lisible."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

# ==========================================================================
#  Endpoints
# ==========================================================================

@router.get(
    "/",
    response_model=LibraryListResponse,
    summary="Liste les éléments de la bibliothèque"
)
async def list_library(
    search: Optional[str] = Query(None, description="Recherche par titre"),
    genre: Optional[str] = Query(None, description="Filtrer par genre"),
    author: Optional[str] = Query(None, description="Filtrer par auteur"),
    sort_by: str = Query("created_at", description="Champ de tri (title, created_at, size)"),
    sort_order: str = Query("desc", description="Ordre de tri (asc, desc)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    file_service: FileService = Depends(get_file_service),
    current_user: Optional[User] = Depends(get_current_user)
) -> LibraryListResponse:
    """
    Récupère la liste des fichiers CBZ dans la bibliothèque.
    Supporte la recherche, les filtres et la pagination.
    """
    download_path = settings.get_download_path()
    items = []
    try:
        # Lister tous les fichiers .cbz
        for entry in os.listdir(download_path):
            if entry.endswith(".cbz"):
                file_path = download_path / entry
                if file_path.is_file():
                    stat = file_path.stat()
                    # Extraire le titre (sans extension)
                    title = os.path.splitext(entry)[0]
                    metadata = extract_metadata_from_cbz(str(file_path))
                    # Utiliser les métadonnées pour enrichir
                    if metadata and metadata.title:
                        title = metadata.title
                    item = LibraryItem(
                        id=entry,
                        filename=entry,
                        title=title,
                        size_bytes=stat.st_size,
                        size_formatted=format_size(stat.st_size),
                        created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        metadata=metadata
                    )
                    # Appliquer les filtres
                    if search and search.lower() not in item.title.lower():
                        continue
                    if genre and metadata and metadata.genre:
                        if genre.lower() not in metadata.genre.lower():
                            continue
                    if author and metadata and metadata.author:
                        if author.lower() not in metadata.author.lower():
                            continue
                    items.append(item)
        
        # Trier
        if sort_by == "title":
            items.sort(key=lambda x: x.title.lower(), reverse=(sort_order == "desc"))
        elif sort_by == "size":
            items.sort(key=lambda x: x.size_bytes, reverse=(sort_order == "desc"))
        else:  # default created_at
            items.sort(key=lambda x: x.created_at, reverse=(sort_order == "desc"))
        
        total = len(items)
        paginated = items[offset:offset + limit]
        return LibraryListResponse(
            items=paginated,
            total=total,
            offset=offset,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Erreur lors de la liste de la bibliothèque: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de la lecture de la bibliothèque."
        )

@router.get(
    "/{item_id}",
    response_model=LibraryItem,
    summary="Obtenir les détails d'un élément"
)
async def get_library_item(
    item_id: str = Path(..., description="Nom du fichier (ID)"),
    current_user: Optional[User] = Depends(get_current_user)
) -> LibraryItem:
    """
    Récupère les détails d'un élément spécifique de la bibliothèque.
    """
    if ".." in item_id or "/" in item_id or "\\" in item_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID invalide."
        )
    file_path = settings.get_download_path() / item_id
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément non trouvé."
        )
    if not item_id.endswith(".cbz"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'élément doit être un fichier CBZ."
        )
    stat = file_path.stat()
    title = os.path.splitext(item_id)[0]
    metadata = extract_metadata_from_cbz(str(file_path))
    if metadata and metadata.title:
        title = metadata.title
    return LibraryItem(
        id=item_id,
        filename=item_id,
        title=title,
        size_bytes=stat.st_size,
        size_formatted=format_size(stat.st_size),
        created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
        modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        metadata=metadata
    )

@router.delete(
    "/{item_id}",
    response_model=DeleteResponse,
    summary="Supprime un élément de la bibliothèque"
)
async def delete_library_item(
    item_id: str = Path(..., description="Nom du fichier (ID)"),
    current_user: User = Depends(get_current_user)  # Authentification requise
) -> DeleteResponse:
    """
    Supprime définitivement un fichier CBZ de la bibliothèque.
    Nécessite d'être authentifié.
    """
    if ".." in item_id or "/" in item_id or "\\" in item_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID invalide."
        )
    file_path = settings.get_download_path() / item_id
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Élément non trouvé."
        )
    try:
        os.remove(file_path)
        return DeleteResponse(success=True, message=f"L'élément '{item_id}' a été supprimé.")
    except Exception as e:
        logger.error(f"Erreur suppression {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression."
        )

@router.get(
    "/stats",
    response_model=LibraryStats,
    summary="Statistiques de la bibliothèque"
)
async def get_library_stats(
    file_service: FileService = Depends(get_file_service),
    current_user: Optional[User] = Depends(get_current_user)
) -> LibraryStats:
    """
    Retourne des statistiques sur la bibliothèque (nombre d'items, taille totale, genres, auteurs).
    """
    download_path = settings.get_download_path()
    items = []
    total_size = 0
    genres_set = set()
    authors_set = set()
    dates = []
    try:
        for entry in os.listdir(download_path):
            if entry.endswith(".cbz"):
                file_path = download_path / entry
                if file_path.is_file():
                    stat = file_path.stat()
                    size = stat.st_size
                    total_size += size
                    items.append(entry)
                    dates.append(datetime.fromtimestamp(stat.st_ctime))
                    metadata = extract_metadata_from_cbz(str(file_path))
                    if metadata:
                        if metadata.genre:
                            genres_set.update([g.strip() for g in metadata.genre.split(',')])
                        if metadata.author:
                            authors_set.add(metadata.author)
        
        total_items = len(items)
        avg_size = total_size / total_items if total_items > 0 else 0
        oldest = min(dates).isoformat() if dates else None
        newest = max(dates).isoformat() if dates else None
        
        return LibraryStats(
            total_items=total_items,
            total_size_bytes=total_size,
            total_size_formatted=format_size(total_size),
            oldest_item=oldest,
            newest_item=newest,
            average_size_bytes=avg_size,
            genres=sorted(genres_set),
            authors=sorted(authors_set)
        )
    except Exception as e:
        logger.error(f"Erreur stats bibliothèque: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du calcul des statistiques."
        )

# ==========================================================================
#  Notes
# ==========================================================================
#  - Les métadonnées sont extraites à la volée depuis ComicInfo.xml.
#    En production, on pourrait les mettre en cache dans une base de données.
#  - L'authentification est optionnelle pour la lecture, mais obligatoire
#    pour la suppression.
#  - La fonction `extract_metadata_from_cbz` gère le namespace ComicInfo.
