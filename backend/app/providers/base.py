# ==========================================================================
#  NexusDL 2.0 - Base Provider (Abstract)
#  Fichier : backend/app/providers/base.py
# ==========================================================================

"""
Classe de base abstraite pour tous les providers de NexusDL.

Cette classe définit l'interface commune que tous les providers doivent implémenter :
- Analyse d'URL (extraction des métadonnées et des chapitres)
- Récupération des images d'un chapitre
- Recherche de séries
- Gestion des sessions HTTP asynchrones
- Rate limiting et retries
- Gestion des erreurs cohérente
"""

import abc
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Callable
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta

import aiohttp
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.exceptions import ProviderError

logger = logging.getLogger(__name__)


class BaseProvider(abc.ABC):
    """
    Classe abstraite pour tous les providers.

    Attributs à définir dans les classes filles :
    - id (str) : Identifiant unique du provider
    - name (str) : Nom affiché
    - base_url (str) : URL de base du site
    - supported_languages (List[str]) : Langues supportées
    - nsfw (bool) : Indique si le contenu est pour adultes
    - version (str) : Version du provider
    - description (str) : Description
    - enabled (bool) : Activation/désactivation
    - priority (int) : Priorité (plus élevé = plus prioritaire)

    Méthodes abstraites à implémenter :
    - analyze(url) -> Dict[str, Any]
    - get_chapter_images(chapter_id) -> List[str]
    - search(query, limit) -> List[Dict[str, Any]]

    Méthodes optionnelles à surcharger :
    - get_series_info(series_id) -> Dict[str, Any] (si différent de analyze)
    - get_chapter_info(chapter_id) -> Dict[str, Any]
    - validate_url(url) -> bool
    """

    # ==========================================================================
    #  Attributs de classe (à surcharger)
    # ==========================================================================

    # Métadonnées du provider
    id: str = "base"
    name: str = "Base Provider"
    base_url: str = "https://example.com"
    supported_languages: List[str] = ["en"]
    nsfw: bool = False
    version: str = "1.0.0"
    description: str = "Provider de base (à étendre)"
    enabled: bool = True
    priority: int = 0

    # Configuration HTTP
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    user_agent: str = f"NexusDL/{settings.APP_VERSION} (compatible; Provider/{id})"
    headers: Dict[str, str] = {}

    # Rate limiting (requêtes par seconde)
    rate_limit: Optional[float] = None  # None = pas de limite
    _last_request_time: Optional[datetime] = None

    # ==========================================================================
    #  Initialisation
    # ==========================================================================

    def __init__(self):
        # Session aiohttp partagée (créée à la demande)
        self._session: Optional[aiohttp.ClientSession] = None
        # Verrou pour le rate limiting
        self._rate_lock = asyncio.Lock()
        # Fusion des headers par défaut avec ceux de l'instance
        self._default_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        self._default_headers.update(self.headers)
        self._rate_limit = self.rate_limit

    # ==========================================================================
    #  Gestion de session HTTP
    # ==========================================================================

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Retourne une session aiohttp partagée, en créant une si nécessaire.
        """
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(
                limit=20,
                limit_per_host=10,
                ttl_dns_cache=300,
                enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self._default_headers
            )
        return self._session

    async def close(self):
        """
        Ferme proprement la session HTTP.
        """
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    # ==========================================================================
    #  Rate limiting
    # ==========================================================================

    async def _rate_limit_wait(self):
        """
        Applique le rate limiting si configuré.
        Bloque jusqu'à ce que la prochaine requête soit autorisée.
        """
        if self._rate_limit is None or self._rate_limit <= 0:
            return

        async with self._rate_lock:
            now = datetime.now()
            if self._last_request_time is not None:
                min_interval = 1.0 / self._rate_limit
                elapsed = (now - self._last_request_time).total_seconds()
                if elapsed < min_interval:
                    wait_time = min_interval - elapsed
                    await asyncio.sleep(wait_time)
            self._last_request_time = datetime.now()

    # ==========================================================================
    #  Requêtes HTTP
    # ==========================================================================

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: Optional[int] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Effectue une requête HTTP avec gestion des retries et du rate limiting.
        Retourne l'objet response (à consommer par l'appelant).
        """
        if retries is None:
            retries = self.max_retries
        if timeout is None:
            timeout = self.timeout

        # Appliquer le rate limiting avant chaque requête
        await self._rate_limit_wait()

        # Préparer les headers
        request_headers = self._default_headers.copy()
        if headers:
            request_headers.update(headers)

        last_exception = None
        for attempt in range(retries + 1):
            try:
                session = await self._get_session()
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=request_headers,
                    timeout=timeout,
                    **kwargs
                ) as response:
                    return response

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt < retries:
                    wait_time = self.retry_delay * (2 ** attempt)  # backoff exponentiel
                    logger.warning(f"Erreur requête {url} (tentative {attempt+1}): {e} - pause {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Échec requête {url} après {retries+1} tentatives: {e}")
                    raise ProviderError(f"Erreur de requête HTTP: {e}", provider_id=self.id)

        # Ne devrait jamais arriver
        raise ProviderError(f"Échec inattendu pour {url}", provider_id=self.id)

    async def _fetch_html(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> str:
        """
        Récupère le HTML d'une page.
        Gère automatiquement les erreurs et les redirections.
        """
        response = await self._request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            retries=retries,
            timeout=timeout
        )
        try:
            text = await response.text()
            # Vérifier le statut
            if response.status >= 400:
                raise ProviderError(
                    f"Erreur HTTP {response.status} sur {url}",
                    provider_id=self.id
                )
            return text
        finally:
            response.close()

    async def _fetch_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Récupère une réponse JSON d'une API.
        """
        response = await self._request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            retries=retries,
            timeout=timeout
        )
        try:
            if response.status >= 400:
                error_text = await response.text()
                raise ProviderError(
                    f"Erreur HTTP {response.status} sur {url}: {error_text[:200]}",
                    provider_id=self.id
                )
            return await response.json()
        finally:
            response.close()

    # ==========================================================================
    #  Parsing HTML
    # ==========================================================================

    def _parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse le HTML avec BeautifulSoup (utilise lxml par défaut).
        """
        return BeautifulSoup(html, 'lxml')

    # ==========================================================================
    #  Utilitaires
    # ==========================================================================

    def _clean_url(self, url: str) -> str:
        """
        Nettoie une URL en supprimant les paramètres de tracking et fragments inutiles.
        Peut être surchargée par les providers fils.
        """
        parsed = urlparse(url)
        # Supprimer les paramètres de tracking courants
        if parsed.query:
            params = parsed.query.split('&')
            filtered = [p for p in params if not p.startswith(('utm_', 'ref='))]
            query = '&'.join(filtered) if filtered else ''
        else:
            query = ''
        # Reconstruire sans fragment (ancre)
        return parsed._replace(query=query, fragment='').geturl()

    def _url_join(self, *parts: str) -> str:
        """
        Combine des parties d'URL en utilisant urljoin de manière sécurisée.
        """
        if not parts:
            return ''
        base = parts[0]
        for part in parts[1:]:
            base = urljoin(base, part)
        return base

    def _normalize_language(self, lang: str) -> str:
        """
        Normalise un code de langue (ex: 'fr_FR' -> 'fr').
        """
        if not lang:
            return 'en'
        return lang.split('_')[0].split('-')[0].lower()[:2]

    # ==========================================================================
    #  Méthodes abstraites (à implémenter)
    # ==========================================================================

    @abc.abstractmethod
    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyse une URL (série ou chapitre) et retourne les informations complètes.
        Retourne un dictionnaire avec au minimum :
            - title (str) : Titre de la série
            - url (str) : URL de la série
            - provider_id (str) : ID du provider
            - chapters (List[Dict]) : Liste des chapitres avec id, title, number, url
            - author (str, optionnel)
            - description (str, optionnel)
            - cover_url (str, optionnel)
            - genre (List[str], optionnel)
            - status (str, optionnel)
            - year (int, optionnel)
            - language (str, optionnel)
            - nsfw (bool)
            - total_chapters (int)
        """
        pass

    @abc.abstractmethod
    async def get_chapter_images(self, chapter_id: str) -> List[str]:
        """
        Récupère les URLs des images d'un chapitre.
        chapter_id peut être un ID ou une URL.
        Retourne une liste d'URLs d'images.
        """
        pass

    @abc.abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche des séries correspondant à une requête.
        Retourne une liste de résultats avec au minimum :
            - series_id (str)
            - title (str)
            - url (str)
            - cover_url (str, optionnel)
            - author (str, optionnel)
            - provider_id (str)
            - provider_name (str)
            - nsfw (bool)
            - language (str)
        """
        pass

    # ==========================================================================
    #  Méthodes optionnelles (peuvent être surchargées)
    # ==========================================================================

    async def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'une série par son ID.
        Par défaut, on appelle analyze avec l'URL construite à partir de l'ID.
        À surcharger si l'API offre une meilleure méthode.
        """
        url = f"{self.base_url}/series/{series_id}/"
        return await self.analyze(url)

    async def get_chapter_info(self, chapter_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un chapitre par son ID.
        Par défaut, renvoie un dictionnaire basique.
        À surcharger si disponible.
        """
        return {
            "id": chapter_id,
            "title": f"Chapitre {chapter_id}",
            "number": 0,
            "url": chapter_id if chapter_id.startswith("http") else f"{self.base_url}/chapter/{chapter_id}/",
            "pages": 0,
            "language": self.supported_languages[0] if self.supported_languages else "en"
        }

    async def validate_url(self, url: str) -> bool:
        """
        Vérifie si une URL est valide pour ce provider.
        Par défaut, vérifie que le domaine correspond à base_url.
        """
        parsed = urlparse(url)
        base_parsed = urlparse(self.base_url)
        return parsed.netloc == base_parsed.netloc

    # ==========================================================================
    #  Gestion du cycle de vie
    # ==========================================================================

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}')>"
