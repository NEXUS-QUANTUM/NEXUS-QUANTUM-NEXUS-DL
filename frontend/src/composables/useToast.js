// ==========================================================================
//  NexusDL 2.0 - useToast Composable
//  Fichier : frontend/src/composables/useToast.js
//  Description : Gestion des notifications toast (snackbars) avec file d'attente
//  Version : 2.0.0
// ==========================================================================

import { ref, reactive, computed, readonly, onUnmounted, inject } from 'vue'

// ==========================================================================
//  Constantes et configurations
// ==========================================================================

const DEFAULT_DURATION = 4000
const DEFAULT_POSITION = 'bottom-right'
const MAX_TOASTS = 5
const TOAST_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
  DEFAULT: 'default',
}

const POSITIONS = [
  'top-left',
  'top-center',
  'top-right',
  'bottom-left',
  'bottom-center',
  'bottom-right',
]

const ICONS = {
  [TOAST_TYPES.SUCCESS]: '✅',
  [TOAST_TYPES.ERROR]: '❌',
  [TOAST_TYPES.WARNING]: '⚠️',
  [TOAST_TYPES.INFO]: 'ℹ️',
  [TOAST_TYPES.DEFAULT]: '📢',
}

const COLORS = {
  [TOAST_TYPES.SUCCESS]: {
    bg: '#1a3a1a',
    border: '#2a5a2a',
    text: '#5cb85c',
  },
  [TOAST_TYPES.ERROR]: {
    bg: '#3a1a1a',
    border: '#5a2a2a',
    text: '#d9534f',
  },
  [TOAST_TYPES.WARNING]: {
    bg: '#3a2a1a',
    border: '#5a4a2a',
    text: '#ff9800',
  },
  [TOAST_TYPES.INFO]: {
    bg: '#1a2a3a',
    border: '#2a4a5a',
    text: '#58b9ff',
  },
  [TOAST_TYPES.DEFAULT]: {
    bg: '#1a2538',
    border: '#2a3a5a',
    text: '#b0c0d8',
  },
}

// ==========================================================================
//  Types (JSDoc)
// ==========================================================================

/**
 * @typedef {Object} ToastOptions
 * @property {string} [type] - Type de toast ('success', 'error', 'warning', 'info', 'default')
 * @property {number} [duration] - Durée d'affichage en ms (0 pour ne pas disparaître)
 * @property {string} [position] - Position ('top-left', 'top-center', 'top-right', 'bottom-left', 'bottom-center', 'bottom-right')
 * @property {boolean} [closable] - Afficher le bouton de fermeture
 * @property {string} [icon] - Icône personnalisée (surcharge le type)
 * @property {string} [className] - Classe CSS additionnelle
 * @property {Function} [onClick] - Callback au clic sur le toast
 * @property {Function} [onClose] - Callback à la fermeture
 */

/**
 * @typedef {Object} ToastInstance
 * @property {string} id - Identifiant unique
 * @property {string} message - Message affiché
 * @property {string} type - Type de toast
 * @property {string} icon - Icône affichée
 * @property {string} position - Position
 * @property {number} duration - Durée d'affichage
 * @property {boolean} closable - Si bouton de fermeture affiché
 * @property {string} className - Classe CSS additionnelle
 * @property {Function} onClick - Callback au clic
 * @property {Function} onClose - Callback à la fermeture
 * @property {number} createdAt - Timestamp de création
 * @property {number} remainingTime - Temps restant (pour pause/repause)
 * @property {boolean} isPaused - Si le toast est en pause
 * @property {boolean} isVisible - Si le toast est visible
 */

// ==========================================================================
//  Composable
// ==========================================================================

/**
 * Composable pour la gestion des toasts (notifications).
 * Fournit des méthodes pour afficher des notifications avec différents types,
 * gère la file d'attente et les positions.
 *
 * @param {Object} options - Options de configuration globale
 * @param {number} options.defaultDuration - Durée par défaut (ms)
 * @param {string} options.defaultPosition - Position par défaut
 * @param {number} options.maxToasts - Nombre max de toasts affichés simultanément
 * @param {string} options.containerId - ID du conteneur de toasts (pour intégration Vue)
 * @returns {Object} - Méthodes et états réactifs
 */
export function useToast(options = {}) {
  // --------------------------------------------------------------------------
  //  Configuration globale
  // --------------------------------------------------------------------------
  const {
    defaultDuration = DEFAULT_DURATION,
    defaultPosition = DEFAULT_POSITION,
    maxToasts = MAX_TOASTS,
    containerId = 'toast-container',
  } = options

  // --------------------------------------------------------------------------
  //  État réactif
  // --------------------------------------------------------------------------
  const toasts = ref([])
  const activeToasts = computed(() => toasts.value.filter(t => t.isVisible))
  const queue = ref([])
  const isPaused = ref(false)

  // Timers pour chaque toast (pour la gestion de la durée)
  const timers = new Map()

  // Compteurs pour générer des IDs uniques
  let idCounter = 0

  // --------------------------------------------------------------------------
  //  Fonctions internes
  // --------------------------------------------------------------------------

  /**
   * Génère un ID unique pour un toast.
   * @returns {string}
   */
  function generateId() {
    idCounter += 1
    return `toast-${Date.now()}-${idCounter}`
  }

  /**
   * Récupère l'icône pour un type de toast.
   * @param {string} type - Type de toast
   * @param {string} customIcon - Icône personnalisée
   * @returns {string}
   */
  function getIcon(type, customIcon = null) {
    if (customIcon) return customIcon
    return ICONS[type] || ICONS[TOAST_TYPES.DEFAULT]
  }

  /**
   * Récupère la configuration de couleurs pour un type.
   * @param {string} type - Type de toast
   * @returns {Object}
   */
  function getColors(type) {
    return COLORS[type] || COLORS[TOAST_TYPES.DEFAULT]
  }

  /**
   * Crée un objet toast à partir des paramètres.
   * @param {string} message - Message
   * @param {ToastOptions} toastOptions - Options
   * @returns {ToastInstance}
   */
  function createToastInstance(message, toastOptions = {}) {
    const {
      type = TOAST_TYPES.DEFAULT,
      duration = defaultDuration,
      position = defaultPosition,
      closable = true,
      icon = null,
      className = '',
      onClick = null,
      onClose = null,
    } = toastOptions

    return {
      id: generateId(),
      message,
      type,
      icon: getIcon(type, icon),
      position,
      duration,
      closable,
      className,
      onClick,
      onClose,
      createdAt: Date.now(),
      remainingTime: duration,
      isPaused: false,
      isVisible: true,
    }
  }

  /**
   * Ajoute un toast à la file d'attente ou l'affiche directement.
   * @param {ToastInstance} toast - Instance de toast
   */
  function addToast(toast) {
    // Si on peut afficher directement
    if (activeToasts.value.length < maxToasts) {
      toasts.value.push(toast)
      scheduleRemoval(toast)
    } else {
      // Mettre en file d'attente
      queue.value.push(toast)
    }
  }

  /**
   * Planifie la suppression automatique d'un toast.
   * @param {ToastInstance} toast - Instance de toast
   */
  function scheduleRemoval(toast) {
    if (toast.duration <= 0) return // Durée infinie, ne pas supprimer automatiquement

    const timer = setTimeout(() => {
      // Vérifier si le toast est toujours visible et non en pause
      const currentToast = toasts.value.find(t => t.id === toast.id)
      if (currentToast && currentToast.isVisible && !currentToast.isPaused) {
        removeToast(toast.id)
      }
    }, toast.duration)

    timers.set(toast.id, timer)
  }

  /**
   * Supprime un toast de la liste et traite la file d'attente.
   * @param {string} id - ID du toast
   */
  function removeToast(id) {
    // Arrêter le timer
    if (timers.has(id)) {
      clearTimeout(timers.get(id))
      timers.delete(id)
    }

    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      const toast = toasts.value[index]
      // Appeler le callback de fermeture
      if (toast.onClose) {
        toast.onClose(toast)
      }
      // Retirer
      toasts.value.splice(index, 1)
    }

    // Traiter la file d'attente
    processQueue()
  }

  /**
   * Traite la file d'attente et affiche le prochain toast.
   */
  function processQueue() {
    while (queue.value.length > 0 && activeToasts.value.length < maxToasts) {
      const nextToast = queue.value.shift()
      if (nextToast) {
        toasts.value.push(nextToast)
        scheduleRemoval(nextToast)
      }
    }
  }

  /**
   * Met à jour le temps restant pour un toast (quand il est mis en pause).
   * @param {ToastInstance} toast - Instance de toast
   */
  function updateRemainingTime(toast) {
    const elapsed = Date.now() - toast.createdAt
    toast.remainingTime = Math.max(0, toast.duration - elapsed)
  }

  // --------------------------------------------------------------------------
  //  Méthodes publiques
  // --------------------------------------------------------------------------

  /**
   * Affiche un toast.
   * @param {string} message - Message à afficher
   * @param {ToastOptions} toastOptions - Options du toast
   * @returns {string} - ID du toast créé
   */
  function show(message, toastOptions = {}) {
    if (!message) {
      console.warn('⚠️ useToast: message vide ignoré')
      return null
    }

    const toast = createToastInstance(message, toastOptions)
    addToast(toast)
    return toast.id
  }

  /**
   * Affiche un toast de succès.
   * @param {string} message - Message
   * @param {ToastOptions} [options] - Options
   * @returns {string} - ID du toast
   */
  function success(message, options = {}) {
    return show(message, { type: TOAST_TYPES.SUCCESS, ...options })
  }

  /**
   * Affiche un toast d'erreur.
   * @param {string} message - Message
   * @param {ToastOptions} [options] - Options
   * @returns {string} - ID du toast
   */
  function error(message, options = {}) {
    return show(message, { type: TOAST_TYPES.ERROR, ...options })
  }

  /**
   * Affiche un toast d'avertissement.
   * @param {string} message - Message
   * @param {ToastOptions} [options] - Options
   * @returns {string} - ID du toast
   */
  function warning(message, options = {}) {
    return show(message, { type: TOAST_TYPES.WARNING, ...options })
  }

  /**
   * Affiche un toast d'information.
   * @param {string} message - Message
   * @param {ToastOptions} [options] - Options
   * @returns {string} - ID du toast
   */
  function info(message, options = {}) {
    return show(message, { type: TOAST_TYPES.INFO, ...options })
  }

  /**
   * Ferme un toast par son ID.
   * @param {string} id - ID du toast
   */
  function close(id) {
    const toast = toasts.value.find(t => t.id === id)
    if (toast) {
      removeToast(id)
    }
  }

  /**
   * Ferme tous les toasts actifs.
   */
  function closeAll() {
    // Copier les IDs pour éviter les problèmes de mutation
    const ids = toasts.value.map(t => t.id)
    for (const id of ids) {
      removeToast(id)
    }
    // Vider la file d'attente
    queue.value = []
    // Annuler tous les timers
    for (const [id, timer] of timers) {
      clearTimeout(timer)
    }
    timers.clear()
  }

  /**
   * Met en pause tous les toasts (arrête les timers de suppression).
   */
  function pauseAll() {
    if (isPaused.value) return
    isPaused.value = true
    for (const toast of toasts.value) {
      if (toast.isVisible && toast.duration > 0) {
        toast.isPaused = true
        updateRemainingTime(toast)
        // Arrêter le timer
        if (timers.has(toast.id)) {
          clearTimeout(timers.get(toast.id))
          timers.delete(toast.id)
        }
      }
    }
  }

  /**
   * Reprend tous les toasts (relance les timers de suppression).
   */
  function resumeAll() {
    if (!isPaused.value) return
    isPaused.value = false
    for (const toast of toasts.value) {
      if (toast.isVisible && toast.isPaused && toast.remainingTime > 0) {
        toast.isPaused = false
        // Remettre le timer avec le temps restant
        const timer = setTimeout(() => {
          const currentToast = toasts.value.find(t => t.id === toast.id)
          if (currentToast && currentToast.isVisible) {
            removeToast(toast.id)
          }
        }, toast.remainingTime)
        timers.set(toast.id, timer)
      }
    }
  }

  /**
   * Met à jour la position de tous les toasts.
   * @param {string} position - Nouvelle position
   */
  function setPosition(position) {
    if (!POSITIONS.includes(position)) {
      console.warn(`Position invalide: ${position}. Utilisation de '${defaultPosition}'`)
      position = defaultPosition
    }
    for (const toast of toasts.value) {
      toast.position = position
    }
  }

  /**
   * Crée un toast de succès qui disparaît rapidement (pour les confirmations légères).
   * @param {string} message - Message
   * @param {number} [duration] - Durée en ms (défaut: 1500)
   * @returns {string} - ID du toast
   */
  function quickSuccess(message, duration = 1500) {
    return success(message, { duration })
  }

  /**
   * Crée un toast persistant (sans disparition automatique) avec un bouton de fermeture.
   * @param {string} message - Message
   * @param {string} [type='info'] - Type de toast
   * @param {Object} [options] - Options supplémentaires
   * @returns {string} - ID du toast
   */
  function persistent(message, type = TOAST_TYPES.INFO, options = {}) {
    return show(message, {
      type,
      duration: 0,
      closable: true,
      ...options,
    })
  }

  /**
   * Affiche une promesse avec un toast de chargement, puis success/error.
   * @param {Promise} promise - Promesse à exécuter
   * @param {Object} options - Options
   * @param {string} options.loading - Message pendant le chargement
   * @param {string} options.success - Message en cas de succès
   * @param {string} options.error - Message en cas d'erreur
   * @param {number} [options.duration] - Durée des toasts de résultat
   * @returns {Promise} - Promesse d'origine
   */
  async function withLoading(promise, options = {}) {
    const {
      loading = 'Chargement...',
      success: successMsg = 'Opération réussie !',
      error: errorMsg = 'Une erreur est survenue.',
      duration = 3000,
    } = options

    const loadingId = info(loading, { duration: 0, closable: false })

    try {
      const result = await promise
      close(loadingId)
      if (successMsg) {
        success(successMsg, { duration })
      }
      return result
    } catch (err) {
      close(loadingId)
      const msg = err?.message || errorMsg || 'Une erreur est survenue.'
      error(msg, { duration })
      throw err
    }
  }

  // ==========================================================================
  //  Gestion du cycle de vie
  // ==========================================================================

  // Nettoyer les timers à la destruction
  onUnmounted(() => {
    for (const [id, timer] of timers) {
      clearTimeout(timer)
    }
    timers.clear()
    // Vider les données réactives
    toasts.value = []
    queue.value = []
    isPaused.value = false
  })

  // ==========================================================================
  //  Retour du composable
  // ==========================================================================

  return {
    // État réactif
    toasts: readonly(toasts),
    activeToasts: readonly(activeToasts),
    queue: readonly(queue),
    isPaused: readonly(isPaused),

    // Méthodes principales
    show,
    success,
    error,
    warning,
    info,
    close,
    closeAll,
    pauseAll,
    resumeAll,

    // Méthodes auxiliaires
    quickSuccess,
    persistent,
    withLoading,
    setPosition,

    // Utilitaires
    getIcon,
    getColors,
    TOAST_TYPES,
    POSITIONS,
  }
}

// ==========================================================================
//  Injection globale (pour utiliser dans tout l'app)
// ==========================================================================

/**
 * Plugin Vue pour fournir useToast à toute l'application.
 * @param {Object} app - Instance Vue
 * @param {Object} options - Options globales
 */
export function installToastPlugin(app, options = {}) {
  const toast = useToast(options)
  app.provide('toast', toast)
  // Permettre d'utiliser $toast dans les Options API
  app.config.globalProperties.$toast = toast
  console.log('✅ Plugin Toast installé')
}

// ==========================================================================
//  Export par défaut (pour utilisation avec `useToast` nommé)
// ==========================================================================

export default useToast
