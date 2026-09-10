<!-- ==========================================================================
  NexusDL 2.0 - Library View (version complète)
  Fichier : frontend/src/views/LibraryView.vue
  Description : Vue principale de la bibliothèque NexusDL. Affiche la grille
                des œuvres téléchargées avec recherche, filtres, tri, pagination,
                statistiques, actions groupées et import de fichiers CBZ.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="library-view">
    <!-- ====================================================================
      EN-TÊTE
    ==================================================================== -->
    <header class="library-view__header">
      <div class="library-view__header-left">
        <h1 class="library-view__title">
          <span aria-hidden="true">📚</span>
          Ma Bibliothèque
        </h1>
        <p class="library-view__subtitle">
          Retrouvez tous vos scans téléchargés
        </p>
      </div>

      <div class="library-view__header-right">
        <!-- Rafraîchir -->
        <button
          type="button"
          class="library-view__btn library-view__btn--refresh"
          :disabled="loading"
          @click="refreshLibrary"
          aria-label="Rafraîchir la bibliothèque"
          title="Rafraîchir"
        >
          <span v-if="loading" class="library-view__spinner" aria-hidden="true">⟳</span>
          <span v-else aria-hidden="true">↻</span>
          Rafraîchir
        </button>

        <!-- Importer un CBZ -->
        <button
          type="button"
          class="library-view__btn library-view__btn--import"
          :disabled="importing"
          @click="triggerFileInput"
          aria-label="Importer un fichier CBZ"
          title="Importer un fichier CBZ"
        >
          <span v-if="importing" class="library-view__spinner" aria-hidden="true">⟳</span>
          <span v-else aria-hidden="true">📥</span>
          {{ importing ? 'Import...' : 'Importer' }}
        </button>

        <!-- Input fichier caché -->
        <input
          ref="fileInputRef"
          type="file"
          accept=".cbz,application/zip"
          class="library-view__file-input"
          @change="handleFileImport"
          multiple
        />

        <!-- Exporter -->
        <button
          type="button"
          class="library-view__btn library-view__btn--export"
          :disabled="totalItems === 0"
          @click="exportLibrary"
          aria-label="Exporter les métadonnées"
          title="Exporter les métadonnées (JSON)"
        >
          <span aria-hidden="true">📤</span>
          Exporter
        </button>

        <!-- Vue grille / liste -->
        <div class="library-view__view-toggle">
          <button
            type="button"
            class="library-view__view-btn"
            :class="{ 'library-view__view-btn--active': viewMode === 'grid' }"
            @click="setViewMode('grid')"
            aria-label="Vue en grille"
            title="Vue en grille"
          >
            <span aria-hidden="true">⊞</span>
          </button>
          <button
            type="button"
            class="library-view__view-btn"
            :class="{ 'library-view__view-btn--active': viewMode === 'list' }"
            @click="setViewMode('list')"
            aria-label="Vue en liste"
            title="Vue en liste"
          >
            <span aria-hidden="true">☰</span>
          </button>
        </div>
      </div>
    </header>

    <!-- ====================================================================
      BARRE D'ERREUR
    ==================================================================== -->
    <div v-if="error" class="library-view__error" role="alert">
      <span class="library-view__error-icon" aria-hidden="true">❌</span>
      <span class="library-view__error-text">{{ error }}</span>
      <button
        type="button"
        class="library-view__error-close"
        @click="error = null"
        aria-label="Fermer"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>

    <!-- ====================================================================
      STATISTIQUES
    ==================================================================== -->
    <div v-if="showStats && totalItems > 0" class="library-view__stats">
      <div class="library-view__stat">
        <span class="library-view__stat-value">{{ totalItems }}</span>
        <span class="library-view__stat-label">Éléments</span>
      </div>
      <div v-if="stats?.total_size_formatted" class="library-view__stat">
        <span class="library-view__stat-value">{{ stats.total_size_formatted }}</span>
        <span class="library-view__stat-label">Taille totale</span>
      </div>
      <div v-if="stats?.favorites_count" class="library-view__stat library-view__stat--favorite">
        <span class="library-view__stat-value">{{ stats.favorites_count }}</span>
        <span class="library-view__stat-label">Favoris ❤️</span>
      </div>
      <div v-if="stats?.authors?.length" class="library-view__stat">
        <span class="library-view__stat-value">{{ stats.authors.length }}</span>
        <span class="library-view__stat-label">Auteurs</span>
      </div>
      <div v-if="stats?.genres?.length" class="library-view__stat">
        <span class="library-view__stat-value">{{ stats.genres.length }}</span>
        <span class="library-view__stat-label">Genres</span>
      </div>
      <div v-if="filteredCount !== totalItems" class="library-view__stat library-view__stat--filtered">
        <span class="library-view__stat-value">{{ filteredCount }}</span>
        <span class="library-view__stat-label">Affichés</span>
      </div>
    </div>

    <!-- ====================================================================
      BARRE DE RECHERCHE ET FILTRES
    ==================================================================== -->
    <div class="library-view__toolbar">
      <!-- Recherche -->
      <div class="library-view__search-wrapper">
        <span class="library-view__search-icon" aria-hidden="true">🔍</span>
        <input
          ref="searchInputRef"
          type="text"
          class="library-view__search-input"
          v-model="searchQuery"
          placeholder="Rechercher un titre, un auteur, une série..."
          aria-label="Rechercher dans la bibliothèque"
          @input="onSearchInput"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="library-view__search-clear"
          @click="clearSearch"
          aria-label="Effacer la recherche"
        >
          <span aria-hidden="true">&times;</span>
        </button>
      </div>

      <!-- Filtres -->
      <div class="library-view__filters">
        <select
          v-model="genreFilter"
          class="library-view__select"
          aria-label="Filtrer par genre"
          :disabled="!stats?.genres?.length"
        >
          <option value="">Tous les genres</option>
          <option v-for="g in stats?.genres || []" :key="g" :value="g">{{ g }}</option>
        </select>

        <select
          v-model="authorFilter"
          class="library-view__select"
          aria-label="Filtrer par auteur"
          :disabled="!stats?.authors?.length"
        >
          <option value="">Tous les auteurs</option>
          <option v-for="a in stats?.authors || []" :key="a" :value="a">{{ a }}</option>
        </select>

        <button
          type="button"
          class="library-view__filter-btn"
          :class="{ 'library-view__filter-btn--active': favoriteFilter }"
          @click="toggleFavoriteFilter"
          :aria-pressed="favoriteFilter"
          title="Favoris uniquement"
        >
          ❤️ Favoris
        </button>

        <select
          v-model="sortBy"
          class="library-view__select"
          aria-label="Trier les éléments"
        >
          <option value="created_at-desc">Plus récents</option>
          <option value="created_at-asc">Plus anciens</option>
          <option value="title-asc">Titre (A-Z)</option>
          <option value="title-desc">Titre (Z-A)</option>
          <option value="size-desc">Taille (grande)</option>
          <option value="size-asc">Taille (petite)</option>
          <option value="rating-desc">Note (élevée)</option>
          <option value="last_read-desc">Dernière lecture</option>
        </select>

        <button
          v-if="hasActiveFilters"
          type="button"
          class="library-view__filter-reset"
          @click="resetFilters"
          aria-label="Réinitialiser les filtres"
          title="Réinitialiser les filtres"
        >
          ✖ Réinitialiser
        </button>
      </div>
    </div>

    <!-- ====================================================================
      BARRE D'ACTIONS GROUPÉES
    ==================================================================== -->
    <Transition name="library-view-slide">
      <div v-if="selectedIds.length > 0" class="library-view__bulk-actions">
        <span class="library-view__bulk-info">
          {{ selectedIds.length }} élément(s) sélectionné(s)
        </span>
        <div class="library-view__bulk-buttons">
          <button
            type="button"
            class="library-view__bulk-btn library-view__bulk-btn--favorite"
            @click="bulkToggleFavorite"
            :disabled="bulkLoading"
          >
            ❤️ Favoris
          </button>
          <button
            type="button"
            class="library-view__bulk-btn library-view__bulk-btn--danger"
            @click="bulkDelete"
            :disabled="bulkLoading"
          >
            🗑️ Supprimer
          </button>
          <button
            type="button"
            class="library-view__bulk-btn library-view__bulk-btn--neutral"
            @click="clearSelection"
          >
            ✖ Annuler
          </button>
        </div>
      </div>
    </Transition>

    <!-- ====================================================================
      CONTENU PRINCIPAL
    ==================================================================== -->
    <div class="library-view__body">
      <!-- État de chargement initial -->
      <div v-if="loading && items.length === 0" class="library-view__loading">
        <NexusSpinner size="lg" variant="gradient" label="Chargement de la bibliothèque..." />
      </div>

      <!-- État vide -->
      <div v-else-if="filteredItems.length === 0" class="library-view__empty">
        <span class="library-view__empty-icon" aria-hidden="true">📭</span>
        <h2 class="library-view__empty-title">
          {{ items.length === 0 ? 'Votre bibliothèque est vide' : 'Aucun résultat' }}
        </h2>
        <p class="library-view__empty-text">
          {{
            items.length === 0
              ? 'Commencez par télécharger ou importer des séries de scans.'
              : 'Essayez de modifier vos filtres ou votre recherche.'
          }}
        </p>
        <div class="library-view__empty-actions">
          <NexusButton
            v-if="hasActiveFilters"
            variant="neutral"
            @click="resetFilters"
          >
            ✖ Réinitialiser les filtres
          </NexusButton>
          <NexusButton
            v-else
            variant="primary"
            @click="goToSearch"
          >
            🔍 Rechercher des séries
          </NexusButton>
          <NexusButton
            variant="neutral"
            @click="triggerFileInput"
            :loading="importing"
          >
            📥 Importer un CBZ
          </NexusButton>
        </div>
      </div>

      <!-- Vue grille -->
      <div
        v-else-if="viewMode === 'grid'"
        class="library-view__grid"
        :class="{ 'library-view__grid--small': gridSize === 'small' }"
      >
        <article
          v-for="item in paginatedItems"
          :key="item.id"
          class="library-view__card"
          :class="{
            'library-view__card--selected': selectedIds.includes(item.id),
            'library-view__card--favorite': item.is_favorite,
          }"
          @click="handleCardClick(item)"
        >
          <!-- Checkbox de sélection -->
          <div class="library-view__card-checkbox" @click.stop>
            <input
              type="checkbox"
              :checked="selectedIds.includes(item.id)"
              @change="toggleSelect(item.id)"
              :aria-label="`Sélectionner ${item.title}`"
            />
          </div>

          <!-- Couverture -->
          <div class="library-view__card-cover-wrapper">
            <img
              v-if="getCover(item)"
              :src="getCover(item)"
              :alt="`Couverture de ${item.title}`"
              class="library-view__card-cover"
              loading="lazy"
              @error="handleCoverError(item)"
            />
            <div v-else class="library-view__card-cover-placeholder">
              <span aria-hidden="true">📖</span>
            </div>

            <!-- Badges superposés -->
            <div class="library-view__card-badges">
              <span
                v-if="item.is_favorite"
                class="library-view__card-badge library-view__card-badge--favorite"
                title="Favori"
              >
                ❤️
              </span>
              <span
                v-if="item.rating > 0"
                class="library-view__card-badge library-view__card-badge--rating"
                :title="`Note : ${item.rating}/10`"
              >
                ⭐ {{ item.rating }}
              </span>
              <span
                v-if="item.read_count > 0"
                class="library-view__card-badge library-view__card-badge--read"
                :title="`Lu ${item.read_count} fois`"
              >
                👁️ {{ item.read_count }}
              </span>
            </div>

            <!-- Overlay d'actions -->
            <div class="library-view__card-overlay">
              <button
                type="button"
                class="library-view__card-action"
                @click.stop="openReader(item)"
                title="Lire"
                aria-label="Lire"
              >
                📖
              </button>
              <button
                type="button"
                class="library-view__card-action"
                @click.stop="toggleFavorite(item)"
                :title="item.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'"
                :aria-label="item.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'"
              >
                {{ item.is_favorite ? '💔' : '❤️' }}
              </button>
              <button
                type="button"
                class="library-view__card-action"
                @click.stop="downloadItem(item)"
                title="Télécharger"
                aria-label="Télécharger"
              >
                ⬇️
              </button>
              <button
                type="button"
                class="library-view__card-action library-view__card-action--danger"
                @click.stop="confirmDelete(item)"
                title="Supprimer"
                aria-label="Supprimer"
              >
                🗑️
              </button>
            </div>
          </div>

          <!-- Infos -->
          <div class="library-view__card-info">
            <h3 class="library-view__card-title" :title="item.title">
              {{ item.title }}
            </h3>
            <p v-if="item.metadata?.author" class="library-view__card-author">
              {{ item.metadata.author }}
            </p>
            <div class="library-view__card-meta">
              <span v-if="item.metadata?.year" class="library-view__card-year">
                {{ item.metadata.year }}
              </span>
              <span class="library-view__card-size">
                {{ item.size_formatted || formatFileSize(item.size_bytes) }}
              </span>
            </div>
          </div>
        </article>
      </div>

      <!-- Vue liste -->
      <div v-else class="library-view__list">
        <table class="library-view__table">
          <thead>
            <tr>
              <th class="library-view__th library-view__th--check">
                <input
                  type="checkbox"
                  :checked="allSelected"
                  @change="toggleSelectAll"
                  aria-label="Tout sélectionner"
                />
              </th>
              <th class="library-view__th library-view__th--cover"></th>
              <th class="library-view__th">Titre</th>
              <th class="library-view__th">Auteur</th>
              <th class="library-view__th library-view__th--center">Année</th>
              <th class="library-view__th library-view__th--center">Taille</th>
              <th class="library-view__th library-view__th--center">Note</th>
              <th class="library-view__th library-view__th--actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in paginatedItems"
              :key="item.id"
              class="library-view__tr"
              :class="{ 'library-view__tr--selected': selectedIds.includes(item.id) }"
              @click="handleCardClick(item)"
            >
              <td class="library-view__td library-view__td--check" @click.stop>
                <input
                  type="checkbox"
                  :checked="selectedIds.includes(item.id)"
                  @change="toggleSelect(item.id)"
                  :aria-label="`Sélectionner ${item.title}`"
                />
              </td>
              <td class="library-view__td library-view__td--cover">
                <img
                  v-if="getCover(item)"
                  :src="getCover(item)"
                  :alt="`Couverture de ${item.title}`"
                  class="library-view__list-cover"
                  loading="lazy"
                />
                <div v-else class="library-view__list-cover-placeholder">📖</div>
              </td>
              <td class="library-view__td">
                <span class="library-view__list-title" :title="item.title">
                  {{ item.title }}
                  <span v-if="item.is_favorite" class="library-view__list-fav">❤️</span>
                </span>
                <span v-if="item.metadata?.series" class="library-view__list-series">
                  📚 {{ item.metadata.series }}
                </span>
              </td>
              <td class="library-view__td">
                <span class="library-view__list-author">{{ item.metadata?.author || '—' }}</span>
              </td>
              <td class="library-view__td library-view__td--center">
                {{ item.metadata?.year || '—' }}
              </td>
              <td class="library-view__td library-view__td--center">
                {{ item.size_formatted || formatFileSize(item.size_bytes) }}
              </td>
              <td class="library-view__td library-view__td--center">
                <span v-if="item.rating > 0" class="library-view__list-rating">
                  ⭐ {{ item.rating }}
                </span>
                <span v-else class="library-view__text-muted">—</span>
              </td>
              <td class="library-view__td library-view__td--actions" @click.stop>
                <button
                  type="button"
                  class="library-view__list-action"
                  @click="openReader(item)"
                  title="Lire"
                  aria-label="Lire"
                >
                  📖
                </button>
                <button
                  type="button"
                  class="library-view__list-action"
                  @click="toggleFavorite(item)"
                  :title="item.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'"
                  :aria-label="item.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'"
                >
                  {{ item.is_favorite ? '💔' : '❤️' }}
                </button>
                <button
                  type="button"
                  class="library-view__list-action library-view__list-action--danger"
                  @click="confirmDelete(item)"
                  title="Supprimer"
                  aria-label="Supprimer"
                >
                  🗑️
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ====================================================================
      PAGINATION
    ==================================================================== -->
    <div v-if="totalPages > 1" class="library-view__pagination">
      <button
        type="button"
        class="library-view__pagination-btn"
        :disabled="currentPage <= 1"
        @click="goToPage(1)"
        aria-label="Première page"
        title="Première page"
      >
        ⏮
      </button>
      <button
        type="button"
        class="library-view__pagination-btn"
        :disabled="currentPage <= 1"
        @click="prevPage"
        aria-label="Page précédente"
        title="Précédente"
      >
        ◀
      </button>

      <span class="library-view__pagination-info">
        Page
        <strong>{{ currentPage }}</strong>
        sur
        <strong>{{ totalPages }}</strong>
      </span>

      <button
        type="button"
        class="library-view__pagination-btn"
        :disabled="currentPage >= totalPages"
        @click="nextPage"
        aria-label="Page suivante"
        title="Suivante"
      >
        ▶
      </button>
      <button
        type="button"
        class="library-view__pagination-btn"
        :disabled="currentPage >= totalPages"
        @click="goToPage(totalPages)"
        aria-label="Dernière page"
        title="Dernière page"
      >
        ⏭
      </button>

      <select
        v-model.number="pageSize"
        class="library-view__pagination-select"
        aria-label="Éléments par page"
        @change="onPageSizeChange"
      >
        <option :value="12">12 / page</option>
        <option :value="24">24 / page</option>
        <option :value="48">48 / page</option>
        <option :value="96">96 / page</option>
      </select>

      <span class="library-view__pagination-count">
        {{ filteredCount }} élément(s)
      </span>
    </div>

    <!-- ====================================================================
      PIED DE PAGE
    ==================================================================== -->
    <footer class="library-view__footer">
      <span class="library-view__footer-info">
        {{ filteredCount }} / {{ totalItems }} éléments affichés
        <span v-if="searchQuery" class="library-view__footer-highlight">
          · recherche : "{{ searchQuery }}"
        </span>
        <span v-if="genreFilter" class="library-view__footer-highlight">
          · genre : {{ genreFilter }}
        </span>
        <span v-if="authorFilter" class="library-view__footer-highlight">
          · auteur : {{ authorFilter }}
        </span>
        <span v-if="favoriteFilter" class="library-view__footer-highlight">
          · favoris
        </span>
      </span>
      <span v-if="lastUpdated" class="library-view__footer-updated">
        Dernière mise à jour : {{ formatDateTime(lastUpdated) }}
      </span>
    </footer>

    <!-- ====================================================================
      MODALE DE CONFIRMATION DE SUPPRESSION
    ==================================================================== -->
    <NexusModal
      v-model="showDeleteModal"
      title="🗑️ Supprimer un élément"
      size="sm"
      confirmable
      confirm-text="Supprimer"
      cancel-text="Annuler"
      confirm-variant="error"
      :loading="deleting"
      @confirm="executeDelete"
      @cancel="showDeleteModal = false"
    >
      <p>
        Êtes-vous sûr de vouloir supprimer
        <strong>"{{ itemToDelete?.title }}"</strong> ?
      </p>
      <p class="library-view__delete-warning">
        ⚠️ Le fichier CBZ sera supprimé du disque. Cette action est
        <strong>irréversible</strong>.
      </p>
    </NexusModal>

    <!-- ====================================================================
      MODALE DE CONFIRMATION DE SUPPRESSION GROUPÉE
    ==================================================================== -->
    <NexusModal
      v-model="showBulkDeleteModal"
      title="🗑️ Supprimer plusieurs éléments"
      size="sm"
      confirmable
      confirm-text="Tout supprimer"
      cancel-text="Annuler"
      confirm-variant="error"
      :loading="bulkLoading"
      @confirm="executeBulkDelete"
      @cancel="showBulkDeleteModal = false"
    >
      <p>
        Êtes-vous sûr de vouloir supprimer
        <strong>{{ selectedIds.length }} élément(s)</strong> ?
      </p>
      <p class="library-view__delete-warning">
        ⚠️ Les fichiers CBZ seront supprimés du disque. Cette action est
        <strong>irréversible</strong>.
      </p>
    </NexusModal>

    <!-- ====================================================================
      MODALE DE PROGRESSION D'IMPORT
    ==================================================================== -->
    <NexusModal
      v-model="showImportModal"
      title="📥 Import en cours"
      size="sm"
      :show-close="false"
      :show-footer="false"
    >
      <div class="library-view__import">
        <NexusSpinner size="md" />
        <p class="library-view__import-text">
          Importation de <strong>{{ importQueue.length }}</strong> fichier(s)...
        </p>
        <div class="library-view__import-progress">
          <div
            class="library-view__import-progress-bar"
            :style="{ width: `${importProgress}%` }"
          />
        </div>
        <p class="library-view__import-current">
          {{ currentImportFile }}
        </p>
      </div>
    </NexusModal>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useLibraryStore } from '@/stores/library'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusButton from '@/components/common/NexusButton.vue'
import NexusModal from '@/components/common/NexusModal.vue'
import { formatFileSize, formatDateTime } from '@/utils/formatters'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const router = useRouter()
const api = useApi()
const toast = useToast()
const libraryStore = useLibraryStore()

// ==========================================================================
//  État réactif
// ==========================================================================

const items = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref(null)
const lastUpdated = ref(null)

// Recherche & filtres
const searchQuery = ref('')
const genreFilter = ref('')
const authorFilter = ref('')
const favoriteFilter = ref(false)
const sortBy = ref('created_at-desc')

// Vue
const viewMode = ref('grid')
const gridSize = ref('normal') // 'normal' | 'small'

// Pagination
const currentPage = ref(1)
const pageSize = ref(24)

// Sélection
const selectedIds = ref([])

// Import
const fileInputRef = ref(null)
const importing = ref(false)
const importQueue = ref([])
const importProgress = ref(0)
const currentImportFile = ref('')
const showImportModal = ref(false)

// Suppression
const showDeleteModal = ref(false)
const showBulkDeleteModal = ref(false)
const itemToDelete = ref(null)
const deleting = ref(false)
const bulkLoading = ref(false)

// Cache des couvertures
const coverCache = ref({})
const coverErrors = ref(new Set())

let searchTimeout = null

// ==========================================================================
//  Computed
// ==========================================================================

const totalItems = computed(() => items.value.length)

const filteredItems = computed(() => {
  let result = [...items.value]

  // Recherche
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter((item) => {
      return (
        (item.title || '').toLowerCase().includes(q) ||
        (item.metadata?.author || '').toLowerCase().includes(q) ||
        (item.metadata?.series || '').toLowerCase().includes(q) ||
        (item.filename || '').toLowerCase().includes(q) ||
        (Array.isArray(item.tags) && item.tags.some((t) => t.toLowerCase().includes(q)))
      )
    })
  }

  // Filtre genre
  if (genreFilter.value) {
    result = result.filter((item) => {
      const genre = item.metadata?.genre
      if (!genre) return false
      if (Array.isArray(genre)) return genre.includes(genreFilter.value)
      return String(genre).toLowerCase().includes(genreFilter.value.toLowerCase())
    })
  }

  // Filtre auteur
  if (authorFilter.value) {
    result = result.filter(
      (item) => item.metadata?.author === authorFilter.value
    )
  }

  // Filtre favoris
  if (favoriteFilter.value) {
    result = result.filter((item) => item.is_favorite)
  }

  // Tri
  const [field, order] = sortBy.value.split('-')
  result.sort((a, b) => {
    let cmp = 0
    switch (field) {
      case 'title':
        cmp = (a.title || '').localeCompare(b.title || '')
        break
      case 'size':
        cmp = (a.size_bytes || 0) - (b.size_bytes || 0)
        break
      case 'rating':
        cmp = (a.rating || 0) - (b.rating || 0)
        break
      case 'last_read': {
        const ta = a.last_read ? new Date(a.last_read).getTime() : 0
        const tb = b.last_read ? new Date(b.last_read).getTime() : 0
        cmp = ta - tb
        break
      }
      case 'created_at':
      default: {
        const ta = a.created_at ? new Date(a.created_at).getTime() : 0
        const tb = b.created_at ? new Date(b.created_at).getTime() : 0
        cmp = ta - tb
        break
      }
    }
    return order === 'desc' ? -cmp : cmp
  })

  return result
})

const filteredCount = computed(() => filteredItems.value.length)

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredCount.value / pageSize.value))
})

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredItems.value.slice(start, end)
})

const allSelected = computed(() => {
  if (paginatedItems.value.length === 0) return false
  return paginatedItems.value.every((item) => selectedIds.value.includes(item.id))
})

const hasActiveFilters = computed(() => {
  return (
    !!searchQuery.value ||
    !!genreFilter.value ||
    !!authorFilter.value ||
    favoriteFilter.value
  )
})

// ==========================================================================
//  Méthodes — Récupération
// ==========================================================================

/**
 * Charge la bibliothèque complète.
 */
async function fetchLibrary() {
  loading.value = true
  error.value = null
  try {
    // Charger tous les éléments via le store
    const result = await libraryStore.fetchLibrary({
      limit: 9999,
      offset: 0,
    })

    // Utiliser la liste du store
    items.value = libraryStore.itemList || []
    lastUpdated.value = new Date().toISOString()
  } catch (err) {
    console.error('Erreur chargement bibliothèque:', err)
    error.value = `Impossible de charger la bibliothèque : ${err.message}`
  } finally {
    loading.value = false
  }
}

/**
 * Charge les statistiques.
 */
async function fetchStats() {
  try {
    await libraryStore.fetchStats()
    stats.value = libraryStore.stats
  } catch (err) {
    console.warn('Erreur chargement stats:', err.message)
  }
}

/**
 * Rafraîchit la bibliothèque.
 */
async function refreshLibrary() {
  toast.info('Rafraîchissement...', '🔄', 1500)
  await Promise.allSettled([fetchLibrary(), fetchStats()])
}

// ==========================================================================
//  Méthodes — Couvertures
// ==========================================================================

/**
 * Récupère l'URL de la couverture pour un élément.
 * @param {Object} item
 * @returns {string}
 */
function getCover(item) {
  if (coverErrors.value.has(item.id)) return ''
  if (coverCache.value[item.id]) return coverCache.value[item.id]

  // Charger de manière asynchrone
  loadCoverAsync(item)
  return ''
}

/**
 * Charge la couverture d'un élément en asynchrone.
 * @param {Object} item
 */
async function loadCoverAsync(item) {
  try {
    const url = await libraryStore.fetchCover(item.id, 200, 300)
    if (url) {
      coverCache.value[item.id] = url
    } else {
      coverErrors.value.add(item.id)
    }
  } catch (_) {
    coverErrors.value.add(item.id)
  }
}

function handleCoverError(item) {
  coverErrors.value.add(item.id)
}

// ==========================================================================
//  Méthodes — Recherche & filtres
// ==========================================================================

function onSearchInput() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
  }, 300)
}

function clearSearch() {
  searchQuery.value = ''
  currentPage.value = 1
  searchInputRef.value?.focus()
}

function toggleFavoriteFilter() {
  favoriteFilter.value = !favoriteFilter.value
  currentPage.value = 1
}

function resetFilters() {
  searchQuery.value = ''
  genreFilter.value = ''
  authorFilter.value = ''
  favoriteFilter.value = false
  sortBy.value = 'created_at-desc'
  currentPage.value = 1
}

// ==========================================================================
//  Méthodes — Vue
// ==========================================================================

function setViewMode(mode) {
  viewMode.value = mode
  try {
    localStorage.setItem('nexus-library-view', mode)
  } catch (_) {}
}

// ==========================================================================
//  Méthodes — Sélection
// ==========================================================================

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) selectedIds.value.push(id)
  else selectedIds.value.splice(idx, 1)
}

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = paginatedItems.value.map((i) => i.id)
  }
}

function clearSelection() {
  selectedIds.value = []
}

// ==========================================================================
//  Méthodes — Actions sur les items
// ==========================================================================

function handleCardClick(item) {
  router.push({ name: 'library-detail', params: { id: item.id } })
}

function openReader(item) {
  router.push({
    name: 'reader',
    params: { jobId: item.id },
  })
}

async function toggleFavorite(item) {
  const newState = !item.is_favorite
  try {
    await libraryStore.toggleFavorite(item.id)
    const found = items.value.find((i) => i.id === item.id)
    if (found) found.is_favorite = newState
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

async function downloadItem(item) {
  try {
    const blob = await api.download(`/library/${encodeURIComponent(item.id)}/download`)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = item.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toast.success('Téléchargement lancé', '⬇️')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

function confirmDelete(item) {
  itemToDelete.value = item
  showDeleteModal.value = true
}

async function executeDelete() {
  if (!itemToDelete.value) return
  deleting.value = true
  try {
    await libraryStore.deleteItem(itemToDelete.value.id, false)
    items.value = items.value.filter((i) => i.id !== itemToDelete.value.id)
    toast.success(`"${itemToDelete.value.title}" supprimé`, '🗑️')
    showDeleteModal.value = false
    itemToDelete.value = null
    await fetchStats()
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    deleting.value = false
  }
}

// ==========================================================================
//  Méthodes — Actions groupées
// ==========================================================================

async function bulkToggleFavorite() {
  if (selectedIds.value.length === 0) return
  bulkLoading.value = true
  try {
    for (const id of selectedIds.value) {
      const item = items.value.find((i) => i.id === id)
      if (item && !item.is_favorite) {
        await libraryStore.toggleFavorite(id)
        item.is_favorite = true
      }
    }
    toast.success(`${selectedIds.value.length} favori(s) ajouté(s)`, '❤️')
    clearSelection()
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    bulkLoading.value = false
  }
}

function bulkDelete() {
  if (selectedIds.value.length === 0) return
  showBulkDeleteModal.value = true
}

async function executeBulkDelete() {
  bulkLoading.value = true
  try {
    await libraryStore.deleteItems([...selectedIds.value], false)
    items.value = items.value.filter((i) => !selectedIds.value.includes(i.id))
    toast.success(`${selectedIds.value.length} élément(s) supprimé(s)`, '🗑️')
    showBulkDeleteModal.value = false
    clearSelection()
    await fetchStats()
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    bulkLoading.value = false
  }
}

// ==========================================================================
//  Méthodes — Import
// ==========================================================================

function triggerFileInput() {
  fileInputRef.value?.click()
}

async function handleFileImport(event) {
  const files = Array.from(event.target.files || [])
  if (files.length === 0) return

  // Filtrer les fichiers CBZ
  const validFiles = files.filter(
    (f) => f.name.toLowerCase().endsWith('.cbz') || f.type === 'application/zip'
  )

  if (validFiles.length === 0) {
    toast.warning('Aucun fichier CBZ valide sélectionné', '⚠️')
    return
  }

  importing.value = true
  importQueue.value = validFiles
  importProgress.value = 0
  showImportModal.value = true

  let successCount = 0
  let errorCount = 0

  try {
    for (let i = 0; i < validFiles.length; i++) {
      const file = validFiles[i]
      currentImportFile.value = file.name
      importProgress.value = Math.round(((i + 1) / validFiles.length) * 100)

      try {
        await libraryStore.importCbz(file)
        successCount++
      } catch (err) {
        console.error(`Erreur import ${file.name}:`, err)
        errorCount++
      }
    }

    if (successCount > 0) {
      toast.success(`${successCount} fichier(s) importé(s)`, '📥')
    }
    if (errorCount > 0) {
      toast.error(`${errorCount} fichier(s) en erreur`, '⚠️')
    }

    await Promise.allSettled([fetchLibrary(), fetchStats()])
  } finally {
    importing.value = false
    showImportModal.value = false
    importQueue.value = []
    importProgress.value = 0
    currentImportFile.value = ''

    // Reset l'input pour permettre de réimporter le même fichier
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
}

// ==========================================================================
//  Méthodes — Export
// ==========================================================================

async function exportLibrary() {
  try {
    await libraryStore.downloadExport()
    toast.success('Bibliothèque exportée', '📤')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

// ==========================================================================
//  Méthodes — Pagination
// ==========================================================================

function goToPage(page) {
  const p = Math.max(1, Math.min(totalPages.value, page))
  currentPage.value = p
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function prevPage() {
  if (currentPage.value > 1) goToPage(currentPage.value - 1)
}

function nextPage() {
  if (currentPage.value < totalPages.value) goToPage(currentPage.value + 1)
}

function onPageSizeChange() {
  currentPage.value = 1
}

// ==========================================================================
//  Méthodes — Navigation
// ==========================================================================

function goToSearch() {
  router.push('/search')
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  // Restaurer la préférence de vue
  try {
    const savedView = localStorage.getItem('nexus-library-view')
    if (savedView === 'grid' || savedView === 'list') {
      viewMode.value = savedView
    }
  } catch (_) {}

  await Promise.allSettled([fetchLibrary(), fetchStats()])
})

onUnmounted(() => {
  clearTimeout(searchTimeout)
})

// ==========================================================================
//  Watchers
// ==========================================================================

// Réinitialiser la page lors d'un changement de filtre
watch([searchQuery, genreFilter, authorFilter, favoriteFilter, sortBy], () => {
  currentPage.value = 1
})

// Recharger si le nombre de pages dépasse
watch(totalPages, (newTotal) => {
  if (currentPage.value > newTotal) {
    currentPage.value = newTotal || 1
  }
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.library-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  min-height: calc(100vh - 100px);
}

// ==========================================================================
//  Header
// ==========================================================================

.library-view__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.library-view__header-left {
  flex: 1;
  min-width: 200px;
}

.library-view__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.library-view__subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.library-view__header-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

// ==========================================================================
//  Boutons
// ==========================================================================

.library-view__btn {
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

  &--import:hover:not(:disabled) {
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-primary, #00d4ff);
  }

  &--export:hover:not(:disabled) {
    border-color: var(--color-success, #4caf50);
    color: var(--color-success, #4caf50);
  }
}

.library-view__spinner {
  display: inline-block;
  animation: libraryViewSpin 0.8s linear infinite;
}

@keyframes libraryViewSpin {
  to { transform: rotate(360deg); }
}

.library-view__file-input {
  display: none;
}

// ==========================================================================
//  View toggle
// ==========================================================================

.library-view__view-toggle {
  display: flex;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
}

.library-view__view-btn {
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
//  Barre d'erreur
// ==========================================================================

.library-view__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid var(--color-error, #f44336);
  border-radius: var(--radius-md, 8px);
  color: var(--color-error, #f44336);
  font-size: 0.85rem;
}

.library-view__error-icon {
  flex-shrink: 0;
}

.library-view__error-text {
  flex: 1;
}

.library-view__error-close {
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0 0.3rem;
  border-radius: var(--radius-sm, 4px);
  &:hover {
    background: rgba(244, 67, 54, 0.15);
  }
}

// ==========================================================================
//  Statistiques
// ==========================================================================

.library-view__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.library-view__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.3rem 0.7rem;
  border-radius: var(--radius-sm, 4px);
  background: var(--color-bg-card, #1a2538);
  min-width: 70px;

  &--favorite { border-left: 3px solid #f44336; }
  &--filtered { border-left: 3px solid var(--color-primary, #00d4ff); }
}

.library-view__stat-value {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  font-variant-numeric: tabular-nums;
}

.library-view__stat-label {
  font-size: 0.6rem;
  text-transform: uppercase;
  color: var(--color-text-muted, #6a7a9a);
  letter-spacing: 0.05em;
}

// ==========================================================================
//  Toolbar
// ==========================================================================

.library-view__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.library-view__search-wrapper {
  position: relative;
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
}

.library-view__search-icon {
  position: absolute;
  left: 0.6rem;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
}

.library-view__search-input {
  width: 100%;
  padding: 0.45rem 0.5rem 0.45rem 2rem;
  font-size: 0.85rem;
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

.library-view__search-clear {
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

.library-view__filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
}

.library-view__select {
  padding: 0.35rem 0.6rem;
  font-size: 0.75rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  outline: none;
  max-width: 180px;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.library-view__filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.35rem 0.7rem;
  font-size: 0.75rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }

  &--active {
    background: rgba(244, 67, 54, 0.15);
    border-color: var(--color-error, #f44336);
    color: var(--color-error, #f44336);
  }
}

.library-view__filter-reset {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.35rem 0.6rem;
  font-size: 0.7rem;
  background: transparent;
  color: var(--color-text-muted, #6a7a9a);
  border: 1px dashed var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--color-error, #f44336);
    color: var(--color-error, #f44336);
  }
}

// ==========================================================================
//  Bulk actions
// ==========================================================================

.library-view__bulk-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.6rem 0.9rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-primary, #00d4ff);
  border-radius: var(--radius-md, 8px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.library-view__bulk-info {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-primary, #e8edf5);
}

.library-view__bulk-buttons {
  display: flex;
  gap: 0.3rem;
  flex-wrap: wrap;
}

.library-view__bulk-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &--favorite:hover:not(:disabled) {
    border-color: #f44336;
    color: #f44336;
  }

  &--danger:hover:not(:disabled) {
    border-color: var(--color-error, #f44336);
    color: var(--color-error, #f44336);
  }

  &--neutral:hover:not(:disabled) {
    border-color: var(--color-border-light, #253254);
  }
}

.library-view-slide-enter-active,
.library-view-slide-leave-active {
  transition: all 0.25s ease;
}

.library-view-slide-enter-from,
.library-view-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

// ==========================================================================
//  Body
// ==========================================================================

.library-view__body {
  flex: 1;
  min-height: 300px;
}

// ==========================================================================
//  États
// ==========================================================================

.library-view__loading,
.library-view__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  gap: 0.75rem;
  min-height: 400px;
}

.library-view__empty-icon {
  font-size: 4rem;
  opacity: 0.5;
  margin-bottom: 0.5rem;
}

.library-view__empty-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.library-view__empty-text {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-muted, #6a7a9a);
  max-width: 400px;
  line-height: 1.5;
}

.library-view__empty-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 0.5rem;
}

// ==========================================================================
//  Grille
// ==========================================================================

.library-view__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;

  &--small {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.75rem;

    .library-view__card-info {
      padding: 0.4rem;
    }

    .library-view__card-title {
      font-size: 0.75rem;
    }
  }
}

.library-view__card {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;

  &:hover {
    transform: translateY(-3px);
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);

    .library-view__card-overlay {
      opacity: 1;
    }
  }

  &--selected {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.3);
  }

  &--favorite .library-view__card-cover-wrapper {
    box-shadow: inset 0 0 0 2px rgba(244, 67, 54, 0.5);
  }
}

.library-view__card-checkbox {
  position: absolute;
  top: 0.4rem;
  left: 0.4rem;
  z-index: 5;

  input[type='checkbox'] {
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: var(--color-primary, #00d4ff);
  }
}

.library-view__card-cover-wrapper {
  position: relative;
  aspect-ratio: 2/3;
  background: var(--color-bg-secondary, #141a2b);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.library-view__card-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.3s ease;

  .library-view__card:hover & {
    transform: scale(1.05);
  }
}

.library-view__card-cover-placeholder {
  font-size: 3rem;
  color: var(--color-text-muted, #6a7a9a);
  opacity: 0.5;
}

.library-view__card-badges {
  position: absolute;
  top: 0.4rem;
  right: 0.4rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  z-index: 4;
  pointer-events: none;
}

.library-view__card-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.15rem 0.35rem;
  font-size: 0.6rem;
  font-weight: 600;
  border-radius: var(--radius-full, 9999px);
  backdrop-filter: blur(4px);
  background: rgba(0, 0, 0, 0.7);
  color: #ffffff;

  &--favorite {
    background: rgba(244, 67, 54, 0.9);
    font-size: 0.75rem;
    padding: 0.1rem 0.3rem;
  }

  &--rating {
    background: rgba(255, 193, 7, 0.9);
    color: #000000;
  }

  &--read {
    background: rgba(33, 150, 243, 0.9);
  }
}

.library-view__card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.85) 0%, transparent 60%);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0.6rem;
  gap: 0.3rem;
  opacity: 0;
  transition: opacity 0.2s ease;
  z-index: 3;
}

.library-view__card-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.15s ease;
  color: #ffffff;

  &:hover {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);
    transform: scale(1.1);
  }

  &--danger:hover {
    background: var(--color-error, #f44336);
    border-color: var(--color-error, #f44336);
  }
}

.library-view__card-info {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.5rem 0.6rem;
}

.library-view__card-title {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.library-view__card-author {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.library-view__card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.65rem;
  color: var(--color-text-muted, #6a7a9a);
  margin-top: 0.15rem;
}

// ==========================================================================
//  Liste
// ==========================================================================

.library-view__list {
  overflow-x: auto;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
}

.library-view__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.library-view__th {
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

  &--check { width: 40px; text-align: center; }
  &--cover { width: 50px; }
  &--center { text-align: center; }
  &--actions { width: 130px; text-align: right; }
}

.library-view__tr {
  cursor: pointer;
  transition: background 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }

  &--selected {
    background: rgba(0, 212, 255, 0.08);
  }

  &:last-child .library-view__td {
    border-bottom: none;
  }
}

.library-view__td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
  color: var(--color-text-secondary, #b0c0d8);
  vertical-align: middle;

  &--check { text-align: center; }
  &--cover { width: 50px; padding: 0.35rem 0.5rem; }
  &--center { text-align: center; }
  &--actions { text-align: right; white-space: nowrap; }

  input[type='checkbox'] {
    width: 16px;
    height: 16px;
    cursor: pointer;
    accent-color: var(--color-primary, #00d4ff);
  }
}

.library-view__list-cover {
  width: 36px;
  height: 54px;
  object-fit: cover;
  border-radius: var(--radius-sm, 4px);
  display: block;
}

.library-view__list-cover-placeholder {
  width: 36px;
  height: 54px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-sm, 4px);
  font-size: 1rem;
  color: var(--color-text-muted, #6a7a9a);
}

.library-view__list-title {
  display: block;
  font-weight: 500;
  color: var(--color-text-primary, #e8edf5);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.library-view__list-fav {
  color: #f44336;
  font-size: 0.75rem;
  margin-left: 0.2rem;
}

.library-view__list-series {
  display: block;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.library-view__list-author {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #b0c0d8);
}

.library-view__list-rating {
  color: #ffc107;
  font-size: 0.75rem;
}

.library-view__text-muted {
  color: var(--color-text-muted, #6a7a9a);
}

.library-view__list-action {
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

  &--danger:hover {
    color: var(--color-error, #f44336);
  }
}

// ==========================================================================
//  Pagination
// ==========================================================================

.library-view__pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.library-view__pagination-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.75rem;

  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-primary, #00d4ff);
  }

  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
}

.library-view__pagination-info {
  font-size: 0.8rem;
  color: var(--color-text-secondary, #b0c0d8);

  strong {
    color: var(--color-primary, #00d4ff);
    font-variant-numeric: tabular-nums;
  }
}

.library-view__pagination-select {
  padding: 0.25rem 0.5rem;
  font-size: 0.7rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
}

.library-view__pagination-count {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Footer
// ==========================================================================

.library-view__footer {
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

.library-view__footer-info {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.library-view__footer-highlight {
  color: var(--color-primary, #00d4ff);
  font-weight: 500;
}

.library-view__footer-updated {
  font-style: italic;
}

// ==========================================================================
//  Delete warning
// ==========================================================================

.library-view__delete-warning {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: rgba(244, 67, 54, 0.1);
  border-left: 3px solid var(--color-error, #f44336);
  border-radius: var(--radius-sm, 4px);
  font-size: 0.8rem;
  color: var(--color-error, #f44336);
}

// ==========================================================================
//  Import
// ==========================================================================

.library-view__import {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  text-align: center;
}

.library-view__import-text {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-secondary, #b0c0d8);

  strong {
    color: var(--color-primary, #00d4ff);
  }
}

.library-view__import-progress {
  width: 100%;
  max-width: 300px;
  height: 6px;
  background: var(--color-bg-input, #1e2a40);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
}

.library-view__import-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #0066ff);
  border-radius: var(--radius-full, 9999px);
  transition: width 0.3s ease;
}

.library-view__import-current {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  font-style: italic;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 768px) {
  .library-view__header {
    flex-direction: column;
  }

  .library-view__header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .library-view__toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .library-view__filters {
    justify-content: flex-start;
    overflow-x: auto;
    padding-bottom: 0.3rem;
  }

  .library-view__select {
    min-width: 120px;
  }

  .library-view__grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 0.75rem;
  }

  .library-view__pagination {
    flex-direction: column;
    gap: 0.4rem;
  }

  .library-view__table {
    font-size: 0.7rem;
  }

  .library-view__th,
  .library-view__td {
    padding: 0.4rem 0.5rem;
  }

  .library-view__list-series,
  .library-view__list-title {
    max-width: 180px;
  }
}

@media (max-width: 480px) {
  .library-view {
    padding: 0.5rem;
  }

  .library-view__title {
    font-size: 1.2rem;
  }

  .library-view__grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .library-view__card-overlay {
    opacity: 1;
    background: rgba(0, 0, 0, 0.7);
  }

  .library-view__bulk-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .library-view__bulk-buttons {
    justify-content: center;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .library-view__btn {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .library-view__search-input,
  .library-view__select,
  .library-view__pagination-select {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .library-view__card {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);

    &:hover {
      border-color: var(--color-primary, #0066cc);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }
  }

  .library-view__card-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .library-view__card-cover-wrapper {
    background: var(--color-bg-secondary, #e9ecf2);
  }

  .library-view__list {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .library-view__th {
    background: var(--color-bg-secondary, #e9ecf2);
    color: var(--color-text-muted, #7a8a9a);
    border-color: var(--color-border, #d0d8e0);
  }

  .library-view__td {
    border-color: var(--color-border, #d0d8e0);
    color: var(--color-text-secondary, #3d4a5c);
  }

  .library-view__tr:hover {
    background: var(--color-bg-hover, #e3e8ef);
  }

  .library-view__list-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .library-view__filter-btn {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);

    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
    }
  }

  .library-view__stats,
  .library-view__footer,
  .library-view__pagination {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .library-view__stat {
    background: var(--color-bg-card, #ffffff);
  }

  .library-view__stat-value {
    color: var(--color-text-primary, #1a1a2e);
  }

  .library-view__empty-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .library-view__bulk-actions {
    background: var(--color-bg-card, #ffffff);
  }
}
</style>
