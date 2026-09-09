// ==========================================================================
//  NexusDL 2.0 - Auth Store (Pinia)
//  Fichier : frontend/src/stores/auth.js
//  Description : Store d'authentification (login, logout, token, utilisateur)
//  Version : 2.0.0
// ==========================================================================

import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useAppStore } from '@/stores/app'

// ==========================================================================
//  Constantes
// ==========================================================================

const TOKEN_KEY = 'auth_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user_data'
const REMEMBER_KEY = 'remember_me'

/**
 * Store d'authentification.
 * Gère la connexion, la déconnexion, le refresh token, la persistance.
 */
export const useAuthStore = defineStore('auth', () => {
  // ==========================================================================
  //  Dépendances
  // ==========================================================================

  const api = useApi()
  const toast = useToast()
  const appStore = useAppStore()

  // ==========================================================================
  //  État
  // ==========================================================================

  const token = ref(null)
  const refreshToken = ref(null)
  const user = ref(null)
  const rememberMe = ref(true)
  const isLoading = ref(false)
  const error = ref(null)
  const isInitialized = ref(false)

  // Timer pour le refresh automatique
  let refreshTimer = null

  // ==========================================================================
  //  Getters
  // ==========================================================================

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const isAdmin = computed(() => user.value?.role === 'admin')

  const isUser = computed(() => user.value?.role === 'user')

  const isGuest = computed(() => !isAuthenticated.value)

  const userId = computed(() => user.value?.id)

  const username = computed(() => user.value?.username)

  const userEmail = computed(() => user.value?.email)

  const userFullName = computed(() => user.value?.full_name || user.value?.username)

  const userAvatar = computed(() => user.value?.avatar_url || null)

  const userRole = computed(() => user.value?.role || 'guest')

  const hasValidToken = computed(() => {
    if (!token.value) return false
    try {
      const payload = parseJwt(token.value)
      if (!payload) return false
      const exp = payload.exp
      if (!exp) return true // pas d'expiration, considéré valide
      const now = Math.floor(Date.now() / 1000)
      return now < exp
    } catch (_) {
      return false
    }
  })

  const tokenExpiry = computed(() => {
    if (!token.value) return null
    try {
      const payload = parseJwt(token.value)
      if (!payload || !payload.exp) return null
      return new Date(payload.exp * 1000)
    } catch (_) {
      return null
    }
  })

  const tokenRemainingSeconds = computed(() => {
    const expiry = tokenExpiry.value
    if (!expiry) return 0
    const remaining = (expiry.getTime() - Date.now()) / 1000
    return Math.max(0, remaining)
  })

  const isTokenExpired = computed(() => {
    if (!token.value) return true
    return tokenRemainingSeconds.value <= 0
  })

  const isTokenExpiringSoon = computed(() => {
    if (!token.value) return false
    // Expire dans moins de 5 minutes
    return tokenRemainingSeconds.value < 300
  })

  // ==========================================================================
  //  Fonctions utilitaires (JWT)
  // ==========================================================================

  /**
   * Parse un token JWT pour en extraire le payload.
   * @param {string} tokenStr - Token JWT
   * @returns {Object|null} - Payload du token
   */
  function parseJwt(tokenStr) {
    try {
      const base64Url = tokenStr.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
      return JSON.parse(jsonPayload)
    } catch (_) {
      return null
    }
  }

  /**
   * Vérifie si un token est expiré.
   * @param {string} tokenStr - Token JWT
   * @returns {boolean}
   */
  function isTokenExpiredFn(tokenStr) {
    if (!tokenStr) return true
    try {
      const payload = parseJwt(tokenStr)
      if (!payload) return true
      const exp = payload.exp
      if (!exp) return false
      return Math.floor(Date.now() / 1000) >= exp
    } catch (_) {
      return true
    }
  }

  // ==========================================================================
  //  Persistance
  // ==========================================================================

  /**
   * Persiste les données d'authentification dans le localStorage.
   */
  function persistAuth() {
    try {
      if (token.value) {
        localStorage.setItem(TOKEN_KEY, token.value)
      } else {
        localStorage.removeItem(TOKEN_KEY)
      }
      if (refreshToken.value && rememberMe.value) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken.value)
      } else {
        localStorage.removeItem(REFRESH_TOKEN_KEY)
      }
      if (user.value) {
        localStorage.setItem(USER_KEY, JSON.stringify(user.value))
      } else {
        localStorage.removeItem(USER_KEY)
      }
      localStorage.setItem(REMEMBER_KEY, String(rememberMe.value))
    } catch (_) {
      // En mode privé ou erreur, on ignore
    }
  }

  /**
   * Charge les données d'authentification depuis le localStorage.
   * @returns {boolean} - true si des données ont été chargées
   */
  function loadPersistedAuth() {
    try {
      const storedToken = localStorage.getItem(TOKEN_KEY)
      const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      const storedUser = localStorage.getItem(USER_KEY)
      const storedRemember = localStorage.getItem(REMEMBER_KEY)

      if (storedRemember !== null) {
        rememberMe.value = storedRemember === 'true'
      }

      if (storedToken) {
        token.value = storedToken
      }
      if (storedRefreshToken && rememberMe.value) {
        refreshToken.value = storedRefreshToken
      }
      if (storedUser) {
        try {
          user.value = JSON.parse(storedUser)
        } catch (_) {
          user.value = null
        }
      }
      return !!storedToken
    } catch (_) {
      return false
    }
  }

  /**
   * Efface toutes les données d'authentification.
   */
  function clearPersistedAuth() {
    try {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      localStorage.removeItem(REMEMBER_KEY)
    } catch (_) {
      // Ignorer
    }
  }

  // ==========================================================================
  //  Refresh automatique
  // ==========================================================================

  /**
   * Planifie un rafraîchissement automatique du token avant expiration.
   */
  function scheduleRefresh() {
    // Annuler le timer existant
    if (refreshTimer) {
      clearTimeout(refreshTimer)
      refreshTimer = null
    }

    if (!token.value) return

    const remaining = tokenRemainingSeconds.value
    // Si le token expire dans moins de 5 minutes, rafraîchir immédiatement
    if (remaining < 300 && remaining > 0) {
      attemptRefresh()
      return
    }
    // Si le token est déjà expiré, tenter un refresh
    if (remaining <= 0) {
      attemptRefresh()
      return
    }
    // Sinon, planifier à (remaining - 5 minutes) ms
    const delay = (remaining - 300) * 1000
    if (delay > 0) {
      refreshTimer = setTimeout(() => {
        attemptRefresh()
      }, delay)
    }
  }

  /**
   * Tente de rafraîchir le token d'accès.
   * @param {boolean} silent - Si true, n'affiche pas de notification
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async function attemptRefresh(silent = false) {
    if (!refreshToken.value) {
      if (!silent) {
        toast.warning('Session expirée, veuillez vous reconnecter.', '🔐')
      }
      await logout()
      return null
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await api.post('/auth/refresh', {
        refresh_token: refreshToken.value,
      })

      const { access_token, refresh_token: newRefreshToken, user: userData } = response

      if (access_token) {
        token.value = access_token
      }
      if (newRefreshToken && rememberMe.value) {
        refreshToken.value = newRefreshToken
      }
      if (userData) {
        user.value = userData
      }

      persistAuth()

      // Reprogrammer le refresh
      scheduleRefresh()

      if (!silent) {
        toast.info('Session rafraîchie avec succès.', '🔄')
      }

      return response
    } catch (err) {
      error.value = err
      // Si le refresh échoue, on déconnecte
      if (!silent) {
        toast.error('Session expirée, veuillez vous reconnecter.', '🔐')
      }
      await logout()
      return null
    } finally {
      isLoading.value = false
    }
  }

  // ==========================================================================
  //  Actions principales
  // ==========================================================================

  /**
   * Connexion de l'utilisateur.
   * @param {string} username - Nom d'utilisateur ou email
   * @param {string} password - Mot de passe
   * @param {boolean} remember - Mémoriser la session
   * @param {string} redirectTo - Route vers laquelle rediriger après connexion
   * @returns {Promise<Object>} - Données utilisateur
   */
  async function login(username, password, remember = true, redirectTo = '/') {
    if (!username || !password) {
      toast.error('Veuillez remplir tous les champs.', '❌')
      throw new Error('Les champs sont requis')
    }

    isLoading.value = true
    error.value = null
    appStore.startLoading('Connexion en cours...')

    try {
      rememberMe.value = remember

      const response = await api.post('/auth/login', {
        username,
        password,
        remember_me: remember,
      })

      // Structure attendue: { access_token, refresh_token, user: { ... } }
      const { access_token, refresh_token: refreshTok, user: userData } = response

      if (!access_token || !userData) {
        throw new Error('Réponse du serveur invalide')
      }

      token.value = access_token
      if (refreshTok && remember) {
        refreshToken.value = refreshTok
      } else {
        refreshToken.value = null
      }
      user.value = userData

      persistAuth()

      // Planifier le refresh automatique
      scheduleRefresh()

      toast.success(`Bienvenue ${userData.username || 'utilisateur'} ! 👋`)

      // Redirection
      if (redirectTo) {
        try {
          const router = useRouter()
          router.push(redirectTo)
        } catch (_) {
          // Pas de routeur disponible
        }
      }

      return userData
    } catch (err) {
      error.value = err
      const message = err?.response?.data?.detail || err.message || 'Identifiants invalides'
      toast.error(`Échec de la connexion : ${message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
      appStore.stopLoading()
    }
  }

  /**
   * Déconnexion de l'utilisateur.
   * @param {string} redirectTo - Route vers laquelle rediriger après déconnexion
   * @returns {Promise<void>}
   */
  async function logout(redirectTo = '/login') {
    isLoading.value = true

    try {
      // Appel au endpoint de logout si disponible
      try {
        await api.post('/auth/logout', {})
      } catch (_) {
        // Ignorer les erreurs du logout serveur
      }
    } catch (_) {
      // Ignorer
    } finally {
      // Nettoyer l'état
      token.value = null
      refreshToken.value = null
      user.value = null

      if (refreshTimer) {
        clearTimeout(refreshTimer)
        refreshTimer = null
      }

      clearPersistedAuth()

      // Redirection
      try {
        const router = useRouter()
        if (redirectTo) {
          router.push(redirectTo)
        }
      } catch (_) {
        // Pas de routeur disponible
      }

      isLoading.value = false
      toast.info('Vous êtes déconnecté.', '👋')
    }
  }

  /**
   * Inscription d'un nouvel utilisateur.
   * @param {Object} userData - Données utilisateur (username, email, password, full_name?)
   * @param {string} redirectTo - Route vers laquelle rediriger après inscription
   * @returns {Promise<Object>} - Données utilisateur
   */
  async function register(userData, redirectTo = '/') {
    if (!userData.username || !userData.email || !userData.password) {
      toast.error('Veuillez remplir tous les champs.', '❌')
      throw new Error('Tous les champs sont requis')
    }

    isLoading.value = true
    error.value = null
    appStore.startLoading('Inscription en cours...')

    try {
      const response = await api.post('/auth/register', userData)

      const { access_token, refresh_token: refreshTok, user: newUser } = response

      if (access_token && newUser) {
        token.value = access_token
        if (refreshTok && rememberMe.value) {
          refreshToken.value = refreshTok
        }
        user.value = newUser
        persistAuth()
        scheduleRefresh()
      }

      toast.success('Inscription réussie ! Bienvenue.', '🎉')

      if (redirectTo) {
        try {
          const router = useRouter()
          router.push(redirectTo)
        } catch (_) {}
      }

      return newUser
    } catch (err) {
      error.value = err
      const message = err?.response?.data?.detail || err.message || 'Erreur lors de l\'inscription'
      toast.error(`Échec de l'inscription : ${message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
      appStore.stopLoading()
    }
  }

  /**
   * Récupère les informations de l'utilisateur courant depuis le serveur.
   * @param {boolean} force - Forcer la récupération même si les données sont déjà présentes
   * @returns {Promise<Object>} - Données utilisateur
   */
  async function fetchUser(force = false) {
    if (!token.value) {
      throw new Error('Non authentifié')
    }

    if (user.value && !force) {
      return user.value
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await api.get('/auth/me')
      // La réponse peut être { user: {...} } ou directement les données
      const userData = response.user || response
      if (userData) {
        user.value = userData
        persistAuth()
      }
      return user.value
    } catch (err) {
      error.value = err
      if (err.response?.status === 401) {
        // Token invalide, on déconnecte
        await logout()
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Change le mot de passe de l'utilisateur.
   * @param {string} oldPassword - Ancien mot de passe
   * @param {string} newPassword - Nouveau mot de passe
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async function changePassword(oldPassword, newPassword) {
    if (!token.value) {
      throw new Error('Non authentifié')
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await api.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      })
      toast.success('Mot de passe modifié avec succès.', '🔐')
      return response
    } catch (err) {
      error.value = err
      const message = err?.response?.data?.detail || err.message || 'Erreur lors du changement de mot de passe'
      toast.error(message, '❌')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Vérifie les privilèges de l'utilisateur.
   * @param {string|string[]} roles - Rôle(s) autorisé(s)
   * @returns {boolean}
   */
  function hasRole(roles) {
    if (!user.value) return false
    const userRole = user.value.role
    if (Array.isArray(roles)) {
      return roles.includes(userRole)
    }
    return userRole === roles
  }

  /**
   * Vérifie si l'utilisateur est authentifié.
   * @returns {boolean}
   */
  function check() {
    return isAuthenticated.value && hasValidToken.value
  }

  // ==========================================================================
  //  Initialisation
  // ==========================================================================

  /**
   * Initialise le store (charge les données persistées).
   * @param {boolean} autoRefresh - Tenter de rafraîchir automatiquement si le token est expiré
   * @returns {Promise<boolean>} - true si l'utilisateur est authentifié
   */
  async function initialize(autoRefresh = true) {
    if (isInitialized.value) {
      return isAuthenticated.value
    }

    // Charger les données persistées
    const hasStored = loadPersistedAuth()

    if (!hasStored || !token.value) {
      isInitialized.value = true
      return false
    }

    // Vérifier la validité du token
    if (isTokenExpiredFn(token.value)) {
      // Token expiré, tenter un refresh
      if (autoRefresh && refreshToken.value) {
        try {
          const result = await attemptRefresh(true)
          if (result) {
            isInitialized.value = true
            return true
          }
        } catch (_) {
          // Échec du refresh
        }
      }
      // Pas de refresh ou échec, déconnecter
      await logout()
      isInitialized.value = true
      return false
    }

    // Token valide, planifier le refresh
    scheduleRefresh()

    // Si on a un utilisateur, on le garde, sinon on le récupère
    if (!user.value) {
      try {
        await fetchUser(true)
      } catch (_) {
        // Échec de récupération, on continue avec les données existantes
      }
    }

    isInitialized.value = true
    return true
  }

  // ==========================================================================
  //  Watchers
  // ==========================================================================

  // Persister automatiquement les changements
  watch([token, refreshToken, user, rememberMe], () => {
    persistAuth()
  }, { deep: true })

  // Si le token change, reprogrammer le refresh
  watch(token, (newToken, oldToken) => {
    if (newToken !== oldToken && newToken) {
      scheduleRefresh()
    }
  })

  // ==========================================================================
  //  Retour
  // ==========================================================================

  return {
    // État
    token,
    refreshToken,
    user,
    rememberMe,
    isLoading,
    error,
    isInitialized,

    // Getters
    isAuthenticated,
    isAdmin,
    isUser,
    isGuest,
    userId,
    username,
    userEmail,
    userFullName,
    userAvatar,
    userRole,
    hasValidToken,
    tokenExpiry,
    tokenRemainingSeconds,
    isTokenExpired,
    isTokenExpiringSoon,

    // Actions
    login,
    logout,
    register,
    fetchUser,
    changePassword,
    hasRole,
    check,
    initialize,
    refresh: attemptRefresh,
    scheduleRefresh,
    parseJwt,
    isTokenExpiredFn,
    persistAuth,
    loadPersistedAuth,
    clearPersistedAuth,
  }
})

// ==========================================================================
//  Import du routeur (au moment de l'utilisation, pour éviter circular)
// ==========================================================================

import { useRouter } from 'vue-router'

// Le store peut utiliser useRouter() directement maintenant,
// mais nous l'avons déjà utilisé via try/catch dans les actions.

export default useAuthStore
