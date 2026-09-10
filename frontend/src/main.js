// ==========================================================================
//  NexusDL 2.0 - Application Entry Point (version complète et corrigée)
//  Fichier : frontend/src/main.js
//  Description : Point d'entrée principal de l'application Vue.js 3.
//                Correction : les styles SCSS sont importés UNE SEULE FOIS
//                ici (pas dans vite.config.js `additionalData`).
//  Version : 2.0.0
// ==========================================================================

// ==========================================================================
//  SECTION 1 - IMPORTS FRAMEWORK
// ==========================================================================

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import dayjs from 'dayjs'

// ==========================================================================
//  SECTION 2 - IMPORTS APPLICATIONS
// ==========================================================================

import App from './App.vue'
import router from './router'

// ==========================================================================
//  SECTION 3 - IMPORTS STYLES GLOBAUX
//  ⚠️ IMPORTANT : Ces imports NE DOIVENT PAS être dupliqués dans
//  vite.config.js (`additionalData`). Sinon, erreur "This file is already
//  being loaded".
// ==========================================================================

import './assets/styles/nexus-theme.scss'
import './assets/styles/global.scss'

// ==========================================================================
//  SECTION 4 - IMPORTS DIRECTIVES PERSONNALISÉES
// ==========================================================================

import { clickOutside } from './directives/click-outside'
import { focus } from './directives/focus'

// ==========================================================================
//  SECTION 5 - CONFIGURATION DAY.JS (LOCALISATION FR)
// ==========================================================================

import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/duration'
import localizedFormat from 'dayjs/plugin/localizedFormat'
import customParseFormat from 'dayjs/plugin/customParseFormat'
import 'dayjs/locale/fr'

dayjs.extend(relativeTime)
dayjs.extend(duration)
dayjs.extend(localizedFormat)
dayjs.extend(customParseFormat)
dayjs.locale('fr')

// ==========================================================================
//  SECTION 6 - VARIABLES D'ENVIRONNEMENT
// ==========================================================================

const APP_VERSION = import.meta.env.VITE_APP_VERSION || '2.0.0'
const API_BASE = import.meta.env.VITE_API_BASE || '/api'
const WS_BASE = import.meta.env.VITE_WS_BASE || null

// ==========================================================================
//  SECTION 7 - CONFIGURATION AXIOS
// ==========================================================================

/**
 * Instance Axios pré-configurée pour communiquer avec l'API NexusDL.
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
    return config
  },
  (error) => Promise.reject(error)
)

// --------------------------------------------------------------------------
//  Intercepteur de réponse : refresh token + gestion 429/5xx
// --------------------------------------------------------------------------

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // --- Gestion du 401 : tentative de refresh token ---
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          throw new Error('Pas de refresh token')
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
        // Nettoyage complet et redirection vers login
        localStorage.removeItem('auth_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user_data')
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

    return Promise.reject(error)
  }
)

// ==========================================================================
//  SECTION 8 - CRÉATION DE L'APPLICATION
// ==========================================================================

const app = createApp(App)
const pinia = createPinia()

// ==========================================================================
//  SECTION 9 - ENREGISTREMENT DES PLUGINS
// ==========================================================================

app.use(pinia)
app.use(router)

// ==========================================================================
//  SECTION 10 - ENREGISTREMENT DES DIRECTIVES GLOBALES
// ==========================================================================

app.directive('click-outside', clickOutside)
app.directive('focus', focus)

// ==========================================================================
//  SECTION 11 - FOURNITURE DES SERVICES GLOBAUX (injectables)
// ==========================================================================

app.provide('apiClient', apiClient)
app.provide('apiBase', API_BASE)
app.provide('appVersion', APP_VERSION)
app.provide('wsBase', WS_BASE)
app.provide('axios', axios)
app.provide('dayjs', dayjs)

// ==========================================================================
//  SECTION 12 - GESTIONNAIRE D'ERREUR GLOBAL (Vue)
// ==========================================================================

app.config.errorHandler = (err, instance, info) => {
  console.error('❌ [Vue Error]', err)
  console.error('ℹ️ [Vue Info]', info)
  // En production, on pourrait envoyer l'erreur à un service de monitoring
}

// Avertissements en développement
app.config.warnHandler = (msg, instance, trace) => {
  if (import.meta.env.DEV) {
    console.warn('⚠️ [Vue Warning]', msg)
  }
}

// ==========================================================================
//  SECTION 13 - GESTION DU THÈME INITIAL
// ==========================================================================

/**
 * Applique le thème sauvegardé ou la préférence système avant le montage,
 * pour éviter un flash de contenu mal thémé (FOUC).
 */
function applyInitialTheme() {
  const savedTheme = localStorage.getItem('nexus-theme')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const isDark = savedTheme ? savedTheme === 'dark' : prefersDark

  document.body.classList.toggle('dark-mode', isDark)
  document.body.classList.toggle('light-mode', !isDark)

  // Mettre à jour la meta `theme-color` pour la barre d'adresse mobile
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) {
    meta.content = isDark ? '#0a0e1a' : '#f4f6fa'
  }
}

applyInitialTheme()

// ==========================================================================
//  SECTION 14 - SYNCHRONISATION DU THÈME ENTRE ONGLETS
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
//  SECTION 15 - GESTION DES ERREURS GLOBALES (window)
// ==========================================================================

window.addEventListener('error', (event) => {
  console.error('❌ [Global Error]', event.message || event)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('❌ [Unhandled Rejection]', event.reason)
})

// ==========================================================================
//  SECTION 16 - MONTAGE DE L'APPLICATION
// ==========================================================================

app.mount('#app')

// ==========================================================================
//  SECTION 17 - MASQUER LE LOADER INITIAL
// ==========================================================================

if (window.__nexusLoader && typeof window.__nexusLoader.hide === 'function') {
  // Masquer le loader après le rendu du premier frame
  requestAnimationFrame(() => {
    setTimeout(() => {
      window.__nexusLoader.hide(true)
    }, 150)
  })
} else {
  // Fallback : masquer directement le loader
  const loader = document.getElementById('nexus-loader')
  if (loader) {
    loader.classList.add('hide')
    setTimeout(() => loader.remove(), 600)
  }
}

// ==========================================================================
//  SECTION 18 - LOGS DE DÉMARRAGE (développement)
// ==========================================================================

if (import.meta.env.DEV) {
  console.log(`%c🧬 NexusDL ${APP_VERSION}`, 'color: #00d4ff; font-weight: bold; font-size: 14px;')
  console.log(`📡 API : ${API_BASE}`)
  console.log(`🔌 WS  : ${WS_BASE || 'défaut'}`)
  console.log(`🌍 Mode : ${import.meta.env.MODE}`)
}

// ==========================================================================
//  SECTION 19 - EXPORT (pour les tests)
// ==========================================================================

export { app, router, pinia, apiClient }
