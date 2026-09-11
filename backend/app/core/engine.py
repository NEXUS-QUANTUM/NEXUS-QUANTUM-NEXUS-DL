# ==========================================================================
#  NexusDL 2.0 - Moteur de téléchargement
#  Fichier : backend/app/core/engine.py
#  Version : 2.0.0-final
# ==========================================================================

import asyncio
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.downloader import Downloader
from app.core.cbz_builder import CbzBuilder
from app.core.exceptions import DownloadError, ProviderError
from app.models.job import Job, JobStatus
from app.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class DownloadEngine:
    """Moteur principal de téléchargement."""

    def __init__(self) -> None:
        self.downloader = Downloader()
        self.cbz_builder = CbzBuilder()
        # Cohérence avec deps.py / main.py : utiliser le singleton
        self.registry = ProviderRegistry.get_instance()
        self.active_jobs: Dict[str, Job] = {}
        self.job_callbacks: List = []
        self._tasks: Dict[str, asyncio.Task] = {}

    # ----------------------------------------------------------------------
    #  Callbacks
    # ----------------------------------------------------------------------

    def register_callback(self, callback) -> None:
        self.job_callbacks.append(callback)

    # ----------------------------------------------------------------------
    #  API publique
    # ----------------------------------------------------------------------

    async def analyze_url(self, url: str) -> Dict[str, Any]:
        provider = self.registry.get_provider_for_url(url)
        if not provider:
            raise ProviderError(f"Aucun provider trouvé pour l'URL : {url}")
        try:
            return await provider.analyze(url)
        except Exception as e:
            logger.error(f"Erreur analyse {url} : {e}", exc_info=True)
            raise ProviderError(f"Erreur lors de l'analyse : {e}")

    async def start_download(self, url: str, chapter_ids: List[str]) -> str:
        analysis = await self.analyze_url(url)
        provider = self.registry.get_provider_for_url(url)

        job_id = f"job_{int(datetime.now().timestamp())}"
        now_iso = datetime.now().isoformat()
        job = Job(
            id=job_id,
            url=url,
            status=JobStatus.PENDING,
            title=analysis.get("title", "unknown"),
            total_chapters=len(chapter_ids),
            done_chapters=0,
            progress=0.0,
            current_chapter="",
            logs=["Job créé"],
            created_at=now_iso,
            updated_at=now_iso,
        )
        self.active_jobs[job_id] = job
        await self._notify_job_update(job)

        # Conserver la référence de la tâche pour éviter le warning
        # "Task exception was never retrieved" et permettre l'annulation.
        task = asyncio.create_task(
            self._run_download(job_id, provider, analysis, chapter_ids),
            name=f"nexusdl-download-{job_id}",
        )
        self._tasks[job_id] = task
        task.add_done_callback(lambda t: self._tasks.pop(job_id, None))

        return job_id

    async def cancel_download(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            job = self.active_jobs.get(job_id)
            if job:
                job.status = JobStatus.CANCELLED if hasattr(JobStatus, "CANCELLED") else JobStatus.FAILED
                job.logs.append("🚫 Job annulé")
                await self._notify_job_update(job)
            return True
        return False

    # ----------------------------------------------------------------------
    #  Exécution
    # ----------------------------------------------------------------------

    async def _run_download(
        self,
        job_id: str,
        provider,
        analysis: Dict[str, Any],
        chapter_ids: List[str],
    ) -> None:
        job = self.active_jobs.get(job_id)
        if not job:
            return

        # ⚠️ temp_dir initialisé AVANT le try pour qu'il soit défini dans le
        #    finally, même en cas de return précoce (bug corrigé).
        temp_dir: Optional[Path] = None

        try:
            job.status = JobStatus.RUNNING
            job.logs.append("Démarrage du téléchargement...")
            await self._notify_job_update(job)

            chapters = analysis.get("chapters", [])
            selected_chapters = [c for c in chapters if c.get("id") in chapter_ids]

            if not selected_chapters:
                job.status = JobStatus.FAILED
                job.logs.append("Aucun chapitre sélectionné trouvé.")
                await self._notify_job_update(job)
                return

            temp_dir = settings.get_temp_path() / job_id
            temp_dir.mkdir(parents=True, exist_ok=True)

            all_images: List[Dict[str, Any]] = []
            total = len(selected_chapters)

            for idx, chapter in enumerate(selected_chapters):
                chapter_title = chapter.get("title", f"Chapitre {idx + 1}")
                job.current_chapter = chapter_title
                job.logs.append(f"Téléchargement : {chapter_title}")
                await self._notify_job_update(job)

                try:
                    images = await provider.get_chapter_images(chapter["id"])
                    image_paths = await self.downloader.download_images(
                        images,
                        temp_dir / f"chapter_{idx + 1:02d}",
                        referer=provider.base_url,
                    )
                    if image_paths:
                        all_images.append(
                            {"chapter_title": chapter_title, "images": image_paths}
                        )
                    else:
                        job.logs.append(f"⚠️ Aucune image pour « {chapter_title} »")
                except Exception as e:
                    job.logs.append(f"Erreur chapitre « {chapter_title} » : {e}")
                    logger.error(f"Erreur téléchargement chapitre : {e}", exc_info=True)

                job.done_chapters = idx + 1
                job.progress = (idx + 1) / total * 100
                await self._notify_job_update(job)

            if not all_images:
                job.status = JobStatus.FAILED
                job.logs.append("Aucune image téléchargée, abandon.")
                await self._notify_job_update(job)
                return

            job.logs.append("Construction du fichier CBZ...")
            await self._notify_job_update(job)

            cbz_path = await self.cbz_builder.build(
                title=analysis.get("title", "unknown"),
                chapters=all_images,
                output_dir=settings.get_download_path(),
                metadata={
                    "title": analysis.get("title"),
                    "author": analysis.get("author", ""),
                    "description": analysis.get("description", ""),
                },
            )

            await self._save_to_library(analysis, cbz_path)

            job.status = JobStatus.COMPLETED
            job.logs.append(f"✅ Terminé : {cbz_path.name}")
            job.progress = 100.0
            await self._notify_job_update(job)

        except asyncio.CancelledError:
            job.status = (
                JobStatus.CANCELLED
                if hasattr(JobStatus, "CANCELLED")
                else JobStatus.FAILED
            )
            job.logs.append("🚫 Job annulé")
            await self._notify_job_update(job)
            raise

        except Exception as e:
            logger.error(
                f"Erreur critique job {job_id} : {e}", exc_info=True
            )
            job.status = JobStatus.FAILED
            job.logs.append(f"❌ Erreur critique : {e}")
            await self._notify_job_update(job)

        finally:
            if temp_dir is not None and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(
                        f"Impossible de supprimer le dossier temporaire {temp_dir} : {e}"
                    )

    # ----------------------------------------------------------------------
    #  Notifications
    # ----------------------------------------------------------------------

    async def _notify_job_update(self, job: Job) -> None:
        job.updated_at = datetime.now().isoformat()
        for callback in self.job_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(job)
                else:
                    callback(job)
            except Exception as e:
                logger.error(f"Erreur dans un callback de job : {e}", exc_info=True)

    # ----------------------------------------------------------------------
    #  Bibliothèque
    # ----------------------------------------------------------------------

    async def _save_to_library(self, analysis: Dict[str, Any], cbz_path: Path) -> None:
        try:
            from app.services.file_service import FileService

            stat = cbz_path.stat()

            # ⚠️ `metadata` est un attribut réservé de SQLAlchemy.
            #    On utilise `extra_metadata` (ou le nom réel de la colonne
            #    dans ton modèle LibraryItem). À vérifier dans models/library.py.
            item = LibraryItem(
                title=analysis.get("title", "Sans titre"),
                filename=cbz_path.name,
                path=str(cbz_path),
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                extra_metadata={  # ← adapte au nom réel de ta colonne
                    "author": analysis.get("author", ""),
                    "description": analysis.get("description", ""),
                    "chapters": analysis.get("chapters", []),
                },
            )

            file_service = FileService()
            file_service.add_library_item(item)
            logger.info(f"📚 Élément ajouté à la bibliothèque : {item.title}")

        except Exception as e:
            logger.error(
                f"Erreur lors de l'enregistrement dans la bibliothèque : {e}",
                exc_info=True,
            )

    # ----------------------------------------------------------------------
    #  Arrêt
    # ----------------------------------------------------------------------

    async def close(self) -> None:
        # Annuler les tâches en cours
        for job_id, task in list(self._tasks.items()):
            if not task.done():
                task.cancel()
        await self.downloader.close()
