# ==========================================================================
#  NexusDL 2.0 - Provider nHentai (NSFW)
#  Fichier : backend/app/providers/nsfw/nhentai.py
# ==========================================================================

"""
Provider pour nHentai (https://nhentai.net).
Site de doujinshi et hentai en anglais/japonais avec une API non officielle.

Caractéristiques :
- API REST non officielle : https://nhentai.net/api/
- Images hébergées sur i.nhentai.net avec des numéros de pages
- Support des tags, parodies, personnages, etc.
- Contenu NSFW uniquement
- Rate limiting respectueux (pas de documentation officielle, on limite à 1 requête par seconde)
- Recherche via l'API /api/galleries/search

Structure des URLs :
- Gallery : https://nhentai.net/g/{id}/
- Page d'image : https://i.nhentai.net/galleries/{media_id}/{page}.jpg

Ce provider utilise des requêtes HTTP classiques (aiohttp) pour l'API et le scraping
lorsque l'API ne suffit pas (ex: pour les métadonnées détaillées).
"""

import logging
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, urljoin
from datetime import datetime

from app.providers.base import BaseProvider
from app.providers.registry import register_provider
from app.core.exceptions import ProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)


@register_provider
class NHentaiProvider(BaseProvider):
    """
    Provider nHentai utilisant l'API non officielle et le scraping.
    """

    # ==========================================================================
    #  Métadonnées du provider
    # ==========================================================================

    id = "nhentai"
    name = "nHentai"
    base_url = "https://nhentai.net"
    supported_languages = ["en", "ja"]  # Contenu multilingue
    nsfw = True
    version = "1.0.0"
    description = "nHentai - Doujinshi et hentai (NSFW)"
    enabled = True
    priority = 2  # Priorité moyenne

    # ==========================================================================
    #  Configuration de l'API
    # ==========================================================================

    API_BASE = "https://nhentai.net/api"
    CDN_BASE = "https://i.nhentai.net"
    # Limite de requêtes (1/seconde pour éviter le blocage)
    RATE_LIMIT = 1
    _last_request_time: Optional[datetime] = None

    # ==========================================================================
    #  Méthodes de gestion de l'API
    # ==========================================================================

    async def _rate_limit_wait(self):
        """Gère le rate limiting (1 requête par seconde)."""
        if self._last_request_time is not None:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            min_interval = 1.0 / self.RATE_LIMIT
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        self._last_request_time = datetime.now()

    async def _make_api_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Effectue une requête vers l'API nHentai.
        """
        url = f"{self.API_BASE}{endpoint}"
        if not url.startswith("http"):
            url = f"https:{url}" if url.startswith("//") else url

        headers = {
            "User-Agent": f"NexusDL/{settings.APP_VERSION} (compatible; nHentai-API)",
            "Accept": "application/json"
        }

        retries = 0
        while retries < max_retries:
            try:
                await self._rate_limit_wait()
                async with self._get_session() as session:
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 404:
                            return {"error": "not_found"}
                        elif response.status >= 500:
                            logger.warning(f"Erreur serveur nHentai: {response.status}, tentative {retries+1}")
                            retries += 1
                            await asyncio.sleep(2 ** retries)
                            continue
                        else:
                            error_text = await response.text()
                            raise ProviderError(f"Erreur API nHentai: {response.status} - {error_text[:200]}", provider_id=self.id)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Erreur réseau nHentai: {e}, tentative {retries+1}")
                retries += 1
                await asyncio.sleep(2 ** retries)
                continue
            except Exception as e:
                logger.error(f"Erreur inattendue nHentai: {e}")
                raise ProviderError(f"Erreur lors de la requête: {e}", provider_id=self.id)

        raise ProviderError(f"Échec après {max_retries} tentatives: {endpoint}", provider_id=self.id)

    # ==========================================================================
    #  Méthodes principales
    # ==========================================================================

    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyse une URL nHentai (gallery) et retourne les informations et la liste des pages.
        """
        try:
            # Nettoyer l'URL
            url = self._clean_url(url)

            # Extraire l'ID de la galerie
            gallery_id = self._extract_id_from_url(url)
            if not gallery_id:
                raise ProviderError("URL nHentai invalide: ID de galerie non trouvé", provider_id=self.id)

            # Récupérer les informations via l'API
            data = await self._make_api_request(f"/gallery/{gallery_id}")
            if "error" in data:
                raise ProviderError(f"Galerie non trouvée: {gallery_id}", provider_id=self.id)

            # Extraire les métadonnées
            title = self._extract_title(data)
            author = self._extract_author(data)
            tags = self._extract_tags(data)
            description = self._extract_description(data)
            cover_url = self._extract_cover_url(data)
            pages_count = data.get("num_pages", 0)

            # Générer la liste des pages
            media_id = data.get("media_id")
            if not media_id:
                raise ProviderError("Media ID manquant pour la galerie", provider_id=self.id)

            pages = self._generate_pages(media_id, pages_count)

            return {
                "title": title,
                "url": url,
                "provider_id": self.id,
                "chapters": [
                    {
                        "id": gallery_id,
                        "title": title,
                        "number": 1,  # Une seule "chapter" pour les doujinshi
                        "pages": pages_count,
                        "images": pages,  # Optionnel, mais on peut les inclure
                        "is_available": True
                    }
                ],
                "author": author,
                "description": description,
                "cover_url": cover_url,
                "genre": tags,
                "status": "completed",  # Les doujinshi sont généralement complets
                "year": None,
                "language": "en",  # Défaut
                "nsfw": self.nsfw,
                "total_chapters": 1,
                # Métadonnées supplémentaires
                "media_id": media_id,
                "tags": tags,
                "pages_count": pages_count,
                "upload_date": data.get("upload_date")
            }

        except Exception as e:
            logger.error(f"Erreur analyse nHentai pour {url}: {e}")
            raise ProviderError(f"Impossible d'analyser l'URL: {e}", provider_id=self.id)

    async def get_chapter_images(self, chapter_id: str) -> List[str]:
        """
        Récupère les URLs des images d'une galerie (chapter_id = gallery_id).
        """
        try:
            # Si chapter_id est une URL, extraire l'ID
            if chapter_id.startswith("http"):
                gallery_id = self._extract_id_from_url(chapter_id)
                if not gallery_id:
                    raise ProviderError("ID de galerie invalide", provider_id=self.id)
            else:
                gallery_id = chapter_id

            # Récupérer les informations de la galerie
            data = await self._make_api_request(f"/gallery/{gallery_id}")
            if "error" in data:
                raise ProviderError(f"Galerie non trouvée: {gallery_id}", provider_id=self.id)

            media_id = data.get("media_id")
            pages_count = data.get("num_pages", 0)
            if not media_id:
                raise ProviderError("Media ID manquant", provider_id=self.id)

            # Générer les URLs des images
            images = self._generate_pages(media_id, pages_count)
            return images

        except Exception as e:
            logger.error(f"Erreur récupération images nHentai pour {chapter_id}: {e}")
            raise ProviderError(f"Impossible de récupérer les images: {e}", provider_id=self.id)

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche des galeries sur nHentai via l'API /galleries/search.
        Supporte les tags (ex: "tag:loli").
        """
        try:
            params = {
                "q": query,
                "page": 1,
                "per_page": min(limit, 25)  # L'API limite à 25 par page
            }
            data = await self._make_api_request("/galleries/search", params=params)
            if "error" in data:
                return []

            results = []
            for item in data.get("result", [])[:limit]:
                gallery_id = item.get("id")
                if not gallery_id:
                    continue
                title = self._extract_title(item)
                cover_url = self._extract_cover_url(item)
                results.append({
                    "series_id": str(gallery_id),
                    "title": title,
                    "url": f"{self.base_url}/g/{gallery_id}/",
                    "cover_url": cover_url,
                    "author": self._extract_author(item),
                    "provider_id": self.id,
                    "provider_name": self.name,
                    "nsfw": True,
                    "language": "en",
                    "genre": self._extract_tags(item),
                    "status": "completed"
                })

            logger.debug(f"Recherche nHentai '{query}': {len(results)} résultats")
            return results

        except Exception as e:
            logger.error(f"Erreur recherche nHentai pour '{query}': {e}")
            return []

    # ==========================================================================
    #  Méthodes d'extraction des données
    # ==========================================================================

    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Extrait l'ID de galerie depuis une URL nHentai."""
        # Pattern: /g/([0-9]+)/
        match = re.search(r'/g/([0-9]+)/?', url)
        if match:
            return match.group(1)
        # Si c'est un lien direct https://nhentai.net/g/123456/
        return None

    def _extract_title(self, data: Dict[str, Any]) -> str:
        """Extrait le titre de la galerie."""
        # Le titre peut être dans 'title' sous forme de dict avec 'english', 'japanese', 'pretty'
        title_data = data.get("title", {})
        # Priorité: english puis japanese
        for lang in ["english", "pretty", "japanese"]:
            if title_data.get(lang):
                return title_data[lang]
        # Fallback: utiliser le premier champ non vide
        for value in title_data.values():
            if value:
                return value
        return f"Galerie {data.get('id', 'inconnue')}"

    def _extract_author(self, data: Dict[str, Any]) -> str:
        """Extrait le nom de l'auteur depuis les tags."""
        tags = data.get("tags", [])
        for tag in tags:
            if tag.get("type") == "artist":
                return tag.get("name", "")
        return "Inconnu"

    def _extract_tags(self, data: Dict[str, Any]) -> List[str]:
        """Extrait la liste des tags (par type)."""
        tags = data.get("tags", [])
        tag_names = []
        for tag in tags:
            name = tag.get("name")
            if name:
                tag_names.append(name)
        return tag_names

    def _extract_description(self, data: Dict[str, Any]) -> str:
        """Génère une description à partir des tags et des métadonnées."""
        tags = data.get("tags", [])
        # Regrouper par type
        parts = []
        tag_types = {
            "parody": "Parodies",
            "character": "Personnages",
            "artist": "Artistes",
            "group": "Groupes",
            "language": "Langues",
            "category": "Catégories",
            "tag": "Tags"
        }
        for type_name, label in tag_types.items():
            items = [t.get("name") for t in tags if t.get("type") == type_name and t.get("name")]
            if items:
                parts.append(f"{label}: {', '.join(items)}")
        return "\n".join(parts) if parts else ""

    def _extract_cover_url(self, data: Dict[str, Any]) -> Optional[str]:
        """Extrait l'URL de la couverture (utilisant l'image de la première page)."""
        media_id = data.get("media_id")
        if media_id:
            # La couverture est généralement la première page
            return f"{self.CDN_BASE}/galleries/{media_id}/1.jpg"
        return None

    def _generate_pages(self, media_id: str, page_count: int) -> List[str]:
        """
        Génère les URLs des pages d'une galerie.
        Les images sont au format: https://i.nhentai.net/galleries/{media_id}/{page}.jpg
        Certaines pages peuvent être en .png ou .webp, mais la convention est .jpg.
        """
        pages = []
        for i in range(1, page_count + 1):
            pages.append(f"{self.CDN_BASE}/galleries/{media_id}/{i}.jpg")
        return pages

    def _clean_url(self, url: str) -> str:
        """Nettoie une URL nHentai."""
        # Supprimer les paramètres de tracking
        parsed = urlparse(url)
        # Garder le chemin principal
        cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return cleaned

    # ==========================================================================
    #  Gestion des erreurs spécifiques
    # ==========================================================================

    # Note: L'API nHentai peut renvoyer des erreurs 429 si trop de requêtes.
    # Le rate limiting est appliqué pour éviter cela.
    # Si l'API est indisponible, on pourrait utiliser le scraping, mais nous ne le faisons pas ici.

    # ==========================================================================
    #  Nettoyage
    # ==========================================================================

    # Pas de ressources spécifiques à fermer (pas de Playwright)
