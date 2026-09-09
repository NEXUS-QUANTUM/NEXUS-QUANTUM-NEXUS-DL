# ==========================================================================
#  NexusDL 2.0 - Gestionnaire de Jobs
#  Fichier : backend/app/workers/job_manager.py
# ==========================================================================

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Callable, Awaitable
from datetime import datetime
from enum import Enum

from app.core.exceptions import JobNotFoundError, JobCancelError
from app.models.job import JobStatus, JobPriority, JobType, JobInMemory

logger = logging.getLogger(__name__)


class JobManager:
    """
    Gestionnaire de jobs de téléchargement.
    Crée, suit, met à jour et annule les jobs.
    Notifie les callbacks enregistrés des changements d'état.
    """

    def __init__(self):
        # Stockage des jobs actifs et historiques
        self._jobs: Dict[str, JobInMemory] = {}
        # Callbacks organisés par type d'événement
        self._callbacks: Dict[str, List[Callable]] = {
            "created": [],
            "updated": [],
            "started": [],
            "completed": [],
            "failed": [],
            "cancelled": [],
            "progress": []
        }
        self._lock = asyncio.Lock()
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Démarre le gestionnaire de jobs."""
        if self._running:
            return
        self._running = True
        # Tâche de nettoyage périodique des jobs terminés (optionnelle)
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("✅ JobManager démarré")

    async def stop(self):
        """Arrête le gestionnaire de jobs."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        logger.info("✅ JobManager arrêté")

    # ==========================================================================
    #  Création et gestion des jobs
    # ==========================================================================

    async def create_job(
        self,
        title: str,
        url: str,
        provider_id: str,
        chapter_ids: List[str],
        total_chapters: int,
        priority: JobPriority = JobPriority.NORMAL,
        job_type: JobType = JobType.DOWNLOAD,
        user_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Crée un nouveau job et le place en attente.
        Retourne l'ID du job créé.
        """
        job_id = f"job_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
        job = JobInMemory(
            job_id=job_id,
            title=title,
            url=url,
            type=job_type,
            priority=priority,
            total_chapters=total_chapters,
            user_id=user_id,
            data=data or {}
        )
        job.provider_id = provider_id
        job.status = JobStatus.PENDING
        job.created_at = datetime.now().isoformat()
        job.updated_at = job.created_at

        async with self._lock:
            self._jobs[job_id] = job

        # Notifier la création
        await self._notify("created", job)
        await self._notify("updated", job)
        logger.info(f"📦 Job créé: {job_id} - {title}")
        return job_id

    async def get_job(self, job_id: str) -> Optional[JobInMemory]:
        """Récupère un job par son ID."""
        async with self._lock:
            return self._jobs.get(job_id)

    async def get_all_jobs(
        self,
        status_filter: Optional[JobStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[JobInMemory]:
        """
        Récupère tous les jobs, avec filtrage optionnel par statut.
        """
        async with self._lock:
            jobs = list(self._jobs.values())
            if status_filter:
                jobs = [j for j in jobs if j.status == status_filter]
            # Trier par date de création décroissante
            jobs.sort(key=lambda j: j.created_at, reverse=True)
            return jobs[offset:offset + limit]

    async def get_active_jobs(self) -> List[JobInMemory]:
        """Récupère les jobs en cours d'exécution ou en attente."""
        async with self._lock:
            return [j for j in self._jobs.values() if j.is_active()]

    # ==========================================================================
    #  Mises à jour des jobs
    # ==========================================================================

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        progress: Optional[float] = None,
        done_chapters: Optional[int] = None,
        current_chapter: Optional[str] = None,
        logs: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        result_path: Optional[str] = None,
        result_size: Optional[int] = None
    ) -> bool:
        """
        Met à jour le statut et les métadonnées d'un job.
        Déclenche les notifications appropriées.
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        old_status = job.status
        job.status = status
        job.updated_at = datetime.now().isoformat()

        if progress is not None:
            job.progress = progress
        if done_chapters is not None:
            job.done_chapters = done_chapters
        if current_chapter is not None:
            job.current_chapter = current_chapter
        if logs is not None:
            job.logs = logs
        if errors is not None:
            job.errors = errors
        if result_path is not None:
            job.result_path = result_path
        if result_size is not None:
            job.result_size = result_size

        # Gestion des dates de début/fin
        if status == JobStatus.RUNNING and old_status != JobStatus.RUNNING:
            job.started_at = datetime.now().isoformat()
        if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            if status == JobStatus.COMPLETED:
                job.completed_at = datetime.now().isoformat()
            elif status == JobStatus.FAILED:
                job.completed_at = datetime.now().isoformat()  # ou échec
            elif status == JobStatus.CANCELLED:
                job.cancelled_at = datetime.now().isoformat()
            # Nettoyer le job (optionnel)
            # On peut garder en mémoire pour l'historique

        await self._notify("updated", job)
        if status != old_status:
            if status == JobStatus.RUNNING:
                await self._notify("started", job)
            elif status == JobStatus.COMPLETED:
                await self._notify("completed", job)
            elif status == JobStatus.FAILED:
                await self._notify("failed", job)
            elif status == JobStatus.CANCELLED:
                await self._notify("cancelled", job)

        # Notification de progression si le pourcentage a changé significativement
        if progress is not None and abs(progress - job.progress) > 1.0:
            await self._notify("progress", job)

        logger.debug(f"🔄 Job {job_id} mis à jour: {status.value} (progress: {job.progress:.1f}%)")
        return True

    async def update_progress(
        self,
        job_id: str,
        done_chapters: int,
        total_chapters: Optional[int] = None,
        current_chapter: Optional[str] = None
    ):
        """
        Met à jour la progression d'un job sans changer le statut.
        """
        job = await self.get_job(job_id)
        if not job:
            return
        job.done_chapters = done_chapters
        if total_chapters is not None:
            job.total_chapters = total_chapters
        if total_chapters and total_chapters > 0:
            job.progress = (done_chapters / total_chapters) * 100
        if current_chapter is not None:
            job.current_chapter = current_chapter
        job.updated_at = datetime.now().isoformat()
        await self._notify("progress", job)
        await self._notify("updated", job)

    async def add_log(self, job_id: str, message: str, level: str = "info"):
        """Ajoute un message de log à un job."""
        job = await self.get_job(job_id)
        if not job:
            return
        if job.logs is None:
            job.logs = []
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        job.logs.append(log_entry)
        # Limiter la taille des logs (conserver les 500 derniers)
        if len(job.logs) > 500:
            job.logs = job.logs[-500:]
        job.updated_at = datetime.now().isoformat()
        await self._notify("updated", job)

    # ==========================================================================
    #  Annulation des jobs
    # ==========================================================================

    async def cancel_job(self, job_id: str, force: bool = False) -> bool:
        """
        Annule un job en cours d'exécution ou en attente.
        Si force=True, annule même si le job est en cours de traitement.
        """
        job = await self.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id=job_id)

        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            raise JobCancelError(f"Le job {job_id} est déjà dans un état terminal.")

        if job.status == JobStatus.RUNNING and not force:
            raise JobCancelError(
                f"Le job {job_id} est en cours d'exécution. Utilisez force=True pour l'annuler."
            )

        # Mettre à jour le statut
        await self.update_job_status(job_id, JobStatus.CANCELLED)
        logger.info(f"⛔ Job annulé: {job_id}")
        return True

    # ==========================================================================
    #  Gestion des callbacks
    # ==========================================================================

    def register_callback(self, event: str, callback: Callable[[JobInMemory], Awaitable[None]]):
        """
        Enregistre un callback pour un événement donné.
        Événements possibles: 'created', 'updated', 'started', 'completed', 'failed', 'cancelled', 'progress'
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)
        else:
            raise ValueError(f"Événement inconnu: {event}")

    def unregister_callback(self, event: str, callback: Callable):
        """
        Supprime un callback enregistré.
        """
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)

    async def _notify(self, event: str, job: JobInMemory):
        """
        Notifie tous les callbacks enregistrés pour un événement.
        """
        if event not in self._callbacks:
            return
        for cb in self._callbacks[event]:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(job)
                else:
                    # Si le callback est synchrone, l'exécuter dans un thread
                    import concurrent.futures
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, cb, job)
            except Exception as e:
                logger.error(f"Erreur dans le callback {event}: {e}")

    # ==========================================================================
    #  Maintenance
    # ==========================================================================

    async def _cleanup_loop(self):
        """Nettoie périodiquement les jobs terminés (optionnel)."""
        while self._running:
            await asyncio.sleep(3600)  # toutes les heures
            # Supprimer les jobs terminés depuis plus de 7 jours (exemple)
            # Ou les déplacer vers une base de données d'historique
            # Ici on ne les supprime pas pour simplifier
            pass

    async def cleanup_old_jobs(self, days: int = 7):
        """
        Supprime les jobs terminés depuis plus de `days` jours.
        À utiliser pour libérer de la mémoire.
        """
        cutoff = datetime.now().timestamp() - (days * 86400)
        to_delete = []
        async with self._lock:
            for job_id, job in self._jobs.items():
                if job.is_finished():
                    # Vérifier la date de complétion (utiliser completed_at ou updated_at)
                    completion_time = job.completed_at or job.updated_at
                    if completion_time:
                        try:
                            dt = datetime.fromisoformat(completion_time)
                            if dt.timestamp() < cutoff:
                                to_delete.append(job_id)
                        except (ValueError, TypeError):
                            pass
            for job_id in to_delete:
                del self._jobs[job_id]
        logger.info(f"Nettoyage : {len(to_delete)} jobs supprimés (plus de {days} jours)")
        return len(to_delete)

    # ==========================================================================
    #  Utilitaires
    # ==========================================================================

    def get_stats(self) -> Dict[str, int]:
        """Retourne des statistiques sur les jobs."""
        async with self._lock:
            total = len(self._jobs)
            pending = sum(1 for j in self._jobs.values() if j.status == JobStatus.PENDING)
            running = sum(1 for j in self._jobs.values() if j.status == JobStatus.RUNNING)
            completed = sum(1 for j in self._jobs.values() if j.status == JobStatus.COMPLETED)
            failed = sum(1 for j in self._jobs.values() if j.status == JobStatus.FAILED)
            cancelled = sum(1 for j in self._jobs.values() if j.status == JobStatus.CANCELLED)
            return {
                "total": total,
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "cancelled": cancelled
            }
