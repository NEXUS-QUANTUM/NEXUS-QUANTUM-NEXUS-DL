# ==========================================================================
#  NexusDL 2.0 - Browse Endpoints
#  Fichier : backend/app/api/v1/endpoints/browse.py
# ==========================================================================

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.registry import ProviderRegistry
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.deps import get_provider_registry
from app.models.user import User
from app.schemas.provider import ProviderInfo, SeriesInfo, ChapterInfo, SearchResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/browse", tags=["Browse"])

# ==========================================================================
#  Schémas (à déplacer dans schemas/ si nécessaire, mais on les définit ici)
# ==========================================================================

class ProviderInfoResponse(ProviderInfo):
    """Informations sur un provider."""
    pass

class SeriesResponse(SeriesInfo):
    """Informations sur une série."""
    pass

class ChapterResponse(ChapterInfo):
    """Informations sur un chapitre."""
    pass

class SearchResponse(BaseModel):
    """Résultat de recherche."""
    query: str
    total: int
    results: List[SeriesResponse]
    provider: str

# ==========================================================================
#  Endpoints
# ==========================================================================

@router.get(
    "/providers",
    response_model=List[ProviderInfoResponse],
    summary="Liste tous les providers disponibles"
)
async def list_providers(
    include_nsfw: bool = Query(False, description="Inclure les providers NSFW"),
    registry: ProviderRegistry = Depends(get_provider_registry),
    current_user: Optional[User] = Depends(get_current_user)
) -> List[ProviderInfoResponse]:
    """
    Récupère la liste de tous les providers enregistrés, avec leurs métadonnées.
    Les providers NSFW ne sont inclus que si `include_nsfw` est True.
    """
    providers = registry.get_all_providers()
    result = []
    for provider_id, provider in providers.items():
        if provider.nsfw and not include_nsfw:
            continue
        # Vérifier si le provider est activé (peut avoir un flag enabled)
        if hasattr(provider, 'enabled') and not provider.enabled:
            continue
        result.append(ProviderInfoResponse(
            id=provider_id,
            name=provider.name,
            base_url=provider.base_url,
            languages=provider.supported_languages,
            nsfw=provider.nsfw,
            version=getattr(provider, 'version', '1.0.0'),
            description=getattr(provider, 'description', '')
        ))
    return result

@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Recherche une série sur un provider donné"
)
async def search_series(
    query: str = Query(..., min_length=1, description="Terme de recherche"),
    provider_id: Optional[str] = Query(None, description="ID du provider (si non spécifié, recherche sur tous)"),
    limit: int = Query(20, ge=1, le=100, description="Nombre maximal de résultats"),
    registry: ProviderRegistry = Depends(get_provider_registry),
    current_user: Optional[User] = Depends(get_current_user)
) -> SearchResponse:
    """
    Effectue une recherche de séries sur un provider spécifique ou sur tous les providers.
    Si `provider_id` est omis, la recherche est exécutée sur tous les providers disponibles.
    """
    try:
        results = []
        providers_to_search = []
        if provider_id:
            provider = registry.get_provider(provider_id)
            if not provider:
                raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' non trouvé")
            providers_to_search = [(provider_id, provider)]
        else:
            # Recherche sur tous les providers actifs
            providers_to_search = registry.get_all_providers().items()
            # Filtrer les NSFW si non demandé (mais on peut laisser l'utilisateur choisir)
            # On pourrait ajouter un paramètre include_nsfw, mais on se contente de tout inclure
            # car le filtre est fait côté frontend.
            # On pourrait aussi limiter les providers à ceux qui supportent la recherche.
        
        for pid, prov in providers_to_search:
            # Vérifier si le provider a une méthode search
            if hasattr(prov, 'search'):
                try:
                    items = await prov.search(query, limit=limit)
                    for item in items:
                        # Ajouter l'ID du provider pour référence
                        item.provider_id = pid
                        results.append(item)
                except Exception as e:
                    logger.warning(f"Erreur recherche sur {pid}: {e}")
            else:
                logger.debug(f"Provider {pid} ne supporte pas la recherche")
        
        # Trier par pertinence (on peut laisser l'ordre actuel)
        # Limiter le nombre total
        results = results[:limit]
        return SearchResponse(
            query=query,
            total=len(results),
            results=results,
            provider=provider_id or "all"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors de la recherche")

@router.get(
    "/series/{provider_id}/{series_id}",
    response_model=SeriesResponse,
    summary="Obtenir les détails d'une série"
)
async def get_series_details(
    provider_id: str = Path(..., description="ID du provider"),
    series_id: str = Path(..., description="ID de la série (URL ou identifiant)"),
    registry: ProviderRegistry = Depends(get_provider_registry),
    current_user: Optional[User] = Depends(get_current_user)
) -> SeriesResponse:
    """
    Récupère les informations détaillées d'une série (titre, auteur, description, etc.)
    et la liste des chapitres disponibles.
    """
    provider = registry.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' non trouvé")
    
    # Vérifier si le provider supporte l'analyse de série
    if not hasattr(provider, 'get_series_info'):
        raise HTTPException(
            status_code=501,
            detail=f"Le provider '{provider_id}' ne supporte pas cette opération."
        )
    
    try:
        series_info = await provider.get_series_info(series_id)
        if not series_info:
            raise HTTPException(status_code=404, detail="Série non trouvée")
        return SeriesResponse(**series_info)
    except ProviderError as e:
        logger.error(f"Erreur provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

@router.get(
    "/chapters/{provider_id}/{series_id}",
    response_model=List[ChapterResponse],
    summary="Liste les chapitres d'une série"
)
async def list_chapters(
    provider_id: str = Path(..., description="ID du provider"),
    series_id: str = Path(..., description="ID de la série"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    limit: int = Query(50, ge=1, le=200, description="Nombre de chapitres à retourner"),
    registry: ProviderRegistry = Depends(get_provider_registry),
    current_user: Optional[User] = Depends(get_current_user)
) -> List[ChapterResponse]:
    """
    Récupère la liste des chapitres d'une série donnée, avec pagination.
    """
    provider = registry.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' non trouvé")
    
    if not hasattr(provider, 'get_chapters'):
        raise HTTPException(
            status_code=501,
            detail=f"Le provider '{provider_id}' ne supporte pas cette opération."
        )
    
    try:
        chapters = await provider.get_chapters(series_id)
        # Pagination
        total = len(chapters)
        start = offset
        end = start + limit
        paginated = chapters[start:end]
        # Ajouter des métadonnées de pagination si nécessaire
        for ch in paginated:
            ch.total_chapters = total
        return [ChapterResponse(**ch) for ch in paginated]
    except ProviderError as e:
        logger.error(f"Erreur provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

@router.get(
    "/chapter-images/{provider_id}/{chapter_id}",
    response_model=List[str],
    summary="Récupère les URLs des images d'un chapitre"
)
async def get_chapter_images(
    provider_id: str = Path(..., description="ID du provider"),
    chapter_id: str = Path(..., description="ID du chapitre"),
    registry: ProviderRegistry = Depends(get_provider_registry),
    current_user: Optional[User] = Depends(get_current_user)
) -> List[str]:
    """
    Retourne la liste des URLs des images d'un chapitre spécifique.
    Cette opération peut être lourde, elle est utilisée principalement pour l'aperçu.
    """
    provider = registry.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' non trouvé")
    
    if not hasattr(provider, 'get_chapter_images'):
        raise HTTPException(
            status_code=501,
            detail=f"Le provider '{provider_id}' ne supporte pas cette opération."
        )
    
    try:
        images = await provider.get_chapter_images(chapter_id)
        if not images:
            raise HTTPException(status_code=404, detail="Aucune image trouvée pour ce chapitre")
        return images
    except ProviderError as e:
        logger.error(f"Erreur provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

# ==========================================================================
#  Notes
# ==========================================================================
#  - Les providers doivent implémenter les méthodes `search`, `get_series_info`,
#    `get_chapters`, `get_chapter_images` pour supporter ces endpoints.
#  - Le registre des providers est injecté via la dépendance `get_provider_registry`.
#  - L'authentification est optionnelle (on peut naviguer sans être connecté),
#    mais on peut ajouter des restrictions si nécessaire.
#  - Les schémas `ProviderInfo`, `SeriesInfo`, `ChapterInfo` sont définis dans
#    `app/schemas/provider.py` (à créer).
