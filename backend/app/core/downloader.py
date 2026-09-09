# ==========================================================================
#  NexusDL 2.0 - Downloader
#  Fichier : backend/app/core/downloader.py
# ==========================================================================

import os
import asyncio
import logging
import random
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlparse

import aiohttp
import aiofiles

from app.core.config import settings
from app.core.exceptions import DownloadError

logger = logging.getLogger(__name__)


class Downloader:
    """
    Gestionnaire de téléchargement asynchrone avec aiohttp.
    Supporte les retries, le parallélisme, les timeouts, et les headers personnalisés.
    """

    def __init__(self):
        self.max_threads = settings.MAX_THREADS
        self.timeout = settings.DOWNLOAD_TIMEOUT
        self.retry_count = settings.DOWNLOAD_RETRY
        self.session: Optional[aiohttp.ClientSession] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
        ]

    async def _get_session(self) -> aiohttp.ClientSession:
        """Retourne une session aiohttp en créant une si nécessaire."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(limit=self.max_threads * 2, limit_per_host=self.max_threads)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                }
            )
        return self.session

    async def _get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Génère des headers avec un User-Agent aléatoire."""
        headers = {
            "User-Agent": random.choice(self._user_agents)
        }
        if referer:
            headers["Referer"] = referer
        return headers

    async def download_image(
        self,
        url: str,
        output_dir: Union[str, Path],
        filename: Optional[str] = None,
        referer: Optional[str] = None,
        retry: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> Optional[Path]:
        """
        Télécharge une image unique et la sauvegarde dans le dossier de sortie.

        Args:
            url (str): URL de l'image.
            output_dir (Union[str, Path]): Dossier de destination.
            filename (Optional[str]): Nom du fichier (si None, déduit de l'URL).
            referer (Optional[str]): Header Referer à ajouter.
            retry (Optional[int]): Nombre de tentatives (par défaut self.retry_count).
            timeout (Optional[int]): Timeout en secondes (par défaut self.timeout).

        Returns:
            Optional[Path]: Chemin du fichier téléchargé, ou None en cas d'échec.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            # Extraire le nom de fichier de l'URL
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            if not filename or '.' not in filename:
                # Ajouter une extension par défaut
                filename = f"image_{int(time.time())}.jpg"
            # Nettoyer le nom
            filename = self._sanitize_filename(filename)

        file_path = output_dir / filename

        # Si le fichier existe déjà, on le retourne directement
        if file_path.exists():
            logger.debug(f"Fichier déjà existant: {file_path}")
            return file_path

        retry_count = retry if retry is not None else self.retry_count
        timeout_value = timeout if timeout is not None else self.timeout

        for attempt in range(retry_count + 1):
            try:
                session = await self._get_session()
                headers = await self._get_headers(referer)

                async with session.get(url, headers=headers, timeout=timeout_value) as response:
                    if response.status == 200:
                        # Lire le contenu
                        content = await response.read()
                        # Sauvegarder
                        async with aiofiles.open(file_path, 'wb') as f:
                            await f.write(content)
                        logger.debug(f"Image téléchargée: {file_path} ({len(content)} octets)")
                        return file_path
                    elif response.status in (404, 410):
                        # Pas de retry pour ces codes
                        logger.warning(f"Image introuvable (HTTP {response.status}): {url}")
                        return None
                    else:
                        logger.warning(f"Échec téléchargement {url} (HTTP {response.status}), tentative {attempt+1}/{retry_count+1}")
                        if attempt < retry_count:
                            await asyncio.sleep(2 ** attempt + random.random())
                        else:
                            return None
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Erreur téléchargement {url}: {e}, tentative {attempt+1}/{retry_count+1}")
                if attempt < retry_count:
                    await asyncio.sleep(2 ** attempt + random.random())
                else:
                    return None
            except Exception as e:
                logger.error(f"Erreur inattendue lors du téléchargement {url}: {e}")
                return None

        return None

    async def download_images(
        self,
        urls: List[str],
        output_dir: Union[str, Path],
        referer: Optional[str] = None,
        max_concurrent: Optional[int] = None
    ) -> List[Path]:
        """
        Télécharge plusieurs images en parallèle.

        Args:
            urls (List[str]): Liste des URLs d'images.
            output_dir (Union[str, Path]): Dossier de destination.
            referer (Optional[str]): Header Referer commun.
            max_concurrent (Optional[int]): Nombre maximum de téléchargements simultanés.

        Returns:
            List[Path]: Liste des chemins des fichiers téléchargés (uniquement les réussis).
        """
        if not urls:
            return []

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []
        semaphore = asyncio.Semaphore(max_concurrent or self.max_threads)

        async def download_one(url):
            async with semaphore:
                # Générer un nom de fichier basé sur l'URL
                filename = self._url_to_filename(url)
                # Si le nom existe déjà, ajouter un suffixe
                if (output_dir / filename).exists():
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while (output_dir / f"{base}_{counter}{ext}").exists():
                        counter += 1
                    filename = f"{base}_{counter}{ext}"
                return await self.download_image(url, output_dir, filename, referer)

        tasks = [download_one(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Path):
                downloaded.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Erreur dans download_one: {result}")

        return downloaded

    def _url_to_filename(self, url: str) -> str:
        """Convertit une URL en nom de fichier valide."""
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = f"image_{hash(url) % 100000}.jpg"
        # Si pas d'extension, ajouter .jpg
        if '.' not in filename:
            filename += '.jpg'
        return self._sanitize_filename(filename)

    def _sanitize_filename(self, filename: str) -> str:
        """Nettoie un nom de fichier pour enlever les caractères invalides."""
        invalid_chars = r'<>:"/\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        # Éviter les noms trop longs
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:195] + ext
        return filename

    async def close(self):
        """Ferme la session aiohttp."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Session aiohttp fermée.")

    def __del__(self):
        """Destructeur pour fermer la session si nécessaire."""
        if self.session and not self.session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.session.close())
                else:
                    loop.run_until_complete(self.session.close())
            except Exception:
                pass
