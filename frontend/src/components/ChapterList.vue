<!-- ==========================================================================
  NexusDL 2.0 - ChapterList Component
  Fichier : frontend/src/components/ChapterList.vue
  Description : Liste des chapitres avec sélection, pagination, recherche, tri
  Version : 2.0.0
========================================================================== -->

<template>
  <div class="nexus-chapter-list">
    <!-- En-tête avec actions -->
    <header class="nexus-chapter-list__header">
      <div class="nexus-chapter-list__header-left">
        <h3 class="nexus-chapter-list__title">
          <slot name="title">
            Chapitres
            <span v-if="totalChapters > 0" class="nexus-chapter-list__count">
              ({{ totalChapters }})
            </span>
          </slot>
        </h3>
      </div>

      <div class="nexus-chapter-list__header-right">
        <!-- Sélection globale -->
        <button
          v-if="selectable"
          type="button"
          class="nexus-chapter-list__select-all"
          @click="toggleSelectAll"
          :aria-label="allSelected ? 'Désélectionner tout' : 'Sélectionner tout'"
        >
          <span class="nexus-chapter-list__select-all-checkbox" :class="{ 'is-checked': allSelected && visibleChapters.length > 0 }">
            <span v-if="allSelected && visibleChapters.length > 0" aria-hidden="true">✓</span>
            <span v-else-if="someSelected" class="nexus-chapter-list__select-all-indeterminate" aria-hidden="true">−</span>
          </span>
        </button>

        <!-- Recherche -->
        <div v-if="searchable" class="nexus-chapter-list__search">
          <span class="nexus-chapter-list__search-icon" aria-hidden="true">🔍</span>
          <input
            ref="searchInputRef"
            type="text"
            class="nexus-chapter-list__search-input"
            v-model="searchQuery"
            :placeholder="searchPlaceholder || 'Rechercher un chapitre...'"
            @input="handleSearch"
            aria-label="Rechercher un chapitre"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="nexus-chapter-list__search-clear"
            @click="clearSearch"
            aria-label="Effacer la recherche"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <!-- Tri -->
        <div v-if="sortable" class="nexus-chapter-list__sort">
          <button
            type="button"
            class="nexus-chapter-list__sort-btn"
            @click="toggleSortOrder"
            :aria-label="`Trier par ${sortField === 'number' ? 'numéro' : 'date'} ${sortOrder === 'asc' ? 'croissant' : 'décroissant'}`"
          >
            <span class="nexus-chapter-list__sort-label">
              {{ sortField === 'number' ? 'N°' : 'Date' }}
            </span>
            <span class="nexus-chapter-list__sort-icon" aria-hidden="true">
              {{ sortOrder === 'asc' ? '↑' : '↓' }}
            </span>
          </button>
          <button
            v-if="sortable"
            type="button"
            class="nexus-chapter-list__sort-field-btn"
            @click="toggleSortField"
            aria-label="Changer le champ de tri"
          >
            <span aria-hidden="true">⚙</span>
          </button>
        </div>

        <!-- Nombre affiché -->
        <div v-if="showCount" class="nexus-chapter-list__count-display">
          {{ visibleChapters.length }} / {{ filteredChapters.length }}
        </div>
      </div>
    </header>

    <!-- Liste des chapitres -->
    <div class="nexus-chapter-list__body">
      <!-- État de chargement -->
      <div v-if="loading" class="nexus-chapter-list__loading">
        <NexusSpinner size="sm" label="Chargement des chapitres..." />
      </div>

      <!-- Aucun résultat -->
      <div v-else-if="filteredChapters.length === 0" class="nexus-chapter-list__empty">
        <slot name="empty">
          <span class="nexus-chapter-list__empty-icon">📭</span>
          <p class="nexus-chapter-list__empty-text">
            {{ searchQuery ? 'Aucun chapitre ne correspond à votre recherche' : 'Aucun chapitre disponible' }}
          </p>
        </slot>
      </div>

      <!-- Liste -->
      <template v-else>
        <div class="nexus-chapter-list__items">
          <div
            v-for="chapter in visibleChapters"
            :key="chapter.id || chapter.number"
            class="nexus-chapter-list__item"
            :class="{
              'nexus-chapter-list__item--selected': isSelected(chapter),
              'nexus-chapter-list__item--disabled': chapter.disabled,
              'nexus-chapter-list__item--read': chapter.read,
              'nexus-chapter-list__item--available': chapter.available !== false,
            }"
            @click="handleChapterClick(chapter)"
          >
            <!-- Case à cocher (si selectable) -->
            <div v-if="selectable" class="nexus-chapter-list__item-checkbox" @click.stop>
              <input
                type="checkbox"
                :id="`chapter-${chapter.id || chapter.number}`"
                :checked="isSelected(chapter)"
                :disabled="chapter.disabled"
                @change="toggleSelect(chapter)"
                :aria-label="`Sélectionner le chapitre ${chapter.title || chapter.number}`"
              />
              <label :for="`chapter-${chapter.id || chapter.number}`" />
            </div>

            <!-- Numéro -->
            <span class="nexus-chapter-list__item-number">
              <slot name="number" :chapter="chapter">
                {{ chapter.number !== undefined && chapter.number !== null ? `#${chapter.number}` : '—' }}
              </slot>
            </span>

            <!-- Titre -->
            <span class="nexus-chapter-list__item-title">
              <slot name="title" :chapter="chapter">
                {{ chapter.title || `Chapitre ${chapter.number}` }}
              </slot>
            </span>

            <!-- Métadonnées -->
            <div class="nexus-chapter-list__item-meta">
              <!-- Date -->
              <span v-if="chapter.release_date || chapter.upload_date" class="nexus-chapter-list__item-date">
                <slot name="date" :chapter="chapter">
                  {{ formatDate(chapter.release_date || chapter.upload_date) }}
                </slot>
              </span>

              <!-- Pages -->
              <span v-if="chapter.pages" class="nexus-chapter-list__item-pages">
                {{ chapter.pages }}p
              </span>

              <!-- Langue -->
              <span v-if="chapter.language" class="nexus-chapter-list__item-language">
                {{ chapter.language }}
              </span>

              <!-- Statut de disponibilité -->
              <span v-if="chapter.available === false" class="nexus-chapter-list__item-status nexus-chapter-list__item-status--unavailable">
                Indisponible
              </span>
              <span v-else-if="chapter.read" class="nexus-chapter-list__item-status nexus-chapter-list__item-status--read">
                Lu
              </span>
            </div>

            <!-- Actions -->
            <div class="nexus-chapter-list__item-actions">
              <slot name="actions" :chapter="chapter">
                <!-- Bouton de téléchargement -->
                <NexusButton
                  v-if="downloadable && chapter.available !== false"
                  size="sm"
                  variant="primary"
                  :loading="isDownloading(chapter)"
                  :disabled="isDownloading(chapter) || chapter.disabled"
                  @click.stop="handleDownload(chapter)"
                  aria-label="Télécharger ce chapitre"
                >
                  <span aria-hidden="true">⬇</span>
                </NexusButton>
              </slot>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="paginated && totalChapters > pageSize" class="nexus-chapter-list__pagination">
          <button
            type="button"
            class="nexus-chapter-list__pagination-btn"
            :disabled="currentPage <= 1"
            @click="prevPage"
            aria-label="Page précédente"
          >
            <span aria-hidden="true">◀</span>
          </button>

          <span class="nexus-chapter-list__pagination-info">
            {{ currentPage }} / {{ totalPages }}
          </span>

          <button
            type="button"
            class="nexus-chapter-list__pagination-btn"
            :disabled="currentPage >= totalPages"
            @click="nextPage"
            aria-label="Page suivante"
          >
            <span aria-hidden="true">▶</span>
          </button>
        </div>
      </template>
    </div>

    <!-- Pied de page avec résumé -->
    <footer v-if="showFooter" class="nexus-chapter-list__footer">
      <slot name="footer">
        <span class="nexus-chapter-list__footer-info">
          {{ selectedChapters.length }} / {{ filteredChapters.length }} chapitre(s) sélectionné(s)
        </span>
        <div class="nexus-chapter-list__footer-actions">
          <slot name="footer-actions" :selected="selectedChapters">
            <NexusButton
              v-if="downloadable && selectedChapters.length > 0"
              size="sm"
              variant="primary"
              :loading="bulkDownloading"
              @click="handleBulkDownload"
            >
              Télécharger les sélectionnés ({{ selectedChapters.length }})
            </NexusButton>
          </slot>
        </div>
      </slot>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import NexusButton from './common/NexusButton.vue'
import NexusSpinner from './common/NexusSpinner.vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Liste des chapitres */
  chapters: {
    type: Array,
    default: () => [],
  },
  /** Nombre total de chapitres (pour la pagination) */
  totalChapters: {
    type: Number,
    default: 0,
  },
  /** Mode sélection */
  selectable: {
    type: Boolean,
    default: true,
  },
  /** Mode téléchargeable */
  downloadable: {
    type: Boolean,
    default: true,
  },
  /** Mode recherche */
  searchable: {
    type: Boolean,
    default: true,
  },
  /** Placeholder de la recherche */
  searchPlaceholder: {
    type: String,
    default: '',
  },
  /** Mode tri */
  sortable: {
    type: Boolean,
    default: true,
  },
  /** Champ de tri par défaut */
  defaultSortField: {
    type: String,
    default: 'number',
    validator: (val) => ['number', 'date', 'title'].includes(val),
  },
  /** Ordre de tri par défaut */
  defaultSortOrder: {
    type: String,
    default: 'desc',
    validator: (val) => ['asc', 'desc'].includes(val),
  },
  /** Pagination activée */
  paginated: {
    type: Boolean,
    default: true,
  },
  /** Nombre de chapitres par page */
  pageSize: {
    type: Number,
    default: 25,
  },
  /** Page initiale */
  initialPage: {
    type: Number,
    default: 1,
  },
  /** Afficher le compteur */
  showCount: {
    type: Boolean,
    default: true,
  },
  /** Afficher le footer */
  showFooter: {
    type: Boolean,
    default: true,
  },
  /** État de chargement */
  loading: {
    type: Boolean,
    default: false,
  },
  /** Désactiver les chapitres déjà téléchargés */
  disableDownloaded: {
    type: Boolean,
    default: false,
  },
  /** IDs des chapitres déjà téléchargés */
  downloadedIds: {
    type: Array,
    default: () => [],
  },
  /** Sélection initiale (IDs) */
  initialSelected: {
    type: Array,
    default: () => [],
  },
})

// ==========================================================================
//  Émits
// ==========================================================================

const emit = defineEmits([
  'update:selected',
  'select',
  'deselect',
  'download',
  'bulk-download',
  'search',
  'sort',
  'page-change',
  'chapter-click',
])

// ==========================================================================
//  État
// ==========================================================================

const searchQuery = ref('')
const sortField = ref(props.defaultSortField)
const sortOrder = ref(props.defaultSortOrder)
const currentPage = ref(props.initialPage)
const selectedIds = ref([...props.initialSelected])
const downloadingIds = ref(new Set())
const bulkDownloading = ref(false)
const searchInputRef = ref(null)

// ==========================================================================
//  Computed
// ==========================================================================

/** Filtrage par recherche */
const filteredChapters = computed(() => {
  let result = [...props.chapters]
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter(ch => {
      const title = (ch.title || '').toLowerCase()
      const number = String(ch.number || '')
      return title.includes(q) || number.includes(q)
    })
  }
  return result
})

/** Tri des chapitres */
const sortedChapters = computed(() => {
  const result = [...filteredChapters.value]
  const field = sortField.value
  const order = sortOrder.value === 'asc' ? 1 : -1

  result.sort((a, b) => {
    let aVal, bVal
    if (field === 'number') {
      aVal = a.number ?? 0
      bVal = b.number ?? 0
    } else if (field === 'date') {
      aVal = new Date(a.release_date || a.upload_date || a.created_at || 0).getTime()
      bVal = new Date(b.release_date || b.upload_date || b.created_at || 0).getTime()
    } else if (field === 'title') {
      aVal = (a.title || '').toLowerCase()
      bVal = (b.title || '').toLowerCase()
      return aVal.localeCompare(bVal) * order
    }
    if (aVal < bVal) return -1 * order
    if (aVal > bVal) return 1 * order
    return 0
  })
  return result
})

/** Pagination */
const visibleChapters = computed(() => {
  if (!props.paginated) return sortedChapters.value
  const start = (currentPage.value - 1) * props.pageSize
  const end = start + props.pageSize
  return sortedChapters.value.slice(start, end)
})

/** Nombre total de pages */
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredChapters.value.length / props.pageSize))
})

/** Tous les chapitres visibles sont-ils sélectionnés ? */
const allSelected = computed(() => {
  if (visibleChapters.value.length === 0) return false
  const visibleIds = visibleChapters.value.map(ch => ch.id || ch.number)
  return visibleIds.every(id => selectedIds.value.includes(id))
})

/** Certains chapitres visibles sont-ils sélectionnés ? */
const someSelected = computed(() => {
  if (visibleChapters.value.length === 0) return false
  const visibleIds = visibleChapters.value.map(ch => ch.id || ch.number)
  return visibleIds.some(id => selectedIds.value.includes(id))
})

/** Chapitres sélectionnés (objets complets) */
const selectedChapters = computed(() => {
  return props.chapters.filter(ch => {
    const id = ch.id || ch.number
    return selectedIds.value.includes(id)
  })
})

/** Taille de la sélection */
const selectionCount = computed(() => selectedIds.value.length)

// ==========================================================================
//  Méthodes
// ==========================================================================

/** Vérifie si un chapitre est sélectionné */
function isSelected(chapter) {
  const id = chapter.id || chapter.number
  return selectedIds.value.includes(id)
}

/** Vérifie si un chapitre est en cours de téléchargement */
function isDownloading(chapter) {
  const id = chapter.id || chapter.number
  return downloadingIds.value.has(id)
}

/** Vérifie si un chapitre est déjà téléchargé */
function isDownloaded(chapter) {
  const id = chapter.id || chapter.number
  return props.downloadedIds.includes(id)
}

/** Basculer la sélection d'un chapitre */
function toggleSelect(chapter) {
  if (chapter.disabled) return
  const id = chapter.id || chapter.number
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) {
    selectedIds.value.push(id)
    emit('select', chapter)
  } else {
    selectedIds.value.splice(idx, 1)
    emit('deselect', chapter)
  }
  emit('update:selected', selectedIds.value)
}

/** Sélectionner/Désélectionner tout */
function toggleSelectAll() {
  if (allSelected.value) {
    // Désélectionner tout
    const visibleIds = visibleChapters.value.map(ch => ch.id || ch.number)
    selectedIds.value = selectedIds.value.filter(id => !visibleIds.includes(id))
    emit('update:selected', selectedIds.value)
  } else {
    // Sélectionner tout
    const visibleIds = visibleChapters.value.map(ch => ch.id || ch.number)
    for (const id of visibleIds) {
      if (!selectedIds.value.includes(id)) {
        selectedIds.value.push(id)
      }
    }
    emit('update:selected', selectedIds.value)
  }
}

/** Gérer le clic sur un chapitre */
function handleChapterClick(chapter) {
  if (chapter.disabled) return
  emit('chapter-click', chapter)
  if (props.selectable) {
    toggleSelect(chapter)
  }
}

/** Gérer le téléchargement d'un chapitre */
function handleDownload(chapter) {
  if (chapter.disabled || chapter.available === false) return
  const id = chapter.id || chapter.number
  if (downloadingIds.value.has(id)) return
  downloadingIds.value.add(id)
  emit('download', chapter)
  // Le parent doit gérer la fin du téléchargement
  // On ne retire pas de la liste, le parent le fera via une prop ou un événement
}

/** Gérer le téléchargement en masse */
async function handleBulkDownload() {
  if (bulkDownloading.value || selectedChapters.value.length === 0) return
  bulkDownloading.value = true
  try {
    await emit('bulk-download', selectedChapters.value)
  } finally {
    bulkDownloading.value = false
  }
}

/** Recherche */
function handleSearch() {
  currentPage.value = 1
  emit('search', searchQuery.value)
}

/** Effacer la recherche */
function clearSearch() {
  searchQuery.value = ''
  currentPage.value = 1
  emit('search', '')
  nextTick(() => {
    if (searchInputRef.value) {
      searchInputRef.value.focus()
    }
  })
}

/** Changer l'ordre de tri */
function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  emit('sort', { field: sortField.value, order: sortOrder.value })
}

/** Changer le champ de tri */
function toggleSortField() {
  const fields = ['number', 'date', 'title']
  const idx = fields.indexOf(sortField.value)
  sortField.value = fields[(idx + 1) % fields.length]
  emit('sort', { field: sortField.value, order: sortOrder.value })
}

/** Pagination */
function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    emit('page-change', currentPage.value)
    // Scroll en haut de la liste
    scrollToTop()
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    emit('page-change', currentPage.value)
    scrollToTop()
  }
}

function goToPage(page) {
  const p = Math.max(1, Math.min(totalPages.value, page))
  if (p !== currentPage.value) {
    currentPage.value = p
    emit('page-change', currentPage.value)
    scrollToTop()
  }
}

function scrollToTop() {
  const el = document.querySelector('.nexus-chapter-list__items')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

/** Formater une date */
function formatDate(date) {
  if (!date) return ''
  const d = new Date(date)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const diff = (now - d) / (1000 * 60 * 60 * 24)
  if (diff < 1) return 'Aujourd\'hui'
  if (diff < 2) return 'Hier'
  if (diff < 7) return d.toLocaleDateString('fr-FR', { weekday: 'long' })
  if (diff < 30) return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
}

/** Réinitialiser la sélection */
function resetSelection() {
  selectedIds.value = []
  emit('update:selected', [])
}

/** Définir la sélection */
function setSelection(ids) {
  selectedIds.value = [...ids]
  emit('update:selected', selectedIds.value)
}

/** Marquer un téléchargement comme terminé */
function markDownloadComplete(chapterId) {
  downloadingIds.value.delete(chapterId)
}

// ==========================================================================
//  Watchers
// ==========================================================================

watch(
  () => props.initialSelected,
  (newVal) => {
    if (JSON.stringify(newVal) !== JSON.stringify(selectedIds.value)) {
      selectedIds.value = [...newVal]
    }
  }
)

watch(
  () => props.totalChapters,
  () => {
    // Si le nombre total change, on vérifie la pagination
    if (currentPage.value > totalPages.value) {
      currentPage.value = totalPages.value
    }
  }
)

// ==========================================================================
//  Exposer
// ==========================================================================

defineExpose({
  resetSelection,
  setSelection,
  selectedIds,
  selectedChapters,
  goToPage,
  currentPage,
  markDownloadComplete,
  searchQuery,
  clearSearch,
  toggleSelectAll,
})

// ==========================================================================
//  Styles
// ==========================================================================

</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$list-transition: all var(--transition-fast, 150ms) ease;

// ==========================================================================
//  Conteneur principal
// ==========================================================================

.nexus-chapter-list {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
  max-height: 100%;
}

// ==========================================================================
//  Header
// ==========================================================================

.nexus-chapter-list__header {
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

.nexus-chapter-list__header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nexus-chapter-list__title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
}

.nexus-chapter-list__count {
  color: var(--color-text-muted, #6a7a9a);
  font-weight: var(--font-weight-normal, 400);
}

.nexus-chapter-list__header-right {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

// ==========================================================================
//  Sélection globale
// ==========================================================================

.nexus-chapter-list__select-all {
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  padding: 0.2rem;
  cursor: pointer;
  border-radius: var(--radius-sm, 4px);
  transition: $list-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
  }
}

.nexus-chapter-list__select-all-checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  background: transparent;
  transition: $list-transition;
  font-size: 0.7rem;
  font-weight: var(--font-weight-bold, 700);
  color: transparent;

  &.is-checked {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
  }
}

.nexus-chapter-list__select-all-indeterminate {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary, #b0c0d8);
}

// ==========================================================================
//  Recherche
// ==========================================================================

.nexus-chapter-list__search {
  position: relative;
  display: flex;
  align-items: center;
}

.nexus-chapter-list__search-icon {
  position: absolute;
  left: 0.5rem;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.8rem;
  pointer-events: none;
}

.nexus-chapter-list__search-input {
  padding: 0.2rem 0.5rem 0.2rem 1.8rem;
  font-size: 0.8rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  width: 140px;
  transition: $list-transition;
  outline: none;
  &:focus {
    width: 180px;
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15);
  }
  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.nexus-chapter-list__search-clear {
  position: absolute;
  right: 0.3rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1rem;
  cursor: pointer;
  padding: 0 0.2rem;
  &:hover {
    color: var(--color-text-primary, #e8edf5);
  }
}

// ==========================================================================
//  Tri
// ==========================================================================

.nexus-chapter-list__sort {
  display: flex;
  align-items: center;
  gap: 0.1rem;
}

.nexus-chapter-list__sort-btn,
.nexus-chapter-list__sort-field-btn {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  padding: 0.15rem 0.4rem;
  font-size: 0.75rem;
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  transition: $list-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-border-light, #253254);
  }
}

.nexus-chapter-list__sort-label {
  font-weight: var(--font-weight-medium, 500);
}

.nexus-chapter-list__sort-icon {
  font-size: 0.6rem;
}

.nexus-chapter-list__sort-field-btn {
  font-size: 0.7rem;
}

// ==========================================================================
//  Compteur d'affichage
// ==========================================================================

.nexus-chapter-list__count-display {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  padding: 0.1rem 0.4rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-sm, 4px);
}

// ==========================================================================
//  Body
// ==========================================================================

.nexus-chapter-list__body {
  flex: 1;
  overflow-y: auto;
  min-height: 100px;
}

// ==========================================================================
//  Loading
// ==========================================================================

.nexus-chapter-list__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

// ==========================================================================
//  Empty
// ==========================================================================

.nexus-chapter-list__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  color: var(--color-text-muted, #6a7a9a);
  text-align: center;
}

.nexus-chapter-list__empty-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.nexus-chapter-list__empty-text {
  margin: 0;
  font-size: 0.9rem;
}

// ==========================================================================
//  Items
// ==========================================================================

.nexus-chapter-list__items {
  display: flex;
  flex-direction: column;
  padding: 0.25rem;
}

// ==========================================================================
//  Item
// ==========================================================================

.nexus-chapter-list__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  border-radius: var(--radius-sm, 4px);
  transition: $list-transition;
  cursor: pointer;
  border-left: 2px solid transparent;
  user-select: none;
  min-height: 40px;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }

  &--selected {
    border-left-color: var(--color-primary, #00d4ff);
    background: rgba(0, 212, 255, 0.05);
    &:hover {
      background: rgba(0, 212, 255, 0.08);
    }
  }

  &--disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }

  &--read {
    opacity: 0.6;
    .nexus-chapter-list__item-title {
      text-decoration: line-through;
    }
  }

  &--available {
    .nexus-chapter-list__item-status--unavailable {
      display: none;
    }
  }
}

// ==========================================================================
//  Item - Checkbox
// ==========================================================================

.nexus-chapter-list__item-checkbox {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  input[type="checkbox"] {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
    &:checked + label {
      background: var(--color-primary, #00d4ff);
      border-color: var(--color-primary, #00d4ff);
      &::after {
        content: '✓';
        color: var(--color-text-inverse, #0a0e1a);
        font-size: 0.65rem;
        font-weight: var(--font-weight-bold, 700);
      }
    }
    &:disabled + label {
      opacity: 0.4;
      cursor: not-allowed;
    }
  }
  label {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border: 2px solid var(--color-border, #1a2538);
    border-radius: var(--radius-sm, 4px);
    background: transparent;
    cursor: pointer;
    transition: $list-transition;
    flex-shrink: 0;
    font-size: 0.65rem;
    font-weight: var(--font-weight-bold, 700);
    color: transparent;
    &:hover {
      border-color: var(--color-primary, #00d4ff);
    }
  }
}

// ==========================================================================
//  Item - Numéro
// ==========================================================================

.nexus-chapter-list__item-number {
  flex-shrink: 0;
  font-size: 0.7rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-muted, #6a7a9a);
  min-width: 2rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

// ==========================================================================
//  Item - Titre
// ==========================================================================

.nexus-chapter-list__item-title {
  flex: 1;
  min-width: 0;
  font-size: 0.85rem;
  color: var(--color-text-primary, #e8edf5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

// ==========================================================================
//  Item - Métadonnées
// ==========================================================================

.nexus-chapter-list__item-meta {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-shrink: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-chapter-list__item-date {
  white-space: nowrap;
}

.nexus-chapter-list__item-pages {
  background: var(--color-bg-secondary, #141a2b);
  padding: 0.05rem 0.3rem;
  border-radius: var(--radius-sm, 4px);
}

.nexus-chapter-list__item-language {
  text-transform: uppercase;
  font-size: 0.6rem;
  background: var(--color-bg-secondary, #141a2b);
  padding: 0.05rem 0.3rem;
  border-radius: var(--radius-sm, 4px);
}

.nexus-chapter-list__item-status {
  font-size: 0.6rem;
  padding: 0.05rem 0.3rem;
  border-radius: var(--radius-sm, 4px);
  text-transform: uppercase;

  &--unavailable {
    background: var(--color-error, #f44336);
    color: var(--color-text-inverse, #ffffff);
  }
  &--read {
    background: var(--color-success, #4caf50);
    color: var(--color-text-inverse, #ffffff);
  }
}

// ==========================================================================
//  Item - Actions
// ==========================================================================

.nexus-chapter-list__item-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  opacity: 0.4;
  transition: $list-transition;

  .nexus-chapter-list__item:hover & {
    opacity: 1;
  }
  .nexus-chapter-list__item--selected & {
    opacity: 1;
  }
}

// ==========================================================================
//  Pagination
// ==========================================================================

.nexus-chapter-list__pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
  flex-shrink: 0;
  background: var(--color-bg-secondary, #141a2b);
}

.nexus-chapter-list__pagination-btn {
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
  transition: $list-transition;
  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-primary, #00d4ff);
  }
  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
  &:focus-visible {
    outline: 2px solid var(--color-primary, #00d4ff);
    outline-offset: 2px;
  }
}

.nexus-chapter-list__pagination-info {
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Footer
// ==========================================================================

.nexus-chapter-list__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  border-top: 1px solid var(--color-border, #1a2538);
  flex-shrink: 0;
  gap: 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
  font-size: 0.8rem;
}

.nexus-chapter-list__footer-info {
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-chapter-list__footer-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

// ==========================================================================
//  Support du thème clair
// ==========================================================================

.light-mode {
  .nexus-chapter-list {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-chapter-list__header {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-chapter-list__title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .nexus-chapter-list__search-input {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);
    &:focus {
      border-color: var(--color-primary, #0066cc);
    }
  }

  .nexus-chapter-list__item {
    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
    }
    &--selected {
      background: rgba(0, 102, 204, 0.05);
      &:hover {
        background: rgba(0, 102, 204, 0.08);
      }
    }
    &--selected .nexus-chapter-list__item-title {
      color: var(--color-primary, #0066cc);
    }
  }

  .nexus-chapter-list__item-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .nexus-chapter-list__footer {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-chapter-list__pagination {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }
}
</style>
