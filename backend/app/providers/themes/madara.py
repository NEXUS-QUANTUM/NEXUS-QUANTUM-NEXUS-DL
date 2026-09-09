# ==========================================================================
#  NexusDL 2.0 - Provider Thème Madara (Base)
#  Fichier : backend/app/providers/themes/madara.py
# ==========================================================================

"""
Provider de base pour les sites utilisant le thème WordPress Madara.

Madara est un thème WordPress spécialisé dans les sites de scan (manga, manhwa, webtoon).
Il est utilisé par la grande majorité des sites français et internationaux.

Ce provider implémente les mécanismes génériques pour :
- L'analyse des séries (titre, auteur, description, couverture, genres, statut)
- L'extraction des chapitres avec gestion de la pagination
- La récupération des images avec gestion du lazy loading et des pages multiples
- La recherche de séries
- La gestion des URLs de chapitres individuels

Ce provider est conçu pour être hérité et surchargé par les providers spécifiques
(sushiscan, asurascans, etc.) qui peuvent avoir des sélecteurs ou des comportements
légèrement différents.
"""

import logging
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, urljoin
from datetime import datetime

from bs4 import BeautifulSoup
import aiohttp

from app.providers.base import BaseProvider
from app.providers.registry import register_provider
from app.core.exceptions import ProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)


@register_provider
class MadaraProvider(BaseProvider):
    """
    Provider générique pour les sites utilisant le thème Madara.
    """

    # ==========================================================================
    #  Métadonnées du provider
    # ==========================================================================

    id = "madara"
    name = "Madara (Générique)"
    base_url = "https://example.com"  # Sera surchargé par les providers fils
    supported_languages = ["en", "fr"]  # Générique
    nsfw = False
    version = "2.0.0"
    description = "Provider générique pour les sites utilisant le thème Madara"
    enabled = True
    priority = 1  # Priorité basse car générique (les spécifiques ont la priorité)

    # ==========================================================================
    #  Sélecteurs CSS par défaut (structure Madara standard)
    # ==========================================================================

    # Ces sélecteurs peuvent être surchargés par les providers fils
    selectors = {
        # Informations de la série (page série)
        "series_title": "h1.entry-title, .post-title, .page-title, .series-title",
        "series_author": ".author-content a, .series-author a, .author a, .meta-author a, .writer a",
        "series_description": ".description-summary p, .entry-content p, .summary__content p, .series-description p, .post-content p",
        "series_cover": ".thumb img, .series-thumb img, .wp-post-image, .attachment-post-thumbnail, .summary_image img",
        "series_genres": ".genres-content a, .meta-genres a, .series-genres a, .taxonomy a",
        "series_status": ".status-content a, .series-status, .meta-status a, .status a",
        "series_release_year": ".release-content, .meta-year, .series-year",
        "series_alternative": ".alternative-content, .meta-alternative, .series-alternative",

        # Chapitres (page série)
        "chapters_list": ".chapters-list .wp-manga-chapter, .wp-manga-chapter, .chapter-list .chapter-item, .list-chapters .chapter-item, .c-list-chapter .chapter-item",
        "chapter_title": "a, .chapter-title",
        "chapter_link": "a",
        "chapter_number": ".chapter-number, .chapternum, .chapter .num, .chapter a .num",
        "chapter_date": ".chapter-release-date, .chapter-date, .release-date, .chapter .date",

        # Images du chapitre (page lecture)
        "image_container": ".reading-content img, .chapter-content img, .page-content img, .text-container img",
        "image_selector": "img",

        # Pagination des chapitres (page série)
        "chapter_pagination": ".wp-pagenavi, .pagination, .nav-links, .c-list-chapter .pagination",
        "chapter_page_link": "a.page-numbers, a.page, .nav-links a, .pagination a",

        # Pagination des pages de chapitre (lecture)
        "chapter_next_page": ".nav-links .next, .next-page, .pagination .next, a.next",
        "chapter_prev_page": ".nav-links .prev, .prev-page, .pagination .prev, a.prev",

        # Recherche
        "search_results": ".c-search-results .c-search-result-item, .search-results .result-item, .manga-item, .c-search-results .item",
        "search_title": ".post-title, .title, h3 a, .manga-title a, .result-item .title",
        "search_cover": "img, .img-responsive, .attachment-thumbnail, .result-item img",
        "search_author": ".author, .meta-author, .writer, .result-item .author",
    }

    # ==========================================================================
    #  Configuration
    # ==========================================================================

    # Nombre maximum de pages de chapitres à parcourir (sécurité)
    MAX_CHAPTER_PAGES = 50
    # Nombre maximum de pages de lecture à parcourir (sécurité)
    MAX_READING_PAGES = 20
    # Délai entre les requêtes de pagination
    PAGINATION_DELAY = 0.5

    # ==========================================================================
    #  Méthodes principales
    # ==========================================================================

    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyse une URL et retourne les informations de la série et des chapitres.
        Gère les URLs de séries et les URLs de chapitres.
        """
        try:
            # Nettoyer l'URL
            url = self._clean_url(url)

            # Détecter le type d'URL
            if self._is_chapter_url(url):
                # Si c'est un chapitre, extraire l'URL de la série
                series_url = await self._extract_series_url_from_chapter(url)
                if series_url:
                    logger.debug(f"URL de chapitre détectée, redirection vers: {series_url}")
                    return await self._analyze_series(series_url)
                else:
                    # Fallback : essayer de deviner l'URL de la série
                    series_url = self._guess_series_url(url)
                    if series_url:
                        return await self._analyze_series(series_url)
                    else:
                        # Si vraiment impossible, analyser le chapitre directement
                        return await self._analyze_single_chapter(url)

            # Analyser la série
            return await self._analyze_series(url)

        except Exception as e:
            logger.error(f"Erreur analyse Madara pour {url}: {e}")
            raise ProviderError(f"Impossible d'analyser l'URL: {e}", provider_id=self.id)

    async def _analyze_series(self, url: str) -> Dict[str, Any]:
        """
        Analyse une page de série et retourne les métadonnées et la liste des chapitres.
        """
        # Récupérer le HTML de la page
        html = await self._fetch_html(url)
        soup = self._parse_html(html)

        # Extraire les métadonnées
        title = self._extract_series_title(soup)
        author = self._extract_series_author(soup)
        description = self._extract_series_description(soup)
        cover_url = self._extract_series_cover(soup)
        genres = self._extract_series_genres(soup)
        status = self._extract_series_status(soup)
        year = self._extract_series_year(soup)

        # Extraire les chapitres (avec pagination)
        chapters = await self._extract_all_chapters(url, soup)

        return {
            "title": title,
            "url": url,
            "provider_id": self.id,
            "chapters": chapters,
            "author": author,
            "description": description,
            "cover_url": cover_url,
            "genre": genres,
            "status": status,
            "year": year,
            "language": self.supported_languages[0] if self.supported_languages else "en",
            "nsfw": self.nsfw,
            "total_chapters": len(chapters)
        }

    async def _analyze_single_chapter(self, url: str) -> Dict[str, Any]:
        """
        Analyse une page de chapitre individuel (fallback).
        Retourne un seul chapitre sans métadonnées de série.
        """
        # Récupérer le HTML
        html = await self._fetch_html(url)
        soup = self._parse_html(html)

        # Extraire le titre du chapitre
        title_elem = soup.select_one(self.selectors.get("series_title", "h1.entry-title"))
        title = title_elem.get_text(strip=True) if title_elem else f"Chapitre {url.split('/')[-2] or 'inconnu'}"

        return {
            "title": title,
            "url": url,
            "provider_id": self.id,
            "chapters": [
                {
                    "id": url,
                    "title": title,
                    "number": 0,
                    "url": url,
                    "is_available": True
                }
            ],
            "author": "",
            "description": "",
            "cover_url": "",
            "genre": [],
            "status": "unknown",
            "year": None,
            "language": self.supported_languages[0] if self.supported_languages else "en",
            "nsfw": self.nsfw,
            "total_chapters": 1
        }

    async def get_chapter_images(self, chapter_id: str) -> List[str]:
        """
        Récupère les URLs des images d'un chapitre.
        Gère les pages multiples et le lazy loading.
        """
        try:
            # Si chapter_id est une URL, l'utiliser
            if chapter_id.startswith("http"):
                chapter_url = chapter_id
            else:
                # Sinon, considérer que c'est un chemin relatif
                chapter_url = urljoin(self.base_url, chapter_id)

            all_images = []
            current_url = chapter_url
            page_num = 1

            while current_url and page_num <= self.MAX_READING_PAGES:
                logger.debug(f"Récupération des images - page {page_num}: {current_url}")

                # Récupérer la page
                html = await self._fetch_html(current_url)
                soup = self._parse_html(html)

                # Extraire les images de la page
                images = self._extract_images_from_page(soup)
                all_images.extend(images)

                # Vérifier s'il y a une page suivante
                next_url = self._get_next_page_url(soup)
                if not next_url or next_url == current_url:
                    break

                current_url = next_url
                page_num += 1
                await asyncio.sleep(self.PAGINATION_DELAY)

            logger.debug(f"Récupéré {len(all_images)} images pour {chapter_id}")
            return all_images

        except Exception as e:
            logger.error(f"Erreur récupération images Madara pour {chapter_id}: {e}")
            raise ProviderError(f"Impossible de récupérer les images: {e}", provider_id=self.id)

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche des séries sur un site Madara.
        """
        try:
            search_url = f"{self.base_url}/?s={query}&post_type=wp-manga"
            html = await self._fetch_html(search_url)
            soup = self._parse_html(html)

            results = []
            items = soup.select(self.selectors.get("search_results", ".c-search-results .c-search-result-item, .search-results .result-item"))

            for item in items[:limit]:
                # Titre et lien
                title_elem = item.select_one(self.selectors.get("search_title", ".post-title, .title, h3 a"))
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                url = title_elem.get("href")
                if not url:
                    continue

                # Couverture
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
                    "language": self.supported_languages[0] if self.supported_languages else "en",
                    "genre": [],
                    "status": "unknown"
                })

            logger.debug(f"Recherche Madara '{query}': {len(results)} résultats")
            return results

        except Exception as e:
            logger.error(f"Erreur recherche Madara pour '{query}': {e}")
            return []

    # ==========================================================================
    #  Méthodes d'extraction des chapitres
    # ==========================================================================

    async def _extract_all_chapters(self, series_url: str, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extrait tous les chapitres d'une série, en gérant la pagination.
        """
        all_chapters = []
        current_soup = soup
        current_url = series_url
        page_num = 1

        while current_soup and page_num <= self.MAX_CHAPTER_PAGES:
            # Extraire les chapitres de la page courante
            chapters = self._extract_chapters_from_soup(current_soup)
            all_chapters.extend(chapters)

            # Vérifier s'il y a une page suivante
            next_url = self._get_next_chapter_page_url(current_soup)
            if not next_url or next_url == current_url:
                break

            # Récupérer la page suivante
            logger.debug(f"Récupération page de chapitres {page_num+1}: {next_url}")
            html = await self._fetch_html(next_url)
            current_soup = self._parse_html(html)
            current_url = next_url
            page_num += 1
            await asyncio.sleep(self.PAGINATION_DELAY)

        # Supprimer les doublons (par URL)
        seen_urls = set()
        unique_chapters = []
        for ch in all_chapters:
            if ch["id"] not in seen_urls:
                seen_urls.add(ch["id"])
                unique_chapters.append(ch)

        # Trier par numéro de chapitre
        unique_chapters.sort(key=lambda x: x.get("number", 0))

        return unique_chapters

    def _extract_chapters_from_soup(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extrait les chapitres depuis un BeautifulSoup d'une page de série.
        """
        chapters = []
        chapter_elems = soup.select(self.selectors.get("chapters_list", ".chapters-list .wp-manga-chapter, .wp-manga-chapter"))

        for elem in chapter_elems:
            # Trouver le lien du chapitre
            link = elem.select_one("a")
            if not link:
                continue
            href = link.get("href")
            if not href:
                continue

            # Titre du chapitre
            title = link.get_text(strip=True) or "Chapitre"

            # Numéro du chapitre
            number_elem = elem.select_one(self.selectors.get("chapter_number", ".chapter-number, .chapternum"))
            if number_elem:
                number_text = number_elem.get_text(strip=True)
                chapter_number = self._extract_number_from_text(number_text)
            else:
                chapter_number = self._extract_number_from_text(title)

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

        return chapters

    # ==========================================================================
    #  Méthodes d'extraction des images
    # ==========================================================================

    def _extract_images_from_page(self, soup: BeautifulSoup) -> List[str]:
        """
        Extrait les URLs des images d'une page de chapitre.
        Gère le lazy loading (data-src, data-lazy-src, etc.).
        """
        images = []
        container = soup.select_one(self.selectors.get("image_container", ".reading-content, .chapter-content"))

        if not container:
            # Fallback: chercher toutes les images de la page
            img_elems = soup.find_all("img")
        else:
            img_elems = container.find_all("img")

        for img in img_elems:
            # Essayer différents attributs pour l'URL (ordre de priorité)
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or img.get("data-original") or img.get("data-url")

            if src:
                # Nettoyer l'URL
                cleaned = self._clean_image_url(src)
                if cleaned and not cleaned.startswith("data:"):
                    images.append(cleaned)
            else:
                # Vérifier si l'image est dans un style background
                style = img.get("style", "")
                match = re.search(r'background-image:\s*url\(["\']?([^"\'\)]+)["\']?\)', style)
                if match:
                    cleaned = self._clean_image_url(match.group(1))
                    if cleaned:
                        images.append(cleaned)

        return images

    def _get_next_page_url(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Récupère l'URL de la page suivante pour la pagination des chapitres (lecture).
        """
        next_elem = soup.select_one(self.selectors.get("chapter_next_page", ".nav-links .next, .next-page, .pagination .next"))
        if next_elem:
            href = next_elem.get("href")
            if href:
                return href
        return None

    def _get_next_chapter_page_url(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Récupère l'URL de la page suivante pour la pagination des chapitres (série).
        """
        pagination = soup.select_one(self.selectors.get("chapter_pagination", ".wp-pagenavi, .pagination"))
        if pagination:
            # Chercher le lien "Suivant" ou "Next"
            next_links = pagination.select(".next, .nextpostslink, .page-numbers.next")
            for link in next_links:
                href = link.get("href")
                if href:
                    return href
            # Sinon, prendre le dernier lien avec un numéro plus grand
            page_links = pagination.select(self.selectors.get("chapter_page_link", "a.page-numbers, a.page"))
            # Si on a des liens numériques, prendre le dernier qui n'est pas "next"
            # C'est complexe, on se contente du lien "next"
        return None

    # ==========================================================================
    #  Méthodes d'extraction des métadonnées
    # ==========================================================================

    def _extract_series_title(self, soup: BeautifulSoup) -> str:
        """Extrait le titre de la série."""
        elem = soup.select_one(self.selectors.get("series_title", "h1.entry-title"))
        return elem.get_text(strip=True) if elem else "Sans titre"

    def _extract_series_author(self, soup: BeautifulSoup) -> str:
        """Extrait l'auteur de la série."""
        elem = soup.select_one(self.selectors.get("series_author", ".author-content a"))
        return elem.get_text(strip=True) if elem else ""

    def _extract_series_description(self, soup: BeautifulSoup) -> str:
        """Extrait la description de la série."""
        elem = soup.select_one(self.selectors.get("series_description", ".description-summary p, .summary__content p"))
        if elem:
            return elem.get_text(strip=True)
        return ""

    def _extract_series_cover(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait l'URL de la couverture."""
        elem = soup.select_one(self.selectors.get("series_cover", ".thumb img, .summary_image img"))
        if elem:
            src = elem.get("src") or elem.get("data-src")
            if src:
                return self._clean_image_url(src)
        return None

    def _extract_series_genres(self, soup: BeautifulSoup) -> List[str]:
        """Extrait la liste des genres."""
        elems = soup.select(self.selectors.get("series_genres", ".genres-content a"))
        genres = [elem.get_text(strip=True) for elem in elems if elem.get_text(strip=True)]
        return genres

    def _extract_series_status(self, soup: BeautifulSoup) -> str:
        """Extrait le statut de la série."""
        elem = soup.select_one(self.selectors.get("series_status", ".status-content a"))
        if elem:
            text = elem.get_text(strip=True)
            # Normalisation des statuts
            status_map = {
                "ongoing": "ongoing",
                "en cours": "ongoing",
                "completed": "completed",
                "terminé": "completed",
                "hiatus": "hiatus",
                "en pause": "hiatus",
                "cancelled": "cancelled",
                "annulé": "cancelled"
            }
            lower_text = text.lower()
            for key, value in status_map.items():
                if key in lower_text:
                    return value
            return lower_text
        return "unknown"

    def _extract_series_year(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait l'année de publication."""
        elem = soup.select_one(self.selectors.get("series_release_year", ".release-content"))
        if elem:
            text = elem.get_text(strip=True)
            match = re.search(r'(\d{4})', text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return None

    # ==========================================================================
    #  Méthodes utilitaires
    # ==========================================================================

    def _is_chapter_url(self, url: str) -> bool:
        """
        Détecte si une URL pointe vers un chapitre.
        Patterns courants : /chapter-{num}/, /ch-{num}/, /lecture/.../chapter-{num}/
        """
        patterns = [
            r'/chapter-?[0-9]+/?',
            r'/chapitre-?[0-9]+/?',
            r'/ch-?[0-9]+/?',
            r'/capitulo-?[0-9]+/?',
            r'/lecture/.*?/chapter-?[0-9]+/?',
            r'/read/.*?/[0-9]+/?',  # Certains sites utilisent /read/series-name/123/
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)

    async def _extract_series_url_from_chapter(self, chapter_url: str) -> Optional[str]:
        """
        Extrait l'URL de la série depuis une URL de chapitre.
        """
        try:
            html = await self._fetch_html(chapter_url)
            soup = self._parse_html(html)

            # Méthode 1: Breadcrumbs (le plus fiable)
            breadcrumb_links = soup.select(".breadcrumb a, .crumbs a, .chapter-breadcrumb a, .entry-breadcrumb a")
            for link in breadcrumb_links:
                href = link.get("href")
                if href and any(keyword in href for keyword in ["/manga/", "/series/", "/manhwa/", "/webtoon/", "/title/"]):
                    return href

            # Méthode 2: Lien "Série" dans la page
            series_link = soup.select_one(".series-title a, .manga-title a, .entry-title a, .page-title a, .post-title a")
            if series_link:
                href = series_link.get("href")
                if href and any(keyword in href for keyword in ["/manga/", "/series/", "/manhwa/", "/webtoon/", "/title/"]):
                    return href

            # Méthode 3: Lien "Retour" ou "Home"
            back_link = soup.select_one("a:has-text('Série'), a:has-text('Retour'), a:has-text('Series')")
            if back_link:
                href = back_link.get("href")
                if href and any(keyword in href for keyword in ["/manga/", "/series/", "/manhwa/", "/webtoon/", "/title/"]):
                    return href

        except Exception as e:
            logger.warning(f"Impossible d'extraire l'URL de la série depuis {chapter_url}: {e}")

        # Fallback: manipulation d'URL
        return self._guess_series_url(chapter_url)

    def _guess_series_url(self, url: str) -> Optional[str]:
        """
        Devine l'URL de la série en manipulant l'URL du chapitre.
        """
        # Supprimer la partie "/chapter-xxx/" ou similaire
        patterns = [
            r'(/chapter-?[0-9]+/?)$',
            r'(/chapitre-?[0-9]+/?)$',
            r'(/ch-?[0-9]+/?)$',
            r'(/capitulo-?[0-9]+/?)$',
            r'(/lecture/[^/]+/)(chapter-?[0-9]+/?)$',
            r'(/read/[^/]+/)([0-9]+/?)$',
        ]
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                # Si c'est /lecture/..., garder la partie avant + le nom de la série
                if '/lecture/' in url or '/read/' in url:
                    # Extraire le nom de la série
                    parts = url.split('/')
                    for i, part in enumerate(parts):
                        if part in ['lecture', 'read'] and i + 1 < len(parts):
                            series_name = parts[i + 1]
                            # Construire l'URL de la série
                            base = '/'.join(parts[:parts.index('lecture') if 'lecture' in url else parts.index('read')])
                            return f"{base}/series/{series_name}/" if base else f"{self.base_url}/series/{series_name}/"
                else:
                    # Supprimer la partie chapitre
                    return url[:match.start()]
        return None

    def _extract_number_from_text(self, text: str) -> float:
        """
        Extrait un numéro de chapitre depuis une chaîne de texte.
        """
        patterns = [
            r'(?:chapitre|chap|chapter|ch|#|vol|volume)\s*([0-9]+(?:\.[0-9]+)?)',
            r'([0-9]+(?:\.[0-9]+)?)\s*(?:chapitre|chap|chapter|ch|#|vol|volume)',
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

    def _clean_url(self, url: str) -> str:
        """Nettoie une URL (supprime les paramètres de tracking)."""
        parsed = urlparse(url)
        query_params = parsed.query.split('&')
        cleaned_params = [p for p in query_params if not p.startswith('utm_') and not p.startswith('ref=')]
        cleaned_query = '&'.join(cleaned_params)
        return parsed._replace(query=cleaned_query).geturl()

    def _clean_image_url(self, url: str) -> Optional[str]:
        """
        Nettoie une URL d'image (rend absolue, supprime les paramètres de taille).
        """
        if not url:
            return None
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = urljoin(self.base_url, url)
        # Supprimer les paramètres de redimensionnement
        parsed = urlparse(url)
        if parsed.query:
            params = parsed.query.split('&')
            kept = [p for p in params if not any(k in p.lower() for k in ['resize', 'w=', 'h=', 'width=', 'height=', 'fit='])]
            url = parsed._replace(query='&'.join(kept)).geturl()
        return url

    async def _fetch_html(self, url: str) -> str:
        """
        Récupère le HTML d'une page.
        """
        try:
            async with self._get_session() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "fr,en;q=0.9",
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 403:
                        # Peut-être Cloudflare, on log mais on tente quand même
                        logger.warning(f"Accès interdit (403) pour {url}, tentative de récupération quand même")
                        return await response.text()
                    else:
                        raise ProviderError(f"Erreur HTTP {response.status} sur {url}", provider_id=self.id)
        except aiohttp.ClientResponseError as e:
            raise ProviderError(f"Erreur requête HTTP: {e}", provider_id=self.id)

    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse le HTML avec BeautifulSoup."""
        return BeautifulSoup(html, 'lxml')
