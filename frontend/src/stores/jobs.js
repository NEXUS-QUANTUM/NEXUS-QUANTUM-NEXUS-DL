// ==========================================================================
//  NexusDL 2.0 - Jobs Store (Pinia)
//  Fichier : frontend/src/stores/jobs.js
//  Description : Store pour la gestion des jobs de téléchargement
//  Version : 2.0.0
// ==========================================================================

import { defineStore } from 'pinia'
import { ref, computed, watch, shallowRef } from 'vue'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useAppStore } from '@/stores/app'

/**
 * Store pour gérer les jobs de téléchargement (file d'attente).
 * Fournit les actions pour lister, créer, mettre à jour, annuler,
 * et suivre les jobs en temps réel via WebSocket.
 */
export const useJobsStore = defineStore('jobs', () => {
  // ==========================================================================
  //  Dépendances
  // ==========================================================================

  const api = useApi()
  const toast = useToast()
  const appStore = useAppStore()

  // ==========================================================================
  //  État
  // ==========================================================================

  /** Liste de tous les jobs (clé: job_id) */
  const jobs = ref({})
  /** IDs des jobs actifs (en attente, en cours) */
  const activeJobIds = ref([])
  /** Indicateur de chargement */
  const isLoading = ref(false)
  /** Erreur globale */
  const error = ref(null)
  /** Dernière mise à jour */
  const lastUpdated = ref(null)
  /** Connexion WebSocket active ? */
  const wsConnected = ref(false)
  /** Tentative de reconnexion WebSocket */
  let wsReconnectTimer = null
  let wsInstance = null
  const wsReconnectAttempts = ref(0)
  const MAX_WS_RECONNECT = 5

  // ==========================================================================
  //  Getters
  // ==========================================================================

  /** Liste des jobs (tableau) */
  const jobsList = computed(() => Object.values(jobs.value))

  /** Jobs actifs (en attente ou en cours) */
  const activeJobs = computed(() =>
    jobsList.value.filter(job => job.status === 'pending' || job.status === 'running' || job.status === 'waiting')
  )

  /** Jobs terminés (succès, échec, annulé) */
  const completedJobs = computed(() =>
    jobsList.value.filter(job => job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled')
  )

  /** Jobs en cours d'exécution */
  const runningJobs = computed(() => jobsList.value.filter(job => job.status === 'running'))

  /** Jobs en attente */
  const pendingJobs = computed(() => jobsList.value.filter(job => job.status === 'pending'))

  /** Nombre total de jobs */
  const totalJobs = computed(() => jobsList.value.length)

  /** Nombre de jobs actifs */
  const activeCount = computed(() => activeJobs.value.length)

  /** Nombre de jobs en cours */
  const runningCount = computed(() => runningJobs.value.length)

  /** Progression globale (moyenne des progress des jobs actifs) */
  const overallProgress = computed(() => {
    if (activeJobs.value.length === 0) return 0
    const total = activeJobs.value.reduce((acc, job) => acc + (job.progress || 0), 0)
    return Math.round(total / activeJobs.value.length)
  })

  /** Vérifie si un job est actif */
  const isJobActive = (jobId) => activeJobIds.value.includes(jobId)

  /** Récupère un job par son ID */
  const getJob = (jobId) => jobs.value[jobId] || null

  /** Jobs triés par date de création (plus récent en premier) */
  const sortedJobs = computed(() =>
    [...jobsList.value].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  )

  // ==========================================================================
  //  Actions
  // ==========================================================================

  // --------------------------------------------------------------------------
  //  Récupération des jobs
  // --------------------------------------------------------------------------

  /**
   * Récupère la liste des jobs depuis l'API.
   * @param {Object} params - Paramètres de filtrage (status, limit, offset)
   * @returns {Promise<Array>} - Liste des jobs
   */
  async function fetchJobs(params = {}) {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get('/downloads/jobs', { params })
      // La réponse peut être un tableau ou un objet paginé
      let jobsArray = Array.isArray(response) ? response : (response.items || response.jobs || [])
      // Mettre à jour le store
      const newJobs = {}
      for (const job of jobsArray) {
        newJobs[job.id] = normalizeJob(job)
      }
      jobs.value = newJobs
      updateActiveIds()
      lastUpdated.value = new Date().toISOString()
      return jobsArray
    } catch (err) {
      error.value = err
      toast.error(`Erreur lors du chargement des jobs: ${err.message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Récupère un job spécifique par son ID.
   * @param {string} jobId - ID du job
   * @param {boolean} force - Forcer la récupération depuis le serveur
   * @returns {Promise<Object>} - Données du job
   */
  async function fetchJob(jobId, force = false) {
    if (!jobId) return null
    // Si déjà présent et pas force, retourner depuis le cache
    if (!force && jobs.value[jobId]) {
      return jobs.value[jobId]
    }
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get(`/downloads/jobs/${jobId}`)
      const job = normalizeJob(response)
      jobs.value[jobId] = job
      updateActiveIds()
      lastUpdated.value = new Date().toISOString()
      return job
    } catch (err) {
      error.value = err
      if (err.response?.status === 404) {
        // Job supprimé, on le retire du store
        delete jobs.value[jobId]
        updateActiveIds()
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Rafraîchit la liste des jobs actifs uniquement.
   * @returns {Promise<Array>} - Jobs actifs
   */
  async function refreshActiveJobs() {
    try {
      const response = await api.get('/downloads/jobs', { params: { status: 'pending,running,waiting' } })
      let jobsArray = Array.isArray(response) ? response : (response.items || response.jobs || [])
      for (const job of jobsArray) {
        const normalized = normalizeJob(job)
        // Mettre à jour ou ajouter
        jobs.value[normalized.id] = normalized
      }
      updateActiveIds()
      lastUpdated.value = new Date().toISOString()
      return jobsArray
    } catch (err) {
      console.warn('Erreur refreshActiveJobs:', err)
      return []
    }
  }

  // --------------------------------------------------------------------------
  //  Création et lancement
  // --------------------------------------------------------------------------

  /**
   * Lance un nouveau téléchargement.
   * @param {string} url - URL de la série ou du chapitre
   * @param {Array<string>} chapterIds - IDs des chapitres à télécharger
   * @param {Object} options - Options supplémentaires
   * @returns {Promise<Object>} - Job créé
   */
  async function startDownload(url, chapterIds, options = {}) {
    if (!url || !chapterIds || chapterIds.length === 0) {
      toast.error('URL et chapitres requis.', '❌')
      throw new Error('URL et chapitres requis')
    }

    isLoading.value = true
    error.value = null
    appStore.startLoading('Lancement du téléchargement...')

    try {
      const payload = { url, chapter_ids: chapterIds, options }
      const response = await api.post('/downloads/', payload)
      // La réponse contient généralement job_id et statut
      const { job_id, title, status, total_chapters } = response
      // Créer un job localement avec les données reçues
      const newJob = {
        id: job_id,
        title: title || 'Téléchargement',
        url,
        status: status || 'pending',
        total_chapters: total_chapters || chapterIds.length,
        done_chapters: 0,
        progress: 0,
        current_chapter: '',
        logs: ['Job créé'],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      jobs.value[job_id] = normalizeJob(newJob)
      updateActiveIds()
      toast.success(`Téléchargement de "${title}" ajouté à la file d'attente.`, '✅')
      return jobs.value[job_id]
    } catch (err) {
      error.value = err
      toast.error(`Erreur lors du lancement: ${err.message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
      appStore.stopLoading()
    }
  }

  // --------------------------------------------------------------------------
  //  Annulation
  // --------------------------------------------------------------------------

  /**
   * Annule un job en cours.
   * @param {string} jobId - ID du job
   * @param {boolean} force - Forcer l'annulation
   * @returns {Promise<boolean>}
   */
  async function cancelJob(jobId, force = false) {
    const job = jobs.value[jobId]
    if (!job) {
      toast.warning('Job non trouvé.', '⚠️')
      return false
    }
    if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
      toast.warning('Ce job est déjà terminé.', '⚠️')
      return false
    }

    isLoading.value = true
    error.value = null

    try {
      await api.delete(`/downloads/jobs/${jobId}`, { params: { force } })
      // Mettre à jour le statut localement
      jobs.value[jobId].status = 'cancelled'
      jobs.value[jobId].updated_at = new Date().toISOString()
      updateActiveIds()
      toast.info(`Job "${job.title}" annulé.`, '⛔')
      return true
    } catch (err) {
      error.value = err
      toast.error(`Erreur lors de l'annulation: ${err.message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Annule tous les jobs actifs.
   * @param {boolean} force - Forcer l'annulation
   * @returns {Promise<number>} - Nombre de jobs annulés
   */
  async function cancelAllActive(force = false) {
    const active = activeJobs.value
    if (active.length === 0) {
      toast.info('Aucun job actif à annuler.', 'ℹ️')
      return 0
    }
    let cancelled = 0
    for (const job of active) {
      try {
        const success = await cancelJob(job.id, force)
        if (success) cancelled++
      } catch (_) {
        // Ignorer les erreurs individuelles
      }
    }
    toast.info(`${cancelled} job(s) annulé(s).`, '⛔')
    return cancelled
  }

  // --------------------------------------------------------------------------
  //  Mise à jour et progression
  // --------------------------------------------------------------------------

  /**
   * Met à jour un job localement (utilisé par WebSocket ou polling).
   * @param {Object} jobData - Données du job
   */
  function updateJob(jobData) {
    if (!jobData || !jobData.id) return
    const existing = jobs.value[jobData.id]
    const normalized = normalizeJob(jobData)
    if (existing) {
      // Fusionner les propriétés
      jobs.value[jobData.id] = { ...existing, ...normalized }
    } else {
      jobs.value[jobData.id] = normalized
    }
    updateActiveIds()
    lastUpdated.value = new Date().toISOString()

    // Afficher des notifications pour les changements d'état
    const status = normalized.status
    const title = normalized.title || 'Job'
    if (status === 'completed' && existing?.status !== 'completed') {
      toast.success(`"${title}" terminé avec succès ! 🎉`)
    } else if (status === 'failed' && existing?.status !== 'failed') {
      toast.error(`"${title}" a échoué.`, '❌')
    } else if (status === 'cancelled' && existing?.status !== 'cancelled') {
      toast.info(`"${title}" annulé.`, '⛔')
    } else if (status === 'running' && existing?.status !== 'running') {
      // Pas de notification pour le démarrage pour éviter le spam
    }
  }

  /**
   * Met à jour la progression d'un job.
   * @param {string} jobId - ID du job
   * @param {number} progress - Progression (0-100)
   * @param {number} doneChapters - Chapitres terminés
   * @param {string} currentChapter - Chapitre en cours
   */
  function updateProgress(jobId, progress, doneChapters, currentChapter) {
    const job = jobs.value[jobId]
    if (!job) return
    job.progress = Math.min(100, Math.max(0, progress))
    if (doneChapters !== undefined) job.done_chapters = doneChapters
    if (currentChapter !== undefined) job.current_chapter = currentChapter
    job.updated_at = new Date().toISOString()
    // Pas besoin de updateActiveIds car le statut ne change pas
  }

  /**
   * Ajoute un log à un job.
   * @param {string} jobId - ID du job
   * @param {string} message - Message de log
   * @param {string} level - Niveau ('info', 'warning', 'error')
   */
  function addJobLog(jobId, message, level = 'info') {
    const job = jobs.value[jobId]
    if (!job) return
    if (!job.logs) job.logs = []
    job.logs.push({
      timestamp: new Date().toISOString(),
      level,
      message,
    })
    // Limiter la taille des logs (500 entrées)
    if (job.logs.length > 500) {
      job.logs = job.logs.slice(-500)
    }
    job.updated_at = new Date().toISOString()
  }

  // --------------------------------------------------------------------------
  //  Nettoyage
  // --------------------------------------------------------------------------

  /**
   * Supprime un job de la liste (localement).
   * @param {string} jobId - ID du job
   */
  function removeJob(jobId) {
    if (jobs.value[jobId]) {
      delete jobs.value[jobId]
      updateActiveIds()
      lastUpdated.value = new Date().toISOString()
    }
  }

  /**
   * Supprime les jobs terminés de la liste.
   * @param {number} olderThanDays - Supprimer les jobs terminés depuis plus de X jours
   */
  function clearCompletedJobs(olderThanDays = 7) {
    const cutoff = new Date()
    cutoff.setDate(cutoff.getDate() - olderThanDays)
    const toRemove = []
    for (const [id, job] of Object.entries(jobs.value)) {
      if (['completed', 'failed', 'cancelled'].includes(job.status)) {
        const completedAt = job.completed_at || job.updated_at || job.created_at
        if (completedAt && new Date(completedAt) < cutoff) {
          toRemove.push(id)
        }
      }
    }
    for (const id of toRemove) {
      delete jobs.value[id]
    }
    if (toRemove.length > 0) {
      updateActiveIds()
      lastUpdated.value = new Date().toISOString()
      toast.info(`${toRemove.length} job(s) ancien(s) nettoyé(s).`, '🧹')
    }
  }

  // ==========================================================================
  //  Utilitaires
  // ==========================================================================

  /**
   * Normalise les données d'un job pour assurer une structure cohérente.
   * @param {Object} raw - Données brutes du job
   * @returns {Object} - Job normalisé
   */
  function normalizeJob(raw) {
    if (!raw) return null
    return {
      id: raw.id || raw.job_id || '',
      title: raw.title || 'Sans titre',
      url: raw.url || '',
      status: raw.status || 'pending',
      progress: typeof raw.progress === 'number' ? Math.min(100, Math.max(0, raw.progress)) : 0,
      total_chapters: raw.total_chapters || 0,
      done_chapters: raw.done_chapters || 0,
      current_chapter: raw.current_chapter || '',
      logs: Array.isArray(raw.logs) ? raw.logs : [],
      errors: Array.isArray(raw.errors) ? raw.errors : [],
      created_at: raw.created_at || new Date().toISOString(),
      updated_at: raw.updated_at || new Date().toISOString(),
      started_at: raw.started_at || null,
      completed_at: raw.completed_at || null,
      cancelled_at: raw.cancelled_at || null,
      provider_id: raw.provider_id || null,
      result_path: raw.result_path || null,
      result_size: raw.result_size || null,
    }
  }

  /**
   * Met à jour la liste des IDs de jobs actifs.
   */
  function updateActiveIds() {
    const ids = []
    for (const [id, job] of Object.entries(jobs.value)) {
      if (job.status === 'pending' || job.status === 'running' || job.status === 'waiting') {
        ids.push(id)
      }
    }
    activeJobIds.value = ids
  }

  // ==========================================================================
  //  WebSocket (pour les mises à jour en temps réel)
  // ==========================================================================

  /**
   * Initialise la connexion WebSocket pour les mises à jour en temps réel.
   * @param {string} token - Token JWT (optionnel, utilise le store auth)
   */
  function initWebSocket(token) {
    // Fermer l'ancienne connexion
    closeWebSocket()

    // Récupérer le token si non fourni
    let authToken = token
    if (!authToken) {
      try {
        const authStore = useAuthStore()
        authToken = authStore.token
      } catch (_) {}
    }
    if (!authToken) {
      console.warn('⚠️ WebSocket: Pas de token JWT, connexion impossible.')
      return
    }

    // Construire l'URL WebSocket (protocole ws/wss)
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.host
    const wsBase = import.meta.env.VITE_WS_BASE || `${wsProtocol}//${wsHost}/api/ws`
    const wsUrl = `${wsBase}?token=${encodeURIComponent(authToken)}`

    wsReconnectAttempts.value = 0

    try {
      wsInstance = new WebSocket(wsUrl)

      wsInstance.onopen = () => {
        wsConnected.value = true
        wsReconnectAttempts.value = 0
        console.log('🔌 WebSocket connecté.')
        // S'abonner aux mises à jour de jobs
        sendWsMessage({ action: 'subscribe', topics: ['job_updates'] })
      }

      wsInstance.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleWsMessage(data)
        } catch (err) {
          console.warn('⚠️ WebSocket message invalide:', err)
        }
      }

      wsInstance.onclose = (event) => {
        wsConnected.value = false
        console.log(`🔌 WebSocket fermé (code: ${event.code})`)
        // Tentative de reconnexion si ce n'est pas une fermeture intentionnelle
        if (event.code !== 1000 && event.code !== 1001) {
          scheduleReconnect()
        }
      }

      wsInstance.onerror = (err) => {
        console.error('❌ WebSocket erreur:', err)
        wsConnected.value = false
        // On laisse le onclose gérer la reconnexion
      }
    } catch (err) {
      console.error('❌ WebSocket init error:', err)
      scheduleReconnect()
    }
  }

  /**
   * Envoie un message via WebSocket.
   * @param {Object} message - Message à envoyer
   * @returns {boolean} - true si envoyé
   */
  function sendWsMessage(message) {
    if (!wsInstance || wsInstance.readyState !== WebSocket.OPEN) {
      console.warn('⚠️ WebSocket non connecté.')
      return false
    }
    try {
      wsInstance.send(JSON.stringify(message))
      return true
    } catch (err) {
      console.error('❌ WebSocket send error:', err)
      return false
    }
  }

  /**
   * Gère les messages WebSocket entrants.
   * @param {Object} data - Message reçu
   */
  function handleWsMessage(data) {
    const { topic, event, job_id, data: payload } = data

    if (topic === 'job_updates') {
      switch (event) {
        case 'job_updated':
        case 'job_started':
        case 'job_finished':
        case 'job_detail':
          if (payload || data.data) {
            const jobData = payload || data.data
            if (jobData) {
              // Si c'est un événement job_finished, on peut ajouter une notification
              if (event === 'job_finished') {
                const title = jobData.title || 'Job'
                toast.success(`"${title}" terminé ! 🎉`)
              }
              updateJob(jobData)
            }
          }
          break
        case 'initial_state':
          // Réception de l'état initial (liste des jobs actifs)
          if (payload?.jobs && Array.isArray(payload.jobs)) {
            for (const job of payload.jobs) {
              updateJob(job)
            }
          }
          break
        default:
          // Autres événements non traités
          break
      }
    } else if (topic === 'system') {
      if (event === 'error') {
        toast.error(`Système: ${payload?.message || 'Erreur'}`, '⚠️')
      } else if (event === 'warning') {
        toast.warning(`Système: ${payload?.message || 'Avertissement'}`, '⚠️')
      }
    } else if (topic === 'logs') {
      // Logs système (à afficher dans la console ou un panneau admin)
      console.log('[WS Log]', payload)
    }
  }

  /**
   * Planifie une reconnexion WebSocket avec backoff exponentiel.
   */
  function scheduleReconnect() {
    if (wsReconnectAttempts.value >= MAX_WS_RECONNECT) {
      console.warn('⚠️ WebSocket: max reconnexions atteint.')
      return
    }
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer)
    }
    const delay = Math.min(1000 * 2 ** wsReconnectAttempts.value, 30000)
    wsReconnectAttempts.value += 1
    console.log(`🔄 WebSocket reconnexion dans ${delay}ms (tentative ${wsReconnectAttempts.value})`)
    wsReconnectTimer = setTimeout(() => {
      // Récupérer le token à jour
      let token = null
      try {
        const authStore = useAuthStore()
        token = authStore.token
      } catch (_) {}
      if (token) {
        initWebSocket(token)
      } else {
        console.warn('⚠️ WebSocket: pas de token, abandon.')
      }
    }, delay)
  }

  /**
   * Ferme proprement la connexion WebSocket.
   */
  function closeWebSocket() {
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer)
      wsReconnectTimer = null
    }
    if (wsInstance) {
      if (wsInstance.readyState === WebSocket.OPEN || wsInstance.readyState === WebSocket.CONNECTING) {
        wsInstance.close(1000, 'Fermeture normale')
      }
      wsInstance = null
    }
    wsConnected.value = false
    wsReconnectAttempts.value = 0
  }

  // ==========================================================================
  //  Initialisation
  // ==========================================================================

  /**
   * Initialise le store (charge les jobs et connecte le WebSocket).
   * @param {Object} options - Options d'initialisation
   * @param {boolean} options.loadJobs - Charger les jobs immédiatement (défaut: true)
   * @param {boolean} options.ws - Connecter le WebSocket (défaut: true)
   * @returns {Promise<void>}
   */
  async function initialize(options = {}) {
    const { loadJobs = true, ws = true } = options

    if (loadJobs) {
      try {
        await fetchJobs()
      } catch (_) {
        // Erreur silencieuse, on continue
      }
    }

    if (ws) {
      try {
        const authStore = useAuthStore()
        if (authStore.token) {
          initWebSocket(authStore.token)
        }
      } catch (_) {}
    }
  }

  /**
   * Nettoie le store (ferme WebSocket, reset état).
   */
  function reset() {
    closeWebSocket()
    jobs.value = {}
    activeJobIds.value = []
    isLoading.value = false
    error.value = null
    lastUpdated.value = null
    wsConnected.value = false
    wsReconnectAttempts.value = 0
  }

  // ==========================================================================
  //  Retour
  // ==========================================================================

  return {
    // État
    jobs,
    activeJobIds,
    isLoading,
    error,
    lastUpdated,
    wsConnected,

    // Getters
    jobsList,
    activeJobs,
    completedJobs,
    runningJobs,
    pendingJobs,
    totalJobs,
    activeCount,
    runningCount,
    overallProgress,
    isJobActive,
    getJob,
    sortedJobs,

    // Actions
    fetchJobs,
    fetchJob,
    refreshActiveJobs,
    startDownload,
    cancelJob,
    cancelAllActive,
    updateJob,
    updateProgress,
    addJobLog,
    removeJob,
    clearCompletedJobs,

    // WebSocket
    initWebSocket,
    closeWebSocket,
    sendWsMessage,

    // Initialisation / Reset
    initialize,
    reset,
  }
})

// ==========================================================================
//  Export du store
// ==========================================================================

export default useJobsStore
