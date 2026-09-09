<!-- ==========================================================================
  NexusDL 2.0 - SettingsPanel Component
  Fichier : frontend/src/components/SettingsPanel.vue
  Description : Panneau de paramètres (préférences utilisateur, providers, système)
  Version : 2.0.0
========================================================================== -->

<template>
  <div class="nexus-settings-panel">
    <!-- En-tête -->
    <header class="nexus-settings-panel__header">
      <h2 class="nexus-settings-panel__title">
        <span aria-hidden="true">⚙️</span>
        Paramètres
      </h2>
      <span class="nexus-settings-panel__subtitle">
        Configurez votre expérience NexusDL
      </span>
    </header>

    <!-- Corps du panneau -->
    <div class="nexus-settings-panel__body">
      <!-- Navigation des sections (tabs) -->
      <nav class="nexus-settings-panel__nav" aria-label="Sections des paramètres">
        <button
          v-for="section in sections"
          :key="section.id"
          class="nexus-settings-panel__nav-btn"
          :class="{ 'nexus-settings-panel__nav-btn--active': activeSection === section.id }"
          @click="activeSection = section.id"
          :aria-current="activeSection === section.id ? 'page' : undefined"
        >
          <span class="nexus-settings-panel__nav-icon" aria-hidden="true">{{ section.icon }}</span>
          <span class="nexus-settings-panel__nav-label">{{ section.label }}</span>
        </button>
      </nav>

      <!-- Contenu des sections -->
      <div class="nexus-settings-panel__content">
        <Transition name="nexus-settings-fade" mode="out-in">
          <div :key="activeSection" class="nexus-settings-panel__section">
            <!-- Section : Profil -->
            <template v-if="activeSection === 'profile'">
              <section class="nexus-settings-panel__section-content">
                <h3 class="nexus-settings-panel__section-title">👤 Profil utilisateur</h3>
                <p class="nexus-settings-panel__section-desc">
                  Gérez vos informations personnelles et votre compte.
                </p>

                <NexusCard class="nexus-settings-panel__card">
                  <div class="nexus-settings-panel__profile-info">
                    <div class="nexus-settings-panel__avatar-section">
                      <div class="nexus-settings-panel__avatar">
                        {{ getInitials(user?.username || 'U') }}
                      </div>
                      <div class="nexus-settings-panel__avatar-actions">
                        <NexusButton size="sm" variant="neutral" @click="changeAvatar">
                          Changer
                        </NexusButton>
                        <NexusButton size="sm" variant="neutral" @click="removeAvatar">
                          Supprimer
                        </NexusButton>
                      </div>
                    </div>
                    <div class="nexus-settings-panel__profile-fields">
                      <NexusInput
                        v-model="profileForm.username"
                        label="Nom d'utilisateur"
                        placeholder="Votre nom d'utilisateur"
                        :disabled="!isEditingProfile"
                      />
                      <NexusInput
                        v-model="profileForm.email"
                        label="Email"
                        placeholder="votre@email.com"
                        type="email"
                        :disabled="!isEditingProfile"
                      />
                      <NexusInput
                        v-model="profileForm.fullName"
                        label="Nom complet"
                        placeholder="Votre nom complet"
                        :disabled="!isEditingProfile"
                      />
                    </div>
                  </div>
                  <div class="nexus-settings-panel__profile-actions">
                    <NexusButton
                      v-if="!isEditingProfile"
                      variant="primary"
                      @click="enableEditing"
                    >
                      ✏️ Modifier
                    </NexusButton>
                    <template v-else>
                      <NexusButton variant="success" :loading="savingProfile" @click="saveProfile">
                        💾 Sauvegarder
                      </NexusButton>
                      <NexusButton variant="neutral" @click="cancelEditing">
                        Annuler
                      </NexusButton>
                    </template>
                    <NexusButton
                      variant="error"
                      size="sm"
                      class="nexus-settings-panel__danger-btn"
                      @click="changePassword"
                    >
                      🔑 Changer le mot de passe
                    </NexusButton>
                  </div>
                </NexusCard>
              </section>
            </template>

            <!-- Section : Thème -->
            <template v-if="activeSection === 'theme'">
              <section class="nexus-settings-panel__section-content">
                <h3 class="nexus-settings-panel__section-title">🎨 Thème et apparence</h3>
                <p class="nexus-settings-panel__section-desc">
                  Personnalisez l'apparence de l'interface.
                </p>

                <NexusCard class="nexus-settings-panel__card">
                  <div class="nexus-settings-panel__theme-options">
                    <div
                      v-for="option in themeOptions"
                      :key="option.value"
                      class="nexus-settings-panel__theme-option"
                      :class="{
                        'nexus-settings-panel__theme-option--active': theme === option.value,
                      }"
                      @click="setTheme(option.value)"
                    >
                      <span class="nexus-settings-panel__theme-option-icon" aria-hidden="true">
                        {{ option.icon }}
                      </span>
                      <span class="nexus-settings-panel__theme-option-label">{{ option.label }}</span>
                    </div>
                  </div>
                  <div class="nexus-settings-panel__theme-preview">
                    <div class="nexus-settings-panel__theme-preview-bar">
                      <span class="nexus-settings-panel__theme-preview-text">Aperçu du thème</span>
                    </div>
                    <div class="nexus-settings-panel__theme-preview-colors">
                      <span class="nexus-settings-panel__theme-preview-color" style="background: var(--color-bg-primary);" />
                      <span class="nexus-settings-panel__theme-preview-color" style="background: var(--color-bg-card);" />
                      <span class="nexus-settings-panel__theme-preview-color" style="background: var(--color-primary);" />
                      <span class="nexus-settings-panel__theme-preview-color" style="background: var(--color-text-primary);" />
                    </div>
                  </div>
                </NexusCard>
              </section>
            </template>

            <!-- Section : Téléchargements -->
            <template v-if="activeSection === 'downloads'">
              <section class="nexus-settings-panel__section-content">
                <h3 class="nexus-settings-panel__section-title">⬇️ Téléchargements</h3>
                <p class="nexus-settings-panel__section-desc">
                  Configurez les paramètres de téléchargement.
                </p>

                <NexusCard class="nexus-settings-panel__card">
                  <div class="nexus-settings-panel__setting">
                    <div class="nexus-settings-panel__setting-info">
                      <span class="nexus-settings-panel__setting-label">Threads parallèles</span>
                      <span class="nexus-settings-panel__setting-desc">
                        Nombre maximum de téléchargements simultanés
                      </span>
                    </div>
                    <NexusSelect
                      v-model="downloadSettings.maxThreads"
                      :options="threadOptions"
                      size="sm"
                      style="min-width: 100px; max-width: 150px;"
                    />
                  </div>

                  <div class="nexus-settings-panel__setting">
                    <div class="nexus-settings-panel__setting-info">
                      <span class="nexus-settings-panel__setting-label">Timeout (secondes)</span>
                      <span class="nexus-settings-panel__setting-desc">
                        Délai d'attente maximum par requête
                      </span>
                    </div>
                    <NexusInput
                      v-model.number="downloadSettings.timeout"
                      type="number"
                      size="sm"
                      min="5"
                      max="120"
                      style="width: 80px;"
                    />
                  </div>

                  <div class="nexus-settings-panel__setting">
                    <div class="nexus-settings-panel__setting-info">
                      <span class="nexus-settings-panel__setting-label">Dossier de téléchargement</span>
                      <span class="nexus-settings-panel__setting-desc">
                        Chemin où sauvegarder les fichiers CBZ
                      </span>
                    </div>
                    <div class="nexus-settings-panel__setting-path">
                      <NexusInput
                        v-model="downloadSettings.downloadPath"
                        size="sm"
                        style="flex: 1; min-width: 150px;"
                        placeholder="./data/downloads"
                      />
                      <NexusButton size="sm" variant="neutral" @click="browseFolder">
                        📁 Parcourir
                      </NexusButton>
                    </div>
                  </div>

                  <div class="nexus-settings-panel__setting">
                    <div class="nexus-settings-panel__setting-info">
                      <span class="nexus-settings-panel__setting-label">Format de sortie</span>
                      <span class="nexus-settings-panel__setting-desc">
                        Format du fichier généré (CBZ recommandé)
                      </span>
                    </div>
                    <NexusSelect
                      v-model="downloadSettings.format"
                      :options="formatOptions"
                      size="sm"
                      style="min-width: 100px; max-width: 150px;"
                    />
                  </div>
                </NexusCard>

                <div class="nexus-settings-panel__actions">
                  <NexusButton variant="primary" :loading="savingDownloadSettings" @click="saveDownloadSettings">
                    💾 Sauvegarder
                  </NexusButton>
                  <NexusButton variant="neutral" @click="resetDownloadSettings">
                    ↺ Réinitialiser
                  </NexusButton>
                </div>
              </section>
            </template>

            <!-- Section : Providers -->
            <template v-if="activeSection === 'providers'">
              <section class="nexus-settings-panel__section-content">
                <h3 class="nexus-settings-panel__section-title">🌐 Providers</h3>
                <p class="nexus-settings-panel__section-desc">
                  Activez ou désactivez les sites de scan (les providers désactivés ne seront pas utilisés).
                </p>

                <div class="nexus-settings-panel__providers-toolbar">
                  <NexusInput
                    v-model="providerSearch"
                    placeholder="Rechercher un provider..."
                    size="sm"
                    left-icon="🔍"
                    style="max-width: 250px;"
                  />
                  <div class="nexus-settings-panel__providers-filters">
                    <NexusButton
                      size="sm"
                      variant="neutral"
                      :class="{ 'nexus-settings-panel__filter-btn--active': providerFilter === 'all' }"
                      @click="providerFilter = 'all'"
                    >
                      Tous
                    </NexusButton>
                    <NexusButton
                      size="sm"
                      variant="neutral"
                      :class="{ 'nexus-settings-panel__filter-btn--active': providerFilter === 'enabled' }"
                      @click="providerFilter = 'enabled'"
                    >
                      ✅ Activés
                    </NexusButton>
                    <NexusButton
                      size="sm"
                      variant="neutral"
                      :class="{ 'nexus-settings-panel__filter-btn--active': providerFilter === 'disabled' }"
                      @click="providerFilter = 'disabled'"
                    >
                      ❌ Désactivés
                    </NexusButton>
                    <NexusButton
                      size="sm"
                      variant="neutral"
                      :class="{ 'nexus-settings-panel__filter-btn--active': providerFilter === 'nsfw' }"
                      @click="providerFilter = 'nsfw'"
                    >
                      🔞 NSFW
                    </NexusButton>
                  </div>
                </div>

                <div class="nexus-settings-panel__providers-list">
                  <div
                    v-for="provider in filteredProviders"
                    :key="provider.id"
                    class="nexus-settings-panel__provider-item"
                  >
                    <div class="nexus-settings-panel__provider-info">
                      <span class="nexus-settings-panel__provider-name">{{ provider.name }}</span>
                      <span class="nexus-settings-panel__provider-url">{{ provider.base_url }}</span>
                      <span v-if="provider.nsfw" class="nexus-settings-panel__provider-badge nsfw">🔞 NSFW</span>
                      <span class="nexus-settings-panel__provider-languages">
                        {{ (provider.languages || []).join(', ') }}
                      </span>
                    </div>
                    <div class="nexus-settings-panel__provider-status">
                      <span class="nexus-settings-panel__provider-version">v{{ provider.version }}</span>
                      <label class="nexus-settings-panel__toggle">
                        <input
                          type="checkbox"
                          :checked="provider.enabled"
                          @change="toggleProvider(provider.id, $event.target.checked)"
                        />
                        <span class="nexus-settings-panel__toggle-slider" />
                      </label>
                    </div>
                  </div>
                </div>
              </section>
            </template>

            <!-- Section : Cache -->
            <template v-if="activeSection === 'cache'">
              <section class="nexus-settings-panel__section-content">
                <h3 class="nexus-settings-panel__section-title">🗄️ Cache</h3>
                <p class="nexus-settings-panel__section-desc">
                  Gérez le cache des pages et des images pour améliorer les performances.
                </p>

                <NexusCard class="nexus-settings-panel__card">
                  <div class="nexus-settings-panel__setting">
                    <div class="nexus-settings-panel__setting-info">
                      <span class="nexus-settings-panel__setting-label">Cache activé</span>
                      <span class="nexus-settings-panel__setting-desc">
                        Mettre en cache les pages et images
                      </span>
                    </div>
                    <label class="nexus-settings-panel__toggle">
                      <input
                        type="checkbox"
                        v-model="cacheSettings.enabled"
                      />
                      <span class="nexus-settings-panel__toggle-slider" />
                    </label>
                  </div>

                  <div class="nexus-settings-panel__setting">
                    <div class="nexus-settings-panel__setting-info">
                      <span class="nexus-settings-panel__setting-label">Taille max du cache</span>
                      <span class="nexus-settings-panel__setting-desc">
                        Nombre maximum d'entrées en mémoire
                      </span>
                    </div>
                    <NexusSelect
                      v-model="cacheSettings.maxSize"
                      :options="cacheSizeOptions"
                      size="sm"
                      style="min-width: 100px; max-width: 150px;"
                    />
                  </div>

                  <div class="nexus-settings-panel__setting">
                    <div class="nexus-settings-panel__setting-info">
                      <span class="nexus-settings-panel__setting-label">TTL (secondes)</span>
                      <span class="nexus-settings-panel__setting-desc">
                        Durée de vie des entrées du cache
                      </span>
                    </div>
                    <NexusInput
                      v-model.number="cacheSettings.ttl"
                      type="number"
                      size="sm"
                      min="60"
                      max="86400"
                      style="width: 100px;"
                    />
                  </div>
                </NexusCard>

                <div class="nexus-settings-panel__cache-actions">
                  <NexusButton variant="warning" @click="clearCache">
                    🗑️ Vider le cache
                  </NexusButton>
                  <NexusButton variant="primary" :loading="savingCache" @click="saveCacheSettings">
                    💾 Sauvegarder
                  </NexusButton>
                </div>
              </section>
            </template>

            <!-- Section : À propos -->
            <template v-if="activeSection === 'about'">
              <section class="nexus-settings-panel__section-content">
                <h3 class="nexus-settings-panel__section-title">📄 À propos</h3>
                <p class="nexus-settings-panel__section-desc">
                  Informations sur NexusDL et les technologies utilisées.
                </p>

                <NexusCard class="nexus-settings-panel__card nexus-settings-panel__about-card">
                  <div class="nexus-settings-panel__about-logo">
                    <svg
                      class="nexus-settings-panel__about-icon"
                      viewBox="0 0 512 512"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <circle cx="256" cy="256" r="200" fill="url(#aboutGrad)" />
                      <defs>
                        <linearGradient id="aboutGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" style="stop-color:#00d4ff;stop-opacity:1" />
                          <stop offset="100%" style="stop-color:#0066ff;stop-opacity:1" />
                        </linearGradient>
                      </defs>
                      <text
                        x="256"
                        y="290"
                        font-family="system-ui, -apple-system, sans-serif"
                        font-size="200"
                        font-weight="bold"
                        text-anchor="middle"
                        fill="white"
                        dominant-baseline="central"
                      >
                        N
                      </text>
                    </svg>
                    <h4 class="nexus-settings-panel__about-name">NexusDL {{ appVersion }}</h4>
                    <span class="nexus-settings-panel__about-tagline">
                      Moteur universel de téléchargement de scans
                    </span>
                  </div>
                  <div class="nexus-settings-panel__about-info">
                    <div class="nexus-settings-panel__about-row">
                      <span class="nexus-settings-panel__about-label">Version</span>
                      <span class="nexus-settings-panel__about-value">{{ appVersion }}</span>
                    </div>
                    <div class="nexus-settings-panel__about-row">
                      <span class="nexus-settings-panel__about-label">Licence</span>
                      <span class="nexus-settings-panel__about-value">GNU GPL v3.0</span>
                    </div>
                    <div class="nexus-settings-panel__about-row">
                      <span class="nexus-settings-panel__about-label">Backend</span>
                      <span class="nexus-settings-panel__about-value">FastAPI</span>
                    </div>
                    <div class="nexus-settings-panel__about-row">
                      <span class="nexus-settings-panel__about-label">Frontend</span>
                      <span class="nexus-settings-panel__about-value">Vue.js 3</span>
                    </div>
                    <div class="nexus-settings-panel__about-row">
                      <span class="nexus-settings-panel__about-label">Built</span>
                      <span class="nexus-settings-panel__about-value">{{ buildDate }}</span>
                    </div>
                  </div>
                  <div class="nexus-settings-panel__about-links">
                    <a href="#" target="_blank" class="nexus-settings-panel__about-link">
                      📖 Documentation
                    </a>
                    <a href="#" target="_blank" class="nexus-settings-panel__about-link">
                      🐛 Signaler un bug
                    </a>
                    <a href="#" target="_blank" class="nexus-settings-panel__about-link">
                      💬 Discord
                    </a>
                  </div>
                </NexusCard>
              </section>
            </template>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Footer avec sauvegarde globale -->
    <footer class="nexus-settings-panel__footer">
      <span class="nexus-settings-panel__footer-status">
        {{ saveStatus }}
      </span>
      <NexusButton variant="primary" size="sm" @click="saveAllSettings">
        💾 Sauvegarder tout
      </NexusButton>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted } from 'vue'
import NexusButton from './common/NexusButton.vue'
import NexusInput from './common/NexusInput.vue'
import NexusSelect from './common/NexusSelect.vue'
import NexusCard from './common/NexusCard.vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useProvidersStore } from '@/stores/providers'
import { useTheme } from '@/composables/useTheme'
import { useToast } from '@/composables/useToast'
import { useApi } from '@/composables/useApi'
import { formatDate } from '@/utils/formatters'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const appStore = useAppStore()
const authStore = useAuthStore()
const providersStore = useProvidersStore()
const { currentTheme, setTheme } = useTheme()
const toast = useToast()
const api = useApi()

// ==========================================================================
//  État
// ==========================================================================

const activeSection = ref('profile')
const isEditingProfile = ref(false)
const savingProfile = ref(false)
const savingDownloadSettings = ref(false)
const savingCache = ref(false)
const saveStatus = ref('Prêt')
const providerSearch = ref('')
const providerFilter = ref('all')

// ==========================================================================
//  Formulaires
// ==========================================================================

const profileForm = reactive({
  username: '',
  email: '',
  fullName: '',
})

const downloadSettings = reactive({
  maxThreads: 10,
  timeout: 30,
  downloadPath: './data/downloads',
  format: 'cbz',
})

const cacheSettings = reactive({
  enabled: true,
  maxSize: 500,
  ttl: 3600,
})

// ==========================================================================
//  Sections
// ==========================================================================

const sections = [
  { id: 'profile', label: 'Profil', icon: '👤' },
  { id: 'theme', label: 'Thème', icon: '🎨' },
  { id: 'downloads', label: 'Téléchargements', icon: '⬇️' },
  { id: 'providers', label: 'Providers', icon: '🌐' },
  { id: 'cache', label: 'Cache', icon: '🗄️' },
  { id: 'about', label: 'À propos', icon: '📄' },
]

// ==========================================================================
//  Options
// ==========================================================================

const themeOptions = [
  { value: 'dark', label: 'Sombre', icon: '🌙' },
  { value: 'light', label: 'Clair', icon: '☀️' },
  { value: 'system', label: 'Système', icon: '🖥️' },
]

const threadOptions = [
  { value: 2, label: '2' },
  { value: 4, label: '4' },
  { value: 8, label: '8' },
  { value: 10, label: '10' },
  { value: 16, label: '16' },
  { value: 20, label: '20' },
]

const formatOptions = [
  { value: 'cbz', label: 'CBZ' },
  { value: 'zip', label: 'ZIP' },
  { value: 'pdf', label: 'PDF' },
]

const cacheSizeOptions = [
  { value: 100, label: '100' },
  { value: 300, label: '300' },
  { value: 500, label: '500' },
  { value: 1000, label: '1000' },
  { value: 2000, label: '2000' },
]

// ==========================================================================
//  Computed
// ==========================================================================

const user = computed(() => authStore.user)
const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')
const buildDate = computed(() => import.meta.env.VITE_BUILD_DATE || new Date().toISOString())
const theme = computed(() => currentTheme.value)

const providers = computed(() => providersStore.providerList)

const filteredProviders = computed(() => {
  let result = providers.value
  // Recherche
  if (providerSearch.value) {
    const q = providerSearch.value.toLowerCase()
    result = result.filter(p =>
      p.name.toLowerCase().includes(q) ||
      p.id.toLowerCase().includes(q) ||
      (p.description && p.description.toLowerCase().includes(q))
    )
  }
  // Filtres
  if (providerFilter.value === 'enabled') {
    result = result.filter(p => p.enabled)
  } else if (providerFilter.value === 'disabled') {
    result = result.filter(p => !p.enabled)
  } else if (providerFilter.value === 'nsfw') {
    result = result.filter(p => p.nsfw)
  }
  return result
})

// ==========================================================================
  //  Méthodes
// ==========================================================================

// --- Profil ---
function getInitials(name) {
  return name ? name.charAt(0).toUpperCase() : '?'
}

function enableEditing() {
  profileForm.username = user.value?.username || ''
  profileForm.email = user.value?.email || ''
  profileForm.fullName = user.value?.full_name || ''
  isEditingProfile.value = true
}

function cancelEditing() {
  isEditingProfile.value = false
}

async function saveProfile() {
  savingProfile.value = true
  saveStatus.value = 'Sauvegarde du profil...'
  try {
    // Appel API pour mettre à jour le profil
    await api.put('/auth/profile', profileForm)
    // Mettre à jour le store
    if (authStore.user) {
      authStore.user.username = profileForm.username
      authStore.user.email = profileForm.email
      authStore.user.full_name = profileForm.fullName
      authStore.persistAuth()
    }
    toast.success('Profil mis à jour.', '✅')
    isEditingProfile.value = false
    saveStatus.value = 'Profil sauvegardé'
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
    saveStatus.value = 'Erreur'
  } finally {
    savingProfile.value = false
  }
}

function changeAvatar() {
  toast.info('Fonctionnalité à venir.', 'ℹ️')
}

function removeAvatar() {
  toast.info('Fonctionnalité à venir.', 'ℹ️')
}

function changePassword() {
  toast.info('Fonctionnalité à venir.', 'ℹ️')
}

// --- Thème ---
function setTheme(themeValue) {
  setTheme(themeValue)
  toast.info(`Thème changé : ${themeOptions.find(t => t.value === themeValue)?.label}`, '🎨')
}

// --- Téléchargements ---
async function saveDownloadSettings() {
  savingDownloadSettings.value = true
  saveStatus.value = 'Sauvegarde des paramètres de téléchargement...'
  try {
    await api.post('/settings/downloads', downloadSettings)
    toast.success('Paramètres de téléchargement sauvegardés.', '✅')
    saveStatus.value = 'Sauvegardé'
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
    saveStatus.value = 'Erreur'
  } finally {
    savingDownloadSettings.value = false
  }
}

function resetDownloadSettings() {
  downloadSettings.maxThreads = 10
  downloadSettings.timeout = 30
  downloadSettings.downloadPath = './data/downloads'
  downloadSettings.format = 'cbz'
  toast.info('Paramètres réinitialisés.', '🔄')
}

function browseFolder() {
  toast.info('Fonctionnalité à venir.', 'ℹ️')
}

// --- Providers ---
async function toggleProvider(providerId, enabled) {
  try {
    await providersStore.toggleProvider(providerId, enabled)
    toast.info(`Provider ${enabled ? 'activé' : 'désactivé'}`, '🔧')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

// --- Cache ---
async function clearCache() {
  if (!confirm('Vider le cache ? Cette action est irréversible.')) return
  try {
    await api.delete('/admin/cache')
    toast.success('Cache vidé.', '🗑️')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

async function saveCacheSettings() {
  savingCache.value = true
  saveStatus.value = 'Sauvegarde des paramètres de cache...'
  try {
    await api.post('/settings/cache', cacheSettings)
    toast.success('Paramètres de cache sauvegardés.', '✅')
    saveStatus.value = 'Sauvegardé'
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
    saveStatus.value = 'Erreur'
  } finally {
    savingCache.value = false
  }
}

// --- Sauvegarde globale ---
async function saveAllSettings() {
  saveStatus.value = 'Sauvegarde de tous les paramètres...'
  try {
    await Promise.all([
      saveProfile(),
      saveDownloadSettings(),
      saveCacheSettings(),
    ])
    toast.success('Tous les paramètres ont été sauvegardés.', '✅')
    saveStatus.value = 'Tout sauvegardé'
  } catch (err) {
    toast.error(`Erreur lors de la sauvegarde : ${err.message}`, '❌')
    saveStatus.value = 'Erreur'
  }
}

// ==========================================================================
//  Initialisation
// ==========================================================================

onMounted(() => {
  // Charger les paramètres depuis l'API
  // Simuler un chargement : on remplit avec les valeurs par défaut ou stockées
  // Récupérer les providers
  providersStore.initialize({ load: true })
  // Si utilisateur connecté, remplir le profil
  if (authStore.isAuthenticated && authStore.user) {
    profileForm.username = authStore.user.username || ''
    profileForm.email = authStore.user.email || ''
    profileForm.fullName = authStore.user.full_name || ''
  }
  // Charger les préférences depuis le localStorage
  const saved = localStorage.getItem('nexus-settings')
  if (saved) {
    try {
      const data = JSON.parse(saved)
      if (data.downloads) Object.assign(downloadSettings, data.downloads)
      if (data.cache) Object.assign(cacheSettings, data.cache)
    } catch (_) {}
  }
})

// Watcher pour persister les paramètres localement
watch(
  [downloadSettings, cacheSettings],
  () => {
    localStorage.setItem('nexus-settings', JSON.stringify({
      downloads: downloadSettings,
      cache: cacheSettings,
    }))
  },
  { deep: true }
)

// ==========================================================================
//  Exposer
// ==========================================================================

defineExpose({
  activeSection,
  refreshLibraryStats: () => { /* le parent peut appeler */ },
})

// ==========================================================================
//  Styles
// ==========================================================================

</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$settings-radius: var(--radius-lg, 12px);
$settings-transition: all var(--transition-base, 300ms) ease;

// ==========================================================================
//  Conteneur principal
// ==========================================================================

.nexus-settings-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
  max-width: 100%;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: $settings-radius;
  padding: 1rem;
  min-height: 400px;
}

// ==========================================================================
//  Header
// ==========================================================================

.nexus-settings-panel__header {
  border-bottom: 1px solid var(--color-border, #1a2538);
  padding-bottom: 0.5rem;
}

.nexus-settings-panel__title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.nexus-settings-panel__subtitle {
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
  //  Body
// ==========================================================================

.nexus-settings-panel__body {
  display: flex;
  gap: 1rem;
  flex: 1;
  min-height: 300px;
}

// ==========================================================================
  //  Navigation
// ==========================================================================

.nexus-settings-panel__nav {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 0 0 160px;
  border-right: 1px solid var(--color-border, #1a2538);
  padding-right: 0.5rem;
}

.nexus-settings-panel__nav-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  transition: $settings-transition;
  font-size: 0.85rem;
  text-align: left;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &--active {
    background: rgba(0, 212, 255, 0.08);
    color: var(--color-primary, #00d4ff);
    font-weight: var(--font-weight-medium, 500);
    &:hover {
      background: rgba(0, 212, 255, 0.12);
    }
  }
}

.nexus-settings-panel__nav-icon {
  font-size: 1rem;
}

.nexus-settings-panel__nav-label {
  font-size: 0.85rem;
}

// ==========================================================================
//  Content
// ==========================================================================

.nexus-settings-panel__content {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 0.25rem 0.5rem 0.25rem 0.75rem;
  max-height: 600px;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: var(--color-bg-secondary, #141a2b);
    border-radius: 3px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
    border-radius: 3px;
    &:hover {
      background: var(--color-text-muted, #6a7a9a);
    }
  }
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) var(--color-bg-secondary);
}

// ==========================================================================
//  Section
// ==========================================================================

.nexus-settings-panel__section {
  animation: fadeIn 0.25s ease;
}

.nexus-settings-panel__section-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.nexus-settings-panel__section-title {
  margin: 0;
  font-size: 1rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
}

.nexus-settings-panel__section-desc {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Cards
// ==========================================================================

.nexus-settings-panel__card {
  padding: 1rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

// ==========================================================================
//  Profil
// ==========================================================================

.nexus-settings-panel__profile-info {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.nexus-settings-panel__avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
}

.nexus-settings-panel__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: var(--color-primary, #00d4ff);
  border-radius: var(--radius-full, 9999px);
  font-size: 1.8rem;
  font-weight: var(--font-weight-bold, 700);
  color: var(--color-text-inverse, #0a0e1a);
}

.nexus-settings-panel__avatar-actions {
  display: flex;
  gap: 0.3rem;
}

.nexus-settings-panel__profile-fields {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 200px;
}

.nexus-settings-panel__profile-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
  padding-top: 0.75rem;
}

.nexus-settings-panel__danger-btn {
  margin-left: auto;
}

// ==========================================================================
//  Thème
// ==========================================================================

.nexus-settings-panel__theme-options {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.nexus-settings-panel__theme-option {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.8rem;
  background: var(--color-bg-card, #1a2538);
  border: 2px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: $settings-transition;
  font-size: 0.85rem;
  color: var(--color-text-secondary, #b0c0d8);

  &:hover {
    border-color: var(--color-primary, #00d4ff);
  }

  &--active {
    border-color: var(--color-primary, #00d4ff);
    background: rgba(0, 212, 255, 0.08);
    color: var(--color-text-primary, #e8edf5);
  }
}

.nexus-settings-panel__theme-option-icon {
  font-size: 1.2rem;
}

.nexus-settings-panel__theme-option-label {
  font-weight: var(--font-weight-medium, 500);
}

.nexus-settings-panel__theme-preview {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: var(--color-bg-card, #1a2538);
  border-radius: var(--radius-sm, 4px);
  border: 1px solid var(--color-border, #1a2538);
}

.nexus-settings-panel__theme-preview-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-sm, 4px);
  margin-bottom: 0.3rem;
}

.nexus-settings-panel__theme-preview-text {
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-settings-panel__theme-preview-colors {
  display: flex;
  gap: 0.3rem;
}

.nexus-settings-panel__theme-preview-color {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm, 4px);
  border: 1px solid var(--color-border, #1a2538);
}

// ==========================================================================
//  Paramètres (setting)
// ==========================================================================

.nexus-settings-panel__setting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.3rem 0;
  border-bottom: 1px solid var(--color-border, #1a2538);

  &:last-child {
    border-bottom: none;
  }
}

.nexus-settings-panel__setting-info {
  flex: 1;
  min-width: 0;
}

.nexus-settings-panel__setting-label {
  display: block;
  font-weight: var(--font-weight-medium, 500);
  color: var(--color-text-primary, #e8edf5);
  font-size: 0.9rem;
}

.nexus-settings-panel__setting-desc {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-settings-panel__setting-path {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex: 1;
  max-width: 400px;
}

// ==========================================================================
//  Toggle (switch)
// ==========================================================================

.nexus-settings-panel__toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;

  input {
    opacity: 0;
    width: 0;
    height: 0;
    &:checked + .nexus-settings-panel__toggle-slider {
      background: var(--color-primary, #00d4ff);
      &::before {
        transform: translateX(20px);
        background: white;
      }
    }
    &:disabled + .nexus-settings-panel__toggle-slider {
      opacity: 0.4;
      cursor: not-allowed;
    }
  }
}

.nexus-settings-panel__toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-bg-input, #1e2a40);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-full, 9999px);
  transition: $settings-transition;

  &::before {
    content: '';
    position: absolute;
    height: 18px;
    width: 18px;
    left: 2px;
    bottom: 2px;
    background: var(--color-text-muted, #6a7a9a);
    border-radius: 50%;
    transition: $settings-transition;
  }
}

// ==========================================================================
//  Providers
// ==========================================================================

.nexus-settings-panel__providers-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.nexus-settings-panel__providers-filters {
  display: flex;
  gap: 0.2rem;
  flex-wrap: wrap;
}

.nexus-settings-panel__filter-btn--active {
  border-color: var(--color-primary, #00d4ff);
  color: var(--color-primary, #00d4ff);
}

.nexus-settings-panel__providers-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  max-height: 350px;
  overflow-y: auto;
  padding-right: 0.25rem;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-track {
    background: var(--color-bg-secondary, #141a2b);
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
    border-radius: 2px;
  }
}

.nexus-settings-panel__provider-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.3rem 0.5rem;
  background: var(--color-bg-card, #1a2538);
  border-radius: var(--radius-sm, 4px);
  border: 1px solid var(--color-border, #1a2538);
  transition: $settings-transition;

  &:hover {
    border-color: var(--color-border-light, #253254);
  }
}

.nexus-settings-panel__provider-info {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  flex: 1;
}

.nexus-settings-panel__provider-name {
  font-weight: var(--font-weight-medium, 500);
  color: var(--color-text-primary, #e8edf5);
}

.nexus-settings-panel__provider-url {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  word-break: break-all;
}

.nexus-settings-panel__provider-badge {
  font-size: 0.6rem;
  padding: 0.05rem 0.4rem;
  border-radius: var(--radius-sm, 4px);
  background: var(--color-warning, #ff9800);
  color: var(--color-text-inverse, #0a0e1a);
  &.nsfw {
    background: var(--color-error, #f44336);
    color: var(--color-text-inverse, #ffffff);
  }
}

.nexus-settings-panel__provider-languages {
  font-size: 0.6rem;
  color: var(--color-text-muted, #6a7a9a);
  text-transform: uppercase;
}

.nexus-settings-panel__provider-status {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.nexus-settings-panel__provider-version {
  font-size: 0.6rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Cache actions
// ==========================================================================

.nexus-settings-panel__cache-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

// ==========================================================================
//  À propos
// ==========================================================================

.nexus-settings-panel__about-card {
  align-items: center;
  text-align: center;
  gap: 1rem;
}

.nexus-settings-panel__about-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
}

.nexus-settings-panel__about-icon {
  width: 80px;
  height: 80px;
}

.nexus-settings-panel__about-name {
  margin: 0;
  font-size: 1.3rem;
  font-weight: var(--font-weight-bold, 700);
  color: var(--color-text-primary, #e8edf5);
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nexus-settings-panel__about-tagline {
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-settings-panel__about-info {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  text-align: left;
  padding: 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-sm, 4px);
}

.nexus-settings-panel__about-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  padding: 0.1rem 0;
}

.nexus-settings-panel__about-label {
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-settings-panel__about-value {
  color: var(--color-text-secondary, #b0c0d8);
}

.nexus-settings-panel__about-links {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
}

.nexus-settings-panel__about-link {
  font-size: 0.8rem;
  color: var(--color-primary, #00d4ff);
  text-decoration: none;
  padding: 0.2rem 0.5rem;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  transition: $settings-transition;
  &:hover {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-primary, #00d4ff);
  }
}

// ==========================================================================
//  Actions
// ==========================================================================

.nexus-settings-panel__actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 0.5rem;
}

// ==========================================================================
//  Footer
// ==========================================================================

.nexus-settings-panel__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border, #1a2538);
  gap: 0.5rem;
}

.nexus-settings-panel__footer-status {
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
  font-style: italic;
}

// ==========================================================================
//  Animations
// ==========================================================================

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.nexus-settings-fade-enter-active,
.nexus-settings-fade-leave-active {
  transition: all 0.2s ease;
}

.nexus-settings-fade-enter-from,
.nexus-settings-fade-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 768px) {
  .nexus-settings-panel__body {
    flex-direction: column;
  }
  .nexus-settings-panel__nav {
    flex: none;
    flex-direction: row;
    flex-wrap: wrap;
    border-right: none;
    border-bottom: 1px solid var(--color-border, #1a2538);
    padding-right: 0;
    padding-bottom: 0.5rem;
    gap: 0.2rem;
  }
  .nexus-settings-panel__nav-btn {
    flex: 1 1 auto;
    justify-content: center;
    padding: 0.3rem 0.6rem;
  }
  .nexus-settings-panel__content {
    padding-left: 0;
    max-height: 400px;
  }
  .nexus-settings-panel__profile-info {
    flex-direction: column;
    align-items: center;
  }
  .nexus-settings-panel__profile-fields {
    width: 100%;
  }
  .nexus-settings-panel__profile-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .nexus-settings-panel__danger-btn {
    margin-left: 0;
  }
  .nexus-settings-panel__setting {
    flex-direction: column;
    align-items: stretch;
    gap: 0.3rem;
  }
  .nexus-settings-panel__setting-path {
    max-width: 100%;
  }
  .nexus-settings-panel__providers-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .nexus-settings-panel__provider-item {
    flex-wrap: wrap;
    gap: 0.3rem;
  }
  .nexus-settings-panel__provider-info {
    flex-wrap: wrap;
  }
  .nexus-settings-panel__footer {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 480px) {
  .nexus-settings-panel {
    padding: 0.5rem;
  }
  .nexus-settings-panel__nav-btn {
    font-size: 0.75rem;
  }
  .nexus-settings-panel__theme-option {
    font-size: 0.75rem;
    padding: 0.2rem 0.5rem;
  }
}

// ==========================================================================
//  Support du thème clair
// ==========================================================================

.light-mode {
  .nexus-settings-panel {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-settings-panel__header {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-settings-panel__title {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-settings-panel__subtitle {
    color: var(--color-text-muted, #7a8a9a);
  }
  .nexus-settings-panel__nav {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-settings-panel__nav-btn {
    color: var(--color-text-secondary, #3d4a5c);
    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
      color: var(--color-text-primary, #1a1a2e);
    }
    &--active {
      background: rgba(0, 102, 204, 0.05);
      color: var(--color-primary, #0066cc);
      &:hover {
        background: rgba(0, 102, 204, 0.08);
      }
    }
  }
  .nexus-settings-panel__section-title {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-settings-panel__section-desc {
    color: var(--color-text-muted, #7a8a9a);
  }
  .nexus-settings-panel__card {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-settings-panel__setting {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-settings-panel__setting-label {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-settings-panel__setting-desc {
    color: var(--color-text-muted, #7a8a9a);
  }
  .nexus-settings-panel__theme-option {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    color: var(--color-text-secondary, #3d4a5c);
    &:hover {
      border-color: var(--color-primary, #0066cc);
    }
    &--active {
      border-color: var(--color-primary, #0066cc);
      background: rgba(0, 102, 204, 0.05);
      color: var(--color-text-primary, #1a1a2e);
    }
  }
  .nexus-settings-panel__theme-preview {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-settings-panel__theme-preview-bar {
    background: var(--color-bg-secondary, #e9ecf2);
  }
  .nexus-settings-panel__theme-preview-color {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-settings-panel__toggle-slider {
    background: var(--color-bg-input, #f0f2f5);
    border-color: var(--color-border, #d0d8e0);
    &::before {
      background: var(--color-text-muted, #7a8a9a);
    }
  }
  .nexus-settings-panel__toggle input:checked + .nexus-settings-panel__toggle-slider {
    background: var(--color-primary, #0066cc);
  }
  .nexus-settings-panel__provider-item {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    &:hover {
      border-color: var(--color-border-light, #e3e8ef);
    }
  }
  .nexus-settings-panel__provider-name {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-settings-panel__provider-url {
    color: var(--color-text-muted, #7a8a9a);
  }
  .nexus-settings-panel__about-info {
    background: var(--color-bg-secondary, #e9ecf2);
  }
  .nexus-settings-panel__about-row {
    color: var(--color-text-secondary, #3d4a5c);
  }
  .nexus-settings-panel__about-label {
    color: var(--color-text-muted, #7a8a9a);
  }
  .nexus-settings-panel__about-value {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-settings-panel__about-link {
    color: var(--color-primary, #0066cc);
    border-color: var(--color-border, #d0d8e0);
    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
      border-color: var(--color-primary, #0066cc);
    }
  }
  .nexus-settings-panel__footer {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-settings-panel__footer-status {
    color: var(--color-text-muted, #7a8a9a);
  }
  .nexus-settings-panel__avatar {
    background: var(--color-primary, #0066cc);
    color: var(--color-text-inverse, #ffffff);
  }
  .nexus-settings-panel__profile-actions {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-settings-panel__provider-badge {
    &.nsfw {
      background: var(--color-error, #c62828);
    }
  }
}
</style>
