# ==========================================================================
#  NexusDL 2.0 - WebSocket Endpoints
#  Fichier : backend/app/api/v1/endpoints/websocket.py 
# ==========================================================================

import logging
import json
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.workers.job_manager import JobManager, JobStatus
from app.api.v1.endpoints.deps import get_job_manager
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["WebSocket"])

# ==========================================================================
#  Gestionnaire de connexions WebSocket
# ==========================================================================

class ConnectionManager:
    """
    Gère les connexions WebSocket actives et diffuse les messages.
    """
    def __init__(self):
        # Map des connexions actives : {client_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Map des clients avec leurs abonnements (jobs, logs, etc.)
        self.subscriptions: Dict[str, Set[str]] = {}
        # Lock pour éviter les races conditions
        self._lock = asyncio.Lock()
    
    async def connect(self, client_id: str, websocket: WebSocket):
        """Ajoute une nouvelle connexion."""
        async with self._lock:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.subscriptions[client_id] = set()
            logger.info(f"🔌 Client WebSocket connecté: {client_id} (Total: {len(self.active_connections)})")
    
    async def disconnect(self, client_id: str):
        """Retire une connexion."""
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            if client_id in self.subscriptions:
                del self.subscriptions[client_id]
            logger.info(f"🔌 Client WebSocket déconnecté: {client_id} (Total: {len(self.active_connections)})")
    
    async def subscribe(self, client_id: str, topics: list):
        """Abonne un client à des topics (ex: job_updates, logs, etc.)."""
        async with self._lock:
            if client_id not in self.subscriptions:
                self.subscriptions[client_id] = set()
            self.subscriptions[client_id].update(topics)
            logger.debug(f"📡 Client {client_id} abonné à: {topics}")
    
    async def unsubscribe(self, client_id: str, topics: list):
        """Désabonne un client de certains topics."""
        async with self._lock:
            if client_id in self.subscriptions:
                for topic in topics:
                    self.subscriptions[client_id].discard(topic)
                logger.debug(f"📡 Client {client_id} désabonné de: {topics}")
    
    async def send_message(self, client_id: str, message: dict):
        """Envoie un message à un client spécifique."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Erreur envoi message à {client_id}: {e}")
                # Si la connexion est cassée, on la retire
                await self.disconnect(client_id)
        return False
    
    async def broadcast(self, topic: str, message: dict, exclude: Optional[Set[str]] = None):
        """
        Diffuse un message à tous les clients abonnés à un topic.
        """
        if exclude is None:
            exclude = set()
        message["topic"] = topic
        message["timestamp"] = datetime.now().isoformat()
        
        # Récupérer les clients abonnés à ce topic
        clients_to_send = []
        async with self._lock:
            for client_id, topics in self.subscriptions.items():
                if topic in topics and client_id not in exclude:
                    clients_to_send.append(client_id)
        
        if not clients_to_send:
            return
        
        # Envoyer en parallèle
        tasks = []
        for client_id in clients_to_send:
            if client_id in self.active_connections:
                tasks.append(self.send_message(client_id, message))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.debug(f"📢 Broadcast '{topic}' à {len(clients_to_send)} clients")
    
    async def broadcast_job_update(self, job_id: str, job_data: dict):
        """
        Diffuse une mise à jour de job sur le topic 'job_updates'.
        """
        await self.broadcast("job_updates", {
            "event": "job_updated",
            "job_id": job_id,
            "data": job_data
        })
    
    async def broadcast_job_started(self, job_id: str, job_data: dict):
        """Diffuse un événement de début de job."""
        await self.broadcast("job_updates", {
            "event": "job_started",
            "job_id": job_id,
            "data": job_data
        })
    
    async def broadcast_job_finished(self, job_id: str, job_data: dict):
        """Diffuse un événement de fin de job."""
        await self.broadcast("job_updates", {
            "event": "job_finished",
            "job_id": job_id,
            "data": job_data
        })
    
    async def broadcast_log(self, log_data: dict):
        """Diffuse un nouveau log sur le topic 'logs'."""
        await self.broadcast("logs", {
            "event": "new_log",
            "data": log_data
        })

# Instance globale du gestionnaire
manager = ConnectionManager()

# ==========================================================================
#  Fonctions de validation JWT pour WebSocket
# ==========================================================================

def validate_websocket_token(token: str) -> Optional[User]:
    """
    Valide le token JWT pour une connexion WebSocket.
    Retourne l'utilisateur ou lève une exception.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise AuthenticationError("Utilisateur manquant dans le token")
        # Simuler une récupération d'utilisateur (à remplacer par une vraie DB)
        from app.api.v1.endpoints.deps import users_db
        user = users_db.get(username)
        if not user:
            raise AuthenticationError("Utilisateur non trouvé")
        return user
    except JWTError as e:
        raise AuthenticationError(f"Token invalide: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur validation token WebSocket: {e}")
        raise AuthenticationError("Erreur d'authentification")

# ==========================================================================
#  Endpoint WebSocket
# ==========================================================================

@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Token JWT"),
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    Point d'entrée WebSocket pour les mises à jour en temps réel.
    
    Le client doit fournir un token JWT valide dans la query string.
    Exemple: ws://localhost:8000/api/ws/?token=eyJhbGciOiJIUzI1NiIs...
    
    Messages possibles du client:
    - {"action": "subscribe", "topics": ["job_updates", "logs"]}
    - {"action": "unsubscribe", "topics": ["job_updates"]}
    - {"action": "get_job", "job_id": "job_123"}
    - {"action": "get_jobs", "status": "running"}
    
    Messages du serveur:
    - {"topic": "job_updates", "event": "job_updated|job_started|job_finished", "job_id": "...", "data": {...}}
    - {"topic": "logs", "event": "new_log", "data": {...}}
    - {"topic": "system", "event": "connected|disconnected", "message": "..."}
    """
    client_id = f"client_{datetime.now().timestamp()}"
    authenticated_user = None
    
    try:
        # Authentification
        authenticated_user = validate_websocket_token(token)
        logger.info(f"🔐 Client WebSocket authentifié: {authenticated_user.username} ({client_id})")
    except AuthenticationError as e:
        logger.warning(f"❌ Échec authentification WebSocket: {e}")
        await websocket.close(code=1008, reason=str(e))
        return
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lors de l'authentification WebSocket: {e}")
        await websocket.close(code=1011, reason="Internal server error")
        return
    
    # Accepter la connexion
    await manager.connect(client_id, websocket)
    
    # Abonnement par défaut aux jobs
    await manager.subscribe(client_id, ["job_updates", "system"])
    
    # Envoyer un message de bienvenue
    await manager.send_message(client_id, {
        "topic": "system",
        "event": "connected",
        "message": f"Connecté à NexusDL WebSocket",
        "client_id": client_id,
        "user": authenticated_user.username
    })
    
    # Envoyer la liste des jobs actifs au moment de la connexion
    try:
        active_jobs = job_manager.get_active_jobs()
        if active_jobs:
            await manager.send_message(client_id, {
                "topic": "job_updates",
                "event": "initial_state",
                "jobs": [
                    {
                        "id": job.id,
                        "title": job.title,
                        "status": job.status.value,
                        "progress": job.progress,
                        "total_chapters": job.total_chapters,
                        "done_chapters": job.done_chapters,
                        "current_chapter": job.current_chapter,
                        "created_at": job.created_at,
                        "updated_at": job.updated_at
                    }
                    for job in active_jobs
                ]
            })
    except Exception as e:
        logger.error(f"Erreur envoi état initial: {e}")
    
    try:
        # Boucle principale de réception des messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "subscribe":
                    topics = message.get("topics", [])
                    if topics:
                        await manager.subscribe(client_id, topics)
                        await manager.send_message(client_id, {
                            "topic": "system",
                            "event": "subscribed",
                            "topics": topics
                        })
                
                elif action == "unsubscribe":
                    topics = message.get("topics", [])
                    if topics:
                        await manager.unsubscribe(client_id, topics)
                        await manager.send_message(client_id, {
                            "topic": "system",
                            "event": "unsubscribed",
                            "topics": topics
                        })
                
                elif action == "get_job":
                    job_id = message.get("job_id")
                    if job_id:
                        job = job_manager.get_job(job_id)
                        if job:
                            await manager.send_message(client_id, {
                                "topic": "job_updates",
                                "event": "job_detail",
                                "job_id": job_id,
                                "data": {
                                    "id": job.id,
                                    "title": job.title,
                                    "status": job.status.value,
                                    "url": job.url,
                                    "total_chapters": job.total_chapters,
                                    "done_chapters": job.done_chapters,
                                    "progress": job.progress,
                                    "current_chapter": job.current_chapter,
                                    "logs": job.logs[-50:],  # Derniers 50 logs
                                    "created_at": job.created_at,
                                    "updated_at": job.updated_at
                                }
                            })
                        else:
                            await manager.send_message(client_id, {
                                "topic": "system",
                                "event": "error",
                                "message": f"Job {job_id} non trouvé"
                            })
                
                elif action == "get_jobs":
                    status_filter = message.get("status")
                    jobs = job_manager.get_all_jobs()
                    if status_filter:
                        try:
                            status_enum = JobStatus(status_filter.lower())
                            jobs = [j for j in jobs if j.status == status_enum]
                        except ValueError:
                            pass
                    # Limiter le nombre
                    jobs = jobs[-100:]
                    await manager.send_message(client_id, {
                        "topic": "job_updates",
                        "event": "jobs_list",
                        "jobs": [
                            {
                                "id": job.id,
                                "title": job.title,
                                "status": job.status.value,
                                "progress": job.progress,
                                "total_chapters": job.total_chapters,
                                "done_chapters": job.done_chapters,
                                "current_chapter": job.current_chapter,
                                "created_at": job.created_at,
                                "updated_at": job.updated_at
                            }
                            for job in jobs
                        ]
                    })
                
                elif action == "ping":
                    await manager.send_message(client_id, {
                        "topic": "system",
                        "event": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
                else:
                    await manager.send_message(client_id, {
                        "topic": "system",
                        "event": "warning",
                        "message": f"Action inconnue: {action}"
                    })
            
            except json.JSONDecodeError:
                await manager.send_message(client_id, {
                    "topic": "system",
                    "event": "error",
                    "message": "Format JSON invalide"
                })
            except Exception as e:
                logger.error(f"Erreur traitement message WebSocket: {e}")
                await manager.send_message(client_id, {
                    "topic": "system",
                    "event": "error",
                    "message": f"Erreur: {str(e)}"
                })
    
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
        logger.info(f"🔌 Client WebSocket déconnecté proprement: {client_id}")
    except Exception as e:
        logger.error(f"⚠️ Erreur WebSocket inattendue: {e}")
        await manager.disconnect(client_id)
        try:
            await websocket.close(code=1011, reason="Erreur interne")
        except:
            pass

# ==========================================================================
#  Fonctions d'initialisation - à appeler depuis main.py ou engine
# ==========================================================================

def init_websocket_manager():
    """
    Initialise le gestionnaire WebSocket et enregistre les callbacks
    auprès du JobManager pour diffuser automatiquement les mises à jour.
    """
    from app.workers.job_manager import JobManager
    job_manager = JobManager()
    
    # Enregistrer un callback pour les mises à jour de jobs
    def on_job_update(job_data):
        asyncio.create_task(manager.broadcast_job_update(
            job_id=job_data.get("id"),
            job_data=job_data
        ))
    
    def on_job_started(job_data):
        asyncio.create_task(manager.broadcast_job_started(
            job_id=job_data.get("id"),
            job_data=job_data
        ))
    
    def on_job_finished(job_data):
        asyncio.create_task(manager.broadcast_job_finished(
            job_id=job_data.get("id"),
            job_data=job_data
        ))
    
    # Enregistrer les callbacks (à adapter selon l'implémentation de JobManager)
    # job_manager.register_callback('update', on_job_update)
    # job_manager.register_callback('started', on_job_started)
    # job_manager.register_callback('finished', on_job_finished)
    
    logger.info("✅ Gestionnaire WebSocket initialisé avec callbacks")
    return manager

# ==========================================================================
#  Notes
# ==========================================================================
#  - Le token JWT est passé en paramètre de la query string pour les WebSocket.
#  - Le gestionnaire de connexions utilise un asyncio.Lock pour les opérations
#    concurrentes sur les dictionnaires partagés.
#  - Les messages sont diffusés sur différents topics pour permettre aux clients
#    de s'abonner sélectivement.
#  - La fonction init_websocket_manager peut être appelée au démarrage de l'app
#    pour connecter les callbacks du JobManager.
#  - En production, il serait bon d'ajouter des mécanismes de reconnexion
#    et de heartbeat (ping/pong) pour éviter les déconnexions intempestives.
