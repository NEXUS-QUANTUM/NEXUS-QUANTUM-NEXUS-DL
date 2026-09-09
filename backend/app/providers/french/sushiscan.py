# ==========================================================================
#  NexusDL 2.0 - Provider SushiScan (French)
#  Fichier : backend/app/providers/french/sushiscan.py
# ==========================================================================

"""
Provider pour SushiScan (https://sushiscan.net).
Site de scan français utilisant le thème Madara avec quelques adaptations.

SushiScan est l'un des sites les plus populaires pour les scans en français,
proposant un large catalogue de mangas, manhwas et webtoons.

Ce provider gère :
- L'analyse des séries et des chapitres
- La récupération des images avec gestion des différents formats
- La recherche de séries
- La gestion des URLs de chapitres individuels
- L'extraction des métadonnées (auteur, genres, statut, etc.)
- Les protections anti-bot (Cloudflare) via Playwright (optionnel)
"""

import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from datetime import datetime

from bs4 import BeautifulSoup

from app.providers.themes.madara import MadaraProvider
from app.providers.registry import register_provider
from app.core.exceptions import ProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)


@register_provider
class SushiScanProvider(MadaraProvider):
    """
    Provider pour SushiScan.
    Hérite de MadaraProvider et surcharge certaines méthodes pour s'adapter
    aux spécificités du site.
    """

    # ==========================================================================
    #  Métadonnées du provider
    # ==========================================================================

    id = "sushiscan"
    name = "SushiScan"
    base_url = "https://sushiscan.net"
    supported_languages = ["fr"]
    nsfw = False
    version = "2.0.0"
    description = "SushiScan - Site de scan en français (manga, manhwa, webtoon)"
    enabled = True
    priority = 10  # Priorité maximale car c'est le site français le plus utilisé

    # ==========================================================================
    #  Sélecteurs CSS personnalisés (adaptés à SushiScan)
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
        "series_alternative": ".alternative-content, .meta-alternative, .series-alternative",

        # Chapitres
        "chapters_list": ".chapters-list .wp-manga-chapter, .wp-manga-chapter, .chapter-list .chapter-item, .list-chapters .chapter-item",
        "chapter_title": "a",
        "chapter_link": "a",
        "chapter_number": "a .chapter-number, .chapter-number, .chapter-title .chapternum, .chapter .chapternum",
        "chapter_date": ".chapter-release-date, .chapter-date, .release-date",

        # Images du chapitre
        "image_container": ".reading-content .page-break img, .reading-content img, .chapter-content img, .page-content img",
        "image_selector": "img",

        # Pagination
        "next_page": ".nav-links .next, .next-page, .pagination .next",
        "previous_page": ".nav-links .prev, .prev-page, .pagination .prev",

        # Recherche
        "search_results": ".c-search-results .c-search-result-item, .search-results .result-item, .manga-item",
        "search_title": ".post-title, .title, h3 a, .manga-title a",
        "search_cover": "img, .img-responsive, .attachment-thumbnail",
        "search_author": ".author, .meta-author, .writer",

        # Pagination des chapitres
        "chapter_pagination": ".wp-pagenavi, .pagination, .nav-links",
        "chapter_page_link": "a.page-numbers, a.page, .nav-links a",
    }

    # ==========================================================================
    #  Configuration anti-bot (optionnel)
    # ==========================================================================

    # SushiScan peut utiliser Cloudflare, on peut activer Playwright pour certains cas
    USE_PLAYWRIGHT_FOR_CLOUDFLARE = True
    _playwright_available = False
    _browser = None
    _context = None
    _playwright = None

    # ==========================================================================
    #  Méthodes surchargées
    # ==========================================================================

    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyse une URL SushiScan et retourne les informations de la série et des chapitres.
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
                else:
                    # Fallback: essayer de deviner l'URL de la série
                    series_url = self._guess_series_url_from_chapter(url)
                    if series_url:
                        logger.debug(f"URL de chapitre détectée (fallback), redirection vers: {series_url}")
                        return await super().analyze(series_url)
                    else:
                        raise ProviderError("Impossible de trouver la série associée au chapitre", provider_id=self.id)

            # Analyse standard via Madara
            return await super().analyze(url)

        except Exception as e:
            logger.error(f"Erreur analyse SushiScan pour {url}: {e}")
            raise ProviderError(f"Impossible d'analyser l'URL: {e}", provider_id=self.id)

    async def get_chapter_images(self, chapter_id: str) -> List[str]:
        """
        Récupère les URLs des images d'un chapitre.
        SushiScan peut utiliser des images avec différents formats (webp, jpg, png).
        Nettoie les URLs et gère les éventuels redimensionnements.
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
            logger.error(f"Erreur récupération images SushiScan pour {chapter_id}: {e}")
            raise ProviderError(f"Impossible de récupérer les images: {e}", provider_id=self.id)

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche des séries sur SushiScan.
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
                    items = soup.select(self.selectors.get("search_results", ".c-search-results .c-search-result-item"))
                    if not items:
                        # Fallback
                        items = soup.select(".search-results .result-item, .manga-item")

                    for item in items[:limit]:
                        # Titre et lien
                        title_elem = item.select_one(self.selectors.get("search_title", ".post-title, .title, h3 a"))
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get("href")
                        if not url:
                            continue

                        # Image de couverture
                        cover_elem = item.select_one(self.selectors.get("search_cover", "img"))
                        cover_url = None
                        if cover_elem:
                            cover_url = cover_elem.get("src") or cover_elem.get("data-src")
                            if cover_url and not cover_url.startswith("http"):
                                cover_url = urljoin(self.base_url, cover_url)

                        # Auteur
                        author_elem = item.select_one(self.selectors.get("search_author", ".author, .meta-author"))
                        author = author_elem.get_text(strip=True) if author_elem else ""

                        results.append({
                            "series_id": url.split("/")[-2] if url.endswith("/") else url.split("/")[-1],
                            "title": title,
                            "url": url,
                            "cover_url": cover_url,
                            "author": author,
                            "provider_id": self.id,
                            "provider_name": self.name,
                            "nsfw": self.nsfw,
                            "language": "fr",
                            "genre": [],
                            "status": "unknown"
                        })

                    logger.debug(f"Recherche SushiScan '{query}': {len(results)} résultats")
                    return results

        except Exception as e:
            logger.error(f"Erreur recherche SushiScan pour '{query}': {e}")
            return []

    # ==========================================================================
    #  Méthodes de gestion des chapitres avec pagination
    # ==========================================================================

    async def _get_chapters_with_pagination(self, series_url: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les chapitres d'une série en gérant la pagination.
        SushiScan peut paginer les chapitres (surtout pour les séries longues).
        """
        all_chapters = []
        current_url = series_url
        max_pages = 10  # Sécurité

        for page_num in range(max_pages):
            try:
                async with self._get_session() as session:
                    async with session.get(current_url) as resp:
                        html = await resp.text()
                        soup = self._parse_html(html)

                        # Extraire les chapitres de la page
                        chapters = self._extract_chapters_from_soup(soup)
                        all_chapters.extend(chapters)

                        # Vérifier s'il y a une page suivante
                        next_page_elem = soup.select_one(self.selectors.get("next_page", ".nav-links .next, .next-page"))
                        if not next_page_elem:
                            break

                        next_url = next_page_elem.get("href")
                        if not next_url or next_url == current_url:
                            break

                        current_url = next_url
                        await asyncio.sleep(0.5)  # Petit délai pour éviter la surcharge

            except Exception as e:
                logger.warning(f"Erreur récupération page {page_num+1} des chapitres: {e}")
                break

        return all_chapters

    def _extract_chapters_from_soup(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extrait la liste des chapitres depuis un BeautifulSoup d'une page de série.
        """
        chapters = []
        chapter_elems = soup.select(self.selectors.get("chapters_list", ".chapters-list .wp-manga-chapter, .wp-manga-chapter"))

        for elem in chapter_elems:
            link = elem.select_one("a")
            if not link:
                continue
            href = link.get("href")
            if not href:
                continue

            # Titre du chapitre
            title = link.get_text(strip=True)
            # Numéro du chapitre
            number_elem = elem.select_one(self.selectors.get("chapter_number", ".chapter-number"))
            number_text = number_elem.get_text(strip=True) if number_elem else ""
            chapter_number = self._extract_chapter_number(number_text or title)

            # Date de publication
            date_elem = elem.select_one(self.selectors.get("chapter_date", ".chapter-release-date, .chapter-date"))
            date_text = date_elem.get_text(strip=True) if date_elem else ""

            chapters.append({
                "id": href,
                "title": title,
                "number": chapter_number,
                "url": href,
                "release_date": date_text,
                "is_available": True
            })

        # Trier par numéro
        chapters.sort(key=lambda x: x["number"])
        return chapters

    def _extract_chapter_number(self, text: str) -> float:
        """
        Extrait le numéro de chapitre depuis une chaîne de caractères.
        """
        # Patterns pour extraire les numéros de chapitre
        patterns = [
            r'(?:chapitre|chap|chapter|ch|#)\s*([0-9]+(?:\.[0-9]+)?)',
            r'([0-9]+(?:\.[0-9]+)?)\s*(?:chapitre|chap|chapter|ch|#)',
            r'([0-9]+(?:\.[0-9]+)?)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return 0.0

    # ==========================================================================
    #  Méthodes utilitaires spécifiques à SushiScan
    # ==========================================================================

    def _is_chapter_url(self, url: str) -> bool:
        """Détecte si une URL pointe vers un chapitre."""
        # SushiScan utilise généralement des URLs du type:
        # https://sushiscan.net/series-name/chapter-1/
        # ou https://sushiscan.net/lecture/series-name/chapter-1/
        patterns = [
            r'/chapter-?[0-9]+/?',
            r'/chapitre-?[0-9]+/?',
            r'/chap-?[0-9]+/?',
            r'/lecture/.*?/chapter-?[0-9]+/?'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)

    async def _extract_series_url_from_chapter(self, chapter_url: str) -> Optional[str]:
        """
        Extrait l'URL de la série parente à partir d'une URL de chapitre.
        """
        try:
            async with self._get_session() as session:
                async with session.get(chapter_url) as resp:
                    html = await resp.text()
                    soup = self._parse_html(html)

                    # Méthode 1: Breadcrumbs (le plus fiable)
                    breadcrumb_links = soup.select(".breadcrumb a, .crumbs a, .chapter-breadcrumb a")
                    for link in breadcrumb_links:
                        href = link.get("href")
                        if href and ("/manga/" in href or "/series/" in href or "/manhwa/" in href):
                            return href

                    # Méthode 2: Lien "Série" dans la page
                    series_link = soup.select_one(".series-title a, .manga-title a, .entry-title a, .page-title a")
                    if series_link:
                        href = series_link.get("href")
                        if href:
                            return href

                    # Méthode 3: Lien "Retour à la série"
                    back_link = soup.select_one("a:has-text('Série'), a:has-text('Retour')")
                    if back_link:
                        href = back_link.get("href")
                        if href:
                            return href

            # Fallback: manipulation d'URL (supprimer la partie chapitre)
            return self._guess_series_url_from_chapter(chapter_url)

        except Exception as e:
            logger.warning(f"Impossible d'extraire l'URL de la série depuis {chapter_url}: {e}")
            return None

    def _guess_series_url_from_chapter(self, chapter_url: str) -> Optional[str]:
        """
        Devine l'URL de la série en manipulant l'URL du chapitre.
        """
        # Supprimer la partie "/chapter-xxx/" ou "/lecture/.../chapter-xxx/"
        patterns = [
            r'(/chapter-?[0-9]+/?)$',
            r'(/chapitre-?[0-9]+/?)$',
            r'(/chap-?[0-9]+/?)$',
            r'(/lecture/[^/]+/)(chapter-?[0-9]+/?)$'
        ]
        for pattern in patterns:
            match = re.search(pattern, chapter_url, re.IGNORECASE)
            if match:
                # Si le pattern est /lecture/.../chapter-xxx/, on supprime la fin
                if '/lecture/' in chapter_url:
                    # Garder la partie avant /lecture/ + la série
                    series_part = chapter_url.split('/lecture/')[0]
                    # Extraire le nom de la série
                    series_name = chapter_url.split('/lecture/')[1].split('/')[0]
                    return f"{series_part}/manga/{series_name}/"
                else:
                    # Supprimer le pattern
                    return chapter_url[:match.start()]
        return None

    def _clean_url(self, url: str) -> str:
        """Nettoie une URL en supprimant les paramètres de tracking inutiles."""
        parsed = urlparse(url)
        # Supprimer les paramètres de tracking
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

        # SushiScan utilise parfois des paramètres de taille
        parsed = urlparse(url)
        if parsed.query:
            params = parsed.query.split('&')
            kept_params = []
            for param in params:
                if not any(key in param.lower() for key in ['resize', 'w=', 'h=', 'width=', 'height=', 'fit=', 'scale=', 'quality=']):
                    kept_params.append(param)
            new_query = '&'.join(kept_params)
            url = parsed._replace(query=new_query).geturl()

        return url

    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse le HTML avec BeautifulSoup."""
        return BeautifulSoup(html, 'lxml')

    # ==========================================================================
    #  Gestion du cache pour les séries très populaires
    # ==========================================================================

    async def get_series_info_cached(self, series_url: str) -> Optional[Dict[str, Any]]:
        """
        Version avec cache pour les séries populaires (à implémenter si nécessaire).
        """
        # Ici on pourrait ajouter une logique de cache Redis ou mémoire
        # Pour l'instant, on appelle simplement super()
        return await self.get_series_info(series_url)
