# ==========================================================================
#  NexusDL 2.0 - Moteur de téléchargement
#  Fichier : backend/app/core/engine.py
# ==========================================================================

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from app.core.config import settings
from app.core.downloader import Downloader
from app.core.cbz_builder import CbzBuilder
from app.providers.registry import ProviderRegistry
from app.models.job import JobStatus, Job
from app.models.library import LibraryItem
from app.core.exceptions import DownloadError, ProviderError

logger = logging.getLogger(__name__)


class DownloadEngine:
    """Moteur principal de téléchargement."""

    def __init__(self):
        self.downloader = Downloader()
        self.cbz_builder = CbzBuilder()
        self.registry = ProviderRegistry()
        self.active_jobs: Dict[str, Job] = {}
        self.job_callbacks = []

    def register_callback(self, callback):
        """Enregistre un callback pour les mises à jour de jobs."""
        self.job_callbacks.append(callback)

    async def analyze_url(self, url: str) -> Dict[str, Any]:
        """Analyse une URL pour identifier le provider et extraire les infos."""
        provider = self.registry.get_provider_for_url(url)
        if not provider:
            raise ProviderError(f"Aucun provider trouvé pour l'URL: {url}")

        try:
            return await provider.analyze(url)
        except Exception as e:
            logger.error(f"Erreur analyse {url}: {e}")
            raise ProviderError(f"Erreur lors de l'analyse: {e}")

    async def start_download(self, url: str, chapter_ids: List[str]) -> str:
        """Démarre un téléchargement pour les chapitres spécifiés."""
        # Analyse de l'URL
        analysis = await self.analyze_url(url)
        title = analysis.get("title", "unknown")
        provider = self.registry.get_provider_for_url(url)

        # Création du job
        job_id = f"job_{int(datetime.now().timestamp())}"
        job = Job(
            id=job_id,
            url=url,
            status=JobStatus.PENDING,
            title=title,
            total_chapters=len(chapter_ids),
            done_chapters=0,
            progress=0.0,
            current_chapter="",
            logs=["Job créé"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.active_jobs[job_id] = job
        await self._notify_job_update(job)

        # Lancement asynchrone
        asyncio.create_task(self._run_download(job_id, provider, analysis, chapter_ids))

        return job_id

    async def _run_download(self, job_id: str, provider, analysis: Dict[str, Any], chapter_ids: List[str]):
        """Exécute le téléchargement en arrière-plan."""
        job = self.active_jobs.get(job_id)
        if not job:
            return

        try:
            job.status = JobStatus.RUNNING
            job.logs.append("Démarrage du téléchargement...")
            await self._notify_job_update(job)

            # Récupération des chapitres
            chapters = analysis.get("chapters", [])
            selected_chapters = [c for c in chapters if c.get("id") in chapter_ids]

            if not selected_chapters:
                job.status = JobStatus.FAILED
                job.logs.append("Aucun chapitre sélectionné trouvé.")
                await self._notify_job_update(job)
                return

            # Téléchargement des images
            temp_dir = settings.get_temp_path() / job_id
            temp_dir.mkdir(parents=True, exist_ok=True)

            all_images = []
            for idx, chapter in enumerate(selected_chapters):
                job.current_chapter = chapter.get("title", f"Chapitre {idx+1}")
                job.logs.append(f"Téléchargement du chapitre: {chapter.get('title')}")
                await self._notify_job_update(job)

                # Télécharger les images du chapitre
                try:
                    images = await provider.get_chapter_images(chapter["id"])
                    # Télécharger chaque image
                    image_paths = await self.downloader.download_images(
                        images,
                        temp_dir / f"chapter_{idx+1:02d}",
                        referer=provider.base_url
                    )
                    if image_paths:
                        all_images.append({
                            "chapter_title": chapter.get("title", f"Chapter {idx+1}"),
                            "images": image_paths
                        })
                    else:
                        job.logs.append(f"⚠️ Aucune image téléchargée pour le chapitre {chapter.get('title')}")
                except Exception as e:
                    job.logs.append(f"Erreur chapitre {chapter.get('title')}: {e}")
                    logger.error(f"Erreur téléchargement chapitre: {e}")

                job.done_chapters = idx + 1
                job.progress = (idx + 1) / len(selected_chapters) * 100
                await self._notify_job_update(job)

            if not all_images:
                job.status = JobStatus.FAILED
                job.logs.append("Aucune image téléchargée, abandon.")
                await self._notify_job_update(job)
                return

            # Construction du CBZ
            job.logs.append("Construction du fichier CBZ...")
            await self._notify_job_update(job)

            cbz_path = await self.cbz_builder.build(
                title=analysis.get("title", "unknown"),
                chapters=all_images,
                output_dir=settings.get_download_path(),
                metadata={
                    "title": analysis.get("title"),
                    "author": analysis.get("author", ""),
                    "description": analysis.get("description", "")
                }
            )

            # Enregistrement dans la bibliothèque
            await self._save_to_library(analysis, cbz_path)

            job.status = JobStatus.COMPLETED
            job.logs.append(f"✅ Téléchargement terminé: {cbz_path.name}")
            job.progress = 100.0
            await self._notify_job_update(job)

        except Exception as e:
            logger.error(f"Erreur critique lors du téléchargement du job {job_id}: {e}", exc_info=True)
            job.status = JobStatus.FAILED
            job.logs.append(f"❌ Erreur critique: {e}")
            await self._notify_job_update(job)

        finally:
            # Nettoyage du dossier temporaire (sauf si on veut garder pour debug)
            if temp_dir.exists():
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Impossible de supprimer le dossier temporaire {temp_dir}: {e}")

    async def _notify_job_update(self, job: Job):
        """Notifie tous les callbacks enregistrés d'une mise à jour de job."""
        job.updated_at = datetime.now().isoformat()
        for callback in self.job_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(job)
                else:
                    callback(job)
            except Exception as e:
                logger.error(f"Erreur dans un callback de job: {e}")

    async def _save_to_library(self, analysis: Dict[str, Any], cbz_path: Path):
        """Enregistre le fichier CBZ dans la bibliothèque (métadonnées)."""
        try:
            from app.services.file_service import FileService
            from app.models.library import LibraryItem
            import os

            stat = cbz_path.stat()
            item = LibraryItem(
                title=analysis.get("title", "Sans titre"),
                filename=cbz_path.name,
                path=str(cbz_path),
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                metadata={
                    "author": analysis.get("author", ""),
                    "description": analysis.get("description", ""),
                    "chapters": analysis.get("chapters", [])
                }
            )
            # Ici on pourrait stocker dans une DB, mais on utilise FileService
            file_service = FileService()
            # Simuler un enregistrement
            file_service.add_library_item(item)
            logger.info(f"📚 Élément ajouté à la bibliothèque: {item.title}")
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement dans la bibliothèque: {e}")

    async def close(self):
        """Ferme proprement le downloader."""
        await self.downloader.close()
