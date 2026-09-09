<!-- ==========================================================================
  NexusDL 2.0 - LibraryGrid Component
  Fichier : frontend/src/components/LibraryGrid.vue
  Description : Grille de bibliothèque avec couvertures, filtres, recherche, pagination, actions
  Version : 2.0.0
========================================================================== -->

<template>
  <div class="nexus-library-grid">
    <!-- En-tête avec barre de recherche et filtres -->
    <header class="nexus-library-grid__header">
      <div class="nexus-library-grid__search-section">
        <div class="nexus-library-grid__search-wrapper">
          <span class="nexus-library-grid__search-icon" aria-hidden="true">🔍</span>
          <input
            ref="searchInputRef"
            type="text"
            class="nexus-library-grid__search-input"
            v-model="searchQuery"
            :placeholder="searchPlaceholder || 'Rechercher un titre, un auteur...'"
            @input="onSearchInput"
            aria-label="Rechercher dans la bibliothèque"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="nexus-library-grid__search-clear"
            @click="clearSearch"
            aria-label="Effacer la recherche"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <!-- Filtres -->
        <div class="nexus-library-grid__filters">
          <!-- Filtre par genre -->
          <NexusSelect
            v-if="availableGenres.length > 0"
            v-model="selectedGenre"
            :options="genreOptions"
            placeholder="Genre"
            size="sm"
            clearable
            @change="onFilterChange"
          />

          <!-- Filtre par auteur -->
          <NexusSelect
            v-if="availableAuthors.length > 0"
            v-model="selectedAuthor"
            :options="authorOptions"
            placeholder="Auteur"
            size="sm"
            clearable
            @change="onFilterChange"
          />

          <!-- Filtre par favoris -->
          <NexusSelect
            v-model="favoriteFilter"
            :options="favoriteOptions"
            placeholder="Favoris"
            size="sm"
            clearable
            @change="onFilterChange"
          />

          <!-- Filtre par note -->
          <NexusSelect
            v-model="ratingFilter"
            :options="ratingOptions"
            placeholder="Note"
            size="sm"
            clearable
            @change="onFilterChange"
          />
        </div>
      </div>

      <div class="nexus-library-grid__actions">
        <!-- Vue Grille / Liste -->
        <div class="nexus-library-grid__view-toggle">
          <button
            type="button"
            class="nexus-library-grid__view-btn"
            :class="{ 'nexus-library-grid__view-btn--active': viewMode === 'grid' }"
            @click="setViewMode('grid')"
            aria-label="Vue en grille"
            title="Vue en grille"
          >
            <span aria-hidden="true">⊞</span>
          </button>
          <button
            type="button"
            class="nexus-library-grid__view-btn"
            :class="{ 'nexus-library-grid__view-btn--active': viewMode === 'list' }"
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
          class="nexus-library-grid__refresh-btn"
          @click="refresh"
          :disabled="loading"
          aria-label="Rafraîchir la bibliothèque"
        >
          <span v-if="loading" class="nexus-library-grid__refresh-spinner" aria-hidden="true">⟳</span>
          <span v-else aria-hidden="true">↻</span>
        </button>
      </div>
    </header>

    <!-- Statistiques rapides -->
    <div v-if="showStats && totalItems > 0" class="nexus-library-grid__stats">
      <span class="nexus-library-grid__stats-item">
        <span class="nexus-library-grid__stats-value">{{ totalItems }}</span>
        <span class="nexus-library-grid__stats-label">éléments</span>
      </span>
      <span v-if="favoriteCount > 0" class="nexus-library-grid__stats-item">
        <span class="nexus-library-grid__stats-value">{{ favoriteCount }}</span>
        <span class="nexus-library-grid__stats-label">favoris ❤️</span>
      </span>
      <span v-if="totalSize" class="nexus-library-grid__stats-item">
        <span class="nexus-library-grid__stats-value">{{ totalSize }}</span>
        <span class="nexus-library-grid__stats-label">espace utilisé</span>
      </span>
    </div>

    <!-- Corps de la grille -->
    <div class="nexus-library-grid__body">
      <!-- État de chargement -->
      <div v-if="loading" class="nexus-library-grid__loading">
        <NexusSpinner size="lg" label="Chargement de la bibliothèque..." />
      </div>

      <!-- État vide -->
      <div v-else-if="filteredItems.length === 0" class="nexus-library-grid__empty">
        <slot name="empty">
          <span class="nexus-library-grid__empty-icon">📭</span>
          <p class="nexus-library-grid__empty-text">
            {{ searchQuery || hasActiveFilters ? 'Aucun résultat pour votre recherche' : 'Votre bibliothèque est vide' }}
          </p>
          <p v-if="!searchQuery && !hasActiveFilters" class="nexus-library-grid__empty-hint">
            Téléchargez des séries pour les voir apparaître ici
          </p>
          <button
            v-if="searchQuery || hasActiveFilters"
            type="button"
            class="nexus-library-grid__empty-reset"
            @click="resetFilters"
          >
            Réinitialiser les filtres
          </button>
        </slot>
      </div>

      <!-- Grille / Liste -->
      <template v-else>
        <div
          class="nexus-library-grid__items"
          :class="{
            'nexus-library-grid__items--grid': viewMode === 'grid',
            'nexus-library-grid__items--list': viewMode === 'list',
          }"
        >
          <div
            v-for="item in paginatedItems"
            :key="item.id"
            class="nexus-library-grid__item"
            :class="{
              'nexus-library-grid__item--selected': selectedIds.includes(item.id),
            }"
            @click="handleItemClick(item)"
          >
            <!-- Mode grille : utilisant NexusCard -->
            <NexusCard
              v-if="viewMode === 'grid'"
              class="nexus-library-grid__card"
              :class="{ 'nexus-library-grid__card--favorite': item.is_favorite }"
              hoverable
              @click.stop="handleCardClick(item)"
            >
              <!-- Couverture -->
              <template #media>
                <div class="nexus-library-grid__cover-wrapper">
                  <img
                    v-if="getCover(item)"
                    :src="getCover(item)"
                    :alt="`Couverture de ${item.title}`"
                    class="nexus-library-grid__cover"
                    loading="lazy"
                    @error="handleCoverError(item)"
                  />
                  <div v-else class="nexus-library-grid__cover-placeholder">
                    <span class="nexus-library-grid__cover-placeholder-icon">📖</span>
                  </div>
                  <!-- Badge favori -->
                  <span v-if="item.is_favorite" class="nexus-library-grid__favorite-badge" aria-hidden="true">❤️</span>
                  <!-- Note -->
                  <span v-if="item.rating > 0" class="nexus-library-grid__rating-badge">
                    ⭐ {{ item.rating }}
                  </span>
                </div>
              </template>

              <!-- Header : titre -->
              <template #header>
                <div class="nexus-library-grid__card-header">
                  <h3 class="nexus-library-grid__card-title" :title="item.title">
                    {{ truncate(item.title, 40) }}
                  </h3>
                  <span v-if="item.metadata?.year" class="nexus-library-grid__card-year">
                    {{ item.metadata.year }}
                  </span>
                </div>
                <div v-if="item.metadata?.author" class="nexus-library-grid__card-author">
                  {{ truncate(item.metadata.author, 30) }}
                </div>
              </template>

              <!-- Body : métadonnées -->
              <div class="nexus-library-grid__card-body">
                <div v-if="item.metadata?.genre" class="nexus-library-grid__card-genres">
                  <span
                    v-for="g in getGenres(item.metadata.genre)"
                    :key="g"
                    class="nexus-library-grid__card-genre"
                  >
                    {{ g }}
                  </span>
                </div>
                <div class="nexus-library-grid__card-meta">
                  <span class="nexus-library-grid__card-pages">
                    {{ item.metadata?.pages || '?' }} pages
                  </span>
                  <span class="nexus-library-grid__card-size">
                    {{ item.size_formatted || formatFileSize(item.size_bytes) }}
                  </span>
                  <span v-if="item.read_count > 0" class="nexus-library-grid__card-reads">
                    📖 {{ item.read_count }}
                  </span>
                </div>
              </div>

              <!-- Footer : actions -->
              <template #footer>
                <div class="nexus-library-grid__card-actions">
                  <button
                    type="button"
                    class="nexus-library-grid__card-action"
                    @click.stop="toggleFavorite(item)"
                    :aria-label="item.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'"
                  >
                    <span aria-hidden="true">{{ item.is_favorite ? '❤️' : '🤍' }}</span>
                  </button>
                  <button
                    type="button"
                    class="nexus-library-grid__card-action"
                    @click.stop="openReader(item)"
                    aria-label="Lire"
                  >
                    <span aria-hidden="true">📖</span>
                  </button>
                  <button
                    type="button"
                    class="nexus-library-grid__card-action"
                    @click.stop="deleteItem(item)"
                    aria-label="Supprimer"
                  >
                    <span aria-hidden="true">🗑️</span>
                  </button>
                </div>
              </template>
            </NexusCard>

            <!-- Mode liste : affichage en lignes -->
            <div v-else class="nexus-library-grid__list-item" @click.stop="handleCardClick(item)">
              <div class="nexus-library-grid__list-cover-wrapper">
                <img
                  v-if="getCover(item)"
                  :src="getCover(item)"
                  :alt="`Couverture de ${item.title}`"
                  class="nexus-library-grid__list-cover"
                  loading="lazy"
                  @error="handleCoverError(item)"
                />
                <div v-else class="nexus-library-grid__list-cover-placeholder">
                  <span>📖</span>
                </div>
              </div>
              <div class="nexus-library-grid__list-info">
                <div class="nexus-library-grid__list-header">
                  <h3 class="nexus-library-grid__list-title" :title="item.title">
                    {{ item.title }}
                  </h3>
                  <span v-if="item.is_favorite" class="nexus-library-grid__list-fav" aria-hidden="true">❤️</span>
                  <span v-if="item.rating > 0" class="nexus-library-grid__list-rating">⭐ {{ item.rating }}</span>
                </div>
                <div class="nexus-library-grid__list-meta">
                  <span v-if="item.metadata?.author" class="nexus-library-grid__list-author">
                    {{ item.metadata.author }}
                  </span>
                  <span v-if="item.metadata?.genre" class="nexus-library-grid__list-genres">
                    {{ getGenres(item.metadata.genre).join(', ') }}
                  </span>
                  <span class="nexus-library-grid__list-size">
                    {{ item.size_formatted || formatFileSize(item.size_bytes) }}
                  </span>
                  <span v-if="item.metadata?.pages" class="nexus-library-grid__list-pages">
                    {{ item.metadata.pages }}p
                  </span>
                </div>
              </div>
              <div class="nexus-library-grid__list-actions">
                <button
                  type="button"
                  class="nexus-library-grid__list-action"
                  @click.stop="toggleFavorite(item)"
                  :aria-label="item.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'"
                >
                  <span aria-hidden="true">{{ item.is_favorite ? '❤️' : '🤍' }}</span>
                </button>
                <button
                  type="button"
                  class="nexus-library-grid__list-action"
                  @click.stop="openReader(item)"
                  aria-label="Lire"
                >
                  <span aria-hidden="true">📖</span>
                </button>
                <button
                  type="button"
                  class="nexus-library-grid__list-action nexus-library-grid__list-action--danger"
                  @click.stop="deleteItem(item)"
                  aria-label="Supprimer"
                >
                  <span aria-hidden="true">🗑️</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="showPagination && totalFiltered > pageSize" class="nexus-library-grid__pagination">
          <button
            type="button"
            class="nexus-library-grid__pagination-btn"
            :disabled="currentPage <= 1"
            @click="prevPage"
          >
            ◀
          </button>
          <span class="nexus-library-grid__pagination-info">
            {{ currentPage }} / {{ totalPages }}
          </span>
          <button
            type="button"
            class="nexus-library-grid__pagination-btn"
            :disabled="currentPage >= totalPages"
            @click="nextPage"
          >
            ▶
          </button>
          <span class="nexus-library-grid__pagination-count">
            {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, totalFiltered) }} / {{ totalFiltered }}
          </span>
        </div>
      </template>
    </div>

    <!-- Pied de page : sélection et actions -->
    <footer v-if="showFooter && selectedIds.length > 0" class="nexus-library-grid__footer">
      <span class="nexus-library-grid__footer-info">
        {{ selectedIds.length }} élément(s) sélectionné(s)
      </span>
      <div class="nexus-library-grid__footer-actions">
        <button
          type="button"
          class="nexus-library-grid__footer-action"
          @click="deleteSelected"
          :disabled="deleting"
        >
          🗑️ Supprimer
        </button>
        <button
          type="button"
          class="nexus-library-grid__footer-action"
          @click="toggleFavoriteSelected"
        >
          ❤️ Favoris
        </button>
        <button
          type="button"
          class="nexus-library-grid__footer-action"
          @click="clearSelection"
        >
          Désélectionner
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import NexusCard from './common/NexusCard.vue'
import NexusSpinner from './common/NexusSpinner.vue'
import NexusSelect from './common/NexusSelect.vue'
import { formatFileSize, truncate } from '@/utils/formatters'
import { useToast } from '@/composables/useToast'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Liste des éléments de la bibliothèque */
  items: {
    type: Array,
    default: () => [],
  },
  /** Indicateur de chargement */
  loading: {
    type: Boolean,
    default: false,
  },
  /** Nombre total d'éléments (pour la pagination) */
  totalItems: {
    type: Number,
    default: 0,
  },
  /** Taille totale formatée (statistiques) */
  totalSize: {
    type: String,
    default: '',
  },
  /** Nombre de favoris */
  favoriteCount: {
    type: Number,
    default: 0,
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
  /** Afficher la pagination */
  showPagination: {
    type: Boolean,
    default: true,
  },
  /** Afficher les statistiques */
  showStats: {
    type: Boolean,
    default: true,
  },
  /** Afficher le footer de sélection */
  showFooter: {
    type: Boolean,
    default: true,
  },
  /** Placeholder de recherche */
  searchPlaceholder: {
    type: String,
    default: '',
  },
  /** URL de base pour l'API (pour les couvertures) */
  apiBase: {
    type: String,
    default: '/api',
  },
  /** Mode grille par défaut */
  defaultView: {
    type: String,
    default: 'grid',
    validator: (val) => ['grid', 'list'].includes(val),
  },
  /** Afficher les genres disponibles (pour filtres) */
  availableGenres: {
    type: Array,
    default: () => [],
  },
  /** Afficher les auteurs disponibles (pour filtres) */
  availableAuthors: {
    type: Array,
    default: () => [],
  },
})

// ==========================================================================
//  Émits
// ==========================================================================

const emit = defineEmits([
  'fetch',
  'search',
  'filter',
  'page-change',
  'item-click',
  'item-delete',
  'item-favorite',
  'item-rating',
  'cover-error',
  'view-change',
  'refresh',
  'delete-selected',
  'favorite-selected',
])

// ==========================================================================
//  Composables
// ==========================================================================

const toast = useToast()

// ==========================================================================
//  État local
// ==========================================================================

const searchQuery = ref('')
const selectedGenre = ref('')
const selectedAuthor = ref('')
const favoriteFilter = ref('')
const ratingFilter = ref('')
const viewMode = ref(props.defaultView)
const currentPage = ref(props.initialPage)
const selectedIds = ref([])
const deleting = ref(false)
const searchInputRef = ref(null)

// Cache des couvertures
const coverCache = ref({})
const coverErrors = ref(new Set())

// ==========================================================================
//  Computed
// ==========================================================================

/** Éléments filtrés localement (si les filtres sont appliqués côté client) */
const filteredItems = computed(() => {
  let result = [...props.items]

  // Recherche
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter(item =>
      item.title.toLowerCase().includes(q) ||
      (item.metadata?.author && item.metadata.author.toLowerCase().includes(q)) ||
      (item.metadata?.series && item.metadata.series.toLowerCase().includes(q))
    )
  }

  // Genre
  if (selectedGenre.value) {
    result = result.filter(item =>
      item.metadata?.genre && item.metadata.genre.toLowerCase().includes(selectedGenre.value.toLowerCase())
    )
  }

  // Auteur
  if (selectedAuthor.value) {
    result = result.filter(item =>
      item.metadata?.author && item.metadata.author.toLowerCase().includes(selectedAuthor.value.toLowerCase())
    )
  }

  // Favoris
  if (favoriteFilter.value === 'true') {
    result = result.filter(item => item.is_favorite)
  } else if (favoriteFilter.value === 'false') {
    result = result.filter(item => !item.is_favorite)
  }

  // Note
  if (ratingFilter.value) {
    const minRating = parseInt(ratingFilter.value)
    result = result.filter(item => item.rating >= minRating)
  }

  return result
})

/** Nombre total après filtrage */
const totalFiltered = computed(() => filteredItems.value.length)

/** Éléments paginés */
const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * props.pageSize
  const end = start + props.pageSize
  return filteredItems.value.slice(start, end)
})

/** Nombre total de pages */
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(totalFiltered.value / props.pageSize))
})

/** Y a-t-il des filtres actifs ? */
const hasActiveFilters = computed(() => {
  return !!selectedGenre.value || !!selectedAuthor.value || !!favoriteFilter.value || !!ratingFilter.value
})

// ==========================================================================
//  Options pour les selects
// ==========================================================================

const genreOptions = computed(() => {
  return props.availableGenres.map(g => ({ value: g, label: g }))
})

const authorOptions = computed(() => {
  return props.availableAuthors.map(a => ({ value: a, label: a }))
})

const favoriteOptions = [
  { value: 'true', label: '❤️ Favoris uniquement' },
  { value: 'false', label: '💔 Non favoris' },
]

const ratingOptions = [
  { value: '1', label: '⭐ 1+ étoiles' },
  { value: '2', label: '⭐⭐ 2+ étoiles' },
  { value: '3', label: '⭐⭐⭐ 3+ étoiles' },
  { value: '4', label: '⭐⭐⭐⭐ 4+ étoiles' },
  { value: '5', label: '⭐⭐⭐⭐⭐ 5+ étoiles' },
]

// ==========================================================================
//  Méthodes
// ==========================================================================

/** Récupère l'URL de la couverture (depuis le cache ou l'API) */
function getCover(item) {
  if (item.cover_path) return item.cover_path
  // Si on a déjà une URL dans le cache, la retourner
  if (coverCache.value[item.id]) return coverCache.value[item.id]
  // Sinon, on pourrait générer une URL via l'API, mais on laisse le parent gérer
  return null
}

/** Gestion d'erreur de chargement de couverture */
function handleCoverError(item) {
  coverErrors.value.add(item.id)
  emit('cover-error', item)
}

/** Extraire les genres d'une chaîne */
function getGenres(genreStr) {
  if (!genreStr) return []
  return genreStr.split(',').map(g => g.trim()).filter(Boolean)
}

/** Gestion de la recherche (avec debounce) */
let searchTimeout = null
function onSearchInput() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    emit('search', searchQuery.value)
  }, 300)
}

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

/** Gestion des filtres */
function onFilterChange() {
  currentPage.value = 1
  emit('filter', {
    genre: selectedGenre.value,
    author: selectedAuthor.value,
    favorite: favoriteFilter.value,
    rating: ratingFilter.value,
  })
}

/** Réinitialiser les filtres */
function resetFilters() {
  selectedGenre.value = ''
  selectedAuthor.value = ''
  favoriteFilter.value = ''
  ratingFilter.value = ''
  searchQuery.value = ''
  currentPage.value = 1
  emit('filter', {
    genre: '',
    author: '',
    favorite: '',
    rating: '',
  })
  emit('search', '')
}

/** Changement de vue */
function setViewMode(mode) {
  viewMode.value = mode
  emit('view-change', mode)
}

/** Pagination */
function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    emit('page-change', currentPage.value)
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

function scrollToTop() {
  const el = document.querySelector('.nexus-library-grid__items')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

/** Rafraîchir */
function refresh() {
  emit('refresh')
}

/** Gestion du clic sur un item (sélection pour actions) */
function handleItemClick(item) {
  const idx = selectedIds.value.indexOf(item.id)
  if (idx === -1) {
    selectedIds.value.push(item.id)
  } else {
    selectedIds.value.splice(idx, 1)
  }
  emit('item-click', item)
}

/** Gestion du clic sur la carte (ouvrir le détail/lecture) */
function handleCardClick(item) {
  openReader(item)
}

/** Ouvrir le lecteur */
function openReader(item) {
  // Le parent doit gérer la navigation
  emit('item-click', item, { action: 'read' })
}

/** Bascule favori */
async function toggleFavorite(item) {
  const newState = !item.is_favorite
  emit('item-favorite', item, newState)
}

/** Supprimer un élément */
async function deleteItem(item) {
  if (!confirm(`Supprimer définitivement "${item.title}" ?`)) return
  emit('item-delete', item)
}

/** Supprimer les éléments sélectionnés */
async function deleteSelected() {
  if (selectedIds.value.length === 0) return
  if (!confirm(`Supprimer ${selectedIds.value.length} élément(s) ?`)) return
  deleting.value = true
  try {
    const ids = [...selectedIds.value]
    emit('delete-selected', ids)
    // Le parent doit mettre à jour la liste
    selectedIds.value = []
  } finally {
    deleting.value = false
  }
}

/** Bascule favori pour la sélection */
function toggleFavoriteSelected() {
  if (selectedIds.value.length === 0) return
  emit('favorite-selected', selectedIds.value)
}

/** Effacer la sélection */
function clearSelection() {
  selectedIds.value = []
}

// ==========================================================================
//  Watchers
// ==========================================================================

watch(
  () => props.items,
  () => {
    // Réinitialiser les erreurs de couverture si les items changent
    coverErrors.value.clear()
  },
  { deep: true }
)

// ==========================================================================
//  Exposer
// ==========================================================================

defineExpose({
  refresh,
  resetFilters,
  clearSelection,
  selectedIds,
  currentPage,
  viewMode,
  searchQuery,
  setSearch: (query) => {
    searchQuery.value = query
    onSearchInput()
  },
  setViewMode,
})

// ==========================================================================
//  Styles
// ==========================================================================

</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$library-transition: all var(--transition-fast, 150ms) ease;
$library-radius: var(--radius-md, 8px);
$grid-gap: 1rem;

// ==========================================================================
//  Conteneur principal
// ==========================================================================

.nexus-library-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
  max-width: 100%;
  min-height: 300px;
}

// ==========================================================================
//  Header
// ==========================================================================

.nexus-library-grid__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
}

.nexus-library-grid__search-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  min-width: 200px;
}

.nexus-library-grid__search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 150px;
}

.nexus-library-grid__search-icon {
  position: absolute;
  left: 0.5rem;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.8rem;
  pointer-events: none;
}

.nexus-library-grid__search-input {
  width: 100%;
  padding: 0.3rem 0.5rem 0.3rem 1.8rem;
  font-size: 0.85rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  transition: $library-transition;
  &:focus {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15);
  }
  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.nexus-library-grid__search-clear {
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

.nexus-library-grid__filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  flex: 1;
  min-width: 150px;
  .nexus-select-wrapper {
    min-width: 100px;
    max-width: 150px;
  }
}

// ==========================================================================
//  Actions
// ==========================================================================

.nexus-library-grid__actions {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-shrink: 0;
}

.nexus-library-grid__view-toggle {
  display: flex;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  overflow: hidden;
}

.nexus-library-grid__view-btn {
  padding: 0.2rem 0.5rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1rem;
  transition: $library-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
  &--active {
    background: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
    &:hover {
      background: var(--color-primary-dark, #0099cc);
    }
  }
}

.nexus-library-grid__refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  transition: $library-transition;
  font-size: 1.2rem;
  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

.nexus-library-grid__refresh-spinner {
  display: inline-block;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// ==========================================================================
//  Stats
// ==========================================================================

.nexus-library-grid__stats {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  padding: 0.3rem 0.75rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.nexus-library-grid__stats-item {
  display: flex;
  align-items: baseline;
  gap: 0.2rem;
}

.nexus-library-grid__stats-value {
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
}

.nexus-library-grid__stats-label {
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.7rem;
}

// ==========================================================================
//  Body
// ==========================================================================

.nexus-library-grid__body {
  flex: 1;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

// ==========================================================================
//  Loading / Empty
// ==========================================================================

.nexus-library-grid__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  flex: 1;
}

.nexus-library-grid__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: var(--color-text-muted, #6a7a9a);
  text-align: center;
  flex: 1;
}

.nexus-library-grid__empty-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.nexus-library-grid__empty-text {
  margin: 0;
  font-size: 1rem;
  font-weight: var(--font-weight-medium, 500);
}

.nexus-library-grid__empty-hint {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  opacity: 0.7;
}

.nexus-library-grid__empty-reset {
  margin-top: 1rem;
  padding: 0.4rem 1rem;
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
  border: none;
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  font-weight: var(--font-weight-medium, 500);
  transition: $library-transition;
  &:hover {
    background: var(--color-primary-dark, #0099cc);
  }
}

// ==========================================================================
//  Items (Grille)
// ==========================================================================

.nexus-library-grid__items {
  display: grid;
  gap: $grid-gap;
  padding: 0.25rem;

  &--grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }

  &--list {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
}

.nexus-library-grid__item {
  transition: $library-transition;
  &--selected {
    outline: 2px solid var(--color-primary, #00d4ff);
    outline-offset: 2px;
    border-radius: var(--radius-md, 8px);
  }
}

// ==========================================================================
//  Carte (mode grille)
// ==========================================================================

.nexus-library-grid__card {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
  transition: $library-transition;
  cursor: pointer;

  &:hover {
    border-color: var(--color-primary, #00d4ff);
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg, 0 8px 24px rgba(0,0,0,0.5));
  }

  &--favorite {
    border-color: rgba(255, 0, 0, 0.3);
  }
}

.nexus-library-grid__cover-wrapper {
  position: relative;
  aspect-ratio: 2/3;
  background: var(--color-bg-secondary, #141a2b);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nexus-library-grid__cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
  .nexus-library-grid__card:hover & {
    transform: scale(1.02);
  }
}

.nexus-library-grid__cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 3rem;
  color: var(--color-text-muted, #6a7a9a);
  background: var(--color-bg-secondary, #141a2b);
}

.nexus-library-grid__favorite-badge {
  position: absolute;
  top: 0.3rem;
  right: 0.3rem;
  font-size: 1rem;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
}

.nexus-library-grid__rating-badge {
  position: absolute;
  bottom: 0.3rem;
  right: 0.3rem;
  padding: 0.1rem 0.4rem;
  font-size: 0.6rem;
  background: rgba(0, 0, 0, 0.7);
  color: #ffc107;
  border-radius: var(--radius-sm, 4px);
  backdrop-filter: blur(4px);
}

// ==========================================================================
//  Card - Header
// ==========================================================================

.nexus-library-grid__card-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.3rem;
}

.nexus-library-grid__card-title {
  margin: 0;
  font-size: 0.85rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nexus-library-grid__card-year {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  flex-shrink: 0;
}

.nexus-library-grid__card-author {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  margin-top: 0.1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

// ==========================================================================
//  Card - Body
// ==========================================================================

.nexus-library-grid__card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding: 0.2rem 0;
}

.nexus-library-grid__card-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem;
}

.nexus-library-grid__card-genre {
  font-size: 0.6rem;
  padding: 0.05rem 0.4rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-muted, #6a7a9a);
  text-transform: lowercase;
  white-space: nowrap;
}

.nexus-library-grid__card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  font-size: 0.6rem;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-library-grid__card-pages,
.nexus-library-grid__card-size,
.nexus-library-grid__card-reads {
  display: inline-flex;
  align-items: center;
  gap: 0.1rem;
}

// ==========================================================================
//  Card - Footer (actions)
// ==========================================================================

.nexus-library-grid__card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.3rem;
  padding-top: 0.3rem;
  border-top: 1px solid var(--color-border, #1a2538);
}

.nexus-library-grid__card-action {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1rem;
  padding: 0.1rem 0.3rem;
  border-radius: var(--radius-sm, 4px);
  transition: $library-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
  &:focus-visible {
    outline: 2px solid var(--color-primary, #00d4ff);
    outline-offset: 2px;
  }
}

// ==========================================================================
//  Liste (mode liste)
// ==========================================================================

.nexus-library-grid__list-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: $library-transition;

  &:hover {
    border-color: var(--color-primary, #00d4ff);
    background: var(--color-bg-hover, #253254);
  }
}

.nexus-library-grid__list-cover-wrapper {
  flex-shrink: 0;
  width: 50px;
  height: 75px;
  border-radius: var(--radius-sm, 4px);
  overflow: hidden;
  background: var(--color-bg-secondary, #141a2b);
  display: flex;
  align-items: center;
  justify-content: center;
}

.nexus-library-grid__list-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.nexus-library-grid__list-cover-placeholder {
  font-size: 1.5rem;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-library-grid__list-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.nexus-library-grid__list-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.nexus-library-grid__list-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nexus-library-grid__list-fav {
  color: #ff6b6b;
  font-size: 0.8rem;
}

.nexus-library-grid__list-rating {
  font-size: 0.7rem;
  color: #ffc107;
}

.nexus-library-grid__list-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-library-grid__list-author {
  font-weight: var(--font-weight-medium, 500);
  color: var(--color-text-secondary, #b0c0d8);
}

.nexus-library-grid__list-genres {
  &::before { content: '•'; margin-right: 0.2rem; }
}

.nexus-library-grid__list-actions {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  flex-shrink: 0;
}

.nexus-library-grid__list-action {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1rem;
  padding: 0.2rem 0.4rem;
  border-radius: var(--radius-sm, 4px);
  transition: $library-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }
  &--danger:hover {
    color: var(--color-error, #f44336);
  }
}

// ==========================================================================
//  Pagination
// ==========================================================================

.nexus-library-grid__pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem;
  margin-top: 0.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
}

.nexus-library-grid__pagination-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  transition: $library-transition;
  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-primary, #00d4ff);
  }
  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
}

.nexus-library-grid__pagination-info {
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-library-grid__pagination-count {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  margin-left: 0.5rem;
}

// ==========================================================================
//  Footer
// ==========================================================================

.nexus-library-grid__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  font-size: 0.8rem;
  gap: 0.5rem;
}

.nexus-library-grid__footer-info {
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-library-grid__footer-actions {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.nexus-library-grid__footer-action {
  padding: 0.2rem 0.6rem;
  font-size: 0.75rem;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  transition: $library-transition;
  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-primary, #00d4ff);
  }
  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

// ==========================================================================
//  Support du thème clair
// ==========================================================================

.light-mode {
  .nexus-library-grid__header {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-library-grid__search-input {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);
    &:focus {
      border-color: var(--color-primary, #0066cc);
    }
    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .nexus-library-grid__stats {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
    .nexus-library-grid__stats-value {
      color: var(--color-text-primary, #1a1a2e);
    }
  }

  .nexus-library-grid__card {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    &:hover {
      border-color: var(--color-primary, #0066cc);
    }
    .nexus-library-grid__card-title {
      color: var(--color-text-primary, #1a1a2e);
    }
    .nexus-library-grid__card-author {
      color: var(--color-text-muted, #7a8a9a);
    }
    .nexus-library-grid__card-actions {
      border-color: var(--color-border, #d0d8e0);
    }
  }

  .nexus-library-grid__list-item {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
    }
    .nexus-library-grid__list-title {
      color: var(--color-text-primary, #1a1a2e);
    }
  }

  .nexus-library-grid__pagination {
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-library-grid__footer {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .nexus-library-grid__view-btn {
    &--active {
      background: var(--color-primary, #0066cc);
      color: var(--color-text-inverse, #ffffff);
      &:hover {
        background: var(--color-primary-dark, #004d99);
      }
    }
  }
}
</style>
