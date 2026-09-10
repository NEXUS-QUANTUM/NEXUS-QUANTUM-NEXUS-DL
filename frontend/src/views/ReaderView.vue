<!-- ==========================================================================
  NexusDL 2.0 - Reader View (version complète)
  Fichier : frontend/src/views/ReaderView.vue
  Description : Lecteur de CBZ avancé. Affiche les images d'un chapitre avec
                navigation, zoom, plein écran, modes de lecture (simple/double),
                direction (LTR/RTL), ajustement, préchargement, raccourcis
                clavier, miniatures et suivi de progression.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div
    class="reader-view"
    :class="[
      `reader-view--theme-${settings.background}`,
      {
        'reader-view--fullscreen': isFullscreen,
        'reader-view--hidden-ui': uiHidden,
        'reader-view--rtl': settings.direction === 'rtl',
        'reader-view--double': settings.mode === 'double',
      },
    ]"
    @mousemove="handleMouseMove"
    @click="handleContainerClick"
    @wheel.prevent="handleWheel"
    @touchstart="handleTouchStart"
    @touchmove="handleTouchMove"
    @touchend="handleTouchEnd"
  >
    <!-- ====================================================================
      ÉTAT DE CHARGEMENT
    ==================================================================== -->
    <div v-if="loading" class="reader-view__loading">
      <NexusSpinner size="xl" variant="gradient" />
      <p class="reader-view__loading-text">Chargement du chapitre...</p>
      <div class="reader-view__loading-progress">
        <div
          class="reader-view__loading-progress-bar"
          :style="{ width: `${loadProgress}%` }"
        />
      </div>
    </div>

    <!-- ====================================================================
      ÉTAT D'ERREUR
    ==================================================================== -->
    <div v-else-if="error" class="reader-view__error">
      <span class="reader-view__error-icon" aria-hidden="true">❌</span>
      <h2 class="reader-view__error-title">Impossible de charger</h2>
      <p class="reader-view__error-message">{{ error }}</p>
      <div class="reader-view__error-actions">
        <NexusButton variant="primary" @click="loadChapter">
          🔄 Réessayer
        </NexusButton>
        <NexusButton variant="neutral" @click="closeReader">
          ← Retour
        </NexusButton>
      </div>
    </div>

    <!-- ====================================================================
      LECTEUR PRINCIPAL
    ==================================================================== -->
    <template v-else-if="pages.length > 0">
      <!-- ================================================================
        TOOLBAR SUPÉRIEURE
      ================================================================ -->
      <header
        class="reader-view__toolbar reader-view__toolbar--top"
        :class="{ 'reader-view__toolbar--hidden': uiHidden }"
      >
        <div class="reader-view__toolbar-left">
          <button
            type="button"
            class="reader-view__toolbar-btn"
            @click="closeReader"
            aria-label="Fermer le lecteur"
            title="Fermer (Échap)"
          >
            ✖
          </button>

          <div class="reader-view__chapter-info">
            <h1 class="reader-view__chapter-title" :title="chapterTitle">
              {{ chapterTitle }}
            </h1>
            <p class="reader-view__chapter-subtitle">
              Page {{ currentPage + 1 }} / {{ pages.length }}
            </p>
          </div>
        </div>

        <div class="reader-view__toolbar-center">
          <!-- Navigation entre chapitres -->
          <button
            type="button"
            class="reader-view__toolbar-btn"
            :disabled="!hasPreviousChapter"
            @click="goToPreviousChapter"
            aria-label="Chapitre précédent"
            title="Chapitre précédent"
          >
            ⏮
          </button>

          <button
            type="button"
            class="reader-view__toolbar-btn"
            :disabled="currentPage === 0"
            @click="goToFirstPage"
            aria-label="Première page"
            title="Première page (Début)"
          >
            ⇤
          </button>

          <button
            type="button"
            class="reader-view__toolbar-btn"
            :disabled="currentPage === 0"
            @click="goToPreviousPage"
            aria-label="Page précédente"
            title="Page précédente (←)"
          >
            ◀
          </button>

          <span class="reader-view__page-indicator">
            {{ currentPage + 1 }} / {{ pages.length }}
          </span>

          <button
            type="button"
            class="reader-view__toolbar-btn"
            :disabled="currentPage >= pages.length - 1"
            @click="goToNextPage"
            aria-label="Page suivante"
            title="Page suivante (→)"
          >
            ▶
          </button>

          <button
            type="button"
            class="reader-view__toolbar-btn"
            :disabled="currentPage >= pages.length - 1"
            @click="goToLastPage"
            aria-label="Dernière page"
            title="Dernière page (Fin)"
          >
            ⇥
          </button>

          <button
            type="button"
            class="reader-view__toolbar-btn"
            :disabled="!hasNextChapter"
            @click="goToNextChapter"
            aria-label="Chapitre suivant"
            title="Chapitre suivant"
          >
            ⏭
          </button>
        </div>

        <div class="reader-view__toolbar-right">
          <!-- Mode simple/double -->
          <button
            type="button"
            class="reader-view__toolbar-btn"
            @click="toggleMode"
            :aria-label="settings.mode === 'single' ? 'Passer en mode double page' : 'Passer en mode simple page'"
            :title="settings.mode === 'single' ? 'Mode double page (D)' : 'Mode simple page (D)'"
          >
            {{ settings.mode === 'single' ? '📄' : '📖' }}
          </button>

          <!-- Direction -->
          <button
            type="button"
            class="reader-view__toolbar-btn"
            @click="toggleDirection"
            :aria-label="settings.direction === 'ltr' ? 'Passer en lecture droite-à-gauche' : 'Passer en lecture gauche-à-droite'"
            :title="settings.direction === 'ltr' ? 'Lecture RTL (R)' : 'Lecture LTR (R)'"
          >
            {{ settings.direction === 'ltr' ? '➡️' : '⬅️' }}
          </button>

          <!-- Ajustement -->
          <button
            type="button"
            class="reader-view__toolbar-btn"
            @click="cycleFitMode"
            :aria-label="`Ajustement : ${settings.fit}`"
            :title="`Ajustement : ${settings.fit} (F)`"
          >
            {{ fitIcon }}
          </button>

          <!-- Thème fond -->
          <button
            type="button"
            class="reader-view__toolbar-btn"
            @click="cycleBackground"
            aria-label="Changer le fond"
            title="Fond (B)"
          >
            🎨
          </button>

          <!-- Miniatures -->
          <button
            type="button"
            class="reader-view__toolbar-btn"
            @click="toggleThumbnails"
            :aria-pressed="showThumbnails"
            aria-label="Miniatures"
            title="Miniatures (T)"
          >
            🖼️
          </button>

          <!-- Paramètres -->
          <button
            type="button"
            class="reader-view__toolbar-btn"
            @click="showSettings = !showSettings"
            :aria-pressed="showSettings"
            aria-label="Paramètres"
            title="Paramètres"
          >
            ⚙️
          </button>

          <!-- Plein écran -->
          <button
            type="button"
            class="reader-view__toolbar-btn"
            @click="toggleFullscreen"
            :aria-label="isFullscreen ? 'Quitter le plein écran' : 'Plein écran'"
            :title="isFullscreen ? 'Quitter le plein écran (F11)' : 'Plein écran (F11)'"
          >
            {{ isFullscreen ? '🗗' : '⛶' }}
          </button>
        </div>
      </header>

      <!-- ================================================================
        ZONE DE LECTURE
      ================================================================ -->
      <main
        ref="viewportRef"
        class="reader-view__viewport"
        :class="{
          'reader-view__viewport--fit-width': settings.fit === 'width',
          'reader-view__viewport--fit-height': settings.fit === 'height',
          'reader-view__viewport--fit-original': settings.fit === 'original',
          'reader-view__viewport--zoom-in': zoomLevel > 1,
        }"
      >
        <!-- Image courante (mode simple) -->
        <div
          v-if="settings.mode === 'single'"
          class="reader-view__page-container"
          :style="pageStyle"
        >
          <img
            ref="currentImageRef"
            :src="pages[currentPage]?.url"
            :alt="`Page ${currentPage + 1}`"
            class="reader-view__page"
            :class="{
              'reader-view__page--fit-width': settings.fit === 'width',
              'reader-view__page--fit-height': settings.fit === 'height',
              'reader-view__page--fit-original': settings.fit === 'original',
            }"
            :style="imageStyle"
            @load="onImageLoad"
            @error="onImageError"
            draggable="false"
          />
        </div>

        <!-- Images (mode double) -->
        <div v-else class="reader-view__double-container">
          <div
            v-for="idx in doublePageIndices"
            :key="idx"
            class="reader-view__page-container reader-view__page-container--half"
          >
            <img
              v-if="pages[idx]"
              :src="pages[idx].url"
              :alt="`Page ${idx + 1}`"
              class="reader-view__page"
              :class="{
                'reader-view__page--fit-width': settings.fit === 'width',
                'reader-view__page--fit-height': settings.fit === 'height',
                'reader-view__page--fit-original': settings.fit === 'original',
              }"
              draggable="false"
              @error="onImageError"
            />
            <div v-else class="reader-view__page-empty" />
          </div>
        </div>

        <!-- Indicateur de zoom -->
        <div v-if="zoomLevel !== 1" class="reader-view__zoom-indicator">
          <button
            type="button"
            class="reader-view__zoom-reset"
            @click="resetZoom"
            title="Réinitialiser le zoom"
          >
            {{ Math.round(zoomLevel * 100) }}%
          </button>
        </div>

        <!-- Flèches de navigation latérales (au survol) -->
        <button
          v-if="!uiHidden && currentPage > 0"
          type="button"
          class="reader-view__nav-arrow reader-view__nav-arrow--left"
          @click="goToPreviousPage"
          aria-label="Page précédente"
        >
          ◀
        </button>

        <button
          v-if="!uiHidden && currentPage < pages.length - 1"
          type="button"
          class="reader-view__nav-arrow reader-view__nav-arrow--right"
          @click="goToNextPage"
          aria-label="Page suivante"
        >
          ▶
        </button>
      </main>

      <!-- ================================================================
        TOOLBAR INFÉRIEURE
      ================================================================ -->
      <footer
        class="reader-view__toolbar reader-view__toolbar--bottom"
        :class="{ 'reader-view__toolbar--hidden': uiHidden }"
      >
        <div class="reader-view__progress-container">
          <input
            type="range"
            class="reader-view__progress-slider"
            :value="currentPage"
            :min="0"
            :max="pages.length - 1"
            step="1"
            @input="onSliderInput"
            :aria-label="`Page ${currentPage + 1} sur ${pages.length}`"
          />
        </div>

        <div class="reader-view__bottom-info">
          <span class="reader-view__bottom-page">
            Page {{ currentPage + 1 }} / {{ pages.length }}
          </span>
          <span v-if="chapterProgress" class="reader-view__bottom-progress">
            Progression : {{ chapterProgress }}%
          </span>
        </div>
      </footer>
    </template>

    <!-- ====================================================================
      PANNEAU DES MINIATURES
    ==================================================================== -->
    <Transition name="reader-view-slide-left">
      <aside
        v-if="showThumbnails"
        class="reader-view__thumbnails"
        aria-label="Miniatures des pages"
      >
        <header class="reader-view__thumbnails-header">
          <h2 class="reader-view__thumbnails-title">
            📖 Miniatures ({{ pages.length }})
          </h2>
          <button
            type="button"
            class="reader-view__thumbnails-close"
            @click="showThumbnails = false"
            aria-label="Fermer les miniatures"
          >
            ✖
          </button>
        </header>

        <div class="reader-view__thumbnails-grid">
          <button
            v-for="(page, idx) in pages"
            :key="idx"
            type="button"
            class="reader-view__thumbnail"
            :class="{ 'reader-view__thumbnail--active': idx === currentPage }"
            @click="goToPage(idx)"
            :aria-label="`Aller à la page ${idx + 1}`"
            :aria-current="idx === currentPage"
          >
            <img
              :src="page.thumbnail || page.url"
              :alt="`Miniature ${idx + 1}`"
              class="reader-view__thumbnail-img"
              loading="lazy"
            />
            <span class="reader-view__thumbnail-number">{{ idx + 1 }}</span>
          </button>
        </div>
      </aside>
    </Transition>

    <!-- ====================================================================
      PANNEAU DES PARAMÈTRES
    ==================================================================== -->
    <Transition name="reader-view-slide-right">
      <aside
        v-if="showSettings"
        class="reader-view__settings"
        aria-label="Paramètres du lecteur"
      >
        <header class="reader-view__settings-header">
          <h2 class="reader-view__settings-title">⚙️ Paramètres</h2>
          <button
            type="button"
            class="reader-view__settings-close"
            @click="showSettings = false"
            aria-label="Fermer les paramètres"
          >
            ✖
          </button>
        </header>

        <div class="reader-view__settings-body">
          <!-- Mode de lecture -->
          <div class="reader-view__setting">
            <label class="reader-view__setting-label">Mode de lecture</label>
            <div class="reader-view__setting-options">
              <button
                type="button"
                class="reader-view__setting-option"
                :class="{ 'reader-view__setting-option--active': settings.mode === 'single' }"
                @click="settings.mode = 'single'; saveSettings()"
              >
                📄 Simple
              </button>
              <button
                type="button"
                class="reader-view__setting-option"
                :class="{ 'reader-view__setting-option--active': settings.mode === 'double' }"
                @click="settings.mode = 'double'; saveSettings()"
              >
                📖 Double
              </button>
            </div>
          </div>

          <!-- Direction -->
          <div class="reader-view__setting">
            <label class="reader-view__setting-label">Direction de lecture</label>
            <div class="reader-view__setting-options">
              <button
                type="button"
                class="reader-view__setting-option"
                :class="{ 'reader-view__setting-option--active': settings.direction === 'ltr' }"
                @click="settings.direction = 'ltr'; saveSettings()"
              >
                ➡️ Gauche → Droite
              </button>
              <button
                type="button"
                class="reader-view__setting-option"
                :class="{ 'reader-view__setting-option--active': settings.direction === 'rtl' }"
                @click="settings.direction = 'rtl'; saveSettings()"
              >
                ⬅️ Droite → Gauche
              </button>
            </div>
          </div>

          <!-- Ajustement -->
          <div class="reader-view__setting">
            <label class="reader-view__setting-label">Ajustement des images</label>
            <div class="reader-view__setting-options">
              <button
                type="button"
                class="reader-view__setting-option"
                :class="{ 'reader-view__setting-option--active': settings.fit === 'width' }"
                @click="settings.fit = 'width'; saveSettings()"
              >
                ↔️ Largeur
              </button>
              <button
                type="button"
                class="reader-view__setting-option"
                :class="{ 'reader-view__setting-option--active': settings.fit === 'height' }"
                @click="settings.fit = 'height'; saveSettings()"
              >
                ↕️ Hauteur
              </button>
              <button
                type="button"
                class="reader-view__setting-option"
                :class="{ 'reader-view__setting-option--active': settings.fit === 'original' }"
                @click="settings.fit = 'original'; saveSettings()"
              >
                🔍 Original
              </button>
            </div>
          </div>

          <!-- Fond -->
          <div class="reader-view__setting">
            <label class="reader-view__setting-label">Couleur de fond</label>
            <div class="reader-view__setting-options">
              <button
                type="button"
                class="reader-view__setting-option reader-view__setting-option--color"
                :class="{ 'reader-view__setting-option--active': settings.background === 'dark' }"
                @click="settings.background = 'dark'; saveSettings()"
                title="Sombre"
              >
                <span class="reader-view__color-swatch" style="background: #0a0e1a" />
              </button>
              <button
                type="button"
                class="reader-view__setting-option reader-view__setting-option--color"
                :class="{ 'reader-view__setting-option--active': settings.background === 'black' }"
                @click="settings.background = 'black'; saveSettings()"
                title="Noir"
              >
                <span class="reader-view__color-swatch" style="background: #000000" />
              </button>
              <button
                type="button"
                class="reader-view__setting-option reader-view__setting-option--color"
                :class="{ 'reader-view__setting-option--active': settings.background === 'sepia' }"
                @click="settings.background = 'sepia'; saveSettings()"
                title="Sépia"
              >
                <span class="reader-view__color-swatch" style="background: #f4ecd8" />
              </button>
              <button
                type="button"
                class="reader-view__setting-option reader-view__setting-option--color"
                :class="{ 'reader-view__setting-option--active': settings.background === 'light' }"
                @click="settings.background = 'light'; saveSettings()"
                title="Clair"
              >
                <span class="reader-view__color-swatch" style="background: #f4f6fa" />
              </button>
            </div>
          </div>

          <!-- Zoom -->
          <div class="reader-view__setting">
            <label class="reader-view__setting-label">
              Zoom : {{ Math.round(zoomLevel * 100) }}%
            </label>
            <input
              type="range"
              class="reader-view__setting-range"
              v-model.number="zoomLevel"
              min="0.5"
              max="3"
              step="0.1"
              @input="saveSettings"
            />
            <button
              type="button"
              class="reader-view__setting-reset"
              @click="resetZoom"
            >
              Réinitialiser (100%)
            </button>
          </div>

          <!-- Préchargement -->
          <div class="reader-view__setting">
            <label class="reader-view__setting-checkbox">
              <input
                type="checkbox"
                v-model="settings.preload"
                @change="saveSettings"
              />
              <span>Précharger les pages suivantes</span>
            </label>
          </div>

          <!-- Auto-scroll -->
          <div class="reader-view__setting">
            <label class="reader-view__setting-checkbox">
              <input
                type="checkbox"
                v-model="settings.autoHideUI"
                @change="saveSettings"
              />
              <span>Masquer l'interface automatiquement</span>
            </label>
          </div>
        </div>
      </aside>
    </Transition>

    <!-- ====================================================================
      INDICATEUR DE PRÉCHARGEMENT
    ==================================================================== -->
    <Transition name="reader-view-fade">
      <div v-if="preloadingCount > 0" class="reader-view__preload-indicator">
        <NexusSpinner size="xs" />
        <span>Préchargement {{ preloadingCount }} page(s)...</span>
      </div>
    </Transition>

    <!-- ====================================================================
      MODALE DE FIN DE CHAPITRE
    ==================================================================== -->
    <NexusModal
      v-model="showEndModal"
      title="🎉 Fin du chapitre"
      size="sm"
      :show-footer="true"
    >
      <p>Vous avez terminé ce chapitre.</p>
      <p v-if="hasNextChapter" class="reader-view__end-modal-hint">
        Passer au chapitre suivant ?
      </p>
      <p v-else class="reader-view__end-modal-hint">
        C'est le dernier chapitre disponible.
      </p>

      <template #footer>
        <NexusButton variant="neutral" @click="showEndModal = false">
          Rester ici
        </NexusButton>
        <NexusButton
          v-if="hasNextChapter"
          variant="primary"
          @click="goToNextChapter(); showEndModal = false"
        >
          Chapitre suivant →
        </NexusButton>
        <NexusButton
          v-else
          variant="primary"
          @click="closeReader"
        >
          Fermer
        </NexusButton>
      </template>
    </NexusModal>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useLibraryStore } from '@/stores/library'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusButton from '@/components/common/NexusButton.vue'
import NexusModal from '@/components/common/NexusModal.vue'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const router = useRouter()
const route = useRoute()
const api = useApi()
const toast = useToast()
const libraryStore = useLibraryStore()

// ==========================================================================
//  Constantes
// ==========================================================================

const STORAGE_KEY = 'nexus-reader-settings'
const DEFAULT_SETTINGS = {
  mode: 'single',       // 'single' | 'double'
  direction: 'ltr',     // 'ltr' | 'rtl'
  fit: 'height',        // 'width' | 'height' | 'original'
  background: 'dark',   // 'dark' | 'black' | 'sepia' | 'light'
  preload: true,
  autoHideUI: false,
}

// ==========================================================================
//  État réactif
// ==========================================================================

const pages = ref([])
const currentPage = ref(0)
const loading = ref(true)
const error = ref(null)
const loadProgress = ref(0)
const zoomLevel = ref(1)
const isFullscreen = ref(false)
const uiHidden = ref(false)
const showThumbnails = ref(false)
const showSettings = ref(false)
const showEndModal = ref(false)
const preloadingCount = ref(0)
const currentImageRef = ref(null)
const viewportRef = ref(null)

// Chapitre / navigation
const chapterData = ref(null)
const allChapters = ref([])
const currentChapterIndex = ref(0)

// Pan (déplacement quand zoomé)
const panX = ref(0)
const panY = ref(0)
let isDragging = false
let dragStartX = 0
let dragStartY = 0

// Touch (swipe)
let touchStartX = 0
let touchStartY = 0
let touchStartTime = 0

// Auto-hide UI
let uiHideTimer = null

// Settings
const settings = reactive({ ...DEFAULT_SETTINGS })

// ==========================================================================
//  Computed
// ==========================================================================

const jobId = computed(() => route.params.jobId)

const chapterId = computed(() => route.params.chapterId || null)

const chapterTitle = computed(() => {
  if (chapterData.value?.title) return chapterData.value.title
  if (chapterId.value) return `Chapitre ${chapterId.value}`
  return 'Lecteur CBZ'
})

const hasPreviousChapter = computed(() => currentChapterIndex.value > 0)

const hasNextChapter = computed(() => {
  return currentChapterIndex.value < allChapters.value.length - 1
})

const chapterProgress = computed(() => {
  if (pages.value.length <= 1) return 100
  return Math.round((currentPage.value / (pages.value.length - 1)) * 100)
})

const fitIcon = computed(() => {
  const map = { width: '↔️', height: '↕️', original: '🔍' }
  return map[settings.fit] || '↕️'
})

const doublePageIndices = computed(() => {
  // Mode double : affiche la page courante et la suivante
  const start = currentPage.value
  const end = Math.min(start + 1, pages.value.length - 1)
  const indices = []
  for (let i = start; i <= end; i++) {
    indices.push(i)
  }
  return settings.direction === 'rtl' ? indices.reverse() : indices
})

const pageStyle = computed(() => {
  if (zoomLevel.value <= 1) return {}
  return {
    transform: `translate(${panX.value}px, ${panY.value}px) scale(${zoomLevel.value})`,
    cursor: isDragging ? 'grabbing' : 'grab',
  }
})

const imageStyle = computed(() => {
  if (zoomLevel.value !== 1) return {}
  return {}
})

// ==========================================================================
//  Méthodes — Chargement
// ==========================================================================

/**
 * Charge le chapitre (job) et ses pages.
 */
async function loadChapter() {
  loading.value = true
  error.value = null
  loadProgress.value = 0

  try {
    // Charger les détails du job depuis l'API
    const response = await api.get(`/downloads/jobs/${jobId.value}`)
    const job = response.data || response

    if (!job) {
      throw new Error('Job introuvable')
    }

    chapterData.value = job

    // Déterminer le chapitre à afficher
    let targetChapter = null
    if (chapterId.value) {
      targetChapter = chapterId.value
    } else {
      targetChapter = job.result_path || job.id
    }

    // Charger les images du chapitre
    await loadPages(targetChapter)

    // Déterminer la position dans la liste des chapitres
    allChapters.value = job.data?.chapters || []
    currentChapterIndex.value = allChapters.value.findIndex(
      (c) => c.id === targetChapter || c.title === chapterTitle.value
    )
    if (currentChapterIndex.value === -1) currentChapterIndex.value = 0

    // Charger la page de progression
    loadProgressFromStorage()

    // Marquer le chapitre comme lu
    markAsRead()
  } catch (err) {
    console.error('Erreur chargement lecteur:', err)
    error.value = err.message || 'Impossible de charger le chapitre.'
  } finally {
    loading.value = false
  }
}

/**
 * Charge les images du chapitre.
 * @param {string} chapterId
 */
async function loadPages(chapterId) {
  try {
    // Essayer de charger depuis l'API du reader
    const response = await api.get(
      `/downloads/jobs/${jobId.value}/chapter/${encodeURIComponent(chapterId)}/pages`
    )

    let rawPages = []
    if (Array.isArray(response)) {
      rawPages = response
    } else if (Array.isArray(response.pages)) {
      rawPages = response.pages
    } else if (Array.isArray(response.data)) {
      rawPages = response.data
    }

    // Normaliser les pages
    pages.value = rawPages.map((p, idx) => ({
      url: typeof p === 'string' ? p : p.url || p.path,
      thumbnail: typeof p === 'object' ? p.thumbnail : null,
      index: idx,
    }))

    if (pages.value.length === 0) {
      throw new Error('Aucune page trouvée pour ce chapitre.')
    }

    // Précharger les premières pages
    if (settings.preload) {
      preloadPages(0, Math.min(5, pages.value.length))
    }
  } catch (err) {
    console.error('Erreur chargement pages:', err)
    // Fallback : essayer avec un autre endpoint
    try {
      const job = chapterData.value
      if (job?.result_path) {
        // Utiliser les URLs directes du CBZ
        const fallbackUrl = `/library/${encodeURIComponent(job.id)}/pages`
        const fallbackResponse = await api.get(fallbackUrl)
        const fallbackPages = fallbackResponse.pages || fallbackResponse.data || []
        pages.value = fallbackPages.map((p, idx) => ({
          url: typeof p === 'string' ? p : p.url,
          index: idx,
        }))
        if (pages.value.length === 0) throw new Error('Aucune page disponible')
      } else {
        throw err
      }
    } catch (fallbackErr) {
      throw new Error('Impossible de charger les pages du chapitre.')
    }
  }
}

/**
 * Précharge des pages en arrière-plan.
 * @param {number} start
 * @param {number} end
 */
function preloadPages(start, end) {
  const toLoad = Math.min(end, pages.value.length)
  for (let i = start; i < toLoad; i++) {
    if (!pages.value[i]?.loaded) {
      preloadingCount.value++
      const img = new Image()
      img.onload = () => {
        pages.value[i].loaded = true
        preloadingCount.value = Math.max(0, preloadingCount.value - 1)
      }
      img.onerror = () => {
        pages.value[i].error = true
        preloadingCount.value = Math.max(0, preloadingCount.value - 1)
      }
      img.src = pages.value[i].url
    }
  }
}

// ==========================================================================
//  Méthodes — Navigation
// ==========================================================================

function goToPage(index) {
  const clamped = Math.max(0, Math.min(pages.value.length - 1, index))
  currentPage.value = clamped
  resetPan()
  scrollToTop()
  saveProgressToStorage()
  preloadAroundCurrent()
}

function goToFirstPage() {
  goToPage(0)
}

function goToLastPage() {
  goToPage(pages.value.length - 1)
}

function goToPreviousPage() {
  if (currentPage.value > 0) {
    if (settings.mode === 'double' && currentPage.value >= 2) {
      goToPage(currentPage.value - 2)
    } else {
      goToPage(currentPage.value - 1)
    }
  } else {
    // Fin du chapitre précédent
    if (hasPreviousChapter.value) {
      goToPreviousChapter()
    } else {
      toast.info('Début du premier chapitre', 'ℹ️', 1500)
    }
  }
}

function goToNextPage() {
  if (currentPage.value < pages.value.length - 1) {
    if (settings.mode === 'double') {
      const step = currentPage.value === 0 ? 2 : 2
      if (currentPage.value + step <= pages.value.length - 1) {
        goToPage(currentPage.value + step)
      } else {
        goToPage(pages.value.length - 1)
      }
    } else {
      goToPage(currentPage.value + 1)
    }
  } else {
    // Fin du chapitre
    if (hasNextChapter.value) {
      showEndModal.value = true
    } else {
      showEndModal.value = true
    }
  }
}

function preloadAroundCurrent() {
  if (!settings.preload) return
  const start = Math.max(0, currentPage.value - 1)
  const end = Math.min(pages.value.length, currentPage.value + 4)
  preloadPages(start, end)
}

function goToPreviousChapter() {
  if (!hasPreviousChapter.value) return
  const prevChapter = allChapters.value[currentChapterIndex.value - 1]
  router.push({
    name: 'reader',
    params: {
      jobId: jobId.value,
      chapterId: prevChapter.id || prevChapter.title,
    },
  })
}

function goToNextChapter() {
  if (!hasNextChapter.value) return
  const nextChapter = allChapters.value[currentChapterIndex.value + 1]
  router.push({
    name: 'reader',
    params: {
      jobId: jobId.value,
      chapterId: nextChapter.id || nextChapter.title,
    },
  })
}

function closeReader() {
  const job = chapterData.value
  if (job?.library_id) {
    router.push({ name: 'library-detail', params: { id: job.library_id } })
  } else {
    router.push('/library')
  }
}

function onSliderInput(event) {
  const value = parseInt(event.target.value, 10)
  goToPage(value)
}

function scrollToTop() {
  const el = viewportRef.value
  if (el) {
    el.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  }
}

// ==========================================================================
//  Méthodes — Zoom / Pan
// ==========================================================================

function resetZoom() {
  zoomLevel.value = 1
  resetPan()
  saveSettings()
}

function resetPan() {
  panX.value = 0
  panY.value = 0
}

function handleWheel(event) {
  if (event.ctrlKey || event.metaKey) {
    // Zoom avec Ctrl + molette
    event.preventDefault()
    if (event.deltaY < 0) {
      zoomLevel.value = Math.min(3, zoomLevel.value + 0.1)
    } else {
      zoomLevel.value = Math.max(0.5, zoomLevel.value - 0.1)
    }
  } else if (zoomLevel.value > 1) {
    // Pan avec la molette quand zoomé
    event.preventDefault()
    panY.value -= event.deltaY
    panX.value -= event.deltaX
  }
}

function handleMouseDown(event) {
  if (zoomLevel.value <= 1) return
  isDragging = true
  dragStartX = event.clientX - panX.value
  dragStartY = event.clientY - panY.value
}

function handleMouseMove(event) {
  // Réafficher l'UI au mouvement
  if (settings.autoHideUI) {
    showUI()
  }

  if (isDragging && zoomLevel.value > 1) {
    panX.value = event.clientX - dragStartX
    panY.value = event.clientY - dragStartY
  }
}

function handleMouseUp() {
  isDragging = false
}

function handleContainerClick(event) {
  // Si on clique sur le fond (pas sur les boutons), naviguer
  if (event.target.classList.contains('reader-view__viewport')) {
    const rect = event.target.getBoundingClientRect()
    const x = event.clientX - rect.left
    const half = rect.width / 2

    if (settings.direction === 'rtl') {
      if (x < half) goToNextPage()
      else goToPreviousPage()
    } else {
      if (x < half) goToPreviousPage()
      else goToNextPage()
    }
  }
}

// ==========================================================================
//  Méthodes — Touch
// ==========================================================================

function handleTouchStart(event) {
  if (event.touches.length === 1) {
    touchStartX = event.touches[0].clientX
    touchStartY = event.touches[0].clientY
    touchStartTime = Date.now()
  }
}

function handleTouchMove(event) {
  if (event.touches.length === 1 && zoomLevel.value > 1) {
    // Pan tactile
    const touch = event.touches[0]
    panX.value = touch.clientX - touchStartX
    panY.value = touch.clientY - touchStartY
  }
}

function handleTouchEnd(event) {
  const touch = event.changedTouches[0]
  const deltaX = touch.clientX - touchStartX
  const deltaY = touch.clientY - touchStartY
  const duration = Date.now() - touchStartTime

  // Swipe rapide (< 300ms, > 50px)
  if (duration < 300 && Math.abs(deltaX) > 50 && Math.abs(deltaY) < 100) {
    if (settings.direction === 'rtl') {
      if (deltaX > 0) goToNextPage()
      else goToPreviousPage()
    } else {
      if (deltaX > 0) goToPreviousPage()
      else goToNextPage()
    }
  }
}

// ==========================================================================
//  Méthodes — Paramètres
// ==========================================================================

function toggleMode() {
  settings.mode = settings.mode === 'single' ? 'double' : 'single'
  saveSettings()
}

function toggleDirection() {
  settings.direction = settings.direction === 'ltr' ? 'rtl' : 'ltr'
  saveSettings()
}

function cycleFitMode() {
  const modes = ['width', 'height', 'original']
  const idx = modes.indexOf(settings.fit)
  settings.fit = modes[(idx + 1) % modes.length]
  saveSettings()
}

function cycleBackground() {
  const backgrounds = ['dark', 'black', 'sepia', 'light']
  const idx = backgrounds.indexOf(settings.background)
  settings.background = backgrounds[(idx + 1) % backgrounds.length]
  saveSettings()
}

function saveSettings() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch (_) {
    // Ignorer
  }
}

function loadSettings() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      Object.assign(settings, JSON.parse(stored))
    }
  } catch (_) {
    // Ignorer
  }
}

// ==========================================================================
//  Méthodes — UI
// ==========================================================================

function toggleThumbnails() {
  showThumbnails.value = !showThumbnails.value
  if (showThumbnails.value) showSettings.value = false
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.().then(() => {
      isFullscreen.value = true
    }).catch(() => {
      toast.error('Plein écran non supporté', '❌')
    })
  } else {
    document.exitFullscreen?.().then(() => {
      isFullscreen.value = false
    })
  }
}

function showUI() {
  uiHidden.value = false
  scheduleHideUI()
}

function scheduleHideUI() {
  if (!settings.autoHideUI) return
  clearTimeout(uiHideTimer)
  uiHideTimer = setTimeout(() => {
    if (!showSettings.value && !showThumbnails.value && !showEndModal.value) {
      uiHidden.value = true
    }
  }, 3000)
}

function onImageLoad() {
  // Image chargée
}

function onImageError(event) {
  console.warn('Erreur chargement image:', event.target?.src)
}

// ==========================================================================
//  Méthodes — Persistance
// ==========================================================================

function saveProgressToStorage() {
  try {
    const key = `nexus-reader-progress-${jobId.value}`
    localStorage.setItem(key, String(currentPage.value))
  } catch (_) {}
}

function loadProgressFromStorage() {
  try {
    const key = `nexus-reader-progress-${jobId.value}`
    const stored = localStorage.getItem(key)
    if (stored) {
      const page = parseInt(stored, 10)
      if (page > 0 && page < pages.value.length) {
        currentPage.value = page
      }
    }
  } catch (_) {}
}

async function markAsRead() {
  try {
    if (chapterData.value?.library_id) {
      await api.post(`/library/${chapterData.value.library_id}/read`).catch(() => null)
    }
  } catch (_) {}
}

// ==========================================================================
//  Gestion des raccourcis clavier
// ==========================================================================

function handleKeydown(event) {
  // Ne pas interférer avec les inputs
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return

  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      if (settings.direction === 'rtl') goToNextPage()
      else goToPreviousPage()
      break
    case 'ArrowRight':
      event.preventDefault()
      if (settings.direction === 'rtl') goToPreviousPage()
      else goToNextPage()
      break
    case 'ArrowUp':
      event.preventDefault()
      goToPreviousPage()
      break
    case 'ArrowDown':
    case ' ':
      event.preventDefault()
      goToNextPage()
      break
    case 'Home':
      event.preventDefault()
      goToFirstPage()
      break
    case 'End':
      event.preventDefault()
      goToLastPage()
      break
    case 'Escape':
      event.preventDefault()
      if (showThumbnails.value) showThumbnails.value = false
      else if (showSettings.value) showSettings.value = false
      else if (isFullscreen.value) toggleFullscreen()
      else closeReader()
      break
    case 'f':
    case 'F':
      event.preventDefault()
      cycleFitMode()
      break
    case 'd':
    case 'D':
      event.preventDefault()
      toggleMode()
      break
    case 'r':
    case 'R':
      event.preventDefault()
      toggleDirection()
      break
    case 'b':
    case 'B':
      event.preventDefault()
      cycleBackground()
      break
    case 't':
    case 'T':
      event.preventDefault()
      toggleThumbnails()
      break
    case 'F11':
      event.preventDefault()
      toggleFullscreen()
      break
    case '+':
    case '=':
      event.preventDefault()
      zoomLevel.value = Math.min(3, zoomLevel.value + 0.1)
      break
    case '-':
      event.preventDefault()
      zoomLevel.value = Math.max(0.5, zoomLevel.value - 0.1)
      break
    case '0':
      event.preventDefault()
      resetZoom()
      break
  }
}

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  loadSettings()
  await loadChapter()

  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('mouseup', handleMouseUp)

  if (settings.autoHideUI) {
    scheduleHideUI()
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('mouseup', handleMouseUp)
  clearTimeout(uiHideTimer)
  saveProgressToStorage()
})

// Surveiller le changement de chapitre dans l'URL
watch(
  () => [route.params.chapterId, route.params.jobId],
  () => {
    if (route.name === 'reader') {
      currentPage.value = 0
      loadChapter()
    }
  }
)

// Sauvegarder la progression à chaque changement de page
watch(currentPage, () => {
  saveProgressToStorage()
})

// Surveiller le changement de mode
watch(() => settings.mode, () => {
  // Ajuster la page courante si paire/impaire
  if (settings.mode === 'double' && currentPage.value % 2 !== 0) {
    currentPage.value = Math.max(0, currentPage.value - 1)
  }
})

// Surveiller l'atteinte de la dernière page
watch(currentPage, (newPage) => {
  if (newPage >= pages.value.length - 1 && pages.value.length > 0) {
    // Marquer comme lu
    markAsRead()
  }
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.reader-view {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #0a0e1a;
  color: #e8edf5;
  user-select: none;
  transition: background 0.3s ease;

  // Thèmes de fond
  &--theme-dark { background: #0a0e1a; }
  &--theme-black { background: #000000; }
  &--theme-sepia { background: #f4ecd8; color: #3d2f1e; }
  &--theme-light { background: #f4f6fa; color: #1a1a2e; }

  &--fullscreen {
    cursor: none;
  }

  &--hidden-ui {
    .reader-view__toolbar {
      opacity: 0;
      pointer-events: none;
      transform: translateY(-100%);
    }

    .reader-view__toolbar--bottom {
      transform: translateY(100%);
    }

    .reader-view__nav-arrow {
      opacity: 0;
    }

    &:hover {
      .reader-view__toolbar {
        opacity: 1;
        pointer-events: auto;
        transform: translateY(0);
      }

      .reader-view__nav-arrow {
        opacity: 0.8;
      }
    }
  }
}

// ==========================================================================
//  États : Loading / Error
// ==========================================================================

.reader-view__loading,
.reader-view__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  width: 100%;
  height: 100%;
  padding: 2rem;
  text-align: center;
}

.reader-view__loading-text {
  margin: 0;
  font-size: 1rem;
  color: var(--color-text-secondary, #b0c0d8);
}

.reader-view__loading-progress {
  width: 240px;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 9999px;
  overflow: hidden;
}

.reader-view__loading-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #0066ff);
  border-radius: 9999px;
  transition: width 0.3s ease;
}

.reader-view__error-icon {
  font-size: 3rem;
}

.reader-view__error-title {
  margin: 0;
  font-size: 1.3rem;
  color: #f44336;
}

.reader-view__error-message {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-muted, #6a7a9a);
  max-width: 400px;
}

.reader-view__error-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 0.5rem;
}

// ==========================================================================
//  Toolbar (top & bottom)
// ==========================================================================

.reader-view__toolbar {
  position: absolute;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  z-index: 20;
  transition: all 0.3s ease;

  &--top {
    top: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    flex-wrap: wrap;
  }

  &--bottom {
    bottom: 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    flex-direction: column;
    gap: 0.5rem;
  }

  &--hidden {
    opacity: 0;
    pointer-events: none;
  }
}

.reader-view__toolbar-left,
.reader-view__toolbar-right {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.reader-view__toolbar-left {
  flex: 1;
  min-width: 0;
}

.reader-view__toolbar-center {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-shrink: 0;
}

.reader-view__toolbar-right {
  flex-shrink: 0;
  justify-content: flex-end;
}

.reader-view__toolbar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
  padding: 0 0.5rem;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #ffffff;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.15s ease;

  &:hover:not(:disabled) {
    background: rgba(0, 212, 255, 0.2);
    border-color: #00d4ff;
    transform: translateY(-1px);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  &:focus-visible {
    outline: 2px solid #00d4ff;
    outline-offset: 2px;
  }
}

// ==========================================================================
//  Chapter info
// ==========================================================================

.reader-view__chapter-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  max-width: 400px;
}

.reader-view__chapter-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reader-view__chapter-subtitle {
  margin: 0;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
}

.reader-view__page-indicator {
  padding: 0 0.6rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #00d4ff;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

// ==========================================================================
//  Viewport
// ==========================================================================

.reader-view__viewport {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 60px 0 80px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;

  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;

    &:hover {
      background: rgba(255, 255, 255, 0.35);
    }
  }
}

// ==========================================================================
//  Page container
// ==========================================================================

.reader-view__page-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-height: fit-content;
  transition: transform 0.1s ease-out;

  &--half {
    width: 50%;
    height: 100%;
  }
}

.reader-view__page {
  display: block;
  max-width: 100%;
  height: auto;
  object-fit: contain;
  border-radius: 2px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.6);
  user-select: none;
  -webkit-user-drag: none;

  &--fit-width {
    width: 100%;
    height: auto;
    max-height: none;
  }

  &--fit-height {
    height: calc(100vh - 140px);
    width: auto;
    max-width: 100%;
  }

  &--fit-original {
    width: auto;
    height: auto;
    max-width: 100%;
    max-height: calc(100vh - 140px);
  }
}

.reader-view__page-empty {
  width: 100%;
  height: 100%;
}

// ==========================================================================
//  Double container
// ==========================================================================

.reader-view__double-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  height: 100%;
}

.reader-view--rtl .reader-view__double-container {
  flex-direction: row-reverse;
}

// ==========================================================================
//  Nav arrows
// ==========================================================================

.reader-view__nav-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 56px;
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ffffff;
  cursor: pointer;
  border-radius: 12px;
  font-size: 1.5rem;
  transition: all 0.2s ease;
  z-index: 15;
  opacity: 0.6;

  &:hover {
    opacity: 1;
    background: rgba(0, 212, 255, 0.3);
    border-color: #00d4ff;
  }

  &--left {
    left: 1rem;
  }

  &--right {
    right: 1rem;
  }

  @media (max-width: 768px) {
    display: none;
  }
}

// ==========================================================================
//  Zoom indicator
// ==========================================================================

.reader-view__zoom-indicator {
  position: absolute;
  top: 80px;
  right: 1rem;
  z-index: 15;
}

.reader-view__zoom-reset {
  padding: 0.35rem 0.7rem;
  background: rgba(0, 212, 255, 0.9);
  color: #0a0e1a;
  border: none;
  border-radius: 9999px;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  transition: all 0.15s ease;

  &:hover {
    filter: brightness(1.1);
    transform: scale(1.05);
  }
}

// ==========================================================================
//  Progress bar (bottom toolbar)
// ==========================================================================

.reader-view__progress-container {
  width: 100%;
}

.reader-view__progress-slider {
  width: 100%;
  height: 6px;
  appearance: none;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 9999px;
  outline: none;
  cursor: pointer;

  &::-webkit-slider-thumb {
    appearance: none;
    width: 18px;
    height: 18px;
    background: #00d4ff;
    border: 2px solid #ffffff;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 212, 255, 0.5);
    transition: all 0.15s ease;

    &:hover {
      transform: scale(1.2);
    }
  }

  &::-moz-range-thumb {
    width: 18px;
    height: 18px;
    background: #00d4ff;
    border: 2px solid #ffffff;
    border-radius: 50%;
    cursor: pointer;
  }
}

.reader-view__bottom-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.7);
}

.reader-view__bottom-page {
  font-variant-numeric: tabular-nums;
}

.reader-view__bottom-progress {
  color: #00d4ff;
  font-weight: 500;
}

// ==========================================================================
//  Thumbnails panel
// ==========================================================================

.reader-view__thumbnails {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 280px;
  max-width: 80vw;
  background: rgba(10, 14, 26, 0.98);
  backdrop-filter: blur(12px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 30;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.reader-view__thumbnails-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.reader-view__thumbnails-title {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: #ffffff;
}

.reader-view__thumbnails-close {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-size: 1rem;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;

  &:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.1);
  }
}

.reader-view__thumbnails-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  padding: 0.75rem;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 3px;
  }
}

.reader-view__thumbnail {
  position: relative;
  display: flex;
  flex-direction: column;
  background: transparent;
  border: 2px solid transparent;
  border-radius: 6px;
  padding: 0;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.15s ease;
  aspect-ratio: 2/3;

  &:hover {
    border-color: rgba(0, 212, 255, 0.5);
    transform: scale(1.03);
  }

  &--active {
    border-color: #00d4ff;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.3);
  }
}

.reader-view__thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  background: #1a2538;
}

.reader-view__thumbnail-number {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0.15rem;
  background: rgba(0, 0, 0, 0.75);
  color: #ffffff;
  font-size: 0.65rem;
  text-align: center;
  font-weight: 600;
}

// ==========================================================================
//  Settings panel
// ==========================================================================

.reader-view__settings {
  position: absolute;
  top: 0;
  bottom: 0;
  right: 0;
  width: 320px;
  max-width: 85vw;
  background: rgba(10, 14, 26, 0.98);
  backdrop-filter: blur(12px);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 30;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.reader-view__settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.reader-view__settings-title {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: #ffffff;
}

.reader-view__settings-close {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-size: 1rem;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;

  &:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.1);
  }
}

.reader-view__settings-body {
  flex: 1;
  padding: 0.75rem 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 3px;
  }
}

.reader-view__setting {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.reader-view__setting-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.reader-view__setting-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.reader-view__setting-option {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.7rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.75);
  cursor: pointer;
  font-size: 0.72rem;
  font-weight: 500;
  transition: all 0.15s ease;
  flex: 1;
  justify-content: center;
  min-width: 0;

  &:hover {
    background: rgba(0, 212, 255, 0.15);
    color: #ffffff;
  }

  &--active {
    background: #00d4ff;
    border-color: #00d4ff;
    color: #0a0e1a;
    font-weight: 600;
  }

  &--color {
    flex: 0 0 auto;
    padding: 0.3rem;
    width: 40px;
    height: 40px;
  }
}

.reader-view__color-swatch {
  display: block;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.reader-view__setting-range {
  width: 100%;
  height: 5px;
  appearance: none;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 9999px;
  outline: none;
  cursor: pointer;

  &::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    background: #00d4ff;
    border: 2px solid #ffffff;
    border-radius: 50%;
    cursor: pointer;
  }

  &::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background: #00d4ff;
    border: 2px solid #ffffff;
    border-radius: 50%;
    cursor: pointer;
  }
}

.reader-view__setting-reset {
  padding: 0.3rem 0.6rem;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  font-size: 0.7rem;
  transition: all 0.15s ease;
  align-self: flex-start;

  &:hover {
    border-color: #00d4ff;
    color: #00d4ff;
  }
}

.reader-view__setting-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.85);
  user-select: none;

  input[type='checkbox'] {
    width: 16px;
    height: 16px;
    cursor: pointer;
    accent-color: #00d4ff;
  }
}

// ==========================================================================
//  Preload indicator
// ==========================================================================

.reader-view__preload-indicator {
  position: absolute;
  bottom: 90px;
  left: 1rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.75rem;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 9999px;
  font-size: 0.72rem;
  color: #ffffff;
  z-index: 15;
}

// ==========================================================================
//  End modal
// ==========================================================================

.reader-view__end-modal-hint {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #00d4ff;
}

// ==========================================================================
//  Transitions
// ==========================================================================

.reader-view-slide-left-enter-active,
.reader-view-slide-left-leave-active {
  transition: transform 0.25s ease;
}

.reader-view-slide-left-enter-from,
.reader-view-slide-left-leave-to {
  transform: translateX(-100%);
}

.reader-view-slide-right-enter-active,
.reader-view-slide-right-leave-active {
  transition: transform 0.25s ease;
}

.reader-view-slide-right-enter-from,
.reader-view-slide-right-leave-to {
  transform: translateX(100%);
}

.reader-view-fade-enter-active,
.reader-view-fade-leave-active {
  transition: opacity 0.2s ease;
}

.reader-view-fade-enter-from,
.reader-view-fade-leave-to {
  opacity: 0;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 768px) {
  .reader-view__toolbar {
    padding: 0.4rem 0.5rem;
  }

  .reader-view__toolbar-center {
    order: 3;
    width: 100%;
    justify-content: center;
    padding-top: 0.4rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    margin-top: 0.4rem;
  }

  .reader-view__toolbar-btn {
    min-width: 32px;
    height: 32px;
    font-size: 0.75rem;
  }

  .reader-view__chapter-info {
    max-width: 160px;
  }

  .reader-view__chapter-title {
    font-size: 0.8rem;
  }

  .reader-view__page--fit-height {
    height: calc(100vh - 180px);
  }

  .reader-view__page--fit-original {
    max-height: calc(100vh - 180px);
  }

  .reader-view__viewport {
    padding: 100px 0 120px;
  }

  .reader-view__thumbnails {
    width: 240px;
  }

  .reader-view__thumbnails-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .reader-view__settings {
    width: 280px;
  }
}

@media (max-width: 480px) {
  .reader-view__toolbar-right {
    gap: 0.2rem;
  }

  .reader-view__toolbar-btn {
    min-width: 28px;
    height: 28px;
    padding: 0 0.3rem;
    font-size: 0.7rem;
  }

  .reader-view__chapter-subtitle {
    display: none;
  }

  .reader-view__page-indicator {
    font-size: 0.7rem;
    padding: 0 0.4rem;
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .reader-view__toolbar,
  .reader-view__nav-arrow,
  .reader-view__thumbnail,
  .reader-view__page-container {
    transition: none !important;
  }
}
</style>
