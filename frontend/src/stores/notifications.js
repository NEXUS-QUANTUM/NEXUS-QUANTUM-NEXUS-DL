// ==========================================================================
//  NexusDL 2.0 - Notifications Store (version complète et finale)
//  Fichier : frontend/src/stores/notifications.js
//  Description : Gestion centralisée des notifications (toasts, alertes,
//                erreurs, historique) avec persistance localStorage.
//  Version : 2.0.0
//  Licence : GNU GPL v3.0
//
//  ⚠️ CORRECTION APPLIQUÉE :
//  - La fonction `error` a été renommée en `showError` pour éviter le
//    conflit avec la variable d'état `error` (renommée en `stateError`).
//  - Toutes les références internes ont été mises à jour.
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
  SYSTEM: 'system'
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

  /** Indicateur de chargement */
  const isLoading = ref(false)

  /**
   * ⚠️ CORRECTION : variable d'état renommée en `stateError`
   * pour éviter le conflit avec la fonction `showError`.
   */
  const stateError = ref(null)

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
  const unread = computed(() => notifications.value.filter((n) => !n.read))

  /** Notifications lues */
  const read = computed(() => notifications.value.filter((n) => n.read))

  /** Nombre de notifications non lues */
  const unreadCount = computed(() => unread.value.length)

  /** Dernières notifications (triées par date décroissante) */
  const latest = computed(() => {
    const sorted = [...notifications.value].sort((a, b) => {
      return new Date(b.created_at) - new Date(a.created_at)
    })
    return sorted
  })

  /** Notifications de succès */
  const successes = computed(() =>
    notifications.value.filter((n) => n.type === NOTIFICATION_TYPES.SUCCESS)
  )

  /** Notifications d'erreur */
  const errors = computed(() =>
    notifications.value.filter((n) => n.type === NOTIFICATION_TYPES.ERROR)
  )

  /** Notifications d'avertissement */
  const warnings = computed(() =>
    notifications.value.filter((n) => n.type === NOTIFICATION_TYPES.WARNING)
  )

  /** Notifications d'information */
  const infos = computed(() =>
    notifications.value.filter((n) => n.type === NOTIFICATION_TYPES.INFO)
  )

  /** Notifications système */
  const systemMessages = computed(() =>
    notifications.value.filter((n) => n.type === NOTIFICATION_TYPES.SYSTEM)
  )

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
   * @param {Date|string} date
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
      second: '2-digit'
    })
  }

  /**
   * Persiste les notifications dans le localStorage.
   */
  function persist() {
    try {
      const toPersist = notifications.value.slice(-MAX_HISTORY)
      const data = {
        notifications: toPersist,
        lastUpdated: new Date().toISOString()
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
      isPersisted.value = true
    } catch (_) {
      // Ignorer les erreurs de localStorage (mode privé, quota dépassé, etc.)
    }
  }

  /**
   * Charge les notifications depuis le localStorage.
   * @returns {Array}
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
   * @param {number} maxAge - Âge maximum en jours
   */
  function cleanOldNotifications(maxAge = 30) {
    const now = Date.now()
    const cutoff = now - maxAge * 24 * 60 * 60 * 1000
    const toKeep = notifications.value.filter((n) => {
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

  /**
   * Retourne l'icône correspondant au type de notification.
   * @param {string} type
   * @returns {string}
   */
  function getIconForType(type) {
    const map = {
      [NOTIFICATION_TYPES.SUCCESS]: '✅',
      [NOTIFICATION_TYPES.ERROR]: '❌',
      [NOTIFICATION_TYPES.WARNING]: '⚠️',
      [NOTIFICATION_TYPES.INFO]: 'ℹ️',
      [NOTIFICATION_TYPES.SYSTEM]: '🔄'
    }
    return map[type] || '📢'
  }

  // ==========================================================================
  //  Actions principales
  // ==========================================================================

  /**
   * Ajoute une notification.
   * @param {Object} payload
   * @returns {Object|null}
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
      onClose = null
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
      dismissed: false
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
    if (showToast && toast && typeof toast.show === 'function') {
      const toastOptions = {
        type,
        duration,
        icon: notification.icon,
        closable: true,
        onClick: () => {
          if (onAction) onAction(notification)
          markAsRead(notification.id)
        },
        onClose: () => {
          if (onClose) onClose(notification)
          dismiss(notification.id)
        }
      }
      toast.show(message, toastOptions)
    }

    return notification
  }

  /**
   * Ajoute une notification de succès.
   * @param {string} message
   * @param {Object} options
   * @returns {Object|null}
   */
  function success(message, options = {}) {
    return add({ ...options, message, type: NOTIFICATION_TYPES.SUCCESS })
  }

  /**
   * ⚠️ CORRECTION : renommé `error` → `showError`
   * Ajoute une notification d'erreur.
   * @param {string} message
   * @param {Object} options
   * @returns {Object|null}
   */
  function showError(message, options = {}) {
    return add({ ...options, message, type: NOTIFICATION_TYPES.ERROR })
  }

  /**
   * Ajoute une notification d'avertissement.
   * @param {string} message
   * @param {Object} options
   * @returns {Object|null}
   */
  function warning(message, options = {}) {
    return add({ ...options, message, type: NOTIFICATION_TYPES.WARNING })
  }

  /**
   * Ajoute une notification d'information.
   * @param {string} message
   * @param {Object} options
   * @returns {Object|null}
   */
  function info(message, options = {}) {
    return add({ ...options, message, type: NOTIFICATION_TYPES.INFO })
  }

  /**
   * Ajoute une notification système.
   * @param {string} message
   * @param {Object} options
   * @returns {Object|null}
   */
  function system(message, options = {}) {
    return add({ ...options, message, type: NOTIFICATION_TYPES.SYSTEM })
  }

  /**
   * Supprime une notification de l'historique.
   * @param {string} id
   */
  function remove(id) {
    const index = notifications.value.findIndex((n) => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
      persist()
      lastUpdated.value = new Date().toISOString()
    }
  }

  /**
   * Marque une notification comme lue.
   * @param {string} id
   */
  function markAsRead(id) {
    const notification = notifications.value.find((n) => n.id === id)
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
   * @param {string} id
   */
  function dismiss(id) {
    const notification = notifications.value.find((n) => n.id === id)
    if (notification) {
      notification.dismissed = true
      persist()
      lastUpdated.value = new Date().toISOString()
    }
  }

  /**
   * Supprime toutes les notifications de l'historique.
   * @param {boolean} confirm
   * @returns {boolean}
   */
  function clearAll(confirm = true) {
    if (confirm && typeof window !== 'undefined') {
      if (!window.confirm("Supprimer tout l'historique des notifications ?")) {
        return false
      }
    }
    notifications.value = []
    persist()
    lastUpdated.value = new Date().toISOString()
    return true
  }

  /**
   * Supprime les notifications lues.
   * @param {boolean} confirm
   * @returns {number}
   */
  function clearRead(confirm = true) {
    if (confirm && typeof window !== 'undefined') {
      if (!window.confirm('Supprimer toutes les notifications lues ?')) {
        return 0
      }
    }
    const count = notifications.value.filter((n) => n.read).length
    notifications.value = notifications.value.filter((n) => !n.read)
    persist()
    lastUpdated.value = new Date().toISOString()
    return count
  }

  /**
   * Supprime les notifications rejetées et lues.
   * @param {boolean} confirm
   * @returns {number}
   */
  function cleanDismissed(confirm = true) {
    if (confirm && typeof window !== 'undefined') {
      if (!window.confirm('Supprimer les notifications rejetées ?')) {
        return 0
      }
    }
    const count = notifications.value.filter((n) => n.dismissed && n.read).length
    notifications.value = notifications.value.filter(
      (n) => !(n.dismissed && n.read)
    )
    persist()
    lastUpdated.value = new Date().toISOString()
    return count
  }

  /**
   * Charge les notifications depuis le localStorage.
   * @param {boolean} clearExisting
   */
  function loadFromStorage(clearExisting = true) {
    const stored = loadPersisted()
    if (stored && stored.length > 0) {
      if (clearExisting) {
        notifications.value = stored
      } else {
        const existingIds = new Set(notifications.value.map((n) => n.id))
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
   * Réinitialise le store.
   */
  function reset() {
    notifications.value = []
    isPersisted.value = false
    lastUpdated.value = null
    stateError.value = null
    isLoading.value = false
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch (_) {
      // Ignorer
    }
  }

  // ==========================================================================
  //  Utilitaires
  // ==========================================================================

  /**
   * Récupère les notifications pour un contexte donné.
   * @param {string} context
   * @returns {Array}
   */
  function getByContext(context) {
    return notifications.value.filter((n) => n.meta?.context === context)
  }

  /**
   * Récupère les notifications par plage de dates.
   * @param {Date} start
   * @param {Date} end
   * @returns {Array}
   */
  function getByDateRange(start, end) {
    const startTime = start.getTime()
    const endTime = end.getTime()
    return notifications.value.filter((n) => {
      const t = new Date(n.created_at).getTime()
      return t >= startTime && t <= endTime
    })
  }

  // ==========================================================================
  //  Intégration avec le store global (app)
  // ==========================================================================

  /**
   * Affiche une notification globale dans l'application.
   * @param {string} message
   * @param {string} type
   * @param {number} duration
   */
  function showGlobal(message, type = 'info', duration = 5000) {
    if (appStore && typeof appStore.showGlobalNotification === 'function') {
      appStore.showGlobalNotification(message, type, duration)
    }
    add({ message, type, duration, showToast: false })
  }

  // ==========================================================================
  //  Initialisation
  // ==========================================================================

  /**
   * Initialise le store.
   * @param {Object} options
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
      stateError.value = err
    } finally {
      isLoading.value = false
    }
  }

  // ==========================================================================
  //  Watchers
  // ==========================================================================

  // Persister automatiquement les changements
  watch(
    notifications,
    () => {
      persist()
      lastUpdated.value = new Date().toISOString()
    },
    { deep: true }
  )

  // ==========================================================================
  //  Retour du store
  // ==========================================================================

  return {
    // ========================================================================
    //  État
    // ========================================================================
    notifications,
    isLoading,
    stateError,
    lastUpdated,
    isPersisted,

    // ========================================================================
    //  Getters
    // ========================================================================
    total,
    unread,
    read,
    unreadCount,
    latest,
    successes,
    errors,
    warnings,
    infos,
    systemMessages,
    hasUnread,
    lastNotification,

    // ========================================================================
    //  Actions principales
    // ========================================================================
    add,
    success,
    showError,       // ⚠️ Renommé depuis `error`
    errorFn: showError, // Alias pratique
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

    // ========================================================================
    //  Utilitaires
    // ========================================================================
    getIconForType,
    getByContext,
    getByDateRange,
    formatDate,

    // ========================================================================
    //  Initialisation
    // ========================================================================
    initialize,

    // ========================================================================
    //  Constantes
    // ========================================================================
    NOTIFICATION_TYPES
  }
})

// ==========================================================================
//  Export par défaut
// ==========================================================================

export default useNotificationsStore
