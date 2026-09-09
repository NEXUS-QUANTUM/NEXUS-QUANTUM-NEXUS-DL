// ==========================================================================
//  NexusDL 2.0 - useTheme Composable
//  Fichier : frontend/src/composables/useTheme.js
//  Description : Gestion du thème (sombre/clair) avec persistance et détection système
//  Version : 2.0.0
// ==========================================================================

import { ref, computed, watch, onMounted, onUnmounted, inject } from 'vue'

// ==========================================================================
//  Constantes
// ==========================================================================

const STORAGE_KEY = 'nexus-theme'
const THEME_DARK = 'dark'
const THEME_LIGHT = 'light'
const THEME_SYSTEM = 'system'

// ==========================================================================
//  Composable
// ==========================================================================

/**
 * Composable pour gérer le thème de l'application.
 * Supporte les thèmes sombre, clair et automatique (suivant le système).
 * Persiste le choix dans le localStorage et synchronise entre les onglets.
 *
 * @param {Object} options - Options de configuration
 * @param {string} options.defaultTheme - Thème par défaut ('dark', 'light', 'system')
 * @param {string} options.darkClass - Classe CSS pour le mode sombre (défaut: 'dark-mode')
 * @param {string} options.lightClass - Classe CSS pour le mode clair (défaut: 'light-mode')
 * @param {HTMLElement} options.targetElement - Élément cible (défaut: document.body)
 * @param {boolean} options.persist - Persister le choix (défaut: true)
 * @param {boolean} options.followSystem - Suivre le système si choix = system (défaut: true)
 * @param {Function} options.onChange - Callback lors du changement de thème
 * @returns {Object} - Méthodes et états réactifs
 */
export function useTheme(options = {}) {
  // --------------------------------------------------------------------------
  //  Configuration
  // --------------------------------------------------------------------------
  const {
    defaultTheme = THEME_SYSTEM,
    darkClass = 'dark-mode',
    lightClass = 'light-mode',
    targetElement = document.body,
    persist = true,
    followSystem = true,
    onChange = null,
  } = options

  // --------------------------------------------------------------------------
  //  État réactif
  // --------------------------------------------------------------------------
  const currentTheme = ref(defaultTheme) // 'dark', 'light', 'system'
  const isDark = ref(false)
  const isLight = ref(false)
  const systemPrefersDark = ref(false)
  const isLoading = ref(true)
  const error = ref(null)

  // --------------------------------------------------------------------------
  //  Compteurs et abonnements
  // --------------------------------------------------------------------------
  let mediaQuery = null
  let mediaListener = null
  let storageListener = null

  // --------------------------------------------------------------------------
  //  Fonctions de détection du système
  // --------------------------------------------------------------------------

  /**
   * Détecte si le système préfère le mode sombre.
   * @returns {boolean}
   */
  function getSystemPreference() {
    try {
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return true
      }
      return false
    } catch (_) {
      return false
    }
  }

  /**
   * Écoute les changements de préférence système.
   * @param {Function} callback - Fonction appelée lors du changement
   * @returns {Function} - Fonction de nettoyage
   */
  function watchSystemPreference(callback) {
    try {
      const mq = window.matchMedia('(prefers-color-scheme: dark)')
      const listener = (e) => {
        const prefersDark = e.matches
        systemPrefersDark.value = prefersDark
        if (callback) {
          callback(prefersDark)
        }
        // Si le thème est "system", on applique automatiquement
        if (currentTheme.value === THEME_SYSTEM) {
          applyTheme()
        }
      }
      mq.addEventListener('change', listener)
      // Initialiser
      systemPrefersDark.value = getSystemPreference()
      return () => {
        mq.removeEventListener('change', listener)
      }
    } catch (_) {
      // Si matchMedia n'est pas supporté
      return () => {}
    }
  }

  // --------------------------------------------------------------------------
  //  Application du thème
  // --------------------------------------------------------------------------

  /**
   * Applique le thème actuel sur l'élément cible.
   * Ajoute/supprime les classes CSS correspondantes.
   */
  function applyTheme() {
    try {
      const target = targetElement || document.body
      if (!target) return

      let shouldBeDark = false

      if (currentTheme.value === THEME_SYSTEM) {
        shouldBeDark = systemPrefersDark.value
      } else {
        shouldBeDark = currentTheme.value === THEME_DARK
      }

      isDark.value = shouldBeDark
      isLight.value = !shouldBeDark

      // Supprimer les classes existantes
      target.classList.remove(darkClass, lightClass)

      // Ajouter la classe appropriée
      if (shouldBeDark) {
        target.classList.add(darkClass)
      } else {
        target.classList.add(lightClass)
      }

      // Mettre à jour la meta tag pour la barre d'adresse (mobile)
      updateMetaThemeColor(shouldBeDark)

      // Mettre à jour la variable CSS pour le fond
      document.documentElement.style.setProperty(
        '--bg-primary',
        shouldBeDark ? '#0a0e1a' : '#f4f6fa'
      )

      // Callback si défini
      if (onChange) {
        onChange({
          theme: currentTheme.value,
          isDark: shouldBeDark,
          isLight: !shouldBeDark,
        })
      }

      isLoading.value = false
    } catch (err) {
      error.value = err
      isLoading.value = false
      console.error('❌ Erreur lors de l\'application du thème:', err)
    }
  }

  /**
   * Met à jour la meta tag theme-color pour les navigateurs mobiles.
   * @param {boolean} isDarkMode - Si le mode sombre est actif
   */
  function updateMetaThemeColor(isDarkMode) {
    try {
      let meta = document.querySelector('meta[name="theme-color"]')
      if (!meta) {
        meta = document.createElement('meta')
        meta.name = 'theme-color'
        document.head.appendChild(meta)
      }
      meta.content = isDarkMode ? '#0a0e1a' : '#f4f6fa'
    } catch (_) {
      // Ignorer si non supporté
    }
  }

  // --------------------------------------------------------------------------
  //  Sauvegarde et chargement
  // --------------------------------------------------------------------------

  /**
   * Sauvegarde le thème dans le localStorage.
   */
  function persistTheme() {
    if (!persist) return
    try {
      localStorage.setItem(STORAGE_KEY, currentTheme.value)
    } catch (_) {
      // Ignorer les erreurs de localStorage (ex: en mode privé)
    }
  }

  /**
   * Charge le thème depuis le localStorage.
   * @returns {string|null} - Thème stocké ou null
   */
  function loadPersistedTheme() {
    if (!persist) return null
    try {
      return localStorage.getItem(STORAGE_KEY)
    } catch (_) {
      return null
    }
  }

  // --------------------------------------------------------------------------
  //  Méthodes publiques
  // --------------------------------------------------------------------------

  /**
   * Définit le thème manuellement.
   * @param {string} theme - 'dark', 'light' ou 'system'
   */
  function setTheme(theme) {
    if (![THEME_DARK, THEME_LIGHT, THEME_SYSTEM].includes(theme)) {
      console.warn(`Thème invalide: ${theme}. Utilisation de 'system'.`)
      theme = THEME_SYSTEM
    }
    currentTheme.value = theme
    persistTheme()
    applyTheme()
  }

  /**
   * Bascule entre sombre et clair (ignore le mode system).
   * Si le thème est 'system', on passe au mode opposé du système.
   */
  function toggleTheme() {
    if (currentTheme.value === THEME_SYSTEM) {
      // Si on est en mode système, on passe au mode opposé du système
      const shouldBeDark = systemPrefersDark.value
      setTheme(shouldBeDark ? THEME_LIGHT : THEME_DARK)
    } else if (currentTheme.value === THEME_DARK) {
      setTheme(THEME_LIGHT)
    } else {
      setTheme(THEME_DARK)
    }
  }

  /**
   * Active le mode sombre.
   */
  function enableDark() {
    setTheme(THEME_DARK)
  }

  /**
   * Active le mode clair.
   */
  function enableLight() {
    setTheme(THEME_LIGHT)
  }

  /**
   * Active le mode système.
   */
  function enableSystem() {
    setTheme(THEME_SYSTEM)
  }

  /**
   * Recharge et applique le thème actuel.
   * Utile après un changement de préférence système.
   */
  function refresh() {
    systemPrefersDark.value = getSystemPreference()
    applyTheme()
  }

  /**
   * Initialise le thème (charge depuis le stockage + applique).
   */
  function initTheme() {
    try {
      const stored = loadPersistedTheme()
      if (stored && [THEME_DARK, THEME_LIGHT, THEME_SYSTEM].includes(stored)) {
        currentTheme.value = stored
      } else {
        currentTheme.value = defaultTheme
      }
      systemPrefersDark.value = getSystemPreference()
      applyTheme()
      persistTheme()
    } catch (err) {
      error.value = err
      // Fallback: utiliser le thème par défaut
      currentTheme.value = defaultTheme
      applyTheme()
    }
  }

  // ==========================================================================
  //  Synchronisation entre onglets
  // ==========================================================================

  function setupCrossTabSync() {
    if (!persist) return
    try {
      storageListener = (event) => {
        if (event.key === STORAGE_KEY && event.newValue) {
          const newTheme = event.newValue
          if ([THEME_DARK, THEME_LIGHT, THEME_SYSTEM].includes(newTheme)) {
            // Si le thème change dans un autre onglet, on le synchronise
            currentTheme.value = newTheme
            applyTheme()
          }
        }
      }
      window.addEventListener('storage', storageListener)
    } catch (_) {
      // Ignorer
    }
  }

  function cleanupCrossTabSync() {
    if (storageListener) {
      window.removeEventListener('storage', storageListener)
      storageListener = null
    }
  }

  // ==========================================================================
  //  État dérivé
  // ==========================================================================

  const themeLabel = computed(() => {
    if (currentTheme.value === THEME_SYSTEM) {
      return `Système (${isDark.value ? 'sombre' : 'clair'})`
    }
    return isDark.value ? 'Sombre' : 'Clair'
  })

  const themeIcon = computed(() => {
    if (currentTheme.value === THEME_SYSTEM) {
      return '🖥️'
    }
    return isDark.value ? '🌙' : '☀️'
  })

  // ==========================================================================
  //  Cycle de vie
  // ==========================================================================

  // Initialisation au montage
  onMounted(() => {
    // Initialiser le thème
    initTheme()

    // Écouter les préférences système
    if (followSystem) {
      const cleanup = watchSystemPreference((prefersDark) => {
        // Si on est en mode système, mettre à jour
        if (currentTheme.value === THEME_SYSTEM) {
          applyTheme()
        }
      })
      // Stocker la fonction de nettoyage
      mediaListener = cleanup
    }

    // Synchronisation entre onglets
    setupCrossTabSync()
  })

  // Nettoyage à la destruction
  onUnmounted(() => {
    if (mediaListener && typeof mediaListener === 'function') {
      mediaListener()
      mediaListener = null
    }
    cleanupCrossTabSync()
  })

  // Watcher pour persister les changements
  watch(currentTheme, () => {
    persistTheme()
    applyTheme()
  })

  // --------------------------------------------------------------------------
  //  Retour du composable
  // --------------------------------------------------------------------------

  return {
    // États réactifs
    currentTheme,
    isDark,
    isLight,
    systemPrefersDark,
    isLoading,
    error,

    // États dérivés
    themeLabel,
    themeIcon,

    // Méthodes
    setTheme,
    toggleTheme,
    enableDark,
    enableLight,
    enableSystem,
    refresh,
    applyTheme,
    initTheme,
    getSystemPreference,

    // Constantes
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM,
  }
}

// ==========================================================================
//  Export par défaut (pour utilisation avec `useTheme` nommé)
// ==========================================================================

export default useTheme
