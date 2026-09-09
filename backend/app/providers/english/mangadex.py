# ==========================================================================
#  NexusDL 2.0 - Provider MangaDex (API Officielle)
#  Fichier : backend/app/providers/english/mangadex.py
# ==========================================================================

"""
Provider pour MangaDex (https://mangadex.org) utilisant l'API REST officielle v5.

MangaDex est une bibliothèque de mangas multi-langues. Ce provider utilise
l'API publique pour récupérer les informations des séries, des chapitres
et des images, sans nécessiter de scraping HTML.

Points clés :
- API REST v5 : api.mangadex.org
- CDN pour les images : uploads.mangadex.org
- Support des langues, des tags, des contenus SFW/NSFW
- Rate limiting : 5 requêtes par seconde (géré avec un throttle)
"""

import logging
import asyncio
import re
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, quote
from datetime import datetime, timedelta

from app.providers.base import BaseProvider
from app.providers.registry import register_provider
from app.core.exceptions import ProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)


@register_provider
class MangaDexProvider(BaseProvider):
    """
    Provider MangaDex utilisant l'API REST officielle.
    """

    # ==========================================================================
    #  Métadonnées du provider
    # ==========================================================================

    id = "mangadex"
    name = "MangaDex"
    base_url = "https://mangadex.org"
    supported_languages = ["en", "fr", "es", "pt", "de", "it", "ru", "ja", "ko", "zh"]
    nsfw = True  # Supporte les contenus SFW et NSFW (configurable)
    version = "2.0.0"
    description = "MangaDex - Plateforme de mangas multi-langues (API officielle)"
    enabled = True
    priority = 8  # Priorité très élevée

    # ==========================================================================
    #  Configuration de l'API
    # ==========================================================================

    API_BASE = "https://api.mangadex.org"
    CDN_BASE = "https://uploads.mangadex.org"
    # Limite de requêtes API (5 par seconde selon la documentation)
    RATE_LIMIT = 5
    _last_request_time: Optional[datetime] = None
    _request_semaphore: Optional[asyncio.Semaphore] = None

    # Filtres par défaut pour les chapitres
    DEFAULT_LANGUAGE = "en"  # Langue par défaut
    MAX_CHAPTERS = 500  # Nombre maximum de chapitres à récupérer
    CHAPTER_LIMIT_PER_REQUEST = 100  # Limite par requête API

    # Contenu autorisé (par défaut tout sauf pornographique lourd)
    ALLOWED_CONTENT_RATINGS = ["safe", "suggestive", "erotica"]
    # Pour du NSFW complet, ajouter "pornographic"

    # ==========================================================================
    #  Méthodes de gestion de l'API
    # ==========================================================================

    def __init__(self):
        super().__init__()
        # Initialiser le sémaphore pour le rate limiting
        if self._request_semaphore is None:
            self._request_semaphore = asyncio.Semaphore(1)  # On utilisera un timer pour le rate limit

    async def _rate_limit_wait(self):
        """Gère le rate limiting en attendant le temps nécessaire entre les requêtes."""
        if self._last_request_time is not None:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            min_interval = 1.0 / self.RATE_LIMIT
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        self._last_request_time = datetime.now()

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Effectue une requête vers l'API MangaDex avec gestion du rate limiting et des retries.
        """
        url = f"{self.API_BASE}{endpoint}"
        if not url.startswith("https://"):
            url = url.replace("http://", "https://")

        # Ajouter les paramètres communs si nécessaire
        if params is None:
            params = {}

        # Ajouter le header user-agent
        headers = {
            "User-Agent": f"NexusDL/{settings.APP_VERSION} (compatible; MangaDex-API)",
            "Accept": "application/json"
        }

        # Ajouter un token si on a une session (optionnel)
        # if self._session_token:
        #     headers["Authorization"] = f"Bearer {self._session_token}"

        retries = 0
        while retries < max_retries:
            try:
                # Appliquer le rate limiting
                await self._rate_limit_wait()

                async with self._get_session() as session:
                    if method.upper() == "GET":
                        async with session.get(url, params=params, headers=headers) as response:
                            return await self._handle_response(response, endpoint)
                    elif method.upper() == "POST":
                        async with session.post(url, params=params, json=json_data, headers=headers) as response:
                            return await self._handle_response(response, endpoint)
                    else:
                        raise ValueError(f"Méthode HTTP non supportée: {method}")

            except aiohttp.ClientResponseError as e:
                if e.status == 429:  # Too Many Requests
                    retry_after = e.headers.get("Retry-After", "5")
                    try:
                        wait_time = int(retry_after)
                    except ValueError:
                        wait_time = 5
                    logger.warning(f"Rate limit MangaDex: attente {wait_time}s")
                    await asyncio.sleep(wait_time + 1)
                    retries += 1
                    continue
                elif e.status == 404:
                    return {"error": "not_found", "message": "Ressource non trouvée"}
                elif e.status >= 500:
                    logger.error(f"Erreur serveur MangaDex: {e.status}")
                    retries += 1
                    await asyncio.sleep(2 ** retries)
                    continue
                else:
                    raise ProviderError(f"Erreur API MangaDex: {e.status} - {e.message}", provider_id=self.id)

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Erreur réseau MangaDex: {e}, tentative {retries+1}/{max_retries}")
                retries += 1
                await asyncio.sleep(2 ** retries)
                continue

            except Exception as e:
                logger.error(f"Erreur inattendue MangaDex: {e}")
                raise ProviderError(f"Erreur lors de la requête: {e}", provider_id=self.id)

        raise ProviderError(f"Échec après {max_retries} tentatives: {endpoint}", provider_id=self.id)

    async def _handle_response(self, response: aiohttp.ClientResponse, endpoint: str) -> Dict[str, Any]:
        """
        Gère la réponse de l'API, vérifie les erreurs et parse le JSON.
        """
        if response.status == 204:
            return {}

        try:
            data = await response.json()
        except aiohttp.ContentTypeError:
            text = await response.text()
            logger.error(f"Réponse non-JSON de MangaDex: {text[:200]}")
            raise ProviderError(f"Réponse invalide de l'API pour {endpoint}", provider_id=self.id)

        if response.status >= 400:
            error_message = data.get("errors", [{}])[0].get("detail", "Erreur inconnue")
            raise ProviderError(f"Erreur API: {error_message} (status {response.status})", provider_id=self.id)

        return data

    # ==========================================================================
    #  Méthodes principales du provider
    # ==========================================================================

    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyse une URL MangaDex pour extraire les informations de la série et des chapitres.
        Gère les URLs de série (/title/...) et les URLs de chapitres (/chapter/...).
        """
        try:
            # Nettoyer l'URL
            url = self._clean_url(url)

            # Extraire l'ID de la série ou du chapitre
            manga_id = self._extract_id_from_url(url, entity_type="manga")
            chapter_id = self._extract_id_from_url(url, entity_type="chapter")

            if manga_id:
                return await self._analyze_manga(manga_id)
            elif chapter_id:
                # Récupérer les infos du chapitre pour remonter à la série
                chapter_info = await self._get_chapter_info(chapter_id)
                if chapter_info and chapter_info.get("manga_id"):
                    return await self._analyze_manga(chapter_info["manga_id"])
                else:
                    raise ProviderError("Impossible de trouver la série associée au chapitre", provider_id=self.id)
            else:
                raise ProviderError("URL MangaDex invalide: ID de série ou de chapitre non trouvé", provider_id=self.id)

        except Exception as e:
            logger.error(f"Erreur analyse MangaDex pour {url}: {e}")
            raise ProviderError(f"Impossible d'analyser l'URL: {e}", provider_id=self.id)

    async def _analyze_manga(self, manga_id: str) -> Dict[str, Any]:
        """
        Analyse une série MangaDex par son ID.
        Retourne les informations complètes avec les chapitres.
        """
        # 1. Récupérer les informations de la série
        manga_data = await self._get_manga_info(manga_id)
        if not manga_data:
            raise ProviderError(f"Série non trouvée: {manga_id}", provider_id=self.id)

        # 2. Extraire les métadonnées
        title = self._extract_title(manga_data)
        author = self._extract_author(manga_data)
        description = self._extract_description(manga_data)
        cover_url = self._extract_cover_url(manga_data)
        genres = self._extract_genres(manga_data)
        status = self._extract_status(manga_data)
        year = self._extract_year(manga_data)

        # 3. Récupérer les chapitres
        chapters = await self._get_chapters_for_manga(manga_id)

        return {
            "title": title,
            "url": f"{self.base_url}/title/{manga_id}",
            "provider_id": self.id,
            "chapters": chapters,
            "author": author,
            "description": description,
            "cover_url": cover_url,
            "genre": genres,
            "status": status,
            "year": year,
            "language": self.DEFAULT_LANGUAGE,
            "nsfw": self.nsfw,
            "total_chapters": len(chapters)
        }

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche des séries sur MangaDex via l'API.
        """
        try:
            params = {
                "title": query,
                "limit": min(limit, 100),
                "offset": 0,
                "includes[]": ["cover_art", "author", "artist"],
                "availableTranslatedLanguage[]": self.DEFAULT_LANGUAGE,
                "contentRating[]": self.ALLOWED_CONTENT_RATINGS,
            }

            data = await self._make_request("/manga", params=params)
            results = []

            for item in data.get("data", []):
                attributes = item.get("attributes", {})
                # Titre
                title_dict = attributes.get("title", {})
                title = title_dict.get("en") or title_dict.get("fr") or list(title_dict.values())[0] if title_dict else "Sans titre"

                # URL de la série
                series_id = item.get("id")
                series_url = f"{self.base_url}/title/{series_id}"

                # Couverture
                cover_url = None
                relationships = item.get("relationships", [])
                for rel in relationships:
                    if rel.get("type") == "cover_art":
                        cover_filename = rel.get("attributes", {}).get("fileName")
                        if cover_filename:
                            cover_url = f"{self.CDN_BASE}/covers/{series_id}/{cover_filename}"

                # Auteur
                author = "Inconnu"
                for rel in relationships:
                    if rel.get("type") == "author":
                        author_name = rel.get("attributes", {}).get("name")
                        if author_name:
                            author = author_name
                            break

                results.append({
                    "series_id": series_id,
                    "title": title,
                    "url": series_url,
                    "cover_url": cover_url,
                    "author": author,
                    "provider_id": self.id,
                    "provider_name": self.name,
                    "genre": attributes.get("tags", []),
                    "status": attributes.get("status", "unknown"),
                    "nsfw": "pornographic" in [tag.get("id") for tag in attributes.get("tags", [])],
                    "language": "en"
                })

            logger.debug(f"Recherche MangaDex '{query}': {len(results)} résultats")
            return results

        except Exception as e:
            logger.error(f"Erreur recherche MangaDex pour '{query}': {e}")
            return []  # Silencieux pour la recherche

    async def get_chapter_images(self, chapter_id: str) -> List[str]:
        """
        Récupère les URLs des images d'un chapitre via l'API At-Home de MangaDex.
        """
        try:
            # 1. Récupérer le serveur et la liste des fichiers
            data = await self._make_request(f"/at-home/server/{chapter_id}")

            if "error" in data:
                logger.warning(f"Erreur At-Home pour {chapter_id}: {data.get('error')}")
                # Fallback: essayer /chapter/{id} pour voir si le chapitre existe
                await self._get_chapter_info(chapter_id)
                raise ProviderError(f"Impossible de récupérer les images: {data.get('error')}", provider_id=self.id)

            base_url_cdn = data.get("baseUrl")
            chapter_data = data.get("chapter", {})
            # Le chapitre peut avoir des images dans 'data' et 'dataSaver'
            # On prend 'data' (haute résolution) par défaut
            image_files = chapter_data.get("data", [])
            if not image_files:
                # Fallback sur dataSaver
                image_files = chapter_data.get("dataSaver", [])

            if not image_files:
                logger.warning(f"Aucune image trouvée pour le chapitre {chapter_id}")
                return []

            # Construire les URLs complètes
            # Format: {base_url}/data/{hash}/{filename}
            hash_value = chapter_data.get("hash")
            if not hash_value or not base_url_cdn:
                raise ProviderError("Données At-Home incomplètes", provider_id=self.id)

            images = [f"{base_url_cdn}/data/{hash_value}/{filename}" for filename in image_files]
            logger.debug(f"Récupéré {len(images)} images pour le chapitre {chapter_id}")
            return images

        except Exception as e:
            logger.error(f"Erreur récupération images MangaDex pour {chapter_id}: {e}")
            raise ProviderError(f"Impossible de récupérer les images: {e}", provider_id=self.id)

    # ==========================================================================
    #  Méthodes internes de l'API
    # ==========================================================================

    async def _get_manga_info(self, manga_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'une série par son ID."""
        try:
            params = {
                "includes[]": ["cover_art", "author", "artist"],
                "contentRating[]": self.ALLOWED_CONTENT_RATINGS,
            }
            data = await self._make_request(f"/manga/{manga_id}", params=params)
            return data.get("data")
        except ProviderError as e:
            logger.error(f"Erreur récupération manga {manga_id}: {e}")
            return None

    async def _get_chapter_info(self, chapter_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un chapitre par son ID."""
        try:
            data = await self._make_request(f"/chapter/{chapter_id}")
            chapter_data = data.get("data")
            if not chapter_data:
                return None
            # Extraire le manga_id depuis les relations
            relationships = chapter_data.get("relationships", [])
            manga_id = None
            for rel in relationships:
                if rel.get("type") == "manga":
                    manga_id = rel.get("id")
                    break
            return {
                "id": chapter_data.get("id"),
                "title": chapter_data.get("attributes", {}).get("title", ""),
                "number": chapter_data.get("attributes", {}).get("chapter"),
                "manga_id": manga_id,
                "language": chapter_data.get("attributes", {}).get("translatedLanguage")
            }
        except Exception as e:
            logger.error(f"Erreur récupération chapitre {chapter_id}: {e}")
            return None

    async def _get_chapters_for_manga(
        self,
        manga_id: str,
        language: str = None,
        limit: int = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Récupère la liste des chapitres d'une série.
        """
        if language is None:
            language = self.DEFAULT_LANGUAGE
        if limit is None:
            limit = self.MAX_CHAPTERS

        all_chapters = []
        current_offset = offset

        while len(all_chapters) < limit:
            params = {
                "limit": min(self.CHAPTER_LIMIT_PER_REQUEST, limit - len(all_chapters)),
                "offset": current_offset,
                "translatedLanguage[]": language,
                "order[chapter]": "asc",
                "order[volume]": "asc",
                "includes[]": ["scanlation_group"]
            }

            try:
                data = await self._make_request(f"/manga/{manga_id}/feed", params=params)
                chapters_data = data.get("data", [])
                if not chapters_data:
                    break

                for item in chapters_data:
                    attributes = item.get("attributes", {})
                    chapter_number = attributes.get("chapter")
                    if chapter_number:
                        try:
                            chapter_num = float(chapter_number)
                        except ValueError:
                            chapter_num = 0
                    else:
                        chapter_num = 0

                    all_chapters.append({
                        "id": item.get("id"),
                        "title": attributes.get("title", f"Chapitre {chapter_num}") if attributes.get("title") else f"Chapitre {chapter_num}",
                        "number": chapter_num,
                        "volume": attributes.get("volume"),
                        "pages": attributes.get("pages", 0),
                        "language": attributes.get("translatedLanguage", language),
                        "upload_date": attributes.get("publishAt") or attributes.get("createdAt"),
                        "is_available": True
                    })

                # Vérifier si la pagination est terminée
                total = data.get("total", 0)
                current_offset += len(chapters_data)
                if current_offset >= total or len(chapters_data) < self.CHAPTER_LIMIT_PER_REQUEST:
                    break

            except Exception as e:
                logger.error(f"Erreur récupération chapitres pour {manga_id}: {e}")
                break

        return all_chapters[:limit]

    # ==========================================================================
    #  Méthodes d'extraction des données
    # ==========================================================================

    def _extract_id_from_url(self, url: str, entity_type: str = "manga") -> Optional[str]:
        """Extrait l'UUID d'une série ou d'un chapitre depuis une URL."""
        # Pattern pour les UUID v4
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        # Rechercher dans l'URL
        match = re.search(uuid_pattern, url, re.IGNORECASE)
        if match:
            return match.group(0)

        # Pour les URLs /title/XXXXX (l'ancien format, bien que MangaDex utilise des UUID)
        # On peut essayer de prendre ce qui suit /title/ ou /chapter/
        if entity_type == "manga":
            patterns = [r'/title/([^/?]+)', r'/manga/([^/?]+)']
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
        elif entity_type == "chapter":
            patterns = [r'/chapter/([^/?]+)', r'/read/[^/]+/([^/?]+)']
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
        return None

    def _extract_title(self, manga_data: Dict[str, Any]) -> str:
        """Extrait le titre d'une série."""
        if not manga_data:
            return "Sans titre"
        attributes = manga_data.get("attributes", {})
        titles = attributes.get("title", {})
        # Priorité: anglais, français, puis première autre langue
        for lang in ["en", "fr", "es", "ja", "ko", "zh"]:
            if lang in titles and titles[lang]:
                return titles[lang]
        # Si aucun, prendre la première valeur
        for title in titles.values():
            if title:
                return title
        return "Sans titre"

    def _extract_author(self, manga_data: Dict[str, Any]) -> str:
        """Extrait l'auteur d'une série."""
        relationships = manga_data.get("relationships", [])
        for rel in relationships:
            if rel.get("type") == "author":
                name = rel.get("attributes", {}).get("name")
                if name:
                    return name
        return "Inconnu"

    def _extract_description(self, manga_data: Dict[str, Any]) -> str:
        """Extrait la description d'une série."""
        attributes = manga_data.get("attributes", {})
        desc = attributes.get("description", {})
        for lang in ["en", "fr", "es"]:
            if lang in desc and desc[lang]:
                return desc[lang]
        for d in desc.values():
            if d:
                return d
        return ""

    def _extract_cover_url(self, manga_data: Dict[str, Any]) -> Optional[str]:
        """Extrait l'URL de la couverture d'une série."""
        relationships = manga_data.get("relationships", [])
        manga_id = manga_data.get("id")
        for rel in relationships:
            if rel.get("type") == "cover_art":
                cover_filename = rel.get("attributes", {}).get("fileName")
                if cover_filename and manga_id:
                    return f"{self.CDN_BASE}/covers/{manga_id}/{cover_filename}"
        return None

    def _extract_genres(self, manga_data: Dict[str, Any]) -> List[str]:
        """Extrait les genres/tags d'une série."""
        attributes = manga_data.get("attributes", {})
        tags = attributes.get("tags", [])
        genres = []
        for tag in tags:
            name_dict = tag.get("attributes", {}).get("name", {})
            name = name_dict.get("en") or name_dict.get("fr") or list(name_dict.values())[0] if name_dict else ""
            if name:
                genres.append(name)
        return genres

    def _extract_status(self, manga_data: Dict[str, Any]) -> str:
        """Extrait le statut d'une série."""
        attributes = manga_data.get("attributes", {})
        status = attributes.get("status", "unknown")
        status_map = {
            "ongoing": "ongoing",
            "completed": "completed",
            "hiatus": "hiatus",
            "cancelled": "cancelled",
            "unknown": "unknown"
        }
        return status_map.get(status, "unknown")

    def _extract_year(self, manga_data: Dict[str, Any]) -> Optional[int]:
        """Extrait l'année de publication."""
        attributes = manga_data.get("attributes", {})
        year = attributes.get("year")
        if year:
            try:
                return int(year)
            except (ValueError, TypeError):
                pass
        return None

    def _clean_url(self, url: str) -> str:
        """Nettoie une URL MangaDex."""
        # Supprimer les paramètres de tracking
        parsed = urlparse(url)
        # Garder le chemin principal
        cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return cleaned
