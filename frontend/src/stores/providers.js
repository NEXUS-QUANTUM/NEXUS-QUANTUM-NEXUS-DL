// ==========================================================================
//  NexusDL 2.0 - Providers Store (Pinia)
//  Fichier : frontend/src/stores/providers.js
//  Description : Gestion des providers de sites de scan (liste, état, filtres)
//  Version : 2.0.0
// ==========================================================================

import { defineStore } from 'pinia'
import { ref, computed, watch, reactive, toRaw } from 'vue'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useAppStore } from '@/stores/app'

/**
 * Store pour gérer les providers (sites de scan) disponibles dans NexusDL.
 * Permet de lister, filtrer, activer/désactiver des providers.
 */
export const useProvidersStore = defineStore('providers', () => {
  // ==========================================================================
  //  Dépendances
  // ==========================================================================

  const api = useApi()
  const toast = useToast()
  const appStore = useAppStore()

  // ==========================================================================
  //  État
  // ==========================================================================

  /** Liste des providers (indexée par id) */
  const providers = ref({})
  /** IDs des providers chargés (ordre) */
  const providerIds = ref([])
  /** Indicateur de chargement */
  const isLoading = ref(false)
  /** Erreur globale */
  const error = ref(null)
  /** Dernière mise à jour */
  const lastUpdated = ref(null)

  /** Filtres actifs */
  const filters = reactive({
    search: '',
    language: '',
    includeNsfw: false,
    onlyEnabled: false,
  })

  /** Mode sélection (pour activation/désactivation en masse) */
  const selectedIds = ref([])

  // ==========================================================================
  //  Getters
  // ==========================================================================

  /** Liste des providers (tableau) */
  const providerList = computed(() =>
    Object.values(providers.value)
  )

  /** Providers filtrés selon les filtres actifs */
  const filteredProviders = computed(() => {
    let result = [...providerList.value]

    // Recherche textuelle (nom, description)
    if (filters.search) {
      const q = filters.search.toLowerCase()
      result = result.filter(p =>
        p.name.toLowerCase().includes(q) ||
        (p.description && p.description.toLowerCase().includes(q)) ||
        p.id.toLowerCase().includes(q)
      )
    }

    // Filtre par langue
    if (filters.language) {
      result = result.filter(p =>
        p.languages && p.languages.some(lang =>
          lang.toLowerCase().includes(filters.language.toLowerCase())
        )
      )
    }

    // Filtre NSFW
    if (!filters.includeNsfw) {
      result = result.filter(p => !p.nsfw)
    }

    // Filtre "uniquement activés"
    if (filters.onlyEnabled) {
      result = result.filter(p => p.enabled)
    }

    // Tri par priorité (décroissant) puis par nom
    result.sort((a, b) => {
      if (a.priority !== b.priority) {
        return (b.priority || 0) - (a.priority || 0)
      }
      return a.name.localeCompare(b.name)
    })

    return result
  })

  /** Providers activés */
  const enabledProviders = computed(() =>
    providerList.value.filter(p => p.enabled)
  )

  /** Providers désactivés */
  const disabledProviders = computed(() =>
    providerList.value.filter(p => !p.enabled)
  )

  /** Nombre total de providers */
  const total = computed(() => providerList.value.length)

  /** Nombre de providers activés */
  const enabledCount = computed(() => enabledProviders.value.length)

  /** Nombre de providers désactivés */
  const disabledCount = computed(() => disabledProviders.value.length)

  /** Vérifie si un provider est sélectionné */
  const isSelected = (id) => selectedIds.value.includes(id)

  /** Vérifie si tous les providers filtrés sont sélectionnés */
  const allSelected = computed(() => {
    if (filteredProviders.value.length === 0) return false
    return filteredProviders.value.every(p => selectedIds.value.includes(p.id))
  })

  /** Récupère un provider par son ID */
  const getProvider = (id) => providers.value[id] || null

  /** Récupère un provider par son nom */
  const getProviderByName = (name) => {
    return providerList.value.find(p => p.name.toLowerCase() === name.toLowerCase()) || null
  }

  /** Liste des langues disponibles parmi tous les providers */
  const availableLanguages = computed(() => {
    const langSet = new Set()
    for (const p of providerList.value) {
      if (p.languages) {
        p.languages.forEach(lang => langSet.add(lang))
      }
    }
    return Array.from(langSet).sort()
  })

  /** Vérifie s'il y a des providers NSFW (pour afficher un warning) */
  const hasNsfwProviders = computed(() =>
    providerList.value.some(p => p.nsfw)
  )

  // ==========================================================================
  //  Actions
  // ==========================================================================

  // --------------------------------------------------------------------------
  //  Chargement des providers
  // --------------------------------------------------------------------------

  /**
   * Récupère la liste des providers depuis l'API.
   * @param {Object} params - Paramètres supplémentaires (ex: include_nsfw)
   * @returns {Promise<Array>} - Liste des providers
   */
  async function fetchProviders(params = {}) {
    isLoading.value = true
    error.value = null

    try {
      // Appel à l'API /providers (ou /admin/providers si admin)
      const response = await api.get('/browse/providers', { params })
      // La réponse peut être un tableau ou un objet paginé
      let providersArray = Array.isArray(response) ? response : (response.providers || response.items || [])
      // Normaliser
      const newProviders = {}
      const ids = []
      for (const p of providersArray) {
        const normalized = normalizeProvider(p)
        newProviders[normalized.id] = normalized
        ids.push(normalized.id)
      }
      providers.value = newProviders
      providerIds.value = ids
      lastUpdated.value = new Date().toISOString()
      return providersArray
    } catch (err) {
      error.value = err
      toast.error(`Erreur chargement des providers: ${err.message}`, '❌')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Récupère un provider spécifique par son ID.
   * @param {string} id - ID du provider
   * @param {boolean} force - Forcer le rechargement
   * @returns {Promise<Object>} - Provider
   */
  async function fetchProvider(id, force = false) {
    if (!force && providers.value[id]) {
      return providers.value[id]
    }
    isLoading.value = true
    error.value = null
    try {
      // On peut utiliser l'endpoint admin si l'utilisateur est admin
      const response = await api.get(`/admin/providers/${id}`)
      const normalized = normalizeProvider(response)
      providers.value[normalized.id] = normalized
      if (!providerIds.value.includes(normalized.id)) {
        providerIds.value.push(normalized.id)
      }
      lastUpdated.value = new Date().toISOString()
      return normalized
    } catch (err) {
      error.value = err
      if (err.response?.status === 404) {
        // Provider introuvable, on le retire du store
        delete providers.value[id]
        const idx = providerIds.value.indexOf(id)
        if (idx !== -1) providerIds.value.splice(idx, 1)
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // --------------------------------------------------------------------------
  //  Activation / Désactivation
  // --------------------------------------------------------------------------

  /**
   * Active ou désactive un provider.
   * @param {string} id - ID du provider
   * @param {boolean} enabled - Nouvel état
   * @returns {Promise<Object>} - Provider mis à jour
   */
  async function toggleProvider(id, enabled) {
    const provider = providers.value[id]
    if (!provider) {
      toast.error('Provider introuvable.', '❌')
      throw new Error('Provider introuvable')
    }
    isLoading.value = true
    error.value = null
    try {
      // Utiliser l'endpoint admin
      const response = await api.patch(`/admin/providers/${id}`, { enabled })
      const updated = normalizeProvider(response)
      providers.value[id] = updated
      lastUpdated.value = new Date().toISOString()
      toast.info(`Provider "${updated.name}" ${enabled ? 'activé' : 'désactivé'}.`, '🔧')
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
   * Active plusieurs providers.
   * @param {Array<string>} ids - Liste d'IDs
   * @returns {Promise<number>} - Nombre de providers activés
   */
  async function enableProviders(ids) {
    let count = 0
    for (const id of ids) {
      try {
        const p = providers.value[id]
        if (p && !p.enabled) {
          await toggleProvider(id, true)
          count++
        }
      } catch (_) {
        // Ignorer les erreurs individuelles
      }
    }
    toast.success(`${count} provider(s) activé(s).`, '✅')
    return count
  }

  /**
   * Désactive plusieurs providers.
   * @param {Array<string>} ids - Liste d'IDs
   * @returns {Promise<number>} - Nombre de providers désactivés
   */
  async function disableProviders(ids) {
    let count = 0
    for (const id of ids) {
      try {
        const p = providers.value[id]
        if (p && p.enabled) {
          await toggleProvider(id, false)
          count++
        }
      } catch (_) {
        // Ignorer les erreurs individuelles
      }
    }
    toast.success(`${count} provider(s) désactivé(s).`, '⛔')
    return count
  }

  // --------------------------------------------------------------------------
  //  Filtres
  // --------------------------------------------------------------------------

  /**
   * Définit le filtre de recherche.
   * @param {string} query - Terme de recherche
   */
  function setSearch(query) {
    filters.search = query || ''
  }

  /**
   * Définit le filtre de langue.
   * @param {string} language - Code langue
   */
  function setLanguage(language) {
    filters.language = language || ''
  }

  /**
   * Inclut ou exclut les providers NSFW.
   * @param {boolean} include - Inclure les NSFW
   */
  function setIncludeNsfw(include) {
    filters.includeNsfw = include
  }

  /**
   * Filtre uniquement les providers activés.
   * @param {boolean} onlyEnabled - Uniquement activés
   */
  function setOnlyEnabled(onlyEnabled) {
    filters.onlyEnabled = onlyEnabled
  }

  /**
   * Réinitialise tous les filtres.
   */
  function resetFilters() {
    filters.search = ''
    filters.language = ''
    filters.includeNsfw = false
    filters.onlyEnabled = false
  }

  // --------------------------------------------------------------------------
  //  Sélection
  // --------------------------------------------------------------------------

  /**
   * Sélectionne/Désélectionne un provider.
   * @param {string} id - ID du provider
   * @param {boolean} selected - État de sélection (toggle si non fourni)
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
  }

  /**
   * Sélectionne tous les providers (filtrés).
   */
  function selectAll() {
    const ids = filteredProviders.value.map(p => p.id)
    selectedIds.value = ids
  }

  /**
   * Désélectionne tous les providers.
   */
  function deselectAll() {
    selectedIds.value = []
  }

  // --------------------------------------------------------------------------
  //  Synchronisation depuis WebSocket (mise à jour en temps réel)
  // --------------------------------------------------------------------------

  /**
   * Met à jour un provider localement (utilisé par WebSocket).
   * @param {Object} data - Données du provider
   */
  function updateProviderFromWs(data) {
    if (!data || !data.id) return
    const existing = providers.value[data.id]
    const normalized = normalizeProvider(data)
    if (existing) {
      // Fusionner
      providers.value[data.id] = { ...existing, ...normalized }
    } else {
      providers.value[data.id] = normalized
      if (!providerIds.value.includes(normalized.id)) {
        providerIds.value.push(normalized.id)
      }
    }
    lastUpdated.value = new Date().toISOString()
  }

  // --------------------------------------------------------------------------
  //  Utilitaires
  // --------------------------------------------------------------------------

  /**
   * Normalise un provider pour garantir une structure cohérente.
   * @param {Object} raw - Données brutes
   * @returns {Object} - Provider normalisé
   */
  function normalizeProvider(raw) {
    if (!raw) return null
    return {
      id: raw.id || raw.provider_id || '',
      provider_id: raw.provider_id || raw.id || '',
      name: raw.name || 'Sans nom',
      base_url: raw.base_url || '',
      enabled: raw.enabled !== undefined ? raw.enabled : true,
      nsfw: raw.nsfw || false,
      languages: Array.isArray(raw.languages) ? raw.languages : (raw.supported_languages || []),
      version: raw.version || '1.0.0',
      description: raw.description || '',
      priority: raw.priority || 0,
      last_used: raw.last_used || null,
      created_at: raw.created_at || new Date().toISOString(),
      updated_at: raw.updated_at || new Date().toISOString(),
      // Compatibilité
      supported_languages: raw.supported_languages || raw.languages || [],
    }
  }

  // ==========================================================================
  //  Initialisation
  // ==========================================================================

  /**
   * Initialise le store.
   * @param {Object} options - Options
   * @param {boolean} options.load - Charger les providers immédiatement (défaut: true)
   * @param {Object} options.params - Paramètres pour la requête
   * @returns {Promise<void>}
   */
  async function initialize({ load = true, params = {} } = {}) {
    if (load) {
      await fetchProviders(params)
    }
  }

  /**
   * Réinitialise le store.
   */
  function reset() {
    providers.value = {}
    providerIds.value = []
    isLoading.value = false
    error.value = null
    lastUpdated.value = null
    selectedIds.value = []
    resetFilters()
  }

  // ==========================================================================
  //  Retour
  // ==========================================================================

  return {
    // État
    providers,
    providerIds,
    isLoading,
    error,
    lastUpdated,
    filters,
    selectedIds,

    // Getters
    providerList,
    filteredProviders,
    enabledProviders,
    disabledProviders,
    total,
    enabledCount,
    disabledCount,
    isSelected,
    allSelected,
    getProvider,
    getProviderByName,
    availableLanguages,
    hasNsfwProviders,

    // Actions
    fetchProviders,
    fetchProvider,
    toggleProvider,
    enableProviders,
    disableProviders,
    setSearch,
    setLanguage,
    setIncludeNsfw,
    setOnlyEnabled,
    resetFilters,
    toggleSelect,
    selectAll,
    deselectAll,
    updateProviderFromWs,
    initialize,
    reset,
  }
})

// ==========================================================================
//  Export du store
// ==========================================================================

export default useProvidersStore
