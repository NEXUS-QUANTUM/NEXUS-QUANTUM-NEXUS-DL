<!-- ==========================================================================
  NexusDL 2.0 - Share View (version complète)
  Fichier : frontend/src/views/share/ShareView.vue
  Description : Vue de partage PWA — Permet de recevoir des URLs et des
                fichiers partagés depuis d'autres applications (Web Share
                Target API). Analyse et lance les téléchargements.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="share-view">
    <!-- ====================================================================
      ÉTAPE 1 — Chargement / Analyse de la cible partagée
    ==================================================================== -->
    <div v-if="step === 'loading'" class="share-view__loading">
      <div class="share-view__loading-content">
        <NexusSpinner size="xl" variant="gradient" />
        <h1 class="share-view__loading-title">🧬 NexusDL</h1>
        <p class="share-view__loading-text">Analyse du contenu partagé...</p>
        <p v-if="shareSource" class="share-view__loading-source">
          Source : <strong>{{ shareSource }}</strong>
        </p>
      </div>
    </div>

    <!-- ====================================================================
      ÉTAPE 2 — Erreur
    ==================================================================== -->
    <div v-else-if="step === 'error'" class="share-view__error">
      <div class="share-view__error-content">
        <span class="share-view__error-icon" aria-hidden="true">❌</span>
        <h1 class="share-view__error-title">Impossible d'analyser</h1>
        <p class="share-view__error-message">{{ errorMessage }}</p>
        <div class="share-view__error-actions">
          <NexusButton variant="primary" @click="retryAnalysis">
            🔄 Réessayer
          </NexusButton>
          <NexusButton variant="neutral" @click="goHome">
            🏠 Retour à l'accueil
          </NexusButton>
        </div>
      </div>
    </div>

    <!-- ====================================================================
      ÉTAPE 3 — Analyse réussie : affichage des chapitres
    ==================================================================== -->
    <div v-else-if="step === 'analyzed'" class="share-view__analyzed">
      <!-- En-tête -->
      <header class="share-view__header">
        <button
          type="button"
          class="share-view__back"
          @click="goHome"
          aria-label="Retour à l'accueil"
        >
          <span aria-hidden="true">←</span>
        </button>
        <div class="share-view__header-info">
          <h1 class="share-view__header-title">📤 Contenu partagé</h1>
          <p class="share-view__header-subtitle">
            {{ analysisResult?.title || 'Série inconnue' }}
          </p>
        </div>
        <span class="share-view__header-badge">
          {{ analysisResult?.provider_id || 'auto' }}
        </span>
      </header>

      <!-- Carte d'analyse -->
      <div class="share-view__result">
        <!-- Sidebar -->
        <aside class="share-view__sidebar">
          <div class="share-view__cover-wrapper">
            <img
              v-if="analysisResult?.cover_url"
              :src="analysisResult.cover_url"
              :alt="`Couverture de ${analysisResult.title}`"
              class="share-view__cover"
              loading="lazy"
              @error="onCoverError"
            />
            <div v-else class="share-view__cover-placeholder">
              <span aria-hidden="true">📖</span>
            </div>
          </div>

          <div class="share-view__info">
            <h2 class="share-view__info-title">{{ analysisResult?.title }}</h2>
            <p v-if="analysisResult?.author" class="share-view__info-author">
              ✍️ {{ analysisResult.author }}
            </p>
            <p class="share-view__info-chapters">
              📚 {{ analysisResult?.total_chapters || 0 }} chapitre(s)
            </p>
          </div>

          <div v-if="analysisResult?.genre?.length" class="share-view__genres">
            <span
              v-for="g in analysisResult.genre"
              :key="g"
              class="share-view__genre"
            >
              {{ g }}
            </span>
          </div>

          <p v-if="analysisResult?.description" class="share-view__description">
            {{ truncate(analysisResult.description, 200) }}
          </p>

          <!-- Bouton principal -->
          <div class="share-view__sidebar-actions">
            <NexusButton
              variant="primary"
              size="lg"
              block
              :loading="downloading"
              :disabled="selectedChapterIds.length === 0"
              @click="startDownload"
            >
              ⬇️ Télécharger ({{ selectedChapterIds.length }})
            </NexusButton>
            <NexusButton
              variant="neutral"
              size="sm"
              block
              @click="selectAllChapters"
            >
              Tout sélectionner
            </NexusButton>
            <NexusButton
              variant="neutral"
              size="sm"
              block
              @click="deselectAllChapters"
            >
              Tout désélectionner
            </NexusButton>
          </div>
        </aside>

        <!-- Liste des chapitres -->
        <main class="share-view__chapters">
          <ChapterList
            :chapters="analysisResult?.chapters || []"
            :total-chapters="analysisResult?.total_chapters || 0"
            :loading="loadingChapters"
            selectable
            downloadable
            searchable
            sortable
            paginated
            :page-size="25"
            :initial-selected="selectedChapterIds"
            @update:selected="onChaptersSelected"
            @download="onChapterDownload"
            @bulk-download="onBulkDownload"
          />
        </main>
      </div>
    </div>

    <!-- ====================================================================
      ÉTAPE 4 — Téléchargement en cours / terminé
    ==================================================================== -->
    <div v-else-if="step === 'downloading'" class="share-view__download">
      <div class="share-view__download-content">
        <NexusSpinner size="xl" variant="gradient" />
        <h1 class="share-view__download-title">Téléchargement en cours...</h1>
        <p class="share-view__download-text">
          {{ jobProgress }}% — {{ currentChapter || 'Préparation...' }}
        </p>
        <div class="share-view__download-progress">
          <div
            class="share-view__download-progress-bar"
            :style="{ width: `${jobProgress}%` }"
          />
        </div>
        <NexusButton variant="neutral" @click="goToQueue">
          ⏳ Voir la file d'attente
        </NexusButton>
      </div>
    </div>

    <!-- ====================================================================
      ÉTAPE 5 — Téléchargement terminé
    ==================================================================== -->
    <div v-else-if="step === 'completed'" class="share-view__completed">
      <div class="share-view__completed-content">
        <span class="share-view__completed-icon" aria-hidden="true">🎉</span>
        <h1 class="share-view__completed-title">Téléchargement terminé !</h1>
        <p class="share-view__completed-text">
          {{ analysisResult?.title }} a été ajouté à votre bibliothèque.
        </p>
        <div class="share-view__completed-actions">
          <NexusButton variant="primary" @click="goToLibrary">
            📚 Voir dans la bibliothèque
          </NexusButton>
          <NexusButton variant="neutral" @click="goHome">
            🏠 Retour à l'accueil
          </NexusButton>
        </div>
      </div>
    </div>

    <!-- ====================================================================
      ÉTAPE 0 — Aucune donnée partagée
    ==================================================================== -->
    <div v-else class="share-view__empty">
      <div class="share-view__empty-content">
        <span class="share-view__empty-icon" aria-hidden="true">📤</span>
        <h1 class="share-view__empty-title">Aucun contenu partagé</h1>
        <p class="share-view__empty-text">
          Cette page est utilisée pour recevoir du contenu partagé depuis d'autres
          applications (URLs, fichiers CBZ). Utilisez le partage natif de votre
          appareil pour envoyer une URL ou un fichier vers NexusDL.
        </p>
        <div class="share-view__empty-actions">
          <NexusButton variant="primary" @click="goHome">
            🏠 Retour à l'accueil
          </NexusButton>
          <NexusButton variant="neutral" @click="goToSearch">
            🔍 Rechercher manuellement
          </NexusButton>
        </div>

        <!-- Aide sur le partage -->
        <div class="share-view__help">
          <h2 class="share-view__help-title">Comment partager vers NexusDL ?</h2>
          <ol class="share-view__help-list">
            <li>Ouvrez une page de manga dans votre navigateur</li>
            <li>Appuyez sur le bouton <strong>Partager</strong></li>
            <li>Sélectionnez <strong>NexusDL</strong> dans la liste</li>
            <li>L'analyse démarre automatiquement</li>
          </ol>
          <p class="share-view__help-note">
            💡 Sur ordinateur, vous pouvez aussi coller directement l'URL dans la
            zone de recherche.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusButton from '@/components/common/NexusButton.vue'
import ChapterList from '@/components/ChapterList.vue'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useJobsStore } from '@/stores/jobs'
import { useLibraryStore } from '@/stores/library'
import { truncate } from '@/utils/formatters'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const router = useRouter()
const route = useRoute()
const api = useApi()
const toast = useToast()
const jobsStore = useJobsStore()
const libraryStore = useLibraryStore()

// ==========================================================================
//  État réactif
// ==========================================================================

const step = ref('loading') // loading | error | analyzed | downloading | completed | empty
const errorMessage = ref('')
const shareSource = ref('')

const analysisResult = ref(null)
const loadingChapters = ref(false)
const selectedChapterIds = ref([])
const downloading = ref(false)
const jobProgress = ref(0)
const currentChapter = ref('')
const currentJobId = ref(null)

let progressPollTimer = null

// ==========================================================================
//  Computed
// ==========================================================================

const isShareRoute = computed(() => route.path === '/share')

// ==========================================================================
//  Méthodes — Analyse du contenu partagé
// ==========================================================================

/**
 * Point d'entrée : analyse le contenu partagé (URL ou fichier).
 * Appelé au montage.
 */
async function processSharedContent() {
  step.value = 'loading'
  errorMessage.value = ''

  // Récupérer les données partagées via la query string (share_target PWA)
  const sharedUrl = route.query.url || route.query.text
  const sharedTitle = route.query.title

  // Cas 1 : URL partagée
  if (sharedUrl && (sharedUrl.startsWith('http://') || sharedUrl.startsWith('https://'))) {
    shareSource.value = extractDomain(sharedUrl)
    await analyzeUrl(sharedUrl)
    return
  }

  // Cas 2 : texte partagé contenant une URL
  if (sharedUrl && typeof sharedUrl === 'string') {
    const urlMatch = sharedUrl.match(/https?:\/\/[^\s]+/)
    if (urlMatch) {
      shareSource.value = extractDomain(urlMatch[0])
      await analyzeUrl(urlMatch[0])
      return
    }
  }

  // Cas 3 : depuis le state (navigation interne)
  const stateUrl = window.history.state?.url
  if (stateUrl) {
    shareSource.value = extractDomain(stateUrl)
    await analyzeUrl(stateUrl)
    return
  }

  // Cas 4 : aucun contenu partagé
  step.value = 'empty'
}

/**
 * Analyse une URL de série.
 * @param {string} url
 */
async function analyzeUrl(url) {
  try {
    const response = await api.post('/browse/analyze', { url })

    // Normaliser la réponse
    const data = response.data || response
    analysisResult.value = normalizeAnalysis(data)

    if (!analysisResult.value.chapters?.length) {
      errorMessage.value = 'Aucun chapitre trouvé pour cette série.'
      step.value = 'error'
      return
    }

    // Sélectionner tous les chapitres par défaut
    selectedChapterIds.value = analysisResult.value.chapters.map((c) => c.id)

    step.value = 'analyzed'
    toast.success(`${analysisResult.value.title} — ${analysisResult.value.total_chapters} chapitres`, '✅')
  } catch (err) {
    console.error('Erreur analyse partage:', err)
    errorMessage.value = err.message || 'Impossible d\'analyser cette URL.'
    step.value = 'error'
  }
}

/**
 * Normalise les données d'analyse.
 * @param {Object} raw
 * @returns {Object}
 */
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
    language: raw.language || 'fr',
    nsfw: raw.nsfw || false,
    chapters: Array.isArray(raw.chapters) ? raw.chapters : [],
    total_chapters: raw.total_chapters || (raw.chapters ? raw.chapters.length : 0),
  }
}

/**
 * Extrait le domaine d'une URL.
 * @param {string} url
 * @returns {string}
 */
function extractDomain(url) {
  try {
    return new URL(url).hostname
  } catch (_) {
    return url
  }
}

// ==========================================================================
//  Méthodes — Sélection des chapitres
// ==========================================================================

function onChaptersSelected(ids) {
  selectedChapterIds.value = ids
}

function selectAllChapters() {
  if (analysisResult.value?.chapters) {
    selectedChapterIds.value = analysisResult.value.chapters.map((c) => c.id)
  }
}

function deselectAllChapters() {
  selectedChapterIds.value = []
}

// ==========================================================================
//  Méthodes — Téléchargement
// ==========================================================================

/**
 * Lance le téléchargement des chapitres sélectionnés.
 */
async function startDownload() {
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

    currentJobId.value = job.id
    step.value = 'downloading'
    jobProgress.value = 0
    currentChapter.value = 'Initialisation...'

    // Démarrer le polling de progression
    startProgressPolling()

    toast.success(`Téléchargement lancé (${selectedChapterIds.value.length} chapitres)`, '✅')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
    step.value = 'analyzed'
  } finally {
    downloading.value = false
  }
}

/**
 * Démarre le polling pour suivre la progression.
 */
function startProgressPolling() {
  stopProgressPolling()
  progressPollTimer = setInterval(async () => {
    if (!currentJobId.value) return
    try {
      const job = await jobsStore.fetchJob(currentJobId.value, true)
      if (job) {
        jobProgress.value = Math.round(job.progress || 0)
        currentChapter.value = job.current_chapter || ''

        if (job.status === 'completed') {
          stopProgressPolling()
          step.value = 'completed'
          // Rafraîchir la bibliothèque
          libraryStore.fetchLibrary()
          toast.success('Téléchargement terminé !', '🎉')
        } else if (job.status === 'failed') {
          stopProgressPolling()
          errorMessage.value = 'Le téléchargement a échoué.'
          step.value = 'error'
        } else if (job.status === 'cancelled') {
          stopProgressPolling()
          step.value = 'analyzed'
        }
      }
    } catch (err) {
      console.warn('Erreur polling progression:', err)
    }
  }, 2000)
}

/**
 * Arrête le polling.
 */
function stopProgressPolling() {
  if (progressPollTimer) {
    clearInterval(progressPollTimer)
    progressPollTimer = null
  }
}

/**
 * Télécharge un chapitre individuel.
 * @param {Object} chapter
 */
async function onChapterDownload(chapter) {
  if (!selectedChapterIds.value.includes(chapter.id)) {
    selectedChapterIds.value.push(chapter.id)
  }
  await startDownload()
}

/**
 * Télécharge en masse les chapitres passés.
 * @param {Array} chapters
 */
async function onBulkDownload(chapters) {
  selectedChapterIds.value = chapters.map((c) => c.id)
  await startDownload()
}

// ==========================================================================
//  Méthodes — Navigation & utilitaires
// ==========================================================================

function retryAnalysis() {
  processSharedContent()
}

function goHome() {
  router.push('/')
}

function goToLibrary() {
  router.push('/library')
}

function goToQueue() {
  router.push('/queue')
}

function goToSearch() {
  router.push('/search')
}

function onCoverError(event) {
  event.target.style.display = 'none'
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  await processSharedContent()
})

onUnmounted(() => {
  stopProgressPolling()
})

// ==========================================================================
//  Gestion de l'API Web Share Target (si supportée nativement)
// ==========================================================================

if ('share' in navigator && typeof navigator.canShare === 'function') {
  // Le partage natif est géré par le manifest.json (share_target)
  // Les données arrivent ici via la query string
}
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.share-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 1rem;
  background: var(--color-bg-primary, #0a0e1a);
}

// ==========================================================================
//  États centrés (loading, error, downloading, completed, empty)
// ==========================================================================

.share-view__loading,
.share-view__error,
.share-view__download,
.share-view__completed,
.share-view__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 80vh;
  padding: 2rem 1rem;
  text-align: center;
}

.share-view__loading-content,
.share-view__error-content,
.share-view__download-content,
.share-view__completed-content,
.share-view__empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  max-width: 560px;
  width: 100%;
}

// ==========================================================================
//  Loading
// ==========================================================================

.share-view__loading-title {
  margin: 0.5rem 0 0;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.share-view__loading-text {
  margin: 0;
  font-size: 1rem;
  color: var(--color-text-secondary, #b0c0d8);
}

.share-view__loading-source {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);

  strong {
    color: var(--color-primary, #00d4ff);
  }
}

// ==========================================================================
//  Error
// ==========================================================================

.share-view__error-icon {
  font-size: 4rem;
  margin-bottom: 0.5rem;
}

.share-view__error-title {
  margin: 0;
  font-size: 1.75rem;
  color: var(--color-text-primary, #e8edf5);
}

.share-view__error-message {
  margin: 0;
  font-size: 0.95rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.6;
}

.share-view__error-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 0.5rem;
}

// ==========================================================================
//  Analyzed — Layout principal
// ==========================================================================

.share-view__analyzed {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem;
}

.share-view__header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
}

.share-view__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-full, 9999px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  font-size: 1.1rem;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
    border-color: var(--color-primary, #00d4ff);
  }
}

.share-view__header-info {
  flex: 1;
  min-width: 0;
}

.share-view__header-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.share-view__header-subtitle {
  margin: 0.1rem 0 0;
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.share-view__header-badge {
  padding: 0.2rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
  border-radius: var(--radius-full, 9999px);
  white-space: nowrap;
}

// ==========================================================================
//  Résultat
// ==========================================================================

.share-view__result {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 1rem;
  align-items: start;
}

// ==========================================================================
//  Sidebar
// ==========================================================================

.share-view__sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  position: sticky;
  top: 1rem;
  max-height: calc(100vh - 2rem);
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
    border-radius: 3px;
  }
}

.share-view__cover-wrapper {
  width: 100%;
  aspect-ratio: 2/3;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.share-view__cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.share-view__cover-placeholder {
  font-size: 3rem;
  color: var(--color-text-muted, #6a7a9a);
}

.share-view__info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.share-view__info-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  line-height: 1.3;
}

.share-view__info-author {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
}

.share-view__info-chapters {
  margin: 0.15rem 0 0;
  font-size: 0.75rem;
  color: var(--color-text-secondary, #b0c0d8);
}

.share-view__genres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem;
}

.share-view__genre {
  font-size: 0.65rem;
  padding: 0.1rem 0.45rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  color: var(--color-text-muted, #6a7a9a);
  border-radius: var(--radius-sm, 4px);
  text-transform: lowercase;
}

.share-view__description {
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

.share-view__sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
}

// ==========================================================================
//  Liste des chapitres
// ==========================================================================

.share-view__chapters {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

// ==========================================================================
//  Downloading
// ==========================================================================

.share-view__download-title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.share-view__download-text {
  margin: 0;
  font-size: 1rem;
  color: var(--color-text-secondary, #b0c0d8);
  font-variant-numeric: tabular-nums;
}

.share-view__download-progress {
  width: 100%;
  max-width: 400px;
  height: 8px;
  background: var(--color-bg-input, #1e2a40);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
  margin: 0.5rem 0;
}

.share-view__download-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #0066ff);
  border-radius: var(--radius-full, 9999px);
  transition: width 0.4s ease;
}

// ==========================================================================
//  Completed
// ==========================================================================

.share-view__completed-icon {
  font-size: 5rem;
  animation: shareCompletedBounce 0.8s ease;
}

@keyframes shareCompletedBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

.share-view__completed-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #4caf50, #00d4ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.share-view__completed-text {
  margin: 0;
  font-size: 1rem;
  color: var(--color-text-secondary, #b0c0d8);
}

.share-view__completed-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 0.5rem;
}

// ==========================================================================
//  Empty
// ==========================================================================

.share-view__empty-icon {
  font-size: 4rem;
  margin-bottom: 0.5rem;
  opacity: 0.6;
}

.share-view__empty-title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.share-view__empty-text {
  margin: 0;
  font-size: 0.95rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.6;
}

.share-view__empty-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 0.5rem;
}

.share-view__help {
  margin-top: 1.5rem;
  padding: 1rem 1.25rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  text-align: left;
  max-width: 100%;
}

.share-view__help-title {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.share-view__help-list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.85rem;
  color: var(--color-text-secondary, #b0c0d8);
  line-height: 1.7;

  li {
    margin-bottom: 0.2rem;

    strong {
      color: var(--color-primary, #00d4ff);
    }
  }
}

.share-view__help-note {
  margin: 0.75rem 0 0;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border, #1a2538);
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
  font-style: italic;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 900px) {
  .share-view__result {
    grid-template-columns: 1fr;
  }

  .share-view__sidebar {
    position: static;
    max-height: none;
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 0.75rem;
    align-items: start;
  }

  .share-view__cover-wrapper {
    grid-row: span 3;
  }

  .share-view__genres,
  .share-view__description {
    grid-column: 2;
  }

  .share-view__sidebar-actions {
    grid-column: 1 / -1;
  }
}

@media (max-width: 600px) {
  .share-view__sidebar {
    grid-template-columns: 1fr;
  }

  .share-view__cover-wrapper {
    grid-row: auto;
    max-width: 180px;
    margin: 0 auto;
  }

  .share-view__genres,
  .share-view__description,
  .share-view__sidebar-actions {
    grid-column: auto;
  }

  .share-view__completed-title,
  .share-view__empty-title,
  .share-view__error-title,
  .share-view__download-title {
    font-size: 1.4rem;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .share-view {
    background: var(--color-bg-primary, #f4f6fa);
  }

  .share-view__header,
  .share-view__sidebar,
  .share-view__help {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .share-view__header-title,
  .share-view__info-title,
  .share-view__help-title,
  .share-view__error-title,
  .share-view__empty-title,
  .share-view__download-title,
  .share-view__completed-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .share-view__header-subtitle,
  .share-view__info-author,
  .share-view__loading-source,
  .share-view__error-message,
  .share-view__empty-text,
  .share-view__help-note {
    color: var(--color-text-muted, #7a8a9a);
  }

  .share-view__cover-wrapper {
    background: var(--color-bg-secondary, #e9ecf2);
  }

  .share-view__genre {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .share-view__download-progress {
    background: var(--color-bg-input, #f0f2f5);
  }

  .share-view__help-list {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .share-view__help-note {
    border-color: var(--color-border, #d0d8e0);
  }

  .share-view__description {
    color: var(--color-text-secondary, #3d4a5c);
  }
}
</style>
