// ==========================================================================
//  NexusDL 2.0 - App Store (Pinia)
//  Fichier : frontend/src/stores/app.js
//  Description : Store global de l'application (thème, layout, état global)
//  Version : 2.0.0
// ==========================================================================

import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useTheme } from '@/composables/useTheme'

/**
 * Store principal de l'application.
 * Gère l'état global non lié à l'authentification ou aux données métier.
 */
export const useAppStore = defineStore('app', () => {
  // ==========================================================================
  //  État
  // ==========================================================================

  // --- Thème ---
  const theme = ref('system') // 'dark' | 'light' | 'system'
  const isDark = ref(false)
  const isLight = ref(false)

  // --- Interface utilisateur ---
  const activeTab = ref('search')
  const previousRoute = ref(null)
  const isLoading = ref(false)
  const loadingMessage = ref('')
  const error = ref(null)
  const isMobile = ref(false)
  const isSidebarOpen = ref(false)
  const isSearchFocused = ref(false)

  // --- Version ---
  const appVersion = ref(import.meta.env.VITE_APP_VERSION || '2.0.0')

  // --- Maintenance ---
  const isMaintenanceMode = ref(false)
  const maintenanceMessage = ref('')

  // --- Notifications globales (pour les erreurs non gérées) ---
  const globalNotification = ref(null) // { message, type, duration }

  // ==========================================================================
  //  Getters
  // ==========================================================================

  const currentThemeLabel = computed(() => {
    if (theme.value === 'system') {
      return isDark.value ? 'Système (sombre)' : 'Système (clair)'
    }
    return isDark.value ? 'Sombre' : 'Clair'
  })

  const isDarkMode = computed(() => isDark.value)

  const themeIcon = computed(() => {
    if (theme.value === 'system') return '🖥️'
    return isDark.value ? '🌙' : '☀️'
  })

  const hasError = computed(() => error.value !== null)

  const isReady = computed(() => !isLoading.value && !error.value)

  // ==========================================================================
  //  Actions
  // ==========================================================================

  // --- Thème ---

  /**
   * Initialise le thème depuis le localStorage ou la préférence système.
   * Utilise le composable useTheme.
   */
  function initTheme() {
    const themeComposable = useTheme()
    theme.value = themeComposable.currentTheme.value
    isDark.value = themeComposable.isDark.value
    isLight.value = themeComposable.isLight.value

    // Synchroniser les changements de thème
    watch(
      () => themeComposable.currentTheme.value,
      (newTheme) => {
        theme.value = newTheme
      }
    )
    watch(
      () => themeComposable.isDark.value,
      (newIsDark) => {
        isDark.value = newIsDark
        isLight.value = !newIsDark
      }
    )
  }

  /**
   * Change le thème.
   * @param {string} newTheme - 'dark', 'light' ou 'system'
   */
  function setTheme(newTheme) {
    const themeComposable = useTheme()
    themeComposable.setTheme(newTheme)
    // Les watchers mettront à jour les refs
  }

  /**
   * Bascule entre sombre et clair (ignore le mode système).
   */
  function toggleTheme() {
    const themeComposable = useTheme()
    themeComposable.toggleTheme()
  }

  // --- Navigation ---

  /**
   * Définit l'onglet actif.
   * @param {string} tab - Identifiant de l'onglet
   */
  function setActiveTab(tab) {
    activeTab.value = tab
  }

  /**
   * Enregistre la route précédente.
   * @param {Object} route - Objet route Vue Router
   */
  function setPreviousRoute(route) {
    previousRoute.value = route
  }

  /**
   * Retourne à la route précédente si elle existe, sinon à la page d'accueil.
   * @param {import('vue-router').Router} router - Instance du routeur
   */
  function goBack(router) {
    if (previousRoute.value) {
      router.push(previousRoute.value.fullPath)
    } else {
      router.push('/')
    }
  }

  // --- État de chargement ---

  /**
   * Affiche un indicateur de chargement global.
   * @param {string} message - Message optionnel
   */
  function startLoading(message = 'Chargement...') {
    isLoading.value = true
    loadingMessage.value = message
  }

  /**
   * Masque l'indicateur de chargement global.
   */
  function stopLoading() {
    isLoading.value = false
    loadingMessage.value = ''
  }

  /**
   * Définit un message d'erreur global.
   * @param {string|Error} err - Message ou erreur
   */
  function setError(err) {
    if (typeof err === 'string') {
      error.value = err
    } else if (err instanceof Error) {
      error.value = err.message
    } else {
      error.value = 'Une erreur inattendue est survenue.'
    }
    // Afficher une notification
    showGlobalNotification(error.value, 'error')
  }

  /**
   * Efface l'erreur globale.
   */
  function clearError() {
    error.value = null
  }

  // --- Notifications globales ---

  /**
   * Affiche une notification globale (pour les erreurs critiques, maintenance, etc.)
   * @param {string} message - Message
   * @param {string} type - 'info', 'warning', 'error', 'success'
   * @param {number} duration - Durée en ms (0 pour persistant)
   */
  function showGlobalNotification(message, type = 'info', duration = 5000) {
    globalNotification.value = { message, type, duration }
    if (duration > 0) {
      setTimeout(() => {
        if (globalNotification.value && globalNotification.value.message === message) {
          globalNotification.value = null
        }
      }, duration)
    }
  }

  /**
   * Ferme la notification globale.
   */
  function closeGlobalNotification() {
    globalNotification.value = null
  }

  // --- Sidebar (mobile) ---

  function openSidebar() {
    isSidebarOpen.value = true
  }

  function closeSidebar() {
    isSidebarOpen.value = false
  }

  function toggleSidebar() {
    isSidebarOpen.value = !isSidebarOpen.value
  }

  // --- Détection mobile ---

  /**
   * Met à jour le statut mobile en fonction de la largeur de l'écran.
   */
  function checkMobile() {
    if (typeof window !== 'undefined') {
      isMobile.value = window.innerWidth < 768
    }
  }

  // --- Mode maintenance ---

  function enableMaintenance(message = 'L\'application est en maintenance.') {
    isMaintenanceMode.value = true
    maintenanceMessage.value = message
  }

  function disableMaintenance() {
    isMaintenanceMode.value = false
    maintenanceMessage.value = ''
  }

  // ==========================================================================
  //  Initialisation
  // ==========================================================================

  // Initialiser le thème au chargement
  if (typeof window !== 'undefined') {
    initTheme()
    checkMobile()
    // Écouter les redimensionnements pour la détection mobile
    window.addEventListener('resize', checkMobile)
  }

  // ==========================================================================
  //  Retour
  // ==========================================================================

  return {
    // État
    theme,
    isDark,
    isLight,
    activeTab,
    previousRoute,
    isLoading,
    loadingMessage,
    error,
    isMobile,
    isSidebarOpen,
    isSearchFocused,
    appVersion,
    isMaintenanceMode,
    maintenanceMessage,
    globalNotification,

    // Getters
    currentThemeLabel,
    isDarkMode,
    themeIcon,
    hasError,
    isReady,

    // Actions
    initTheme,
    setTheme,
    toggleTheme,
    setActiveTab,
    setPreviousRoute,
    goBack,
    startLoading,
    stopLoading,
    setError,
    clearError,
    showGlobalNotification,
    closeGlobalNotification,
    openSidebar,
    closeSidebar,
    toggleSidebar,
    checkMobile,
    enableMaintenance,
    disableMaintenance,
  }
})

// ==========================================================================
//  Export du store avec persistence (optionnelle)
// ==========================================================================

// Si vous utilisez pinia-plugin-persistedstate, vous pouvez ajouter :
// useAppStore.$persist = true
// Mais nous laissons l'utilisateur configurer selon ses besoins.

export default useAppStore
