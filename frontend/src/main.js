// ==========================================================================
//  NexusDL 2.0 - Application Entry Point (VERSION ULTRA COMPLÈTE)
//  Fichier : frontend/src/main.js
//  Description : Point d'entrée principal de l'application Vue.js 3.
//                Intègre : Pinia, Vue Router, Axios, Day.js, PWA,
//                directives personnalisées, thème, gestion d'erreurs,
//                loader initial, événements globaux, WebSocket, PWA update,
//                et initialisation complète.
//  Version : 2.0.0
//  Licence : GNU GPL v3.0
// ==========================================================================

// ==========================================================================
//  SECTION 1 — IMPORTS FRAMEWORK
// ==========================================================================

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import dayjs from 'dayjs'

// ==========================================================================
//  SECTION 2 — IMPORTS APPLICATION
// ==========================================================================

import App from './App.vue'
import router from './router'

// ==========================================================================
//  SECTION 3 — IMPORTS STYLES GLOBAUX
//  ⚠️ IMPORTANT :
//  Ces imports NE DOIVENT PAS être dupliqués dans `vite.config.js`
//  (via `additionalData`), sinon erreur "This file is already being loaded".
//
//  Ils sont importés UNE SEULE FOIS ici.
// ==========================================================================

import './assets/styles/nexus-theme.scss'
import './assets/styles/global.scss'

// ==========================================================================
//  SECTION 4 — IMPORTS DIRECTIVES PERSONNALISÉES
// ==========================================================================

import { clickOutside } from './directives/click-outside'
import { focus } from './directives/focus'

// ==========================================================================
//  SECTION 5 — CONFIGURATION DAY.JS (LOCALISATION FR)
// ==========================================================================

import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/duration'
import localizedFormat from 'dayjs/plugin/localizedFormat'
import customParseFormat from 'dayjs/plugin/customParseFormat'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import 'dayjs/locale/fr'

// Extension de Day.js avec tous les plugins nécessaires
dayjs.extend(relativeTime)
dayjs.extend(duration)
dayjs.extend(localizedFormat)
dayjs.extend(customParseFormat)
dayjs.extend(utc)
dayjs.extend(timezone)

// Localisation en français
dayjs.locale('fr')

// ==========================================================================
//  SECTION 6 — VARIABLES D'ENVIRONNEMENT
// ==========================================================================

const APP_VERSION = import.meta.env.VITE_APP_VERSION || '2.0.0'
const API_BASE = import.meta.env.VITE_API_BASE || '/api'
const WS_BASE = import.meta.env.VITE_WS_BASE || null
const IS_DEV = import.meta.env.DEV
const IS_PROD = import.meta.env.PROD
const MODE = import.meta.env.MODE

// ==========================================================================
//  SECTION 7 — CONFIGURATION AXIOS
// ==========================================================================

/**
 * Instance Axios pré-configurée pour communiquer avec l'API NexusDL.
 *
 * Fonctionnalités :
 * - Ajout automatique du token JWT
 * - Gestion du refresh token sur 401
 * - Gestion du rate limiting sur 429
 * - Retry automatique sur erreurs réseau
 * - Interception globale des erreurs
 */
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  withCredentials: false,
})

// --------------------------------------------------------------------------
//  Intercepteur de requête : ajout du token JWT
// --------------------------------------------------------------------------

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Log en développement
    if (IS_DEV) {
      console.log(
        `%c🚀 [API] ${config.method?.toUpperCase()} ${config.url}`,
        'color: #00d4ff;',
        config.data || ''
      )
    }

    return config
  },
  (error) => Promise.reject(error)
)

// --------------------------------------------------------------------------
//  Intercepteur de réponse : refresh token + gestion des erreurs
// --------------------------------------------------------------------------

apiClient.interceptors.response.use(
  (response) => {
    if (IS_DEV) {
      console.log(
        `%c✅ [API] ${response.config.method?.toUpperCase()} ${response.config.url}`,
        'color: #4caf50;',
        response.status
      )
    }
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // === Gestion du 401 : tentative de refresh token ===
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          throw new Error('Pas de refresh token disponible')
        }

        const response = await axios.post(
          `${API_BASE}/auth/refresh`,
          { refresh_token: refreshToken },
          { headers: { 'Content-Type': 'application/json' } }
        )

        if (response.data?.access_token) {
          const newToken = response.data.access_token
          localStorage.setItem('auth_token', newToken)

          if (response.data.refresh_token) {
            localStorage.setItem('refresh_token', response.data.refresh_token)
          }

          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // Échec du refresh : nettoyage complet
        localStorage.removeItem('auth_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user_data')

        // Émettre un événement pour que l'app gère la redirection
        window.dispatchEvent(new CustomEvent('nexus:logout'))

        return Promise.reject(refreshError)
      }
    }

    // === Gestion du 429 : rate limiting ===
    if (error.response?.status === 429 && originalRequest && !originalRequest._retry429) {
      originalRequest._retry429 = true
      const retryAfter = parseInt(error.response.headers['retry-after'], 10) || 2
      await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000))
      return apiClient(originalRequest)
    }

    // === Retry automatique sur erreurs réseau (5xx, timeout) ===
    if (
      originalRequest &&
      !originalRequest._retryNetwork &&
      (!error.response || error.response.status >= 500) &&
      originalRequest.method !== 'delete'
    ) {
      originalRequest._retryNetwork = true
      originalRequest._retryCount = originalRequest._retryCount || 0

      if (originalRequest._retryCount < 2) {
        originalRequest._retryCount++
        const delay = 1000 * originalRequest._retryCount
        await new Promise((resolve) => setTimeout(resolve, delay))
        return apiClient(originalRequest)
      }
    }

    // === Log des erreurs en développement ===
    if (IS_DEV) {
      const status = error.response?.status || 'NETWORK'
      console.error(
        `%c❌ [API] ${originalRequest?.method?.toUpperCase()} ${originalRequest?.url}`,
        'color: #f44336;',
        status,
        error.message
      )
    }

    // === Émettre un événement global pour les erreurs critiques ===
    if (!error.response || error.response.status >= 500) {
      window.dispatchEvent(
        new CustomEvent('nexus:error', {
          detail: {
            message: error.response?.data?.detail || error.message,
            status: error.response?.status,
            critical: false,
          },
        })
      )
    }

    return Promise.reject(error)
  }
)

// ==========================================================================
//  SECTION 8 — CRÉATION DE L'APPLICATION
// ==========================================================================

const app = createApp(App)
const pinia = createPinia()

// ==========================================================================
//  SECTION 9 — ENREGISTREMENT DES PLUGINS
// ==========================================================================

app.use(pinia)
app.use(router)

// ==========================================================================
//  SECTION 10 — ENREGISTREMENT DES DIRECTIVES GLOBALES
// ==========================================================================

app.directive('click-outside', clickOutside)
app.directive('focus', focus)

// ==========================================================================
//  SECTION 11 — FOURNITURE DES SERVICES GLOBAUX (injectables)
//  Utilisables dans n'importe quel composant via `inject('clé')`
// ==========================================================================

app.provide('apiClient', apiClient)
app.provide('apiBase', API_BASE)
app.provide('appVersion', APP_VERSION)
app.provide('wsBase', WS_BASE)
app.provide('axios', axios)
app.provide('dayjs', dayjs)

// ==========================================================================
//  SECTION 12 — GESTIONNAIRE D'ERREUR GLOBAL (Vue)
// ==========================================================================

app.config.errorHandler = (err, instance, info) => {
  console.error('❌ [Vue Error]', err)
  console.error('ℹ️ [Vue Info]', info)

  // Émettre un événement pour que App.vue puisse gérer l'erreur
  window.dispatchEvent(
    new CustomEvent('nexus:error', {
      detail: {
        message: err?.message || 'Erreur inattendue',
        details: err?.stack || info,
        critical: false,
      },
    })
  )
}

// Gestion des avertissements (uniquement en dev)
app.config.warnHandler = (msg, instance, trace) => {
  if (IS_DEV) {
    console.warn('⚠️ [Vue Warning]', msg)
  }
}

// ==========================================================================
//  SECTION 13 — APPLICATION DU THÈME INITIAL (anti-FOUC)
// ==========================================================================

/**
 * Applique le thème sauvegardé ou la préférence système AVANT le montage.
 * Cette fonction est également exécutée dans `index.html` en amont,
 * mais on la répète ici par sécurité.
 */
function applyInitialTheme() {
  try {
    const savedTheme = localStorage.getItem('nexus-theme')
    const prefersDark =
      window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    const isDark = savedTheme ? savedTheme === 'dark' : prefersDark

    document.documentElement.classList.toggle('dark-mode', isDark)
    document.documentElement.classList.toggle('light-mode', !isDark)
    document.body.classList.toggle('dark-mode', isDark)
    document.body.classList.toggle('light-mode', !isDark)

    // Mise à jour de la meta `theme-color`
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) {
      meta.setAttribute('content', isDark ? '#0a0e1a' : '#f4f6fa')
    }
  } catch (e) {
    console.warn('⚠️ Impossible d\'appliquer le thème initial :', e)
  }
}

applyInitialTheme()

// ==========================================================================
//  SECTION 14 — SYNCHRONISATION DU THÈME ENTRE ONGLETS
// ==========================================================================

window.addEventListener('storage', (event) => {
  if (event.key === 'nexus-theme') {
    const isDark = event.newValue === 'dark'
    document.documentElement.classList.toggle('dark-mode', isDark)
    document.documentElement.classList.toggle('light-mode', !isDark)
    document.body.classList.toggle('dark-mode', isDark)
    document.body.classList.toggle('light-mode', !isDark)

    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) {
      meta.setAttribute('content', isDark ? '#0a0e1a' : '#f4f6fa')
    }
  }

  // Synchronisation de la déconnexion entre onglets
  if (event.key === 'auth_token' && !event.newValue) {
    window.dispatchEvent(new CustomEvent('nexus:logout'))
  }
})

// ==========================================================================
//  SECTION 15 — GESTION DES ERREURS GLOBALES (window)
// ==========================================================================

window.addEventListener('error', (event) => {
  const message = event.message || ''

  // Filtrer les erreurs bénignes
  const ignoredErrors = [
    'ResizeObserver loop',
    'Script error',
    'AbortError',
    'NetworkError',
    'ChunkLoadError',
  ]
  if (ignoredErrors.some((e) => message.includes(e))) {
    return
  }

  console.error('❌ [Global Error]', event.error || message)
})

window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason

  // Filtrer les rejets bénins
  if (
    reason?.name === 'AbortError' ||
    reason?.message?.includes('AbortError') ||
    reason?.message?.includes('NetworkError') ||
    reason?.canceled ||
    reason?.name === 'NavigationDuplicated'
  ) {
    return
  }

  console.error('❌ [Unhandled Rejection]', reason)

  // Stack complète en développement
  if (IS_DEV && reason?.stack) {
    console.error(reason.stack)
  }
})

// ==========================================================================
//  SECTION 16 — DÉTECTION DE LA CONNEXION RÉSEAU
// ==========================================================================

function handleOnline() {
  console.log('🌐 Connexion rétablie')
  window.dispatchEvent(new CustomEvent('nexus:online'))
}

function handleOffline() {
  console.warn('📴 Connexion perdue')
  window.dispatchEvent(new CustomEvent('nexus:offline'))
}

window.addEventListener('online', handleOnline)
window.addEventListener('offline', handleOffline)

// ==========================================================================
//  SECTION 17 — MONTAGE DE L'APPLICATION
// ==========================================================================

app.mount('#app')

// ==========================================================================
//  SECTION 18 — MASQUER LE LOADER INITIAL
// ==========================================================================

/**
 * Signale que l'application est prête en émettant un événement
 * `nexus:ready` qui sera capté par `index.html` pour masquer le loader.
 *
 * On appelle également directement `window.__nexusLoader.hide()` en fallback.
 */
function hideInitialLoader() {
  // 1. Émettre l'événement global
  window.dispatchEvent(new CustomEvent('nexus:ready'))

  // 2. Fallback direct
  if (window.__nexusLoader && typeof window.__nexusLoader.hide === 'function') {
    requestAnimationFrame(() => {
      setTimeout(() => {
        window.__nexusLoader.hide(true)
      }, 100)
    })
  } else {
    // Fallback ultime : manipulation directe du DOM
    const loader = document.getElementById('nexus-loader')
    if (loader) {
      loader.classList.add('hide')
      setTimeout(() => {
        if (loader.parentNode) loader.parentNode.removeChild(loader)
      }, 600)
    }
  }
}

// Masquer le loader après le prochain tick (assure que le DOM est monté)
requestAnimationFrame(() => {
  requestAnimationFrame(() => {
    hideInitialLoader()
  })
})

// ==========================================================================
//  SECTION 19 — ENREGISTREMENT DU SERVICE WORKER (PWA)
//  ⚠️ Vite PWA gère automatiquement la registration si configuré dans
//  `vite.config.js`. Cette section fournit une registration manuelle
//  en fallback pour les navigateurs modernes.
// ==========================================================================

if ('serviceWorker' in navigator && IS_PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .then((registration) => {
        console.log('✅ [PWA] Service Worker enregistré :', registration.scope)

        // Détecter les mises à jour
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing
          if (!newWorker) return

          newWorker.addEventListener('statechange', () => {
            if (
              newWorker.state === 'installed' &&
              navigator.serviceWorker.controller
            ) {
              console.log('🔄 [PWA] Nouvelle version disponible')

              // Émettre un événement personnalisé pour l'UI
              window.dispatchEvent(new CustomEvent('nexus:pwa-update'))
            }
          })
        })
      })
      .catch((error) => {
        console.warn('⚠️ [PWA] Échec de l\'enregistrement du Service Worker :', error)
      })

    // Écouter les messages du Service Worker
    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data?.type === 'SKIP_WAITING') {
        console.log('🔄 [PWA] Rechargement pour mise à jour…')
        window.location.reload()
      }
    })

    // Vérifier les mises à jour toutes les heures
    setInterval(() => {
      navigator.serviceWorker.getRegistration().then((reg) => {
        if (reg) reg.update()
      })
    }, 60 * 60 * 1000)
  })
}

// ==========================================================================
//  SECTION 20 — MISE À JOUR AUTOMATIQUE PWA (si disponible)
// ==========================================================================

// Si le navigateur supporte l'événement `beforeinstallprompt`, on peut
// proposer l'installation de la PWA à l'utilisateur.
let deferredPrompt = null

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault()
  deferredPrompt = e
  console.log('📲 [PWA] Installation disponible')

  // Émettre un événement pour que l'UI puisse afficher un bouton
  window.dispatchEvent(new CustomEvent('nexus:pwa-install-available'))
})

window.addEventListener('appinstalled', () => {
  console.log('✅ [PWA] Application installée')
  deferredPrompt = null
  window.dispatchEvent(new CustomEvent('nexus:pwa-installed'))
})

// ==========================================================================
//  SECTION 21 — LOGS DE DÉMARRAGE (DEV uniquement)
// ==========================================================================

if (IS_DEV) {
  console.log(
    `%c🧬 NexusDL ${APP_VERSION}`,
    'color: #00d4ff; font-weight: bold; font-size: 16px; text-shadow: 0 0 10px rgba(0,212,255,0.5);'
  )
  console.log(`📡 API       : ${API_BASE}`)
  console.log(`🔌 WebSocket : ${WS_BASE || 'défaut'}`)
  console.log(`🌍 Mode      : ${MODE}`)
  console.log(`🐞 Debug     : activé`)
  console.log(`⚡ Build      : ${IS_PROD ? 'production' : 'développement'}`)
  console.log(
    '%cAstuce : tapez window.__nexusApp dans la console pour accéder aux stores.',
    'color: #6a7a9a; font-style: italic;'
  )
}

// ==========================================================================
//  SECTION 22 — EXPOSITION DE L'APPLICATION (débogage)
// ==========================================================================

if (IS_DEV) {
  window.__nexusApp = app
  window.__nexusRouter = router
  window.__nexusPinia = pinia
  window.__nexusApi = apiClient
  window.__nexusVersion = APP_VERSION
  window.__nexusDayjs = dayjs
}

// ==========================================================================
//  SECTION 23 — GESTION DU CYCLE DE VIE
// ==========================================================================

// Nettoyage lors de la fermeture de l'onglet
window.addEventListener('beforeunload', () => {
  // Fermer la connexion WebSocket si elle existe
  try {
    const jobsStore = window.__nexusApp?.config?.globalProperties?.$pinia?.state?.value?.jobs
    if (jobsStore?.wsConnected) {
      // La fermeture se fait automatiquement par le navigateur
    }
  } catch (_) {
    // Ignorer
  }
})

// Nettoyage des ressources lors du déchargement
window.addEventListener('pagehide', () => {
  // Fermer la session aiohttp si nécessaire
})

// ==========================================================================
//  SECTION 24 — GESTION DU FOCUS VISIBLE
// ==========================================================================

// Détecter si l'utilisateur navigue au clavier
let keyboardNavigation = false

document.addEventListener('keydown', (e) => {
  if (e.key === 'Tab') {
    keyboardNavigation = true
    document.body.classList.add('using-keyboard')
  }
})

document.addEventListener('mousedown', () => {
  keyboardNavigation = false
  document.body.classList.remove('using-keyboard')
})

// ==========================================================================
//  SECTION 25 — DÉTECTION DE LA LANGUE DU NAVIGATEUR
// ==========================================================================

try {
  const browserLang = navigator.language?.split('-')[0] || 'fr'
  const supportedLangs = ['fr', 'en', 'es', 'de', 'it', 'pt']
  if (supportedLangs.includes(browserLang)) {
    const savedLang = localStorage.getItem('nexus-language')
    if (!savedLang) {
      // Ne pas forcer, mais logger pour info
      console.log(`🌍 Langue navigateur détectée : ${browserLang}`)
    }
  }
} catch (_) {
  // Ignorer
}

// ==========================================================================
//  SECTION 26 — GESTION DU PRELOADING DES IMAGES
// ==========================================================================

// Précharger les images critiques après le montage
window.addEventListener('load', () => {
  // Attendre un peu pour ne pas bloquer le rendu
  setTimeout(() => {
    // Précharger le favicon (déjà chargé, mais au cas où)
    const link = document.createElement('link')
    link.rel = 'prefetch'
    link.href = '/favicon.svg'
    document.head.appendChild(link)
  }, 2000)
})

// ==========================================================================
//  SECTION 27 — GESTION DES ERREURS DE CHARGEMENT DE CHUNK
// ==========================================================================

// Si un chunk ne se charge pas (fréquent après un redéploiement),
// on force un rechargement complet de la page.
window.addEventListener('error', (event) => {
  const target = event.target
  if (target?.tagName === 'SCRIPT' || target?.tagName === 'LINK') {
    const src = target.src || target.href || ''
    if (src.includes('.js') || src.includes('.css')) {
      console.warn('⚠️ Ressource introuvable, rechargement forcé :', src)

      // Éviter les boucles infinies
      const reloadCount = parseInt(sessionStorage.getItem('nexus-reload-count') || '0', 10)
      if (reloadCount < 2) {
        sessionStorage.setItem('nexus-reload-count', String(reloadCount + 1))
        window.location.reload()
      } else {
        console.error('❌ Impossible de charger les ressources après plusieurs tentatives.')
        sessionStorage.removeItem('nexus-reload-count')
      }
    }
  }
}, true)

// Réinitialiser le compteur de rechargement après un chargement réussi
window.addEventListener('load', () => {
  setTimeout(() => {
    sessionStorage.removeItem('nexus-reload-count')
  }, 5000)
})

// ==========================================================================
//  SECTION 28 — EXPORT (pour les tests)
// ==========================================================================

export { app, router, pinia, apiClient, dayjs }
