<!-- ==========================================================================
  NexusDL 2.0 - Admin Providers View (version complète)
  Fichier : frontend/src/views/admin/ProvidersView.vue
  Description : Console d'administration pour gérer les providers de scan
                (sites supportés par NexusDL) : activation, désactivation,
                filtres, statistiques, recherche et actions groupées.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="admin-providers">
    <!-- ====================================================================
      EN-TÊTE — Titre, actions, statistiques
    ==================================================================== -->
    <header class="admin-providers__header">
      <div class="admin-providers__header-left">
        <h1 class="admin-providers__title">
          <span aria-hidden="true">🌐</span>
          Providers
        </h1>
        <p class="admin-providers__subtitle">
          Gérez les sites de scan activés pour NexusDL
        </p>
      </div>

      <div class="admin-providers__header-right">
        <!-- Recherche -->
        <div class="admin-providers__search-wrapper">
          <span class="admin-providers__search-icon" aria-hidden="true">🔍</span>
          <input
            ref="searchInputRef"
            type="text"
            class="admin-providers__search-input"
            v-model="searchQuery"
            placeholder="Rechercher un provider..."
            aria-label="Rechercher un provider"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="admin-providers__search-clear"
            @click="clearSearch"
            aria-label="Effacer la recherche"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <!-- Toggle vue grille/liste -->
        <div class="admin-providers__view-toggle">
          <button
            type="button"
            class="admin-providers__view-btn"
            :class="{ 'admin-providers__view-btn--active': viewMode === 'grid' }"
            @click="setViewMode('grid')"
            aria-label="Vue en grille"
            title="Vue en grille"
          >
            <span aria-hidden="true">⊞</span>
          </button>
          <button
            type="button"
            class="admin-providers__view-btn"
            :class="{ 'admin-providers__view-btn--active': viewMode === 'list' }"
            @click="setViewMode('list')"
            aria-label="Vue en liste"
            title="Vue en liste"
          >
            <span aria-hidden="true">☰</span>
          </button>
        </div>

        <!-- Rafraîchir -->
        <button
          type="button"
          class="admin-providers__btn admin-providers__btn--refresh"
          :disabled="loading"
          @click="refreshProviders"
          aria-label="Rafraîchir la liste"
          title="Rafraîchir"
        >
          <span v-if="loading" class="admin-providers__spinner" aria-hidden="true">⟳</span>
          <span v-else aria-hidden="true">↻</span>
          Rafraîchir
        </button>

        <!-- Tout activer -->
        <button
          type="button"
          class="admin-providers__btn admin-providers__btn--success"
          :disabled="loading || filteredProviders.length === 0"
          @click="enableAllFiltered"
          aria-label="Activer tous les providers filtrés"
          title="Activer tous les providers affichés"
        >
          <span aria-hidden="true">✅</span>
          Tout activer
        </button>

        <!-- Tout désactiver -->
        <button
          type="button"
          class="admin-providers__btn admin-providers__btn--danger"
          :disabled="loading || filteredProviders.length === 0"
          @click="disableAllFiltered"
          aria-label="Désactiver tous les providers filtrés"
          title="Désactiver tous les providers affichés"
        >
          <span aria-hidden="true">⛔</span>
          Tout désactiver
        </button>
      </div>
    </header>

    <!-- ====================================================================
      BARRE DE STATISTIQUES
    ==================================================================== -->
    <div class="admin-providers__stats">
      <div class="admin-providers__stat">
        <span class="admin-providers__stat-value">{{ totalProviders }}</span>
        <span class="admin-providers__stat-label">Total</span>
      </div>
      <div class="admin-providers__stat admin-providers__stat--enabled">
        <span class="admin-providers__stat-value">{{ statsCount.enabled }}</span>
        <span class="admin-providers__stat-label">Activés</span>
      </div>
      <div class="admin-providers__stat admin-providers__stat--disabled">
        <span class="admin-providers__stat-value">{{ statsCount.disabled }}</span>
        <span class="admin-providers__stat-label">Désactivés</span>
      </div>
      <div class="admin-providers__stat admin-providers__stat--nsfw">
        <span class="admin-providers__stat-value">{{ statsCount.nsfw }}</span>
        <span class="admin-providers__stat-label">NSFW</span>
      </div>
      <div class="admin-providers__stat admin-providers__stat--french">
        <span class="admin-providers__stat-value">{{ statsCount.french }}</span>
        <span class="admin-providers__stat-label">Français</span>
      </div>
      <div class="admin-providers__stat admin-providers__stat--english">
        <span class="admin-providers__stat-value">{{ statsCount.english }}</span>
        <span class="admin-providers__stat-label">Anglais</span>
      </div>
      <div class="admin-providers__stat admin-providers__stat--filtered">
        <span class="admin-providers__stat-value">{{ filteredProviders.length }}</span>
        <span class="admin-providers__stat-label">Affichés</span>
      </div>
    </div>

    <!-- ====================================================================
      FILTRES
    ==================================================================== -->
    <div class="admin-providers__filters">
      <!-- Filtres par statut -->
      <div class="admin-providers__filter-group">
        <span class="admin-providers__filter-label">Statut :</span>
        <button
          v-for="filter in statusFilters"
          :key="filter.value"
          type="button"
          class="admin-providers__filter-btn"
          :class="{ 'admin-providers__filter-btn--active': statusFilter === filter.value }"
          @click="statusFilter = filter.value"
          :aria-pressed="statusFilter === filter.value"
        >
          <span aria-hidden="true">{{ filter.icon }}</span>
          {{ filter.label }}
        </button>
      </div>

      <!-- Filtres par langue -->
      <div class="admin-providers__filter-group">
        <span class="admin-providers__filter-label">Langue :</span>
        <button
          v-for="lang in languageFilters"
          :key="lang.value"
          type="button"
          class="admin-providers__filter-btn"
          :class="{ 'admin-providers__filter-btn--active': languageFilter === lang.value }"
          @click="languageFilter = lang.value"
          :aria-pressed="languageFilter === lang.value"
        >
          <span aria-hidden="true">{{ lang.icon }}</span>
          {{ lang.label }}
        </button>
      </div>

      <!-- Tri -->
      <div class="admin-providers__filter-group admin-providers__filter-group--right">
        <span class="admin-providers__filter-label">Trier :</span>
        <select
          v-model="sortBy"
          class="admin-providers__sort-select"
          aria-label="Trier les providers"
        >
          <option value="name">Nom (A-Z)</option>
          <option value="name-desc">Nom (Z-A)</option>
          <option value="priority">Priorité (élevée → basse)</option>
          <option value="priority-asc">Priorité (basse → élevée)</option>
          <option value="enabled">Activés en premier</option>
          <option value="disabled">Désactivés en premier</option>
        </select>
      </div>
    </div>

    <!-- ====================================================================
      LISTE / GRILLE DES PROVIDERS
    ==================================================================== -->
    <div class="admin-providers__body">
      <!-- État de chargement -->
      <div v-if="loading && providers.length === 0" class="admin-providers__loading">
        <NexusSpinner size="lg" label="Chargement des providers..." />
      </div>

      <!-- État vide -->
      <div v-else-if="filteredProviders.length === 0" class="admin-providers__empty">
        <span class="admin-providers__empty-icon" aria-hidden="true">📭</span>
        <p class="admin-providers__empty-text">
          {{ providers.length === 0 ? 'Aucun provider disponible' : 'Aucun provider ne correspond à vos filtres' }}
        </p>
        <button
          v-if="providers.length > 0"
          type="button"
          class="admin-providers__empty-reset"
          @click="resetFilters"
        >
          Réinitialiser les filtres
        </button>
      </div>

      <!-- Vue grille -->
      <div
        v-else-if="viewMode === 'grid'"
        class="admin-providers__grid"
      >
        <div
          v-for="provider in filteredProviders"
          :key="provider.id"
          class="admin-providers__card"
          :class="[
            `admin-providers__card--${provider.nsfw ? 'nsfw' : 'sfw'}`,
            { 'admin-providers__card--disabled': !provider.enabled },
          ]"
        >
          <!-- En-tête de la carte -->
          <div class="admin-providers__card-header">
            <div class="admin-providers__card-title-wrapper">
              <h3 class="admin-providers__card-title" :title="provider.name">
                {{ provider.name }}
              </h3>
              <div class="admin-providers__card-badges">
                <span
                  v-if="provider.nsfw"
                  class="admin-providers__badge admin-providers__badge--nsfw"
                  title="Contenu pour adultes"
                >
                  🔞 NSFW
                </span>
                <span
                  v-for="lang in provider.languages"
                  :key="lang"
                  class="admin-providers__badge admin-providers__badge--lang"
                >
                  {{ getLanguageFlag(lang) }} {{ lang.toUpperCase() }}
                </span>
              </div>
            </div>

            <!-- Toggle activation -->
            <label
              class="admin-providers__toggle"
              :title="provider.enabled ? 'Désactiver' : 'Activer'"
            >
              <input
                type="checkbox"
                :checked="provider.enabled"
                @change="toggleProvider(provider, $event.target.checked)"
                :aria-label="`${provider.enabled ? 'Désactiver' : 'Activer'} ${provider.name}`"
              />
              <span class="admin-providers__toggle-slider" />
            </label>
          </div>

          <!-- Corps de la carte -->
          <div class="admin-providers__card-body">
            <div class="admin-providers__card-row">
              <span class="admin-providers__card-label">URL :</span>
              <a
                :href="provider.base_url"
                target="_blank"
                rel="noopener noreferrer"
                class="admin-providers__card-url"
                :title="provider.base_url"
              >
                {{ truncateUrl(provider.base_url) }}
              </a>
            </div>

            <div v-if="provider.description" class="admin-providers__card-row">
              <span class="admin-providers__card-label">Description :</span>
              <span class="admin-providers__card-description" :title="provider.description">
                {{ truncate(provider.description, 80) }}
              </span>
            </div>

            <div class="admin-providers__card-row">
              <span class="admin-providers__card-label">Version :</span>
              <span class="admin-providers__card-value">v{{ provider.version || '1.0.0' }}</span>
            </div>

            <div class="admin-providers__card-row">
              <span class="admin-providers__card-label">Priorité :</span>
              <span class="admin-providers__card-value">
                <span class="admin-providers__priority">
                  <span
                    v-for="i in 10"
                    :key="i"
                    class="admin-providers__priority-dot"
                    :class="{ 'admin-providers__priority-dot--filled': i <= (provider.priority || 0) }"
                  />
                </span>
                {{ provider.priority || 0 }}/10
              </span>
            </div>

            <div v-if="provider.last_used" class="admin-providers__card-row">
              <span class="admin-providers__card-label">Dernière utilisation :</span>
              <span class="admin-providers__card-value">
                {{ formatRelativeTime(provider.last_used) }}
              </span>
            </div>
          </div>

          <!-- Actions de la carte -->
          <div class="admin-providers__card-actions">
            <button
              type="button"
              class="admin-providers__card-action"
              @click="openProvider(provider)"
              title="Ouvrir le site"
              aria-label="Ouvrir le site"
            >
              <span aria-hidden="true">🔗</span>
            </button>
            <button
              type="button"
              class="admin-providers__card-action"
              @click="testProvider(provider)"
              title="Tester le provider"
              aria-label="Tester le provider"
            >
              <span aria-hidden="true">🧪</span>
            </button>
            <button
              type="button"
              class="admin-providers__card-action"
              @click="copyProviderInfo(provider)"
              title="Copier les informations"
              aria-label="Copier les informations"
            >
              <span aria-hidden="true">📄</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Vue liste -->
      <div v-else class="admin-providers__list">
        <table class="admin-providers__table">
          <thead>
            <tr>
              <th class="admin-providers__th admin-providers__th--toggle">Actif</th>
              <th class="admin-providers__th">Nom</th>
              <th class="admin-providers__th">URL</th>
              <th class="admin-providers__th admin-providers__th--center">Langues</th>
              <th class="admin-providers__th admin-providers__th--center">NSFW</th>
              <th class="admin-providers__th admin-providers__th--center">Version</th>
              <th class="admin-providers__th admin-providers__th--center">Priorité</th>
              <th class="admin-providers__th admin-providers__th--actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="provider in filteredProviders"
              :key="provider.id"
              class="admin-providers__tr"
              :class="{ 'admin-providers__tr--disabled': !provider.enabled }"
            >
              <td class="admin-providers__td admin-providers__td--toggle">
                <label
                  class="admin-providers__toggle admin-providers__toggle--sm"
                  :title="provider.enabled ? 'Désactiver' : 'Activer'"
                >
                  <input
                    type="checkbox"
                    :checked="provider.enabled"
                    @change="toggleProvider(provider, $event.target.checked)"
                  />
                  <span class="admin-providers__toggle-slider" />
                </label>
              </td>
              <td class="admin-providers__td">
                <span class="admin-providers__list-name" :title="provider.name">
                  {{ provider.name }}
                </span>
              </td>
              <td class="admin-providers__td">
                <a
                  :href="provider.base_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="admin-providers__list-url"
                  :title="provider.base_url"
                >
                  {{ truncateUrl(provider.base_url) }}
                </a>
              </td>
              <td class="admin-providers__td admin-providers__td--center">
                <span
                  v-for="lang in provider.languages"
                  :key="lang"
                  class="admin-providers__badge admin-providers__badge--lang admin-providers__badge--sm"
                >
                  {{ getLanguageFlag(lang) }}
                </span>
              </td>
              <td class="admin-providers__td admin-providers__td--center">
                <span v-if="provider.nsfw" class="admin-providers__badge admin-providers__badge--nsfw admin-providers__badge--sm">
                  🔞
                </span>
                <span v-else class="admin-providers__text-muted">—</span>
              </td>
              <td class="admin-providers__td admin-providers__td--center">
                <span class="admin-providers__text-muted">v{{ provider.version || '1.0.0' }}</span>
              </td>
              <td class="admin-providers__td admin-providers__td--center">
                <span class="admin-providers__priority admin-providers__priority--sm">
                  <span
                    v-for="i in 5"
                    :key="i"
                    class="admin-providers__priority-dot"
                    :class="{ 'admin-providers__priority-dot--filled': i <= ((provider.priority || 0) / 2) }"
                  />
                </span>
              </td>
              <td class="admin-providers__td admin-providers__td--actions">
                <button
                  type="button"
                  class="admin-providers__list-action"
                  @click="openProvider(provider)"
                  title="Ouvrir"
                  aria-label="Ouvrir"
                >
                  <span aria-hidden="true">🔗</span>
                </button>
                <button
                  type="button"
                  class="admin-providers__list-action"
                  @click="testProvider(provider)"
                  title="Tester"
                  aria-label="Tester"
                >
                  <span aria-hidden="true">🧪</span>
                </button>
                <button
                  type="button"
                  class="admin-providers__list-action"
                  @click="copyProviderInfo(provider)"
                  title="Copier"
                  aria-label="Copier"
                >
                  <span aria-hidden="true">📄</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ====================================================================
      PIED DE PAGE
    ==================================================================== -->
    <footer class="admin-providers__footer">
      <span class="admin-providers__footer-info">
        {{ filteredProviders.length }} / {{ providers.length }} providers affichés
        <span v-if="searchQuery" class="admin-providers__footer-highlight">
          · recherche : "{{ searchQuery }}"
        </span>
        <span v-if="statusFilter !== 'all'" class="admin-providers__footer-highlight">
          · statut : {{ statusFilter }}
        </span>
        <span v-if="languageFilter !== 'all'" class="admin-providers__footer-highlight">
          · langue : {{ languageFilter }}
        </span>
      </span>
      <span v-if="lastUpdated" class="admin-providers__footer-updated">
        Dernière mise à jour : {{ formatTimestamp(lastUpdated) }}
      </span>
    </footer>

    <!-- ====================================================================
      MODALE DE CONFIRMATION POUR ACTIONS GROUPÉES
    ==================================================================== -->
    <NexusModal
      v-model="showConfirmModal"
      :title="confirmModalTitle"
      size="sm"
      confirmable
      :confirm-text="confirmModalConfirmText"
      :cancel-text="'Annuler'"
      :confirm-variant="confirmModalVariant"
      :loading="actionLoading"
      @confirm="executeConfirmedAction"
      @cancel="cancelConfirmedAction"
    >
      <p>{{ confirmModalMessage }}</p>
    </NexusModal>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useProvidersStore } from '@/stores/providers'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusModal from '@/components/common/NexusModal.vue'
import { truncate, formatRelativeTime } from '@/utils/formatters'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const api = useApi()
const toast = useToast()
const providersStore = useProvidersStore()

// ==========================================================================
//  État réactif
// ==========================================================================

const providers = ref([])
const loading = ref(false)
const actionLoading = ref(false)
const lastUpdated = ref(null)
const searchQuery = ref('')
const statusFilter = ref('all')
const languageFilter = ref('all')
const sortBy = ref('priority')
const viewMode = ref('grid')
const searchInputRef = ref(null)

// Modale de confirmation
const showConfirmModal = ref(false)
const confirmModalTitle = ref('')
const confirmModalMessage = ref('')
const confirmModalConfirmText = ref('Confirmer')
const confirmModalVariant = ref('primary')
let pendingAction = null

let searchTimeout = null

// ==========================================================================
//  Options
// ==========================================================================

const statusFilters = [
  { value: 'all', label: 'Tous', icon: '📋' },
  { value: 'enabled', label: 'Activés', icon: '✅' },
  { value: 'disabled', label: 'Désactivés', icon: '⛔' },
  { value: 'nsfw', label: 'NSFW', icon: '🔞' },
  { value: 'sfw', label: 'SFW', icon: '🌿' },
]

const languageFilters = [
  { value: 'all', label: 'Toutes', icon: '🌍' },
  { value: 'fr', label: 'Français', icon: '🇫🇷' },
  { value: 'en', label: 'Anglais', icon: '🇬🇧' },
]

// ==========================================================================
//  Computed
// ==========================================================================

/**
 * Nombre total de providers.
 */
const totalProviders = computed(() => providers.value.length)

/**
 * Statistiques.
 */
const statsCount = computed(() => {
  const counts = {
    enabled: 0,
    disabled: 0,
    nsfw: 0,
    french: 0,
    english: 0,
  }
  for (const p of providers.value) {
    if (p.enabled) counts.enabled++
    else counts.disabled++

    if (p.nsfw) counts.nsfw++

    const langs = Array.isArray(p.languages) ? p.languages : []
    if (langs.includes('fr')) counts.french++
    if (langs.includes('en')) counts.english++
  }
  return counts
})

/**
 * Providers filtrés et triés.
 */
const filteredProviders = computed(() => {
  let result = [...providers.value]

  // Filtre statut
  if (statusFilter.value === 'enabled') {
    result = result.filter((p) => p.enabled)
  } else if (statusFilter.value === 'disabled') {
    result = result.filter((p) => !p.enabled)
  } else if (statusFilter.value === 'nsfw') {
    result = result.filter((p) => p.nsfw)
  } else if (statusFilter.value === 'sfw') {
    result = result.filter((p) => !p.nsfw)
  }

  // Filtre langue
  if (languageFilter.value !== 'all') {
    result = result.filter((p) => {
      const langs = Array.isArray(p.languages) ? p.languages : []
      return langs.includes(languageFilter.value)
    })
  }

  // Recherche
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter((p) => {
      const name = (p.name || '').toLowerCase()
      const id = (p.id || '').toLowerCase()
      const url = (p.base_url || '').toLowerCase()
      const desc = (p.description || '').toLowerCase()
      return (
        name.includes(q) ||
        id.includes(q) ||
        url.includes(q) ||
        desc.includes(q)
      )
    })
  }

  // Tri
  const [sortField, sortOrder] = sortBy.value.split('-')
  result.sort((a, b) => {
    switch (sortField) {
      case 'name': {
        const cmp = (a.name || '').localeCompare(b.name || '')
        return sortOrder === 'desc' ? -cmp : cmp
      }
      case 'priority': {
        const cmp = (b.priority || 0) - (a.priority || 0)
        return sortOrder === 'asc' ? -cmp : cmp
      }
      case 'enabled': {
        return (b.enabled ? 1 : 0) - (a.enabled ? 1 : 0)
      }
      case 'disabled': {
        return (a.enabled ? 1 : 0) - (b.enabled ? 1 : 0)
      }
      default:
        return 0
    }
  })

  return result
})

// ==========================================================================
//  Méthodes — Récupération
// ==========================================================================

/**
 * Récupère la liste des providers depuis l'API.
 */
async function fetchProviders() {
  loading.value = true
  try {
    // Récupérer depuis l'API admin (tous les providers, même désactivés)
    const response = await api.get('/admin/providers', {
      params: { include_disabled: true },
    })

    // Normaliser la réponse
    let rawProviders = []
    if (Array.isArray(response)) {
      rawProviders = response
    } else if (Array.isArray(response?.providers)) {
      rawProviders = response.providers
    } else if (Array.isArray(response?.items)) {
      rawProviders = response.items
    }

    providers.value = rawProviders.map((p) => normalizeProvider(p))
    lastUpdated.value = new Date().toISOString()
  } catch (err) {
    console.error('Erreur chargement providers:', err)
    toast.error(`Impossible de charger les providers: ${err.message}`, '❌')
  } finally {
    loading.value = false
  }
}

/**
 * Rafraîchit la liste.
 */
async function refreshProviders() {
  toast.info('Rafraîchissement des providers...', '🔄', 1500)
  await fetchProviders()
}

/**
 * Normalise un provider.
 * @param {Object} raw
 * @returns {Object}
 */
function normalizeProvider(raw) {
  return {
    id: raw.id || raw.provider_id || '',
    provider_id: raw.provider_id || raw.id || '',
    name: raw.name || 'Sans nom',
    base_url: raw.base_url || '',
    enabled: raw.enabled !== undefined ? raw.enabled : true,
    nsfw: raw.nsfw || false,
    languages: Array.isArray(raw.languages)
      ? raw.languages
      : raw.supported_languages || [],
    version: raw.version || '1.0.0',
    description: raw.description || '',
    priority: raw.priority || 0,
    last_used: raw.last_used || null,
    created_at: raw.created_at || null,
    updated_at: raw.updated_at || null,
  }
}

// ==========================================================================
//  Méthodes — Actions sur les providers
// ==========================================================================

/**
 * Active ou désactive un provider.
 * @param {Object} provider
 * @param {boolean} enabled
 */
async function toggleProvider(provider, enabled) {
  if (!provider || provider.enabled === enabled) return

  // Mise à jour optimiste
  const previousState = provider.enabled
  provider.enabled = enabled

  try {
    await api.patch(`/admin/providers/${provider.id}`, { enabled })

    toast.success(
      `Provider "${provider.name}" ${enabled ? 'activé' : 'désactivé'}`,
      enabled ? '✅' : '⛔'
    )

    // Synchroniser avec le store global
    if (providersStore && typeof providersStore.updateProviderFromWs === 'function') {
      providersStore.updateProviderFromWs({ ...provider, enabled })
    }
  } catch (err) {
    // Rollback
    provider.enabled = previousState
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

/**
 * Ouvre le site du provider dans un nouvel onglet.
 * @param {Object} provider
 */
function openProvider(provider) {
  if (provider.base_url) {
    window.open(provider.base_url, '_blank', 'noopener,noreferrer')
  }
}

/**
 * Teste le provider en essayant d'analyser une URL fictive.
 * @param {Object} provider
 */
async function testProvider(provider) {
  loading.value = true
  toast.info(`Test du provider "${provider.name}"...`, '🧪', 2000)
  try {
    const response = await api.post('/browse/analyze', {
      url: provider.base_url,
      provider_id: provider.id,
    })
    toast.success(`Provider "${provider.name}" opérationnel !`, '✅')
    return response
  } catch (err) {
    toast.error(`Provider "${provider.name}" en erreur : ${err.message}`, '❌')
  } finally {
    loading.value = false
  }
}

/**
 * Copie les informations d'un provider.
 * @param {Object} provider
 */
async function copyProviderInfo(provider) {
  const info = [
    `Nom       : ${provider.name}`,
    `ID        : ${provider.id}`,
    `URL       : ${provider.base_url}`,
    `Langues   : ${provider.languages.join(', ')}`,
    `NSFW      : ${provider.nsfw ? 'oui' : 'non'}`,
    `Version   : ${provider.version}`,
    `Priorité  : ${provider.priority}`,
    `Activé    : ${provider.enabled ? 'oui' : 'non'}`,
  ].join('\n')

  try {
    await navigator.clipboard.writeText(info)
    toast.success('Informations copiées', '📄')
  } catch (err) {
    toast.error('Impossible de copier', '❌')
  }
}

// ==========================================================================
//  Méthodes — Actions groupées
// ==========================================================================

/**
 * Active tous les providers filtrés.
 */
function enableAllFiltered() {
  const targets = filteredProviders.value.filter((p) => !p.enabled)
  if (targets.length === 0) {
    toast.info('Aucun provider à activer', 'ℹ️')
    return
  }

  confirmModalTitle.value = 'Activer des providers'
  confirmModalMessage.value = `Activer ${targets.length} provider(s) ?`
  confirmModalConfirmText.value = 'Activer'
  confirmModalVariant.value = 'success'
  pendingAction = async () => {
    for (const p of targets) {
      await toggleProvider(p, true)
    }
    toast.success(`${targets.length} provider(s) activé(s)`, '✅')
  }
  showConfirmModal.value = true
}

/**
 * Désactive tous les providers filtrés.
 */
function disableAllFiltered() {
  const targets = filteredProviders.value.filter((p) => p.enabled)
  if (targets.length === 0) {
    toast.info('Aucun provider à désactiver', 'ℹ️')
    return
  }

  confirmModalTitle.value = 'Désactiver des providers'
  confirmModalMessage.value = `Désactiver ${targets.length} provider(s) ?`
  confirmModalConfirmText.value = 'Désactiver'
  confirmModalVariant.value = 'error'
  pendingAction = async () => {
    for (const p of targets) {
      await toggleProvider(p, false)
    }
    toast.success(`${targets.length} provider(s) désactivé(s)`, '⛔')
  }
  showConfirmModal.value = true
}

/**
 * Exécute l'action confirmée.
 */
async function executeConfirmedAction() {
  if (!pendingAction) return
  actionLoading.value = true
  try {
    await pendingAction()
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    actionLoading.value = false
    pendingAction = null
    showConfirmModal.value = false
  }
}

/**
 * Annule l'action en attente.
 */
function cancelConfirmedAction() {
  pendingAction = null
  showConfirmModal.value = false
}

// ==========================================================================
//  Méthodes — Filtres
// ==========================================================================

/**
 * Efface la recherche.
 */
function clearSearch() {
  searchQuery.value = ''
  searchInputRef.value?.focus()
}

/**
 * Réinitialise tous les filtres.
 */
function resetFilters() {
  searchQuery.value = ''
  statusFilter.value = 'all'
  languageFilter.value = 'all'
  sortBy.value = 'priority'
}

/**
 * Change le mode d'affichage.
 * @param {string} mode
 */
function setViewMode(mode) {
  viewMode.value = mode
  try {
    localStorage.setItem('nexus-providers-view', mode)
  } catch (_) {
    // Ignorer
  }
}

// ==========================================================================
//  Méthodes — Formatage
// ==========================================================================

/**
 * Retourne l'emoji du drapeau pour une langue.
 * @param {string} lang
 * @returns {string}
 */
function getLanguageFlag(lang) {
  const flags = {
    fr: '🇫🇷',
    en: '🇬🇧',
    es: '🇪🇸',
    pt: '🇵🇹',
    de: '🇩🇪',
    it: '🇮🇹',
    ja: '🇯🇵',
    ko: '🇰🇷',
    zh: '🇨🇳',
    ru: '🇷🇺',
  }
  return flags[lang] || '🌐'
}

/**
 * Tronque une URL pour l'affichage.
 * @param {string} url
 * @returns {string}
 */
function truncateUrl(url) {
  if (!url) return ''
  return url.replace(/^https?:\/\//, '').replace(/\/$/, '')
}

/**
 * Formate un timestamp.
 * @param {string} timestamp
 * @returns {string}
 */
function formatTimestamp(timestamp) {
  if (!timestamp) return ''
  try {
    const d = dayjs(timestamp)
    if (!d.isValid()) return timestamp
    return d.format('DD/MM/YYYY HH:mm:ss')
  } catch (_) {
    return timestamp
  }
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  // Charger le mode d'affichage préféré
  try {
    const savedView = localStorage.getItem('nexus-providers-view')
    if (savedView === 'grid' || savedView === 'list') {
      viewMode.value = savedView
    }
  } catch (_) {
    // Ignorer
  }

  await fetchProviders()
})

onUnmounted(() => {
  clearTimeout(searchTimeout)
})

// ==========================================================================
//  Debounce de la recherche (optionnel)
// ==========================================================================

function onSearchInput() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    // Rien de spécial, le computed gère le filtrage
  }, 150)
}
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.admin-providers {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

// ==========================================================================
//  Header
// ==========================================================================

.admin-providers__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.admin-providers__header-left {
  flex: 1;
  min-width: 200px;
}

.admin-providers__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.admin-providers__subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.admin-providers__header-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

// ==========================================================================
//  Recherche
// ==========================================================================

.admin-providers__search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 200px;
}

.admin-providers__search-icon {
  position: absolute;
  left: 0.5rem;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
}

.admin-providers__search-input {
  width: 100%;
  padding: 0.4rem 0.5rem 0.4rem 1.9rem;
  font-size: 0.8rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15);
  }

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.admin-providers__search-clear {
  position: absolute;
  right: 0.3rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0 0.3rem;
  &:hover {
    color: var(--color-text-primary, #e8edf5);
  }
}

// ==========================================================================
//  Boutons
// ==========================================================================

.admin-providers__btn {
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

  &--success:hover:not(:disabled) {
    border-color: var(--color-success, #4caf50);
    color: var(--color-success, #4caf50);
  }

  &--danger:hover:not(:disabled) {
    border-color: var(--color-error, #f44336);
    color: var(--color-error, #f44336);
  }
}

.admin-providers__spinner {
  display: inline-block;
  animation: adminProvidersSpin 0.8s linear infinite;
}

@keyframes adminProvidersSpin {
  to {
    transform: rotate(360deg);
  }
}

// ==========================================================================
//  View toggle
// ==========================================================================

.admin-providers__view-toggle {
  display: flex;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
}

.admin-providers__view-btn {
  padding: 0.35rem 0.55rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &--active {
    background: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
  }
}

// ==========================================================================
//  Statistiques
// ==========================================================================

.admin-providers__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.admin-providers__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.3rem 0.7rem;
  border-radius: var(--radius-sm, 4px);
  background: var(--color-bg-card, #1a2538);
  min-width: 60px;

  &--enabled { border-left: 3px solid #4caf50; }
  &--disabled { border-left: 3px solid #6a7a9a; }
  &--nsfw { border-left: 3px solid #f44336; }
  &--french { border-left: 3px solid #2196f3; }
  &--english { border-left: 3px solid #ff9800; }
  &--filtered { border-left: 3px solid var(--color-primary, #00d4ff); }
}

.admin-providers__stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  font-variant-numeric: tabular-nums;
}

.admin-providers__stat-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  color: var(--color-text-muted, #6a7a9a);
  letter-spacing: 0.05em;
}

// ==========================================================================
//  Filtres
// ==========================================================================

.admin-providers__filters {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.admin-providers__filter-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;

  &--right {
    margin-left: auto;
  }
}

.admin-providers__filter-label {
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
  font-weight: 500;
  margin-right: 0.25rem;
}

.admin-providers__filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.25rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--color-bg-card, #1a2538);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }

  &--active {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
  }
}

.admin-providers__sort-select {
  padding: 0.3rem 0.6rem;
  font-size: 0.75rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  outline: none;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
  }
}

// ==========================================================================
//  Body
// ==========================================================================

.admin-providers__body {
  flex: 1;
  min-height: 300px;
}

// ==========================================================================
//  Vue grille
// ==========================================================================

.admin-providers__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 0.75rem;
}

.admin-providers__card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;

  &:hover {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  &--disabled {
    opacity: 0.6;
    &:hover {
      opacity: 0.8;
    }
  }

  &--nsfw {
    border-left: 3px solid #f44336;
  }

  &--sfw {
    border-left: 3px solid #4caf50;
  }
}

.admin-providers__card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.admin-providers__card-title-wrapper {
  flex: 1;
  min-width: 0;
}

.admin-providers__card-title {
  margin: 0 0 0.25rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.admin-providers__card-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem;
}

.admin-providers__badge {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
  padding: 0.1rem 0.35rem;
  font-size: 0.6rem;
  font-weight: 600;
  border-radius: var(--radius-sm, 4px);
  white-space: nowrap;

  &--nsfw {
    background: rgba(244, 67, 54, 0.15);
    color: #e57373;
    border: 1px solid rgba(244, 67, 54, 0.3);
  }

  &--lang {
    background: var(--color-bg-secondary, #141a2b);
    color: var(--color-text-secondary, #b0c0d8);
    border: 1px solid var(--color-border, #1a2538);
  }

  &--sm {
    padding: 0.05rem 0.25rem;
    font-size: 0.55rem;
  }
}

// ==========================================================================
//  Toggle (switch)
// ==========================================================================

.admin-providers__toggle {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
  flex-shrink: 0;

  input {
    opacity: 0;
    width: 0;
    height: 0;

    &:checked + .admin-providers__toggle-slider {
      background: var(--color-success, #4caf50);
      &::before {
        transform: translateX(18px);
      }
    }

    &:focus-visible + .admin-providers__toggle-slider {
      box-shadow: 0 0 0 2px var(--color-primary, #00d4ff);
    }
  }

  &--sm {
    width: 32px;
    height: 18px;
    input:checked + .admin-providers__toggle-slider::before {
      transform: translateX(14px);
    }
    .admin-providers__toggle-slider::before {
      width: 14px;
      height: 14px;
    }
  }
}

.admin-providers__toggle-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: var(--color-bg-input, #1e2a40);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-full, 9999px);
  transition: background 0.2s ease;

  &::before {
    content: '';
    position: absolute;
    height: 16px;
    width: 16px;
    left: 2px;
    top: 50%;
    transform: translateY(-50%);
    background: var(--color-text-muted, #6a7a9a);
    border-radius: 50%;
    transition: transform 0.2s ease, background 0.2s ease;
  }

  input:checked + & {
    background: var(--color-success, #4caf50);
    border-color: var(--color-success, #4caf50);
    &::before {
      background: #ffffff;
    }
  }
}

// ==========================================================================
//  Card body
// ==========================================================================

.admin-providers__card-body {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.75rem;
}

.admin-providers__card-row {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
  line-height: 1.4;
}

.admin-providers__card-label {
  flex-shrink: 0;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.7rem;
}

.admin-providers__card-value,
.admin-providers__card-description {
  color: var(--color-text-secondary, #b0c0d8);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-providers__card-url {
  color: var(--color-primary, #00d4ff);
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.7rem;

  &:hover {
    text-decoration: underline;
  }
}

.admin-providers__priority {
  display: inline-flex;
  gap: 1px;
  align-items: center;
  margin-right: 0.2rem;
}

.admin-providers__priority-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);

  &--filled {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);
  }

  .admin-providers__priority--sm & {
    width: 4px;
    height: 4px;
  }
}

// ==========================================================================
//  Card actions
// ==========================================================================

.admin-providers__card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.2rem;
  padding-top: 0.4rem;
  border-top: 1px solid var(--color-border, #1a2538);
}

.admin-providers__card-action {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.2rem 0.35rem;
  border-radius: var(--radius-sm, 4px);
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
}

// ==========================================================================
//  Vue liste (table)
// ==========================================================================

.admin-providers__list {
  overflow-x: auto;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
}

.admin-providers__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.admin-providers__th {
  padding: 0.6rem 0.75rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #6a7a9a);
  border-bottom: 1px solid var(--color-border, #1a2538);
  background: var(--color-bg-secondary, #141a2b);
  white-space: nowrap;

  &--center { text-align: center; }
  &--toggle { width: 60px; text-align: center; }
  &--actions { width: 120px; text-align: right; }
}

.admin-providers__tr {
  transition: background 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }

  &--disabled {
    opacity: 0.6;
  }

  &:last-child .admin-providers__td {
    border-bottom: none;
  }
}

.admin-providers__td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
  color: var(--color-text-secondary, #b0c0d8);
  vertical-align: middle;

  &--center { text-align: center; }
  &--toggle { text-align: center; }
  &--actions { text-align: right; white-space: nowrap; }
}

.admin-providers__list-name {
  font-weight: 500;
  color: var(--color-text-primary, #e8edf5);
}

.admin-providers__list-url {
  color: var(--color-primary, #00d4ff);
  text-decoration: none;
  font-size: 0.75rem;

  &:hover {
    text-decoration: underline;
  }
}

.admin-providers__list-action {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.2rem 0.35rem;
  border-radius: var(--radius-sm, 4px);
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
}

.admin-providers__text-muted {
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.75rem;
}

// ==========================================================================
//  États
// ==========================================================================

.admin-providers__loading,
.admin-providers__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: var(--color-text-muted, #6a7a9a);
  text-align: center;
  gap: 0.5rem;
  min-height: 250px;
}

.admin-providers__empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.admin-providers__empty-text {
  margin: 0;
  font-size: 0.95rem;
}

.admin-providers__empty-reset {
  margin-top: 0.5rem;
  padding: 0.3rem 0.8rem;
  font-size: 0.75rem;
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
  border: none;
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  font-weight: 500;

  &:hover {
    filter: brightness(1.1);
  }
}

// ==========================================================================
//  Footer
// ==========================================================================

.admin-providers__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.admin-providers__footer-info {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.admin-providers__footer-highlight {
  color: var(--color-primary, #00d4ff);
  font-weight: 500;
}

.admin-providers__footer-updated {
  font-style: italic;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 768px) {
  .admin-providers__header {
    flex-direction: column;
  }

  .admin-providers__header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .admin-providers__search-wrapper {
    flex: 1;
    min-width: 0;
  }

  .admin-providers__filters {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .admin-providers__filter-group {
    width: 100%;
    overflow-x: auto;
    padding-bottom: 0.2rem;

    &--right {
      margin-left: 0;
    }
  }

  .admin-providers__grid {
    grid-template-columns: 1fr;
  }

  .admin-providers__table {
    font-size: 0.7rem;
  }

  .admin-providers__th,
  .admin-providers__td {
    padding: 0.4rem 0.5rem;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .admin-providers__search-input,
  .admin-providers__sort-select {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .admin-providers__card {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);

    &:hover {
      border-color: var(--color-primary, #0066cc);
    }
  }

  .admin-providers__card-title,
  .admin-providers__list-name {
    color: var(--color-text-primary, #1a1a2e);
  }

  .admin-providers__card-value,
  .admin-providers__card-description,
  .admin-providers__td {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .admin-providers__badge--lang {
    background: var(--color-bg-secondary, #e9ecf2);
    color: var(--color-text-secondary, #3d4a5c);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-providers__filter-btn {
    background: var(--color-bg-card, #ffffff);
    color: var(--color-text-secondary, #3d4a5c);
    border-color: var(--color-border, #d0d8e0);

    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
    }

    &--active {
      background: var(--color-primary, #0066cc);
      color: #ffffff;
    }
  }

  .admin-providers__table {
    background: var(--color-bg-card, #ffffff);
  }

  .admin-providers__th {
    background: var(--color-bg-secondary, #e9ecf2);
    color: var(--color-text-muted, #7a8a9a);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-providers__td {
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-providers__tr:hover {
    background: var(--color-bg-hover, #e3e8ef);
  }

  .admin-providers__toggle-slider {
    background: var(--color-bg-input, #f0f2f5);
    border-color: var(--color-border, #d0d8e0);

    &::before {
      background: var(--color-text-muted, #7a8a9a);
    }
  }

  .admin-providers__priority-dot {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);

    &--filled {
      background: var(--color-primary, #0066cc);
      border-color: var(--color-primary, #0066cc);
    }
  }
}
</style>
