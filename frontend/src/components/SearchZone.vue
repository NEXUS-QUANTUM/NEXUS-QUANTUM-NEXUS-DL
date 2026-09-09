<!-- ==========================================================================
  NexusDL 2.0 - SearchZone Component
  Fichier : frontend/src/components/SearchZone.vue
  Description : Zone de recherche et d'analyse de séries (URL, recherche, sélection de chapitres, téléchargement)
  Version : 2.0.0
========================================================================== -->

<template>
  <div class="nexus-search-zone">
    <!-- Barre de recherche -->
    <div class="nexus-search-zone__bar">
      <div class="nexus-search-zone__input-wrapper">
        <span class="nexus-search-zone__input-icon" aria-hidden="true">🔍</span>
        <input
          ref="inputRef"
          type="text"
          class="nexus-search-zone__input"
          v-model="searchQuery"
          :placeholder="inputPlaceholder"
          @keydown.enter="handleSearch"
          @input="onInputChange"
          :disabled="loading"
          aria-label="Rechercher ou coller une URL"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="nexus-search-zone__clear-btn"
          @click="clearSearch"
          aria-label="Effacer"
        >
          <span aria-hidden="true">&times;</span>
        </button>
      </div>

      <div class="nexus-search-zone__actions">
        <!-- Bouton de recherche/analyse -->
        <NexusButton
          variant="primary"
          size="md"
          :loading="loading"
          :disabled="!searchQuery.trim()"
          @click="handleSearch"
        >
          <span aria-hidden="true">🔎</span>
          Analyser
        </NexusButton>

        <!-- Sélecteur de provider (optionnel) -->
        <NexusSelect
          v-if="providers.length > 1"
          v-model="selectedProviderId"
          :options="providerOptions"
          placeholder="Provider"
          size="sm"
          clearable
          @change="onProviderChange"
          style="min-width: 130px; max-width: 180px;"
        />
      </div>
    </div>

    <!-- Résultat de l'analyse -->
    <div v-if="analysisResult" class="nexus-search-zone__result">
      <!-- En-tête du résultat -->
      <div class="nexus-search-zone__result-header">
        <div class="nexus-search-zone__result-info">
          <h2 class="nexus-search-zone__result-title">{{ analysisResult.title }}</h2>
          <div class="nexus-search-zone__result-meta">
            <span v-if="analysisResult.author" class="nexus-search-zone__result-author">
              ✍️ {{ analysisResult.author }}
            </span>
            <span v-if="analysisResult.status" class="nexus-search-zone__result-status">
              {{ analysisResult.status }}
            </span>
            <span v-if="analysisResult.total_chapters" class="nexus-search-zone__result-chapters">
              📚 {{ analysisResult.total_chapters }} chapitres
            </span>
          </div>
        </div>
        <div class="nexus-search-zone__result-actions">
          <NexusButton
            variant="success"
            size="sm"
            :disabled="selectedChapterIds.length === 0 || downloading"
            :loading="downloading"
            @click="handleDownloadSelected"
          >
            ⬇️ Télécharger ({{ selectedChapterIds.length }})
          </NexusButton>
          <NexusButton
            variant="neutral"
            size="sm"
            @click="clearResult"
            aria-label="Fermer les résultats"
          >
            ✕
          </NexusButton>
        </div>
      </div>

      <!-- Corps du résultat : couverture + description + chapitres -->
      <div class="nexus-search-zone__result-body">
        <!-- Colonne de gauche : couverture et infos -->
        <div class="nexus-search-zone__result-sidebar">
          <div class="nexus-search-zone__result-cover-wrapper">
            <img
              v-if="analysisResult.cover_url"
              :src="analysisResult.cover_url"
              :alt="`Couverture de ${analysisResult.title}`"
              class="nexus-search-zone__result-cover"
              loading="lazy"
              @error="handleCoverError"
            />
            <div v-else class="nexus-search-zone__result-cover-placeholder">
              <span>📖</span>
            </div>
          </div>
          <div v-if="analysisResult.genre && analysisResult.genre.length" class="nexus-search-zone__result-genres">
            <span
              v-for="g in analysisResult.genre"
              :key="g"
              class="nexus-search-zone__result-genre"
            >
              {{ g }}
            </span>
          </div>
          <p v-if="analysisResult.description" class="nexus-search-zone__result-description">
            {{ truncate(analysisResult.description, 200) }}
          </p>
        </div>

        <!-- Colonne de droite : liste des chapitres -->
        <div class="nexus-search-zone__result-chapters">
          <ChapterList
            :chapters="analysisResult.chapters || []"
            :total-chapters="analysisResult.total_chapters || 0"
            :loading="loadingChapters"
            selectable
            downloadable
            searchable
            sortable
            paginated
            :page-size="20"
            :initial-selected="selectedChapterIds"
            @update:selected="updateSelectedChapters"
            @download="handleChapterDownload"
            @bulk-download="handleBulkChapterDownload"
            @search="onChapterSearch"
            @sort="onChapterSort"
            @page-change="onChapterPageChange"
          >
            <template #title>
              <span>Chapitres</span>
            </template>
            <template #empty>
              <span>Aucun chapitre disponible</span>
            </template>
          </ChapterList>
        </div>
      </div>
    </div>

    <!-- État de chargement initial -->
    <div v-else-if="loading" class="nexus-search-zone__loading">
      <NexusSpinner size="lg" label="Analyse en cours..." />
    </div>

    <!-- État vide / suggestions -->
    <div v-else class="nexus-search-zone__empty">
      <div class="nexus-search-zone__empty-content">
        <span class="nexus-search-zone__empty-icon">🧬</span>
        <h3 class="nexus-search-zone__empty-title">Rechercher une série</h3>
        <p class="nexus-search-zone__empty-text">
          Collez l'URL d'une série depuis un site de scan ou recherchez par titre.
          NexusDL analysera la page et vous proposera de télécharger les chapitres.
        </p>
        <div class="nexus-search-zone__empty-examples">
          <span class="nexus-search-zone__empty-example-label">Exemples :</span>
          <button
            v-for="example in examples"
            :key="example"
            class="nexus-search-zone__empty-example"
            @click="setExample(example)"
          >
            {{ example }}
          </button>
        </div>
      </div>
    </div>

    <!-- Messages d'erreur -->
    <div v-if="error" class="nexus-search-zone__error">
      <span class="nexus-search-zone__error-icon" aria-hidden="true">❌</span>
      <span class="nexus-search-zone__error-text">{{ error }}</span>
      <button
        type="button"
        class="nexus-search-zone__error-close"
        @click="error = null"
        aria-label="Fermer"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import NexusButton from './common/NexusButton.vue'
import NexusSelect from './common/NexusSelect.vue'
import NexusSpinner from './common/NexusSpinner.vue'
import ChapterList from './ChapterList.vue'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useJobsStore } from '@/stores/jobs'
import { useProvidersStore } from '@/stores/providers'
import { truncate } from '@/utils/formatters'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** URL de base de l'API */
  apiBase: {
    type: String,
    default: '/api',
  },
  /** Requête initiale (depuis l'URL) */
  initialQuery: {
    type: String,
    default: '',
  },
  /** Placeholder du champ de recherche */
  placeholder: {
    type: String,
    default: 'Coller une URL de série ou rechercher par titre...',
  },
})

// ==========================================================================
//  Émits
// ==========================================================================

const emit = defineEmits([
  'analyze',
  'download',
  'search',
])

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const api = useApi()
const toast = useToast()
const jobsStore = useJobsStore()
const providersStore = useProvidersStore()

// ==========================================================================
//  État
// ==========================================================================

const searchQuery = ref('')
const selectedProviderId = ref('')
const loading = ref(false)
const loadingChapters = ref(false)
const downloading = ref(false)
const error = ref(null)
const analysisResult = ref(null)
const selectedChapterIds = ref([])
const inputRef = ref(null)

// ==========================================================================
//  Computed
// ==========================================================================

/** Liste des providers pour le sélecteur */
const providers = computed(() => providersStore.filteredProviders)

const providerOptions = computed(() => {
  return providers.value.map(p => ({
    value: p.id,
    label: p.name,
    group: p.nsfw ? 'NSFW' : 'Général',
  }))
})

/** Placeholder dynamique */
const inputPlaceholder = computed(() => {
  if (providers.value.length === 0) return 'Chargement des providers...'
  return props.placeholder
})

// ==========================================================================
//  Exemples (pour l'état vide)
// ==========================================================================

const examples = [
  'https://sushiscan.net/manga/one-piece/',
  'https://asurascans.com/manga/solo-leveling/',
  'https://mangadex.org/title/a6c5b6f0-...',
]

// ==========================================================================
//  Méthodes
// ==========================================================================

/** Gère la recherche / analyse */
async function handleSearch() {
  const query = searchQuery.value.trim()
  if (!query) {
    toast.warning('Veuillez saisir une URL ou un titre.', '⚠️')
    return
  }

  // Si c'est une URL valide, on analyse directement
  const isUrl = query.startsWith('http://') || query.startsWith('https://')
  if (isUrl) {
    await analyzeUrl(query)
  } else {
    // Sinon, on recherche par titre (via l'API de recherche)
    await searchByTitle(query)
  }
}

/** Analyse une URL directement */
async function analyzeUrl(url) {
  loading.value = true
  error.value = null
  analysisResult.value = null
  selectedChapterIds.value = []

  try {
    const response = await api.post('/browse/analyze', { url })
    // La réponse peut être directement l'analyse ou avec un wrapper
    const data = response.data || response
    analysisResult.value = normalizeAnalysis(data)
    toast.success(`Analyse terminée : ${analysisResult.value.title}`, '✅')
    // Sélectionner tous les chapitres par défaut (ou les premiers 100)
    const chapters = analysisResult.value.chapters || []
    if (chapters.length > 0) {
      selectedChapterIds.value = chapters.map(c => c.id)
    }
    emit('analyze', analysisResult.value)
  } catch (err) {
    error.value = err.message || 'Erreur lors de l\'analyse.'
    toast.error(error.value, '❌')
  } finally {
    loading.value = false
  }
}

/** Recherche par titre (via l'API) */
async function searchByTitle(query) {
  loading.value = true
  error.value = null
  analysisResult.value = null
  selectedChapterIds.value = []

  try {
    // On utilise l'endpoint de recherche
    const params = { q: query, provider: selectedProviderId.value || undefined }
    const response = await api.get('/browse/search', { params })
    const results = response.results || []
    if (results.length === 0) {
      toast.warning('Aucune série trouvée.', '🔍')
      return
    }
    // Si un seul résultat, on l'analyse directement
    if (results.length === 1) {
      const series = results[0]
      await analyzeUrl(series.url)
      return
    }
    // Sinon, afficher une liste de résultats (on peut améliorer avec un composant de liste)
    // Pour l'instant, on prend le premier ou on propose un choix via un modal ? On simplifie :
    // On prend le premier résultat (le plus pertinent)
    const first = results[0]
    if (first.url) {
      await analyzeUrl(first.url)
    } else {
      toast.warning('Impossible d\'analyser ce résultat.', '⚠️')
    }
    emit('search', results)
  } catch (err) {
    error.value = err.message || 'Erreur lors de la recherche.'
    toast.error(error.value, '❌')
  } finally {
    loading.value = false
  }
}

/** Normalise les données d'analyse (pour garantir une structure) */
function normalizeAnalysis(data) {
  return {
    title: data.title || 'Sans titre',
    url: data.url || '',
    provider_id: data.provider_id || '',
    author: data.author || '',
    description: data.description || '',
    cover_url: data.cover_url || '',
    genre: Array.isArray(data.genre) ? data.genre : (data.genres || []),
    status: data.status || 'unknown',
    year: data.year || null,
    language: data.language || 'fr',
    nsfw: data.nsfw || false,
    chapters: Array.isArray(data.chapters) ? data.chapters : [],
    total_chapters: data.total_chapters || (data.chapters ? data.chapters.length : 0),
  }
}

/** Met à jour la sélection des chapitres (depuis ChapterList) */
function updateSelectedChapters(ids) {
  selectedChapterIds.value = ids
}

/** Gère le téléchargement des chapitres sélectionnés */
async function handleDownloadSelected() {
  if (selectedChapterIds.value.length === 0) {
    toast.warning('Sélectionnez au moins un chapitre.', '⚠️')
    return
  }
  if (!analysisResult.value || !analysisResult.value.url) {
    toast.error('URL de la série manquante.', '❌')
    return
  }

  downloading.value = true
  try {
    const payload = {
      url: analysisResult.value.url,
      chapter_ids: selectedChapterIds.value,
    }
    // Utiliser le store jobs pour lancer le téléchargement
    const job = await jobsStore.startDownload(
      payload.url,
      payload.chapter_ids,
      { provider_id: analysisResult.value.provider_id }
    )
    toast.success(`Téléchargement lancé (${selectedChapterIds.value.length} chapitres)`, '✅')
    emit('download', { job, url: payload.url, chapter_ids: payload.chapter_ids })
    // Option: nettoyer la sélection après le lancement
    // selectedChapterIds.value = []
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    downloading.value = false
  }
}

/** Gère le téléchargement d'un chapitre individuel (depuis ChapterList) */
function handleChapterDownload(chapter) {
  // Ajouter ce chapitre à la sélection et lancer le téléchargement
  const chapterId = chapter.id || chapter.url
  if (!selectedChapterIds.value.includes(chapterId)) {
    selectedChapterIds.value.push(chapterId)
  }
  handleDownloadSelected()
}

/** Gère le téléchargement en masse (depuis ChapterList) */
function handleBulkChapterDownload(chapters) {
  const ids = chapters.map(c => c.id || c.url)
  selectedChapterIds.value = ids
  handleDownloadSelected()
}

/** Efface le résultat affiché */
function clearResult() {
  analysisResult.value = null
  selectedChapterIds.value = []
  error.value = null
}

/** Efface la recherche */
function clearSearch() {
  searchQuery.value = ''
  inputRef.value?.focus()
}

/** Gère le changement de provider */
function onProviderChange() {
  // Si un provider est sélectionné, on peut l'utiliser pour la recherche
}

/** Gère les événements de ChapterList (recherche, tri, page) */
function onChapterSearch(query) {
  // La recherche est gérée localement par ChapterList, mais on peut l'écouter
}

function onChapterSort(sort) {
  // Le tri est géré localement
}

function onChapterPageChange(page) {
  // La pagination est gérée localement
}

/** Gestion de l'erreur de couverture */
function handleCoverError() {
  // On pourrait remplacer par un placeholder
}

/** Définit un exemple dans la recherche */
function setExample(example) {
  searchQuery.value = example
  handleSearch()
}

/** Gère l'input pour déclencher la recherche automatique (optionnel) */
function onInputChange() {
  // On pourrait implémenter un debounce pour la recherche automatique
  // Mais on préfère laisser l'utilisateur cliquer sur le bouton
}

// ==========================================================================
//  Initialisation
// ==========================================================================

onMounted(() => {
  if (props.initialQuery) {
    searchQuery.value = props.initialQuery
    handleSearch()
  }
})

// ==========================================================================
//  Watchers
// ==========================================================================

// Si l'utilisateur sélectionne un provider, on peut l'utiliser pour la prochaine recherche
watch(selectedProviderId, (newId) => {
  // Rien de spécial
})

// ==========================================================================
//  Exposer
// ==========================================================================

defineExpose({
  searchQuery,
  analysisResult,
  handleSearch,
  clearResult,
  focus: () => inputRef.value?.focus(),
})

// ==========================================================================
//  Styles
// ==========================================================================

</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$zone-radius: var(--radius-lg, 12px);
$zone-transition: all var(--transition-base, 300ms) ease;

// ==========================================================================
//  Conteneur principal
// ==========================================================================

.nexus-search-zone {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
  max-width: 100%;
}

// ==========================================================================
//  Barre de recherche
// ==========================================================================

.nexus-search-zone__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: $zone-radius;
  transition: $zone-transition;

  &:focus-within {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15);
  }
}

.nexus-search-zone__input-wrapper {
  position: relative;
  flex: 1;
  min-width: 150px;
}

.nexus-search-zone__input-icon {
  position: absolute;
  left: 0.6rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1rem;
  pointer-events: none;
}

.nexus-search-zone__input {
  width: 100%;
  padding: 0.4rem 0.5rem 0.4rem 2.2rem;
  font-size: 0.95rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  transition: $zone-transition;
  &:focus {
    border-color: var(--color-primary, #00d4ff);
  }
  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.nexus-search-zone__clear-btn {
  position: absolute;
  right: 0.3rem;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0.1rem 0.3rem;
  border-radius: var(--radius-sm, 4px);
  transition: $zone-transition;
  &:hover {
    color: var(--color-text-primary, #e8edf5);
    background: var(--color-bg-hover, #253254);
  }
}

.nexus-search-zone__actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
}

// ==========================================================================
//  Résultat
// ==========================================================================

.nexus-search-zone__result {
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: $zone-radius;
  overflow: hidden;
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// ==========================================================================
//  Résultat - Header
// ==========================================================================

.nexus-search-zone__result-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
  gap: 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
}

.nexus-search-zone__result-info {
  flex: 1;
  min-width: 0;
}

.nexus-search-zone__result-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nexus-search-zone__result-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.1rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-search-zone__result-author {
  display: inline-flex;
  align-items: center;
  gap: 0.1rem;
}

.nexus-search-zone__result-status {
  text-transform: capitalize;
  padding: 0.05rem 0.4rem;
  background: var(--color-bg-input, #1e2a40);
  border-radius: var(--radius-sm, 4px);
}

.nexus-search-zone__result-chapters {
  display: inline-flex;
  align-items: center;
  gap: 0.1rem;
}

.nexus-search-zone__result-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
}

// ==========================================================================
//  Résultat - Body
// ==========================================================================

.nexus-search-zone__result-body {
  display: flex;
  gap: 1rem;
  padding: 0.75rem 1rem;
  max-height: 600px;
  overflow: hidden;
}

// ==========================================================================
//  Résultat - Sidebar (couverture + infos)
// ==========================================================================

.nexus-search-zone__result-sidebar {
  flex: 0 0 180px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  overflow-y: auto;
}

.nexus-search-zone__result-cover-wrapper {
  aspect-ratio: 2/3;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nexus-search-zone__result-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.nexus-search-zone__result-cover-placeholder {
  font-size: 3rem;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-search-zone__result-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem;
}

.nexus-search-zone__result-genre {
  font-size: 0.6rem;
  padding: 0.05rem 0.4rem;
  background: var(--color-bg-input, #1e2a40);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-muted, #6a7a9a);
  text-transform: lowercase;
  white-space: nowrap;
}

.nexus-search-zone__result-description {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-text-secondary, #b0c0d8);
  line-height: 1.5;
  overflow-y: auto;
  max-height: 120px;
  padding-right: 0.3rem;
  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
    border-radius: 2px;
  }
}

// ==========================================================================
//  Résultat - Chapitres
// ==========================================================================

.nexus-search-zone__result-chapters {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  .nexus-chapter-list {
    max-height: 100%;
    height: 100%;
  }
}

// ==========================================================================
//  Loading / Empty / Error
// ==========================================================================

.nexus-search-zone__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
}

.nexus-search-zone__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.nexus-search-zone__empty-content {
  max-width: 480px;
  text-align: center;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-search-zone__empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.nexus-search-zone__empty-title {
  margin: 0 0 0.25rem;
  font-size: 1.1rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-secondary, #b0c0d8);
}

.nexus-search-zone__empty-text {
  margin: 0 0 0.75rem;
  font-size: 0.85rem;
  line-height: 1.5;
}

.nexus-search-zone__empty-examples {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.3rem;
}

.nexus-search-zone__empty-example-label {
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
  margin-right: 0.2rem;
}

.nexus-search-zone__empty-example {
  font-size: 0.7rem;
  padding: 0.1rem 0.5rem;
  background: var(--color-bg-input, #1e2a40);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  transition: $zone-transition;
  white-space: nowrap;
  &:hover {
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-primary, #e8edf5);
  }
}

.nexus-search-zone__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(244, 67, 54, 0.08);
  border: 1px solid var(--color-error, #f44336);
  border-radius: var(--radius-md, 8px);
  color: var(--color-error, #f44336);
  font-size: 0.85rem;
}

.nexus-search-zone__error-icon {
  flex-shrink: 0;
}

.nexus-search-zone__error-text {
  flex: 1;
}

.nexus-search-zone__error-close {
  background: transparent;
  border: none;
  color: var(--color-error, #f44336);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.1rem 0.3rem;
  border-radius: var(--radius-sm, 4px);
  transition: $zone-transition;
  &:hover {
    background: rgba(244, 67, 54, 0.1);
  }
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 992px) {
  .nexus-search-zone__result-body {
    flex-direction: column;
    max-height: none;
    padding: 0.5rem;
  }
  .nexus-search-zone__result-sidebar {
    flex: none;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: flex-start;
    max-height: 200px;
    overflow-y: visible;
  }
  .nexus-search-zone__result-cover-wrapper {
    width: 120px;
    aspect-ratio: 2/3;
    flex-shrink: 0;
  }
  .nexus-search-zone__result-description {
    max-height: 80px;
  }
  .nexus-search-zone__result-chapters {
    max-height: 400px;
  }
}

@media (max-width: 600px) {
  .nexus-search-zone__bar {
    flex-direction: column;
    align-items: stretch;
    gap: 0.4rem;
  }
  .nexus-search-zone__actions {
    justify-content: flex-end;
  }
  .nexus-search-zone__result-header {
    flex-direction: column;
    align-items: stretch;
  }
  .nexus-search-zone__result-actions {
    justify-content: flex-start;
  }
  .nexus-search-zone__result-sidebar {
    flex-direction: column;
    align-items: center;
  }
  .nexus-search-zone__result-cover-wrapper {
    width: 100%;
    max-width: 200px;
  }
  .nexus-search-zone__result-description {
    max-height: 100px;
  }
}

// ==========================================================================
//  Support du thème clair
// ==========================================================================

.light-mode {
  .nexus-search-zone__bar {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-search-zone__input {
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
  .nexus-search-zone__result {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-search-zone__result-header {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-search-zone__result-title {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-search-zone__result-description {
    color: var(--color-text-secondary, #3d4a5c);
  }
  .nexus-search-zone__result-genre {
    background: var(--color-bg-secondary, #e9ecf2);
    color: var(--color-text-muted, #7a8a9a);
  }
  .nexus-search-zone__result-cover-wrapper {
    background: var(--color-bg-secondary, #e9ecf2);
  }
  .nexus-search-zone__empty-example {
    background: var(--color-bg-input, #f0f2f5);
    border-color: var(--color-border, #d0d8e0);
    color: var(--color-text-secondary, #3d4a5c);
    &:hover {
      border-color: var(--color-primary, #0066cc);
      color: var(--color-text-primary, #1a1a2e);
    }
  }
  .nexus-search-zone__error {
    background: rgba(198, 40, 40, 0.05);
    border-color: var(--color-error, #c62828);
    color: var(--color-error, #c62828);
  }
  .nexus-search-zone__clear-btn {
    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
    }
  }
}
</style>
