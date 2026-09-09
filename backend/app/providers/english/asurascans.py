# ==========================================================================
#  NexusDL 2.0 - Provider Asura Scans (English)
#  Fichier : backend/app/providers/english/asurascans.py
# ==========================================================================

"""
Provider pour Asura Scans (https://asurascans.com).
Site de scan en anglais utilisant le thème Madara avec quelques particularités.

Ce provider gère :
- L'analyse des séries et des chapitres
- La récupération des images avec nettoyage des URLs
- La gestion des URLs de chapitres individuels
- L'extraction des métadonnées (auteur, genres, statut, etc.)
"""

import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup

from app.providers.themes.madara import MadaraProvider
from app.providers.registry import register_provider
from app.core.exceptions import ProviderError

logger = logging.getLogger(__name__)


@register_provider
class AsuraScansProvider(MadaraProvider):
    """
    Provider pour Asura Scans.
    Hérite de MadaraProvider et surcharge certaines méthodes pour s'adapter
    aux spécificités du site.
    """

    # ==========================================================================
    #  Métadonnées du provider
    # ==========================================================================

    id = "asurascans"
    name = "Asura Scans"
    base_url = "https://asurascans.com"
    supported_languages = ["en"]
    nsfw = False
    version = "2.0.0"
    description = "Asura Scans - Site de scan en anglais (manhwa, manga, webtoon)"
    enabled = True
    priority = 5  # Priorité élevée car site très utilisé

    # ==========================================================================
    #  Sélecteurs CSS personnalisés (adaptés à Asura Scans)
    # ==========================================================================

    selectors = {
        # Informations de la série
        "series_title": "h1.entry-title, .post-title, .page-title, .series-title",
        "series_author": ".author-content a, .series-author a, .author a, .meta-author a",
        "series_description": ".description-summary p, .entry-content p, .summary__content p, .series-description p",
        "series_cover": ".thumb img, .series-thumb img, .wp-post-image, .attachment-post-thumbnail",
        "series_genres": ".genres-content a, .meta-genres a, .series-genres a",
        "series_status": ".status-content a, .series-status, .meta-status a",
        "series_release_year": ".release-content, .meta-year, .series-year",

        # Chapitres
        "chapters_list": ".chapters-list .wp-manga-chapter, .wp-manga-chapter, .chapter-list .chapter-item, .list-chapters .chapter-item",
        "chapter_title": "a",
        "chapter_link": "a",
        "chapter_number": "a .chapter-number, .chapter-number, .chapter-title .chapternum, .chapter .chapternum",

        # Images du chapitre
        "image_container": ".reading-content .page-break img, .reading-content img, .chapter-content img, .page-content img",
        "image_selector": "img",

        # Pagination
        "next_page": ".nav-links .next, .next-page, .pagination .next",
    }

    # ==========================================================================
    #  Méthodes surchargées
    # ==========================================================================

    def __init__(self):
        super().__init__()
        # S'assurer que les sélecteurs sont fusionnés avec ceux du parent
        # (MadaraProvider a déjà des sélecteurs par défaut, on les surcharge partiellement)
        # La fusion est déjà gérée par le constructeur de MadaraProvider via update()
        pass

    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyse une URL et retourne les informations de la série et des chapitres.
        Gère les URLs de chapitres individuels en redirigeant vers la série parente.
        """
        try:
            # Nettoyer l'URL (supprimer les paramètres de tracking)
            url = self._clean_url(url)

            # Si l'URL pointe vers un chapitre, on redirige vers la série
            if self._is_chapter_url(url):
                series_url = await self._extract_series_url_from_chapter(url)
                if series_url:
                    logger.debug(f"URL de chapitre détectée, redirection vers: {series_url}")
                    return await super().analyze(series_url)

            # Analyse standard via Madara
            return await super().analyze(url)

        except Exception as e:
            logger.error(f"Erreur analyse AsuraScans pour {url}: {e}")
            raise ProviderError(f"Impossible d'analyser l'URL: {e}", provider_id=self.id)

    async def get_chapter_images(self, chapter_id: str) -> List[str]:
        """
        Récupère les URLs des images d'un chapitre.
        Nettoie les URLs pour obtenir les images en pleine résolution.
        Gère les différents formats d'images (jpg, png, webp).
        """
        try:
            images = await super().get_chapter_images(chapter_id)
            if not images:
                logger.warning(f"Aucune image trouvée pour le chapitre {chapter_id}")
                return []

            # Nettoyer les URLs
            cleaned_images = []
            for url in images:
                cleaned = self._clean_image_url(url)
                if cleaned:
                    cleaned_images.append(cleaned)

            logger.debug(f"Récupéré {len(cleaned_images)} images pour le chapitre {chapter_id}")
            return cleaned_images

        except Exception as e:
            logger.error(f"Erreur récupération images AsuraScans pour {chapter_id}: {e}")
            raise ProviderError(f"Impossible de récupérer les images: {e}", provider_id=self.id)

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche des séries sur Asura Scans.
        Utilise la recherche interne du site.
        """
        try:
            # Utiliser l'endpoint de recherche de Madara
            search_url = f"{self.base_url}/?s={query}&post_type=wp-manga"
            async with self._get_session() as session:
                async with session.get(search_url) as resp:
                    html = await resp.text()
                    soup = self._parse_html(html)

                    results = []
                    # Sélecteur pour les résultats de recherche (adapté à Asura Scans)
                    items = soup.select(".c-search-results .c-search-result-item, .search-results .result-item, .manga-item")
                    if not items:
                        # Fallback: utiliser les sélecteurs de Madara
                        items = soup.select(".c-search-results .c-search-result-item")

                    for item in items[:limit]:
                        title_elem = item.select_one(".post-title, .title, h3 a, .manga-title a")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        url = title_elem.get("href")
                        if not url:
                            continue

                        # Image de couverture
                        cover_elem = item.select_one("img, .img-responsive, .attachment-thumbnail")
                        cover_url = cover_elem.get("src") if cover_elem else None

                        # Auteur (si disponible)
                        author_elem = item.select_one(".author, .meta-author, .writer")
                        author = author_elem.get_text(strip=True) if author_elem else ""

                        results.append({
                            "title": title,
                            "url": url,
                            "cover_url": cover_url,
                            "author": author,
                            "provider_id": self.id,
                            "provider_name": self.name,
                            "nsfw": self.nsfw,
                            "language": "en"
                        })

                    logger.debug(f"Recherche AsuraScans '{query}': {len(results)} résultats")
                    return results

        except Exception as e:
            logger.error(f"Erreur recherche AsuraScans pour '{query}': {e}")
            raise ProviderError(f"Erreur lors de la recherche: {e}", provider_id=self.id)

    # ==========================================================================
    #  Méthodes utilitaires
    # ==========================================================================

    def _is_chapter_url(self, url: str) -> bool:
        """Détecte si une URL pointe vers un chapitre."""
        # Asura Scans utilise généralement des URLs du type:
        # https://asurascans.com/manga/series-name/chapter-1/
        # ou https://asurascans.com/series-name/chapter-1/
        # ou avec /chapter/ au lieu de /chapter-
        patterns = [
            r'/chapter-[0-9]+',
            r'/chapter/[0-9]+',
            r'/ch-[0-9]+',
            r'/capitulo-[0-9]+'
        ]
        for pattern in patterns:
            if re.search(pattern, url):
                return True
        return False

    async def _extract_series_url_from_chapter(self, chapter_url: str) -> Optional[str]:
        """
        Extrait l'URL de la série parente à partir d'une URL de chapitre.
        Deux méthodes: essayer de trouver un lien vers la série dans la page,
        ou effectuer une manipulation d'URL (supprimer la partie chapitre).
        """
        try:
            # Méthode 1: Extraire depuis la page
            async with self._get_session() as session:
                async with session.get(chapter_url) as resp:
                    html = await resp.text()
                    soup = self._parse_html(html)

                    # Chercher dans les breadcrumbs
                    breadcrumb_links = soup.select(".breadcrumb a, .crumbs a, .chapter-breadcrumb a")
                    for link in breadcrumb_links:
                        href = link.get("href")
                        if href and "/manga/" in href or "/series/" in href or "/manhwa/" in href:
                            return href

                    # Chercher le lien "Series" dans la page
                    series_link = soup.select_one(".series-title a, .manga-title a, .entry-title a")
                    if series_link:
                        href = series_link.get("href")
                        if href:
                            return href

            # Méthode 2: Manipulation d'URL (fallback)
            # Supprimer la partie "/chapter-xxx/" de l'URL
            chapter_pattern = r'(/chapter-[0-9]+/?|/chapter/[0-9]+/?|/ch-[0-9]+/?)'
            cleaned = re.sub(chapter_pattern, '/', chapter_url)
            # S'assurer que l'URL se termine par un slash
            if not cleaned.endswith('/'):
                cleaned += '/'
            return cleaned

        except Exception as e:
            logger.warning(f"Impossible d'extraire l'URL de la série depuis {chapter_url}: {e}")
            return None

    def _clean_url(self, url: str) -> str:
        """Nettoie une URL en supprimant les paramètres de tracking inutiles."""
        parsed = urlparse(url)
        # Supprimer les paramètres de tracking courants
        query_params = parsed.query.split('&')
        cleaned_params = [p for p in query_params if not p.startswith('utm_') and not p.startswith('ref=')]
        cleaned_query = '&'.join(cleaned_params)
        cleaned_url = parsed._replace(query=cleaned_query).geturl()
        return cleaned_url

    def _clean_image_url(self, url: str) -> Optional[str]:
        """
        Nettoie l'URL d'une image pour obtenir la version pleine résolution.
        Supprime les paramètres de redimensionnement (resize, w, h, etc.).
        """
        if not url:
            return None

        # Si l'URL est relative, la rendre absolue
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = urljoin(self.base_url, url)

        # Supprimer les paramètres de taille
        parsed = urlparse(url)
        # Garder seulement le chemin, sans les paramètres de query
        # Mais parfois les paramètres sont nécessaires (ex: pour les images webp)
        # On supprime seulement les paramètres de redimensionnement connus
        if parsed.query:
            params = parsed.query.split('&')
            kept_params = []
            for param in params:
                if not any(key in param.lower() for key in ['resize', 'w=', 'h=', 'width=', 'height=', 'fit=']):
                    kept_params.append(param)
            new_query = '&'.join(kept_params)
            url = parsed._replace(query=new_query).geturl()

        return url

    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse le HTML avec BeautifulSoup."""
        return BeautifulSoup(html, 'lxml')
