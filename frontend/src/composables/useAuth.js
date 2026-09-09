// ==========================================================================
//  NexusDL 2.0 - useAuth Composable
//  Fichier : frontend/src/composables/useAuth.js
//  Description : Gestion de l'authentification (login, logout, token, etc.)
//  Version : 2.0.0
// ==========================================================================

import { ref, computed, watch, inject, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { useApi } from '@/composables/useApi'

// ==========================================================================
//  Constantes
// ==========================================================================

const TOKEN_KEY = 'auth_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user_data'

// ==========================================================================
//  Composable
// ==========================================================================

/**
 * Composable pour gérer l'authentification et l'état utilisateur.
 * Fournit les méthodes login, logout, refresh, et les états réactifs.
 * Utilise useApi pour les requêtes HTTP et useToast pour les notifications.
 *
 * @param {Object} options - Options de configuration
 * @param {string} options.loginEndpoint - Endpoint de login (par défaut: /auth/login)
 * @param {string} options.refreshEndpoint - Endpoint de refresh (par défaut: /auth/refresh)
 * @param {string} options.registerEndpoint - Endpoint d'inscription (par défaut: /auth/register)
 * @param {string} options.logoutEndpoint - Endpoint de logout (par défaut: /auth/logout)
 * @param {string} options.meEndpoint - Endpoint user info (par défaut: /auth/me)
 * @param {boolean} options.autoRefresh - Tenter de rafraîchir automatiquement (défaut: true)
 * @param {number} options.refreshThreshold - Délai avant expiration pour refresh (ms, défaut: 60000)
 * @param {Function} options.onLogin - Callback après login
 * @param {Function} options.onLogout - Callback après logout
 * @returns {Object} - Méthodes et états réactifs
 */
export function useAuth(options = {}) {
  // --------------------------------------------------------------------------
  //  Injection des dépendances
  // --------------------------------------------------------------------------
  const router = inject('router', null) || useRouter()
  const toast = useToast()
  const api = useApi()

  // --------------------------------------------------------------------------
  //  Configuration
  // --------------------------------------------------------------------------
  const {
    loginEndpoint = '/auth/login',
    refreshEndpoint = '/auth/refresh',
    registerEndpoint = '/auth/register',
    logoutEndpoint = '/auth/logout',
    meEndpoint = '/auth/me',
    autoRefresh = true,
    refreshThreshold = 60000, // 1 minute avant expiration
    onLogin = null,
    onLogout = null,
  } = options

  // --------------------------------------------------------------------------
  //  État réactif
  // --------------------------------------------------------------------------
  const user = ref(null)
  const token = ref(null)
  const refreshToken = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isUser = computed(() => user.value?.role === 'user')
  const userId = computed(() => user.value?.id)
  const username = computed(() => user.value?.username)
  const email = computed(() => user.value?.email)

  // Timer pour le refresh automatique
  let refreshTimer = null

  // --------------------------------------------------------------------------
  //  Initialisation : charger les données depuis le localStorage
  // --------------------------------------------------------------------------
  function loadStoredAuth() {
    try {
      const storedToken = localStorage.getItem(TOKEN_KEY)
      const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      const storedUser = localStorage.getItem(USER_KEY)

      if (storedToken) {
        token.value = storedToken
        // Vérifier si le token est expiré (approximatif via JWT)
        if (isTokenExpired(storedToken)) {
          // Si expiré, on essaye de rafraîchir
          if (storedRefreshToken) {
            refreshToken.value = storedRefreshToken
            attemptRefresh()
          } else {
            clearAuth()
          }
        } else {
          if (storedRefreshToken) {
            refreshToken.value = storedRefreshToken
          }
          if (storedUser) {
            try {
              user.value = JSON.parse(storedUser)
            } catch (_) {
              user.value = null
            }
          }
          // Programmer le rafraîchissement automatique
          if (autoRefresh) {
            scheduleRefresh(storedToken)
          }
        }
      } else if (storedRefreshToken) {
        // On n'a pas de token, mais on a un refresh → on tente de récupérer
        refreshToken.value = storedRefreshToken
        attemptRefresh()
      }
    } catch (_) {
      // Échec de lecture, on ignore
    }
  }

  // --------------------------------------------------------------------------
  //  Fonctions utilitaires (JWT)
  // --------------------------------------------------------------------------
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

  function isTokenExpired(tokenStr) {
    const payload = parseJwt(tokenStr)
    if (!payload) return true
    const exp = payload.exp
    if (!exp) return false // pas d'expiration, on considère valide
    const now = Math.floor(Date.now() / 1000)
    return now >= exp
  }

  function getTokenExpiry(tokenStr) {
    const payload = parseJwt(tokenStr)
    if (!payload) return null
    return payload.exp ? new Date(payload.exp * 1000) : null
  }

  function getTokenRemainingTime(tokenStr) {
    const expiry = getTokenExpiry(tokenStr)
    if (!expiry) return Infinity
    const now = Date.now()
    return expiry.getTime() - now
  }

  // --------------------------------------------------------------------------
  //  Sauvegarde / effacement des données
  // --------------------------------------------------------------------------
  function persistAuth(tokenVal, refreshTokenVal, userVal) {
    if (tokenVal) {
      localStorage.setItem(TOKEN_KEY, tokenVal)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
    if (refreshTokenVal) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshTokenVal)
    } else {
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    }
    if (userVal) {
      localStorage.setItem(USER_KEY, JSON.stringify(userVal))
    } else {
      localStorage.removeItem(USER_KEY)
    }
  }

  function clearAuth() {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    if (refreshTimer) {
      clearTimeout(refreshTimer)
      refreshTimer = null
    }
  }

  // --------------------------------------------------------------------------
  //  Méthodes de l'API
  // --------------------------------------------------------------------------

  /**
   * Connexion de l'utilisateur.
   * @param {string} username - Nom d'utilisateur ou email
   * @param {string} password - Mot de passe
   * @param {boolean} rememberMe - Mémoriser la session (défaut: true)
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async function login(username, password, rememberMe = true) {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.post(loginEndpoint, {
        username,
        password,
        remember_me: rememberMe,
      })

      // Structure attendue: { access_token, refresh_token, user: { ... } }
      const { access_token, refresh_token, user: userData } = response

      if (access_token) {
        token.value = access_token
      }
      if (refresh_token) {
        refreshToken.value = refresh_token
      }
      if (userData) {
        user.value = userData
      }

      // Persister
      persistAuth(access_token, refresh_token, userData)

      // Programmer le refresh automatique
      if (autoRefresh && access_token) {
        scheduleRefresh(access_token)
      }

      // Appel du callback
      if (onLogin) {
        onLogin(userData, access_token)
      }

      toast.success(`Bienvenue ${userData?.username || 'utilisateur'} !`, '👋')
      return response
    } catch (err) {
      error.value = err
      toast.error(`Erreur de connexion : ${err.message || 'Identifiants invalides'}`, '❌')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Inscription d'un nouvel utilisateur.
   * @param {Object} userData - { username, email, password, full_name? }
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async function register(userData) {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.post(registerEndpoint, userData)
      // Généralement on renvoie un token et l'utilisateur
      const { access_token, refresh_token, user: newUser } = response
      if (access_token) {
        token.value = access_token
      }
      if (refresh_token) {
        refreshToken.value = refresh_token
      }
      if (newUser) {
        user.value = newUser
      }
      persistAuth(access_token, refresh_token, newUser)
      if (autoRefresh && access_token) {
        scheduleRefresh(access_token)
      }
      toast.success('Inscription réussie ! Bienvenue.', '🎉')
      return response
    } catch (err) {
      error.value = err
      toast.error(`Erreur d'inscription : ${err.message || 'Veuillez vérifier vos données'}`, '❌')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Rafraîchit le token d'accès.
   * @returns {Promise<Object>} - Réponse de l'API
   */
  async function refresh() {
    if (!refreshToken.value) {
      throw new Error('Aucun refresh token disponible')
    }
    isLoading.value = true
    error.value = null
    try {
      const response = await api.post(refreshEndpoint, {
        refresh_token: refreshToken.value,
      })
      const { access_token, refresh_token: newRefresh, user: userData } = response
      if (access_token) {
        token.value = access_token
      }
      if (newRefresh) {
        refreshToken.value = newRefresh
      }
      if (userData) {
        user.value = userData
      }
      persistAuth(access_token, newRefresh || refreshToken.value, userData)
      if (autoRefresh && access_token) {
        scheduleRefresh(access_token)
      }
      toast.info('Session rafraîchie.', '🔄')
      return response
    } catch (err) {
      error.value = err
      // Si le refresh échoue, on déconnecte
      toast.error('Session expirée, veuillez vous reconnecter.', '🔐')
      logout()
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Déconnexion.
   */
  async function logout() {
    isLoading.value = true
    try {
      // Appel au endpoint de logout si disponible
      if (logoutEndpoint) {
        try {
          await api.post(logoutEndpoint, {})
        } catch (_) {
          // Ignorer les erreurs du logout (côté serveur)
        }
      }
    } catch (_) {
      // Ignorer
    } finally {
      clearAuth()
      isLoading.value = false
      if (onLogout) {
        onLogout()
      }
      toast.info('Vous êtes déconnecté.', '👋')
      // Rediriger vers la page de connexion
      if (router && router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
  }

  /**
   * Tente de rafraîchir automatiquement le token.
   * Si le token est expiré, on essaie le refresh.
   * Sinon, on planifie un refresh avant expiration.
   */
  function attemptRefresh() {
    if (refreshToken.value) {
      return refresh().catch(() => {
        // Échec, on logout déjà fait dans refresh
      })
    }
    return Promise.reject(new Error('Pas de refresh token'))
  }

  /**
   * Planifie un rafraîchissement automatique du token avant son expiration.
   * @param {string} tokenStr - Token à vérifier
   */
  function scheduleRefresh(tokenStr) {
    if (refreshTimer) {
      clearTimeout(refreshTimer)
      refreshTimer = null
    }
    if (!tokenStr || !autoRefresh) return

    const remaining = getTokenRemainingTime(tokenStr)
    // Si le token expire dans moins de refreshThreshold, on rafraîchit immédiatement
    // Sinon, on planifie à (remaining - refreshThreshold) ms
    let delay = remaining - refreshThreshold
    if (delay <= 0) {
      // Déjà proche de l'expiration
      attemptRefresh()
      return
    }
    // Ne pas planifier au-delà de 24h
    if (delay > 24 * 60 * 60 * 1000) {
      delay = 24 * 60 * 60 * 1000
    }
    refreshTimer = setTimeout(() => {
      attemptRefresh()
    }, delay)
  }

  /**
   * Récupère les informations de l'utilisateur courant.
   * @param {boolean} force - Forcer la récupération depuis le serveur.
   * @returns {Promise<Object>} - Données utilisateur
   */
  async function fetchUser(force = false) {
    if (!token.value) {
      throw new Error('Non authentifié')
    }
    if (user.value && !force) {
      return user.value
    }
    try {
      const response = await api.get(meEndpoint)
      if (response?.user) {
        user.value = response.user
        persistAuth(token.value, refreshToken.value, user.value)
      } else if (response) {
        user.value = response
        persistAuth(token.value, refreshToken.value, user.value)
      }
      return user.value
    } catch (err) {
      // Si erreur 401, on logout
      if (err.response?.status === 401) {
        logout()
      }
      throw err
    }
  }

  /**
   * Vérifie si l'utilisateur a un rôle spécifique.
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

  // --------------------------------------------------------------------------
  //  Cycle de vie
  // --------------------------------------------------------------------------
  onMounted(() => {
    loadStoredAuth()
  })

  // --------------------------------------------------------------------------
  //  Retour du composable
  // --------------------------------------------------------------------------

  return {
    // États réactifs
    user,
    token,
    refreshToken,
    isLoading,
    error,
    isAuthenticated,
    isAdmin,
    isUser,
    userId,
    username,
    email,

    // Méthodes publiques
    login,
    register,
    logout,
    refresh,
    fetchUser,
    hasRole,
    clearAuth,
    loadStoredAuth,
    scheduleRefresh,
    isTokenExpired,
    getTokenRemainingTime,

    // Utilitaires
    parseJwt,
  }
}

// ==========================================================================
//  Export par défaut (pour utilisation avec `useAuth` nommé)
// ==========================================================================

export default useAuth
