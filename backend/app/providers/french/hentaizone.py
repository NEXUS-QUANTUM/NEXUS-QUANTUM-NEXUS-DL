# ==========================================================================
#  NexusDL 2.0 - Provider Hentaizone (French)
#  Fichier : backend/app/providers/french/hentaizone.py
# ==========================================================================

"""
Provider pour Hentaizone (https://hentaizone.xyz).
Site de scan français spécialisé dans les doujinshi et contenus pour adultes.

Particularités :
- Utilisation de Playwright pour le scraping (site JS-heavy avec Cloudflare)
- Contenu NSFW (hentai, doujinshi, ero-manga)
- Structure spécifique : séries, chapitres, images
- Gestion des popups et des redirections
"""

import logging
import asyncio
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from app.providers.base import BaseProvider
from app.providers.registry import register_provider
from app.core.exceptions import ProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)


@register_provider
class HentaizoneProvider(BaseProvider):
    """
    Provider Hentaizone utilisant Playwright pour le scraping.
    """

    # ==========================================================================
    #  Métadonnées du provider
    # ==========================================================================

    id = "hentaizone"
    name = "Hentaizone"
    base_url = "https://hentaizone.xyz"
    supported_languages = ["fr"]
    nsfw = True
    version = "1.0.0"
    description = "Hentaizone - Doujinshi et hentai en français (NSFW)"
    enabled = True
    priority = 3

    # ==========================================================================
    #  Configuration Playwright
    # ==========================================================================

    # Timeout pour les opérations Playwright (ms)
    PLAYWRIGHT_TIMEOUT = 30000
    # Nombre de tentatives en cas d'échec
    MAX_RETRIES = 3
    # Délai entre les requêtes pour éviter la détection
    REQUEST_DELAY = 1.0

    # ==========================================================================
    #  Sélecteurs CSS
    # ==========================================================================

    selectors = {
        # Page série
        "series_title": "h1.entry-title, .post-title, .series-title",
        "series_author": ".author-content a, .meta-author a",
        "series_description": ".description-summary p, .entry-content p",
        "series_cover": ".thumb img, .series-thumb img, .attachment-post-thumbnail",
        "series_genres": ".genres-content a, .meta-genres a",
        "series_status": ".status-content a",

        # Liste des chapitres
        "chapters_list": ".chapters-list .wp-manga-chapter, .chapter-list li",
        "chapter_title": "a",
        "chapter_link": "a",

        # Page chapitre (images)
        "image_container": ".reading-content .page-break img, .chapter-content img",
        "image_selector": "img",

        # Navigation
        "next_page": ".nav-links .next, .next-page",
        "pagination": ".pagination",
    }

    # ==========================================================================
    #  Gestion du navigateur Playwright
    # ==========================================================================

    _browser: Optional[Browser] = None
    _context: Optional[BrowserContext] = None
    _playwright = None

    async def _ensure_browser(self) -> Browser:
        """
        Assure qu'un navigateur Playwright est lancé et prêt.
        """
        if self._browser is not None and self._browser.is_connected():
            return self._browser

        if self._playwright is None:
            self._playwright = await async_playwright().start()

        # Lancer Chromium avec des options pour éviter la détection
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--window-size=1920,1080"
            ]
        )

        # Créer un contexte avec des vues réalistes
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="fr-FR",
            timezone_id="Europe/Paris",
            ignore_https_errors=True
        )

        logger.info("✅ Navigateur Playwright lancé pour Hentaizone")
        return self._browser

    async def _close_browser(self):
        """Ferme le navigateur Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("🔒 Navigateur Playwright fermé")

    async def _get_page(self, url: str, retry: int = 0) -> Optional[Page]:
        """
        Récupère une page Playwright après avoir géré les éventuels défis Cloudflare.
        """
        max_retries = self.MAX_RETRIES
        try:
            browser = await self._ensure_browser()
            context = self._context
            if not context:
                context = await browser.new_context()
                self._context = context

            page = await context.new_page()

            # Naviguer vers l'URL avec un timeout
            await page.goto(url, timeout=self.PLAYWRIGHT_TIMEOUT, wait_until="domcontentloaded")

            # Attendre que la page soit chargée
            await page.wait_for_load_state("networkidle", timeout=self.PLAYWRIGHT_TIMEOUT)

            # Gérer les éventuels popups ou overlays (ex: accept cookies)
            try:
                # Accepter les cookies si présent
                accept_button = page.locator("button:has-text('Accepter'), button:has-text('Accept'), button:has-text('OK')")
                if await accept_button.count() > 0:
                    await accept_button.first.click()
                    await asyncio.sleep(0.5)
            except Exception:
                pass

            return page

        except Exception as e:
            logger.warning(f"Erreur Playwright sur {url} (tentative {retry+1}/{max_retries}): {e}")

            if retry < max_retries - 1:
                await asyncio.sleep(2 ** retry + 1)
                # Fermer la page si créée
                if 'page' in locals():
                    await page.close()
                return await self._get_page(url, retry + 1)
            else:
                raise ProviderError(f"Échec de chargement de la page après {max_retries} tentatives: {url}", provider_id=self.id)

    # ==========================================================================
    #  Méthodes principales
    # ==========================================================================

    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyse une URL Hentaizone et retourne les informations de la série et des chapitres.
        Gère les URLs de séries et les URLs de chapitres.
        """
        try:
            url = self._clean_url(url)

            # Détecter si c'est une URL de série ou de chapitre
            if self._is_chapter_url(url):
                # Extraire l'URL de la série depuis le chapitre
                series_url = await self._extract_series_url_from_chapter(url)
                if series_url:
                    url = series_url
                else:
                    raise ProviderError("Impossible de trouver la série associée au chapitre", provider_id=self.id)

            # Analyser la série
            return await self._analyze_series(url)

        except Exception as e:
            logger.error(f"Erreur analyse Hentaizone pour {url}: {e}")
            raise ProviderError(f"Impossible d'analyser l'URL: {e}", provider_id=self.id)

    async def _analyze_series(self, url: str) -> Dict[str, Any]:
        """
        Analyse une page de série pour extraire les métadonnées et la liste des chapitres.
        """
        page = await self._get_page(url)
        try:
            # Attendre que le contenu principal soit chargé
            await page.wait_for_selector(".entry-title, .post-title, .series-title", timeout=self.PLAYWRIGHT_TIMEOUT)

            # Extraire le titre
            title_elem = page.locator(self.selectors["series_title"])
            title = await title_elem.text_content()
            title = title.strip() if title else "Sans titre"

            # Extraire l'auteur
            author_elem = page.locator(self.selectors["series_author"])
            author = await author_elem.text_content()
            author = author.strip() if author else ""

            # Extraire la description
            desc_elem = page.locator(self.selectors["series_description"])
            description = await desc_elem.text_content()
            description = description.strip() if description else ""

            # Extraire la couverture
            cover_elem = page.locator(self.selectors["series_cover"])
            cover_url = await cover_elem.get_attribute("src")
            if cover_url and not cover_url.startswith("http"):
                cover_url = urljoin(self.base_url, cover_url)

            # Extraire les genres
            genre_elems = page.locator(self.selectors["series_genres"])
            genres = []
            async for elem in genre_elems.all():
                text = await elem.text_content()
                if text:
                    genres.append(text.strip())

            # Extraire les chapitres
            chapters = await self._extract_chapters(page)

            return {
                "title": title,
                "url": url,
                "provider_id": self.id,
                "chapters": chapters,
                "author": author,
                "description": description,
                "cover_url": cover_url,
                "genre": genres,
                "status": "",
                "year": None,
                "language": "fr",
                "nsfw": self.nsfw,
                "total_chapters": len(chapters)
            }

        finally:
            await page.close()

    async def _extract_chapters(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extrait la liste des chapitres depuis la page de la série.
        """
        chapters = []
        try:
            # Attendre la liste des chapitres
            await page.wait_for_selector(self.selectors["chapters_list"], timeout=self.PLAYWRIGHT_TIMEOUT)

            # Sélectionner les éléments de chapitre
            chapter_elems = page.locator(self.selectors["chapters_list"])

            # On prend tous les éléments <a> à l'intérieur
            async for item in chapter_elems.all():
                link = item.locator("a")
                if await link.count() > 0:
                    href = await link.get_attribute("href")
                    title_text = await link.text_content()
                    if href:
                        # Nettoyer le titre
                        if title_text:
                            title = title_text.strip()
                        else:
                            # Extraire le numéro du chapitre depuis l'URL
                            match = re.search(r'/chapter-?([0-9]+)/?', href)
                            if match:
                                title = f"Chapitre {match.group(1)}"
                            else:
                                title = "Chapitre"
                        # Extraire le numéro
                        chapter_number = 0
                        match = re.search(r'/chapter-?([0-9]+)/?', href)
                        if match:
                            try:
                                chapter_number = float(match.group(1))
                            except ValueError:
                                pass

                        chapters.append({
                            "id": href,
                            "title": title,
                            "number": chapter_number,
                            "url": href,
                            "is_available": True
                        })

            # Trier par numéro de chapitre
            chapters.sort(key=lambda x: x["number"])

        except Exception as e:
            logger.warning(f"Erreur extraction chapitres: {e}")

        return chapters

    async def get_chapter_images(self, chapter_id: str) -> List[str]:
        """
        Récupère les URLs des images d'un chapitre.
        """
        page = None
        try:
            # Si chapter_id est une URL, l'utiliser directement
            if chapter_id.startswith("http"):
                url = chapter_id
            else:
                # Sinon, considérer que c'est un chemin relatif
                url = urljoin(self.base_url, chapter_id)

            page = await self._get_page(url)

            # Attendre que les images soient chargées
            await page.wait_for_selector(self.selectors["image_container"], timeout=self.PLAYWRIGHT_TIMEOUT)

            # Récupérer toutes les images
            images = await page.evaluate("""
                () => {
                    const images = [];
                    document.querySelectorAll('.reading-content .page-break img, .chapter-content img').forEach(img => {
                        let src = img.getAttribute('src') || img.getAttribute('data-src');
                        if (src && !src.startsWith('data:')) {
                            images.push(src);
                        }
                    });
                    return images;
                }
            """)

            if not images:
                logger.warning(f"Aucune image trouvée pour le chapitre {chapter_id}")
                return []

            # Nettoyer les URLs
            cleaned = []
            for url in images:
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    url = urljoin(self.base_url, url)
                cleaned.append(url)

            logger.debug(f"Récupéré {len(cleaned)} images pour {chapter_id}")
            return cleaned

        except Exception as e:
            logger.error(f"Erreur récupération images Hentaizone pour {chapter_id}: {e}")
            raise ProviderError(f"Impossible de récupérer les images: {e}", provider_id=self.id)
        finally:
            if page:
                await page.close()

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche des séries sur Hentaizone.
        Utilise le formulaire de recherche du site.
        """
        try:
            search_url = f"{self.base_url}/?s={query}&post_type=wp-manga"
            page = await self._get_page(search_url)

            results = []
            # Sélecteur pour les résultats
            items = page.locator(".c-search-results .c-search-result-item, .search-results .result-item, .manga-item")

            async for item in items.all()[:limit]:
                # Titre et lien
                link = item.locator("a")
                if await link.count() == 0:
                    continue
                title = await link.text_content()
                href = await link.get_attribute("href")
                if not href:
                    continue

                # Couverture
                cover = item.locator("img")
                cover_url = await cover.get_attribute("src") if await cover.count() > 0 else None
                if cover_url and not cover_url.startswith("http"):
                    cover_url = urljoin(self.base_url, cover_url)

                results.append({
                    "title": title.strip() if title else "Sans titre",
                    "url": href,
                    "cover_url": cover_url,
                    "provider_id": self.id,
                    "provider_name": self.name,
                    "nsfw": self.nsfw,
                    "language": "fr"
                })

            await page.close()
            logger.debug(f"Recherche Hentaizone '{query}': {len(results)} résultats")
            return results

        except Exception as e:
            logger.error(f"Erreur recherche Hentaizone pour '{query}': {e}")
            return []

    # ==========================================================================
    #  Méthodes utilitaires
    # ==========================================================================

    def _is_chapter_url(self, url: str) -> bool:
        """Détecte si une URL pointe vers un chapitre."""
        patterns = [r'/chapter-?[0-9]+/?', r'/chapitre-?[0-9]+/?']
        return any(re.search(pattern, url) for pattern in patterns)

    async def _extract_series_url_from_chapter(self, chapter_url: str) -> Optional[str]:
        """
        Extrait l'URL de la série parente depuis une URL de chapitre.
        Utilise le breadcrumb ou le lien de retour.
        """
        page = await self._get_page(chapter_url)
        try:
            # Chercher le lien "Série" dans les breadcrumbs
            breadcrumb = page.locator(".breadcrumb a, .crumbs a")
            if await breadcrumb.count() >= 2:
                # Le dernier lien avant le chapitre est la série
                links = await breadcrumb.all()
                if len(links) >= 2:
                    href = await links[-2].get_attribute("href")
                    if href and ("/manga/" in href or "/series/" in href):
                        return href

            # Chercher un lien spécifique "Retour à la série"
            back_link = page.locator("a:has-text('Série'), a:has-text('Retour')")
            if await back_link.count() > 0:
                href = await back_link.first.get_attribute("href")
                if href:
                    return href

            return None
        finally:
            await page.close()

    def _clean_url(self, url: str) -> str:
        """Nettoie une URL en supprimant les paramètres de tracking."""
        parsed = urlparse(url)
        # Garder seulement le chemin
        cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return cleaned

    # ==========================================================================
    #  Nettoyage
    # ==========================================================================

    async def __aenter__(self):
        await self._ensure_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_browser()
