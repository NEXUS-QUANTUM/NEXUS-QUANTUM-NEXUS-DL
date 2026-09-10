<!-- ==========================================================================
  NexusDL 2.0 - Admin View (version complète)
  Fichier : frontend/src/views/AdminView.vue
  Description : Tableau de bord principal du panneau d'administration.
                Contient la navigation latérale, les statistiques globales,
                les accès rapides aux sous-sections (Providers, Logs, Users,
                System) et un routeur imbriqué pour les vues enfants.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="admin-view">
    <!-- ====================================================================
      EN-TÊTE — Titre, actions
    ==================================================================== -->
    <header class="admin-view__header">
      <div class="admin-view__header-left">
        <h1 class="admin-view__title">
          <span aria-hidden="true">🛠️</span>
          Administration
        </h1>
        <p class="admin-view__subtitle">
          Panneau de contrôle NexusDL — Gérez votre instance
        </p>
      </div>

      <div class="admin-view__header-right">
        <!-- Statut global du système -->
        <div
          class="admin-view__status"
          :class="`admin-view__status--${systemStatusClass}`"
          :title="systemStatusTitle"
        >
          <span class="admin-view__status-dot" aria-hidden="true" />
          <span class="admin-view__status-text">{{ systemStatusLabel }}</span>
        </div>

        <!-- Bouton rafraîchir -->
        <button
          type="button"
          class="admin-view__btn admin-view__btn--refresh"
          :disabled="loading"
          @click="refreshDashboard"
          aria-label="Rafraîchir le tableau de bord"
          title="Rafraîchir"
        >
          <span v-if="loading" class="admin-view__spinner" aria-hidden="true">⟳</span>
          <span v-else aria-hidden="true">↻</span>
          Rafraîchir
        </button>

        <!-- Retour au site -->
        <router-link
          to="/"
          class="admin-view__btn admin-view__btn--back"
          aria-label="Retour au site"
          title="Retour au site"
        >
          <span aria-hidden="true">🏠</span>
          Retour
        </router-link>
      </div>
    </header>

    <!-- ====================================================================
      LAYOUT PRINCIPAL — Sidebar + Contenu
    ==================================================================== -->
    <div class="admin-view__layout">
      <!-- ================================================================
        SIDEBAR — Navigation
      ================================================================ -->
      <aside class="admin-view__sidebar" :class="{ 'admin-view__sidebar--collapsed': sidebarCollapsed }">
        <!-- Bouton de réduction -->
        <button
          type="button"
          class="admin-view__sidebar-toggle"
          @click="toggleSidebar"
          :aria-label="sidebarCollapsed ? 'Déplier le menu' : 'Réduire le menu'"
          :title="sidebarCollapsed ? 'Déplier' : 'Réduire'"
        >
          <span aria-hidden="true">{{ sidebarCollapsed ? '▶' : '◀' }}</span>
        </button>

        <!-- Navigation -->
        <nav class="admin-view__nav" aria-label="Navigation administration">
          <template v-for="item in navItems" :key="item.name">
            <!-- Séparateur -->
            <div v-if="item.type === 'divider'" class="admin-view__nav-divider">
              <span v-if="!sidebarCollapsed" class="admin-view__nav-divider-label">
                {{ item.label }}
              </span>
            </div>

            <!-- Élément simple -->
            <router-link
              v-else
              :to="item.to"
              class="admin-view__nav-item"
              :class="{ 'admin-view__nav-item--active': isActive(item) }"
              :title="sidebarCollapsed ? item.label : undefined"
              :aria-current="isActive(item) ? 'page' : undefined"
            >
              <span class="admin-view__nav-icon" aria-hidden="true">{{ item.icon }}</span>
              <span v-if="!sidebarCollapsed" class="admin-view__nav-label">
                {{ item.label }}
              </span>
              <span
                v-if="!sidebarCollapsed && item.badge && item.badge > 0"
                class="admin-view__nav-badge"
                :class="`admin-view__nav-badge--${item.badgeVariant || 'primary'}`"
              >
                {{ item.badge > 99 ? '99+' : item.badge }}
              </span>
            </router-link>
          </template>
        </nav>

        <!-- Footer de la sidebar -->
        <div class="admin-view__sidebar-footer">
          <div v-if="!sidebarCollapsed" class="admin-view__sidebar-footer-info">
            <span class="admin-view__sidebar-footer-label">Version</span>
            <span class="admin-view__sidebar-footer-value">v{{ appVersion }}</span>
          </div>
          <div class="admin-view__sidebar-footer-info" v-if="!sidebarCollapsed">
            <span class="admin-view__sidebar-footer-label">Environnement</span>
            <span
              class="admin-view__sidebar-footer-value admin-view__sidebar-footer-value--env"
              :class="`admin-view__sidebar-footer-value--env-${environment}`"
            >
              {{ environment }}
            </span>
          </div>
        </div>
      </aside>

      <!-- ================================================================
        CONTENU PRINCIPAL
      ================================================================ -->
      <main class="admin-view__content">
        <!-- Vue par défaut : Dashboard -->
        <div v-if="isDashboard" class="admin-view__dashboard">
          <!-- Message de bienvenue -->
          <div class="admin-view__welcome">
            <h2 class="admin-view__welcome-title">
              👋 Bienvenue {{ username }} !
            </h2>
            <p class="admin-view__welcome-text">
              Gérez votre instance NexusDL depuis ce panneau central.
              Toutes les modifications sont appliquées en temps réel.
            </p>
          </div>

          <!-- Cartes de statistiques -->
          <div class="admin-view__stats">
            <div
              v-for="stat in dashboardStats"
              :key="stat.id"
              class="admin-view__stat-card"
              :class="`admin-view__stat-card--${stat.variant || 'default'}`"
            >
              <div class="admin-view__stat-icon" aria-hidden="true">
                {{ stat.icon }}
              </div>
              <div class="admin-view__stat-content">
                <span class="admin-view__stat-value">
                  <span v-if="loading && stat.id === 'users'" class="admin-view__stat-loading">...</span>
                  <span v-else>{{ stat.value }}</span>
                </span>
                <span class="admin-view__stat-label">{{ stat.label }}</span>
              </div>
              <router-link
                v-if="stat.link"
                :to="stat.link"
                class="admin-view__stat-link"
                :aria-label="`Voir ${stat.label}`"
                :title="`Voir ${stat.label}`"
              >
                →
              </router-link>
            </div>
          </div>

          <!-- Accès rapides -->
          <div class="admin-view__section">
            <h3 class="admin-view__section-title">⚡ Accès rapides</h3>
            <div class="admin-view__quick-access">
              <router-link
                v-for="quick in quickActions"
                :key="quick.to"
                :to="quick.to"
                class="admin-view__quick-card"
                :class="`admin-view__quick-card--${quick.variant || 'primary'}`"
              >
                <span class="admin-view__quick-icon" aria-hidden="true">{{ quick.icon }}</span>
                <div class="admin-view__quick-content">
                  <span class="admin-view__quick-title">{{ quick.title }}</span>
                  <span class="admin-view__quick-desc">{{ quick.description }}</span>
                </div>
                <span class="admin-view__quick-arrow" aria-hidden="true">→</span>
              </router-link>
            </div>
          </div>

          <!-- Informations système rapides -->
          <div class="admin-view__section">
            <h3 class="admin-view__section-title">📊 État du système</h3>
            <div class="admin-view__system-info">
              <div class="admin-view__system-info-item">
                <span class="admin-view__system-info-label">Version</span>
                <span class="admin-view__system-info-value">v{{ appVersion }}</span>
              </div>
              <div class="admin-view__system-info-item">
                <span class="admin-view__system-info-label">Environnement</span>
                <span
                  class="admin-view__system-info-badge"
                  :class="`admin-view__system-info-badge--${environment}`"
                >
                  {{ environment }}
                </span>
              </div>
              <div class="admin-view__system-info-item">
                <span class="admin-view__system-info-label">Providers</span>
                <span class="admin-view__system-info-value">{{ providersCount }} actifs</span>
              </div>
              <div class="admin-view__system-info-item">
                <span class="admin-view__system-info-label">Jobs en cours</span>
                <span class="admin-view__system-info-value">{{ activeJobsCount }}</span>
              </div>
              <div class="admin-view__system-info-item">
                <span class="admin-view__system-info-label">Bibliothèque</span>
                <span class="admin-view__system-info-value">{{ libraryCount }} éléments</span>
              </div>
              <div class="admin-view__system-info-item">
                <span class="admin-view__system-info-label">Stockage</span>
                <span class="admin-view__system-info-value">{{ storageUsed || 'N/A' }}</span>
              </div>
            </div>
          </div>

          <!-- Activité récente -->
          <div v-if="recentActivity.length > 0" class="admin-view__section">
            <h3 class="admin-view__section-title">📋 Activité récente</h3>
            <div class="admin-view__activity">
              <div
                v-for="(activity, idx) in recentActivity"
                :key="idx"
                class="admin-view__activity-item"
                :class="`admin-view__activity-item--${activity.type}`"
              >
                <span class="admin-view__activity-icon" aria-hidden="true">{{ activity.icon }}</span>
                <div class="admin-view__activity-content">
                  <span class="admin-view__activity-text">{{ activity.text }}</span>
                  <span class="admin-view__activity-time">{{ activity.time }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Sous-vues (Providers, Logs, Users, System) -->
        <router-view v-else v-slot="{ Component }">
          <transition name="admin-view-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- ====================================================================
      PIED DE PAGE
    ==================================================================== -->
    <footer class="admin-view__footer">
      <span class="admin-view__footer-info">
        🧬 NexusDL {{ appVersion }} — Panneau d'administration
      </span>
      <span v-if="lastUpdated" class="admin-view__footer-updated">
        Dernière mise à jour : {{ formatDateTime(lastUpdated) }}
      </span>
    </footer>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProvidersStore } from '@/stores/providers'
import { useJobsStore } from '@/stores/jobs'
import { useLibraryStore } from '@/stores/library'
import { useToast } from '@/composables/useToast'
import { useApi } from '@/composables/useApi'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const providersStore = useProvidersStore()
const jobsStore = useJobsStore()
const libraryStore = useLibraryStore()
const toast = useToast()
const api = useApi()

// ==========================================================================
//  État réactif
// ==========================================================================

const loading = ref(false)
const lastUpdated = ref(null)
const sidebarCollapsed = ref(false)
const recentActivity = ref([])

// Cache pour les stats système
const systemHealth = ref(null)

// ==========================================================================
//  Computed
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')

const environment = computed(() => import.meta.env.MODE || 'production')

const username = computed(() => {
  return authStore.user?.full_name || authStore.user?.username || 'Administrateur'
})

const providersCount = computed(() => providersStore.enabledCount || 0)

const activeJobsCount = computed(() => jobsStore.activeCount || 0)

const libraryCount = computed(() => libraryStore.total || 0)

const storageUsed = computed(() => {
  const stats = libraryStore.stats
  if (stats?.total_size_formatted) return stats.total_size_formatted
  return ''
})

/**
 * Vérifie si on est sur le dashboard (route racine /admin).
 */
const isDashboard = computed(() => {
  return route.path === '/admin' || route.path === '/admin/'
})

/**
 * Classe du statut système.
 */
const systemStatusClass = computed(() => {
  if (!systemHealth.value) return 'unknown'
  return systemHealth.value.status === 'healthy' ? 'ok' : 'error'
})

/**
 * Libellé du statut système.
 */
const systemStatusLabel = computed(() => {
  if (!systemHealth.value) return 'Vérification...'
  return systemHealth.value.status === 'healthy' ? '✅ Opérationnel' : '❌ En erreur'
})

/**
 * Titre du statut système.
 */
const systemStatusTitle = computed(() => {
  if (!systemHealth.value) return 'Statut inconnu'
  if (systemHealth.value.status === 'healthy') {
    return 'Tous les systèmes sont opérationnels'
  }
  return 'Certains systèmes sont en erreur'
})

// ==========================================================================
//  Navigation
// ==========================================================================

const navItems = computed(() => [
  {
    type: 'divider',
    label: 'Principal',
  },
  {
    name: 'admin-dashboard',
    to: '/admin',
    icon: '🏠',
    label: 'Tableau de bord',
  },
  {
    type: 'divider',
    label: 'Gestion',
  },
  {
    name: 'admin-providers',
    to: '/admin/providers',
    icon: '🌐',
    label: 'Providers',
    badge: providersCount.value,
    badgeVariant: 'primary',
  },
  {
    name: 'admin-users',
    to: '/admin/users',
    icon: '👥',
    label: 'Utilisateurs',
    badge: null,
  },
  {
    type: 'divider',
    label: 'Monitoring',
  },
  {
    name: 'admin-logs',
    to: '/admin/logs',
    icon: '📋',
    label: 'Logs',
    badge: null,
  },
  {
    name: 'admin-system',
    to: '/admin/system',
    icon: '⚙️',
    label: 'Système',
    badge: null,
  },
])

/**
 * Vérifie si un élément de navigation est actif.
 * @param {Object} item
 * @returns {boolean}
 */
function isActive(item) {
  if (!item.to) return false
  if (item.to === '/admin') {
    return route.path === '/admin' || route.path === '/admin/'
  }
  return route.path.startsWith(item.to)
}

// ==========================================================================
//  Statistiques du dashboard
// ==========================================================================

const dashboardStats = computed(() => [
  {
    id: 'providers',
    icon: '🌐',
    label: 'Providers actifs',
    value: providersCount.value,
    variant: 'primary',
    link: '/admin/providers',
  },
  {
    id: 'users',
    icon: '👥',
    label: 'Utilisateurs',
    value: '—',
    variant: 'info',
    link: '/admin/users',
  },
  {
    id: 'jobs',
    icon: '⏳',
    label: 'Jobs actifs',
    value: activeJobsCount.value,
    variant: 'warning',
    link: '/queue',
  },
  {
    id: 'library',
    icon: '📚',
    label: 'Bibliothèque',
    value: libraryCount.value,
    variant: 'success',
    link: '/library',
  },
])

// ==========================================================================
//  Actions rapides
// ==========================================================================

const quickActions = [
  {
    to: '/admin/providers',
    icon: '🌐',
    title: 'Gérer les providers',
    description: 'Activer, désactiver ou configurer les sites de scan',
    variant: 'primary',
  },
  {
    to: '/admin/users',
    icon: '👥',
    title: 'Gérer les utilisateurs',
    description: 'Créer, modifier ou supprimer des comptes',
    variant: 'info',
  },
  {
    to: '/admin/logs',
    icon: '📋',
    title: 'Consulter les logs',
    description: 'Analyser les journaux d\'exécution du backend',
    variant: 'warning',
  },
  {
    to: '/admin/system',
    icon: '⚙️',
    title: 'Superviser le système',
    description: 'CPU, mémoire, disque et healthcheck en temps réel',
    variant: 'success',
  },
]

// ==========================================================================
//  Méthodes
// ==========================================================================

/**
 * Rafraîchit toutes les données du dashboard.
 */
async function refreshDashboard() {
  loading.value = true
  try {
    await Promise.allSettled([
      fetchHealth(),
      providersStore.fetchProviders(),
      jobsStore.refreshActiveJobs(),
      libraryStore.fetchLibrary(),
      libraryStore.fetchStats(),
    ])
    lastUpdated.value = new Date().toISOString()
    toast.info('Tableau de bord rafraîchi', '🔄', 1500)
  } catch (err) {
    console.error('Erreur rafraîchissement dashboard:', err)
  } finally {
    loading.value = false
  }
}

/**
 * Récupère le healthcheck du système.
 */
async function fetchHealth() {
  try {
    const response = await api.get('/system/health')
    systemHealth.value = response.data || response
  } catch (err) {
    systemHealth.value = { status: 'unhealthy' }
  }
}

/**
 * Ajoute une activité récente.
 * @param {string} text
 * @param {string} type
 * @param {string} icon
 */
function addActivity(text, type = 'info', icon = 'ℹ️') {
  recentActivity.value.unshift({
    text,
    type,
    icon,
    time: dayjs().format('HH:mm'),
  })
  if (recentActivity.value.length > 10) {
    recentActivity.value = recentActivity.value.slice(0, 10)
  }
}

/**
 * Toggle la sidebar.
 */
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  try {
    localStorage.setItem('nexus-admin-sidebar-collapsed', String(sidebarCollapsed.value))
  } catch (_) {
    // Ignorer
  }
}

/**
 * Formate une date.
 * @param {string} date
 * @returns {string}
 */
function formatDateTime(date) {
  if (!date) return ''
  try {
    const d = dayjs(date)
    return d.isValid() ? d.format('DD/MM/YYYY HH:mm:ss') : ''
  } catch (_) {
    return ''
  }
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  // Restaurer l'état de la sidebar
  try {
    const saved = localStorage.getItem('nexus-admin-sidebar-collapsed')
    if (saved === 'true') sidebarCollapsed.value = true
  } catch (_) {
    // Ignorer
  }

  // Charger le healthcheck
  await fetchHealth()

  // Initialiser les stores si nécessaire
  if (providersStore.total === 0) {
    providersStore.fetchProviders().catch(() => null)
  }
  if (jobsStore.totalJobs === 0) {
    jobsStore.refreshActiveJobs().catch(() => null)
  }
  if (libraryStore.total === 0) {
    libraryStore.fetchLibrary().catch(() => null)
  }

  addActivity('Panneau d\'administration chargé', 'info', '🛠️')
})

onUnmounted(() => {
  // Nettoyage si nécessaire
})

// Recharger le healthcheck quand on revient sur le dashboard
watch(
  () => route.path,
  (newPath) => {
    if (newPath === '/admin' || newPath === '/admin/') {
      fetchHealth()
      lastUpdated.value = new Date().toISOString()
    }
  }
)
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.admin-view {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--color-bg-primary, #0a0e1a);
  color: var(--color-text-primary, #e8edf5);
}

// ==========================================================================
//  Header
// ==========================================================================

.admin-view__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  background: var(--color-bg-card, #1a2538);
  border-bottom: 1px solid var(--color-border, #1a2538);
  position: sticky;
  top: 0;
  z-index: 20;
}

.admin-view__header-left {
  flex: 1;
  min-width: 200px;
}

.admin-view__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.admin-view__subtitle {
  margin: 0.1rem 0 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
}

.admin-view__header-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

// ==========================================================================
//  Statut système
// ==========================================================================

.admin-view__status {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.7rem;
  border-radius: var(--radius-full, 9999px);
  font-size: 0.7rem;
  font-weight: 600;
  border: 1px solid var(--color-border, #1a2538);
  background: var(--color-bg-secondary, #141a2b);
  white-space: nowrap;

  &--ok {
    border-color: rgba(76, 175, 80, 0.4);
    background: rgba(76, 175, 80, 0.1);
    color: #4caf50;
    .admin-view__status-dot { background: #4caf50; }
  }

  &--error {
    border-color: rgba(244, 67, 54, 0.4);
    background: rgba(244, 67, 54, 0.1);
    color: #f44336;
    .admin-view__status-dot {
      background: #f44336;
      animation: adminViewPulse 1s infinite;
    }
  }

  &--unknown {
    color: var(--color-text-muted, #6a7a9a);
    .admin-view__status-dot { background: #6a7a9a; }
  }
}

.admin-view__status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

@keyframes adminViewPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

// ==========================================================================
//  Boutons
// ==========================================================================

.admin-view__btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.7rem;
  font-size: 0.75rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: all 0.15s ease;
  text-decoration: none;
  white-space: nowrap;

  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-border-light, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &--refresh:hover:not(:disabled) {
    border-color: var(--color-info, #2196f3);
    color: var(--color-info, #2196f3);
  }

  &--back:hover {
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-primary, #00d4ff);
  }
}

.admin-view__spinner {
  display: inline-block;
  animation: adminViewSpin 0.8s linear infinite;
}

@keyframes adminViewSpin {
  to { transform: rotate(360deg); }
}

// ==========================================================================
//  Layout principal (Sidebar + Content)
// ==========================================================================

.admin-view__layout {
  display: flex;
  flex: 1;
  gap: 1rem;
  padding: 1rem 1.25rem;
  min-height: calc(100vh - 140px);
}

// ==========================================================================
//  Sidebar
// ==========================================================================

.admin-view__sidebar {
  flex: 0 0 220px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  transition: flex-basis 0.25s ease, padding 0.25s ease;
  position: sticky;
  top: 1rem;
  max-height: calc(100vh - 2rem);
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
    border-radius: 2px;
  }

  &--collapsed {
    flex: 0 0 64px;
    padding: 0.5rem 0.4rem;
    overflow: visible;
  }
}

.admin-view__sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: flex-end;
  width: 24px;
  height: 24px;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 0.6rem;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
    border-color: var(--color-primary, #00d4ff);
  }
}

.admin-view__nav {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  flex: 1;
}

.admin-view__nav-divider {
  padding: 0.5rem 0.5rem 0.15rem;
  margin-top: 0.25rem;
}

.admin-view__nav-divider-label {
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted, #6a7a9a);
  opacity: 0.7;
}

.admin-view__nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  background: transparent;
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid transparent;
  border-radius: var(--radius-md, 8px);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
  position: relative;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &--active {
    background: rgba(0, 212, 255, 0.1);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-primary, #00d4ff);

    &:hover {
      background: rgba(0, 212, 255, 0.15);
    }

    &::before {
      content: '';
      position: absolute;
      left: -1px;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 60%;
      background: var(--color-primary, #00d4ff);
      border-radius: 0 3px 3px 0;
    }
  }

  .admin-view__sidebar--collapsed & {
    justify-content: center;
    padding: 0.5rem 0.3rem;
  }
}

.admin-view__nav-icon {
  font-size: 1rem;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
}

.admin-view__nav-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.admin-view__nav-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  font-size: 0.6rem;
  font-weight: 700;
  border-radius: var(--radius-full, 9999px);
  color: var(--color-text-inverse, #0a0e1a);

  &--primary {
    background: var(--color-primary, #00d4ff);
  }
  &--info {
    background: #2196f3;
    color: #ffffff;
  }
  &--warning {
    background: #ff9800;
  }
  &--error {
    background: #f44336;
    color: #ffffff;
  }
}

.admin-view__sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
  margin-top: auto;
}

.admin-view__sidebar-footer-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.65rem;
}

.admin-view__sidebar-footer-label {
  color: var(--color-text-muted, #6a7a9a);
}

.admin-view__sidebar-footer-value {
  color: var(--color-text-secondary, #b0c0d8);
  font-weight: 500;

  &--env {
    padding: 0 0.35rem;
    border-radius: var(--radius-sm, 4px);
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  &--env-production {
    background: rgba(76, 175, 80, 0.15);
    color: #4caf50;
  }
  &--env-development {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
  }
  &--env-test {
    background: rgba(33, 150, 243, 0.15);
    color: #2196f3;
  }
}

// ==========================================================================
//  Contenu principal
// ==========================================================================

.admin-view__content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

// ==========================================================================
//  Dashboard
// ==========================================================================

.admin-view__dashboard {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.admin-view__welcome {
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(0, 102, 255, 0.05));
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
}

.admin-view__welcome-title {
  margin: 0 0 0.3rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.admin-view__welcome-text {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-secondary, #b0c0d8);
  line-height: 1.5;
}

// ==========================================================================
//  Cartes de statistiques
// ==========================================================================

.admin-view__stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.admin-view__stat-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
    border-color: var(--color-primary, #00d4ff);
  }

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
  }

  &--primary::before { background: linear-gradient(180deg, #00d4ff, #0066ff); }
  &--info::before { background: linear-gradient(180deg, #2196f3, #1565c0); }
  &--warning::before { background: linear-gradient(180deg, #ff9800, #f57c00); }
  &--success::before { background: linear-gradient(180deg, #4caf50, #388e3c); }
}

.admin-view__stat-icon {
  font-size: 1.8rem;
  flex-shrink: 0;
}

.admin-view__stat-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.admin-view__stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.admin-view__stat-loading {
  opacity: 0.5;
}

.admin-view__stat-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #6a7a9a);
  margin-top: 0.1rem;
}

.admin-view__stat-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-full, 9999px);
  color: var(--color-text-muted, #6a7a9a);
  text-decoration: none;
  font-size: 0.8rem;
  transition: all 0.15s ease;
  flex-shrink: 0;

  &:hover {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
    transform: translateX(2px);
  }
}

// ==========================================================================
//  Sections
// ==========================================================================

.admin-view__section {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.admin-view__section-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

// ==========================================================================
//  Accès rapides
// ==========================================================================

.admin-view__quick-access {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 0.6rem;
}

.admin-view__quick-card {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.8rem 0.9rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  text-decoration: none;
  color: inherit;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);

    .admin-view__quick-arrow {
      transform: translateX(4px);
      opacity: 1;
    }
  }

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
  }

  &--primary::before { background: #00d4ff; }
  &--info::before { background: #2196f3; }
  &--warning::before { background: #ff9800; }
  &--success::before { background: #4caf50; }

  &--primary:hover { border-color: #00d4ff; }
  &--info:hover { border-color: #2196f3; }
  &--warning:hover { border-color: #ff9800; }
  &--success:hover { border-color: #4caf50; }
}

.admin-view__quick-icon {
  font-size: 1.4rem;
  flex-shrink: 0;
}

.admin-view__quick-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.admin-view__quick-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.admin-view__quick-desc {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.4;
}

.admin-view__quick-arrow {
  font-size: 1rem;
  color: var(--color-text-muted, #6a7a9a);
  opacity: 0.5;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

// ==========================================================================
//  État du système
// ==========================================================================

.admin-view__system-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
}

.admin-view__system-info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.5rem;
  font-size: 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-sm, 4px);
}

.admin-view__system-info-label {
  color: var(--color-text-muted, #6a7a9a);
}

.admin-view__system-info-value {
  color: var(--color-text-primary, #e8edf5);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.admin-view__system-info-badge {
  padding: 0.1rem 0.45rem;
  font-size: 0.65rem;
  font-weight: 600;
  border-radius: var(--radius-sm, 4px);
  text-transform: uppercase;
  letter-spacing: 0.05em;

  &--production {
    background: rgba(76, 175, 80, 0.15);
    color: #4caf50;
  }
  &--development {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
  }
  &--test {
    background: rgba(33, 150, 243, 0.15);
    color: #2196f3;
  }
}

// ==========================================================================
//  Activité récente
// ==========================================================================

.admin-view__activity {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding: 0.6rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  max-height: 300px;
  overflow-y: auto;
}

.admin-view__activity-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  border-radius: var(--radius-sm, 4px);
  background: var(--color-bg-secondary, #141a2b);
  font-size: 0.75rem;
  border-left: 3px solid var(--color-border, #1a2538);

  &--info { border-left-color: #2196f3; }
  &--success { border-left-color: #4caf50; }
  &--warning { border-left-color: #ff9800; }
  &--error { border-left-color: #f44336; }
}

.admin-view__activity-icon {
  flex-shrink: 0;
  font-size: 0.9rem;
}

.admin-view__activity-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
  min-width: 0;
}

.admin-view__activity-text {
  color: var(--color-text-secondary, #b0c0d8);
}

.admin-view__activity-time {
  font-size: 0.65rem;
  color: var(--color-text-muted, #6a7a9a);
  white-space: nowrap;
}

// ==========================================================================
//  Transitions
// ==========================================================================

.admin-view-fade-enter-active,
.admin-view-fade-leave-active {
  transition: all 0.25s ease;
}

.admin-view-fade-enter-from,
.admin-view-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

// ==========================================================================
//  Footer
// ==========================================================================

.admin-view__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 1.25rem;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  background: var(--color-bg-secondary, #141a2b);
  border-top: 1px solid var(--color-border, #1a2538);
}

.admin-view__footer-updated {
  font-style: italic;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 900px) {
  .admin-view__layout {
    flex-direction: column;
    padding: 0.75rem;
  }

  .admin-view__sidebar {
    flex: none;
    position: static;
    max-height: none;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 0.3rem;
    padding: 0.5rem;

    &--collapsed {
      flex: none;
    }
  }

  .admin-view__sidebar-toggle {
    display: none;
  }

  .admin-view__nav {
    flex-direction: row;
    flex-wrap: wrap;
    flex: 1;
    gap: 0.2rem;
  }

  .admin-view__nav-divider {
    width: 100%;
    padding: 0.25rem 0.4rem;
  }

  .admin-view__nav-divider-label {
    font-size: 0.55rem;
  }

  .admin-view__nav-item {
    padding: 0.35rem 0.55rem;
    font-size: 0.7rem;

    &::before {
      display: none;
    }
  }

  .admin-view__nav-label {
    display: none;
  }

  .admin-view__sidebar-footer {
    display: none;
  }

  .admin-view__stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .admin-view__system-info {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .admin-view__header {
    padding: 0.5rem 0.75rem;
  }

  .admin-view__header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .admin-view__stats {
    grid-template-columns: 1fr;
  }

  .admin-view__quick-access {
    grid-template-columns: 1fr;
  }

  .admin-view__footer {
    padding: 0.5rem 0.75rem;
    flex-direction: column;
    align-items: flex-start;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .admin-view {
    background: var(--color-bg-primary, #f4f6fa);
    color: var(--color-text-primary, #1a1a2e);
  }

  .admin-view__header {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-view__title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .admin-view__sidebar {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-view__nav-item {
    color: var(--color-text-secondary, #3d4a5c);

    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
      color: var(--color-text-primary, #1a1a2e);
    }

    &--active {
      background: rgba(0, 102, 204, 0.1);
      border-color: var(--color-primary, #0066cc);
      color: var(--color-primary, #0066cc);
    }
  }

  .admin-view__nav-divider-label {
    color: var(--color-text-muted, #7a8a9a);
  }

  .admin-view__sidebar-footer {
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-view__welcome {
    background: linear-gradient(135deg, rgba(0, 102, 204, 0.08), rgba(0, 68, 179, 0.05));
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-view__welcome-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .admin-view__stat-card,
  .admin-view__quick-card,
  .admin-view__system-info,
  .admin-view__activity {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-view__stat-value,
  .admin-view__quick-title,
  .admin-view__section-title,
  .admin-view__system-info-value {
    color: var(--color-text-primary, #1a1a2e);
  }

  .admin-view__system-info-item,
  .admin-view__activity-item {
    background: var(--color-bg-secondary, #e9ecf2);
  }

  .admin-view__activity-text {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .admin-view__footer {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0e0e0);
  }

  .admin-view__btn {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }
}
</style>
