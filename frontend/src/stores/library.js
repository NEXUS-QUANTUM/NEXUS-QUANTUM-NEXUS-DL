// ==========================================================================
//  NexusDL 2.0 - Library Store (Pinia)
//  Fichier : frontend/src/stores/library.js
//  Description : Gestion de la bibliothèque de fichiers CBZ (métadonnées, recherche, pagination, couverture)
//  Version : 2.0.0
// ==========================================================================

import { defineStore } from 'pinia'
import { ref, computed, watch, reactive, toRaw } from 'vue'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useAppStore } from '@/stores/app'

/**
 * Store pour la bibliothèque de fichiers CBZ.
 * Gère la liste des œuvres, les filtres, la pagination, les métadonnées,
 * les couvertures, les favoris, les notations, l'import/export.
 */
export const useLibraryStore = defineStore('library', () => {
  // ==========================================================================
  //  Dépendances
  // ==========================================================================

  const api = useApi()
  const toast = useToast()
  const appStore = useAppStore()

  // ==========================================================================
  //  État
  // ==========================================================================

  /** Liste des éléments de la bibliothèque (clé: id) */
  const items = ref({})
  /** IDs des éléments chargés */
  const itemIds = ref([])
  /** Filtres de recherche actuels */
  const filters = reactive({
    search: '',
    genre: '',
    author: '',
    tag: '',
    favorite: null, // null, true, false
    minRating: 0,
    maxRating: 10,
    sortBy: 'created_at', // 'title' | 'created_at' | 'size' | 'rating' | 'last_read' | 'read_count'
    sortOrder: 'desc', // 'asc' | 'desc'
    limit: 20,
    offset: 0,
  })
  /** Nombre total d'éléments (pour la pagination) */
  const totalItems = ref(0)
  /** Indicateur de chargement */
  const isLoading = ref(false)
  /** Erreur globale */
  const error = ref(null)
  /** Dernière mise à jour */
  const lastUpdated = ref(null)
  /** Éléments sélectionnés (pour les actions batch) */
  const selectedIds = ref([])
  /** Mode sélection */
  const selectionMode = ref(false)

  /** Cache des URLs de couverture (key: filename, value: url) */
  const coverCache = ref({})
  /** Couverture en cours de chargement (pour éviter les requêtes en double) */
  const coverLoading = ref(new Set())

  /** Statistiques de la bibliothèque (mises en cache) */
  const stats = ref(null)

  // ==========================================================================
  //  Getters
  // ==========================================================================

  /** Liste des éléments (tableau) */
  const itemList = computed(() =>
    Object.values(items.value)
  )

  /** Éléments paginés selon les filtres courants (calculé localement) */
  const filteredItems = computed(() => {
    let result = [...itemList.value]

    // Filtres
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      result = result.filter(item =>
        item.title.toLowerCase().includes(searchLower) ||
        (item.metadata?.author && item.metadata.author.toLowerCase().includes(searchLower)) ||
        (item.metadata?.series && item.metadata.series.toLowerCase().includes(searchLower))
      )
    }
    if (filters.genre) {
      const genreLower = filters.genre.toLowerCase()
      result = result.filter(item =>
        item.metadata?.genre && item.metadata.genre.toLowerCase().includes(genreLower)
      )
    }
    if (filters.author) {
      const authorLower = filters.author.toLowerCase()
      result = result.filter(item =>
        item.metadata?.author && item.metadata.author.toLowerCase().includes(authorLower)
      )
    }
    if (filters.tag) {
      const tagLower = filters.tag.toLowerCase()
      result = result.filter(item =>
        item.tags && item.tags.some(t => t.toLowerCase().includes(tagLower))
      )
    }
    if (filters.favorite !== null) {
      result = result.filter(item => item.is_favorite === filters.favorite)
    }
    if (filters.minRating > 0) {
      result = result.filter(item => item.rating >= filters.minRating)
    }
    if (filters.maxRating < 10) {
      result = result.filter(item => item.rating <= filters.maxRating)
    }

    // Tri
    const sortField = filters.sortBy || 'created_at'
    const sortOrder = filters.sortOrder || 'desc'
    result.sort((a, b) => {
      let aVal, bVal
      if (sortField === 'title') {
        aVal = a.title.toLowerCase()
        bVal = b.title.toLowerCase()
      } else if (sortField === 'size') {
        aVal = a.size_bytes || 0
        bVal = b.size_bytes || 0
      } else if (sortField === 'rating') {
        aVal = a.rating || 0
        bVal = b.rating || 0
      } else if (sortField === 'last_read') {
        aVal = a.last_read ? new Date(a.last_read).getTime() : 0
        bVal = b.last_read ? new Date(b.last_read).getTime() : 0
      } else if (sortField === 'read_count') {
        aVal = a.read_count || 0
        bVal = b.read_count || 0
      } else { // created_at par défaut
        aVal = new Date(a.created_at).getTime()
        bVal = new Date(b.created_at).getTime()
      }
      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1
      return 0
    })

    return result
  })

  /** Éléments paginés pour l'affichage */
  const paginatedItems = computed(() => {
    const start = filters.offset
    const end = start + filters.limit
    return filteredItems.value.slice(start, end)
  })

  /** Nombre total d'éléments après filtrage (pour la pagination) */
  const filteredTotal = computed(() => filteredItems.value.length)

  /** Vérifie si la bibliothèque est vide */
  const isEmpty = computed(() => Object.keys(items.value).length === 0)

  /** Nombre total d'éléments en bibliothèque (avant filtres) */
  const total = computed(() => Object.keys(items.value).length)

  /** Vérifie si un élément est sélectionné */
  const isSelected = (id) => selectedIds.value.includes(id)

  /** Tous les éléments sont-ils sélectionnés ? */
  const allSelected = computed(() => {
    if (paginatedItems.value.length === 0) return false
    return paginatedItems.value.every(item => selectedIds.value.includes(item.id))
  })

  /** Récupère un élément par son ID */
  const getItem = (id) => items.value[id] || null

  /** Récupère l'URL de couverture d'un élément (depuis le cache) */
  const getCover = (filename) => coverCache.value[filename] || null

  // ==========================================================================
  //  Actions
  // ==========================================================================

  // --------------------------------------------------------------------------
  //  Chargement
  // --------------------------------------------------------------------------

  /**
   * Récupère la liste des éléments depuis l'API en tenant compte des filtres.
   * @param {Object} overrideFilters - Surcharge des filtres pour cette requête
   * @returns {Promise<Array>} - Liste des éléments
   */
  async function fetchLibrary(overrideFilters = {}) {
    isLoading.value = true
    error.value = null

    // Fusionner les filtres
    const params = {
      search: filters.search || undefined,
      genre: filters.genre || undefined,
      author: filters.author || undefined,
      tag: filters.tag || undefined,
      favorite: filters.favorite !== null ? filters.favorite : undefined,
      min_rating: filters.minRating || undefined,
      max_rating: filters.maxRating || undefined,
      sort_by: filters.sortBy || 'created_at',
      sort_order: filters.sortOrder || 'desc',
      limit: filters.limit,
      offset: filters.offset,
      ...overrideFilters,
    }

    // Supprimer les valeurs vides
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === null || params[key] === '') {
        delete params[key]
      }
    })

    try {
      const response = await api.get('/library/', { params })
      // La réponse peut être un tableau ou un objet paginé
      let itemsArray = Array.isArray(response) ? response : (response.items || [])
      const total = response.total ?? itemsArray.length

      // Mettre à jour le store
      const newItems = {}
      for (const item of itemsArray) {
        // S'assurer que les métadonnées sont bien structurées
        const normalized = normalizeItem(item)
        newItems[normalized.id] = normalized
      }
      items.value = { ...items.value, ...newItems }
      // Pour les IDs, on peut garder l'ordre de la réponse
      const ids = itemsArray.map(item => item.id || item.filename)
      // Ne pas remplacer complètement itemIds si on a une pagination partielle ?
      // On va fusionner : garder l'ordre pour la page courante
      // Mais pour simplifier, on met à jour la liste complète des IDs (peut être lourd)
      // On va stocker uniquement les IDs de la page courante
      itemIds.value = ids
      totalItems.value = total
      lastUpdated.value = new Date().toISOString()
      return itemsArray
    } catch (err) {
      error.value = err
      toast.error(`Erreur chargement bibliothèque: ${err.message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Récupère un élément spécifique par son ID (filename).
   * @param {string} id - ID de l'élément (filename)
   * @param {boolean} force - Forcer la récupération depuis le serveur
   * @returns {Promise<Object>} - Élément
   */
  async function fetchItem(id, force = false) {
    if (!id) return null
    if (!force && items.value[id]) {
      return items.value[id]
    }
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get(`/library/${encodeURIComponent(id)}`)
      const normalized = normalizeItem(response)
      items.value[normalized.id] = normalized
      // Mettre à jour les IDs si nécessaire
      if (!itemIds.value.includes(normalized.id)) {
        itemIds.value.push(normalized.id)
      }
      lastUpdated.value = new Date().toISOString()
      return normalized
    } catch (err) {
      error.value = err
      if (err.response?.status === 404) {
        // Élément introuvable, le retirer du store
        delete items.value[id]
        const idx = itemIds.value.indexOf(id)
        if (idx !== -1) itemIds.value.splice(idx, 1)
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Rafraîchit la bibliothèque (recharge depuis le serveur).
   */
  async function refresh() {
    // Réinitialiser les filtres ?
    // On garde les filtres actuels mais on recharge
    await fetchLibrary()
  }

  // --------------------------------------------------------------------------
  //  Recherche et filtres
  // --------------------------------------------------------------------------

  /**
   * Applique un filtre de recherche.
   * @param {string} query - Terme de recherche
   * @param {string} field - Champ de recherche ('title', 'author', 'genre', 'tag')
   */
  function setSearch(query, field = 'search') {
    if (field === 'title' || field === 'search') {
      filters.search = query
    } else if (field === 'author') {
      filters.author = query
    } else if (field === 'genre') {
      filters.genre = query
    } else if (field === 'tag') {
      filters.tag = query
    }
    // Réinitialiser l'offset pour la pagination
    filters.offset = 0
    // Recharger
    fetchLibrary()
  }

  /**
   * Applique un filtre de genre.
   * @param {string} genre - Genre à filtrer
   */
  function setGenre(genre) {
    filters.genre = genre || ''
    filters.offset = 0
    fetchLibrary()
  }

  /**
   * Applique un filtre d'auteur.
   * @param {string} author - Auteur à filtrer
   */
  function setAuthor(author) {
    filters.author = author || ''
    filters.offset = 0
    fetchLibrary()
  }

  /**
   * Applique un filtre de tag.
   * @param {string} tag - Tag à filtrer
   */
  function setTag(tag) {
    filters.tag = tag || ''
    filters.offset = 0
    fetchLibrary()
  }

  /**
   * Filtre par favoris.
   * @param {boolean|null} value - true, false ou null (tous)
   */
  function setFavoriteFilter(value) {
    filters.favorite = value
    filters.offset = 0
    fetchLibrary()
  }

  /**
   * Définit les bornes de notation.
   * @param {number} min - Note minimale (0-10)
   * @param {number} max - Note maximale (0-10)
   */
  function setRatingFilter(min = 0, max = 10) {
    filters.minRating = Math.max(0, Math.min(10, min))
    filters.maxRating = Math.max(0, Math.min(10, max))
    filters.offset = 0
    fetchLibrary()
  }

  /**
   * Définit le tri.
   * @param {string} sortBy - Champ de tri ('title', 'created_at', 'size', 'rating', 'last_read', 'read_count')
   * @param {string} sortOrder - 'asc' ou 'desc'
   */
  function setSort(sortBy, sortOrder = 'desc') {
    filters.sortBy = sortBy
    filters.sortOrder = sortOrder
    filters.offset = 0
    fetchLibrary()
  }

  /**
   * Change la page de résultats.
   * @param {number} page - Numéro de page (commence à 1)
   */
  function setPage(page) {
    const offset = (page - 1) * filters.limit
    filters.offset = Math.max(0, offset)
    fetchLibrary()
  }

  /**
   * Change le nombre d'éléments par page.
   * @param {number} limit - Nouvelle limite
   */
  function setLimit(limit) {
    filters.limit = Math.max(1, Math.min(100, limit))
    filters.offset = 0
    fetchLibrary()
  }

  /**
   * Réinitialise tous les filtres.
   */
  function resetFilters() {
    filters.search = ''
    filters.genre = ''
    filters.author = ''
    filters.tag = ''
    filters.favorite = null
    filters.minRating = 0
    filters.maxRating = 10
    filters.sortBy = 'created_at'
    filters.sortOrder = 'desc'
    filters.offset = 0
    fetchLibrary()
  }

  // --------------------------------------------------------------------------
  //  Mise à jour des éléments
  // --------------------------------------------------------------------------

  /**
   * Met à jour les métadonnées d'un élément.
   * @param {string} id - ID de l'élément
   * @param {Object} updates - Champs à mettre à jour (title, tags, is_favorite, rating, metadata)
   * @returns {Promise<Object>} - Élément mis à jour
   */
  async function updateItem(id, updates) {
    const item = items.value[id]
    if (!item) {
      toast.error('Élément introuvable.', '❌')
      throw new Error('Élément introuvable')
    }

    isLoading.value = true
    error.value = null
    try {
      // On utilise PATCH /library/{id}
      const response = await api.patch(`/library/${encodeURIComponent(id)}`, updates)
      // Fusionner les données
      const updated = normalizeItem({ ...item, ...response, ...updates })
      items.value[id] = updated
      lastUpdated.value = new Date().toISOString()
      // Si le titre change, mettre à jour le cache des couvertures (peut-être)
      if (updates.title) {
        // Pas d'action spéciale
      }
      toast.success(`"${updated.title}" mis à jour.`, '✅')
      return updated
    } catch (err) {
      error.value = err
      toast.error(`Erreur mise à jour: ${err.message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Bascule le statut favori d'un élément.
   * @param {string} id - ID de l'élément
   * @returns {Promise<Object>}
   */
  async function toggleFavorite(id) {
    const item = items.value[id]
    if (!item) {
      toast.error('Élément introuvable.', '❌')
      throw new Error('Élément introuvable')
    }
    const newState = !item.is_favorite
    const result = await updateItem(id, { is_favorite: newState })
    toast.info(newState ? 'Ajouté aux favoris ❤️' : 'Retiré des favoris 💔')
    return result
  }

  /**
   * Définit la notation d'un élément.
   * @param {string} id - ID de l'élément
   * @param {number} rating - Note (0-10)
   * @returns {Promise<Object>}
   */
  async function setRating(id, rating) {
    const item = items.value[id]
    if (!item) {
      toast.error('Élément introuvable.', '❌')
      throw new Error('Élément introuvable')
    }
    if (rating < 0 || rating > 10) {
      toast.error('La note doit être comprise entre 0 et 10.', '❌')
      throw new Error('Note invalide')
    }
    return await updateItem(id, { rating })
  }

  /**
   * Ajoute un tag à un élément.
   * @param {string} id - ID de l'élément
   * @param {string} tag - Tag à ajouter
   * @returns {Promise<Object>}
   */
  async function addTag(id, tag) {
    const item = items.value[id]
    if (!item) {
      toast.error('Élément introuvable.', '❌')
      throw new Error('Élément introuvable')
    }
    const currentTags = Array.isArray(item.tags) ? item.tags : []
    if (currentTags.includes(tag)) {
      toast.warning('Tag déjà présent.', '⚠️')
      return item
    }
    const newTags = [...currentTags, tag]
    return await updateItem(id, { tags: newTags })
  }

  /**
   * Supprime un tag d'un élément.
   * @param {string} id - ID de l'élément
   * @param {string} tag - Tag à supprimer
   * @returns {Promise<Object>}
   */
  async function removeTag(id, tag) {
    const item = items.value[id]
    if (!item) {
      toast.error('Élément introuvable.', '❌')
      throw new Error('Élément introuvable')
    }
    const currentTags = Array.isArray(item.tags) ? item.tags : []
    const newTags = currentTags.filter(t => t !== tag)
    if (newTags.length === currentTags.length) {
      toast.warning('Tag non trouvé.', '⚠️')
      return item
    }
    return await updateItem(id, { tags: newTags })
  }

  // --------------------------------------------------------------------------
  //  Suppression
  // --------------------------------------------------------------------------

  /**
   * Supprime un élément de la bibliothèque.
   * @param {string} id - ID de l'élément
   * @param {boolean} confirm - Demander confirmation
   * @returns {Promise<boolean>}
   */
  async function deleteItem(id, confirm = true) {
    const item = items.value[id]
    if (!item) {
      toast.error('Élément introuvable.', '❌')
      return false
    }
    if (confirm && !window.confirm(`Supprimer définitivement "${item.title}" ?`)) {
      return false
    }
    isLoading.value = true
    error.value = null
    try {
      await api.delete(`/library/${encodeURIComponent(id)}`)
      // Retirer du store
      delete items.value[id]
      const idx = itemIds.value.indexOf(id)
      if (idx !== -1) itemIds.value.splice(idx, 1)
      // Retirer du cache de couverture
      delete coverCache.value[id]
      // Désélectionner si sélectionné
      const selIdx = selectedIds.value.indexOf(id)
      if (selIdx !== -1) selectedIds.value.splice(selIdx, 1)
      lastUpdated.value = new Date().toISOString()
      toast.success(`"${item.title}" supprimé.`, '🗑️')
      return true
    } catch (err) {
      error.value = err
      toast.error(`Erreur suppression: ${err.message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Supprime plusieurs éléments.
   * @param {Array<string>} ids - Liste des IDs
   * @param {boolean} confirm - Demander confirmation
   * @returns {Promise<number>} - Nombre d'éléments supprimés
   */
  async function deleteItems(ids, confirm = true) {
    if (!ids || ids.length === 0) {
      toast.warning('Aucun élément sélectionné.', '⚠️')
      return 0
    }
    if (confirm && !window.confirm(`Supprimer ${ids.length} élément(s) ?`)) {
      return 0
    }
    let deleted = 0
    for (const id of ids) {
      try {
        const success = await deleteItem(id, false)
        if (success) deleted++
      } catch (_) {
        // Ignorer les erreurs individuelles
      }
    }
    toast.success(`${deleted} élément(s) supprimé(s).`, '🗑️')
    return deleted
  }

  // --------------------------------------------------------------------------
  //  Sélection
  // --------------------------------------------------------------------------

  /**
   * Sélectionne/Désélectionne un élément.
   * @param {string} id - ID de l'élément
   * @param {boolean} selected - État de sélection (si non fourni, toggle)
   */
  function toggleSelect(id, selected) {
    if (selected === undefined) {
      const idx = selectedIds.value.indexOf(id)
      if (idx === -1) {
        selectedIds.value.push(id)
      } else {
        selectedIds.value.splice(idx, 1)
      }
    } else if (selected) {
      if (!selectedIds.value.includes(id)) {
        selectedIds.value.push(id)
      }
    } else {
      const idx = selectedIds.value.indexOf(id)
      if (idx !== -1) selectedIds.value.splice(idx, 1)
    }
    selectionMode.value = selectedIds.value.length > 0
  }

  /**
   * Sélectionne tous les éléments de la page courante.
   */
  function selectAll() {
    const ids = paginatedItems.value.map(item => item.id)
    for (const id of ids) {
      if (!selectedIds.value.includes(id)) {
        selectedIds.value.push(id)
      }
    }
    selectionMode.value = true
  }

  /**
   * Désélectionne tous les éléments.
   */
  function deselectAll() {
    selectedIds.value = []
    selectionMode.value = false
  }

  /**
   * Sélectionne tous les éléments de la bibliothèque (attention, peut être lourd).
   */
  function selectAllItems() {
    const ids = Object.keys(items.value)
    selectedIds.value = [...ids]
    selectionMode.value = true
  }

  // --------------------------------------------------------------------------
  //  Import / Export
  // --------------------------------------------------------------------------

  /**
   * Importe un fichier CBZ dans la bibliothèque (upload).
   * @param {File} file - Fichier CBZ
   * @param {Object} metadata - Métadonnées additionnelles
   * @returns {Promise<Object>} - Élément importé
   */
  async function importCbz(file, metadata = {}) {
    if (!file || file.type !== 'application/zip' && !file.name.endsWith('.cbz')) {
      toast.error('Veuillez sélectionner un fichier CBZ.', '❌')
      throw new Error('Fichier invalide')
    }

    const formData = new FormData()
    formData.append('file', file)
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata))
    }

    isLoading.value = true
    error.value = null
    appStore.startLoading('Importation en cours...')

    try {
      const response = await api.upload('/library/import', formData, (percent) => {
        // Progression (utiliser un toast ou une barre de progression)
        if (percent % 10 === 0) {
          toast.info(`Importation: ${percent}%`, '⏳', { duration: 1000 })
        }
      })
      const item = normalizeItem(response)
      items.value[item.id] = item
      if (!itemIds.value.includes(item.id)) {
        itemIds.value.push(item.id)
      }
      lastUpdated.value = new Date().toISOString()
      toast.success(`"${item.title}" importé avec succès.`, '📥')
      return item
    } catch (err) {
      error.value = err
      toast.error(`Erreur importation: ${err.message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
      appStore.stopLoading()
    }
  }

  /**
   * Exporte la bibliothèque au format JSON (métadonnées uniquement).
   * @param {Array<string>} ids - IDs à exporter (tous si vide)
   * @returns {Promise<Object>} - Données exportées
   */
  async function exportMetadata(ids = []) {
    const data = {
      exported_at: new Date().toISOString(),
      version: import.meta.env.VITE_APP_VERSION || '2.0.0',
      items: [],
    }
    const itemsToExport = ids.length > 0 ? ids.map(id => items.value[id]).filter(Boolean) : Object.values(items.value)
    for (const item of itemsToExport) {
      // N'inclure que les métadonnées, pas les chemins de fichiers sensibles
      data.items.push({
        id: item.id,
        title: item.title,
        filename: item.filename,
        size_bytes: item.size_bytes,
        created_at: item.created_at,
        updated_at: item.updated_at,
        last_read: item.last_read,
        read_count: item.read_count,
        is_favorite: item.is_favorite,
        rating: item.rating,
        metadata: item.metadata || {},
        tags: item.tags || [],
      })
    }
    return data
  }

  /**
   * Télécharge la bibliothèque exportée en JSON.
   * @param {Array<string>} ids - IDs à exporter
   */
  async function downloadExport(ids = []) {
    const data = await exportMetadata(ids)
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `nexusdl_library_export_${new Date().toISOString().slice(0,10)}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toast.success('Export terminé.', '📤')
  }

  // --------------------------------------------------------------------------
  //  Couvertures (miniatures)
  // --------------------------------------------------------------------------

  /**
   * Récupère l'URL de la couverture pour un élément.
   * @param {string} id - ID de l'élément
   * @param {number} width - Largeur souhaitée
   * @param {number} height - Hauteur souhaitée
   * @returns {Promise<string|null>} - URL de la couverture
   */
  async function fetchCover(id, width = 200, height = 300) {
    const item = items.value[id]
    if (!item) return null
    const filename = item.filename
    if (coverCache.value[filename]) {
      return coverCache.value[filename]
    }
    // Éviter les requêtes en double
    if (coverLoading.value.has(filename)) {
      // Attendre que le chargement se termine (approche simple : on retourne null et on réessaiera)
      return null
    }
    coverLoading.value.add(filename)
    try {
      const response = await api.get(`/library/${encodeURIComponent(id)}/cover`, {
        params: { width, height },
        responseType: 'blob',
      })
      const url = URL.createObjectURL(response)
      coverCache.value[filename] = url
      return url
    } catch (err) {
      // Erreur silencieuse (pas de notification)
      return null
    } finally {
      coverLoading.value.delete(filename)
    }
  }

  /**
   * Nettoie le cache des couvertures.
   */
  function clearCoverCache() {
    // Révoquer les URLs
    for (const url of Object.values(coverCache.value)) {
      try { URL.revokeObjectURL(url) } catch (_) {}
    }
    coverCache.value = {}
    coverLoading.value.clear()
  }

  // --------------------------------------------------------------------------
  //  Statistiques
  // --------------------------------------------------------------------------

  /**
   * Récupère les statistiques de la bibliothèque.
   * @param {boolean} force - Forcer la récupération
   * @returns {Promise<Object>} - Statistiques
   */
  async function fetchStats(force = false) {
    if (stats.value && !force) {
      return stats.value
    }
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get('/library/stats')
      stats.value = response
      return stats.value
    } catch (err) {
      error.value = err
      toast.error(`Erreur statistiques: ${err.message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // --------------------------------------------------------------------------
  //  Utilitaires
  // --------------------------------------------------------------------------

  /**
   * Normalise un élément pour garantir une structure cohérente.
   * @param {Object} raw - Données brutes
   * @returns {Object} - Élément normalisé
   */
  function normalizeItem(raw) {
    if (!raw) return null
    return {
      id: raw.id || raw.filename || '',
      filename: raw.filename || raw.id || '',
      title: raw.title || 'Sans titre',
      file_path: raw.file_path || '',
      size_bytes: raw.size_bytes || 0,
      created_at: raw.created_at || new Date().toISOString(),
      updated_at: raw.updated_at || new Date().toISOString(),
      last_read: raw.last_read || null,
      read_count: raw.read_count || 0,
      is_favorite: raw.is_favorite || false,
      rating: raw.rating || 0,
      metadata: raw.metadata || {},
      tags: Array.isArray(raw.tags) ? raw.tags : [],
      cover_path: raw.cover_path || null,
      size_formatted: raw.size_formatted || formatSize(raw.size_bytes || 0),
      // Pour compatibilité
      author: raw.metadata?.author || '',
      genre: raw.metadata?.genre || '',
      description: raw.metadata?.description || '',
      series: raw.metadata?.series || '',
    }
  }

  /**
   * Formate une taille en octets en chaîne lisible.
   * @param {number} bytes - Taille en octets
   * @returns {string}
   */
  function formatSize(bytes) {
    if (bytes === 0) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
  }

  // ==========================================================================
  //  Initialisation
  // ==========================================================================

  /**
   * Initialise le store.
   * @param {Object} options - Options
   * @param {boolean} options.load - Charger les données immédiatement (défaut: true)
   * @param {boolean} options.stats - Charger les statistiques (défaut: false)
   * @returns {Promise<void>}
   */
  async function initialize({ load = true, stats: loadStats = false } = {}) {
    if (load) {
      await fetchLibrary()
    }
    if (loadStats) {
      await fetchStats()
    }
  }

  /**
   * Réinitialise le store.
   */
  function reset() {
    items.value = {}
    itemIds.value = []
    totalItems.value = 0
    isLoading.value = false
    error.value = null
    lastUpdated.value = null
    selectedIds.value = []
    selectionMode.value = false
    clearCoverCache()
    stats.value = null
    // Réinitialiser les filtres ?
    Object.assign(filters, {
      search: '',
      genre: '',
      author: '',
      tag: '',
      favorite: null,
      minRating: 0,
      maxRating: 10,
      sortBy: 'created_at',
      sortOrder: 'desc',
      limit: 20,
      offset: 0,
    })
  }

  // ==========================================================================
  //  Retour
  // ==========================================================================

  return {
    // État
    items,
    itemIds,
    filters,
    totalItems,
    isLoading,
    error,
    lastUpdated,
    selectedIds,
    selectionMode,
    stats,

    // Getters
    itemList,
    filteredItems,
    paginatedItems,
    filteredTotal,
    isEmpty,
    total,
    isSelected,
    allSelected,
    getItem,
    getCover,

    // Actions
    fetchLibrary,
    fetchItem,
    refresh,
    setSearch,
    setGenre,
    setAuthor,
    setTag,
    setFavoriteFilter,
    setRatingFilter,
    setSort,
    setPage,
    setLimit,
    resetFilters,
    updateItem,
    toggleFavorite,
    setRating,
    addTag,
    removeTag,
    deleteItem,
    deleteItems,
    toggleSelect,
    selectAll,
    deselectAll,
    selectAllItems,
    importCbz,
    exportMetadata,
    downloadExport,
    fetchCover,
    clearCoverCache,
    fetchStats,
    initialize,
    reset,
  }
})

// ==========================================================================
//  Export du store
// ==========================================================================

export default useLibraryStore
