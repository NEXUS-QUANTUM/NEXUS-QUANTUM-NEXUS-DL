<!-- ==========================================================================
  NexusDL 2.0 - App.vue (VERSION ULTRA COMPLÈTE)
  Fichier : frontend/src/App.vue
  Description : Composant racine ULTRA-COMPLET de NexusDL. Gère :
                - Layout dynamique (app, auth, reader, admin)
                - Header avec tous les handlers
                - Router-view avec transitions
                - Footer avec toutes les infos
                - Toasts globaux avec file d'attente
                - Overlay de chargement global
                - Mode maintenance
                - Error boundary critique
                - Bannière PWA
                - Bannière réseau (online/offline)
                - Raccourcis clavier complets
                - Initialisation des stores
                - WebSocket temps réel
                - Gestion du thème avancée
                - Détection d'inactivité
                - Notifications système
                - Gestion du focus
                - Analytics événements
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div
    id="app"
    class="app"
    :class="appClasses"
    :data-theme="themeClass"
    :data-layout="layoutType"
    :data-route="routeName"
  >
    <!-- ====================================================================
      SECTION 1 — OVERLAY DE CHARGEMENT GLOBAL
    ==================================================================== -->
    <Transition name="app-fade">
      <div
        v-if="globalLoading"
        class="app__global-loading"
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <div class="app__global-loading-content">
          <NexusSpinner size="xl" variant="gradient" />
          <p class="app__global-loading-text">
            {{ globalLoadingMessage || 'Chargement...' }}
          </p>
          <p v-if="globalLoadingSubtext" class="app__global-loading-subtext">
            {{ globalLoadingSubtext }}
          </p>
        </div>
      </div>
    </Transition>

    <!-- ====================================================================
      SECTION 2 — BANNIÈRE HORS LIGNE
    ==================================================================== -->
    <Transition name="app-slide-down">
      <div
        v-if="!isOnline"
        class="app__offline-banner"
        role="alert"
        aria-live="assertive"
      >
        <span class="app__offline-icon" aria-hidden="true">📴</span>
        <span class="app__offline-text">
          Vous êtes hors ligne. Certaines fonctionnalités peuvent être limitées.
        </span>
        <button
          type="button"
          class="app__offline-retry"
          @click="checkConnectivity"
          aria-label="Vérifier la connexion"
        >
          🔄 Réessayer
        </button>
      </div>
    </Transition>

    <!-- ====================================================================
      SECTION 3 — BANNIÈRE DE MAINTENANCE
    ==================================================================== -->
    <Transition name="app-slide-down">
      <div
        v-if="isMaintenanceMode && !isMaintenanceFullScreen"
        class="app__maintenance-banner"
        role="alert"
        aria-live="polite"
      >
        <span class="app__maintenance-banner-icon" aria-hidden="true">🔧</span>
        <span class="app__maintenance-banner-text">
          {{ maintenanceMessage || 'Maintenance en cours. Certaines fonctionnalités peuvent être indisponibles.' }}
        </span>
      </div>
    </Transition>

    <!-- ====================================================================
      SECTION 4 — ÉCRAN DE MAINTENANCE COMPLET
    ==================================================================== -->
    <div
      v-if="isMaintenanceFullScreen"
      class="app__maintenance-fullscreen"
      role="alert"
      aria-live="assertive"
    >
      <div class="app__maintenance-fullscreen-content">
        <div class="app__maintenance-fullscreen-icon-wrapper">
          <span class="app__maintenance-fullscreen-icon" aria-hidden="true">🔧</span>
          <div class="app__maintenance-fullscreen-ring" />
        </div>
        <h1 class="app__maintenance-fullscreen-title">
          Maintenance en cours
        </h1>
        <p class="app__maintenance-fullscreen-message">
          {{ maintenanceMessage || 'L\'application est temporairement indisponible.' }}
        </p>
        <p class="app__maintenance-fullscreen-sub">
          Nous revenons très bientôt. Merci de votre patience.
        </p>
        <div class="app__maintenance-fullscreen-actions">
          <button
            type="button"
            class="app__maintenance-fullscreen-btn"
            @click="reloadApp"
          >
            🔄 Rafraîchir
          </button>
          <a
            href="https://github.com/nexus-dl/nexus-dl"
            target="_blank"
            rel="noopener noreferrer"
            class="app__maintenance-fullscreen-link"
          >
            📖 Voir sur GitHub
          </a>
        </div>
      </div>
    </div>

    <!-- ====================================================================
      SECTION 5 — LAYOUT PRINCIPAL
    ==================================================================== -->
    <template v-else>
      <!-- ================================================================
        HEADER
      ================================================================ -->
      <Transition name="app-slide-down">
        <NexusHeader
          v-if="showHeader"
          ref="headerRef"
          :current-tab="currentTab"
          :providers-count="providersCount"
          :active-jobs-count="activeJobsCount"
          :library-count="libraryItemsCount"
          :storage-used="storageUsed"
          :user="user"
          :is-authenticated="isAuthenticated"
          :is-admin="isAdmin"
          :is-fullscreen="isFullscreen"
          @change-tab="handleTabChange"
          @toggle-theme="handleThemeToggle"
          @search="handleGlobalSearch"
          @refresh="handleGlobalRefresh"
          @login="goToLogin"
          @register="goToRegister"
          @logout="handleLogout"
          @profile="goToProfile"
          @settings="goToSettings"
          @admin="goToAdmin"
        />
      </Transition>

      <!-- ================================================================
        CONTENU PRINCIPAL (router-view)
      ================================================================ -->
      <main
        ref="mainRef"
        class="app__main"
        :class="mainClasses"
        role="main"
      >
        <router-view v-slot="{ Component, route: currentRoute }">
          <Transition
            :name="currentRoute.meta?.transition || 'app-fade'"
            mode="out-in"
            appear
          >
            <component
              :is="Component"
              :key="currentRoute.fullPath"
              class="app__route-component"
            />
          </Transition>
        </router-view>
      </main>

      <!-- ================================================================
        FOOTER
      ================================================================ -->
      <Transition name="app-fade">
        <footer
          v-if="showFooter"
          class="app__footer"
          role="contentinfo"
        >
          <div class="app__footer-container">
            <div class="app__footer-left">
              <p class="app__footer-text">
                <span class="app__footer-brand">
                  🧬 NexusDL {{ appVersion }}
                </span>
                <span class="app__footer-sep" aria-hidden="true">•</span>
                <span class="app__footer-license">GNU GPL v3.0</span>
              </p>
              <p v-if="buildDate" class="app__footer-build">
                Build : {{ buildDate }}
              </p>
            </div>

            <div class="app__footer-center">
              <p class="app__footer-tech">
                Propulsé par
                <a
                  href="https://fastapi.tiangolo.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  FastAPI
                </a>
                <span aria-hidden="true"> • </span>
                <a
                  href="https://vuejs.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Vue.js
                </a>
                <span aria-hidden="true"> • </span>
                <a
                  href="https://playwright.dev/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Playwright
                </a>
              </p>
            </div>

            <div class="app__footer-right">
              <div class="app__footer-status">
                <span
                  class="app__footer-status-dot"
                  :class="{
                    'app__footer-status-dot--online': isOnline && wsConnected,
                    'app__footer-status-dot--offline': !isOnline,
                    'app__footer-status-dot--degraded': isOnline && !wsConnected,
                  }"
                  aria-hidden="true"
                />
                <span class="app__footer-status-text">
                  {{ connectionStatusLabel }}
                </span>
              </div>
              <span v-if="lastRefreshTime" class="app__footer-refresh">
                Actualisé : {{ lastRefreshTime }}
              </span>
            </div>
          </div>
        </footer>
      </Transition>
    </template>

    <!-- ====================================================================
      SECTION 6 — TOASTS GLOBAUX (File d'attente)
    ==================================================================== -->
    <Teleport to="body">
      <div
        class="app__toast-container"
        role="region"
        aria-label="Notifications"
        aria-live="polite"
      >
        <TransitionGroup name="app-toast-list" tag="div">
          <div
            v-for="toastItem in activeToasts"
            :key="toastItem.id"
            class="app-toast"
            :class="`app-toast--${toastItem.type}`"
            role="alert"
            :aria-live="toastItem.type === 'error' ? 'assertive' : 'polite'"
          >
            <!-- Icône -->
            <span class="app-toast__icon" aria-hidden="true">
              {{ toastItem.icon }}
            </span>

            <!-- Contenu -->
            <div class="app-toast__content">
              <span class="app-toast__message">{{ toastItem.message }}</span>
              <span v-if="toastItem.details" class="app-toast__details">
                {{ toastItem.details }}
              </span>
            </div>

            <!-- Action -->
            <button
              v-if="toastItem.action"
              type="button"
              class="app-toast__action"
              @click="handleToastAction(toastItem)"
            >
              {{ toastItem.action }}
            </button>

            <!-- Fermeture -->
            <button
              v-if="toastItem.closable"
              type="button"
              class="app-toast__close"
              @click="removeToast(toastItem.id)"
              aria-label="Fermer la notification"
            >
              <span aria-hidden="true">&times;</span>
            </button>

            <!-- Barre de progression -->
            <div
              v-if="toastItem.duration > 0"
              class="app-toast__progress"
              :style="{ animationDuration: `${toastItem.duration}ms` }"
            />
          </div>
        </TransitionGroup>
      </div>
    </Teleport>

    <!-- ====================================================================
      SECTION 7 — ERREUR CRITIQUE (Error Boundary)
    ==================================================================== -->
    <Teleport to="body">
      <Transition name="app-fade">
        <div
          v-if="criticalError"
          class="app__critical-error"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="critical-error-title"
          aria-describedby="critical-error-message"
        >
          <div class="app__critical-error-content">
            <span class="app__critical-error-icon" aria-hidden="true">💥</span>

            <h2 id="critical-error-title" class="app__critical-error-title">
              Une erreur critique est survenue
            </h2>

            <p id="critical-error-message" class="app__critical-error-message">
              {{ criticalError }}
            </p>

            <details v-if="criticalErrorDetails" class="app__critical-error-details">
              <summary>Détails techniques</summary>
              <pre>{{ criticalErrorDetails }}</pre>
            </details>

            <div class="app__critical-error-actions">
              <button
                type="button"
                class="app__critical-error-btn app__critical-error-btn--primary"
                @click="reloadApp"
              >
                🔄 Recharger l'application
              </button>
              <button
                type="button"
                class="app__critical-error-btn app__critical-error-btn--neutral"
                @click="dismissCriticalError"
              >
                ✖ Continuer quand même
              </button>
              <button
                type="button"
                class="app__critical-error-btn app__critical-error-btn--link"
                @click="copyErrorReport"
              >
                📋 Copier le rapport
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ====================================================================
      SECTION 8 — BANNIÈRE PWA UPDATE
    ==================================================================== -->
    <Teleport to="body">
      <Transition name="app-slide-up">
        <div
          v-if="pwaUpdateAvailable"
          class="app__pwa-update"
          role="alert"
          aria-live="polite"
        >
          <span class="app__pwa-update-icon" aria-hidden="true">🎉</span>
          <div class="app__pwa-update-content">
            <span class="app__pwa-update-title">Nouvelle version disponible</span>
            <span class="app__pwa-update-subtitle">
              Mettez à jour pour bénéficier des dernières améliorations
            </span>
          </div>
          <div class="app__pwa-update-actions">
            <button
              type="button"
              class="app__pwa-update-btn app__pwa-update-btn--primary"
              @click="applyPwaUpdate"
            >
              🔄 Mettre à jour
            </button>
            <button
              type="button"
              class="app__pwa-update-btn app__pwa-update-btn--neutral"
              @click="dismissPwaUpdate"
              aria-label="Ignorer cette mise à jour"
            >
              Plus tard
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ====================================================================
      SECTION 9 — BOUTON RETOUR EN HAUT
    ==================================================================== -->
    <Teleport to="body">
      <Transition name="app-fade">
        <button
          v-if="showScrollTop"
          type="button"
          class="app__scroll-top"
          @click="scrollToTop"
          aria-label="Retourner en haut de la page"
          title="Retour en haut"
        >
          <span aria-hidden="true">↑</span>
        </button>
      </Transition>
    </Teleport>

    <!-- ====================================================================
      SECTION 10 — INDICATEUR DE CHARGEMENT DE ROUTE
    ==================================================================== -->
    <Teleport to="body">
      <Transition name="app-fade">
        <div
          v-if="routeLoading"
          class="app__route-loading"
          role="progressbar"
          aria-label="Chargement de la page"
        >
          <div class="app__route-loading-bar" />
        </div>
      </Transition>
    </Teleport>

    <!-- ====================================================================
      SECTION 11 — DIALOG DE CONFIRMATION GLOBAL
    ==================================================================== -->
    <Teleport to="body">
      <Transition name="app-fade">
        <div
          v-if="globalConfirm.show"
          class="app__global-confirm"
          role="alertdialog"
          aria-modal="true"
          @click.self="cancelGlobalConfirm"
        >
          <div class="app__global-confirm-content">
            <span class="app__global-confirm-icon" aria-hidden="true">
              {{ globalConfirm.icon || '❓' }}
            </span>
            <h3 class="app__global-confirm-title">
              {{ globalConfirm.title }}
            </h3>
            <p class="app__global-confirm-message">
              {{ globalConfirm.message }}
            </p>
            <div class="app__global-confirm-actions">
              <button
                type="button"
                class="app__global-confirm-btn app__global-confirm-btn--neutral"
                @click="cancelGlobalConfirm"
              >
                {{ globalConfirm.cancelText || 'Annuler' }}
              </button>
              <button
                type="button"
                class="app__global-confirm-btn app__global-confirm-btn--primary"
                :class="`app__global-confirm-btn--${globalConfirm.variant || 'primary'}`"
                @click="acceptGlobalConfirm"
              >
                {{ globalConfirm.confirmText || 'Confirmer' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
// ==========================================================================
//  IMPORTS
// ==========================================================================

import {
  ref,
  reactive,
  computed,
  onMounted,
  onUnmounted,
  provide,
  watch,
  nextTick,
  defineAsyncComponent,
} from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import { useLibraryStore } from '@/stores/library'
import { useProvidersStore } from '@/stores/providers'
import { useNotificationsStore } from '@/stores/notifications'
import { useTheme } from '@/composables/useTheme'
import { useToast } from '@/composables/useToast'
import { useApi } from '@/composables/useApi'
import NexusHeader from '@/components/NexusHeader.vue'
import NexusSpinner from '@/components/common/NexusSpinner.vue'

// ==========================================================================
//  COMPOSABLES & STORES
// ==========================================================================

const router = useRouter()
const route = useRoute()

const appStore = useAppStore()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const libraryStore = useLibraryStore()
const providersStore = useProvidersStore()
const notifStore = useNotificationsStore()

const { currentTheme, isDark, isLight, setTheme, toggleTheme } = useTheme()
const toast = useToast()
const api = useApi()

// ==========================================================================
//  ÉTAT RÉACTIF — Références DOM
// ==========================================================================

const headerRef = ref(null)
const mainRef = ref(null)

// ==========================================================================
//  ÉTAT RÉACTIF — Application
// ==========================================================================

const isAppInitialized = ref(false)
const isInitializing = ref(false)
const initError = ref(null)

// ==========================================================================
//  ÉTAT RÉACTIF — Erreurs
// ==========================================================================

const criticalError = ref(null)
const criticalErrorDetails = ref('')

// ==========================================================================
//  ÉTAT RÉACTIF — PWA
// ==========================================================================

const pwaUpdateAvailable = ref(false)
const pwaUpdateDismissed = ref(false)

// ==========================================================================
//  ÉTAT RÉACTIF — Réseau
// ==========================================================================

const isOnline = ref(navigator.onLine)
const wsConnected = computed(() => jobsStore.wsConnected || false)

// ==========================================================================
//  ÉTAT RÉACTIF — Loading global
// ==========================================================================

const globalLoading = ref(false)
const globalLoadingMessage = ref('')
const globalLoadingSubtext = ref('')
let globalLoadingTimeout = null

// ==========================================================================
//  ÉTAT RÉACTIF — Route loading
// ==========================================================================

const routeLoading = ref(false)
let routeLoadingTimeout = null

// ==========================================================================
//  ÉTAT RÉACTIF — Scroll to top
// ==========================================================================

const showScrollTop = ref(false)
const scrollThreshold = 300

// ==========================================================================
//  ÉTAT RÉACTIF — Fullscreen
// ==========================================================================

const isFullscreen = ref(false)

// ==========================================================================
//  ÉTAT RÉACTIF — Toasts
// ==========================================================================

const toasts = ref([])
const toastsTimers = new Map()
let toastIdCounter = 0

// ==========================================================================
//  ÉTAT RÉACTIF — Confirm global
// ==========================================================================

const globalConfirm = reactive({
  show: false,
  title: '',
  message: '',
  icon: '❓',
  confirmText: 'Confirmer',
  cancelText: 'Annuler',
  variant: 'primary',
  resolve: null,
  reject: null,
})

// ==========================================================================
//  ÉTAT RÉACTIF — Statistiques footer
// ==========================================================================

const lastRefreshTime = ref('')
const lastUpdated = ref(new Date())

// ==========================================================================
//  ÉTAT RÉACTIF — Session
// ==========================================================================

const inactivityTimeout = ref(null)
const lastActivityTime = ref(Date.now())
const INACTIVITY_LIMIT = 30 * 60 * 1000 // 30 minutes

// ==========================================================================
//  MÉTADONNÉES
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')

const buildDate = computed(() => {
  const date = import.meta.env.VITE_BUILD_DATE
  if (!date) return ''
  try {
    const d = new Date(date)
    return d.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  } catch (_) {
    return ''
  }
})

// ==========================================================================
//  COMPUTED — Layout
// ==========================================================================

const themeClass = computed(() => (isDark.value ? 'dark' : 'light'))

const layoutType = computed(() => route.meta?.layout || 'app')

const isAuthLayout = computed(() => layoutType.value === 'auth')
const isReaderLayout = computed(() => layoutType.value === 'reader')
const isAppLayout = computed(() => layoutType.value === 'app')
const isAdminLayout = computed(() => route.path.startsWith('/admin'))

const showHeader = computed(() => !isAuthLayout.value && !isReaderLayout.value)
const showFooter = computed(() => !isAuthLayout.value && !isReaderLayout.value)

const routeName = computed(() => route.name?.toString() || 'unknown')

const currentTab = computed(() => {
  return route.meta?.tab || appStore.activeTab || 'search'
})

const mainClasses = computed(() => ({
  'app__main--auth': isAuthLayout.value,
  'app__main--reader': isReaderLayout.value,
  'app__main--app': isAppLayout.value && !isAdminLayout.value,
  'app__main--admin': isAdminLayout.value,
  'app__main--fullscreen': isFullscreen.value,
}))

const appClasses = computed(() => ({
  'app--dark': isDark.value,
  'app--light': isLight.value,
  'app--online': isOnline.value,
  'app--offline': !isOnline.value,
  'app--fullscreen': isFullscreen.value,
  'app--maintenance': isMaintenanceMode.value,
}))

// ==========================================================================
//  COMPUTED — Stores
// ==========================================================================

const providersCount = computed(() => providersStore.enabledCount || 0)

const activeJobsCount = computed(() => jobsStore.activeCount || 0)

const libraryItemsCount = computed(() => libraryStore.total || 0)

const storageUsed = computed(() => {
  const stats = libraryStore.stats
  if (stats?.total_size_formatted) return stats.total_size_formatted
  return ''
})

const user = computed(() => authStore.user)
const isAuthenticated = computed(() => authStore.isAuthenticated)
const isAdmin = computed(() => authStore.isAdmin)

// ==========================================================================
//  COMPUTED — Maintenance
// ==========================================================================

const isMaintenanceMode = computed(() => appStore.isMaintenanceMode)

const maintenanceMessage = computed(() => appStore.maintenanceMessage)

const isMaintenanceFullScreen = computed(() => {
  // Mode maintenance complet uniquement si pas sur les routes auth
  return isMaintenanceMode.value && !isAuthLayout.value && !route.path.startsWith('/login')
})

// ==========================================================================
//  COMPUTED — Toasts
// ==========================================================================

const activeToasts = computed(() => toasts.value.slice(-5))

// ==========================================================================
//  COMPUTED — Connexion
// ==========================================================================

const connectionStatusLabel = computed(() => {
  if (!isOnline.value) return 'Hors ligne'
  if (!wsConnected.value) return 'Connecté (dégradé)'
  return 'En ligne'
})

// ==========================================================================
//  MÉTHODES — Toasts
// ==========================================================================

/**
 * Affiche un toast.
 * @param {string} message
 * @param {string} type
 * @param {string} icon
 * @param {number} duration
 * @param {Object} options
 * @returns {string} ID du toast
 */
function showToast(message, type = 'info', icon = null, duration = 4000, options = {}) {
  const id = `toast-${Date.now()}-${++toastIdCounter}`

  const toastItem = {
    id,
    message,
    type,
    icon: icon || getDefaultIcon(type),
    duration,
    closable: options.closable !== false,
    action: options.action || null,
    onAction: options.onAction || null,
    details: options.details || null,
    createdAt: Date.now(),
  }

  toasts.value.push(toastItem)

  // Auto-suppression
  if (duration > 0) {
    const timer = setTimeout(() => {
      removeToast(id)
    }, duration)
    toastsTimers.set(id, timer)
  }

  return id
}

/**
 * Supprime un toast.
 * @param {string} id
 */
function removeToast(id) {
  const index = toasts.value.findIndex((t) => t.id === id)
  if (index !== -1) {
    toasts.value.splice(index, 1)
  }
  if (toastsTimers.has(id)) {
    clearTimeout(toastsTimers.get(id))
    toastsTimers.delete(id)
  }
}

/**
 * Gère l'action d'un toast.
 * @param {Object} toastItem
 */
function handleToastAction(toastItem) {
  if (typeof toastItem.onAction === 'function') {
    try {
      toastItem.onAction(toastItem)
    } catch (err) {
      console.error('Erreur dans l\'action du toast:', err)
    }
  }
  removeToast(toastItem.id)
}

/**
 * Supprime tous les toasts.
 */
function clearAllToasts() {
  toasts.value = []
  toastsTimers.forEach((timer) => clearTimeout(timer))
  toastsTimers.clear()
}

/**
 * Retourne une icône par défaut selon le type.
 * @param {string} type
 * @returns {string}
 */
function getDefaultIcon(type) {
  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️',
    loading: '⏳',
  }
  return icons[type] || '📢'
}

// ==========================================================================
//  MÉTHODES — Global Loading
// ==========================================================================

/**
 * Affiche l'overlay de chargement global.
 * @param {string} message
 * @param {string} subtext
 * @param {number} timeout
 */
function setGlobalLoading(message = 'Chargement...', subtext = '', timeout = 0) {
  globalLoadingMessage.value = message
  globalLoadingSubtext.value = subtext
  globalLoading.value = true

  if (globalLoadingTimeout) {
    clearTimeout(globalLoadingTimeout)
    globalLoadingTimeout = null
  }

  if (timeout > 0) {
    globalLoadingTimeout = setTimeout(() => {
      clearGlobalLoading()
    }, timeout)
  }
}

/**
 * Masque l'overlay de chargement global.
 */
function clearGlobalLoading() {
  globalLoading.value = false
  globalLoadingMessage.value = ''
  globalLoadingSubtext.value = ''

  if (globalLoadingTimeout) {
    clearTimeout(globalLoadingTimeout)
    globalLoadingTimeout = null
  }
}

// ==========================================================================
//  MÉTHODES — Erreur critique
// ==========================================================================

/**
 * Définit une erreur critique.
 * @param {Error|string} error
 * @param {string} details
 */
function setCriticalError(error, details = '') {
  criticalError.value =
    typeof error === 'string' ? error : error?.message || 'Erreur inconnue'
  criticalErrorDetails.value = details
  console.error('💥 [Critical Error]', error)
}

/**
 * Ferme l'erreur critique.
 */
function dismissCriticalError() {
  criticalError.value = null
  criticalErrorDetails.value = ''
}

/**
 * Recharge l'application.
 */
function reloadApp() {
  window.location.reload()
}

/**
 * Copie le rapport d'erreur.
 */
async function copyErrorReport() {
  const report = [
    '=== NexusDL Error Report ===',
    `Date: ${new Date().toISOString()}`,
    `Version: ${appVersion.value}`,
    `URL: ${window.location.href}`,
    `User Agent: ${navigator.userAgent}`,
    `Error: ${criticalError.value}`,
    criticalErrorDetails.value ? `Details:\n${criticalErrorDetails.value}` : '',
  ].join('\n')

  try {
    await navigator.clipboard.writeText(report)
    showToast('Rapport copié dans le presse-papiers', 'success', '📋')
  } catch (err) {
    showToast('Impossible de copier', 'error', '❌')
  }
}

// ==========================================================================
//  MÉTHODES — Navigation
// ==========================================================================

/**
 * Change d'onglet.
 * @param {string} tabId
 */
function handleTabChange(tabId) {
  appStore.setActiveTab(tabId)

  const routeMap = {
    search: '/search',
    library: '/library',
    queue: '/queue',
    settings: '/settings',
    admin: '/admin',
  }

  const target = routeMap[tabId]
  if (target && route.path !== target) {
    router.push(target).catch((err) => {
      if (err.name !== 'NavigationDuplicated') {
        console.error('Erreur navigation:', err)
      }
    })
  }
}

function goToLogin() {
  router.push('/login')
}

function goToRegister() {
  router.push('/register')
}

function goToProfile() {
  router.push('/profile')
}

function goToSettings() {
  router.push('/settings')
}

function goToAdmin() {
  router.push('/admin')
}

async function handleLogout() {
  const confirmed = await showConfirm({
    title: 'Déconnexion',
    message: 'Êtes-vous sûr de vouloir vous déconnecter ?',
    icon: '🚪',
    confirmText: 'Se déconnecter',
    cancelText: 'Annuler',
    variant: 'warning',
  })

  if (confirmed) {
    await authStore.logout('/login')
    showToast('Vous êtes déconnecté', 'info', '👋', 2500)
  }
}

// ==========================================================================
//  MÉTHODES — Thème
// ==========================================================================

/**
 * Bascule le thème.
 */
function handleThemeToggle() {
  toggleTheme()
  const newTheme = isDark.value ? 'sombre' : 'clair'
  showToast(`Thème ${newTheme} activé`, 'info', isDark.value ? '🌙' : '☀️', 1500)
}

// ==========================================================================
//  MÉTHODES — Recherche & Refresh
// ==========================================================================

/**
 * Recherche globale.
 * @param {string} query
 */
async function handleGlobalSearch(query) {
  const q = query?.trim()
  if (!q) return

  try {
    if (q.startsWith('http://') || q.startsWith('https://')) {
      await router.push({ path: '/search', query: { q } })
    } else {
      await router.push({ path: '/library', query: { q } })
    }
  } catch (err) {
    console.error('Erreur recherche globale:', err)
  }
}

/**
 * Refresh global.
 */
async function handleGlobalRefresh() {
  showToast('Rafraîchissement...', 'info', '🔄', 1500)

  try {
    await Promise.allSettled([
      jobsStore.refreshActiveJobs(),
      libraryStore.fetchLibrary(),
      libraryStore.fetchStats(),
      providersStore.fetchProviders(),
    ])
    lastRefreshTime.value = new Date().toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch (err) {
    console.warn('Erreur refresh global:', err)
  }
}

// ==========================================================================
//  MÉTHODES — Réseau
// ==========================================================================

/**
 * Vérifie la connectivité.
 */
async function checkConnectivity() {
  try {
    await api.get('/health')
    isOnline.value = true
  } catch (_) {
    isOnline.value = false
  }
}

// ==========================================================================
//  MÉTHODES — Fullscreen
// ==========================================================================

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

// ==========================================================================
//  MÉTHODES — PWA
// ==========================================================================

function applyPwaUpdate() {
  pwaUpdateAvailable.value = false
  // Envoyer un message au service worker pour forcer l'activation
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistration().then((reg) => {
      if (reg && reg.waiting) {
        reg.waiting.postMessage({ type: 'SKIP_WAITING' })
      }
    })
  }
  setTimeout(() => window.location.reload(), 500)
}

function dismissPwaUpdate() {
  pwaUpdateAvailable.value = false
  pwaUpdateDismissed.value = true
  try {
    localStorage.setItem('nexus-pwa-dismissed', 'true')
  } catch (_) {}
}

// ==========================================================================
//  MÉTHODES — Scroll to top
// ==========================================================================

function handleScroll() {
  showScrollTop.value = window.scrollY > scrollThreshold
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ==========================================================================
//  MÉTHODES — Confirm global
// ==========================================================================

/**
 * Affiche un dialog de confirmation global.
 * @param {Object} options
 * @returns {Promise<boolean>}
 */
function showConfirm(options) {
  return new Promise((resolve, reject) => {
    globalConfirm.show = true
    globalConfirm.title = options.title || 'Confirmation'
    globalConfirm.message = options.message || ''
    globalConfirm.icon = options.icon || '❓'
    globalConfirm.confirmText = options.confirmText || 'Confirmer'
    globalConfirm.cancelText = options.cancelText || 'Annuler'
    globalConfirm.variant = options.variant || 'primary'
    globalConfirm.resolve = resolve
    globalConfirm.reject = reject
  })
}

function acceptGlobalConfirm() {
  if (globalConfirm.resolve) {
    globalConfirm.resolve(true)
  }
  resetGlobalConfirm()
}

function cancelGlobalConfirm() {
  if (globalConfirm.resolve) {
    globalConfirm.resolve(false)
  }
  resetGlobalConfirm()
}

function resetGlobalConfirm() {
  globalConfirm.show = false
  globalConfirm.title = ''
  globalConfirm.message = ''
  globalConfirm.resolve = null
  globalConfirm.reject = null
}

// ==========================================================================
//  MÉTHODES — Initialisation
// ==========================================================================

/**
 * Initialise l'application.
 */
async function initializeApp() {
  if (isAppInitialized.value || isInitializing.value) return

  isInitializing.value = true
  initError.value = null

  try {
    // 1. Initialiser l'authentification (bloquant)
    await authStore.initialize()

    // 2. Initialiser les stores en parallèle (non bloquant)
    const results = await Promise.allSettled([
      jobsStore.initialize({ loadJobs: true, ws: true }),
      libraryStore.initialize({ load: true }),
      providersStore.initialize({ load: true }),
      notifStore.initialize({ load: true }),
    ])

    // Log des échecs éventuels
    results.forEach((result, idx) => {
      if (result.status === 'rejected') {
        const storeName = ['jobs', 'library', 'providers', 'notifications'][idx]
        console.warn(`Erreur init ${storeName}:`, result.reason)
      }
    })

    // 3. Restaurer les préférences
    restoreUserPreferences()

    // 4. Marquer comme initialisé
    isAppInitialized.value = true

    // 5. Message de bienvenue
    if (isAuthenticated.value && user.value) {
      const username = user.value.username || 'utilisateur'
      setTimeout(() => {
        showToast(`👋 Bonjour ${username} !`, 'success', '👋', 3000)
      }, 500)
    }

    console.log(
      `%c🧬 NexusDL ${appVersion.value}`,
      'color: #00d4ff; font-weight: bold; font-size: 14px;',
      `Mode: ${import.meta.env.MODE}`
    )
  } catch (err) {
    console.error('Erreur initialisation:', err)
    initError.value = err.message
    setCriticalError(`Impossible d'initialiser l'application : ${err.message}`)
  } finally {
    isInitializing.value = false
  }
}

/**
 * Restaure les préférences utilisateur.
 */
function restoreUserPreferences() {
  // Restaurer la préférence PWA dismissed
  try {
    const dismissed = localStorage.getItem('nexus-pwa-dismissed')
    if (dismissed === 'true') {
      pwaUpdateDismissed.value = true
    }
  } catch (_) {}

  // Restaurer la préférence de thème
  // (déjà géré par useTheme)
}

// ==========================================================================
//  MÉTHODES — Raccourcis clavier
// ==========================================================================

function handleKeyDown(event) {
  // Ignorer si focus sur input/textarea (sauf pour certains raccourcis)
  const tag = event.target?.tagName
  const isInput =
    tag === 'INPUT' || tag === 'TEXTAREA' || event.target?.isContentEditable

  // === Ctrl/Cmd + 1-5 : changer d'onglet ===
  if ((event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey) {
    const tabMap = {
      1: 'search',
      2: 'library',
      3: 'queue',
      4: 'settings',
      5: 'admin',
    }
    if (tabMap[event.key]) {
      event.preventDefault()
      handleTabChange(tabMap[event.key])
      return
    }

    // === Ctrl/Cmd + K : focus recherche ===
    if (event.key === 'k' || event.key === 'K') {
      event.preventDefault()
      const searchInput = document.querySelector('.nexus-header__search-input')
      if (searchInput) {
        searchInput.focus()
        searchInput.select?.()
      }
      return
    }

    // === Ctrl/Cmd + Shift + D : toggle thème ===
    if (event.shiftKey && (event.key === 'd' || event.key === 'D')) {
      event.preventDefault()
      handleThemeToggle()
      return
    }

    // === Ctrl/Cmd + Shift + R : refresh global ===
    if (event.shiftKey && (event.key === 'r' || event.key === 'R')) {
      event.preventDefault()
      handleGlobalRefresh()
      return
    }

    // === Ctrl/Cmd + / : afficher l'aide ===
    if (event.key === '/' || event.key === '?') {
      event.preventDefault()
      showKeyboardShortcuts()
      return
    }
  }

  // === Échap : fermer menus/modals ===
  if (event.key === 'Escape') {
    if (headerRef.value?.closeAllDropdowns) {
      headerRef.value.closeAllDropdowns()
    }
    clearAllToasts()
    if (globalConfirm.show) {
      cancelGlobalConfirm()
    }
    return
  }

  // === F11 ou F : fullscreen ===
  if (event.key === 'F11') {
    // Laisser le navigateur gérer
    return
  }

  // === Touche / : focus recherche (si pas dans input) ===
  if (event.key === '/' && !isInput) {
    event.preventDefault()
    const searchInput = document.querySelector('.nexus-header__search-input')
    if (searchInput) searchInput.focus()
    return
  }

  // === Touche t : scroll top ===
  if (event.key === 't' && !isInput && !event.ctrlKey && !event.metaKey) {
    if (event.target?.closest?.('input, textarea, select')) return
    scrollToTop()
    return
  }
}

/**
 * Affiche l'aide des raccourcis clavier.
 */
function showKeyboardShortcuts() {
  showToast(
    'Raccourcis : Ctrl+1-5 (onglets), Ctrl+K (recherche), Ctrl+Shift+D (thème), Ctrl+Shift+R (refresh), Échap (fermer), / (recherche)',
    'info',
    '⌨️',
    8000
  )
}

// ==========================================================================
//  MÉTHODES — Activité & Session
// ==========================================================================

function updateLastActivity() {
  lastActivityTime.value = Date.now()
}

function checkInactivity() {
  if (!isAuthenticated.value) return

  const elapsed = Date.now() - lastActivityTime.value
  if (elapsed > INACTIVITY_LIMIT) {
    console.log('🔒 Session expirée par inactivité')
    showToast(
      'Session expirée par inactivité',
      'warning',
      '🔒',
      5000
    )
    authStore.logout('/login')
  }
}

// ==========================================================================
//  MÉTHODES — Handlers globaux
// ==========================================================================

function handleWindowError(event) {
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

  console.error('❌ [Window Error]', event.error || message)

  // En production, envoyer au monitoring si disponible
  // if (window.__nexusSentry) window.__nexusSentry.captureException(event.error)
}

function handleUnhandledRejection(event) {
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

  // Ne pas déclencher d'erreur critique pour les erreurs HTTP 4xx
  if (reason?.response?.status && reason.response.status < 500) {
    return
  }

  // Afficher un toast pour les erreurs non HTTP
  if (!reason?.response) {
    showToast(
      reason?.message || 'Une erreur inattendue est survenue',
      'error',
      '❌',
      5000
    )
  }
}

function handleOnline() {
  isOnline.value = true
  showToast('Connexion rétablie', 'success', '🌐', 2000)
  handleGlobalRefresh()
}

function handleOffline() {
  isOnline.value = false
  showToast('Connexion perdue', 'warning', '📴', 4000)
}

function handleBeforeUnload(event) {
  // Ne pas avertir si en mode maintenance
  if (isMaintenanceMode.value) return

  // Avertir si jobs actifs
  if (activeJobsCount.value > 0) {
    event.preventDefault()
    event.returnValue =
      'Des téléchargements sont en cours. Voulez-vous vraiment quitter ?'
    return event.returnValue
  }
}

// ==========================================================================
//  MÉTHODES — Watchers Route
// ==========================================================================

function handleRouteChange(to, from) {
  // Simuler un chargement de route
  routeLoading.value = true
  if (routeLoadingTimeout) clearTimeout(routeLoadingTimeout)
  routeLoadingTimeout = setTimeout(() => {
    routeLoading.value = false
  }, 300)

  // Fermer les dropdowns
  if (headerRef.value?.closeAllDropdowns) {
    headerRef.value.closeAllDropdowns()
  }

  // Scroll en haut
  window.scrollTo({ top: 0, behavior: 'smooth' })

  // Log en dev
  if (import.meta.env.DEV) {
    console.log(`🧭 ${from.path} → ${to.path}`)
  }
}

// ==========================================================================
//  PROVIDE — Services injectables
// ==========================================================================

provide('showToast', showToast)
provide('removeToast', removeToast)
provide('clearAllToasts', clearAllToasts)
provide('showConfirm', showConfirm)
provide('setGlobalLoading', setGlobalLoading)
provide('clearGlobalLoading', clearGlobalLoading)
provide('setCriticalError', setCriticalError)

// ==========================================================================
//  CYCLE DE VIE
// ==========================================================================

let scrollListener = null
let activityListener = null
let inactivityCheckInterval = null
let routeWatch = null

onMounted(async () => {
  // 1. Initialiser l'application
  await initializeApp()

  // 2. Écouter les événements window
  window.addEventListener('error', handleWindowError)
  window.addEventListener('unhandledrejection', handleUnhandledRejection)
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  window.addEventListener('beforeunload', handleBeforeUnload)

  // 3. Événements document
  document.addEventListener('keydown', handleKeyDown)
  document.addEventListener('fullscreenchange', handleFullscreenChange)

  // 4. Scroll listener
  scrollListener = () => handleScroll()
  window.addEventListener('scroll', scrollListener, { passive: true })

  // 5. Activité utilisateur (pour l'inactivité)
  activityListener = () => updateLastActivity()
  window.addEventListener('mousemove', activityListener, { passive: true })
  window.addEventListener('keydown', activityListener, { passive: true })
  window.addEventListener('click', activityListener, { passive: true })
  window.addEventListener('scroll', activityListener, { passive: true })
  window.addEventListener('touchstart', activityListener, { passive: true })

  // 6. Vérifier l'inactivité toutes les minutes
  inactivityCheckInterval = setInterval(checkInactivity, 60 * 1000)

  // 7. Écouter les événements personnalisés
  window.addEventListener('nexus:pwa-update', () => {
    if (!pwaUpdateDismissed.value) {
      pwaUpdateAvailable.value = true
    }
  })

  window.addEventListener('nexus:logout', () => {
    authStore.logout('/login').catch(() => {})
  })

  window.addEventListener('nexus:error', (e) => {
    if (e.detail?.critical) {
      setCriticalError(e.detail.message, e.detail.details)
    } else {
      showToast(e.detail?.message || 'Erreur', 'error', '❌')
    }
  })

  // 8. Vérifier la connectivité initiale
  if (!navigator.onLine) {
    isOnline.value = false
  }
})

onUnmounted(() => {
  // Nettoyer les écouteurs
  window.removeEventListener('error', handleWindowError)
  window.removeEventListener('unhandledrejection', handleUnhandledRejection)
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  document.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)

  if (scrollListener) {
    window.removeEventListener('scroll', scrollListener)
  }
  if (activityListener) {
    window.removeEventListener('mousemove', activityListener)
    window.removeEventListener('keydown', activityListener)
    window.removeEventListener('click', activityListener)
    window.removeEventListener('scroll', activityListener)
    window.removeEventListener('touchstart', activityListener)
  }

  if (inactivityCheckInterval) {
    clearInterval(inactivityCheckInterval)
  }

  // Nettoyer les timers
  toastsTimers.forEach((timer) => clearTimeout(timer))
  toastsTimers.clear()

  if (globalLoadingTimeout) clearTimeout(globalLoadingTimeout)
  if (routeLoadingTimeout) clearTimeout(routeLoadingTimeout)
})

// ==========================================================================
//  WATCHERS
// ==========================================================================

// Surveiller les changements de route
watch(
  () => route.fullPath,
  (to, from) => {
    handleRouteChange(route, { path: from })
  }
)

// Surveiller la connexion WebSocket
watch(wsConnected, (connected, wasConnected) => {
  if (connected && !wasConnected) {
    console.log('🔌 WebSocket reconnecté')
  } else if (!connected && wasConnected) {
    console.warn('⚠️ WebSocket déconnecté')
  }
})

// Surveiller l'état d'authentification
watch(isAuthenticated, (authenticated, wasAuthenticated) => {
  if (!authenticated && wasAuthenticated) {
    // L'utilisateur vient de se déconnecter
    clearAllToasts()
    if (route.meta?.requiresAuth) {
      router.push('/login')
    }
  }
})

// Surveiller le mode maintenance
watch(isMaintenanceMode, (isMaintenance) => {
  if (isMaintenance) {
    showToast(
      'Mode maintenance activé',
      'warning',
      '🔧',
      5000
    )
  }
})

// ==========================================================================
//  EXPOSITION (dev)
// ==========================================================================

if (import.meta.env.DEV) {
  window.__nexusApp = {
    appStore,
    authStore,
    jobsStore,
    libraryStore,
    providersStore,
    notifStore,
    showToast,
    showConfirm,
    version: appVersion.value,
  }
  console.log('🔧 App exposée dans window.__nexusApp (dev)')
}

// ==========================================================================
//  EXPOSE
// ==========================================================================

defineExpose({
  showToast,
  removeToast,
  clearAllToasts,
  showConfirm,
  setGlobalLoading,
  clearGlobalLoading,
  setCriticalError,
  handleGlobalRefresh,
  handleGlobalSearch,
  handleTabChange,
  reloadApp,
})
</script>

<style lang="scss">
// ==========================================================================
//  RESET GLOBAL
// ==========================================================================

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  scroll-behavior: smooth;
  -webkit-text-size-adjust: 100%;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  font-family: var(
    --font-family,
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    'Helvetica Neue',
    Arial,
    sans-serif
  );
  color: var(--color-text-primary, #e8edf5);
  background-color: var(--color-bg-primary, #0a0e1a);
  min-height: 100vh;
  min-height: 100dvh;
  overflow-x: hidden;
  margin: 0;
  line-height: 1.6;
  transition: background-color 0.3s ease, color 0.3s ease;
}

#app {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
}

// ==========================================================================
//  APP
// ==========================================================================

.app {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  width: 100%;
  background: var(--color-bg-primary, #0a0e1a);
  transition: background-color 0.3s ease;
  isolation: isolate;
}

// ==========================================================================
//  MAIN
// ==========================================================================

.app__main {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  transition: padding 0.3s ease, max-width 0.3s ease;

  &--app {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem 1.5rem 2rem;
  }

  &--admin {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem 1.5rem 2rem;
  }

  &--auth {
    max-width: 100%;
    padding: 0;
    margin: 0;
  }

  &--reader {
    max-width: 100%;
    padding: 0;
    margin: 0;
    overflow: hidden;
    position: relative;
  }

  &--fullscreen {
    padding: 0;
    max-width: 100%;
  }
}

.app__route-component {
  animation: appRouteEnter 0.3s ease;
}

@keyframes appRouteEnter {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

// ==========================================================================
//  FOOTER
// ==========================================================================

.app__footer {
  margin-top: auto;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
  background: var(--color-bg-secondary, #141a2b);
  transition: background-color 0.3s ease;
}

.app__footer-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
}

.app__footer-left,
.app__footer-center,
.app__footer-right {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.app__footer-left {
  flex: 1;
  min-width: 150px;
}

.app__footer-center {
  flex: 1;
  align-items: center;
  text-align: center;
}

.app__footer-right {
  flex: 1;
  align-items: flex-end;
  text-align: right;
}

.app__footer-text {
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

.app__footer-brand {
  font-weight: 700;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.app__footer-sep {
  color: var(--color-border, #1a2538);
  opacity: 0.6;
}

.app__footer-license {
  color: var(--color-text-muted, #6a7a9a);
}

.app__footer-build {
  margin: 0;
  font-size: 0.68rem;
  color: var(--color-text-muted, #6a7a9a);
  opacity: 0.75;
  font-style: italic;
}

.app__footer-tech {
  margin: 0;
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.15rem;
  justify-content: center;

  a {
    color: var(--color-primary, #00d4ff);
    text-decoration: none;
    transition: color 0.15s ease;

    &:hover {
      color: var(--color-primary-light, #66e5ff);
      text-decoration: underline;
    }
  }
}

.app__footer-status {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.app__footer-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6a7a9a;

  &--online {
    background: #4caf50;
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
    animation: appStatusPulse 2s infinite;
  }

  &--offline {
    background: #f44336;
  }

  &--degraded {
    background: #ff9800;
  }
}

@keyframes appStatusPulse {
  0% {
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(76, 175, 80, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
  }
}

.app__footer-status-text {
  font-size: 0.7rem;
}

.app__footer-refresh {
  font-size: 0.65rem;
  opacity: 0.7;
  font-style: italic;
}

// ==========================================================================
//  GLOBAL LOADING
// ==========================================================================

.app__global-loading {
  position: fixed;
  inset: 0;
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 14, 26, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.app__global-loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  text-align: center;
  max-width: 400px;
}

.app__global-loading-text {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-primary, #e8edf5);
}

.app__global-loading-subtext {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
  font-style: italic;
}

// ==========================================================================
//  OFFLINE BANNER
// ==========================================================================

.app__offline-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: linear-gradient(135deg, #f44336, #d32f2f);
  color: #ffffff;
  font-size: 0.82rem;
  font-weight: 500;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.app__offline-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.app__offline-text {
  flex: 1;
}

.app__offline-retry {
  padding: 0.3rem 0.7rem;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius-md, 8px);
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;

  &:hover {
    background: rgba(255, 255, 255, 0.25);
  }
}

// ==========================================================================
//  MAINTENANCE BANNER
// ==========================================================================

.app__maintenance-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: linear-gradient(135deg, #ff9800, #f57c00);
  color: #ffffff;
  font-size: 0.82rem;
  font-weight: 500;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.app__maintenance-banner-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.app__maintenance-banner-text {
  flex: 1;
}

// ==========================================================================
//  MAINTENANCE FULLSCREEN
// ==========================================================================

.app__maintenance-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 99998;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-primary, #0a0e1a);
  padding: 2rem;
}

.app__maintenance-fullscreen-content {
  text-align: center;
  max-width: 520px;
  padding: 2rem;
}

.app__maintenance-fullscreen-icon-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.app__maintenance-fullscreen-icon {
  font-size: 4rem;
  animation: appMaintenanceBounce 2s ease-in-out infinite;
  position: relative;
  z-index: 2;
  filter: drop-shadow(0 4px 16px rgba(255, 152, 0, 0.5));
}

.app__maintenance-fullscreen-ring {
  position: absolute;
  inset: -20px;
  border: 3px solid rgba(255, 152, 0, 0.3);
  border-radius: 50%;
  animation: appMaintenanceRing 2.5s ease-in-out infinite;
}

@keyframes appMaintenanceBounce {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-10px) rotate(-5deg);
  }
}

@keyframes appMaintenanceRing {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.1;
  }
}

.app__maintenance-fullscreen-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  margin: 0 0 0.75rem;
}

.app__maintenance-fullscreen-message {
  color: var(--color-text-secondary, #b0c0d8);
  font-size: 1.05rem;
  margin: 0 0 0.5rem;
  line-height: 1.5;
}

.app__maintenance-fullscreen-sub {
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.85rem;
  margin: 0 0 1.5rem;
}

.app__maintenance-fullscreen-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
}

.app__maintenance-fullscreen-btn {
  padding: 0.6rem 1.4rem;
  background: var(--color-warning, #ff9800);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-md, 8px);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
  }
}

.app__maintenance-fullscreen-link {
  padding: 0.6rem 1.4rem;
  background: transparent;
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  font-size: 0.85rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
}

// ==========================================================================
//  TOASTS
// ==========================================================================

.app__toast-container {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 420px;
  pointer-events: none;
}

.app-toast {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.85rem 1.1rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
  overflow: hidden;
  pointer-events: auto;
  min-width: 280px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);

  &--success {
    border-left: 4px solid #4caf50;
    .app-toast__icon { color: #4caf50; }
    .app-toast__progress { background: #4caf50; }
  }

  &--error {
    border-left: 4px solid #f44336;
    .app-toast__icon { color: #f44336; }
    .app-toast__progress { background: #f44336; }
  }

  &--warning {
    border-left: 4px solid #ff9800;
    .app-toast__icon { color: #ff9800; }
    .app-toast__progress { background: #ff9800; }
  }

  &--info {
    border-left: 4px solid #00d4ff;
    .app-toast__icon { color: #00d4ff; }
    .app-toast__progress { background: #00d4ff; }
  }

  &--loading {
    border-left: 4px solid #9c27b0;
    .app-toast__icon {
      color: #9c27b0;
      animation: appToastSpin 1.5s linear infinite;
    }
  }
}

@keyframes appToastSpin {
  to { transform: rotate(360deg); }
}

.app-toast__icon {
  font-size: 1.3rem;
  flex-shrink: 0;
  line-height: 1;
}

.app-toast__content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.app-toast__message {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text-primary, #e8edf5);
  word-break: break-word;
  line-height: 1.4;
}

.app-toast__details {
  font-size: 0.72rem;
  color: var(--color-text-muted, #6a7a9a);
  word-break: break-word;
  line-height: 1.4;
}

.app-toast__action {
  flex-shrink: 0;
  padding: 0.25rem 0.6rem;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  color: var(--color-primary, #00d4ff);
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  align-self: center;

  &:hover {
    background: rgba(0, 212, 255, 0.1);
    border-color: var(--color-primary, #00d4ff);
  }
}

.app-toast__close {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0.1rem 0.3rem;
  border-radius: var(--radius-sm, 4px);
  transition: all 0.15s ease;
  line-height: 1;
  align-self: flex-start;

  &:hover {
    color: var(--color-text-primary, #e8edf5);
    background: var(--color-bg-hover, #253254);
  }
}

.app-toast__progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  width: 100%;
  transform-origin: left;
  animation: appToastProgress linear forwards;
  opacity: 0.7;
}

@keyframes appToastProgress {
  from { transform: scaleX(1); }
  to { transform: scaleX(0); }
}

// ==========================================================================
//  CRITICAL ERROR
// ==========================================================================

.app__critical-error {
  position: fixed;
  inset: 0;
  z-index: 100000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  padding: 1.5rem;
}

.app__critical-error-content {
  text-align: center;
  max-width: 520px;
  width: 100%;
  padding: 2rem;
  background: var(--color-bg-card, #1a2538);
  border: 2px solid var(--color-error, #f44336);
  border-radius: var(--radius-xl, 16px);
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.8);
}

.app__critical-error-icon {
  font-size: 3.5rem;
  display: block;
  margin-bottom: 0.75rem;
  animation: appCriticalPulse 1.5s ease-in-out infinite;
}

@keyframes appCriticalPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

.app__critical-error-title {
  color: var(--color-text-primary, #e8edf5);
  font-size: 1.35rem;
  margin: 0 0 0.6rem;
  font-weight: 700;
}

.app__critical-error-message {
  color: var(--color-text-secondary, #b0c0d8);
  font-size: 0.9rem;
  margin: 0 0 1rem;
  word-break: break-word;
  line-height: 1.5;
}

.app__critical-error-details {
  margin: 0 0 1.25rem;
  padding: 0.6rem 0.8rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: var(--radius-md, 8px);
  text-align: left;
  font-size: 0.72rem;

  summary {
    cursor: pointer;
    color: var(--color-text-muted, #6a7a9a);
    font-weight: 500;
    padding: 0.2rem 0;
    user-select: none;

    &:hover {
      color: var(--color-text-secondary, #b0c0d8);
    }
  }

  pre {
    margin: 0.5rem 0 0;
    padding: 0.5rem;
    background: rgba(0, 0, 0, 0.4);
    border-radius: var(--radius-sm, 4px);
    color: #e57373;
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 0.68rem;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 200px;
    overflow-y: auto;
  }
}

.app__critical-error-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.app__critical-error-btn {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: var(--radius-md, 8px);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;

  &--primary {
    background: var(--color-error, #f44336);
    color: #ffffff;

    &:hover {
      filter: brightness(1.1);
      transform: translateY(-1px);
    }
  }

  &--neutral {
    background: transparent;
    color: var(--color-text-secondary, #b0c0d8);
    border: 1px solid var(--color-border, #1a2538);

    &:hover {
      background: var(--color-bg-hover, #253254);
      color: var(--color-text-primary, #e8edf5);
    }
  }

  &--link {
    background: transparent;
    color: var(--color-primary, #00d4ff);
    padding: 0.6rem 0.6rem;

    &:hover {
      text-decoration: underline;
    }
  }
}

// ==========================================================================
//  PWA UPDATE
// ==========================================================================

.app__pwa-update {
  position: fixed;
  bottom: 5rem;
  right: 1.5rem;
  z-index: 9998;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-primary, #00d4ff);
  border-radius: var(--radius-lg, 12px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
  max-width: 460px;
  animation: appSlideUp 0.3s ease;
}

@keyframes appSlideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.app__pwa-update-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.app__pwa-update-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.app__pwa-update-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.app__pwa-update-subtitle {
  font-size: 0.72rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.3;
}

.app__pwa-update-actions {
  display: flex;
  gap: 0.35rem;
  flex-shrink: 0;
}

.app__pwa-update-btn {
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: var(--radius-md, 8px);
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;

  &--primary {
    background: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);

    &:hover {
      filter: brightness(1.1);
    }
  }

  &--neutral {
    background: transparent;
    color: var(--color-text-muted, #6a7a9a);
    border: 1px solid var(--color-border, #1a2538);

    &:hover {
      color: var(--color-text-primary, #e8edf5);
      background: var(--color-bg-hover, #253254);
    }
  }
}

// ==========================================================================
//  SCROLL TOP
// ==========================================================================

.app__scroll-top {
  position: fixed;
  bottom: 1.5rem;
  left: 1.5rem;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(0, 212, 255, 0.4);
  transition: all 0.25s ease;
  z-index: 9997;

  &:hover {
    transform: translateY(-4px) scale(1.05);
    box-shadow: 0 8px 24px rgba(0, 212, 255, 0.6);
  }

  &:active {
    transform: translateY(-2px) scale(1);
  }
}

// ==========================================================================
//  ROUTE LOADING BAR
// ==========================================================================

.app__route-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 100000;
  background: transparent;
  overflow: hidden;
}

.app__route-loading-bar {
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, transparent, #00d4ff, #0066ff, transparent);
  animation: appRouteLoadingBar 1.5s ease-in-out infinite;
}

@keyframes appRouteLoadingBar {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(350%);
  }
}

// ==========================================================================
//  GLOBAL CONFIRM
// ==========================================================================

.app__global-confirm {
  position: fixed;
  inset: 0;
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  padding: 1.5rem;
}

.app__global-confirm-content {
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  padding: 1.75rem;
  max-width: 420px;
  width: 100%;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.7);
  animation: appConfirmIn 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes appConfirmIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.app__global-confirm-icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 0.75rem;
}

.app__global-confirm-title {
  margin: 0 0 0.5rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.app__global-confirm-message {
  margin: 0 0 1.25rem;
  font-size: 0.85rem;
  color: var(--color-text-secondary, #b0c0d8);
  line-height: 1.5;
}

.app__global-confirm-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.app__global-confirm-btn {
  padding: 0.55rem 1.2rem;
  border: none;
  border-radius: var(--radius-md, 8px);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  min-width: 100px;

  &--neutral {
    background: transparent;
    color: var(--color-text-secondary, #b0c0d8);
    border: 1px solid var(--color-border, #1a2538);

    &:hover {
      background: var(--color-bg-hover, #253254);
      color: var(--color-text-primary, #e8edf5);
    }
  }

  &--primary {
    background: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);

    &:hover {
      filter: brightness(1.1);
      transform: translateY(-1px);
    }
  }

  &--warning {
    background: var(--color-warning, #ff9800);
    color: #ffffff;

    &:hover {
      filter: brightness(1.1);
      transform: translateY(-1px);
    }
  }

  &--error {
    background: var(--color-error, #f44336);
    color: #ffffff;

    &:hover {
      filter: brightness(1.1);
      transform: translateY(-1px);
    }
  }

  &--success {
    background: var(--color-success, #4caf50);
    color: #ffffff;

    &:hover {
      filter: brightness(1.1);
      transform: translateY(-1px);
    }
  }
}

// ==========================================================================
//  TRANSITIONS
// ==========================================================================

.app-fade-enter-active,
.app-fade-leave-active {
  transition: opacity 0.25s ease;
}

.app-fade-enter-from,
.app-fade-leave-to {
  opacity: 0;
}

.app-slide-up-enter-active,
.app-slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.app-slide-up-enter-from,
.app-slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.app-slide-down-enter-active,
.app-slide-down-leave-active {
  transition: all 0.3s ease;
}

.app-slide-down-enter-from,
.app-slide-down-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.app-toast-list-enter-active,
.app-toast-list-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.app-toast-list-enter-from {
  opacity: 0;
  transform: translateX(60px) scale(0.9);
}

.app-toast-list-leave-to {
  opacity: 0;
  transform: translateX(60px) scale(0.9);
}

.app-toast-list-move {
  transition: transform 0.3s ease;
}

// ==========================================================================
//  RESPONSIVE
// ==========================================================================

@media (max-width: 900px) {
  .app__main--app,
  .app__main--admin {
    padding: 0.75rem 1rem 1.5rem;
  }

  .app__footer {
    padding: 0.85rem 1rem;
  }

  .app__footer-container {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .app__footer-left,
  .app__footer-center,
  .app__footer-right {
    align-items: center;
    text-align: center;
  }
}

@media (max-width: 640px) {
  .app__main--app,
  .app__main--admin {
    padding: 0.5rem 0.75rem 1rem;
  }

  .app__footer {
    padding: 0.65rem 0.75rem;
    font-size: 0.68rem;
  }

  .app__footer-text {
    flex-direction: column;
    gap: 0.15rem;
    justify-content: center;
  }

  .app__footer-sep {
    display: none;
  }

  .app__toast-container {
    bottom: 1rem;
    right: 1rem;
    left: 1rem;
    max-width: none;
  }

  .app-toast {
    min-width: 0;
  }

  .app__pwa-update {
    bottom: 4.5rem;
    right: 0.75rem;
    left: 0.75rem;
    max-width: none;
    flex-wrap: wrap;
  }

  .app__pwa-update-actions {
    width: 100%;
  }

  .app__pwa-update-btn {
    flex: 1;
  }

  .app__scroll-top {
    bottom: 1rem;
    left: 1rem;
    width: 40px;
    height: 40px;
  }

  .app__maintenance-fullscreen-title {
    font-size: 1.5rem;
  }

  .app__maintenance-fullscreen-icon {
    font-size: 3rem;
  }

  .app__critical-error-title {
    font-size: 1.15rem;
  }

  .app__critical-error-icon {
    font-size: 2.5rem;
  }

  .app__critical-error-actions {
    flex-direction: column;
  }

  .app__critical-error-btn {
    width: 100%;
  }

  .app__offline-banner,
  .app__maintenance-banner {
    font-size: 0.75rem;
    padding: 0.5rem 0.75rem;
    flex-wrap: wrap;
  }
}

// ==========================================================================
//  LIGHT MODE
// ==========================================================================

.light-mode {
  .app {
    background: var(--color-bg-primary, #f4f6fa);
  }

  .app__global-loading {
    background: rgba(244, 246, 250, 0.9);
  }

  .app__maintenance-fullscreen {
    background: var(--color-bg-primary, #f4f6fa);
  }

  .app__maintenance-fullscreen-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .app__maintenance-fullscreen-message {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .app__maintenance-fullscreen-sub {
    color: var(--color-text-muted, #7a8a9a);
  }

  .app-toast {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  }

  .app-toast__message {
    color: var(--color-text-primary, #1a1a2e);
  }

  .app-toast__close:hover {
    background: var(--color-bg-hover, #e3e8ef);
  }

  .app__critical-error-content {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-error, #c62828);
    box-shadow: 0 25px 80px rgba(0, 0, 0, 0.25);
  }

  .app__critical-error-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .app__critical-error-message {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .app__footer {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .app__pwa-update {
    background: var(--color-bg-card, #ffffff);
  }

  .app__pwa-update-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .app__global-confirm-content {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .app__global-confirm-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .app__global-confirm-message {
    color: var(--color-text-secondary, #3d4a5c);
  }
}

// ==========================================================================
//  SCROLLBAR GLOBALE
// ==========================================================================

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg-secondary, #141a2b);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: var(--color-border, #1a2538);
  border-radius: 4px;
  transition: background 0.2s ease;

  &:hover {
    background: var(--color-text-muted, #6a7a9a);
  }
}

.light-mode ::-webkit-scrollbar-track {
  background: var(--color-bg-secondary, #e9ecf2);
}

.light-mode ::-webkit-scrollbar-thumb {
  background: var(--color-border, #d0d8e0);

  &:hover {
    background: var(--color-text-muted, #7a8a9a);
  }
}

* {
  scrollbar-width: thin;
  scrollbar-color: var(--color-border, #1a2538) var(--color-bg-secondary, #141a2b);
}

// ==========================================================================
//  SÉLECTION
// ==========================================================================

::selection {
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
}

::-moz-selection {
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
}

// ==========================================================================
//  FOCUS VISIBLE
// ==========================================================================

:focus-visible {
  outline: 2px solid var(--color-primary, #00d4ff);
  outline-offset: 2px;
}

// ==========================================================================
//  REDUCED MOTION
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  .app__maintenance-fullscreen-icon,
  .app__maintenance-fullscreen-ring,
  .app-toast,
  .app-toast__progress,
  .app__footer-status-dot,
  .app__route-loading-bar,
  .app__scroll-top {
    animation: none !important;
  }
}

// ==========================================================================
//  PRINT
// ==========================================================================

@media print {
  .app__footer,
  .app__toast-container,
  .app__scroll-top,
  .app__offline-banner,
  .app__maintenance-banner,
  .app__pwa-update,
  .app__route-loading {
    display: none !important;
  }

  .app {
    background: #ffffff !important;
    color: #000000 !important;
  }

  .app__main {
    padding: 0 !important;
    max-width: 100% !important;
  }
}
</style>
