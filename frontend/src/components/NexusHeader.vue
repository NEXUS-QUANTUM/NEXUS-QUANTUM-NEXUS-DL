<!-- ==========================================================================
  NexusDL 2.0 - NexusHeader Component
  Fichier : frontend/src/components/NexusHeader.vue
  Description : En-tête principal avec navigation, recherche, thème et profil
  Version : 2.0.0
========================================================================== -->

<template>
  <header class="nexus-header" :class="{ 'nexus-header--scrolled': isScrolled }">
    <div class="nexus-header__container">
      <!-- ====================================================================
        Logo & Brand
      ==================================================================== -->
      <div class="nexus-header__brand">
        <router-link to="/" class="nexus-header__logo" aria-label="Accueil NexusDL">
          <svg
            class="nexus-header__logo-icon"
            viewBox="0 0 512 512"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <defs>
              <linearGradient id="headerLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#00d4ff;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#0066ff;stop-opacity:1" />
              </linearGradient>
            </defs>
            <circle cx="256" cy="256" r="200" fill="url(#headerLogoGrad)" />
            <text
              x="256"
              y="290"
              font-family="system-ui, -apple-system, sans-serif"
              font-size="200"
              font-weight="bold"
              text-anchor="middle"
              fill="white"
              dominant-baseline="central"
            >
              N
            </text>
          </svg>
          <span class="nexus-header__brand-name">NexusDL</span>
          <span class="nexus-header__brand-version">v{{ appVersion }}</span>
        </router-link>
      </div>

      <!-- ====================================================================
        Navigation principale
      ==================================================================== -->
      <nav class="nexus-header__nav" aria-label="Navigation principale">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="nexus-header__nav-btn"
          :class="{
            'nexus-header__nav-btn--active': activeTab === tab.id,
          }"
          @click="switchTab(tab.id)"
          :aria-current="activeTab === tab.id ? 'page' : undefined"
          :aria-label="tab.label"
        >
          <span class="nexus-header__nav-icon" aria-hidden="true">{{ tab.icon }}</span>
          <span class="nexus-header__nav-label">{{ tab.label }}</span>
          <span v-if="tab.badge && tab.badge > 0" class="nexus-header__nav-badge">
            {{ tab.badge > 99 ? '99+' : tab.badge }}
          </span>
        </button>
      </nav>

      <!-- ====================================================================
        Actions : recherche, thème, notifications, profil
      ==================================================================== -->
      <div class="nexus-header__actions">
        <!-- Barre de recherche (dépliable sur mobile) -->
        <div class="nexus-header__search" :class="{ 'nexus-header__search--expanded': isSearchExpanded }">
          <button
            type="button"
            class="nexus-header__search-toggle"
            @click="toggleSearch"
            aria-label="Ouvrir la recherche"
            :aria-expanded="isSearchExpanded"
          >
            <span aria-hidden="true">🔍</span>
          </button>
          <div class="nexus-header__search-wrapper">
            <input
              ref="searchInputRef"
              type="text"
              class="nexus-header__search-input"
              v-model="searchQuery"
              placeholder="Rechercher une série..."
              @keydown.enter="submitSearch"
              @focus="isSearchExpanded = true"
              aria-label="Rechercher dans NexusDL"
            />
            <button
              v-if="searchQuery"
              type="button"
              class="nexus-header__search-clear"
              @click="clearSearch"
              aria-label="Effacer la recherche"
            >
              <span aria-hidden="true">&times;</span>
            </button>
            <button
              type="button"
              class="nexus-header__search-submit"
              @click="submitSearch"
              aria-label="Lancer la recherche"
            >
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>

        <!-- Bouton thème -->
        <button
          type="button"
          class="nexus-header__theme-btn"
          @click="toggleTheme"
          :aria-label="isDarkMode ? 'Activer le mode clair' : 'Activer le mode sombre'"
          :title="isDarkMode ? 'Mode clair' : 'Mode sombre'"
        >
          <span aria-hidden="true">{{ isDarkMode ? '☀️' : '🌙' }}</span>
        </button>

        <!-- Notifications -->
        <button
          type="button"
          class="nexus-header__notif-btn"
          @click="toggleNotifications"
          :aria-label="`Notifications${unreadCount > 0 ? ` (${unreadCount} non lues)` : ''}`"
          :aria-expanded="isNotifOpen"
        >
          <span aria-hidden="true">🔔</span>
          <span v-if="unreadCount > 0" class="nexus-header__notif-badge">
            {{ unreadCount > 99 ? '99+' : unreadCount }}
          </span>
        </button>

        <!-- Profil / Connexion -->
        <div class="nexus-header__profile">
          <button
            v-if="isAuthenticated"
            type="button"
            class="nexus-header__profile-btn"
            @click="toggleProfileMenu"
            :aria-label="`Profil de ${user?.username || 'utilisateur'}`"
            :aria-expanded="isProfileOpen"
          >
            <span class="nexus-header__profile-avatar">
              {{ user?.avatar_url ? '' : getInitials(user?.username || 'U') }}
              <img
                v-if="user?.avatar_url"
                :src="user.avatar_url"
                :alt="`Avatar de ${user.username}`"
                class="nexus-header__profile-avatar-img"
                loading="lazy"
              />
            </span>
          </button>
          <div v-else class="nexus-header__auth-buttons">
            <NexusButton
              size="sm"
              variant="ghost"
              @click="goToLogin"
              aria-label="Se connecter"
            >
              Connexion
            </NexusButton>
            <NexusButton
              size="sm"
              variant="primary"
              @click="goToRegister"
              aria-label="S'inscrire"
            >
              Inscription
            </NexusButton>
          </div>

          <!-- Menu déroulant du profil -->
          <Transition name="nexus-header-dropdown">
            <div
              v-if="isProfileOpen && isAuthenticated"
              class="nexus-header__profile-dropdown"
              role="menu"
              aria-label="Menu utilisateur"
            >
              <div class="nexus-header__profile-dropdown-header">
                <span class="nexus-header__profile-dropdown-avatar">
                  {{ getInitials(user?.username || 'U') }}
                </span>
                <div class="nexus-header__profile-dropdown-info">
                  <span class="nexus-header__profile-dropdown-name">
                    {{ user?.full_name || user?.username }}
                  </span>
                  <span class="nexus-header__profile-dropdown-email">{{ user?.email }}</span>
                  <span class="nexus-header__profile-dropdown-role">{{ user?.role }}</span>
                </div>
              </div>
              <div class="nexus-header__profile-dropdown-divider" />
              <button
                class="nexus-header__profile-dropdown-item"
                role="menuitem"
                @click="goToProfile"
              >
                <span aria-hidden="true">👤</span> Mon profil
              </button>
              <button
                v-if="isAdmin"
                class="nexus-header__profile-dropdown-item"
                role="menuitem"
                @click="goToAdmin"
              >
                <span aria-hidden="true">🛠️</span> Administration
              </button>
              <button
                class="nexus-header__profile-dropdown-item"
                role="menuitem"
                @click="goToSettings"
              >
                <span aria-hidden="true">⚙️</span> Paramètres
              </button>
              <div class="nexus-header__profile-dropdown-divider" />
              <button
                class="nexus-header__profile-dropdown-item nexus-header__profile-dropdown-item--danger"
                role="menuitem"
                @click="handleLogout"
              >
                <span aria-hidden="true">🚪</span> Déconnexion
              </button>
            </div>
          </Transition>
        </div>

        <!-- Menu hamburger (mobile) -->
        <button
          type="button"
          class="nexus-header__menu-btn"
          @click="toggleMobileMenu"
          :aria-label="isMobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'"
          :aria-expanded="isMobileMenuOpen"
        >
          <span class="nexus-header__menu-hamburger" :class="{ 'nexus-header__menu-hamburger--active': isMobileMenuOpen }">
            <span />
            <span />
            <span />
          </span>
        </button>
      </div>
    </div>

    <!-- ====================================================================
      Menu mobile
    ==================================================================== -->
    <Transition name="nexus-header-mobile">
      <div v-if="isMobileMenuOpen" class="nexus-header__mobile-menu" role="navigation" aria-label="Menu mobile">
        <div class="nexus-header__mobile-menu-items">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="nexus-header__mobile-menu-item"
            :class="{
              'nexus-header__mobile-menu-item--active': activeTab === tab.id,
            }"
            @click="switchTab(tab.id); closeMobileMenu()"
          >
            <span class="nexus-header__mobile-menu-icon" aria-hidden="true">{{ tab.icon }}</span>
            <span class="nexus-header__mobile-menu-label">{{ tab.label }}</span>
            <span v-if="tab.badge && tab.badge > 0" class="nexus-header__mobile-menu-badge">
              {{ tab.badge > 99 ? '99+' : tab.badge }}
            </span>
          </button>
        </div>
        <div class="nexus-header__mobile-menu-footer">
          <div v-if="isAuthenticated" class="nexus-header__mobile-menu-user">
            <span class="nexus-header__mobile-menu-avatar">
              {{ getInitials(user?.username || 'U') }}
            </span>
            <span class="nexus-header__mobile-menu-username">{{ user?.username }}</span>
          </div>
          <div v-else class="nexus-header__mobile-menu-auth">
            <NexusButton size="sm" variant="ghost" block @click="goToLogin(); closeMobileMenu()">
              Connexion
            </NexusButton>
            <NexusButton size="sm" variant="primary" block @click="goToRegister(); closeMobileMenu()">
              Inscription
            </NexusButton>
          </div>
          <button
            type="button"
            class="nexus-header__mobile-menu-theme"
            @click="toggleTheme"
          >
            <span aria-hidden="true">{{ isDarkMode ? '☀️' : '🌙' }}</span>
            {{ isDarkMode ? 'Mode clair' : 'Mode sombre' }}
          </button>
        </div>
      </div>
    </Transition>

    <!-- ====================================================================
      Panneau des notifications
    ==================================================================== -->
    <Transition name="nexus-header-dropdown">
      <div v-if="isNotifOpen" class="nexus-header__notif-panel" role="dialog" aria-label="Notifications">
        <div class="nexus-header__notif-panel-header">
          <span class="nexus-header__notif-panel-title">🔔 Notifications</span>
          <button
            type="button"
            class="nexus-header__notif-panel-close"
            @click="isNotifOpen = false"
            aria-label="Fermer les notifications"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="nexus-header__notif-panel-body">
          <div v-if="notifications.length === 0" class="nexus-header__notif-empty">
            <span class="nexus-header__notif-empty-icon">📭</span>
            <p>Aucune notification</p>
          </div>
          <div
            v-for="notif in latestNotifications"
            :key="notif.id"
            class="nexus-header__notif-item"
            :class="{
              'nexus-header__notif-item--unread': !notif.read,
              [`nexus-header__notif-item--${notif.type}`]: true,
            }"
            @click="handleNotificationClick(notif)"
          >
            <span class="nexus-header__notif-item-icon">{{ notif.icon || '📢' }}</span>
            <div class="nexus-header__notif-item-content">
              <span class="nexus-header__notif-item-message">{{ notif.message }}</span>
              <span class="nexus-header__notif-item-time">{{ formatRelativeTime(notif.created_at) }}</span>
            </div>
            <button
              v-if="!notif.read"
              type="button"
              class="nexus-header__notif-item-mark"
              @click.stop="markNotificationRead(notif.id)"
              aria-label="Marquer comme lue"
            >
              <span aria-hidden="true">✓</span>
            </button>
          </div>
        </div>
        <div v-if="notifications.length > 0" class="nexus-header__notif-panel-footer">
          <button
            type="button"
            class="nexus-header__notif-panel-mark-all"
            @click="markAllRead"
          >
            Tout marquer comme lu
          </button>
          <button
            type="button"
            class="nexus-header__notif-panel-clear"
            @click="clearNotifications"
          >
            Tout supprimer
          </button>
        </div>
      </div>
    </Transition>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import { useLibraryStore } from '@/stores/library'
import { useNotificationsStore } from '@/stores/notifications'
import { useTheme } from '@/composables/useTheme'
import NexusButton from './common/NexusButton.vue'
import { formatRelativeTime } from '@/utils/formatters'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Onglet courant (reçu du parent) */
  currentTab: {
    type: String,
    default: 'search',
  },
  /** Nombre de providers (pour affichage) */
  providersCount: {
    type: Number,
    default: 0,
  },
  /** Nombre de jobs actifs */
  activeJobsCount: {
    type: Number,
    default: 0,
  },
  /** Nombre d'éléments dans la bibliothèque */
  libraryCount: {
    type: Number,
    default: 0,
  },
  /** Espace utilisé (formaté) */
  storageUsed: {
    type: String,
    default: '',
  },
})

// ==========================================================================
//  Émits
// ==========================================================================

const emit = defineEmits([
  'change-tab',
  'toggle-theme',
  'search',
  'refresh',
])

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const libraryStore = useLibraryStore()
const notifStore = useNotificationsStore()
const { isDark, toggleTheme } = useTheme()

// ==========================================================================
//  État local
// ==========================================================================

const isScrolled = ref(false)
const isSearchExpanded = ref(false)
const isProfileOpen = ref(false)
const isNotifOpen = ref(false)
const isMobileMenuOpen = ref(false)
const searchQuery = ref('')
const searchInputRef = ref(null)

// ==========================================================================
//  Computed
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')

const isAuthenticated = computed(() => authStore.isAuthenticated)
const user = computed(() => authStore.user)
const isAdmin = computed(() => authStore.isAdmin)

const unreadCount = computed(() => notifStore.unreadCount)
const notifications = computed(() => notifStore.notifications)
const latestNotifications = computed(() => notifStore.latest.slice(0, 10))

const isDarkMode = computed(() => isDark.value)

/** Configuration des onglets avec badges */
const tabs = computed(() => [
  {
    id: 'search',
    label: 'Recherche',
    icon: '🔍',
    badge: 0,
  },
  {
    id: 'library',
    label: 'Bibliothèque',
    icon: '📚',
    badge: props.libraryCount || 0,
  },
  {
    id: 'queue',
    label: 'File d\'attente',
    icon: '⏳',
    badge: props.activeJobsCount || 0,
  },
  {
    id: 'settings',
    label: 'Paramètres',
    icon: '⚙️',
    badge: 0,
  },
])

const activeTab = computed({
  get: () => props.currentTab || appStore.activeTab || 'search',
  set: (val) => {
    emit('change-tab', val)
    appStore.setActiveTab(val)
  },
})

// ==========================================================================
//  Méthodes
// ==========================================================================

/** Changer d'onglet */
function switchTab(tabId) {
  if (tabId === activeTab.value) return
  activeTab.value = tabId
  // Fermer les menus
  closeAllDropdowns()
  // Naviguer si nécessaire
  const routeMap = {
    search: '/search',
    library: '/library',
    queue: '/queue',
    settings: '/settings',
  }
  if (routeMap[tabId] && route.path !== routeMap[tabId]) {
    router.push(routeMap[tabId])
  }
}

/** Basculer la recherche (mobile) */
function toggleSearch() {
  isSearchExpanded.value = !isSearchExpanded.value
  if (isSearchExpanded.value) {
    nextTick(() => {
      searchInputRef.value?.focus()
    })
  }
}

/** Soumettre la recherche */
function submitSearch() {
  if (searchQuery.value.trim()) {
    emit('search', searchQuery.value.trim())
    // Basculer sur l'onglet bibliothèque si on est ailleurs
    if (activeTab.value !== 'library') {
      switchTab('library')
    }
    closeAllDropdowns()
  }
}

/** Effacer la recherche */
function clearSearch() {
  searchQuery.value = ''
  emit('search', '')
  searchInputRef.value?.focus()
}

/** Basculer le menu du profil */
function toggleProfileMenu() {
  isProfileOpen.value = !isProfileOpen.value
  if (isProfileOpen.value) {
    isNotifOpen.value = false
  }
}

/** Basculer les notifications */
function toggleNotifications() {
  isNotifOpen.value = !isNotifOpen.value
  if (isNotifOpen.value) {
    isProfileOpen.value = false
  }
}

/** Basculer le menu mobile */
function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
  if (isMobileMenuOpen.value) {
    isProfileOpen.value = false
    isNotifOpen.value = false
    isSearchExpanded.value = false
  }
}

function closeMobileMenu() {
  isMobileMenuOpen.value = false
}

function closeAllDropdowns() {
  isProfileOpen.value = false
  isNotifOpen.value = false
  isSearchExpanded.value = false
}

/** Gestion des notifications */
function handleNotificationClick(notif) {
  // Marquer comme lue
  if (!notif.read) {
    notifStore.markAsRead(notif.id)
  }
  // Action personnalisée
  if (notif.onAction) {
    notif.onAction(notif)
  }
  // Navigation selon le contexte
  if (notif.meta?.route) {
    router.push(notif.meta.route)
  }
  isNotifOpen.value = false
}

function markNotificationRead(id) {
  notifStore.markAsRead(id)
}

function markAllRead() {
  notifStore.markAllAsRead()
}

function clearNotifications() {
  notifStore.clearAll()
  isNotifOpen.value = false
}

/** Profil */
function getInitials(name) {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

function goToLogin() {
  closeAllDropdowns()
  router.push('/login')
}

function goToRegister() {
  closeAllDropdowns()
  router.push('/register')
}

function goToProfile() {
  closeAllDropdowns()
  router.push('/profile')
}

function goToAdmin() {
  closeAllDropdowns()
  router.push('/admin')
}

function goToSettings() {
  closeAllDropdowns()
  router.push('/settings')
}

function handleLogout() {
  closeAllDropdowns()
  authStore.logout()
}

// ==========================================================================
//  Gestion du scroll
// ==========================================================================

function handleScroll() {
  isScrolled.value = window.scrollY > 20
}

// ==========================================================================
//  Click outside (fermeture des dropdowns)
// ==========================================================================

function handleClickOutside(event) {
  const target = event.target
  if (!target) return

  const header = document.querySelector('.nexus-header')
  if (header && header.contains(target)) {
    // Ne pas fermer si on clique à l'intérieur du header
    return
  }

  // Fermer tous les dropdowns
  closeAllDropdowns()
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  document.addEventListener('click', handleClickOutside)
  // Synchroniser l'onglet avec la route
  const routeTab = route.meta?.tab
  if (routeTab && routeTab !== activeTab.value) {
    activeTab.value = routeTab
  }
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  document.removeEventListener('click', handleClickOutside)
})

// ==========================================================================
//  Watchers
// ==========================================================================

// Synchroniser l'onglet avec les changements de route
watch(
  () => route.meta?.tab,
  (newTab) => {
    if (newTab && newTab !== activeTab.value) {
      activeTab.value = newTab
    }
  }
)

// ==========================================================================
//  Exposer
// ==========================================================================

defineExpose({
  switchTab,
  closeAllDropdowns,
  activeTab,
})

// ==========================================================================
//  Styles
// ==========================================================================

</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$header-height: 60px;
$header-bg: var(--color-bg-card, #1a2538);
$header-border: var(--color-border, #1a2538);
$header-shadow: var(--shadow-md, 0 4px 12px rgba(0,0,0,0.4));
$header-transition: all var(--transition-base, 300ms) ease;

// ==========================================================================
//  Header principal
// ==========================================================================

.nexus-header {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: $header-bg;
  border-bottom: 1px solid $header-border;
  transition: $header-transition;
  height: $header-height;
  min-height: $header-height;

  &--scrolled {
    box-shadow: $header-shadow;
  }
}

.nexus-header__container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 0.75rem;
  height: 100%;
  gap: 0.5rem;
}

// ==========================================================================
//  Brand / Logo
// ==========================================================================

.nexus-header__brand {
  flex-shrink: 0;
}

.nexus-header__logo {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  text-decoration: none;
  color: var(--color-text-primary, #e8edf5);
  transition: opacity var(--transition-fast, 150ms) ease;
  &:hover {
    opacity: 0.8;
  }
}

.nexus-header__logo-icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.nexus-header__brand-name {
  font-size: 1.1rem;
  font-weight: var(--font-weight-bold, 700);
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.nexus-header__brand-version {
  font-size: 0.55rem;
  color: var(--color-text-muted, #6a7a9a);
  padding: 0.05rem 0.3rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-sm, 4px);
  border: 1px solid var(--color-border, #1a2538);
  font-weight: var(--font-weight-medium, 500);
  -webkit-text-fill-color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Navigation
// ==========================================================================

.nexus-header__nav {
  display: flex;
  align-items: center;
  gap: 0.15rem;
  flex: 1;
  justify-content: center;
  overflow-x: auto;
  padding: 0 0.5rem;
  scrollbar-width: none;
  &::-webkit-scrollbar {
    display: none;
  }
}

.nexus-header__nav-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.3rem 0.7rem;
  font-size: 0.8rem;
  font-weight: var(--font-weight-medium, 500);
  background: transparent;
  border: none;
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  transition: $header-transition;
  white-space: nowrap;
  position: relative;

  &:hover {
    color: var(--color-text-secondary, #b0c0d8);
    background: var(--color-bg-hover, #253254);
  }

  &--active {
    color: var(--color-primary, #00d4ff);
    background: rgba(0, 212, 255, 0.08);
    &:hover {
      background: rgba(0, 212, 255, 0.12);
    }
    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 20px;
      height: 2px;
      background: var(--color-primary, #00d4ff);
      border-radius: var(--radius-full, 9999px);
    }
  }
}

.nexus-header__nav-icon {
  font-size: 0.9rem;
}

.nexus-header__nav-label {
  font-size: 0.75rem;
}

.nexus-header__nav-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  font-size: 0.6rem;
  font-weight: var(--font-weight-bold, 700);
  background: var(--color-error, #f44336);
  color: var(--color-text-inverse, #ffffff);
  border-radius: var(--radius-full, 9999px);
  line-height: 1;
  margin-left: 0.1rem;
}

// ==========================================================================
//  Actions
// ==========================================================================

.nexus-header__actions {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-shrink: 0;
}

// ==========================================================================
//  Recherche
// ==========================================================================

.nexus-header__search {
  display: flex;
  align-items: center;
  gap: 0.2rem;
}

.nexus-header__search-toggle {
  display: none;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0.2rem 0.3rem;
  border-radius: var(--radius-sm, 4px);
  transition: $header-transition;
  &:hover {
    color: var(--color-text-primary, #e8edf5);
    background: var(--color-bg-hover, #253254);
  }
}

.nexus-header__search-wrapper {
  display: flex;
  align-items: center;
  position: relative;
  background: var(--color-bg-input, #1e2a40);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  transition: $header-transition;
  &:focus-within {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15);
  }
}

.nexus-header__search-input {
  width: 150px;
  padding: 0.3rem 0.5rem;
  font-size: 0.8rem;
  background: transparent;
  border: none;
  outline: none;
  color: var(--color-text-primary, #e8edf5);
  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.nexus-header__search-clear {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.1rem 0.3rem;
  &:hover {
    color: var(--color-text-primary, #e8edf5);
  }
}

.nexus-header__search-submit {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.1rem 0.3rem;
  &:hover {
    color: var(--color-primary, #00d4ff);
  }
}

// ==========================================================================
//  Thème
// ==========================================================================

.nexus-header__theme-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-full, 9999px);
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1rem;
  transition: $header-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
}

// ==========================================================================
//  Notifications
// ==========================================================================

.nexus-header__notif-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-full, 9999px);
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1rem;
  transition: $header-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
}

.nexus-header__notif-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  font-size: 0.55rem;
  font-weight: var(--font-weight-bold, 700);
  background: var(--color-error, #f44336);
  color: var(--color-text-inverse, #ffffff);
  border-radius: var(--radius-full, 9999px);
  line-height: 1;
  border: 2px solid var(--color-bg-card, #1a2538);
}

// ==========================================================================
//  Profil
// ==========================================================================

.nexus-header__profile {
  position: relative;
}

.nexus-header__profile-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--color-primary, #00d4ff);
  border: none;
  border-radius: var(--radius-full, 9999px);
  cursor: pointer;
  transition: $header-transition;
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.3);
  }
}

.nexus-header__profile-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-weight: var(--font-weight-semibold, 600);
  font-size: 0.8rem;
  color: var(--color-text-inverse, #0a0e1a);
  border-radius: inherit;
  overflow: hidden;
}

.nexus-header__profile-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.nexus-header__auth-buttons {
  display: flex;
  gap: 0.3rem;
}

// ==========================================================================
//  Dropdowns (profil et notifications)
// ==========================================================================

.nexus-header__profile-dropdown,
.nexus-header__notif-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 280px;
  max-height: 400px;
  overflow-y: auto;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  box-shadow: var(--shadow-lg, 0 8px 24px rgba(0,0,0,0.5));
  z-index: 1001;
  animation: nexusHeaderDropIn 0.2s ease;
}

.nexus-header__profile-dropdown {
  width: 240px;
  max-height: 420px;
  right: 0;
}

.nexus-header__profile-dropdown-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.nexus-header__profile-dropdown-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-primary, #00d4ff);
  border-radius: var(--radius-full, 9999px);
  font-weight: var(--font-weight-semibold, 600);
  font-size: 1rem;
  color: var(--color-text-inverse, #0a0e1a);
  flex-shrink: 0;
}

.nexus-header__profile-dropdown-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.nexus-header__profile-dropdown-name {
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nexus-header__profile-dropdown-email {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nexus-header__profile-dropdown-role {
  font-size: 0.6rem;
  text-transform: uppercase;
  color: var(--color-primary, #00d4ff);
  font-weight: var(--font-weight-semibold, 600);
}

.nexus-header__profile-dropdown-divider {
  height: 1px;
  background: var(--color-border, #1a2538);
  margin: 0.2rem 0;
}

.nexus-header__profile-dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 1rem;
  width: 100%;
  background: transparent;
  border: none;
  color: var(--color-text-secondary, #b0c0d8);
  font-size: 0.8rem;
  cursor: pointer;
  transition: $header-transition;
  text-align: left;
  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
  &--danger {
    color: var(--color-error, #f44336);
    &:hover {
      background: rgba(244, 67, 54, 0.1);
    }
  }
}

// ==========================================================================
//  Panneau des notifications
// ==========================================================================

.nexus-header__notif-panel {
  width: 340px;
  max-height: 420px;
  right: 0;
  display: flex;
  flex-direction: column;
}

.nexus-header__notif-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
  flex-shrink: 0;
}

.nexus-header__notif-panel-title {
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
  font-size: 0.9rem;
}

.nexus-header__notif-panel-close {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.1rem 0.3rem;
  border-radius: var(--radius-sm, 4px);
  transition: $header-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
}

.nexus-header__notif-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 0.25rem 0;
}

.nexus-header__notif-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.5rem 0;
  color: var(--color-text-muted, #6a7a9a);
  text-align: center;
  font-size: 0.85rem;
}

.nexus-header__notif-empty-icon {
  font-size: 2rem;
  margin-bottom: 0.3rem;
  opacity: 0.5;
}

.nexus-header__notif-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem 0.8rem;
  cursor: pointer;
  transition: $header-transition;
  border-left: 2px solid transparent;

  &--unread {
    background: rgba(0, 212, 255, 0.03);
    border-left-color: var(--color-primary, #00d4ff);
  }
  &--success { border-left-color: var(--color-success, #4caf50); }
  &--error { border-left-color: var(--color-error, #f44336); }
  &--warning { border-left-color: var(--color-warning, #ff9800); }
  &--info { border-left-color: var(--color-info, #2196f3); }

  &:hover {
    background: var(--color-bg-hover, #253254);
  }
}

.nexus-header__notif-item-icon {
  font-size: 1rem;
  flex-shrink: 0;
  margin-top: 0.05rem;
}

.nexus-header__notif-item-content {
  flex: 1;
  min-width: 0;
}

.nexus-header__notif-item-message {
  display: block;
  font-size: 0.8rem;
  color: var(--color-text-secondary, #b0c0d8);
  word-break: break-word;
}

.nexus-header__notif-item-time {
  font-size: 0.6rem;
  color: var(--color-text-muted, #6a7a9a);
  display: block;
  margin-top: 0.1rem;
}

.nexus-header__notif-item-mark {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 0.7rem;
  padding: 0.1rem 0.3rem;
  border-radius: var(--radius-sm, 4px);
  transition: $header-transition;
  flex-shrink: 0;
  &:hover {
    color: var(--color-primary, #00d4ff);
    background: var(--color-bg-hover, #253254);
  }
}

.nexus-header__notif-panel-footer {
  display: flex;
  justify-content: space-between;
  padding: 0.4rem 1rem;
  border-top: 1px solid var(--color-border, #1a2538);
  flex-shrink: 0;
  gap: 0.5rem;
}

.nexus-header__notif-panel-mark-all,
.nexus-header__notif-panel-clear {
  background: transparent;
  border: none;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  padding: 0.1rem 0.3rem;
  transition: $header-transition;
  &:hover {
    color: var(--color-text-primary, #e8edf5);
  }
}

.nexus-header__notif-panel-clear:hover {
  color: var(--color-error, #f44336);
}

// ==========================================================================
//  Menu mobile
// ==========================================================================

.nexus-header__menu-btn {
  display: none;
  background: transparent;
  border: none;
  padding: 0.2rem;
  cursor: pointer;
  border-radius: var(--radius-sm, 4px);
  transition: $header-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
  }
}

.nexus-header__menu-hamburger {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 24px;
  span {
    display: block;
    height: 2px;
    background: var(--color-text-secondary, #b0c0d8);
    border-radius: var(--radius-full, 9999px);
    transition: $header-transition;
    transform-origin: center;
  }
  &--active {
    span:nth-child(1) {
      transform: rotate(45deg) translate(4px, 4px);
    }
    span:nth-child(2) {
      opacity: 0;
    }
    span:nth-child(3) {
      transform: rotate(-45deg) translate(4px, -4px);
    }
  }
}

.nexus-header__mobile-menu {
  position: fixed;
  top: $header-height;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-bg-card, #1a2538);
  border-top: 1px solid var(--color-border, #1a2538);
  z-index: 999;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 0.5rem 0;
}

.nexus-header__mobile-menu-items {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0 0.5rem;
}

.nexus-header__mobile-menu-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 0.8rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-secondary, #b0c0d8);
  font-size: 0.9rem;
  cursor: pointer;
  transition: $header-transition;
  text-align: left;
  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
  &--active {
    color: var(--color-primary, #00d4ff);
    background: rgba(0, 212, 255, 0.08);
  }
}

.nexus-header__mobile-menu-icon {
  font-size: 1.1rem;
}

.nexus-header__mobile-menu-label {
  flex: 1;
}

.nexus-header__mobile-menu-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 4px;
  font-size: 0.6rem;
  font-weight: var(--font-weight-bold, 700);
  background: var(--color-error, #f44336);
  color: var(--color-text-inverse, #ffffff);
  border-radius: var(--radius-full, 9999px);
}

.nexus-header__mobile-menu-footer {
  margin-top: auto;
  padding: 0.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
}

.nexus-header__mobile-menu-user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.5rem;
}

.nexus-header__mobile-menu-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--color-primary, #00d4ff);
  border-radius: var(--radius-full, 9999px);
  font-weight: var(--font-weight-semibold, 600);
  font-size: 0.8rem;
  color: var(--color-text-inverse, #0a0e1a);
}

.nexus-header__mobile-menu-username {
  font-weight: var(--font-weight-medium, 500);
  color: var(--color-text-primary, #e8edf5);
}

.nexus-header__mobile-menu-auth {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding: 0.3rem 0;
}

.nexus-header__mobile-menu-theme {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  width: 100%;
  font-size: 0.8rem;
  transition: $header-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
}

// ==========================================================================
//  Animations
// ==========================================================================

@keyframes nexusHeaderDropIn {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.nexus-header-dropdown-enter-active,
.nexus-header-dropdown-leave-active {
  transition: all 0.2s ease;
}

.nexus-header-dropdown-enter-from,
.nexus-header-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}

.nexus-header-mobile-enter-active,
.nexus-header-mobile-leave-active {
  transition: all 0.25s ease;
}

.nexus-header-mobile-enter-from,
.nexus-header-mobile-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 992px) {
  .nexus-header__nav-label {
    font-size: 0.65rem;
  }
  .nexus-header__nav-btn {
    padding: 0.2rem 0.4rem;
  }
  .nexus-header__search-input {
    width: 120px;
  }
}

@media (max-width: 768px) {
  .nexus-header__brand-name {
    font-size: 0.9rem;
  }
  .nexus-header__brand-version {
    display: none;
  }
  .nexus-header__nav {
    gap: 0.1rem;
  }
  .nexus-header__nav-label {
    display: none;
  }
  .nexus-header__nav-btn {
    padding: 0.3rem 0.5rem;
    &--active::after {
      width: 12px;
    }
  }
  .nexus-header__search-wrapper {
    position: fixed;
    top: $header-height;
    left: 0;
    right: 0;
    width: 100%;
    border-radius: 0;
    background: var(--color-bg-card, #1a2538);
    border: none;
    border-bottom: 1px solid var(--color-border, #1a2538);
    padding: 0.3rem 0.75rem;
    box-shadow: var(--shadow-md, 0 4px 12px rgba(0,0,0,0.4));
    transform: translateY(-120%);
    transition: transform 0.3s ease;
    .nexus-header__search--expanded & {
      transform: translateY(0);
    }
  }
  .nexus-header__search-input {
    width: 100%;
    padding: 0.4rem 0.5rem;
  }
  .nexus-header__search-toggle {
    display: flex;
  }
  .nexus-header__profile-dropdown,
  .nexus-header__notif-panel {
    position: fixed;
    top: $header-height;
    right: 0.5rem;
    width: calc(100% - 1rem);
    max-width: 380px;
    max-height: 60vh;
  }
  .nexus-header__menu-btn {
    display: flex;
  }
  .nexus-header__auth-buttons {
    display: none;
  }
}

@media (max-width: 480px) {
  .nexus-header__container {
    padding: 0 0.4rem;
  }
  .nexus-header__brand-name {
    font-size: 0.8rem;
  }
  .nexus-header__logo-icon {
    width: 28px;
    height: 28px;
  }
  .nexus-header__theme-btn,
  .nexus-header__notif-btn {
    width: 28px;
    height: 28px;
    font-size: 0.8rem;
  }
  .nexus-header__profile-btn {
    width: 28px;
    height: 28px;
    font-size: 0.7rem;
  }
  .nexus-header__profile-dropdown,
  .nexus-header__notif-panel {
    width: calc(100% - 0.8rem);
    right: 0.4rem;
  }
}

// ==========================================================================
//  Support du thème clair
// ==========================================================================

.light-mode {
  .nexus-header {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-header__search-wrapper {
    background: var(--color-bg-input, #f0f2f5);
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-header__search-input {
    color: var(--color-text-primary, #1a1a2e);
    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }
  .nexus-header__profile-dropdown,
  .nexus-header__notif-panel {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    box-shadow: var(--shadow-lg, 0 8px 24px rgba(0,0,0,0.12));
  }
  .nexus-header__profile-dropdown-header {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-header__profile-dropdown-name {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-header__profile-dropdown-email {
    color: var(--color-text-muted, #7a8a9a);
  }
  .nexus-header__profile-dropdown-item {
    color: var(--color-text-secondary, #3d4a5c);
    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
      color: var(--color-text-primary, #1a1a2e);
    }
  }
  .nexus-header__profile-dropdown-divider {
    background: var(--color-border, #d0d8e0);
  }
  .nexus-header__profile-dropdown-role {
    color: var(--color-primary, #0066cc);
  }
  .nexus-header__notif-panel-header {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-header__notif-panel-title {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-header__notif-item {
    &--unread {
      background: rgba(0, 102, 204, 0.03);
    }
    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
    }
  }
  .nexus-header__notif-item-message {
    color: var(--color-text-secondary, #3d4a5c);
  }
  .nexus-header__notif-panel-footer {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-header__notif-panel-mark-all,
  .nexus-header__notif-panel-clear {
    &:hover {
      color: var(--color-text-primary, #1a1a2e);
    }
  }
  .nexus-header__mobile-menu {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-header__mobile-menu-item {
    color: var(--color-text-secondary, #3d4a5c);
    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
      color: var(--color-text-primary, #1a1a2e);
    }
    &--active {
      color: var(--color-primary, #0066cc);
      background: rgba(0, 102, 204, 0.05);
    }
  }
  .nexus-header__mobile-menu-footer {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-header__mobile-menu-username {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-header__mobile-menu-theme {
    color: var(--color-text-secondary, #3d4a5c);
    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
      color: var(--color-text-primary, #1a1a2e);
    }
  }
  .nexus-header__theme-btn,
  .nexus-header__notif-btn {
    border-color: var(--color-border, #d0d8e0);
    color: var(--color-text-muted, #7a8a9a);
    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
      color: var(--color-text-primary, #1a1a2e);
    }
  }
  .nexus-header__nav-btn {
    color: var(--color-text-muted, #7a8a9a);
    &:hover {
      color: var(--color-text-secondary, #3d4a5c);
      background: var(--color-bg-hover, #e3e8ef);
    }
    &--active {
      color: var(--color-primary, #0066cc);
      background: rgba(0, 102, 204, 0.05);
      &::after {
        background: var(--color-primary, #0066cc);
      }
    }
  }
  .nexus-header__nav-badge {
    border-color: var(--color-bg-card, #ffffff);
  }
  .nexus-header__notif-badge {
    border-color: var(--color-bg-card, #ffffff);
  }
  .nexus-header__profile-avatar {
    background: var(--color-primary, #0066cc);
  }
  .nexus-header__search-toggle {
    color: var(--color-text-muted, #7a8a9a);
    &:hover {
      color: var(--color-text-primary, #1a1a2e);
      background: var(--color-bg-hover, #e3e8ef);
    }
  }
  .nexus-header__menu-hamburger span {
    background: var(--color-text-secondary, #3d4a5c);
  }
}
</style>
