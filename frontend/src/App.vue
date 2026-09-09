<!-- ==========================================================================
  NexusDL 2.0 - Application Root Component
  Fichier : frontend/src/App.vue
  Description : Composant racine de l'application Vue.js 3
  Version : 2.0.0
========================================================================== -->

<template>
  <div id="app" :class="themeClass">
    <!-- ====================================================================
      Global Loading Overlay (pour les chargements critiques)
    ==================================================================== -->
    <div v-if="globalLoading" class="app-global-loading">
      <NexusSpinner size="lg" variant="gradient" label="Chargement..." />
    </div>

    <!-- ====================================================================
      Mode Maintenance
    ==================================================================== -->
    <div v-if="isMaintenanceMode" class="app-maintenance">
      <div class="app-maintenance__content">
        <span class="app-maintenance__icon">🔧</span>
        <h1 class="app-maintenance__title">Maintenance en cours</h1>
        <p class="app-maintenance__message">{{ maintenanceMessage || 'L\'application est temporairement indisponible.' }}</p>
        <p class="app-maintenance__sub">Revenez dans quelques instants.</p>
      </div>
    </div>

    <!-- ====================================================================
      Layout principal
    ==================================================================== -->
    <template v-else>
      <!-- Header (affiché sur tous les layouts sauf auth et reader) -->
      <NexusHeader
        v-if="showHeader"
        ref="headerRef"
        :current-tab="currentTab"
        :providers-count="providersCount"
        :active-jobs-count="activeJobsCount"
        :library-count="libraryItemsCount"
        :storage-used="storageUsed"
        @change-tab="handleTabChange"
        @toggle-theme="handleThemeToggle"
        @search="handleGlobalSearch"
        @refresh="handleGlobalRefresh"
      />

      <!-- Contenu principal -->
      <main class="app-main" :class="{ 'app-main--auth': isAuthLayout, 'app-main--reader': isReaderLayout }">
        <router-view v-slot="{ Component, route }">
          <transition :name="route.meta?.transition || 'fade'" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </main>

      <!-- Footer -->
      <footer v-if="showFooter" class="app-footer">
        <div class="app-footer__container">
          <p class="app-footer__text">
            <span class="app-footer__brand">🧬 NexusDL {{ appVersion }}</span>
            <span class="app-footer__sep">•</span>
            <span class="app-footer__license">GNU GPL v3.0</span>
            <span class="app-footer__sep">•</span>
            <span class="app-footer__tech">
              Propulsé par
              <a href="https://fastapi.tiangolo.com/" target="_blank" rel="noopener">FastAPI</a>
              et
              <a href="https://vuejs.org/" target="_blank" rel="noopener">Vue.js</a>
            </span>
          </p>
          <p v-if="buildDate" class="app-footer__build">
            Build: {{ buildDate }}
          </p>
        </div>
      </footer>
    </template>

    <!-- ====================================================================
      Toast Global (pour les notifications)
    ==================================================================== -->
    <Teleport to="body">
      <Transition name="toast-slide">
        <div
          v-if="toast.visible"
          class="app-toast"
          :class="`app-toast--${toast.type}`"
          role="alert"
          :aria-live="toast.type === 'error' ? 'assertive' : 'polite'"
        >
          <span class="app-toast__icon">{{ toast.icon }}</span>
          <span class="app-toast__message">{{ toast.message }}</span>
          <button
            v-if="toast.closable !== false"
            type="button"
            class="app-toast__close"
            @click="closeToast"
            aria-label="Fermer la notification"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
      </Transition>
    </Teleport>

    <!-- ====================================================================
      Global Error Boundary (affichage d'erreur critique)
    ==================================================================== -->
    <Teleport to="body">
      <div v-if="criticalError" class="app-critical-error">
        <div class="app-critical-error__content">
          <span class="app-critical-error__icon">💥</span>
          <h2 class="app-critical-error__title">Une erreur critique est survenue</h2>
          <p class="app-critical-error__message">{{ criticalError }}</p>
          <button
            type="button"
            class="app-critical-error__btn"
            @click="reloadApp"
          >
            🔄 Recharger l'application
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted, onUnmounted, provide, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import { useLibraryStore } from '@/stores/library'
import { useNotificationsStore } from '@/stores/notifications'
import { useTheme } from '@/composables/useTheme'
import { useToast } from '@/composables/useToast'
import { useApi } from '@/composables/useApi'
import NexusHeader from '@/components/NexusHeader.vue'
import NexusSpinner from '@/components/common/NexusSpinner.vue'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const route = useRoute()
const router = useRouter()

const appStore = useAppStore()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const libraryStore = useLibraryStore()
const notifStore = useNotificationsStore()
const { isDark, toggleTheme } = useTheme()
const toast = useToast()
const api = useApi()

// ==========================================================================
//  Références
// ==========================================================================

const headerRef = ref(null)
const isAppInitialized = ref(false)
const criticalError = ref(null)

// ==========================================================================
//  État réactif (toast)
// ==========================================================================

const toastState = ref({
  visible: false,
  message: '',
  type: 'info',
  icon: 'ℹ️',
  closable: true,
  duration: 4000,
})
let toastTimer = null

// ==========================================================================
//  Computed (App)
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')
const buildDate = computed(() => import.meta.env.VITE_BUILD_DATE || '')

const themeClass = computed(() => ({
  'dark-mode': isDark.value,
  'light-mode': !isDark.value,
}))

// Layout détection
const isAuthLayout = computed(() => route.meta?.layout === 'auth')
const isReaderLayout = computed(() => route.meta?.layout === 'reader')
const showHeader = computed(() => !isAuthLayout.value && !isReaderLayout.value)
const showFooter = computed(() => !isAuthLayout.value && !isReaderLayout.value)

// Onglet courant
const currentTab = computed(() => route.meta?.tab || appStore.activeTab || 'search')

// Stores computed
const providersCount = computed(() => {
  try {
    const providersStore = useProvidersStore()
    return providersStore.total || 0
  } catch { return 0 }
})

const activeJobsCount = computed(() => jobsStore.activeCount || 0)

const libraryItemsCount = computed(() => libraryStore.total || 0)

const storageUsed = computed(() => {
  // Peut être amélioré avec les stats de la bibliothèque
  const stats = libraryStore.stats
  if (stats?.total_size_formatted) return stats.total_size_formatted
  return '0 MB'
})

const globalLoading = computed(() => appStore.isLoading)

const isMaintenanceMode = computed(() => appStore.isMaintenanceMode)

const maintenanceMessage = computed(() => appStore.maintenanceMessage)

// ==========================================================================
//  Toast (global)
// ==========================================================================

function showToast(message, type = 'info', icon = 'ℹ️', duration = 4000, closable = true) {
  if (toastTimer) {
    clearTimeout(toastTimer)
    toastTimer = null
  }
  toastState.value = {
    visible: true,
    message,
    type,
    icon,
    duration,
    closable,
  }
  if (duration > 0) {
    toastTimer = setTimeout(() => {
      closeToast()
    }, duration)
  }
}

function closeToast() {
  toastState.value.visible = false
  if (toastTimer) {
    clearTimeout(toastTimer)
    toastTimer = null
  }
}

// ==========================================================================
//  Provide (injectables pour les composants enfants)
// ==========================================================================

provide('showToast', showToast)
provide('apiBase', '/api')
provide('appVersion', appVersion.value)

// ==========================================================================
//  Handlers
// ==========================================================================

function handleTabChange(tabId) {
  appStore.setActiveTab(tabId)
  const routeMap = {
    search: '/search',
    library: '/library',
    queue: '/queue',
    settings: '/settings',
    admin: '/admin',
  }
  if (routeMap[tabId] && route.path !== routeMap[tabId]) {
    router.push(routeMap[tabId])
  }
}

function handleThemeToggle(isDarkMode) {
  toggleTheme()
}

function handleGlobalSearch(query) {
  if (query && query.trim()) {
    // Basculer vers l'onglet bibliothèque et appliquer la recherche
    if (currentTab.value !== 'library') {
      router.push('/library')
    }
    // La recherche sera appliquée par le composant LibraryGrid via son exposé
    nextTick(() => {
      const libraryView = document.querySelector('.nexus-library-grid')
      if (libraryView) {
        // Chercher le composant LibraryGrid et appeler setSearch
        // On utilise un événement personnalisé ou on passe par le store
        libraryStore.setSearch(query.trim())
      }
    })
  }
}

function handleGlobalRefresh() {
  showToast('🔄 Rafraîchissement...', 'info', '🔄', 1500)
  // Rafraîchir les stores
  jobsStore.refreshActiveJobs()
  libraryStore.refresh()
  // Rafraîchir les providers
  try {
    const providersStore = useProvidersStore()
    providersStore.fetchProviders()
  } catch {}
}

// ==========================================================================
//  Gestion d'erreur globale
// ==========================================================================

function handleGlobalError(event) {
  console.error('❌ Erreur globale:', event.message || event)
  if (event.message && !event.message.includes('Abort')) {
    criticalError.value = event.message || 'Erreur inattendue'
  }
}

function reloadApp() {
  criticalError.value = null
  window.location.reload()
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  // 1. Charger le thème
  const savedTheme = localStorage.getItem('nexus-theme')
  if (savedTheme === 'dark' || savedTheme === 'light') {
    // Le thème est géré par useTheme
  }

  // 2. Initialiser les stores
  try {
    await authStore.initialize()
    await jobsStore.initialize({ loadJobs: true, ws: true })
    await libraryStore.initialize({ load: true })
    // Providers déjà initialisés via leur store
    try {
      const providersStore = useProvidersStore()
      await providersStore.initialize({ load: true })
    } catch {}

    // 3. Initialiser les notifications
    notifStore.initialize({ load: true })

    // 4. Démarrer le polling pour les jobs (si nécessaire)
    // Déjà géré par le store jobs

    // 5. Marquer comme initialisé
    isAppInitialized.value = true

    // 6. Afficher un toast de bienvenue si l'utilisateur est connecté
    if (authStore.isAuthenticated) {
      const username = authStore.user?.username || 'utilisateur'
      showToast(`👋 Bonjour ${username} !`, 'success', '👋', 3000)
    }

    console.log(`🧬 NexusDL ${appVersion.value} prêt`)
  } catch (err) {
    console.error('❌ Erreur d\'initialisation:', err)
    criticalError.value = `Impossible d'initialiser l'application : ${err.message}`
  }

  // 6. Gestion des erreurs globales
  window.addEventListener('error', handleGlobalError)
  window.addEventListener('unhandledrejection', (event) => {
    handleGlobalError(event.reason)
  })

  // 7. Raccourcis clavier
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('error', handleGlobalError)
  window.removeEventListener('unhandledrejection', handleGlobalError)
  document.removeEventListener('keydown', handleKeyDown)
})

// ==========================================================================
//  Raccourcis clavier
// ==========================================================================

function handleKeyDown(event) {
  // Ctrl/Cmd + 1-4 pour changer d'onglet
  if (event.ctrlKey || event.metaKey) {
    const tabMap = {
      '1': 'search',
      '2': 'library',
      '3': 'queue',
      '4': 'settings',
    }
    const tabId = tabMap[event.key]
    if (tabId) {
      event.preventDefault()
      handleTabChange(tabId)
    }
  }

  // Échap pour fermer les modals / menus
  if (event.key === 'Escape') {
    // Fermer les menus du header
    if (headerRef.value?.closeAllDropdowns) {
      headerRef.value.closeAllDropdowns()
    }
    // Fermer les toasts
    closeToast()
  }

  // Ctrl+F / Cmd+F pour focus sur la recherche
  if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
    event.preventDefault()
    // Focus sur le champ de recherche du header
    const searchInput = document.querySelector('.nexus-header__search-input')
    if (searchInput) {
      searchInput.focus()
    }
  }
}

// ==========================================================================
//  Imports dynamiques pour les stores (éviter les circular dependencies)
// ==========================================================================

import { useProvidersStore } from '@/stores/providers'

// ==========================================================================
//  Exposer
// ==========================================================================

defineExpose({
  showToast,
  closeToast,
  handleGlobalRefresh,
  handleGlobalSearch,
  handleTabChange,
})

// ==========================================================================
//  Styles
// ==========================================================================

</script>

<style lang="scss">
// ==========================================================================
//  Styles globaux (non scoped)
// ==========================================================================

// --- Reset et base (déjà dans global.scss, on ajoute ce qui manque) ---
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
}

body {
  font-family: var(--font-family, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif);
  color: var(--color-text-primary, #e8edf5);
  background-color: var(--color-bg-primary, #0a0e1a);
  transition: background-color 0.3s ease, color 0.3s ease;
  min-height: 100vh;
  min-height: 100dvh;
  overflow-x: hidden;
  margin: 0;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  transition: background-color 0.3s ease;
}

// ==========================================================================
//  Classes de thème
// ==========================================================================

.dark-mode {
  --color-bg-primary: #0a0e1a;
  --color-bg-secondary: #141a2b;
  --color-bg-card: #1a2538;
  --color-bg-input: #1e2a40;
  --color-bg-hover: #253254;
  --color-text-primary: #e8edf5;
  --color-text-secondary: #b0c0d8;
  --color-text-muted: #6a7a9a;
  --color-text-inverse: #0a0e1a;
  --color-border: #1a2538;
  --color-border-light: #253254;
  --color-primary: #00d4ff;
  --color-primary-dark: #0099cc;
  --color-primary-light: #66e5ff;
  --color-secondary: #0066ff;
  --color-secondary-dark: #0044cc;
  --color-success: #4caf50;
  --color-success-dark: #388e3c;
  --color-warning: #ff9800;
  --color-warning-dark: #f57c00;
  --color-error: #f44336;
  --color-error-dark: #c62828;
  --color-info: #2196f3;
  --color-info-dark: #1565c0;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
  --shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.6);
}

.light-mode {
  --color-bg-primary: #f4f6fa;
  --color-bg-secondary: #e9ecf2;
  --color-bg-card: #ffffff;
  --color-bg-input: #f0f2f5;
  --color-bg-hover: #e3e8ef;
  --color-text-primary: #1a1a2e;
  --color-text-secondary: #3d4a5c;
  --color-text-muted: #7a8a9a;
  --color-text-inverse: #ffffff;
  --color-border: #d0d8e0;
  --color-border-light: #e3e8ef;
  --color-primary: #0066cc;
  --color-primary-dark: #004d99;
  --color-primary-light: #3399ff;
  --color-secondary: #0044b3;
  --color-secondary-dark: #003380;
  --color-success: #2e7d32;
  --color-success-dark: #1b5e20;
  --color-warning: #e65100;
  --color-warning-dark: #bf360c;
  --color-error: #c62828;
  --color-error-dark: #b71c1c;
  --color-info: #0d47a1;
  --color-info-dark: #002171;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
  --shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.16);
}

// ==========================================================================
//  Layout principal
// ==========================================================================

.app-main {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 1rem 1.5rem 2rem;
  transition: padding 0.3s ease;

  &--auth {
    max-width: 480px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem 1rem;
  }

  &--reader {
    max-width: 100%;
    padding: 0;
    margin: 0;
  }
}

// ==========================================================================
//  Footer
// ==========================================================================

.app-footer {
  margin-top: auto;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
  background: var(--color-bg-secondary, #141a2b);
  transition: background 0.3s ease;
}

.app-footer__container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
}

.app-footer__text {
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.3rem;
}

.app-footer__brand {
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-secondary, #b0c0d8);
}

.app-footer__sep {
  color: var(--color-border, #1a2538);
}

.app-footer__license {
  color: var(--color-text-muted, #6a7a9a);
}

.app-footer__tech {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  a {
    color: var(--color-primary, #00d4ff);
    text-decoration: none;
    &:hover {
      text-decoration: underline;
    }
  }
}

.app-footer__build {
  margin: 0;
  font-size: 0.65rem;
  color: var(--color-text-muted, #6a7a9a);
  opacity: 0.6;
}

// ==========================================================================
//  Global Loading Overlay
// ==========================================================================

.app-global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  animation: fadeIn 0.3s ease;
}

// ==========================================================================
//  Maintenance Mode
// ==========================================================================

.app-maintenance {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-primary, #0a0e1a);
}

.app-maintenance__content {
  text-align: center;
  max-width: 500px;
  padding: 2rem;
}

.app-maintenance__icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 1rem;
}

.app-maintenance__title {
  font-size: 2rem;
  font-weight: var(--font-weight-bold, 700);
  color: var(--color-text-primary, #e8edf5);
  margin-bottom: 0.5rem;
}

.app-maintenance__message {
  color: var(--color-text-secondary, #b0c0d8);
  font-size: 1.1rem;
  margin-bottom: 0.25rem;
}

.app-maintenance__sub {
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.9rem;
}

// ==========================================================================
//  Toast Global
// ==========================================================================

.app-toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 1rem 0.7rem 1.2rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  box-shadow: var(--shadow-lg, 0 8px 24px rgba(0, 0, 0, 0.5));
  max-width: 480px;
  min-width: 280px;
  animation: toastIn 0.3s ease;

  &--success {
    border-left: 4px solid var(--color-success, #4caf50);
    .app-toast__icon { color: var(--color-success, #4caf50); }
  }
  &--error {
    border-left: 4px solid var(--color-error, #f44336);
    .app-toast__icon { color: var(--color-error, #f44336); }
  }
  &--warning {
    border-left: 4px solid var(--color-warning, #ff9800);
    .app-toast__icon { color: var(--color-warning, #ff9800); }
  }
  &--info {
    border-left: 4px solid var(--color-primary, #00d4ff);
    .app-toast__icon { color: var(--color-primary, #00d4ff); }
  }
}

.app-toast__icon {
  font-size: 1.3rem;
  flex-shrink: 0;
}

.app-toast__message {
  flex: 1;
  font-size: 0.85rem;
  color: var(--color-text-primary, #e8edf5);
  word-break: break-word;
}

.app-toast__close {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0.1rem 0.2rem;
  border-radius: var(--radius-sm, 4px);
  transition: all 0.2s ease;
  &:hover {
    color: var(--color-text-primary, #e8edf5);
    background: var(--color-bg-hover, #253254);
  }
}

// ==========================================================================
//  Critical Error
// ==========================================================================

.app-critical-error {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.app-critical-error__content {
  text-align: center;
  max-width: 500px;
  padding: 2rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-error, #f44336);
  border-radius: var(--radius-lg, 12px);
  box-shadow: var(--shadow-xl, 0 16px 48px rgba(0, 0, 0, 0.6));
}

.app-critical-error__icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.5rem;
}

.app-critical-error__title {
  color: var(--color-text-primary, #e8edf5);
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
}

.app-critical-error__message {
  color: var(--color-text-secondary, #b0c0d8);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
  word-break: break-word;
}

.app-critical-error__btn {
  padding: 0.5rem 1.5rem;
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
  border: none;
  border-radius: var(--radius-md, 8px);
  font-size: 0.9rem;
  font-weight: var(--font-weight-medium, 500);
  cursor: pointer;
  transition: all 0.2s ease;
  &:hover {
    background: var(--color-primary-dark, #0099cc);
    transform: scale(1.02);
  }
}

// ==========================================================================
//  Transitions
// ==========================================================================

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes toastIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: all 0.3s ease;
}
.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 768px) {
  .app-main {
    padding: 0.75rem 0.75rem 1.5rem;
    &--auth {
      padding: 1rem 0.75rem;
    }
  }
  .app-footer {
    padding: 0.75rem 0.75rem;
  }
  .app-footer__container {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .app-footer__text {
    justify-content: center;
  }
  .app-footer__tech {
    flex-wrap: wrap;
    justify-content: center;
  }
  .app-toast {
    bottom: 1rem;
    right: 1rem;
    left: 1rem;
    max-width: none;
    min-width: 0;
    font-size: 0.85rem;
  }
}

@media (max-width: 480px) {
  .app-main {
    padding: 0.5rem 0.5rem 1rem;
  }
  .app-footer {
    padding: 0.5rem 0.5rem;
    font-size: 0.65rem;
  }
  .app-footer__sep {
    display: none;
  }
  .app-footer__text {
    flex-direction: column;
    gap: 0.1rem;
  }
  .app-toast {
    padding: 0.5rem 0.7rem 0.5rem 0.9rem;
    border-radius: var(--radius-md, 8px);
  }
  .app-toast__icon {
    font-size: 1rem;
  }
  .app-toast__message {
    font-size: 0.8rem;
  }
}

// ==========================================================================
//  Mode clair - Support
// ==========================================================================

.light-mode {
  .app-global-loading {
    background: rgba(255, 255, 255, 0.6);
  }
  .app-toast {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    box-shadow: var(--shadow-lg, 0 8px 24px rgba(0, 0, 0, 0.12));
  }
  .app-toast__message {
    color: var(--color-text-primary, #1a1a2e);
  }
  .app-toast__close:hover {
    background: var(--color-bg-hover, #e3e8ef);
  }
  .app-critical-error__content {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-error, #c62828);
  }
  .app-critical-error__title {
    color: var(--color-text-primary, #1a1a2e);
  }
  .app-critical-error__message {
    color: var(--color-text-secondary, #3d4a5c);
  }
  .app-maintenance {
    background: var(--color-bg-primary, #f4f6fa);
  }
  .app-maintenance__title {
    color: var(--color-text-primary, #1a1a2e);
  }
  .app-maintenance__message {
    color: var(--color-text-secondary, #3d4a5c);
  }
  .app-maintenance__sub {
    color: var(--color-text-muted, #7a8a9a);
  }
}

// ==========================================================================
//  Scrollbar globale
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

/* Firefox */
* {
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) var(--color-bg-secondary);
}

.light-mode * {
  scrollbar-color: var(--color-border) var(--color-bg-secondary);
}
</style>
