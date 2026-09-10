<!-- ==========================================================================
  NexusDL 2.0 - Admin Logs View (version complète)
  Fichier : frontend/src/views/admin/LogsView.vue
  Description : Console d'administration pour consulter, filtrer, rechercher,
                exporter et analyser les logs système du backend NexusDL.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="admin-logs">
    <!-- ====================================================================
      EN-TÊTE — Titre, actions, statistiques
    ==================================================================== -->
    <header class="admin-logs__header">
      <div class="admin-logs__header-left">
        <h1 class="admin-logs__title">
          <span aria-hidden="true">📋</span>
          Logs système
        </h1>
        <p class="admin-logs__subtitle">
          Consultez, filtrez et analysez les journaux d'exécution du backend
        </p>
      </div>

      <div class="admin-logs__header-right">
        <!-- Sélecteur de niveau de log -->
        <NexusSelect
          v-model="logLevel"
          :options="logLevelOptions"
          placeholder="Niveau"
          size="sm"
          style="min-width: 130px"
          @change="onLevelChange"
        />

        <!-- Sélecteur d'auto-refresh -->
        <NexusSelect
          v-model="autoRefreshInterval"
          :options="autoRefreshOptions"
          placeholder="Auto-refresh"
          size="sm"
          style="min-width: 140px"
        />

        <!-- Bouton d'auto-refresh toggle -->
        <button
          type="button"
          class="admin-logs__btn admin-logs__btn--auto"
          :class="{ 'admin-logs__btn--active': autoRefreshEnabled }"
          @click="toggleAutoRefresh"
          :aria-label="autoRefreshEnabled ? 'Désactiver l\'auto-refresh' : 'Activer l\'auto-refresh'"
          :title="autoRefreshEnabled ? 'Désactiver l\'auto-refresh' : 'Activer l\'auto-refresh'"
        >
          <span aria-hidden="true">{{ autoRefreshEnabled ? '⏸️' : '▶️' }}</span>
          Auto
        </button>

        <!-- Bouton de rafraîchissement manuel -->
        <button
          type="button"
          class="admin-logs__btn admin-logs__btn--refresh"
          :disabled="loading"
          @click="fetchLogs"
          aria-label="Rafraîchir les logs"
          title="Rafraîchir maintenant"
        >
          <span v-if="loading" class="admin-logs__spinner" aria-hidden="true">⟳</span>
          <span v-else aria-hidden="true">↻</span>
          Rafraîchir
        </button>

        <!-- Bouton d'export -->
        <button
          type="button"
          class="admin-logs__btn admin-logs__btn--export"
          :disabled="filteredLogs.length === 0"
          @click="exportLogs"
          aria-label="Exporter les logs"
          title="Télécharger les logs (JSON)"
        >
          <span aria-hidden="true">⬇️</span>
          Exporter
        </button>

        <!-- Bouton pour vider le cache de logs (local) -->
        <button
          type="button"
          class="admin-logs__btn admin-logs__btn--danger"
          :disabled="logs.length === 0"
          @click="clearLogs"
          aria-label="Effacer l'affichage des logs"
          title="Effacer l'affichage"
        >
          <span aria-hidden="true">🗑️</span>
          Vider
        </button>
      </div>
    </header>

    <!-- ====================================================================
      BARRE DE STATISTIQUES
    ==================================================================== -->
    <div class="admin-logs__stats">
      <div class="admin-logs__stat">
        <span class="admin-logs__stat-value">{{ logs.length }}</span>
        <span class="admin-logs__stat-label">Total</span>
      </div>
      <div class="admin-logs__stat admin-logs__stat--debug">
        <span class="admin-logs__stat-value">{{ statsCount.debug }}</span>
        <span class="admin-logs__stat-label">Debug</span>
      </div>
      <div class="admin-logs__stat admin-logs__stat--info">
        <span class="admin-logs__stat-value">{{ statsCount.info }}</span>
        <span class="admin-logs__stat-label">Info</span>
      </div>
      <div class="admin-logs__stat admin-logs__stat--warning">
        <span class="admin-logs__stat-value">{{ statsCount.warning }}</span>
        <span class="admin-logs__stat-label">Warning</span>
      </div>
      <div class="admin-logs__stat admin-logs__stat--error">
        <span class="admin-logs__stat-value">{{ statsCount.error }}</span>
        <span class="admin-logs__stat-label">Error</span>
      </div>
      <div class="admin-logs__stat admin-logs__stat--critical">
        <span class="admin-logs__stat-value">{{ statsCount.critical }}</span>
        <span class="admin-logs__stat-label">Critical</span>
      </div>
      <div class="admin-logs__stat admin-logs__stat--filtered">
        <span class="admin-logs__stat-value">{{ filteredLogs.length }}</span>
        <span class="admin-logs__stat-label">Affichés</span>
      </div>
    </div>

    <!-- ====================================================================
      BARRE DE RECHERCHE ET FILTRES
    ==================================================================== -->
    <div class="admin-logs__toolbar">
      <div class="admin-logs__search-wrapper">
        <span class="admin-logs__search-icon" aria-hidden="true">🔍</span>
        <input
          ref="searchInputRef"
          type="text"
          class="admin-logs__search-input"
          v-model="searchQuery"
          placeholder="Rechercher dans les logs (message, module, timestamp)..."
          aria-label="Rechercher dans les logs"
          @input="onSearchInput"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="admin-logs__search-clear"
          @click="clearSearch"
          aria-label="Effacer la recherche"
        >
          <span aria-hidden="true">&times;</span>
        </button>
      </div>

      <div class="admin-logs__toolbar-right">
        <!-- Filtre par niveau (badges cliquables) -->
        <div class="admin-logs__level-filters">
          <button
            v-for="level in levels"
            :key="level.value"
            type="button"
            class="admin-logs__level-btn"
            :class="[
              `admin-logs__level-btn--${level.value}`,
              { 'admin-logs__level-btn--active': activeLevelFilters.includes(level.value) },
            ]"
            @click="toggleLevelFilter(level.value)"
            :aria-pressed="activeLevelFilters.includes(level.value)"
            :title="`Filtrer : ${level.label}`"
          >
            <span aria-hidden="true">{{ level.icon }}</span>
            <span class="admin-logs__level-btn-label">{{ level.label }}</span>
            <span class="admin-logs__level-btn-count">
              {{ statsCount[level.value] || 0 }}
            </span>
          </button>
        </div>

        <!-- Nombre de lignes -->
        <NexusSelect
          v-model.number="maxLines"
          :options="maxLinesOptions"
          placeholder="Lignes"
          size="sm"
          style="min-width: 110px"
          @change="fetchLogs"
        />
      </div>
    </div>

    <!-- ====================================================================
      ZONE D'AFFICHAGE DES LOGS
    ==================================================================== -->
    <div class="admin-logs__console" ref="consoleRef">
      <!-- État vide -->
      <div v-if="filteredLogs.length === 0 && !loading" class="admin-logs__empty">
        <span class="admin-logs__empty-icon" aria-hidden="true">📭</span>
        <p class="admin-logs__empty-text">
          {{
            logs.length === 0
              ? 'Aucun log disponible'
              : 'Aucun log ne correspond à vos filtres'
          }}
        </p>
        <button
          v-if="logs.length > 0"
          type="button"
          class="admin-logs__empty-reset"
          @click="resetFilters"
        >
          Réinitialiser les filtres
        </button>
      </div>

      <!-- Chargement initial -->
      <div v-else-if="loading && logs.length === 0" class="admin-logs__loading">
        <NexusSpinner size="lg" label="Chargement des logs..." />
      </div>

      <!-- Liste des logs -->
      <div v-else class="admin-logs__list" role="log" aria-live="polite">
        <div
          v-for="(log, index) in displayedLogs"
          :key="log.id || index"
          class="admin-logs__entry"
          :class="[
            `admin-logs__entry--${log.level}`,
            { 'admin-logs__entry--highlight': isHighlighted(log) },
          ]"
        >
          <!-- Timestamp -->
          <span class="admin-logs__entry-time" :title="log.timestamp">
            {{ formatTimestamp(log.timestamp) }}
          </span>

          <!-- Niveau -->
          <span class="admin-logs__entry-level" :class="`admin-logs__entry-level--${log.level}`">
            {{ log.level.toUpperCase() }}
          </span>

          <!-- Module -->
          <span v-if="log.module" class="admin-logs__entry-module" :title="log.module">
            [{{ log.module }}]
          </span>

          <!-- Message -->
          <span class="admin-logs__entry-message" v-html="highlightMessage(log.message)" />

          <!-- Détails (si présents) -->
          <button
            v-if="log.details"
            type="button"
            class="admin-logs__entry-details-btn"
            @click="toggleDetails(log.id || index)"
            :aria-label="isDetailsOpen(log.id || index) ? 'Masquer les détails' : 'Afficher les détails'"
            :aria-expanded="isDetailsOpen(log.id || index)"
          >
            <span aria-hidden="true">{{ isDetailsOpen(log.id || index) ? '▲' : '▼' }}</span>
          </button>

          <!-- Copier le log -->
          <button
            type="button"
            class="admin-logs__entry-copy"
            @click="copyLog(log)"
            :aria-label="'Copier ce log'"
            title="Copier"
          >
            <span aria-hidden="true">📄</span>
          </button>
        </div>

        <!-- Détails affichés sous le log concerné -->
        <template v-for="(log, index) in displayedLogs" :key="`details-${log.id || index}`">
          <div
            v-if="log.details && isDetailsOpen(log.id || index)"
            class="admin-logs__entry-details"
          >
            <pre class="admin-logs__entry-details-pre">{{ formatDetails(log.details) }}</pre>
          </div>
        </template>
      </div>

      <!-- Indicateur de chargement en bas -->
      <div v-if="loading && logs.length > 0" class="admin-logs__loading-more">
        <NexusSpinner size="sm" label="Mise à jour..." />
      </div>
    </div>

    <!-- ====================================================================
      PIED DE PAGE — Résumé, dernière mise à jour
    ==================================================================== -->
    <footer class="admin-logs__footer">
      <span class="admin-logs__footer-info">
        {{ filteredLogs.length }} / {{ logs.length }} logs affichés
        <span v-if="searchQuery" class="admin-logs__footer-search">
          · recherche : "{{ searchQuery }}"
        </span>
        <span v-if="activeLevelFilters.length > 0" class="admin-logs__footer-filters">
          · filtres : {{ activeLevelFilters.join(', ') }}
        </span>
      </span>
      <span v-if="lastUpdated" class="admin-logs__footer-updated">
        Dernière mise à jour : {{ formatTimestamp(lastUpdated) }}
      </span>
    </footer>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useNotificationsStore } from '@/stores/notifications'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusSelect from '@/components/common/NexusSelect.vue'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const api = useApi()
const toast = useToast()
const notificationsStore = useNotificationsStore()

// ==========================================================================
//  État réactif
// ==========================================================================

const logs = ref([])
const loading = ref(false)
const lastUpdated = ref(null)
const searchQuery = ref('')
const activeLevelFilters = ref([])
const autoRefreshEnabled = ref(false)
const autoRefreshInterval = ref(5000)
const logLevel = ref('')
const maxLines = ref(500)
const openDetails = ref(new Set())
const consoleRef = ref(null)
const searchInputRef = ref(null)

let autoRefreshTimer = null
let searchTimeout = null

// ==========================================================================
//  Options
// ==========================================================================

const levels = [
  { value: 'debug', label: 'Debug', icon: '🐞' },
  { value: 'info', label: 'Info', icon: 'ℹ️' },
  { value: 'warning', label: 'Warning', icon: '⚠️' },
  { value: 'error', label: 'Error', icon: '❌' },
  { value: 'critical', label: 'Critical', icon: '🔥' },
]

const logLevelOptions = [
  { value: '', label: 'Tous les niveaux' },
  { value: 'debug', label: 'Debug+' },
  { value: 'info', label: 'Info+' },
  { value: 'warning', label: 'Warning+' },
  { value: 'error', label: 'Error+' },
  { value: 'critical', label: 'Critical' },
]

const autoRefreshOptions = [
  { value: 2000, label: '2 secondes' },
  { value: 5000, label: '5 secondes' },
  { value: 10000, label: '10 secondes' },
  { value: 30000, label: '30 secondes' },
  { value: 60000, label: '1 minute' },
]

const maxLinesOptions = [
  { value: 100, label: '100 lignes' },
  { value: 250, label: '250 lignes' },
  { value: 500, label: '500 lignes' },
  { value: 1000, label: '1000 lignes' },
  { value: 5000, label: '5000 lignes' },
]

// ==========================================================================
//  Computed
// ==========================================================================

/**
 * Statistiques par niveau (sur tous les logs).
 */
const statsCount = computed(() => {
  const counts = {
    debug: 0,
    info: 0,
    warning: 0,
    error: 0,
    critical: 0,
  }
  for (const log of logs.value) {
    if (counts[log.level] !== undefined) {
      counts[log.level]++
    }
  }
  return counts
})

/**
 * Logs filtrés (par niveau + recherche).
 */
const filteredLogs = computed(() => {
  let result = [...logs.value]

  // Filtre par niveaux actifs
  if (activeLevelFilters.value.length > 0) {
    result = result.filter((log) => activeLevelFilters.value.includes(log.level))
  }

  // Filtre par recherche
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.trim().toLowerCase()
    result = result.filter((log) => {
      const message = (log.message || '').toLowerCase()
      const module = (log.module || '').toLowerCase()
      const timestamp = (log.timestamp || '').toLowerCase()
      return (
        message.includes(query) ||
        module.includes(query) ||
        timestamp.includes(query)
      )
    })
  }

  // Tri par timestamp décroissant (plus récent en premier)
  result.sort((a, b) => {
    const ta = new Date(a.timestamp).getTime() || 0
    const tb = new Date(b.timestamp).getTime() || 0
    return tb - ta
  })

  return result
})

/**
 * Logs affichés (limités en nombre pour la performance).
 */
const displayedLogs = computed(() => {
  // Limiter l'affichage à `maxLines` pour ne pas saturer le DOM
  return filteredLogs.value.slice(0, maxLines.value)
})

// ==========================================================================
//  Méthodes
// ==========================================================================

/**
 * Récupère les logs depuis l'API.
 */
async function fetchLogs() {
  loading.value = true
  try {
    const params = {
      lines: maxLines.value,
      level: logLevel.value || undefined,
    }
    const response = await api.get('/admin/logs', { params })

    // Le backend peut renvoyer : { lines: [...] } ou { logs: [...] } ou directement un tableau
    let rawLogs = []
    if (Array.isArray(response)) {
      rawLogs = response
    } else if (Array.isArray(response?.lines)) {
      rawLogs = response.lines
    } else if (Array.isArray(response?.logs)) {
      rawLogs = response.logs
    } else if (typeof response?.lines === 'string') {
      // Si le backend renvoie une chaîne multiligne (log brut)
      rawLogs = response.lines
        .split('\n')
        .filter((line) => line.trim())
        .map((line) => parseLogLine(line))
    }

    // Normaliser les logs
    logs.value = rawLogs.map((log, index) => normalizeLog(log, index))
    lastUpdated.value = new Date().toISOString()

    // Scroll automatique vers le bas si l'utilisateur était déjà en bas
    await nextTick()
    scrollToBottomIfNeeded()
  } catch (err) {
    console.error('Erreur lors du chargement des logs:', err)
    toast.error(`Impossible de charger les logs: ${err.message}`, '❌')
  } finally {
    loading.value = false
  }
}

/**
 * Parse une ligne de log brute (format texte) en objet.
 * @param {string} line
 * @returns {Object}
 */
function parseLogLine(line) {
  // Format : [2025-01-15 14:30:00] [INFO] [module] message
  const regex = /^\[([^\]]+)\]\s*\[([^\]]+)\]\s*\[([^\]]+)\]\s*(.*)$/
  const match = line.match(regex)

  if (match) {
    return {
      timestamp: match[1],
      level: match[2].toLowerCase(),
      module: match[3],
      message: match[4],
    }
  }

  // Fallback : toute la ligne est le message
  return {
    timestamp: new Date().toISOString(),
    level: 'info',
    module: '',
    message: line,
  }
}

/**
 * Normalise un objet log pour garantir une structure cohérente.
 * @param {Object|string} raw
 * @param {number} index
 * @returns {Object}
 */
function normalizeLog(raw, index) {
  if (typeof raw === 'string') {
    const parsed = parseLogLine(raw)
    return { id: `log-${index}-${parsed.timestamp}`, ...parsed }
  }

  return {
    id: raw.id || `log-${index}-${raw.timestamp || Date.now()}`,
    timestamp: raw.timestamp || new Date().toISOString(),
    level: (raw.level || 'info').toLowerCase(),
    module: raw.module || '',
    message: raw.message || '',
    details: raw.details || raw.stack || raw.exception || null,
  }
}

/**
 * Formate un timestamp pour l'affichage.
 * @param {string} timestamp
 * @returns {string}
 */
function formatTimestamp(timestamp) {
  if (!timestamp) return ''
  try {
    const d = dayjs(timestamp)
    if (!d.isValid()) return timestamp
    // Si le log date d'aujourd'hui, on affiche juste l'heure
    if (d.isSame(dayjs(), 'day')) {
      return d.format('HH:mm:ss.SSS')
    }
    return d.format('DD/MM HH:mm:ss')
  } catch (_) {
    return timestamp
  }
}

/**
 * Formate les détails (stack trace, JSON, etc.).
 * @param {*} details
 * @returns {string}
 */
function formatDetails(details) {
  if (details == null) return ''
  if (typeof details === 'string') return details
  try {
    return JSON.stringify(details, null, 2)
  } catch (_) {
    return String(details)
  }
}

/**
 * Met en surbrillance le terme recherché dans le message.
 * @param {string} message
 * @returns {string} - HTML avec <mark>
 */
function highlightMessage(message) {
  if (!message) return ''

  // Échapper le HTML pour éviter les injections
  const escaped = String(message)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')

  if (!searchQuery.value.trim()) return escaped

  const query = searchQuery.value.trim()
  const regex = new RegExp(
    `(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`,
    'gi'
  )
  return escaped.replace(regex, '<mark class="admin-logs__highlight">$1</mark>')
}

/**
 * Vérifie si un log est mis en surbrillance (contient le terme recherché).
 * @param {Object} log
 * @returns {boolean}
 */
function isHighlighted(log) {
  if (!searchQuery.value.trim()) return false
  const query = searchQuery.value.trim().toLowerCase()
  return (
    (log.message || '').toLowerCase().includes(query) ||
    (log.module || '').toLowerCase().includes(query)
  )
}

/**
 * Toggle l'affichage des détails d'un log.
 * @param {string|number} id
 */
function toggleDetails(id) {
  if (openDetails.value.has(id)) {
    openDetails.value.delete(id)
  } else {
    openDetails.value.add(id)
  }
}

/**
 * Vérifie si les détails d'un log sont ouverts.
 * @param {string|number} id
 * @returns {boolean}
 */
function isDetailsOpen(id) {
  return openDetails.value.has(id)
}

/**
 * Toggle un filtre de niveau.
 * @param {string} level
 */
function toggleLevelFilter(level) {
  const idx = activeLevelFilters.value.indexOf(level)
  if (idx === -1) {
    activeLevelFilters.value.push(level)
  } else {
    activeLevelFilters.value.splice(idx, 1)
  }
}

/**
 * Change le niveau de log global (via le select).
 */
function onLevelChange() {
  // Mettre à jour les filtres en fonction du niveau sélectionné
  const idx = levels.findIndex((l) => l.value === logLevel.value)
  if (idx === -1) {
    activeLevelFilters.value = []
  } else {
    // Sélectionner tous les niveaux >= au niveau choisi
    activeLevelFilters.value = levels.slice(idx).map((l) => l.value)
  }
}

/**
 * Debounce de la recherche.
 */
function onSearchInput() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    // La recherche est instantanée via le computed, mais on peut
    // déclencher des actions supplémentaires ici si nécessaire.
  }, 200)
}

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
  activeLevelFilters.value = []
  logLevel.value = ''
}

/**
 * Toggle l'auto-refresh.
 */
function toggleAutoRefresh() {
  autoRefreshEnabled.value = !autoRefreshEnabled.value
  if (autoRefreshEnabled.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

/**
 * Démarre l'auto-refresh.
 */
function startAutoRefresh() {
  stopAutoRefresh()
  autoRefreshTimer = setInterval(() => {
    if (!loading.value) {
      fetchLogs()
    }
  }, autoRefreshInterval.value)
}

/**
 * Arrête l'auto-refresh.
 */
function stopAutoRefresh() {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

/**
 * Scroll vers le bas de la console si l'utilisateur est déjà en bas.
 */
function scrollToBottomIfNeeded() {
  const el = consoleRef.value
  if (!el) return

  // Vérifier si l'utilisateur est proche du bas (à 100px près)
  const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100

  if (isNearBottom) {
    el.scrollTop = el.scrollHeight
  }
}

/**
 * Copie un log dans le presse-papiers.
 * @param {Object} log
 */
async function copyLog(log) {
  const text = `[${log.timestamp}] [${log.level.toUpperCase()}]${log.module ? ` [${log.module}]` : ''} ${log.message}`
  try {
    await navigator.clipboard.writeText(text)
    toast.success('Log copié dans le presse-papiers', '📋')
  } catch (err) {
    toast.error('Impossible de copier', '❌')
  }
}

/**
 * Exporte les logs filtrés en JSON.
 */
function exportLogs() {
  if (filteredLogs.value.length === 0) {
    toast.warning('Aucun log à exporter', '⚠️')
    return
  }

  const data = {
    exported_at: new Date().toISOString(),
    total: filteredLogs.value.length,
    filters: {
      search: searchQuery.value,
      levels: activeLevelFilters.value,
      max_lines: maxLines.value,
    },
    logs: filteredLogs.value,
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `nexusdl-logs-${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  toast.success(`${filteredLogs.value.length} logs exportés`, '📥')
}

/**
 * Vide l'affichage des logs (local uniquement).
 */
function clearLogs() {
  if (!confirm('Effacer l\'affichage des logs ? (Les logs sur le serveur ne seront pas modifiés)')) {
    return
  }
  logs.value = []
  openDetails.value.clear()
  toast.info('Affichage vidé', '🗑️')
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  await fetchLogs()
})

onUnmounted(() => {
  stopAutoRefresh()
  clearTimeout(searchTimeout)
})

// ==========================================================================
//  Watchers
// ==========================================================================

// Redémarrer l'auto-refresh si l'intervalle change
watch(autoRefreshInterval, () => {
  if (autoRefreshEnabled.value) {
    startAutoRefresh()
  }
})

// Recharger quand le nombre de lignes change
watch(maxLines, () => {
  fetchLogs()
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.admin-logs {
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

.admin-logs__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.admin-logs__header-left {
  flex: 1;
  min-width: 200px;
}

.admin-logs__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.admin-logs__subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.admin-logs__header-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

// ==========================================================================
//  Boutons
// ==========================================================================

.admin-logs__btn {
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

  &--auto.admin-logs__btn--active {
    background: rgba(0, 212, 255, 0.15);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-primary, #00d4ff);
  }

  &--refresh:hover:not(:disabled) {
    border-color: var(--color-info, #2196f3);
    color: var(--color-info, #2196f3);
  }

  &--export:hover:not(:disabled) {
    border-color: var(--color-success, #4caf50);
    color: var(--color-success, #4caf50);
  }

  &--danger:hover:not(:disabled) {
    border-color: var(--color-error, #f44336);
    color: var(--color-error, #f44336);
  }
}

.admin-logs__spinner {
  display: inline-block;
  animation: adminLogsSpin 0.8s linear infinite;
}

@keyframes adminLogsSpin {
  to {
    transform: rotate(360deg);
  }
}

// ==========================================================================
//  Statistiques
// ==========================================================================

.admin-logs__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.admin-logs__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.3rem 0.7rem;
  border-radius: var(--radius-sm, 4px);
  background: var(--color-bg-card, #1a2538);
  min-width: 60px;

  &--debug { border-left: 3px solid #6a7a9a; }
  &--info { border-left: 3px solid #2196f3; }
  &--warning { border-left: 3px solid #ff9800; }
  &--error { border-left: 3px solid #f44336; }
  &--critical { border-left: 3px solid #d32f2f; }
  &--filtered { border-left: 3px solid var(--color-primary, #00d4ff); }
}

.admin-logs__stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  font-variant-numeric: tabular-nums;
}

.admin-logs__stat-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  color: var(--color-text-muted, #6a7a9a);
  letter-spacing: 0.05em;
}

// ==========================================================================
//  Toolbar
// ==========================================================================

.admin-logs__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: space-between;
}

.admin-logs__search-wrapper {
  position: relative;
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
}

.admin-logs__search-icon {
  position: absolute;
  left: 0.5rem;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
}

.admin-logs__search-input {
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

.admin-logs__search-clear {
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

.admin-logs__toolbar-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

// ==========================================================================
//  Filtres par niveau
// ==========================================================================

.admin-logs__level-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem;
}

.admin-logs__level-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.55rem;
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }

  &--active {
    border-color: currentColor;
    background: rgba(255, 255, 255, 0.05);
  }

  &--debug.admin-logs__level-btn--active {
    background: rgba(106, 122, 154, 0.2);
    color: #8899b0;
  }

  &--info.admin-logs__level-btn--active {
    background: rgba(33, 150, 243, 0.2);
    color: #64b5f6;
  }

  &--warning.admin-logs__level-btn--active {
    background: rgba(255, 152, 0, 0.2);
    color: #ffb74d;
  }

  &--error.admin-logs__level-btn--active {
    background: rgba(244, 67, 54, 0.2);
    color: #e57373;
  }

  &--critical.admin-logs__level-btn--active {
    background: rgba(211, 47, 47, 0.25);
    color: #ef5350;
  }
}

.admin-logs__level-btn-label {
  font-size: 0.7rem;
}

.admin-logs__level-btn-count {
  font-size: 0.6rem;
  padding: 0 0.3rem;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.3);
  color: inherit;
  opacity: 0.8;
  font-variant-numeric: tabular-nums;
}

// ==========================================================================
//  Console
// ==========================================================================

.admin-logs__console {
  flex: 1;
  min-height: 400px;
  max-height: 60vh;
  overflow-y: auto;
  background: #0d1117;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  position: relative;

  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  &::-webkit-scrollbar-track {
    background: #161b22;
  }
  &::-webkit-scrollbar-thumb {
    background: #30363d;
    border-radius: 4px;
    &:hover {
      background: #484f58;
    }
  }
  scrollbar-width: thin;
  scrollbar-color: #30363d #161b22;
}

.admin-logs__list {
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.admin-logs__entry {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.15rem 0.4rem;
  border-radius: var(--radius-sm, 4px);
  transition: background 0.15s ease;
  word-break: break-word;

  &:hover {
    background: rgba(255, 255, 255, 0.03);
    .admin-logs__entry-copy,
    .admin-logs__entry-details-btn {
      opacity: 1;
    }
  }

  &--highlight {
    background: rgba(255, 235, 59, 0.08);
  }
}

.admin-logs__entry-time {
  flex-shrink: 0;
  color: #6a7a9a;
  font-variant-numeric: tabular-nums;
  cursor: help;
}

.admin-logs__entry-level {
  flex-shrink: 0;
  font-weight: 700;
  width: 4.5rem;
  text-align: left;

  &--debug { color: #8899b0; }
  &--info { color: #64b5f6; }
  &--warning { color: #ffb74d; }
  &--error { color: #e57373; }
  &--critical {
    color: #ffffff;
    background: #d32f2f;
    padding: 0 0.3rem;
    border-radius: 3px;
  }
}

.admin-logs__entry-module {
  flex-shrink: 0;
  color: #b8c4d0;
  opacity: 0.7;
}

.admin-logs__entry-message {
  flex: 1;
  color: #c9d1d9;
  white-space: pre-wrap;
}

.admin-logs__highlight {
  background: #ffeb3b;
  color: #000;
  padding: 0 2px;
  border-radius: 2px;
}

.admin-logs__entry-details-btn,
.admin-logs__entry-copy {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: #6a7a9a;
  cursor: pointer;
  padding: 0 0.3rem;
  font-size: 0.7rem;
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease;

  &:hover {
    color: #e8edf5;
  }
}

.admin-logs__entry-details {
  padding: 0.5rem 0.8rem;
  margin: 0.2rem 0.5rem 0.5rem;
  background: #161b22;
  border-left: 3px solid #30363d;
  border-radius: var(--radius-sm, 4px);
  overflow-x: auto;
}

.admin-logs__entry-details-pre {
  margin: 0;
  color: #c9d1d9;
  font-size: 0.7rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}

// ==========================================================================
//  États
// ==========================================================================

.admin-logs__empty,
.admin-logs__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: #6a7a9a;
  text-align: center;
  gap: 0.5rem;
}

.admin-logs__empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.admin-logs__empty-text {
  margin: 0;
  font-size: 0.9rem;
}

.admin-logs__empty-reset {
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

.admin-logs__loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  position: sticky;
  bottom: 0;
  background: linear-gradient(transparent, #0d1117 30%);
}

// ==========================================================================
//  Footer
// ==========================================================================

.admin-logs__footer {
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

.admin-logs__footer-info {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.admin-logs__footer-search,
.admin-logs__footer-filters {
  color: var(--color-primary, #00d4ff);
  font-weight: 500;
}

.admin-logs__footer-updated {
  font-style: italic;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 768px) {
  .admin-logs__header {
    flex-direction: column;
  }

  .admin-logs__header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .admin-logs__toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .admin-logs__toolbar-right {
    justify-content: space-between;
  }

  .admin-logs__level-filters {
    overflow-x: auto;
    padding-bottom: 0.2rem;
  }

  .admin-logs__entry {
    font-size: 0.7rem;
    flex-wrap: wrap;
  }

  .admin-logs__entry-level {
    width: auto;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .admin-logs__console {
    background: #f6f8fa;
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-logs__list {
    color: #24292e;
  }

  .admin-logs__entry:hover {
    background: rgba(0, 0, 0, 0.03);
  }

  .admin-logs__entry-time {
    color: #6a737d;
  }

  .admin-logs__entry-message {
    color: #24292e;
  }

  .admin-logs__entry-level {
    &--debug { color: #6a737d; }
    &--info { color: #0366d6; }
    &--warning { color: #b08800; }
    &--error { color: #d73a49; }
    &--critical { background: #d73a49; color: #fff; }
  }

  .admin-logs__entry-details {
    background: #eaeef2;
    border-left-color: #d0d7de;
  }

  .admin-logs__entry-details-pre {
    color: #24292e;
  }

  .admin-logs__highlight {
    background: #fff3c4;
    color: #24292e;
  }

  .admin-logs__loading-more {
    background: linear-gradient(transparent, #f6f8fa 30%);
  }
}
</style>
