// ==========================================================================
//  NexusDL 2.0 - useApi Composable
//  Fichier : frontend/src/composables/useApi.js
//  Description : Composable Vue.js pour les appels API avec Axios
//  Version : 2.0.0
// ==========================================================================

import { ref, inject, computed, shallowRef, toValue, watchEffect } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

// ==========================================================================
//  Configuration par défaut
// ==========================================================================

const DEFAULT_BASE_URL = import.meta.env.VITE_API_BASE || '/api'
const DEFAULT_TIMEOUT = 30000
const MAX_RETRIES = 3
const RETRY_DELAY = 1000

// ==========================================================================
//  Type des options
// ==========================================================================

/**
 * @typedef {Object} ApiOptions
 * @property {string} [baseURL] - URL de base de l'API
 * @property {number} [timeout] - Timeout en millisecondes
 * @property {Object} [headers] - Headers par défaut
 * @property {boolean} [withCredentials] - Envoyer les cookies
 * @property {number} [maxRetries] - Nombre maximal de tentatives
 * @property {number} [retryDelay] - Délai entre les tentatives (ms)
 * @property {Function} [onError] - Callback global d'erreur
 * @property {Function} [onSuccess] - Callback global de succès
 */

// ==========================================================================
//  Composable
// ==========================================================================

/**
 * Composable pour interagir avec l'API via Axios.
 * Gère l'authentification, les erreurs, les retries, les annulations et les
 * intercepteurs.
 *
 * @param {ApiOptions} options - Options de configuration
 * @returns {Object} - Méthodes et états réactifs
 */
export function useApi(options = {}) {
  // --------------------------------------------------------------------------
  //  Injection des dépendances globales
  // --------------------------------------------------------------------------
  const apiBase = inject('apiBase', DEFAULT_BASE_URL)
  const showToast = inject('showToast', null)

  // Store d'authentification (si disponible)
  let authStore = null
  try {
    authStore = useAuthStore()
  } catch (_) {
    // Pas de store, on utilisera le localStorage directement
  }

  // --------------------------------------------------------------------------
  //  État réactif local
  // --------------------------------------------------------------------------
  const isLoading = ref(false)
  const error = ref(null)
  const lastResponse = ref(null)
  const abortControllers = ref(new Map())

  // --------------------------------------------------------------------------
  //  Configuration de l'instance Axios
  // --------------------------------------------------------------------------
  const baseURL = options.baseURL || apiBase
  const timeout = options.timeout || DEFAULT_TIMEOUT
  const maxRetries = options.maxRetries || MAX_RETRIES
  const retryDelay = options.retryDelay || RETRY_DELAY

  // Création de l'instance Axios
  const instance = axios.create({
    baseURL,
    timeout,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options.headers,
    },
    withCredentials: options.withCredentials ?? false,
  })

  // --------------------------------------------------------------------------
  //  Intercepteurs
  // --------------------------------------------------------------------------

  // Intercepteur de requête : ajout du token JWT
  instance.interceptors.request.use(
    (config) => {
      // Récupérer le token depuis le store ou le localStorage
      let token = null
      if (authStore && authStore.token) {
        token = authStore.token
      } else {
        token = localStorage.getItem('auth_token')
      }

      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }

      // Ajouter un AbortController si non déjà présent
      if (!config.signal) {
        const controller = new AbortController()
        config.signal = controller.signal
        // Stocker pour pouvoir annuler plus tard
        const requestId = config.url + (config.method || 'get')
        abortControllers.value.set(requestId, controller)
      }

      // Log en développement
      if (import.meta.env.DEV) {
        console.log(`🚀 [API] ${config.method?.toUpperCase()} ${config.url}`, config.data || '')
      }

      return config
    },
    (error) => Promise.reject(error)
  )

  // Intercepteur de réponse : gestion des erreurs globales
  instance.interceptors.response.use(
    (response) => {
      // Nettoyer le contrôleur d'abandon
      const requestId = response.config.url + (response.config.method || 'get')
      abortControllers.value.delete(requestId)

      // Log en développement
      if (import.meta.env.DEV) {
        console.log(`✅ [API] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.status)
      }

      // Appel du callback succès
      if (options.onSuccess) {
        options.onSuccess(response)
      }

      lastResponse.value = response
      return response
    },
    async (error) => {
      // Récupérer la requête originale
      const originalRequest = error.config

      // Log d'erreur
      if (import.meta.env.DEV) {
        console.error(`❌ [API] ${originalRequest?.method?.toUpperCase()} ${originalRequest?.url}`, error.message)
      }

      // Nettoyer le contrôleur d'abandon
      if (originalRequest) {
        const requestId = originalRequest.url + (originalRequest.method || 'get')
        abortControllers.value.delete(requestId)
      }

      // --- Gestion des erreurs spécifiques ---
      // 1. Erreur d'annulation (AbortController)
      if (axios.isCancel(error)) {
        return Promise.reject({ canceled: true, message: 'Requête annulée' })
      }

      // 2. Erreur 401 (Non autorisé) - Tentative de refresh token
      if (error.response?.status === 401 && !originalRequest?._retry) {
        if (originalRequest) {
          originalRequest._retry = true
        }

        try {
          const refreshToken = localStorage.getItem('refresh_token')
          if (!refreshToken) {
            throw new Error('Aucun refresh token')
          }

          // Appel au endpoint de refresh
          const refreshResponse = await axios.post(
            `${baseURL}/auth/refresh`,
            { refresh_token: refreshToken },
            { headers: { 'Content-Type': 'application/json' } }
          )

          if (refreshResponse.data?.access_token) {
            const newToken = refreshResponse.data.access_token
            // Mettre à jour le store et le localStorage
            if (authStore) {
              authStore.setToken(newToken)
            } else {
              localStorage.setItem('auth_token', newToken)
            }
            if (refreshResponse.data.refresh_token) {
              localStorage.setItem('refresh_token', refreshResponse.data.refresh_token)
            }
            // Réessayer la requête originale avec le nouveau token
            if (originalRequest) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
              return instance(originalRequest)
            }
          }
        } catch (refreshError) {
          // Échec du refresh : rediriger vers la page de login
          if (authStore) {
            authStore.logout()
          } else {
            localStorage.removeItem('auth_token')
            localStorage.removeItem('refresh_token')
          }
          // Redirection si possible
          const router = inject('router', null)
          if (router) {
            router.push('/login')
          }
          // Afficher une notification
          if (showToast) {
            showToast('Session expirée, veuillez vous reconnecter.', 'error', '🔐')
          }
          return Promise.reject({ ...error, handled: true })
        }
      }

      // 3. Erreur 429 (Trop de requêtes) - Attendre et réessayer
      if (error.response?.status === 429 && originalRequest && !originalRequest._retry429) {
        originalRequest._retry429 = true
        const retryAfter = error.response.headers['retry-after'] || 2
        const waitTime = parseInt(retryAfter, 10) * 1000 || 2000
        await new Promise((resolve) => setTimeout(resolve, waitTime))
        return instance(originalRequest)
      }

      // 4. Erreurs réseau / timeouts - Retries automatiques
      if (originalRequest && maxRetries > 0 && !originalRequest._retryCount) {
        originalRequest._retryCount = 0
      }
      if (originalRequest && originalRequest._retryCount < maxRetries) {
        originalRequest._retryCount += 1
        const delay = retryDelay * originalRequest._retryCount
        await new Promise((resolve) => setTimeout(resolve, delay))
        return instance(originalRequest)
      }

      // 5. Autres erreurs : afficher une notification
      if (showToast) {
        const message = error.response?.data?.detail || error.message || 'Erreur inconnue'
        showToast(`❌ ${message}`, 'error', '❌')
      }

      // Appel du callback d'erreur
      if (options.onError) {
        options.onError(error)
      }

      // Mettre à jour l'état error
      error.value = error

      return Promise.reject(error)
    }
  )

  // ==========================================================================
  //  Méthodes publiques
  // ==========================================================================

  /**
   * Effectue une requête GET.
   * @param {string} url - URL de la ressource
   * @param {Object} [params] - Paramètres de la requête
   * @param {Object} [config] - Configuration Axios supplémentaire
   * @returns {Promise} - Promesse de la réponse
   */
  async function get(url, params = {}, config = {}) {
    return request('get', url, { params, ...config })
  }

  /**
   * Effectue une requête POST.
   * @param {string} url - URL de la ressource
   * @param {Object} [data] - Corps de la requête
   * @param {Object} [config] - Configuration Axios supplémentaire
   * @returns {Promise} - Promesse de la réponse
   */
  async function post(url, data = {}, config = {}) {
    return request('post', url, { data, ...config })
  }

  /**
   * Effectue une requête PUT.
   * @param {string} url - URL de la ressource
   * @param {Object} [data] - Corps de la requête
   * @param {Object} [config] - Configuration Axios supplémentaire
   * @returns {Promise} - Promesse de la réponse
   */
  async function put(url, data = {}, config = {}) {
    return request('put', url, { data, ...config })
  }

  /**
   * Effectue une requête PATCH.
   * @param {string} url - URL de la ressource
   * @param {Object} [data] - Corps de la requête
   * @param {Object} [config] - Configuration Axios supplémentaire
   * @returns {Promise} - Promesse de la réponse
   */
  async function patch(url, data = {}, config = {}) {
    return request('patch', url, { data, ...config })
  }

  /**
   * Effectue une requête DELETE.
   * @param {string} url - URL de la ressource
   * @param {Object} [config] - Configuration Axios supplémentaire
   * @returns {Promise} - Promesse de la réponse
   */
  async function remove(url, config = {}) {
    return request('delete', url, config)
  }

  /**
   * Méthode générique pour effectuer une requête HTTP.
   * Gère le chargement, les erreurs, les annulations.
   * @param {string} method - Méthode HTTP (get, post, put, patch, delete)
   * @param {string} url - URL de la requête
   * @param {Object} [config] - Configuration Axios
   * @returns {Promise} - Promesse de la réponse
   */
  async function request(method, url, config = {}) {
    // Configurer le signal d'annulation si non fourni
    if (!config.signal) {
      const controller = new AbortController()
      config.signal = controller.signal
      const requestId = url + method
      abortControllers.value.set(requestId, controller)
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await instance.request({
        method,
        url,
        ...config,
      })
      return response.data
    } catch (err) {
      // Les erreurs sont gérées par l'intercepteur, mais on les propage
      error.value = err
      throw err
    } finally {
      isLoading.value = false
      // Nettoyer les controllers associés
      const requestId = url + method
      abortControllers.value.delete(requestId)
    }
  }

  /**
   * Annule une requête en cours.
   * @param {string} [url] - URL de la requête à annuler (si omis, annule toutes)
   * @param {string} [method] - Méthode HTTP (si omis, annule toutes pour cette URL)
   */
  function cancelRequest(url, method = null) {
    if (url && method) {
      const requestId = url + method
      const controller = abortControllers.value.get(requestId)
      if (controller) {
        controller.abort()
        abortControllers.value.delete(requestId)
      }
    } else if (url) {
      // Annuler toutes les requêtes pour cette URL (toutes méthodes)
      for (const [key, controller] of abortControllers.value) {
        if (key.startsWith(url)) {
          controller.abort()
          abortControllers.value.delete(key)
        }
      }
    } else {
      // Annuler toutes les requêtes
      for (const controller of abortControllers.value.values()) {
        controller.abort()
      }
      abortControllers.value.clear()
    }
  }

  /**
   * Télécharge un fichier avec progression.
   * @param {string} url - URL du fichier
   * @param {Object} [params] - Paramètres de la requête
   * @param {Function} [onProgress] - Callback de progression (reçu: nombre d'octets chargés, total)
   * @param {Object} [config] - Configuration Axios supplémentaire
   * @returns {Promise<Blob>} - Promesse du Blob téléchargé
   */
  async function download(url, params = {}, onProgress = null, config = {}) {
    const controller = new AbortController()
    const requestId = url + 'download'
    abortControllers.value.set(requestId, controller)

    isLoading.value = true
    error.value = null

    try {
      const response = await instance.get(url, {
        params,
        responseType: 'blob',
        signal: controller.signal,
        onDownloadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(percent, progressEvent.loaded, progressEvent.total)
          }
        },
        ...config,
      })
      return response.data
    } catch (err) {
      error.value = err
      throw err
    } finally {
      isLoading.value = false
      abortControllers.value.delete(requestId)
    }
  }

  /**
   * Télécharge un fichier avec progression et sauvegarde automatique.
   * @param {string} url - URL du fichier
   * @param {string} filename - Nom du fichier à sauvegarder
   * @param {Object} [params] - Paramètres de la requête
   * @param {Function} [onProgress] - Callback de progression
   * @returns {Promise<void>}
   */
  async function downloadAndSave(url, filename, params = {}, onProgress = null) {
    const blob = await download(url, params, onProgress)
    // Créer un lien de téléchargement
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  }

  /**
   * Upload de fichier multipart/form-data.
   * @param {string} url - URL de destination
   * @param {FormData} formData - Données du formulaire
   * @param {Function} [onProgress] - Callback de progression
   * @param {Object} [config] - Configuration Axios supplémentaire
   * @returns {Promise} - Promesse de la réponse
   */
  async function upload(url, formData, onProgress = null, config = {}) {
    const controller = new AbortController()
    const requestId = url + 'upload'
    abortControllers.value.set(requestId, controller)

    isLoading.value = true
    error.value = null

    try {
      const response = await instance.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        signal: controller.signal,
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(percent, progressEvent.loaded, progressEvent.total)
          }
        },
        ...config,
      })
      return response.data
    } catch (err) {
      error.value = err
      throw err
    } finally {
      isLoading.value = false
      abortControllers.value.delete(requestId)
    }
  }

  // ==========================================================================
  //  Utilitaire pour les requêtes avec debounce
  // ==========================================================================

  /**
   * Crée une version debounced d'une fonction de requête.
   * @param {Function} fn - Fonction de requête (ex: get)
   * @param {number} delay - Délai en millisecondes
   * @returns {Function} - Fonction debounced
   */
  function debounceRequest(fn, delay = 300) {
    let timeout = null
    return function (...args) {
      clearTimeout(timeout)
      return new Promise((resolve, reject) => {
        timeout = setTimeout(async () => {
          try {
            const result = await fn(...args)
            resolve(result)
          } catch (err) {
            reject(err)
          }
        }, delay)
      })
    }
  }

  // ==========================================================================
  //  Retour du composable
  // ==========================================================================

  return {
    // Méthodes HTTP
    get,
    post,
    put,
    patch,
    delete: remove,
    request,

    // Méthodes spécialisées
    download,
    downloadAndSave,
    upload,

    // Utilitaires
    cancelRequest,
    debounceRequest,
    instance,

    // État réactif
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    lastResponse: computed(() => lastResponse.value),

    // Accès direct à l'instance pour des cas avancés
    axios: instance,
  }
}

// ==========================================================================
//  Export par défaut (pour utilisation avec `useApi` nommé)
// ==========================================================================

export default useApi

// ==========================================================================
//  Notes
// ==========================================================================
//  - Ce composable utilise les stores Pinia si disponibles (useAuthStore)
//  - Il s'intègre avec useToast pour les notifications
//  - Gère le refresh token automatiquement sur 401
//  - Supporte l'annulation de requêtes via AbortController
//  - Fournit des méthodes spécialisées pour upload/download avec progression
//  - Compatible avec Vue 3 et la Composition API
