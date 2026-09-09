<!-- ==========================================================================
  NexusDL 2.0 - DownloadQueue Component
  Fichier : frontend/src/components/DownloadQueue.vue
  Description : File d'attente des téléchargements avec jobs, statuts, progression,
                logs, actions (annulation, suppression, reprise, etc.)
  Version : 2.0.0
========================================================================== -->

<template>
  <div class="nexus-queue">
    <!-- En-tête -->
    <header class="nexus-queue__header">
      <div class="nexus-queue__header-left">
        <h2 class="nexus-queue__title">
          <span aria-hidden="true">⏳</span>
          File d'attente
          <span v-if="totalJobs > 0" class="nexus-queue__count">
            ({{ totalJobs }})
          </span>
        </h2>
        <span v-if="activeCount > 0" class="nexus-queue__active-badge">
          {{ activeCount }} en cours
        </span>
      </div>

      <div class="nexus-queue__header-right">
        <!-- Actions -->
        <button
          v-if="showClearCompleted"
          type="button"
          class="nexus-queue__clear-btn"
          @click="clearCompleted"
          :disabled="completedJobs.length === 0"
          aria-label="Supprimer les jobs terminés"
        >
          <span aria-hidden="true">🧹</span>
          Nettoyer
        </button>

        <button
          v-if="showCancelAll"
          type="button"
          class="nexus-queue__cancel-all-btn"
          @click="cancelAllActive"
          :disabled="activeJobs.length === 0"
          aria-label="Annuler tous les jobs actifs"
        >
          <span aria-hidden="true">⛔</span>
          Tout annuler
        </button>

        <button
          v-if="showPauseResume"
          type="button"
          class="nexus-queue__pause-btn"
          @click="togglePause"
          :disabled="activeJobs.length === 0"
          :aria-label="isPaused ? 'Reprendre' : 'Mettre en pause'"
        >
          <span aria-hidden="true">{{ isPaused ? '▶️' : '⏸️' }}</span>
          {{ isPaused ? 'Reprendre' : 'Pause' }}
        </button>
      </div>
    </header>

    <!-- Barre de progression globale -->
    <div v-if="showGlobalProgress && activeJobs.length > 0" class="nexus-queue__global-progress">
      <div class="nexus-queue__global-progress-track">
        <div
          class="nexus-queue__global-progress-bar"
          :style="{ width: `${overallProgress}%` }"
          :aria-valuenow="overallProgress"
          aria-valuemin="0"
          aria-valuemax="100"
          role="progressbar"
        />
      </div>
      <span class="nexus-queue__global-progress-label">
        {{ Math.round(overallProgress) }}% global
      </span>
    </div>

    <!-- Liste des jobs -->
    <div class="nexus-queue__list">
      <!-- État vide -->
      <div v-if="sortedJobs.length === 0" class="nexus-queue__empty">
        <slot name="empty">
          <span class="nexus-queue__empty-icon">📭</span>
          <p class="nexus-queue__empty-text">Aucun téléchargement en file d'attente</p>
          <p class="nexus-queue__empty-hint">Les téléchargements apparaîtront ici</p>
        </slot>
      </div>

      <!-- Jobs -->
      <TransitionGroup name="nexus-queue-list" tag="div">
        <div
          v-for="job in sortedJobs"
          :key="job.id"
          class="nexus-queue__item"
          :class="[
            `nexus-queue__item--${job.status}`,
            {
              'nexus-queue__item--expanded': expandedJobId === job.id,
              'nexus-queue__item--selected': selectedJobIds.includes(job.id),
            }
          ]"
          @click="handleItemClick(job)"
        >
          <!-- En-tête du job -->
          <div class="nexus-queue__item-header">
            <!-- Icône de statut -->
            <span class="nexus-queue__item-status-icon" aria-hidden="true">
              {{ getStatusIcon(job.status) }}
            </span>

            <!-- Titre et progression -->
            <div class="nexus-queue__item-info">
              <div class="nexus-queue__item-title-row">
                <span class="nexus-queue__item-title">
                  {{ job.title || 'Sans titre' }}
                </span>
                <span class="nexus-queue__item-status-label">
                  {{ getStatusLabel(job.status) }}
                </span>
              </div>

              <div class="nexus-queue__item-progress-row">
                <div class="nexus-queue__item-progress-track">
                  <div
                    class="nexus-queue__item-progress-bar"
                    :style="{ width: `${job.progress || 0}%` }"
                    :aria-valuenow="job.progress || 0"
                    aria-valuemin="0"
                    aria-valuemax="100"
                    role="progressbar"
                  />
                </div>
                <span class="nexus-queue__item-progress-text">
                  {{ job.done_chapters || 0 }} / {{ job.total_chapters || 0 }} chapitres
                  ({{ Math.round(job.progress || 0) }}%)
                </span>
              </div>

              <!-- Détails supplémentaires (chapitre en cours) -->
              <div v-if="job.current_chapter" class="nexus-queue__item-current">
                <span class="nexus-queue__item-current-label">Chapitre en cours :</span>
                <span class="nexus-queue__item-current-value">{{ job.current_chapter }}</span>
              </div>
            </div>

            <!-- Actions -->
            <div class="nexus-queue__item-actions">
              <!-- Bouton d'expansion -->
              <button
                type="button"
                class="nexus-queue__item-expand-btn"
                @click.stop="toggleExpand(job.id)"
                :aria-label="expandedJobId === job.id ? 'Réduire' : 'Développer'"
              >
                <span aria-hidden="true">{{ expandedJobId === job.id ? '▲' : '▼' }}</span>
              </button>

              <!-- Annulation -->
              <button
                v-if="canCancel(job)"
                type="button"
                class="nexus-queue__item-cancel-btn"
                @click.stop="handleCancel(job)"
                :disabled="cancellingIds.has(job.id)"
                aria-label="Annuler ce job"
              >
                <span v-if="cancellingIds.has(job.id)" class="nexus-queue__item-spinner" aria-hidden="true">⟳</span>
                <span v-else aria-hidden="true">✕</span>
              </button>
            </div>
          </div>

          <!-- Détails étendus (logs, erreurs) -->
          <div v-if="expandedJobId === job.id" class="nexus-queue__item-details">
            <!-- Logs -->
            <div v-if="job.logs && job.logs.length > 0" class="nexus-queue__item-logs">
              <div class="nexus-queue__item-logs-header">
                <span class="nexus-queue__item-logs-title">📋 Logs</span>
                <button
                  type="button"
                  class="nexus-queue__item-logs-copy"
                  @click.stop="copyLogs(job)"
                  aria-label="Copier les logs"
                >
                  📄
                </button>
              </div>
              <div class="nexus-queue__item-logs-content">
                <div
                  v-for="(log, idx) in job.logs.slice(-50)"
                  :key="idx"
                  class="nexus-queue__item-log"
                  :class="`nexus-queue__item-log--${log.level || 'info'}`"
                >
                  <span class="nexus-queue__item-log-time">{{ formatTime(log.timestamp) }}</span>
                  <span class="nexus-queue__item-log-level">{{ log.level || 'info' }}</span>
                  <span class="nexus-queue__item-log-message">{{ log.message }}</span>
                </div>
              </div>
            </div>

            <!-- Erreurs -->
            <div v-if="job.errors && job.errors.length > 0" class="nexus-queue__item-errors">
              <div class="nexus-queue__item-errors-title">❌ Erreurs</div>
              <div class="nexus-queue__item-errors-content">
                <div
                  v-for="(err, idx) in job.errors"
                  :key="idx"
                  class="nexus-queue__item-error"
                >
                  <span class="nexus-queue__item-error-time">{{ formatTime(err.timestamp) }}</span>
                  <span class="nexus-queue__item-error-message">{{ err.message }}</span>
                </div>
              </div>
            </div>

            <!-- Résultat (lien de téléchargement) -->
            <div v-if="job.status === 'completed' && job.result_path" class="nexus-queue__item-result">
              <NexusButton
                size="sm"
                variant="success"
                @click.stop="handleDownloadResult(job)"
              >
                📥 Télécharger le CBZ
              </NexusButton>
              <span v-if="job.result_size" class="nexus-queue__item-result-size">
                ({{ formatFileSize(job.result_size) }})
              </span>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- Pagination (optionnelle si beaucoup de jobs) -->
    <div v-if="showPagination && totalJobs > pageSize" class="nexus-queue__pagination">
      <button
        type="button"
        class="nexus-queue__pagination-btn"
        :disabled="currentPage <= 1"
        @click="prevPage"
      >
        ◀
      </button>
      <span class="nexus-queue__pagination-info">
        {{ currentPage }} / {{ totalPages }}
      </span>
      <button
        type="button"
        class="nexus-queue__pagination-btn"
        :disabled="currentPage >= totalPages"
        @click="nextPage"
      >
        ▶
      </button>
    </div>

    <!-- Footer -->
    <footer v-if="showFooter" class="nexus-queue__footer">
      <span class="nexus-queue__footer-info">
        {{ activeJobs.length }} actif(s) · {{ completedJobs.length }} terminé(s)
      </span>
      <span v-if="lastUpdated" class="nexus-queue__footer-updated">
        Dernière mise à jour : {{ formatTime(lastUpdated) }}
      </span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import NexusButton from './common/NexusButton.vue'
import { formatFileSize, formatTime, formatRelativeTime } from '@/utils/formatters'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Liste des jobs (objet ou tableau) */
  jobs: {
    type: [Object, Array],
    default: () => ({}),
  },
  /** IDs des jobs actifs */
  activeJobIds: {
    type: Array,
    default: () => [],
  },
  /** État de pause global */
  isPaused: {
    type: Boolean,
    default: false,
  },
  /** Polling interval en ms */
  pollingInterval: {
    type: Number,
    default: 3000,
  },
  /** Afficher la progression globale */
  showGlobalProgress: {
    type: Boolean,
    default: true,
  },
  /** Afficher le bouton de nettoyage */
  showClearCompleted: {
    type: Boolean,
    default: true,
  },
  /** Afficher le bouton d'annulation globale */
  showCancelAll: {
    type: Boolean,
    default: true,
  },
  /** Afficher le bouton pause/reprise */
  showPauseResume: {
    type: Boolean,
    default: true,
  },
  /** Afficher la pagination */
  showPagination: {
    type: Boolean,
    default: false,
  },
  /** Afficher le footer */
  showFooter: {
    type: Boolean,
    default: true,
  },
  /** Nombre d'éléments par page */
  pageSize: {
    type: Number,
    default: 20,
  },
  /** Page initiale */
  initialPage: {
    type: Number,
    default: 1,
  },
  /** URL de base pour l'API (pour les actions) */
  apiBase: {
    type: String,
    default: '/api',
  },
})

// ==========================================================================
//  Émits
// ==========================================================================

const emit = defineEmits([
  'job-selected',
  'cancel-job',
  'cancel-all',
  'clear-completed',
  'pause-toggle',
  'download-result',
  'update-count',
  'job-started',
  'job-finished',
  'job-cancelled',
  'refresh',
])

// ==========================================================================
//  État
// ==========================================================================

const expandedJobId = ref(null)
const selectedJobIds = ref([])
const cancellingIds = ref(new Set())
const currentPage = ref(props.initialPage)
const lastUpdated = ref(null)

// ==========================================================================
//  Computed
// ==========================================================================

/** Jobs sous forme de tableau */
const jobsArray = computed(() => {
  if (Array.isArray(props.jobs)) return props.jobs
  return Object.values(props.jobs)
})

/** Jobs triés par date (plus récent en premier) */
const sortedJobs = computed(() => {
  const jobs = [...jobsArray.value]
  jobs.sort((a, b) => {
    const dateA = new Date(a.created_at || a.updated_at || 0)
    const dateB = new Date(b.created_at || b.updated_at || 0)
    return dateB - dateA
  })
  return jobs
})

/** Jobs actifs (en attente ou en cours) */
const activeJobs = computed(() => {
  return jobsArray.value.filter(j =>
    ['pending', 'running', 'waiting'].includes(j.status)
  )
})

/** Jobs terminés */
const completedJobs = computed(() => {
  return jobsArray.value.filter(j =>
    ['completed', 'failed', 'cancelled'].includes(j.status)
  )
})

/** Nombre total de jobs */
const totalJobs = computed(() => jobsArray.value.length)

/** Nombre de jobs actifs */
const activeCount = computed(() => activeJobs.value.length)

/** Progression globale (moyenne des jobs actifs) */
const overallProgress = computed(() => {
  if (activeJobs.value.length === 0) return 0
  const total = activeJobs.value.reduce((acc, j) => acc + (j.progress || 0), 0)
  return total / activeJobs.value.length
})

/** Jobs paginés */
const paginatedJobs = computed(() => {
  if (!props.showPagination) return sortedJobs.value
  const start = (currentPage.value - 1) * props.pageSize
  const end = start + props.pageSize
  return sortedJobs.value.slice(start, end)
})

/** Nombre total de pages */
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(sortedJobs.value.length / props.pageSize))
})

/** Vérifie si un job peut être annulé */
const canCancel = (job) => {
  return ['pending', 'running', 'waiting'].includes(job.status)
}

// ==========================================================================
//  Méthodes
// ==========================================================================

/** Récupère l'icône du statut */
function getStatusIcon(status) {
  const map = {
    pending: '⏳',
    running: '🔄',
    completed: '✅',
    failed: '❌',
    cancelled: '⛔',
    waiting: '⏸️',
  }
  return map[status] || '❓'
}

/** Récupère le libellé du statut */
function getStatusLabel(status) {
  const map = {
    pending: 'En attente',
    running: 'En cours',
    completed: 'Terminé',
    failed: 'Échec',
    cancelled: 'Annulé',
    waiting: 'En pause',
  }
  return map[status] || status
}

/** Bascule l'expansion d'un job */
function toggleExpand(jobId) {
  expandedJobId.value = expandedJobId.value === jobId ? null : jobId
}

/** Gère le clic sur un item */
function handleItemClick(job) {
  emit('job-selected', job)
  // Sélectionner/désélectionner pour actions batch
  const idx = selectedJobIds.value.indexOf(job.id)
  if (idx === -1) {
    selectedJobIds.value.push(job.id)
  } else {
    selectedJobIds.value.splice(idx, 1)
  }
}

/** Annuler un job */
async function handleCancel(job) {
  if (cancellingIds.value.has(job.id)) return
  cancellingIds.value.add(job.id)
  try {
    await emit('cancel-job', job)
    emit('job-cancelled', job)
  } finally {
    cancellingIds.value.delete(job.id)
  }
}

/** Annuler tous les jobs actifs */
function handleCancelAll() {
  if (activeJobs.value.length === 0) return
  if (confirm(`Annuler ${activeJobs.value.length} job(s) en cours ?`)) {
    emit('cancel-all', activeJobs.value)
  }
}

/** Nettoyer les jobs terminés */
function handleClearCompleted() {
  if (completedJobs.value.length === 0) return
  if (confirm(`Supprimer ${completedJobs.value.length} job(s) terminé(s) de la file ?`)) {
    emit('clear-completed', completedJobs.value)
  }
}

/** Basculer la pause/reprise */
function togglePause() {
  emit('pause-toggle', !props.isPaused)
}

/** Télécharger le résultat d'un job */
function handleDownloadResult(job) {
  emit('download-result', job)
}

/** Copier les logs */
function copyLogs(job) {
  if (!job.logs) return
  const text = job.logs.map(l => `[${l.timestamp}] ${l.level}: ${l.message}`).join('\n')
  navigator.clipboard?.writeText(text).then(() => {
    // Notification silencieuse
  }).catch(() => {})
}

/** Pagination */
function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    scrollToTop()
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    scrollToTop()
  }
}

function scrollToTop() {
  const el = document.querySelector('.nexus-queue__list')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

/** Ajouter un job (depuis l'extérieur) */
function addJob(job) {
  // Le parent gère l'ajout via les props
  emit('refresh')
}

/** Rafraîchir la liste */
function refreshAll() {
  emit('refresh')
  lastUpdated.value = new Date().toISOString()
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

let pollingTimer = null

onMounted(() => {
  // Polling automatique
  if (props.pollingInterval > 0) {
    pollingTimer = setInterval(() => {
      refreshAll()
    }, props.pollingInterval)
  }
  lastUpdated.value = new Date().toISOString()
})

onUnmounted(() => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
})

// ==========================================================================
//  Watchers
// ==========================================================================

watch(
  () => props.activeJobIds,
  (newIds) => {
    emit('update-count', newIds.length)
  },
  { immediate: true }
)

watch(
  () => props.jobs,
  () => {
    lastUpdated.value = new Date().toISOString()
  },
  { deep: true }
)

// ==========================================================================
//  Exposer
// ==========================================================================

defineExpose({
  refreshAll,
  addJob,
  toggleExpand,
  expandedJobId,
  selectedJobIds,
  activeJobs,
})

// ==========================================================================
//  Styles
// ==========================================================================

</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$queue-transition: all var(--transition-fast, 150ms) ease;
$queue-radius: var(--radius-md, 8px);

// ==========================================================================
//  Conteneur principal
// ==========================================================================

.nexus-queue {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
  max-height: 100%;
  min-height: 200px;
}

// ==========================================================================
//  Header
// ==========================================================================

.nexus-queue__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  gap: 0.5rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
  flex-shrink: 0;
  background: var(--color-bg-secondary, #141a2b);
}

.nexus-queue__header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.nexus-queue__title {
  margin: 0;
  font-size: 1rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.nexus-queue__count {
  color: var(--color-text-muted, #6a7a9a);
  font-weight: var(--font-weight-normal, 400);
}

.nexus-queue__active-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.1rem 0.6rem;
  font-size: 0.7rem;
  font-weight: var(--font-weight-medium, 500);
  border-radius: var(--radius-full, 9999px);
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
}

.nexus-queue__header-right {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

// ==========================================================================
//  Boutons d'action
// ==========================================================================

.nexus-queue__clear-btn,
.nexus-queue__cancel-all-btn,
.nexus-queue__pause-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.6rem;
  font-size: 0.75rem;
  font-weight: var(--font-weight-medium, 500);
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  transition: $queue-transition;
  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-border-light, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

.nexus-queue__clear-btn:hover:not(:disabled) {
  border-color: var(--color-success, #4caf50);
  color: var(--color-success, #4caf50);
}

.nexus-queue__cancel-all-btn:hover:not(:disabled) {
  border-color: var(--color-error, #f44336);
  color: var(--color-error, #f44336);
}

.nexus-queue__pause-btn:hover:not(:disabled) {
  border-color: var(--color-warning, #ff9800);
  color: var(--color-warning, #ff9800);
}

// ==========================================================================
//  Progression globale
// ==========================================================================

.nexus-queue__global-progress {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 1rem;
  background: var(--color-bg-secondary, #141a2b);
  border-bottom: 1px solid var(--color-border, #1a2538);
  flex-shrink: 0;
}

.nexus-queue__global-progress-track {
  flex: 1;
  height: 4px;
  background: var(--color-bg-input, #1e2a40);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
}

.nexus-queue__global-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary, #00d4ff), var(--color-secondary, #0066ff));
  border-radius: var(--radius-full, 9999px);
  transition: width 0.5s ease;
}

.nexus-queue__global-progress-label {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  white-space: nowrap;
}

// ==========================================================================
//  Liste
// ==========================================================================

.nexus-queue__list {
  flex: 1;
  overflow-y: auto;
  padding: 0.25rem;
  min-height: 100px;
}

// ==========================================================================
//  Empty
// ==========================================================================

.nexus-queue__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  color: var(--color-text-muted, #6a7a9a);
  text-align: center;
}

.nexus-queue__empty-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.nexus-queue__empty-text {
  margin: 0;
  font-size: 0.95rem;
  font-weight: var(--font-weight-medium, 500);
}

.nexus-queue__empty-hint {
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
  opacity: 0.7;
}

// ==========================================================================
//  Item
// ==========================================================================

.nexus-queue__item {
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  margin-bottom: 0.25rem;
  transition: $queue-transition;
  cursor: pointer;

  &:hover {
    border-color: var(--color-border-light, #253254);
  }

  &--selected {
    border-left: 3px solid var(--color-primary, #00d4ff);
  }

  &--pending {
    border-left: 3px solid var(--color-warning, #ff9800);
  }
  &--running {
    border-left: 3px solid var(--color-primary, #00d4ff);
  }
  &--completed {
    border-left: 3px solid var(--color-success, #4caf50);
  }
  &--failed {
    border-left: 3px solid var(--color-error, #f44336);
  }
  &--cancelled {
    border-left: 3px solid var(--color-text-muted, #6a7a9a);
    opacity: 0.6;
  }
  &--waiting {
    border-left: 3px solid var(--color-warning, #ff9800);
  }

  &--expanded {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.2);
  }
}

// ==========================================================================
//  Item - Header
// ==========================================================================

.nexus-queue__item-header {
  display: flex;
  align-items: stretch;
  padding: 0.5rem 0.6rem;
  gap: 0.5rem;
}

.nexus-queue__item-status-icon {
  display: flex;
  align-items: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.nexus-queue__item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.1rem;
}

.nexus-queue__item-title-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.nexus-queue__item-title {
  font-size: 0.85rem;
  font-weight: var(--font-weight-medium, 500);
  color: var(--color-text-primary, #e8edf5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.nexus-queue__item-status-label {
  font-size: 0.6rem;
  text-transform: uppercase;
  padding: 0.05rem 0.4rem;
  border-radius: var(--radius-sm, 4px);
  font-weight: var(--font-weight-semibold, 600);
  flex-shrink: 0;

  .nexus-queue__item--pending & {
    background: var(--color-warning, #ff9800);
    color: var(--color-text-inverse, #0a0e1a);
  }
  .nexus-queue__item--running & {
    background: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
  }
  .nexus-queue__item--completed & {
    background: var(--color-success, #4caf50);
    color: var(--color-text-inverse, #ffffff);
  }
  .nexus-queue__item--failed & {
    background: var(--color-error, #f44336);
    color: var(--color-text-inverse, #ffffff);
  }
  .nexus-queue__item--cancelled & {
    background: var(--color-text-muted, #6a7a9a);
    color: var(--color-text-inverse, #ffffff);
  }
  .nexus-queue__item--waiting & {
    background: var(--color-warning, #ff9800);
    color: var(--color-text-inverse, #0a0e1a);
  }
}

.nexus-queue__item-progress-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.nexus-queue__item-progress-track {
  flex: 1;
  height: 3px;
  background: var(--color-bg-input, #1e2a40);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
}

.nexus-queue__item-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary, #00d4ff), var(--color-secondary, #0066ff));
  border-radius: var(--radius-full, 9999px);
  transition: width 0.3s ease;
}

.nexus-queue__item-progress-text {
  font-size: 0.65rem;
  color: var(--color-text-muted, #6a7a9a);
  white-space: nowrap;
}

.nexus-queue__item-current {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  display: flex;
  align-items: center;
  gap: 0.2rem;
}

.nexus-queue__item-current-label {
  opacity: 0.7;
}

.nexus-queue__item-current-value {
  color: var(--color-text-secondary, #b0c0d8);
  font-style: italic;
}

// ==========================================================================
//  Item - Actions
// ==========================================================================

.nexus-queue__item-actions {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  flex-shrink: 0;
}

.nexus-queue__item-expand-btn,
.nexus-queue__item-cancel-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  transition: $queue-transition;
  font-size: 0.7rem;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

.nexus-queue__item-cancel-btn:hover {
  color: var(--color-error, #f44336);
  border-color: var(--color-error, #f44336);
}

.nexus-queue__item-spinner {
  display: inline-block;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// ==========================================================================
//  Item - Details
// ==========================================================================

.nexus-queue__item-details {
  padding: 0.5rem 0.6rem 0.6rem;
  border-top: 1px solid var(--color-border, #1a2538);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

// ==========================================================================
//  Item - Logs
// ==========================================================================

.nexus-queue__item-logs {
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-sm, 4px);
  overflow: hidden;
}

.nexus-queue__item-logs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.3rem 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.nexus-queue__item-logs-title {
  font-size: 0.7rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-queue__item-logs-copy {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 0.8rem;
  &:hover {
    color: var(--color-text-primary, #e8edf5);
  }
}

.nexus-queue__item-logs-content {
  padding: 0.25rem 0.5rem;
  max-height: 150px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 0.6rem;
  line-height: 1.6;
}

.nexus-queue__item-log {
  display: flex;
  gap: 0.4rem;
  padding: 0.05rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  align-items: baseline;

  &--error {
    color: var(--color-error, #f44336);
  }
  &--warning {
    color: var(--color-warning, #ff9800);
  }
  &--info {
    color: var(--color-text-secondary, #b0c0d8);
  }
  &--debug {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.nexus-queue__item-log-time {
  color: var(--color-text-muted, #6a7a9a);
  flex-shrink: 0;
}

.nexus-queue__item-log-level {
  text-transform: uppercase;
  font-weight: var(--font-weight-semibold, 600);
  flex-shrink: 0;
  width: 3.5rem;
  font-size: 0.55rem;
}

.nexus-queue__item-log-message {
  word-break: break-word;
}

// ==========================================================================
//  Item - Errors
// ==========================================================================

.nexus-queue__item-errors {
  background: rgba(244, 67, 54, 0.05);
  border: 1px solid rgba(244, 67, 54, 0.2);
  border-radius: var(--radius-sm, 4px);
  overflow: hidden;
}

.nexus-queue__item-errors-title {
  padding: 0.3rem 0.5rem;
  font-size: 0.7rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-error, #f44336);
  background: rgba(244, 67, 54, 0.05);
  border-bottom: 1px solid rgba(244, 67, 54, 0.1);
}

.nexus-queue__item-errors-content {
  padding: 0.25rem 0.5rem;
  max-height: 100px;
  overflow-y: auto;
}

.nexus-queue__item-error {
  display: flex;
  gap: 0.4rem;
  padding: 0.1rem 0;
  font-size: 0.7rem;
  color: var(--color-error, #f44336);
  border-bottom: 1px solid rgba(244, 67, 54, 0.05);
}

.nexus-queue__item-error-time {
  color: var(--color-text-muted, #6a7a9a);
  flex-shrink: 0;
  font-size: 0.6rem;
}

.nexus-queue__item-error-message {
  flex: 1;
}

// ==========================================================================
//  Item - Result
// ==========================================================================

.nexus-queue__item-result {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.5rem;
  background: rgba(76, 175, 80, 0.05);
  border-radius: var(--radius-sm, 4px);
  border: 1px solid rgba(76, 175, 80, 0.1);
}

.nexus-queue__item-result-size {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Pagination
// ==========================================================================

.nexus-queue__pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
  flex-shrink: 0;
  background: var(--color-bg-secondary, #141a2b);
}

.nexus-queue__pagination-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  transition: $queue-transition;
  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-primary, #00d4ff);
  }
  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
}

.nexus-queue__pagination-info {
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Footer
// ==========================================================================

.nexus-queue__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 1rem;
  border-top: 1px solid var(--color-border, #1a2538);
  flex-shrink: 0;
  gap: 0.5rem;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  background: var(--color-bg-secondary, #141a2b);
}

.nexus-queue__footer-updated {
  font-style: italic;
}

// ==========================================================================
//  Animations de liste
// ==========================================================================

.nexus-queue-list-move {
  transition: transform 0.3s ease;
}

.nexus-queue-list-enter-active,
.nexus-queue-list-leave-active {
  transition: all 0.3s ease;
}

.nexus-queue-list-enter-from,
.nexus-queue-list-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.nexus-queue-list-leave-active {
  position: absolute;
}

// ==========================================================================
//  Support du thème clair
// ==========================================================================

.light-mode {
  .nexus-queue {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-queue__header {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-queue__title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .nexus-queue__item {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    &:hover {
      border-color: var(--color-border-light, #e3e8ef);
    }
    &--pending {
      border-left-color: var(--color-warning, #e65100);
    }
    &--running {
      border-left-color: var(--color-primary, #0066cc);
    }
    &--completed {
      border-left-color: var(--color-success, #2e7d32);
    }
    &--failed {
      border-left-color: var(--color-error, #c62828);
    }
    &--cancelled {
      border-left-color: var(--color-text-muted, #7a8a9a);
    }
  }

  .nexus-queue__item-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .nexus-queue__item-logs {
    background: var(--color-bg-secondary, #e9ecf2);
  }
  .nexus-queue__item-logs-header {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-queue__item-log {
    &--info {
      color: var(--color-text-secondary, #3d4a5c);
    }
    &--debug {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .nexus-queue__item-errors {
    background: rgba(198, 40, 40, 0.05);
    border-color: rgba(198, 40, 40, 0.15);
  }

  .nexus-queue__item-result {
    background: rgba(46, 125, 50, 0.05);
    border-color: rgba(46, 125, 50, 0.1);
  }

  .nexus-queue__footer {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-queue__pagination {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-queue__global-progress {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-queue__item-status-label {
    .nexus-queue__item--pending & {
      background: var(--color-warning, #e65100);
    }
    .nexus-queue__item--running & {
      background: var(--color-primary, #0066cc);
    }
  }
}
</style>
