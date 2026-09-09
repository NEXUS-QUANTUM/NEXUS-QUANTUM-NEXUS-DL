// ==========================================================================
//  NexusDL 2.0 - Notifications Store (Pinia)
//  Fichier : frontend/src/stores/notifications.js
//  Description : Gestion centralisée des notifications (toasts, alertes, erreurs, historique)
//  Version : 2.0.0
// ==========================================================================

import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useToast } from '@/composables/useToast'
import { useAppStore } from '@/stores/app'

// ==========================================================================
//  Constantes
// ==========================================================================

const STORAGE_KEY = 'nexus_notifications'
const MAX_HISTORY = 100
const DEFAULT_DURATION = 5000

/**
 * Types de notifications
 * @enum {string}
 */
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
  SYSTEM: 'system',
}

// ==========================================================================
//  Store
// ==========================================================================

export const useNotificationsStore = defineStore('notifications', () => {
  // ==========================================================================
  //  Dépendances
  // ==========================================================================

  const toast = useToast()
  const appStore = useAppStore()

  // ==========================================================================
  //  État
  // ==========================================================================

  /** Liste des notifications (historique) */
  const notifications = ref([])
  /** ID incrémentiel pour générer des identifiants uniques */
  let _idCounter = 0
  /** Indicateur de chargement (pour les opérations) */
  const isLoading = ref(false)
  /** Erreur liée au store */
  const error = ref(null)
  /** Dernière mise à jour */
  const lastUpdated = ref(null)
  /** Si les notifications sont persistées */
  const isPersisted = ref(false)

  // ==========================================================================
  //  Getters
  // ==========================================================================

  /** Nombre total de notifications */
  const total = computed(() => notifications.value.length)

  /** Notifications non lues */
  const unread = computed(() => notifications.value.filter(n => !n.read))

  /** Notifications lues */
  const read = computed(() => notifications.value.filter(n => n.read))

  /** Nombre de notifications non lues */
  const unreadCount = computed(() => unread.value.length)

  /** Dernières notifications (triées par date décroissante) */
  const latest = computed(() => {
    const sorted = [...notifications.value].sort((a, b) => {
      return new Date(b.created_at) - new Date(a.created_at)
    })
    return sorted
  })

  /** Notifications par type */
  const byType = (type) => computed(() =>
    notifications.value.filter(n => n.type === type)
  )

  /** Notifications de succès */
  const successes = computed(() => notifications.value.filter(n => n.type === NOTIFICATION_TYPES.SUCCESS))

  /** Notifications d'erreur */
  const errors = computed(() => notifications.value.filter(n => n.type === NOTIFICATION_TYPES.ERROR))

  /** Notifications d'avertissement */
  const warnings = computed(() => notifications.value.filter(n => n.type === NOTIFICATION_TYPES.WARNING))

  /** Notifications d'information */
  const infos = computed(() => notifications.value.filter(n => n.type === NOTIFICATION_TYPES.INFO))

  /** Notifications système */
  const system = computed(() => notifications.value.filter(n => n.type === NOTIFICATION_TYPES.SYSTEM))

  /** Vérifie s'il y a des notifications non lues */
  const hasUnread = computed(() => unreadCount.value > 0)

  /** Dernière notification (la plus récente) */
  const lastNotification = computed(() => {
    if (notifications.value.length === 0) return null
    return [...notifications.value].sort((a, b) => {
      return new Date(b.created_at) - new Date(a.created_at)
    })[0] || null
  })

  // ==========================================================================
  //  Fonctions internes
  // ==========================================================================

  /**
   * Génère un ID unique pour une notification.
   * @returns {string}
   */
  function generateId() {
    _idCounter += 1
    return `notif-${Date.now()}-${_idCounter}`
  }

  /**
   * Formate la date pour l'affichage.
   * @param {Date|string} date - Date
   * @returns {string}
   */
  function formatDate(date) {
    if (!date) return ''
    const d = typeof date === 'string' ? new Date(date) : date
    return d.toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  /**
   * Persiste les notifications dans le localStorage.
   */
  function persist() {
    try {
      // Ne persister que les notifications récentes (ex: dernières 100)
      const toPersist = notifications.value.slice(-MAX_HISTORY)
      const data = {
        notifications: toPersist,
        lastUpdated: new Date().toISOString(),
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
      isPersisted.value = true
    } catch (_) {
      // Ignorer les erreurs de localStorage (ex: mode privé)
    }
  }

  /**
   * Charge les notifications depuis le localStorage.
   * @returns {Array} - Liste des notifications chargées
   */
  function loadPersisted() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return []
      const data = JSON.parse(raw)
      if (data && Array.isArray(data.notifications)) {
        return data.notifications
      }
    } catch (_) {
      // Ignorer
    }
    return []
  }

  /**
   * Nettoie les notifications trop anciennes.
   * @param {number} maxAge - Âge maximum en jours (défaut: 30)
   */
  function cleanOldNotifications(maxAge = 30) {
    const now = Date.now()
    const cutoff = now - maxAge * 24 * 60 * 60 * 1000
    const toKeep = notifications.value.filter(n => {
      const createdAt = new Date(n.created_at).getTime()
      return createdAt >= cutoff
    })
    if (toKeep.length < notifications.value.length) {
      notifications.value = toKeep
      if (notifications.value.length > MAX_HISTORY) {
        notifications.value = notifications.value.slice(-MAX_HISTORY)
      }
      lastUpdated.value = new Date().toISOString()
      persist()
    }
  }

  // ==========================================================================
  //  Actions
  // ==========================================================================

  /**
   * Ajoute une notification.
   * @param {Object} payload - Données de la notification
   * @param {string} payload.message - Message
   * @param {string} [payload.type=NOTIFICATION_TYPES.INFO] - Type de notification
   * @param {number} [payload.duration] - Durée d'affichage en ms (0 = persistant)
   * @param {boolean} [payload.showToast=true] - Afficher un toast en plus de l'historique
   * @param {string} [payload.icon] - Icône personnalisée
   * @param {Object} [payload.meta] - Métadonnées supplémentaires
   * @param {string} [payload.action] - Texte d'action (bouton)
   * @param {Function} [payload.onAction] - Callback lors de l'action
   * @param {Function} [payload.onClose] - Callback lors de la fermeture
   * @returns {Object} - Notification créée
   */
  function add(payload) {
    const {
      message,
      type = NOTIFICATION_TYPES.INFO,
      duration = DEFAULT_DURATION,
      showToast = true,
      icon = null,
      meta = null,
      action = null,
      onAction = null,
      onClose = null,
    } = payload

    if (!message) {
      console.warn('⚠️ Notifications: message vide ignoré')
      return null
    }

    // Créer l'objet notification
    const notification = {
      id: generateId(),
      message,
      type,
      duration,
      icon: icon || getIconForType(type),
      meta,
      action,
      onAction,
      onClose,
      created_at: new Date().toISOString(),
      read: false,
      dismissed: false,
    }

    // Ajouter à la liste (en tête)
    notifications.value.unshift(notification)

    // Limiter l'historique
    if (notifications.value.length > MAX_HISTORY) {
      notifications.value = notifications.value.slice(0, MAX_HISTORY)
    }

    // Persister
    persist()
    lastUpdated.value = new Date().toISOString()

    // Afficher un toast si demandé
    if (showToast) {
      const toastOptions = {
        type,
        duration,
        icon: notification.icon,
        closable: true,
        onClick: () => {
          if (onAction) onAction(notification)
          // Marquer comme lu lors du clic
          markAsRead(notification.id)
        },
        onClose: () => {
          if (onClose) onClose(notification)
          dismiss(notification.id)
        },
      }
      toast.show(message, toastOptions)
    }

    return notification
  }

  /**
   * Ajoute une notification de succès.
   * @param {string} message - Message
   * @param {Object} options - Options supplémentaires
   * @returns {Object} - Notification créée
   */
  function success(message, options = {}) {
    return add({ ...options, message, type: NOTIFICATION_TYPES.SUCCESS })
  }

  /**
   * Ajoute une notification d'erreur.
   * @param {string} message - Message
   * @param {Object} options - Options supplémentaires
   * @returns {Object} - Notification créée
   */
  function error(message, options = {}) {
    return add({ ...options, message, type: NOTIFICATION_TYPES.ERROR })
  }

  /**
   * Ajoute une notification d'avertissement.
   * @param {string} message - Message
   * @param {Object} options - Options supplémentaires
   * @returns {Object} - Notification créée
   */
  function warning(message, options = {}) {
    return add({ ...options, message, type: NOTIFICATION_TYPES.WARNING })
  }

  /**
   * Ajoute une notification d'information.
   * @param {string} message - Message
   * @param {Object} options - Options supplémentaires
   * @returns {Object} - Notification créée
   */
  function info(message, options = {}) {
    return add({ ...options, message, type: NOTIFICATION_TYPES.INFO })
  }

  /**
   * Ajoute une notification système (ex: maintenance).
   * @param {string} message - Message
   * @param {Object} options - Options supplémentaires
   * @returns {Object} - Notification créée
   */
  function system(message, options = {}) {
    return add({ ...options, message, type: NOTIFICATION_TYPES.SYSTEM })
  }

  /**
   * Supprime une notification de l'historique.
   * @param {string} id - ID de la notification
   */
  function remove(id) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
      persist()
      lastUpdated.value = new Date().toISOString()
    }
  }

  /**
   * Marque une notification comme lue.
   * @param {string} id - ID de la notification
   */
  function markAsRead(id) {
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.read = true
      persist()
      lastUpdated.value = new Date().toISOString()
    }
  }

  /**
   * Marque toutes les notifications comme lues.
   */
  function markAllAsRead() {
    for (const n of notifications.value) {
      n.read = true
    }
    persist()
    lastUpdated.value = new Date().toISOString()
  }

  /**
   * Marque une notification comme rejetée (dismissed).
   * @param {string} id - ID de la notification
   */
  function dismiss(id) {
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.dismissed = true
      // Ne pas supprimer immédiatement, garder pour historique avec flag
      persist()
      lastUpdated.value = new Date().toISOString()
    }
  }

  /**
   * Supprime toutes les notifications de l'historique (avec confirmation).
   * @param {boolean} confirm - Demander confirmation
   * @returns {boolean} - true si supprimé
   */
  function clearAll(confirm = true) {
    if (confirm && !window.confirm('Supprimer tout l\'historique des notifications ?')) {
      return false
    }
    notifications.value = []
    persist()
    lastUpdated.value = new Date().toISOString()
    return true
  }

  /**
   * Supprime les notifications lues (avec confirmation).
   * @param {boolean} confirm - Demander confirmation
   * @returns {number} - Nombre de notifications supprimées
   */
  function clearRead(confirm = true) {
    if (confirm && !window.confirm('Supprimer toutes les notifications lues ?')) {
      return 0
    }
    const count = notifications.value.filter(n => n.read).length
    notifications.value = notifications.value.filter(n => !n.read)
    persist()
    lastUpdated.value = new Date().toISOString()
    return count
  }

  /**
   * Supprime les notifications qui ont été rejetées (dismissed) et sont lues.
   * @param {boolean} confirm - Demander confirmation
   * @returns {number} - Nombre de notifications supprimées
   */
  function cleanDismissed(confirm = true) {
    if (confirm && !window.confirm('Supprimer les notifications rejetées ?')) {
      return 0
    }
    const count = notifications.value.filter(n => n.dismissed && n.read).length
    notifications.value = notifications.value.filter(n => !(n.dismissed && n.read))
    persist()
    lastUpdated.value = new Date().toISOString()
    return count
  }

  /**
   * Charge les notifications depuis le localStorage.
   * @param {boolean} clearExisting - Effacer les notifications existantes
   */
  function loadFromStorage(clearExisting = true) {
    const stored = loadPersisted()
    if (stored && stored.length > 0) {
      if (clearExisting) {
        notifications.value = stored
      } else {
        // Fusionner en évitant les doublons
        const existingIds = new Set(notifications.value.map(n => n.id))
        for (const n of stored) {
          if (!existingIds.has(n.id)) {
            notifications.value.push(n)
          }
        }
      }
      lastUpdated.value = new Date().toISOString()
    }
  }

  /**
   * Sauvegarde manuellement les notifications.
   */
  function save() {
    persist()
  }

  /**
   * Réinitialise le store (vide tout).
   */
  function reset() {
    notifications.value = []
    isPersisted.value = false
    lastUpdated.value = null
    error.value = null
    isLoading.value = false
    localStorage.removeItem(STORAGE_KEY)
  }

  // ==========================================================================
  //  Utilitaires
  // ==========================================================================

  /**
   * Retourne l'icône correspondant au type de notification.
   * @param {string} type - Type de notification
   * @returns {string} - Emoji icône
   */
  function getIconForType(type) {
    const map = {
      [NOTIFICATION_TYPES.SUCCESS]: '✅',
      [NOTIFICATION_TYPES.ERROR]: '❌',
      [NOTIFICATION_TYPES.WARNING]: '⚠️',
      [NOTIFICATION_TYPES.INFO]: 'ℹ️',
      [NOTIFICATION_TYPES.SYSTEM]: '🔄',
    }
    return map[type] || '📢'
  }

  /**
   * Récupère les notifications pour un contexte donné (ex: une page).
   * @param {string} context - Contexte (ex: 'library', 'downloads')
   * @returns {Array} - Notifications filtrées
   */
  function getByContext(context) {
    return notifications.value.filter(n => n.meta?.context === context)
  }

  /**
   * Récupère les notifications par plage de dates.
   * @param {Date} start - Date de début
   * @param {Date} end - Date de fin
   * @returns {Array} - Notifications filtrées
   */
  function getByDateRange(start, end) {
    const startTime = start.getTime()
    const endTime = end.getTime()
    return notifications.value.filter(n => {
      const t = new Date(n.created_at).getTime()
      return t >= startTime && t <= endTime
    })
  }

  // ==========================================================================
  //  Intégration avec le store global (app)
  // ==========================================================================

  /**
   * Affiche une notification globale dans l'application (via appStore).
   * @param {string} message - Message
   * @param {string} type - Type
   * @param {number} duration - Durée
   */
  function showGlobal(message, type = 'info', duration = 5000) {
    appStore.showGlobalNotification(message, type, duration)
    // Ajouter également dans l'historique
    add({ message, type, duration, showToast: false })
  }

  // ==========================================================================
  //  Initialisation
  // ==========================================================================

  /**
   * Initialise le store (charge les notifications persistées).
   * @param {Object} options - Options
   * @param {boolean} options.load - Charger les données persistées (défaut: true)
   * @param {boolean} options.cleanOld - Nettoyer les anciennes notifications (défaut: true)
   * @param {number} options.maxAge - Âge maximum en jours pour le nettoyage
   */
  function initialize({ load = true, cleanOld = true, maxAge = 30 } = {}) {
    isLoading.value = true
    try {
      if (load) {
        loadFromStorage(true)
      }
      if (cleanOld && notifications.value.length > 0) {
        cleanOldNotifications(maxAge)
      }
      lastUpdated.value = new Date().toISOString()
    } catch (err) {
      error.value = err
    } finally {
      isLoading.value = false
    }
  }

  // ==========================================================================
  //  Watchers
  // ==========================================================================

  // Persister automatiquement les changements
  watch(notifications, () => {
    persist()
    lastUpdated.value = new Date().toISOString()
  }, { deep: true })

  // ==========================================================================
  //  Retour
  // ==========================================================================

  return {
    // État
    notifications,
    isLoading,
    error,
    lastUpdated,
    isPersisted,

    // Getters
    total,
    unread,
    read,
    unreadCount,
    latest,
    successes,
    errors,
    warnings,
    infos,
    system,
    hasUnread,
    lastNotification,

    // Actions principales
    add,
    success,
    error,
    warning,
    info,
    system,
    remove,
    markAsRead,
    markAllAsRead,
    dismiss,
    clearAll,
    clearRead,
    cleanDismissed,
    loadFromStorage,
    save,
    reset,
    cleanOldNotifications,
    showGlobal,

    // Utilitaires
    getIconForType,
    getByContext,
    getByDateRange,
    formatDate,

    // Initialisation
    initialize,

    // Constantes
    NOTIFICATION_TYPES,
  }
})

// ==========================================================================
//  Export du store
// ==========================================================================

export default useNotificationsStore
