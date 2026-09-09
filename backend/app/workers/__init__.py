# ==========================================================================
#  NexusDL 2.0 - Package Workers
#  Fichier : backend/app/workers/__init__.py
# ==========================================================================

"""
Package contenant les workers et gestionnaires de tâches asynchrones de NexusDL.

Ce package expose :
- JobManager : Gestionnaire central des jobs de téléchargement
"""

from app.workers.job_manager import JobManager

__all__ = [
    "JobManager",
]
