<!-- ==========================================================================
  NexusDL 2.0 - Library Detail View (version complète)
  Fichier : frontend/src/views/LibraryDetailView.vue
  Description : Vue de détail d'un élément de la bibliothèque (fichier CBZ).
                Affiche la couverture, les métadonnées, les statistiques,
                permet l'édition, la lecture, le téléchargement et la
                suppression. Inclut la gestion des tags et la notation.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="library-detail">
    <!-- ====================================================================
      ÉTAT DE CHARGEMENT
    ==================================================================== -->
    <div v-if="loading && !item" class="library-detail__loading">
      <NexusSpinner size="xl" variant="gradient" label="Chargement des détails..." />
    </div>

    <!-- ====================================================================
      ÉTAT D'ERREUR
    ==================================================================== -->
    <div v-else-if="error" class="library-detail__error">
      <div class="library-detail__error-content">
        <span class="library-detail__error-icon" aria-hidden="true">❌</span>
        <h2 class="library-detail__error-title">Impossible de charger l'élément</h2>
        <p class="library-detail__error-message">{{ error }}</p>
        <div class="library-detail__error-actions">
          <NexusButton variant="primary" @click="fetchItem">
            🔄 Réessayer
          </NexusButton>
          <NexusButton variant="neutral" @click="goBack">
            ← Retour
          </NexusButton>
        </div>
      </div>
    </div>

    <!-- ====================================================================
      CONTENU PRINCIPAL
    ==================================================================== -->
    <template v-else-if="item">
      <!-- ================================================================
        BREADCRUMB / NAVIGATION
      ================================================================ -->
      <nav class="library-detail__breadcrumb" aria-label="Fil d'Ariane">
        <button
          type="button"
          class="library-detail__breadcrumb-back"
          @click="goBack"
          aria-label="Retour à la bibliothèque"
        >
          <span aria-hidden="true">←</span>
          Bibliothèque
        </button>
        <span class="library-detail__breadcrumb-sep" aria-hidden="true">/</span>
        <span class="library-detail__breadcrumb-current" :title="item.title">
          {{ truncate(item.title, 50) }}
        </span>
      </nav>

      <!-- ================================================================
        LAYOUT PRINCIPAL
      ================================================================ -->
      <div class="library-detail__layout">
        <!-- ============================================================
          COLONNE GAUCHE — Couverture & Actions
        ============================================================ -->
        <aside class="library-detail__sidebar">
          <!-- Couverture -->
          <div class="library-detail__cover-wrapper">
            <img
              v-if="coverUrl && !coverError"
              :src="coverUrl"
              :alt="`Couverture de ${item.title}`"
              class="library-detail__cover"
              loading="lazy"
              @error="onCoverError"
            />
            <div v-else class="library-detail__cover-placeholder">
              <span aria-hidden="true">📖</span>
              <span class="library-detail__cover-placeholder-text">Aucune couverture</span>
            </div>

            <!-- Badges superposés -->
            <div class="library-detail__cover-badges">
              <span v-if="item.is_favorite" class="library-detail__cover-badge library-detail__cover-badge--favorite">
                ❤️ Favori
              </span>
              <span v-if="item.rating > 0" class="library-detail__cover-badge library-detail__cover-badge--rating">
                ⭐ {{ item.rating }}/10
              </span>
            </div>
          </div>

          <!-- Actions principales -->
          <div class="library-detail__actions">
            <NexusButton
              variant="primary"
              size="lg"
              block
              @click="openReader"
              aria-label="Lire dans le lecteur"
            >
              📖 Lire
            </NexusButton>

            <NexusButton
              variant="success"
              size="md"
              block
              :loading="downloading"
              @click="downloadItem"
              aria-label="Télécharger le fichier CBZ"
            >
              ⬇️ Télécharger ({{ item.size_formatted || formatFileSize(item.size_bytes) }})
            </NexusButton>

            <NexusButton
              variant="neutral"
              size="md"
              block
              @click="showEditModal = true"
              aria-label="Modifier les métadonnées"
            >
              ✏️ Modifier
            </NexusButton>

            <NexusButton
              variant="neutral"
              size="md"
              block
              :class="{ 'library-detail__favorite-btn--active': item.is_favorite }"
              @click="toggleFavorite"
              :aria-label="item.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'"
            >
              {{ item.is_favorite ? '❤️ Retirer des favoris' : '🤍 Ajouter aux favoris' }}
            </NexusButton>

            <NexusButton
              variant="error"
              size="md"
              block
              @click="confirmDelete"
              aria-label="Supprimer de la bibliothèque"
            >
              🗑️ Supprimer
            </NexusButton>
          </div>

          <!-- Notation -->
          <div class="library-detail__rating-section">
            <label class="library-detail__rating-label">
              Note : <strong>{{ item.rating }}/10</strong>
            </label>
            <div class="library-detail__rating-stars">
              <button
                v-for="n in 10"
                :key="n"
                type="button"
                class="library-detail__rating-star"
                :class="{ 'library-detail__rating-star--active': n <= item.rating }"
                @click="setRating(n)"
                :aria-label="`Noter ${n} sur 10`"
                :title="`${n}/10`"
              >
                ★
              </button>
            </div>
          </div>

          <!-- Statistiques -->
          <div class="library-detail__stats-mini">
            <div class="library-detail__stat-mini">
              <span class="library-detail__stat-mini-icon" aria-hidden="true">👁️</span>
              <span class="library-detail__stat-mini-value">{{ item.read_count || 0 }}</span>
              <span class="library-detail__stat-mini-label">lecture(s)</span>
            </div>
            <div v-if="item.last_read" class="library-detail__stat-mini">
              <span class="library-detail__stat-mini-icon" aria-hidden="true">🕐</span>
              <span class="library-detail__stat-mini-value">{{ formatRelativeTime(item.last_read) }}</span>
            </div>
          </div>
        </aside>

        <!-- ============================================================
          COLONNE DROITE — Métadonnées & Contenu
        ============================================================ -->
        <main class="library-detail__main">
          <!-- Titre -->
          <header class="library-detail__header">
            <h1 class="library-detail__title">{{ item.title }}</h1>
            <p v-if="item.metadata?.series" class="library-detail__series">
              📚 {{ item.metadata.series }}
            </p>
          </header>

          <!-- Métadonnées principales -->
          <section class="library-detail__section">
            <h2 class="library-detail__section-title">
              <span aria-hidden="true">📋</span>
              Informations
            </h2>
            <dl class="library-detail__meta-grid">
              <div v-if="item.metadata?.author" class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Auteur</dt>
                <dd class="library-detail__meta-value">{{ item.metadata.author }}</dd>
              </div>
              <div v-if="item.metadata?.artist" class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Artiste</dt>
                <dd class="library-detail__meta-value">{{ item.metadata.artist }}</dd>
              </div>
              <div v-if="item.metadata?.publisher" class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Éditeur</dt>
                <dd class="library-detail__meta-value">{{ item.metadata.publisher }}</dd>
              </div>
              <div v-if="item.metadata?.year" class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Année</dt>
                <dd class="library-detail__meta-value">{{ item.metadata.year }}</dd>
              </div>
              <div v-if="item.metadata?.volume" class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Volume</dt>
                <dd class="library-detail__meta-value">{{ item.metadata.volume }}</dd>
              </div>
              <div v-if="item.metadata?.language" class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Langue</dt>
                <dd class="library-detail__meta-value">
                  {{ getLanguageLabel(item.metadata.language) }}
                </dd>
              </div>
              <div v-if="item.metadata?.pages" class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Pages</dt>
                <dd class="library-detail__meta-value">{{ item.metadata.pages }}</dd>
              </div>
              <div v-if="item.metadata?.chapters" class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Chapitres</dt>
                <dd class="library-detail__meta-value">{{ item.metadata.chapters }}</dd>
              </div>
              <div class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Taille</dt>
                <dd class="library-detail__meta-value">
                  {{ item.size_formatted || formatFileSize(item.size_bytes) }}
                </dd>
              </div>
              <div class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Ajouté le</dt>
                <dd class="library-detail__meta-value">{{ formatDateTime(item.created_at) }}</dd>
              </div>
              <div class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Fichier</dt>
                <dd class="library-detail__meta-value library-detail__meta-value--mono">
                  {{ item.filename }}
                </dd>
              </div>
            </dl>
          </section>

          <!-- Genres -->
          <section v-if="genres.length > 0" class="library-detail__section">
            <h2 class="library-detail__section-title">
              <span aria-hidden="true">🏷️</span>
              Genres
            </h2>
            <div class="library-detail__genres">
              <span
                v-for="genre in genres"
                :key="genre"
                class="library-detail__genre"
              >
                {{ genre }}
              </span>
            </div>
          </section>

          <!-- Tags -->
          <section class="library-detail__section">
            <h2 class="library-detail__section-title">
              <span aria-hidden="true">🔖</span>
              Tags
              <span v-if="item.tags?.length" class="library-detail__section-count">
                ({{ item.tags.length }})
              </span>
            </h2>

            <div class="library-detail__tags">
              <span
                v-for="tag in item.tags || []"
                :key="tag"
                class="library-detail__tag"
              >
                {{ tag }}
                <button
                  type="button"
                  class="library-detail__tag-remove"
                  @click="removeTag(tag)"
                  :aria-label="`Supprimer le tag ${tag}`"
                  title="Supprimer"
                >
                  ×
                </button>
              </span>

              <div class="library-detail__tag-add">
                <input
                  v-model="newTag"
                  type="text"
                  class="library-detail__tag-input"
                  placeholder="Ajouter un tag..."
                  @keydown.enter.prevent="addTag"
                  maxlength="30"
                  aria-label="Nouveau tag"
                />
                <button
                  type="button"
                  class="library-detail__tag-add-btn"
                  :disabled="!newTag.trim()"
                  @click="addTag"
                  aria-label="Ajouter le tag"
                >
                  ➕
                </button>
              </div>
            </div>
          </section>

          <!-- Description -->
          <section v-if="item.metadata?.description" class="library-detail__section">
            <h2 class="library-detail__section-title">
              <span aria-hidden="true">📝</span>
              Description
            </h2>
            <p class="library-detail__description">
              {{ item.metadata.description }}
            </p>
          </section>

          <!-- Aperçu / Informations techniques -->
          <section class="library-detail__section">
            <h2 class="library-detail__section-title">
              <span aria-hidden="true">🔧</span>
              Informations techniques
            </h2>
            <dl class="library-detail__meta-grid library-detail__meta-grid--tech">
              <div class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Chemin</dt>
                <dd class="library-detail__meta-value library-detail__meta-value--mono">
                  {{ item.file_path }}
                </dd>
              </div>
              <div class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Modifié le</dt>
                <dd class="library-detail__meta-value">{{ formatDateTime(item.updated_at) }}</dd>
              </div>
              <div v-if="item.cover_path" class="library-detail__meta-item">
                <dt class="library-detail__meta-label">Couverture</dt>
                <dd class="library-detail__meta-value library-detail__meta-value--mono">
                  {{ item.cover_path }}
                </dd>
              </div>
            </dl>
          </section>
        </main>
      </div>
    </template>

    <!-- ====================================================================
      MODALE D'ÉDITION DES MÉTADONNÉES
    ==================================================================== -->
    <NexusModal
      v-model="showEditModal"
      title="✏️ Modifier les métadonnées"
      size="lg"
      :loading="saving"
      :show-footer="true"
    >
      <div class="library-detail__edit-form">
        <div class="library-detail__form-group">
          <label class="library-detail__form-label">Titre</label>
          <input
            v-model="editForm.title"
            type="text"
            class="library-detail__form-input"
            placeholder="Titre de l'œuvre"
            maxlength="200"
          />
        </div>

        <div class="library-detail__form-row">
          <div class="library-detail__form-group">
            <label class="library-detail__form-label">Auteur</label>
            <input
              v-model="editForm.author"
              type="text"
              class="library-detail__form-input"
              placeholder="Nom de l'auteur"
            />
          </div>
          <div class="library-detail__form-group">
            <label class="library-detail__form-label">Artiste</label>
            <input
              v-model="editForm.artist"
              type="text"
              class="library-detail__form-input"
              placeholder="Nom de l'artiste"
            />
          </div>
        </div>

        <div class="library-detail__form-row">
          <div class="library-detail__form-group">
            <label class="library-detail__form-label">Série</label>
            <input
              v-model="editForm.series"
              type="text"
              class="library-detail__form-input"
              placeholder="Nom de la série"
            />
          </div>
          <div class="library-detail__form-group">
            <label class="library-detail__form-label">Volume</label>
            <input
              v-model="editForm.volume"
              type="text"
              class="library-detail__form-input"
              placeholder="Volume"
            />
          </div>
        </div>

        <div class="library-detail__form-row">
          <div class="library-detail__form-group">
            <label class="library-detail__form-label">Éditeur</label>
            <input
              v-model="editForm.publisher"
              type="text"
              class="library-detail__form-input"
              placeholder="Éditeur"
            />
          </div>
          <div class="library-detail__form-group">
            <label class="library-detail__form-label">Année</label>
            <input
              v-model.number="editForm.year"
              type="number"
              class="library-detail__form-input"
              placeholder="2025"
              min="1900"
              max="2100"
            />
          </div>
        </div>

        <div class="library-detail__form-group">
          <label class="library-detail__form-label">Genres (séparés par des virgules)</label>
          <input
            v-model="editForm.genre"
            type="text"
            class="library-detail__form-input"
            placeholder="Action, Aventure, Fantasy..."
          />
        </div>

        <div class="library-detail__form-group">
          <label class="library-detail__form-label">Langue</label>
          <select v-model="editForm.language" class="library-detail__form-input">
            <option value="fr">🇫🇷 Français</option>
            <option value="en">🇬🇧 Anglais</option>
            <option value="es">🇪🇸 Espagnol</option>
            <option value="pt">🇵🇹 Portugais</option>
            <option value="de">🇩🇪 Allemand</option>
            <option value="it">🇮🇹 Italien</option>
            <option value="ja">🇯🇵 Japonais</option>
            <option value="ko">🇰🇷 Coréen</option>
            <option value="zh">🇨🇳 Chinois</option>
            <option value="ru">🇷🇺 Russe</option>
          </select>
        </div>

        <div class="library-detail__form-group">
          <label class="library-detail__form-label">Description</label>
          <textarea
            v-model="editForm.description"
            class="library-detail__form-textarea"
            placeholder="Description de l'œuvre..."
            rows="5"
            maxlength="2000"
          />
        </div>
      </div>

      <template #footer>
        <NexusButton variant="neutral" @click="showEditModal = false" :disabled="saving">
          Annuler
        </NexusButton>
        <NexusButton variant="primary" :loading="saving" @click="saveMetadata">
          💾 Sauvegarder
        </NexusButton>
      </template>
    </NexusModal>

    <!-- ====================================================================
      MODALE DE CONFIRMATION DE SUPPRESSION
    ==================================================================== -->
    <NexusModal
      v-model="showDeleteModal"
      title="🗑️ Supprimer l'élément"
      size="sm"
      confirmable
      confirm-text="Supprimer définitivement"
      cancel-text="Annuler"
      confirm-variant="error"
      :loading="deleting"
      @confirm="deleteItem"
      @cancel="showDeleteModal = false"
    >
      <p>
        Êtes-vous sûr de vouloir supprimer
        <strong>"{{ item?.title }}"</strong> ?
      </p>
      <p class="library-detail__delete-warning">
        ⚠️ Le fichier CBZ sera supprimé du disque. Cette action est
        <strong>irréversible</strong>.
      </p>
    </NexusModal>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useLibraryStore } from '@/stores/library'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusButton from '@/components/common/NexusButton.vue'
import NexusModal from '@/components/common/NexusModal.vue'
import { formatFileSize, formatRelativeTime, truncate, formatDateTime } from '@/utils/formatters'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const router = useRouter()
const route = useRoute()
const api = useApi()
const toast = useToast()
const libraryStore = useLibraryStore()

// ==========================================================================
//  État réactif
// ==========================================================================

const item = ref(null)
const loading = ref(false)
const error = ref(null)
const coverUrl = ref('')
const coverError = ref(false)

const newTag = ref('')
const saving = ref(false)
const deleting = ref(false)
const downloading = ref(false)

const showEditModal = ref(false)
const showDeleteModal = ref(false)

const editForm = reactive({
  title: '',
  author: '',
  artist: '',
  series: '',
  volume: '',
  publisher: '',
  year: null,
  genre: '',
  language: 'fr',
  description: '',
})

// ==========================================================================
//  Computed
// ==========================================================================

const itemId = computed(() => route.params.id)

const genres = computed(() => {
  if (!item.value?.metadata?.genre) return []
  const genre = item.value.metadata.genre
  if (Array.isArray(genre)) return genre
  return String(genre)
    .split(',')
    .map((g) => g.trim())
    .filter(Boolean)
})

// ==========================================================================
//  Méthodes — Récupération
// ==========================================================================

/**
 * Récupère les détails de l'élément.
 */
async function fetchItem() {
  if (!itemId.value) {
    error.value = 'Identifiant manquant'
    return
  }

  loading.value = true
  error.value = null
  coverError.value = false

  try {
    // Essayer d'abord de récupérer depuis le store
    let data = libraryStore.getItem(itemId.value)

    // Sinon, aller chercher depuis l'API
    if (!data) {
      const response = await api.get(`/library/${encodeURIComponent(itemId.value)}`)
      data = response.data || response
      // Enregistrer dans le store
      if (data) {
        libraryStore.items[data.id || data.filename] = data
      }
    }

    if (!data) {
      throw new Error('Élément introuvable')
    }

    item.value = normalizeItem(data)

    // Charger la couverture
    await loadCover()
  } catch (err) {
    console.error('Erreur chargement item:', err)
    error.value = err.message || 'Impossible de charger cet élément.'
  } finally {
    loading.value = false
  }
}

/**
 * Normalise un élément.
 * @param {Object} raw
 * @returns {Object}
 */
function normalizeItem(raw) {
  return {
    id: raw.id || raw.filename || '',
    filename: raw.filename || raw.id || '',
    title: raw.title || 'Sans titre',
    file_path: raw.file_path || '',
    size_bytes: raw.size_bytes || 0,
    size_formatted: raw.size_formatted || formatFileSize(raw.size_bytes || 0),
    created_at: raw.created_at || null,
    updated_at: raw.updated_at || null,
    last_read: raw.last_read || null,
    read_count: raw.read_count || 0,
    is_favorite: raw.is_favorite || false,
    rating: raw.rating || 0,
    metadata: raw.metadata || {},
    tags: Array.isArray(raw.tags) ? raw.tags : [],
    cover_path: raw.cover_path || null,
  }
}

/**
 * Charge la couverture de l'élément.
 */
async function loadCover() {
  if (!item.value) return

  try {
    // Essayer d'abord via le store
    const cachedCover = libraryStore.getCover(item.value.filename)
    if (cachedCover) {
      coverUrl.value = cachedCover
      return
    }

    // Essayer via l'API
    const url = await libraryStore.fetchCover(item.value.id, 400, 600)
    if (url) {
      coverUrl.value = url
    }
  } catch (err) {
    console.warn('Erreur chargement couverture:', err)
  }
}

function onCoverError() {
  coverError.value = true
}

// ==========================================================================
//  Méthodes — Actions
// ==========================================================================

/**
 * Bascule le statut favori.
 */
async function toggleFavorite() {
  if (!item.value) return
  const newState = !item.value.is_favorite
  try {
    await libraryStore.toggleFavorite(item.value.id)
    item.value.is_favorite = newState
    toast.success(newState ? 'Ajouté aux favoris ❤️' : 'Retiré des favoris 💔')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

/**
 * Définit la note.
 * @param {number} rating
 */
async function setRating(rating) {
  if (!item.value) return
  if (rating < 0 || rating > 10) return

  try {
    await libraryStore.setRating(item.value.id, rating)
    item.value.rating = rating
    toast.success(`Note : ${rating}/10`, '⭐')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

/**
 * Ajoute un tag.
 */
async function addTag() {
  const tag = newTag.value.trim()
  if (!tag || !item.value) return

  if (item.value.tags.includes(tag)) {
    toast.warning('Ce tag existe déjà', '⚠️')
    return
  }

  try {
    const updatedTags = [...item.value.tags, tag]
    await libraryStore.updateItem(item.value.id, { tags: updatedTags })
    item.value.tags = updatedTags
    newTag.value = ''
    toast.success(`Tag "${tag}" ajouté`, '🔖')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

/**
 * Supprime un tag.
 * @param {string} tag
 */
async function removeTag(tag) {
  if (!item.value) return

  try {
    const updatedTags = item.value.tags.filter((t) => t !== tag)
    await libraryStore.updateItem(item.value.id, { tags: updatedTags })
    item.value.tags = updatedTags
    toast.success(`Tag "${tag}" supprimé`, '🗑️')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

/**
 * Ouvre le lecteur.
 */
function openReader() {
  if (!item.value) return
  router.push({
    name: 'reader',
    params: {
      jobId: item.value.id,
    },
  })
}

/**
 * Télécharge le fichier CBZ.
 */
async function downloadItem() {
  if (!item.value) return
  downloading.value = true
  try {
    const blob = await api.download(`/library/${encodeURIComponent(item.value.id)}/download`)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = item.value.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toast.success('Téléchargement lancé', '⬇️')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    downloading.value = false
  }
}

/**
 * Ouvre la modale d'édition et pré-remplit le formulaire.
 */
function openEditModal() {
  if (!item.value) return
  editForm.title = item.value.title || ''
  editForm.author = item.value.metadata?.author || ''
  editForm.artist = item.value.metadata?.artist || ''
  editForm.series = item.value.metadata?.series || ''
  editForm.volume = item.value.metadata?.volume || ''
  editForm.publisher = item.value.metadata?.publisher || ''
  editForm.year = item.value.metadata?.year || null
  editForm.genre = Array.isArray(item.value.metadata?.genre)
    ? item.value.metadata.genre.join(', ')
    : item.value.metadata?.genre || ''
  editForm.language = item.value.metadata?.language || 'fr'
  editForm.description = item.value.metadata?.description || ''
  showEditModal.value = true
}

/**
 * Sauvegarde les métadonnées.
 */
async function saveMetadata() {
  if (!item.value) return
  saving.value = true
  try {
    const metadata = {
      author: editForm.author,
      artist: editForm.artist,
      series: editForm.series,
      volume: editForm.volume,
      publisher: editForm.publisher,
      year: editForm.year,
      genre: editForm.genre,
      language: editForm.language,
      description: editForm.description,
    }

    const updates = {
      title: editForm.title,
      metadata,
    }

    await libraryStore.updateItem(item.value.id, updates)

    // Mettre à jour localement
    item.value.title = editForm.title
    item.value.metadata = { ...item.value.metadata, ...metadata }

    showEditModal.value = false
    toast.success('Métadonnées sauvegardées', '💾')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    saving.value = false
  }
}

/**
 * Confirme la suppression.
 */
function confirmDelete() {
  showDeleteModal.value = true
}

/**
 * Supprime l'élément.
 */
async function deleteItem() {
  if (!item.value) return
  deleting.value = true
  try {
    await libraryStore.deleteItem(item.value.id, false)
    showDeleteModal.value = false
    toast.success(`"${item.value.title}" supprimé`, '🗑️')
    router.push('/library')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    deleting.value = false
  }
}

/**
 * Retour à la bibliothèque.
 */
function goBack() {
  router.push('/library')
}

/**
 * Retourne le label d'une langue.
 * @param {string} code
 * @returns {string}
 */
function getLanguageLabel(code) {
  const map = {
    fr: '🇫🇷 Français',
    en: '🇬🇧 Anglais',
    es: '🇪🇸 Espagnol',
    pt: '🇵🇹 Portugais',
    de: '🇩🇪 Allemand',
    it: '🇮🇹 Italien',
    ja: '🇯🇵 Japonais',
    ko: '🇰🇷 Coréen',
    zh: '🇨🇳 Chinois',
    ru: '🇷🇺 Russe',
  }
  return map[code] || code
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  await fetchItem()
})

// Surveiller les changements d'ID dans la route
watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      fetchItem()
    }
  }
)

// Ouvre automatiquement la modale d'édition si demandé via query
watch(
  () => route.query.edit,
  (val) => {
    if (val === 'true' && item.value) {
      openEditModal()
    }
  }
)
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.library-detail {
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
//  Loading / Error
// ==========================================================================

.library-detail__loading,
.library-detail__error {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  width: 100%;
}

.library-detail__error-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  text-align: center;
  padding: 2rem;
  max-width: 480px;
}

.library-detail__error-icon {
  font-size: 3rem;
}

.library-detail__error-title {
  margin: 0;
  font-size: 1.3rem;
  color: var(--color-text-primary, #e8edf5);
}

.library-detail__error-message {
  margin: 0;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.9rem;
}

.library-detail__error-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 0.5rem;
}

// ==========================================================================
//  Breadcrumb
// ==========================================================================

.library-detail__breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
  padding: 0.25rem 0;
}

.library-detail__breadcrumb-back {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: transparent;
  border: none;
  color: var(--color-primary, #00d4ff);
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0.15rem 0.4rem;
  border-radius: var(--radius-sm, 4px);
  transition: background 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }
}

.library-detail__breadcrumb-sep {
  opacity: 0.5;
}

.library-detail__breadcrumb-current {
  color: var(--color-text-secondary, #b0c0d8);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}

// ==========================================================================
//  Layout
// ==========================================================================

.library-detail__layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 1.5rem;
  align-items: start;
}

// ==========================================================================
//  Sidebar (colonne gauche)
// ==========================================================================

.library-detail__sidebar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
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

// ==========================================================================
//  Couverture
// ==========================================================================

.library-detail__cover-wrapper {
  position: relative;
  aspect-ratio: 2/3;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border, #1a2538);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.library-detail__cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.library-detail__cover-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 3rem;

  .library-detail__cover-placeholder-text {
    font-size: 0.75rem;
  }
}

.library-detail__cover-badges {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  right: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  pointer-events: none;
}

.library-detail__cover-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.2rem 0.5rem;
  font-size: 0.65rem;
  font-weight: 600;
  border-radius: var(--radius-full, 9999px);
  backdrop-filter: blur(4px);
  background: rgba(0, 0, 0, 0.6);
  color: #ffffff;

  &--favorite {
    background: rgba(244, 67, 54, 0.85);
  }

  &--rating {
    background: rgba(255, 193, 7, 0.9);
    color: #000;
  }
}

// ==========================================================================
//  Actions
// ==========================================================================

.library-detail__actions {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

// ==========================================================================
//  Notation
// ==========================================================================

.library-detail__rating-section {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding: 0.6rem 0.75rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
}

.library-detail__rating-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #b0c0d8);

  strong {
    color: var(--color-warning, #ff9800);
  }
}

.library-detail__rating-stars {
  display: flex;
  gap: 0.15rem;
  justify-content: center;
}

.library-detail__rating-star {
  background: transparent;
  border: none;
  color: var(--color-border, #1a2538);
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0;
  line-height: 1;
  transition: color 0.15s ease, transform 0.15s ease;

  &:hover {
    transform: scale(1.2);
    color: var(--color-warning, #ff9800);
  }

  &--active {
    color: var(--color-warning, #ff9800);
  }
}

// ==========================================================================
//  Stats mini
// ==========================================================================

.library-detail__stats-mini {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.library-detail__stat-mini {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  flex: 1;
  justify-content: center;
}

.library-detail__stat-mini-icon {
  font-size: 0.85rem;
}

.library-detail__stat-mini-value {
  color: var(--color-text-primary, #e8edf5);
  font-weight: 600;
}

// ==========================================================================
//  Main (colonne droite)
// ==========================================================================

.library-detail__main {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-width: 0;
}

.library-detail__header {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.library-detail__title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  line-height: 1.2;
  word-break: break-word;
}

.library-detail__series {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Sections
// ==========================================================================

.library-detail__section {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.library-detail__section-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.library-detail__section-count {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Meta grid
// ==========================================================================

.library-detail__meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.6rem;
  padding: 0.85rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  margin: 0;

  &--tech {
    grid-template-columns: 1fr;
  }
}

.library-detail__meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.library-detail__meta-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #6a7a9a);
  font-weight: 500;
}

.library-detail__meta-value {
  font-size: 0.8rem;
  color: var(--color-text-primary, #e8edf5);
  word-break: break-word;

  &--mono {
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 0.7rem;
    color: var(--color-text-secondary, #b0c0d8);
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

// ==========================================================================
//  Genres
// ==========================================================================

.library-detail__genres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.library-detail__genre {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.65rem;
  font-size: 0.7rem;
  font-weight: 500;
  background: rgba(0, 212, 255, 0.1);
  color: var(--color-primary, #00d4ff);
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: var(--radius-full, 9999px);
  text-transform: lowercase;
}

// ==========================================================================
//  Tags
// ==========================================================================

.library-detail__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
  padding: 0.6rem 0.75rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  min-height: 50px;
}

.library-detail__tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.5rem 0.2rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border-light, #253254);
  border-radius: var(--radius-full, 9999px);
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--color-primary, #00d4ff);
  }
}

.library-detail__tag-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  border-radius: 50%;
  padding: 0;
  transition: all 0.15s ease;

  &:hover {
    color: var(--color-error, #f44336);
    background: rgba(244, 67, 54, 0.1);
  }
}

.library-detail__tag-add {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  flex: 1;
  min-width: 150px;
  max-width: 250px;
}

.library-detail__tag-input {
  flex: 1;
  padding: 0.25rem 0.6rem;
  font-size: 0.7rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-full, 9999px);
  outline: none;
  min-width: 0;
  transition: border-color 0.15s ease;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
  }

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.library-detail__tag-add-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.15s ease;
  flex-shrink: 0;

  &:hover:not(:disabled) {
    transform: scale(1.1);
    filter: brightness(1.1);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

// ==========================================================================
//  Description
// ==========================================================================

.library-detail__description {
  margin: 0;
  padding: 0.85rem;
  font-size: 0.85rem;
  line-height: 1.65;
  color: var(--color-text-secondary, #b0c0d8);
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  white-space: pre-wrap;
  word-break: break-word;
}

// ==========================================================================
//  Delete warning
// ==========================================================================

.library-detail__delete-warning {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: rgba(244, 67, 54, 0.1);
  border-left: 3px solid var(--color-error, #f44336);
  border-radius: var(--radius-sm, 4px);
  font-size: 0.8rem;
  color: var(--color-error, #f44336);
}

// ==========================================================================
//  Formulaire d'édition
// ==========================================================================

.library-detail__edit-form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 0.25rem;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
    border-radius: 3px;
  }
}

.library-detail__form-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.library-detail__form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.library-detail__form-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-secondary, #b0c0d8);
}

.library-detail__form-input,
.library-detail__form-textarea {
  width: 100%;
  padding: 0.5rem 0.7rem;
  font-size: 0.85rem;
  font-family: inherit;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15);
  }

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.library-detail__form-textarea {
  resize: vertical;
  min-height: 100px;
  line-height: 1.5;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 900px) {
  .library-detail__layout {
    grid-template-columns: 1fr;
  }

  .library-detail__sidebar {
    position: static;
    max-height: none;
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 1rem;
    align-items: start;
  }

  .library-detail__cover-wrapper {
    grid-row: span 3;
  }

  .library-detail__actions {
    grid-column: 2;
    grid-row: 1;
  }

  .library-detail__rating-section {
    grid-column: 2;
    grid-row: 2;
  }

  .library-detail__stats-mini {
    grid-column: 2;
    grid-row: 3;
  }
}

@media (max-width: 600px) {
  .library-detail {
    padding: 0.5rem;
  }

  .library-detail__sidebar {
    grid-template-columns: 1fr;
  }

  .library-detail__cover-wrapper {
    grid-row: auto;
    max-width: 200px;
    margin: 0 auto;
  }

  .library-detail__actions,
  .library-detail__rating-section,
  .library-detail__stats-mini {
    grid-column: auto;
    grid-row: auto;
  }

  .library-detail__title {
    font-size: 1.35rem;
  }

  .library-detail__meta-grid {
    grid-template-columns: 1fr;
  }

  .library-detail__form-row {
    grid-template-columns: 1fr;
  }

  .library-detail__breadcrumb-current {
    max-width: 150px;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .library-detail__breadcrumb-current {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .library-detail__cover-wrapper {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  }

  .library-detail__title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .library-detail__meta-grid,
  .library-detail__tags,
  .library-detail__description,
  .library-detail__rating-section,
  .library-detail__stats-mini {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .library-detail__meta-value {
    color: var(--color-text-primary, #1a1a2e);
  }

  .library-detail__description {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .library-detail__tag {
    background: var(--color-bg-secondary, #e9ecf2);
    color: var(--color-text-secondary, #3d4a5c);
    border-color: var(--color-border, #d0d8e0);
  }

  .library-detail__tag-input {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);
  }

  .library-detail__form-input,
  .library-detail__form-textarea {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);
  }

  .library-detail__rating-star {
    color: var(--color-border, #d0d8e0);
  }

  .library-detail__stats-mini {
    color: var(--color-text-muted, #7a8a9a);
  }

  .library-detail__stat-mini-value {
    color: var(--color-text-primary, #1a1a2e);
  }

  .library-detail__genre {
    background: rgba(0, 102, 204, 0.1);
    color: var(--color-primary, #0066cc);
    border-color: rgba(0, 102, 204, 0.25);
  }
}
</style>
