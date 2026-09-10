// ==========================================================================
//  NexusDL 2.0 - Application Entry Point (version complète et finale)
//  Fichier : frontend/src/main.js
//  Description : Point d'entrée principal de l'application Vue.js 3.
//                Intègre : Pinia, Vue Router, Axios, Day.js, PWA,
//                directives personnalisées, thème, gestion d'erreurs,
//                loader initial, et événements globaux.
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
 * - Ajout automatique du token JWT
 * - Gestion du refresh token sur 401
 * - Gestion du rate limiting sur 429
 */
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json'
  }
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
      console.log(`🚀 [API] ${config.method?.toUpperCase()} ${config.url}`, config.data || '')
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
      console.log(`✅ [API] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.status)
    }
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // --- Gestion du 401 : tentative de refresh token ---
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

        // Rediriger vers login si on n'y est pas déjà
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }

        return Promise.reject(refreshError)
      }
    }

    // --- Gestion du 429 : rate limiting ---
    if (error.response?.status === 429 && originalRequest && !originalRequest._retry429) {
      originalRequest._retry429 = true
      const retryAfter = parseInt(error.response.headers['retry-after'], 10) || 2
      await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000))
      return apiClient(originalRequest)
    }

    // --- Log des erreurs en développement ---
    if (IS_DEV) {
      console.error(
        `❌ [API] ${originalRequest?.method?.toUpperCase()} ${originalRequest?.url}`,
        error.response?.status,
        error.message
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

  // En production, on pourrait envoyer l'erreur à un service de monitoring
  // if (IS_PROD && window.__nexusSentry) {
  //   window.__nexusSentry.captureException(err)
  // }
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
 * Applique le thème sauvegardé ou la préférence système.
 * Cette fonction est également exécutée dans `index.html` en amont,
 * mais on la répète ici par sécurité.
 */
function applyInitialTheme() {
  try {
    const savedTheme = localStorage.getItem('nexus-theme')
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    const isDark = savedTheme ? savedTheme === 'dark' : prefersDark

    document.documentElement.classList.toggle('dark-mode', isDark)
    document.documentElement.classList.toggle('light-mode', !isDark)

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

    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) {
      meta.setAttribute('content', isDark ? '#0a0e1a' : '#f4f6fa')
    }
  }
})

// ==========================================================================
//  SECTION 15 — GESTION DES ERREURS GLOBALES (window)
// ==========================================================================

window.addEventListener('error', (event) => {
  console.error('❌ [Global Error]', event.message || event)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('❌ [Unhandled Rejection]', event.reason)

  // En développement, on log la stack complète
  if (IS_DEV && event.reason?.stack) {
    console.error(event.reason.stack)
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
  })
}

// ==========================================================================
//  SECTION 20 — LOGS DE DÉMARRAGE (DEV uniquement)
// ==========================================================================

if (IS_DEV) {
  console.log(
    `%c🧬 NexusDL ${APP_VERSION}`,
    'color: #00d4ff; font-weight: bold; font-size: 14px;'
  )
  console.log(`📡 API       : ${API_BASE}`)
  console.log(`🔌 WebSocket : ${WS_BASE || 'défaut'}`)
  console.log(`🌍 Mode      : ${MODE}`)
  console.log(`🐞 Debug     : ${IS_DEV ? 'activé' : 'désactivé'}`)
}

// ==========================================================================
//  SECTION 21 — EXPOSITION DE L'APPLICATION (débogage)
// ==========================================================================

if (IS_DEV) {
  window.__nexusApp = app
  window.__nexusRouter = router
  window.__nexusPinia = pinia
  window.__nexusApi = apiClient
  window.__nexusVersion = APP_VERSION
}

// ==========================================================================
//  SECTION 22 — EXPORT (pour les tests)
// ==========================================================================

export { app, router, pinia, apiClient, dayjs }
