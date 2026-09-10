<!-- ==========================================================================
  NexusDL 2.0 - Search View (version complète)
  Fichier : frontend/src/views/SearchView.vue
  Description : Page de recherche et d'analyse. Permet de rechercher des
                séries par titre (multi-providers) ou de coller une URL
                pour analyse directe. Affiche les résultats, les détails
                d'une série et lance les téléchargements.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="search-view">
    <!-- ====================================================================
      EN-TÊTE
    ==================================================================== -->
    <header class="search-view__header">
      <div class="search-view__header-left">
        <h1 class="search-view__title">
          <span aria-hidden="true">🔍</span>
          Recherche
        </h1>
        <p class="search-view__subtitle">
          Recherchez une série par titre ou collez une URL pour l'analyser
        </p>
      </div>
    </header>

    <!-- ====================================================================
      BARRE DE RECHERCHE PRINCIPALE
    ==================================================================== -->
    <div class="search-view__search-zone">
      <div class="search-view__search-input-wrapper">
        <span class="search-view__search-icon" aria-hidden="true">🔎</span>
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          type="text"
          class="search-view__search-input"
          :placeholder="searchPlaceholder"
          aria-label="Rechercher une série ou coller une URL"
          @keydown.enter="handleSearch"
          @input="onSearchInput"
          :disabled="loading"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="search-view__search-clear"
          @click="clearSearch"
          aria-label="Effacer la recherche"
        >
          <span aria-hidden="true">&times;</span>
        </button>
      </div>

      <!-- Sélecteur de provider -->
      <NexusSelect
        v-if="providers.length > 1"
        v-model="selectedProviderId"
        :options="providerOptions"
        placeholder="Tous les providers"
        size="md"
        clearable
        style="min-width: 180px; max-width: 220px;"
      />

      <!-- Bouton principal -->
      <NexusButton
        variant="primary"
        size="md"
        :loading="loading"
        :disabled="!searchQuery.trim()"
        @click="handleSearch"
      >
        <span v-if="!loading" aria-hidden="true">🔍</span>
        {{ loading ? 'Recherche...' : 'Rechercher' }}
      </NexusButton>
    </div>

    <!-- ====================================================================
      INDICATEURS RAPIDES
    ==================================================================== -->
    <div class="search-view__quick-info">
      <div class="search-view__quick-item">
        <span class="search-view__quick-icon" aria-hidden="true">⚡</span>
        <span class="search-view__quick-text">{{ providers.length }} providers disponibles</span>
      </div>
      <div class="search-view__quick-item">
        <span class="search-view__quick-icon" aria-hidden="true">💡</span>
        <span class="search-view__quick-text">
          Astuce : collez une URL de chapitre ou de série pour analyse directe
        </span>
      </div>
    </div>

    <!-- ====================================================================
      EXEMPLES / SUGGESTIONS
    ==================================================================== -->
    <div v-if="!hasSearched && !loading" class="search-view__suggestions">
      <h2 class="search-view__suggestions-title">
        🎯 Suggestions
      </h2>
      <div class="search-view__suggestions-grid">
        <button
          v-for="(example, idx) in examples"
          :key="idx"
          type="button"
          class="search-view__suggestion"
          @click="setExample(example.url)"
        >
          <div class="search-view__suggestion-icon" aria-hidden="true">
            {{ example.icon }}
          </div>
          <div class="search-view__suggestion-content">
            <span class="search-view__suggestion-title">{{ example.title }}</span>
            <span class="search-view__suggestion-desc">{{ example.description }}</span>
          </div>
        </button>
      </div>
    </div>

    <!-- ====================================================================
      ALERTE D'ERREUR
    ==================================================================== -->
    <div v-if="error" class="search-view__error" role="alert">
      <span class="search-view__error-icon" aria-hidden="true">❌</span>
      <div class="search-view__error-content">
        <span class="search-view__error-text">{{ error }}</span>
        <span v-if="errorHint" class="search-view__error-hint">{{ errorHint }}</span>
      </div>
      <button
        type="button"
        class="search-view__error-close"
        @click="error = null; errorHint = ''"
        aria-label="Fermer"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>

    <!-- ====================================================================
      ÉTAT DE CHARGEMENT
    ==================================================================== -->
    <div v-if="loading" class="search-view__loading">
      <NexusSpinner size="lg" variant="gradient" />
      <p class="search-view__loading-text">
        {{ isUrlSearch ? 'Analyse de l\'URL en cours...' : 'Recherche en cours...' }}
      </p>
      <p v-if="isUrlSearch" class="search-view__loading-hint">
        L'analyse peut prendre quelques secondes selon le site.
      </p>
    </div>

    <!-- ====================================================================
      RÉSULTATS D'ANALYSE (URL)
    ==================================================================== -->
    <div v-else-if="analysisResult" class="search-view__analysis">
      <!-- Carte de série analysée -->
      <div class="search-view__analysis-card">
        <!-- Sidebar -->
        <aside class="search-view__analysis-sidebar">
          <div class="search-view__cover-wrapper">
            <img
              v-if="analysisResult.cover_url && !coverError"
              :src="analysisResult.cover_url"
              :alt="`Couverture de ${analysisResult.title}`"
              class="search-view__cover"
              loading="lazy"
              @error="coverError = true"
            />
            <div v-else class="search-view__cover-placeholder">
              <span aria-hidden="true">📖</span>
            </div>
          </div>

          <div class="search-view__analysis-info">
            <h2 class="search-view__analysis-title">{{ analysisResult.title }}</h2>
            <p v-if="analysisResult.author" class="search-view__analysis-author">
              ✍️ {{ analysisResult.author }}
            </p>
            <p class="search-view__analysis-provider">
              🌐 {{ analysisResult.provider_id }}
            </p>
          </div>

          <div v-if="analysisResult.genre?.length" class="search-view__genres">
            <span
              v-for="g in analysisResult.genre"
              :key="g"
              class="search-view__genre"
            >
              {{ g }}
            </span>
          </div>

          <p v-if="analysisResult.description" class="search-view__description">
            {{ truncate(analysisResult.description, 250) }}
          </p>

          <div class="search-view__analysis-actions">
            <NexusButton
              variant="primary"
              size="md"
              block
              :disabled="selectedChapterIds.length === 0"
              :loading="downloading"
              @click="handleDownloadSelected"
            >
              ⬇️ Télécharger ({{ selectedChapterIds.length }})
            </NexusButton>
            <NexusButton
              variant="neutral"
              size="sm"
              block
              @click="selectAllChapters"
            >
              ✅ Tout sélectionner
            </NexusButton>
            <NexusButton
              variant="neutral"
              size="sm"
              block
              @click="deselectAllChapters"
            >
              ⬜ Tout désélectionner
            </NexusButton>
            <NexusButton
              variant="ghost"
              size="sm"
              block
              @click="clearAnalysis"
            >
              ✖ Fermer l'analyse
            </NexusButton>
          </div>
        </aside>

        <!-- Liste des chapitres -->
        <main class="search-view__analysis-main">
          <ChapterList
            :chapters="analysisResult.chapters || []"
            :total-chapters="analysisResult.total_chapters || 0"
            :loading="loadingChapters"
            selectable
            downloadable
            searchable
            sortable
            paginated
            :page-size="30"
            :initial-selected="selectedChapterIds"
            @update:selected="onChaptersSelected"
            @download="onChapterDownload"
            @bulk-download="onBulkDownload"
          />
        </main>
      </div>
    </div>

    <!-- ====================================================================
      RÉSULTATS DE RECHERCHE (TITRE)
    ==================================================================== -->
    <div v-else-if="searchResults.length > 0" class="search-view__results">
      <header class="search-view__results-header">
        <h2 class="search-view__results-title">
          📚 Résultats ({{ totalResults }})
        </h2>
        <p class="search-view__results-query">
          pour « <strong>{{ lastSearchQuery }}</strong> »
        </p>
      </header>

      <!-- Grille de résultats -->
      <div class="search-view__results-grid">
        <article
          v-for="result in searchResults"
          :key="`${result.provider_id}-${result.series_id || result.url}`"
          class="search-view__result-card"
          @click="analyzeResult(result)"
        >
          <div class="search-view__result-cover-wrapper">
            <img
              v-if="result.cover_url"
              :src="result.cover_url"
              :alt="`Couverture de ${result.title}`"
              class="search-view__result-cover"
              loading="lazy"
              @error="onResultCoverError($event)"
            />
            <div v-else class="search-view__result-cover-placeholder">
              <span aria-hidden="true">📖</span>
            </div>

            <!-- Badge provider -->
            <span class="search-view__result-provider">
              {{ result.provider_name || result.provider_id }}
            </span>

            <!-- Badge NSFW -->
            <span v-if="result.nsfw" class="search-view__result-nsfw" title="Contenu pour adultes">
              🔞
            </span>

            <!-- Overlay au survol -->
            <div class="search-view__result-overlay">
              <span class="search-view__result-overlay-icon">🔍</span>
              <span class="search-view__result-overlay-text">Analyser</span>
            </div>
          </div>

          <div class="search-view__result-info">
            <h3 class="search-view__result-title" :title="result.title">
              {{ truncate(result.title, 60) }}
            </h3>
            <p v-if="result.author" class="search-view__result-author">
              {{ result.author }}
            </p>
            <div class="search-view__result-meta">
              <span v-if="result.status" class="search-view__result-status">
                {{ result.status }}
              </span>
              <span v-if="result.language" class="search-view__result-language">
                {{ getLanguageFlag(result.language) }} {{ result.language.toUpperCase() }}
              </span>
            </div>
          </div>
        </article>
      </div>

      <!-- Actions de recherche -->
      <div class="search-view__results-actions">
        <NexusButton
          variant="neutral"
          size="sm"
          @click="clearSearch"
        >
          🔄 Nouvelle recherche
        </NexusButton>
      </div>
    </div>

    <!-- ====================================================================
      AUCUN RÉSULTAT
    ==================================================================== -->
    <div v-else-if="hasSearched && !loading" class="search-view__empty">
      <span class="search-view__empty-icon" aria-hidden="true">📭</span>
      <h2 class="search-view__empty-title">
        Aucun résultat
      </h2>
      <p class="search-view__empty-text">
        Aucune série ne correspond à « <strong>{{ lastSearchQuery }}</strong> ».
      </p>
      <div class="search-view__empty-hints">
        <p class="search-view__empty-hint">
          💡 Vérifiez l'orthographe ou essayez un autre terme
        </p>
        <p class="search-view__empty-hint">
          💡 Essayez avec le titre original (japonais, coréen, anglais)
        </p>
        <p class="search-view__empty-hint">
          💡 Sélectionnez un provider spécifique ou changez de provider
        </p>
      </div>
      <div class="search-view__empty-actions">
        <NexusButton
          variant="neutral"
          size="md"
          @click="clearSearch"
        >
          🔄 Réessayer
        </NexusButton>
      </div>
    </div>

    <!-- ====================================================================
      PIED DE PAGE
    ==================================================================== -->
    <footer v-if="hasSearched || analysisResult" class="search-view__footer">
      <span class="search-view__footer-info">
        <span v-if="analysisResult">
          Analyse terminée · {{ analysisResult.total_chapters || 0 }} chapitres
        </span>
        <span v-else-if="searchResults.length > 0">
          {{ totalResults }} résultat(s) pour « {{ lastSearchQuery }} »
        </span>
      </span>
      <span v-if="lastUpdated" class="search-view__footer-updated">
        Dernière mise à jour : {{ formatDateTime(lastUpdated) }}
      </span>
    </footer>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useProvidersStore } from '@/stores/providers'
import { useJobsStore } from '@/stores/jobs'
import NexusButton from '@/components/common/NexusButton.vue'
import NexusSelect from '@/components/common/NexusSelect.vue'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import ChapterList from '@/components/ChapterList.vue'
import { truncate, formatDateTime as fmtDateTime } from '@/utils/formatters'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const router = useRouter()
const route = useRoute()
const api = useApi()
const toast = useToast()
const providersStore = useProvidersStore()
const jobsStore = useJobsStore()

// ==========================================================================
//  État réactif
// ==========================================================================

const searchQuery = ref('')
const lastSearchQuery = ref('')
const selectedProviderId = ref('')
const searchResults = ref([])
const totalResults = ref(0)
const loading = ref(false)
const loadingChapters = ref(false)
const error = ref(null)
const errorHint = ref('')
const hasSearched = ref(false)
const lastUpdated = ref(null)
const searchInputRef = ref(null)

// Analyse
const analysisResult = ref(null)
const selectedChapterIds = ref([])
const downloading = ref(false)
const coverError = ref(false)

// ==========================================================================
//  Configuration
// ==========================================================================

const examples = [
  {
    icon: '🇫🇷',
    title: 'SushiScan',
    description: 'Mangas et manhwas en français',
    url: 'https://sushiscan.net/manga/one-piece/',
  },
  {
    icon: '🌍',
    title: 'Asura Scans',
    description: 'Manhwas et webtoons en anglais',
    url: 'https://asurascans.com/manga/solo-leveling/',
  },
  {
    icon: '🧬',
    title: 'MangaDex',
    description: 'Bibliothèque multi-langues',
    url: 'https://mangadex.org/title/solo-leveling',
  },
  {
    icon: '🔞',
    title: 'nHentai',
    description: 'Doujinshi (NSFW)',
    url: 'https://nhentai.net/g/123456/',
  },
]

// ==========================================================================
//  Computed
// ==========================================================================

const providers = computed(() => providersStore.filteredProviders || [])

const providerOptions = computed(() => {
  return [
    { value: '', label: '🌍 Tous les providers' },
    ...providers.value.map((p) => ({
      value: p.id,
      label: `${p.nsfw ? '🔞 ' : ''}${p.name}`,
    })),
  ]
})

const isUrlSearch = computed(() => {
  const q = searchQuery.value.trim()
  return q.startsWith('http://') || q.startsWith('https://')
})

const searchPlaceholder = computed(() => {
  return 'Rechercher une série ou coller une URL (https://...)'
})

// ==========================================================================
//  Méthodes — Recherche
// ==========================================================================

/**
 * Gère la soumission de la recherche.
 */
async function handleSearch() {
  const query = searchQuery.value.trim()
  if (!query) {
    toast.warning('Veuillez saisir un terme de recherche ou une URL', '⚠️')
    return
  }

  error.value = null
  errorHint.value = ''
  coverError.value = false
  analysisResult.value = null
  searchResults.value = []
  totalResults.value = 0
  selectedChapterIds.value = []

  if (isUrlSearch.value) {
    await analyzeUrl(query)
  } else {
    await searchByTitle(query)
  }
}

/**
 * Recherche par titre sur tous les providers (ou un spécifique).
 * @param {string} query
 */
async function searchByTitle(query) {
  loading.value = true
  hasSearched.value = true
  lastSearchQuery.value = query

  try {
    const params = {
      q: query,
      provider: selectedProviderId.value || undefined,
      limit: 50,
    }

    const response = await api.get('/browse/search', { params })

    // Normaliser la réponse
    let results = []
    if (Array.isArray(response)) {
      results = response
    } else if (Array.isArray(response.results)) {
      results = response.results
    } else if (Array.isArray(response.data)) {
      results = response.data
    }

    searchResults.value = results.map((r) => normalizeSearchResult(r))
    totalResults.value = searchResults.value.length
    lastUpdated.value = new Date().toISOString()

    if (totalResults.value === 0) {
      toast.info('Aucun résultat trouvé', '🔍')
    } else {
      toast.success(`${totalResults.value} résultat(s) trouvé(s)`, '✅')
    }
  } catch (err) {
    console.error('Erreur recherche:', err)
    handleSearchError(err)
  } finally {
    loading.value = false
  }
}

/**
 * Analyse une URL directe.
 * @param {string} url
 */
async function analyzeUrl(url) {
  loading.value = true
  loadingChapters.value = true
  hasSearched.value = true
  lastSearchQuery.value = url

  try {
    const response = await api.post('/browse/analyze', { url })
    const data = response.data || response

    analysisResult.value = normalizeAnalysis(data)
    lastUpdated.value = new Date().toISOString()

    // Sélectionner tous les chapitres par défaut
    if (analysisResult.value.chapters?.length) {
      selectedChapterIds.value = analysisResult.value.chapters.map((c) => c.id)
      toast.success(
        `"${analysisResult.value.title}" — ${analysisResult.value.total_chapters} chapitres`,
        '✅'
      )
    } else {
      toast.warning('Aucun chapitre trouvé pour cette série', '⚠️')
    }
  } catch (err) {
    console.error('Erreur analyse URL:', err)
    handleSearchError(err, true)
  } finally {
    loading.value = false
    loadingChapters.value = false
  }
}

/**
 * Analyse un résultat de recherche (clic sur une carte).
 * @param {Object} result
 */
async function analyzeResult(result) {
  if (!result.url) {
    toast.error('URL de la série manquante', '❌')
    return
  }

  searchQuery.value = result.url
  await analyzeUrl(result.url)
}

/**
 * Réinitialise la recherche.
 */
function clearSearch() {
  searchQuery.value = ''
  lastSearchQuery.value = ''
  searchResults.value = []
  totalResults.value = 0
  analysisResult.value = null
  selectedChapterIds.value = []
  error.value = null
  errorHint.value = ''
  hasSearched.value = false
  coverError.value = false
  nextTick(() => {
    searchInputRef.value?.focus()
  })
}

/**
 * Efface uniquement l'analyse en cours.
 */
function clearAnalysis() {
  analysisResult.value = null
  selectedChapterIds.value = []
  coverError.value = false
}

/**
 * Définit un exemple dans la recherche.
 * @param {string} url
 */
function setExample(url) {
  searchQuery.value = url
  handleSearch()
}

/**
 * Debounce de la saisie (non utilisé pour l'instant).
 */
function onSearchInput() {
  // Optionnel : recherche automatique avec debounce
}

// ==========================================================================
//  Méthodes — Sélection de chapitres
// ==========================================================================

function onChaptersSelected(ids) {
  selectedChapterIds.value = ids
}

function selectAllChapters() {
  if (analysisResult.value?.chapters) {
    selectedChapterIds.value = analysisResult.value.chapters.map((c) => c.id)
    toast.info(`Tous les chapitres sélectionnés (${selectedChapterIds.value.length})`, '✅', 1500)
  }
}

function deselectAllChapters() {
  selectedChapterIds.value = []
}

// ==========================================================================
//  Méthodes — Téléchargement
// ==========================================================================

/**
 * Télécharge les chapitres sélectionnés.
 */
async function handleDownloadSelected() {
  if (selectedChapterIds.value.length === 0) {
    toast.warning('Sélectionnez au moins un chapitre', '⚠️')
    return
  }
  if (!analysisResult.value?.url) {
    toast.error('URL de la série manquante', '❌')
    return
  }

  downloading.value = true
  try {
    const job = await jobsStore.startDownload(
      analysisResult.value.url,
      selectedChapterIds.value,
      { provider_id: analysisResult.value.provider_id }
    )

    toast.success(
      `Téléchargement lancé (${selectedChapterIds.value.length} chapitres)`,
      '✅'
    )

    // Redirection vers la file d'attente après un court délai
    setTimeout(() => {
      router.push('/queue')
    }, 800)
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    downloading.value = false
  }
}

/**
 * Télécharge un chapitre individuel.
 * @param {Object} chapter
 */
async function onChapterDownload(chapter) {
  const chapterId = chapter.id || chapter.url
  if (!selectedChapterIds.value.includes(chapterId)) {
    selectedChapterIds.value.push(chapterId)
  }
  await handleDownloadSelected()
}

/**
 * Télécharge en masse les chapitres passés.
 * @param {Array} chapters
 */
async function onBulkDownload(chapters) {
  selectedChapterIds.value = chapters.map((c) => c.id || c.url)
  await handleDownloadSelected()
}

// ==========================================================================
//  Méthodes — Normalisation
// ==========================================================================

function normalizeSearchResult(raw) {
  return {
    series_id: raw.series_id || raw.id || '',
    title: raw.title || 'Sans titre',
    alt_titles: raw.alt_titles || [],
    author: raw.author || '',
    cover_url: raw.cover_url || '',
    url: raw.url || '',
    provider_id: raw.provider_id || '',
    provider_name: raw.provider_name || raw.provider_id || '',
    genre: raw.genre || [],
    status: raw.status || '',
    nsfw: raw.nsfw || false,
    language: raw.language || 'fr',
  }
}

function normalizeAnalysis(raw) {
  return {
    title: raw.title || 'Sans titre',
    url: raw.url || '',
    provider_id: raw.provider_id || '',
    author: raw.author || '',
    description: raw.description || '',
    cover_url: raw.cover_url || '',
    genre: Array.isArray(raw.genre) ? raw.genre : raw.genres || [],
    status: raw.status || 'unknown',
    year: raw.year || null,
    language: raw.language || 'fr',
    nsfw: raw.nsfw || false,
    chapters: Array.isArray(raw.chapters) ? raw.chapters : [],
    total_chapters: raw.total_chapters || (raw.chapters ? raw.chapters.length : 0),
  }
}

// ==========================================================================
//  Méthodes — Gestion d'erreurs
// ==========================================================================

function handleSearchError(err, isAnalysis = false) {
  const status = err.response?.status
  const detail = err.response?.data?.detail

  if (status === 400) {
    error.value = detail || 'Requête invalide.'
    errorHint.value = isAnalysis
      ? 'Vérifiez que l\'URL est valide et complète.'
      : 'Essayez un autre terme de recherche.'
  } else if (status === 404) {
    error.value = isAnalysis
      ? 'La série n\'a pas été trouvée sur ce site.'
      : 'Aucun résultat trouvé.'
    errorHint.value = 'Essayez avec un autre provider ou une autre URL.'
  } else if (status === 429) {
    error.value = 'Trop de requêtes. Veuillez patienter.'
    errorHint.value = 'Réessayez dans quelques secondes.'
  } else if (status >= 500) {
    error.value = 'Le serveur est temporairement indisponible.'
    errorHint.value = 'Réessayez dans quelques instants.'
  } else if (!err.response) {
    error.value = 'Impossible de contacter le serveur.'
    errorHint.value = 'Vérifiez votre connexion Internet.'
  } else {
    error.value = detail || 'Une erreur est survenue.'
    errorHint.value = ''
  }

  toast.error(error.value, '❌')
}

// ==========================================================================
//  Méthodes — Utilitaires
// ==========================================================================

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
  return flags[lang?.toLowerCase()] || '🌐'
}

function onResultCoverError(event) {
  event.target.style.display = 'none'
}

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
  // Charger les providers si nécessaire
  if (providersStore.total === 0) {
    providersStore.fetchProviders().catch(() => null)
  }

  // Restaurer une recherche depuis la query string
  const q = route.query.q
  if (q && typeof q === 'string') {
    searchQuery.value = q
    await handleSearch()
  }

  // Focus sur l'input
  nextTick(() => {
    searchInputRef.value?.focus()
  })
})

onUnmounted(() => {
  // Nettoyage
})

// ==========================================================================
//  Watchers
// ==========================================================================

// Fermer l'analyse si on change de provider
watch(selectedProviderId, () => {
  if (analysisResult.value) {
    // On ne ferme pas automatiquement, mais on pourrait demander
  }
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.search-view {
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

.search-view__header {
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.search-view__header-left {
  min-width: 200px;
}

.search-view__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.search-view__subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Search zone
// ==========================================================================

.search-view__search-zone {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  transition: all 0.2s ease;

  &:focus-within {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
  }
}

.search-view__search-input-wrapper {
  position: relative;
  flex: 1;
  min-width: 250px;
  display: flex;
  align-items: center;
}

.search-view__search-icon {
  position: absolute;
  left: 0.7rem;
  font-size: 1rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
}

.search-view__search-input {
  width: 100%;
  padding: 0.7rem 2.4rem 0.7rem 2.4rem;
  font-size: 0.9rem;
  font-family: inherit;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  transition: all 0.15s ease;

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

.search-view__search-clear {
  position: absolute;
  right: 0.4rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: var(--radius-sm, 4px);
  transition: all 0.15s ease;

  &:hover {
    color: var(--color-text-primary, #e8edf5);
    background: var(--color-bg-hover, #253254);
  }
}

// ==========================================================================
//  Quick info
// ==========================================================================

.search-view__quick-info {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  font-size: 0.72rem;
}

.search-view__quick-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: var(--color-text-muted, #6a7a9a);
}

.search-view__quick-icon {
  font-size: 0.85rem;
}

// ==========================================================================
//  Suggestions
// ==========================================================================

.search-view__suggestions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
}

.search-view__suggestions-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.search-view__suggestions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.5rem;
}

.search-view__suggestion {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-primary, #00d4ff);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);

    .search-view__suggestion-icon {
      transform: scale(1.1);
    }
  }
}

.search-view__suggestion-icon {
  font-size: 1.4rem;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.search-view__suggestion-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.search-view__suggestion-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.search-view__suggestion-desc {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.3;
}

// ==========================================================================
//  Barre d'erreur
// ==========================================================================

.search-view__error {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.7rem 0.85rem;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.35);
  border-radius: var(--radius-md, 8px);
  color: var(--color-error, #f44336);
  font-size: 0.82rem;
  animation: searchErrorIn 0.3s ease;
}

@keyframes searchErrorIn {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.search-view__error-icon {
  flex-shrink: 0;
  font-size: 1rem;
  margin-top: 0.05rem;
}

.search-view__error-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.search-view__error-text {
  font-weight: 500;
}

.search-view__error-hint {
  font-size: 0.72rem;
  opacity: 0.85;
  font-style: italic;
}

.search-view__error-close {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
  padding: 0 0.2rem;
  opacity: 0.7;
  transition: opacity 0.15s ease;

  &:hover {
    opacity: 1;
  }
}

// ==========================================================================
//  Loading
// ==========================================================================

.search-view__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem 1rem;
  min-height: 300px;
  text-align: center;
}

.search-view__loading-text {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-text-secondary, #b0c0d8);
}

.search-view__loading-hint {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
  font-style: italic;
}

// ==========================================================================
//  Empty
// ====================================================================

.search-view__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem 1rem;
  min-height: 350px;
  text-align: center;
}

.search-view__empty-icon {
  font-size: 4rem;
  opacity: 0.5;
  margin-bottom: 0.5rem;
}

.search-view__empty-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.search-view__empty-text {
  margin: 0;
  max-width: 400px;
  font-size: 0.9rem;
  color: var(--color-text-secondary, #b0c0d8);

  strong {
    color: var(--color-primary, #00d4ff);
  }
}

.search-view__empty-hints {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-top: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  text-align: left;
}

.search-view__empty-hint {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.5;
}

.search-view__empty-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

// ==========================================================================
//  Analysis
// ==========================================================================

.search-view__analysis {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  animation: searchAnalysisIn 0.3s ease;
}

@keyframes searchAnalysisIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.search-view__analysis-card {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1rem;
  padding: 1rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
}

// ==========================================================================
//  Analysis sidebar
// ==========================================================================

.search-view__analysis-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  position: sticky;
  top: 1rem;
  max-height: calc(100vh - 2rem);
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 5px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
    border-radius: 3px;
  }
}

.search-view__cover-wrapper {
  width: 100%;
  aspect-ratio: 2/3;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border, #1a2538);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.search-view__cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.search-view__cover-placeholder {
  font-size: 3rem;
  color: var(--color-text-muted, #6a7a9a);
  opacity: 0.5;
}

.search-view__analysis-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.search-view__analysis-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  line-height: 1.3;
}

.search-view__analysis-author {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
}

.search-view__analysis-provider {
  margin: 0.15rem 0 0;
  font-size: 0.7rem;
  color: var(--color-primary, #00d4ff);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 500;
}

.search-view__genres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem;
}

.search-view__genre {
  font-size: 0.62rem;
  padding: 0.1rem 0.45rem;
  background: rgba(0, 212, 255, 0.1);
  color: var(--color-primary, #00d4ff);
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 9999px;
  text-transform: lowercase;
  white-space: nowrap;
}

.search-view__description {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-secondary, #b0c0d8);
  line-height: 1.5;
  max-height: 120px;
  overflow-y: auto;
  padding-right: 0.3rem;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
    border-radius: 2px;
  }
}

.search-view__analysis-actions {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
}

// ==========================================================================
//  Analysis main
// ==========================================================================

.search-view__analysis-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

// ==========================================================================
//  Results
// ==========================================================================

.search-view__results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.search-view__results-header {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.search-view__results-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.search-view__results-query {
  margin: 0;
  font-size: 0.82rem;
  color: var(--color-text-muted, #6a7a9a);

  strong {
    color: var(--color-primary, #00d4ff);
  }
}

.search-view__results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 0.85rem;
}

.search-view__result-card {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-3px);
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);

    .search-view__result-overlay {
      opacity: 1;
    }

    .search-view__result-cover {
      transform: scale(1.05);
    }
  }
}

.search-view__result-cover-wrapper {
  position: relative;
  aspect-ratio: 2/3;
  background: var(--color-bg-secondary, #141a2b);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-view__result-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.3s ease;
}

.search-view__result-cover-placeholder {
  font-size: 3rem;
  color: var(--color-text-muted, #6a7a9a);
  opacity: 0.5;
}

.search-view__result-provider {
  position: absolute;
  top: 0.3rem;
  left: 0.3rem;
  padding: 0.15rem 0.45rem;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  color: #ffffff;
  font-size: 0.6rem;
  font-weight: 600;
  border-radius: 9999px;
  max-width: 80%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-view__result-nsfw {
  position: absolute;
  top: 0.3rem;
  right: 0.3rem;
  font-size: 0.85rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.6));
}

.search-view__result-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.85) 0%, transparent 50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding: 0.75rem;
  gap: 0.3rem;
  opacity: 0;
  transition: opacity 0.2s ease;
  color: #ffffff;
}

.search-view__result-overlay-icon {
  font-size: 1.8rem;
  margin-bottom: 0.2rem;
}

.search-view__result-overlay-text {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.search-view__result-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.5rem 0.6rem;
}

.search-view__result-title {
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

.search-view__result-author {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-view__result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  align-items: center;
  font-size: 0.65rem;
  margin-top: 0.15rem;
}

.search-view__result-status {
  padding: 0.05rem 0.35rem;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-muted, #6a7a9a);
  border-radius: 9999px;
  text-transform: capitalize;
}

.search-view__result-language {
  color: var(--color-text-muted, #6a7a9a);
}

.search-view__results-actions {
  display: flex;
  justify-content: center;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
}

// ==========================================================================
//  Footer
// ==========================================================================

.search-view__footer {
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

.search-view__footer-updated {
  font-style: italic;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 900px) {
  .search-view__analysis-card {
    grid-template-columns: 1fr;
  }

  .search-view__analysis-sidebar {
    position: static;
    max-height: none;
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 0.75rem;
    align-items: start;
  }

  .search-view__cover-wrapper {
    grid-row: span 3;
  }

  .search-view__genres,
  .search-view__description {
    grid-column: 2;
  }

  .search-view__analysis-actions {
    grid-column: 1 / -1;
  }
}

@media (max-width: 640px) {
  .search-view {
    padding: 0.5rem;
  }

  .search-view__title {
    font-size: 1.2rem;
  }

  .search-view__search-zone {
    flex-direction: column;
    align-items: stretch;
  }

  .search-view__search-input-wrapper {
    min-width: 0;
  }

  .search-view__suggestions-grid {
    grid-template-columns: 1fr;
  }

  .search-view__results-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }

  .search-view__analysis-sidebar {
    grid-template-columns: 1fr;
  }

  .search-view__cover-wrapper {
    grid-row: auto;
    max-width: 180px;
    margin: 0 auto;
  }

  .search-view__genres,
  .search-view__description,
  .search-view__analysis-actions {
    grid-column: auto;
  }

  .search-view__result-overlay {
    opacity: 1;
    background: rgba(0, 0, 0, 0.7);
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .search-view__search-zone,
  .search-view__suggestions,
  .search-view__analysis-card,
  .search-view__result-card {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .search-view__title,
  .search-view__suggestions-title,
  .search-view__suggestion-title,
  .search-view__analysis-title,
  .search-view__result-title,
  .search-view__results-title,
  .search-view__empty-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .search-view__subtitle,
  .search-view__suggestion-desc,
  .search-view__analysis-author,
  .search-view__result-author,
  .search-view__empty-text {
    color: var(--color-text-muted, #7a8a9a);
  }

  .search-view__search-input {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .search-view__quick-info,
  .search-view__empty-hints,
  .search-view__footer {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .search-view__suggestion {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);

    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
    }
  }

  .search-view__cover-wrapper,
  .search-view__result-cover-wrapper {
    background: var(--color-bg-secondary, #e9ecf2);
  }

  .search-view__genre {
    background: rgba(0, 102, 204, 0.1);
    color: var(--color-primary, #0066cc);
    border-color: rgba(0, 102, 204, 0.25);
  }

  .search-view__result-status {
    background: var(--color-bg-secondary, #e9ecf2);
  }

  .search-view__error {
    background: rgba(198, 40, 40, 0.1);
    border-color: rgba(198, 40, 40, 0.35);
    color: var(--color-error, #c62828);
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .search-view__analysis,
  .search-view__error {
    animation: none !important;
  }

  .search-view__suggestion:hover,
  .search-view__result-card:hover {
    transform: none;
  }

  .search-view__result-cover {
    transition: none;
  }
}
</style>
