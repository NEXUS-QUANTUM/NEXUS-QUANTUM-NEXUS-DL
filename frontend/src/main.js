// ==========================================================================
//  NexusDL 2.0 - Application Entry Point
//  Fichier : frontend/src/main.js
//  Description : Point d'entrée principal de l'application Vue.js 3
//  Version : 2.0.0
// ==========================================================================

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/duration'
import localizedFormat from 'dayjs/plugin/localizedFormat'
import 'dayjs/locale/fr'

// ==========================================================================
//  Composants et configuration
// ==========================================================================

import App from './App.vue'
import router from './router'

// ==========================================================================
//  Styles globaux
// ==========================================================================

import './assets/styles/global.scss'
import './assets/styles/nexus-theme.scss'

// ==========================================================================
//  Directives personnalisées
// ==========================================================================

import { clickOutside } from './directives/click-outside'
import { focus } from './directives/focus'

// ==========================================================================
//  Configuration Day.js
// ==========================================================================

dayjs.extend(relativeTime)
dayjs.extend(duration)
dayjs.extend(localizedFormat)
dayjs.locale('fr')

// ==========================================================================
//  Variables d'environnement
// ==========================================================================

const APP_VERSION = import.meta.env.VITE_APP_VERSION || '2.0.0'
const API_BASE = import.meta.env.VITE_API_BASE || '/api'
const WS_BASE = import.meta.env.VITE_WS_BASE || null

// ==========================================================================
//  Configuration Axios
// ==========================================================================

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// --- Intercepteur de requête : ajout du token JWT ---
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// --- Intercepteur de réponse : gestion des erreurs et refresh token ---
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Si erreur 401 et qu'on n'a pas déjà tenté un refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          // Pas de refresh token, rediriger vers login
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          return Promise.reject(error)
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
          // Mettre à jour le header et réessayer
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // Échec du refresh, déconnecter l'utilisateur
        localStorage.removeItem('auth_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user_data')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }

    // Gestion des erreurs 429 (rate limiting)
    if (error.response?.status === 429 && !originalRequest._retry429) {
      originalRequest._retry429 = true
      const retryAfter = parseInt(error.response.headers['retry-after'], 10) || 2
      await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000))
      return apiClient(originalRequest)
    }

    return Promise.reject(error)
  }
)

// ==========================================================================
//  Création de l'application
// ==========================================================================

const app = createApp(App)
const pinia = createPinia()

// ==========================================================================
//  Utilisation des plugins
// ==========================================================================

app.use(pinia)
app.use(router)

// ==========================================================================
//  Enregistrement des directives globales
// ==========================================================================

app.directive('click-outside', clickOutside)
app.directive('focus', focus)

// ==========================================================================
//  Fourniture des services globaux (injectables)
// ==========================================================================

app.provide('apiClient', apiClient)
app.provide('apiBase', API_BASE)
app.provide('appVersion', APP_VERSION)
app.provide('wsBase', WS_BASE)

// ==========================================================================
//  Gestionnaire d'erreur global (Vue)
// ==========================================================================

app.config.errorHandler = (err, vm, info) => {
  console.error('❌ Erreur Vue:', err)
  console.error('ℹ️ Info:', info)
  // Afficher une notification toast si disponible
  try {
    const toast = app.config.globalProperties.$toast
    if (toast && toast.error) {
      toast.error(`Erreur : ${err.message || 'Erreur inattendue'}`, '❌')
    }
  } catch (_) {}
}

// ==========================================================================
//  Performance monitoring (optionnel)
// ==========================================================================

if (import.meta.env.DEV) {
  // Log des performances en développement
  window.addEventListener('load', () => {
    const perfData = performance.timing
    const loadTime = perfData.loadEventEnd - perfData.navigationStart
    console.log(`⏱️ Temps de chargement : ${loadTime}ms`)
  })
}

// ==========================================================================
//  Application du thème (chargement initial)
// ==========================================================================

function applyInitialTheme() {
  const savedTheme = localStorage.getItem('nexus-theme')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const isDark = savedTheme ? savedTheme === 'dark' : prefersDark

  document.body.classList.toggle('dark-mode', isDark)
  document.body.classList.toggle('light-mode', !isDark)

  // Mettre à jour la meta tag theme-color
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) {
    meta.content = isDark ? '#0a0e1a' : '#f4f6fa'
  }
}

applyInitialTheme()

// ==========================================================================
//  Écouter les changements de thème entre onglets
// ==========================================================================

window.addEventListener('storage', (event) => {
  if (event.key === 'nexus-theme') {
    const isDark = event.newValue === 'dark'
    document.body.classList.toggle('dark-mode', isDark)
    document.body.classList.toggle('light-mode', !isDark)
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) {
      meta.content = isDark ? '#0a0e1a' : '#f4f6fa'
    }
  }
})

// ==========================================================================
//  Montage de l'application
// ==========================================================================

app.mount('#app')

// ==========================================================================
//  Log de démarrage
// ==========================================================================

console.log(`🧬 NexusDL ${APP_VERSION} — Mode: ${import.meta.env.MODE}`)
console.log(`📡 API: ${API_BASE}`)
console.log(`🔌 WebSocket: ${WS_BASE || 'défaut'}`)

// ==========================================================================
//  Export pour tests (optionnel)
// ==========================================================================

export { app, router, pinia, apiClient }
