<!-- ==========================================================================
  NexusDL 2.0 - Settings View (version complète)
  Fichier : frontend/src/views/SettingsView.vue
  Description : Page de paramètres complète de NexusDL. Organisée en sections :
                Général, Apparence, Téléchargements, Providers, Cache, Système,
                Notifications, Confidentialité, À propos. Avec gestion du
                thème, préférences utilisateur, configuration système, et
                sauvegarde persistante.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="settings-view">
    <!-- ====================================================================
      EN-TÊTE
    ==================================================================== -->
    <header class="settings-view__header">
      <div class="settings-view__header-left">
        <h1 class="settings-view__title">
          <span aria-hidden="true">⚙️</span>
          Paramètres
        </h1>
        <p class="settings-view__subtitle">
          Configurez votre expérience NexusDL
        </p>
      </div>

      <div class="settings-view__header-right">
        <!-- Indicateur de modifications -->
        <div
          v-if="hasUnsavedChanges"
          class="settings-view__unsaved-badge"
          role="status"
          aria-live="polite"
        >
          <span aria-hidden="true">●</span>
          Modifications non enregistrées
        </div>

        <!-- Bouton réinitialiser -->
        <button
          type="button"
          class="settings-view__btn settings-view__btn--reset"
          :disabled="!hasUnsavedChanges || saving"
          @click="confirmReset"
          aria-label="Réinitialiser les modifications"
          title="Réinitialiser"
        >
          <span aria-hidden="true">↺</span>
          Réinitialiser
        </button>

        <!-- Bouton sauvegarder -->
        <button
          type="button"
          class="settings-view__btn settings-view__btn--save"
          :disabled="!hasUnsavedChanges || saving"
          @click="saveAllSettings"
          :aria-label="saving ? 'Sauvegarde en cours' : 'Sauvegarder les modifications'"
          :title="saving ? 'Sauvegarde...' : 'Sauvegarder'"
        >
          <span v-if="saving" class="settings-view__spinner" aria-hidden="true">⟳</span>
          <span v-else aria-hidden="true">💾</span>
          {{ saving ? 'Sauvegarde...' : 'Sauvegarder' }}
        </button>
      </div>
    </header>

    <!-- ====================================================================
      MESSAGE DE SUCCÈS
    ==================================================================== -->
    <Transition name="settings-view-fade">
      <div
        v-if="successMessage"
        class="settings-view__success"
        role="status"
        aria-live="polite"
      >
        <span class="settings-view__success-icon" aria-hidden="true">✅</span>
        <span class="settings-view__success-text">{{ successMessage }}</span>
      </div>
    </Transition>

    <!-- ====================================================================
      BARRE D'ERREUR
    ==================================================================== -->
    <div v-if="error" class="settings-view__error" role="alert">
      <span class="settings-view__error-icon" aria-hidden="true">❌</span>
      <span class="settings-view__error-text">{{ error }}</span>
      <button
        type="button"
        class="settings-view__error-close"
        @click="error = null"
        aria-label="Fermer"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>

    <!-- ====================================================================
      LAYOUT PRINCIPAL — Sidebar + Contenu
    ==================================================================== -->
    <div class="settings-view__layout">
      <!-- ================================================================
        SIDEBAR — Navigation des sections
      ================================================================ -->
      <aside class="settings-view__sidebar">
        <nav class="settings-view__nav" aria-label="Sections des paramètres">
          <button
            v-for="section in sections"
            :key="section.id"
            type="button"
            class="settings-view__nav-item"
            :class="{ 'settings-view__nav-item--active': activeSection === section.id }"
            @click="activeSection = section.id"
            :aria-current="activeSection === section.id ? 'page' : undefined"
          >
            <span class="settings-view__nav-icon" aria-hidden="true">{{ section.icon }}</span>
            <div class="settings-view__nav-content">
              <span class="settings-view__nav-label">{{ section.label }}</span>
              <span class="settings-view__nav-desc">{{ section.description }}</span>
            </div>
            <span
              v-if="getSectionChanges(section.id) > 0"
              class="settings-view__nav-badge"
            >
              {{ getSectionChanges(section.id) }}
            </span>
          </button>
        </nav>

        <!-- Infos de version -->
        <div class="settings-view__sidebar-footer">
          <div class="settings-view__sidebar-footer-info">
            <span class="settings-view__sidebar-footer-label">Version</span>
            <span class="settings-view__sidebar-footer-value">v{{ appVersion }}</span>
          </div>
          <div class="settings-view__sidebar-footer-info">
            <span class="settings-view__sidebar-footer-label">Environnement</span>
            <span
              class="settings-view__sidebar-footer-value settings-view__sidebar-footer-value--env"
              :class="`settings-view__sidebar-footer-value--env-${environment}`"
            >
              {{ environment }}
            </span>
          </div>
        </div>
      </aside>

      <!-- ================================================================
        CONTENU PRINCIPAL
      ================================================================ -->
      <main class="settings-view__content">
        <Transition name="settings-view-section" mode="out-in">
          <!-- =========================================================
            SECTION 1 : Général
          ========================================================= -->
          <section
            v-if="activeSection === 'general'"
            key="general"
            class="settings-view__section"
          >
            <header class="settings-view__section-header">
              <h2 class="settings-view__section-title">
                <span aria-hidden="true">🎯</span>
                Général
              </h2>
              <p class="settings-view__section-desc">
                Paramètres généraux de l'application
              </p>
            </header>

            <!-- Langue -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-language" class="settings-view__setting-label">
                  Langue de l'interface
                </label>
                <p class="settings-view__setting-desc">
                  Langue utilisée pour l'affichage et les recherches
                </p>
              </div>
              <div class="settings-view__setting-control">
                <select
                  id="setting-language"
                  v-model="settings.general.language"
                  class="settings-view__select"
                  @change="markChanged('general')"
                >
                  <option value="fr">🇫🇷 Français</option>
                  <option value="en">🇬🇧 English</option>
                  <option value="es">🇪🇸 Español</option>
                  <option value="de">🇩🇪 Deutsch</option>
                  <option value="it">🇮🇹 Italiano</option>
                  <option value="pt">🇵🇹 Português</option>
                </select>
              </div>
            </div>

            <!-- Date format -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-date-format" class="settings-view__setting-label">
                  Format de date
                </label>
                <p class="settings-view__setting-desc">
                  Format d'affichage des dates dans l'interface
                </p>
              </div>
              <div class="settings-view__setting-control">
                <select
                  id="setting-date-format"
                  v-model="settings.general.dateFormat"
                  class="settings-view__select"
                  @change="markChanged('general')"
                >
                  <option value="DD/MM/YYYY">DD/MM/YYYY (31/12/2025)</option>
                  <option value="MM/DD/YYYY">MM/DD/YYYY (12/31/2025)</option>
                  <option value="YYYY-MM-DD">YYYY-MM-DD (2025-12-31)</option>
                  <option value="DD MMMM YYYY">DD MMMM YYYY (31 décembre 2025)</option>
                </select>
              </div>
            </div>

            <!-- Timezone -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-timezone" class="settings-view__setting-label">
                  Fuseau horaire
                </label>
                <p class="settings-view__setting-desc">
                  Fuseau horaire pour l'affichage des heures
                </p>
              </div>
              <div class="settings-view__setting-control">
                <select
                  id="setting-timezone"
                  v-model="settings.general.timezone"
                  class="settings-view__select"
                  @change="markChanged('general')"
                >
                  <option value="Europe/Paris">Europe/Paris (UTC+1)</option>
                  <option value="Europe/London">Europe/London (UTC+0)</option>
                  <option value="America/New_York">America/New_York (UTC-5)</option>
                  <option value="America/Los_Angeles">America/Los_Angeles (UTC-8)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (UTC+9)</option>
                </select>
              </div>
            </div>

            <!-- Contenu NSFW -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Contenu pour adultes (NSFW)
                </label>
                <p class="settings-view__setting-desc">
                  Afficher les providers et résultats NSFW dans les recherches
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.general.showNsfw"
                    type="checkbox"
                    @change="markChanged('general')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>

            <!-- Démarrage -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Animation de démarrage
                </label>
                <p class="settings-view__setting-desc">
                  Afficher l'animation de chargement au démarrage
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.general.showLoadingScreen"
                    type="checkbox"
                    @change="markChanged('general')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>
          </section>

          <!-- =========================================================
            SECTION 2 : Apparence
          ========================================================= -->
          <section
            v-else-if="activeSection === 'appearance'"
            key="appearance"
            class="settings-view__section"
          >
            <header class="settings-view__section-header">
              <h2 class="settings-view__section-title">
                <span aria-hidden="true">🎨</span>
                Apparence
              </h2>
              <p class="settings-view__section-desc">
                Personnalisez l'apparence de l'interface
              </p>
            </header>

            <!-- Thème -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">Thème</label>
                <p class="settings-view__setting-desc">
                  Choisissez entre le mode clair, sombre ou automatique
                </p>
              </div>
              <div class="settings-view__setting-control">
                <div class="settings-view__theme-options">
                  <button
                    v-for="option in themeOptions"
                    :key="option.value"
                    type="button"
                    class="settings-view__theme-option"
                    :class="{ 'settings-view__theme-option--active': currentTheme === option.value }"
                    @click="setTheme(option.value)"
                    :aria-pressed="currentTheme === option.value"
                  >
                    <span class="settings-view__theme-option-icon" aria-hidden="true">{{ option.icon }}</span>
                    <span class="settings-view__theme-option-label">{{ option.label }}</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Couleur d'accentuation -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Couleur d'accentuation
                </label>
                <p class="settings-view__setting-desc">
                  Couleur principale utilisée dans l'interface
                </p>
              </div>
              <div class="settings-view__setting-control">
                <div class="settings-view__color-options">
                  <button
                    v-for="color in accentColors"
                    :key="color.value"
                    type="button"
                    class="settings-view__color-option"
                    :class="{ 'settings-view__color-option--active': settings.appearance.accentColor === color.value }"
                    :style="{ background: color.value }"
                    @click="settings.appearance.accentColor = color.value; markChanged('appearance')"
                    :aria-label="`Couleur ${color.label}`"
                    :title="color.label"
                  >
                    <span v-if="settings.appearance.accentColor === color.value" class="settings-view__color-check">
                      ✓
                    </span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Taille de police -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-font-size" class="settings-view__setting-label">
                  Taille de police
                </label>
                <p class="settings-view__setting-desc">
                  Ajuster la taille du texte ({{ settings.appearance.fontSize }}px)
                </p>
              </div>
              <div class="settings-view__setting-control">
                <input
                  id="setting-font-size"
                  v-model.number="settings.appearance.fontSize"
                  type="range"
                  min="12"
                  max="20"
                  step="1"
                  class="settings-view__range"
                  @input="markChanged('appearance')"
                />
              </div>
            </div>

            <!-- Animations -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Activer les animations
                </label>
                <p class="settings-view__setting-desc">
                  Transitions et animations dans l'interface
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.appearance.animations"
                    type="checkbox"
                    @change="markChanged('appearance')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>

            <!-- Interface compacte -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Interface compacte
                </label>
                <p class="settings-view__setting-desc">
                  Réduire les espaces entre les éléments
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.appearance.compactMode"
                    type="checkbox"
                    @change="markChanged('appearance')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>

            <!-- Bannière de fond -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Effets de fond
                </label>
                <p class="settings-view__setting-desc">
                  Grille et effets de lueur en arrière-plan
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.appearance.backgroundEffects"
                    type="checkbox"
                    @change="markChanged('appearance')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>
          </section>

          <!-- =========================================================
            SECTION 3 : Téléchargements
          ========================================================= -->
          <section
            v-else-if="activeSection === 'downloads'"
            key="downloads"
            class="settings-view__section"
          >
            <header class="settings-view__section-header">
              <h2 class="settings-view__section-title">
                <span aria-hidden="true">⬇️</span>
                Téléchargements
              </h2>
              <p class="settings-view__section-desc">
                Configurez les paramètres de téléchargement
              </p>
            </header>

            <!-- Threads parallèles -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-threads" class="settings-view__setting-label">
                  Threads parallèles
                </label>
                <p class="settings-view__setting-desc">
                  Nombre maximum de téléchargements simultanés
                </p>
              </div>
              <div class="settings-view__setting-control">
                <select
                  id="setting-threads"
                  v-model.number="settings.downloads.maxThreads"
                  class="settings-view__select"
                  @change="markChanged('downloads')"
                >
                  <option :value="2">2 threads</option>
                  <option :value="4">4 threads</option>
                  <option :value="8">8 threads</option>
                  <option :value="10">10 threads (recommandé)</option>
                  <option :value="16">16 threads</option>
                  <option :value="20">20 threads</option>
                  <option :value="30">30 threads</option>
                </select>
              </div>
            </div>

            <!-- Timeout -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-timeout" class="settings-view__setting-label">
                  Timeout des requêtes
                </label>
                <p class="settings-view__setting-desc">
                  Délai d'attente maximum par requête ({{ settings.downloads.timeout }}s)
                </p>
              </div>
              <div class="settings-view__setting-control">
                <input
                  id="setting-timeout"
                  v-model.number="settings.downloads.timeout"
                  type="range"
                  min="5"
                  max="120"
                  step="5"
                  class="settings-view__range"
                  @input="markChanged('downloads')"
                />
              </div>
            </div>

            <!-- Retry -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-retry" class="settings-view__setting-label">
                  Tentatives en cas d'échec
                </label>
                <p class="settings-view__setting-desc">
                  Nombre de tentatives avant abandon
                </p>
              </div>
              <div class="settings-view__setting-control">
                <select
                  id="setting-retry"
                  v-model.number="settings.downloads.maxRetries"
                  class="settings-view__select"
                  @change="markChanged('downloads')"
                >
                  <option :value="1">1 tentative</option>
                  <option :value="2">2 tentatives</option>
                  <option :value="3">3 tentatives (recommandé)</option>
                  <option :value="5">5 tentatives</option>
                </select>
              </div>
            </div>

            <!-- Format CBZ -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-format" class="settings-view__setting-label">
                  Format de sortie
                </label>
                <p class="settings-view__setting-desc">
                  Format du fichier généré
                </p>
              </div>
              <div class="settings-view__setting-control">
                <select
                  id="setting-format"
                  v-model="settings.downloads.format"
                  class="settings-view__select"
                  @change="markChanged('downloads')"
                >
                  <option value="cbz">CBZ (recommandé)</option>
                  <option value="zip">ZIP</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>
            </div>

            <!-- Qualité images -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-quality" class="settings-view__setting-label">
                  Qualité des images
                </label>
                <p class="settings-view__setting-desc">
                  Niveau de qualité lors de la compression
                </p>
              </div>
              <div class="settings-view__setting-control">
                <select
                  id="setting-quality"
                  v-model="settings.downloads.imageQuality"
                  class="settings-view__select"
                  @change="markChanged('downloads')"
                >
                  <option value="original">Originale (sans recompression)</option>
                  <option value="high">Haute (95%)</option>
                  <option value="medium">Moyenne (85%)</option>
                  <option value="low">Basse (70%)</option>
                </select>
              </div>
            </div>

            <!-- Redimensionnement -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Redimensionner les grandes images
                </label>
                <p class="settings-view__setting-desc">
                  Réduire automatiquement les images dépassant 4000px
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.downloads.resizeLargeImages"
                    type="checkbox"
                    @change="markChanged('downloads')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>

            <!-- Dossier de destination -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-download-path" class="settings-view__setting-label">
                  Dossier de destination
                </label>
                <p class="settings-view__setting-desc">
                  Chemin où sauvegarder les fichiers CBZ
                </p>
              </div>
              <div class="settings-view__setting-control settings-view__setting-control--wide">
                <input
                  id="setting-download-path"
                  v-model="settings.downloads.downloadPath"
                  type="text"
                  class="settings-view__input"
                  placeholder="./data/downloads"
                  @input="markChanged('downloads')"
                />
              </div>
            </div>
          </section>

          <!-- =========================================================
            SECTION 4 : Providers
          ========================================================= -->
          <section
            v-else-if="activeSection === 'providers'"
            key="providers"
            class="settings-view__section"
          >
            <header class="settings-view__section-header">
              <h2 class="settings-view__section-title">
                <span aria-hidden="true">🌐</span>
                Providers
              </h2>
              <p class="settings-view__section-desc">
                Gérez les sites de scan activés ({{ enabledProvidersCount }}/{{ totalProvidersCount }})
              </p>
            </header>

            <!-- Filtres -->
            <div class="settings-view__providers-toolbar">
              <div class="settings-view__search-wrapper">
                <span class="settings-view__search-icon" aria-hidden="true">🔍</span>
                <input
                  v-model="providerSearch"
                  type="text"
                  class="settings-view__search-input"
                  placeholder="Rechercher un provider..."
                  aria-label="Rechercher un provider"
                />
              </div>
              <div class="settings-view__provider-filters">
                <button
                  v-for="filter in providerFilters"
                  :key="filter.value"
                  type="button"
                  class="settings-view__provider-filter"
                  :class="{ 'settings-view__provider-filter--active': providerFilter === filter.value }"
                  @click="providerFilter = filter.value"
                >
                  <span aria-hidden="true">{{ filter.icon }}</span>
                  {{ filter.label }}
                </button>
              </div>
            </div>

            <!-- Actions groupées -->
            <div class="settings-view__providers-actions">
              <button
                type="button"
                class="settings-view__provider-action settings-view__provider-action--success"
                @click="enableAllProviders"
              >
                ✅ Tout activer
              </button>
              <button
                type="button"
                class="settings-view__provider-action settings-view__provider-action--danger"
                @click="disableAllProviders"
              >
                ⛔ Tout désactiver
              </button>
            </div>

            <!-- Liste des providers -->
            <div class="settings-view__providers-list">
              <div
                v-for="provider in filteredSettingsProviders"
                :key="provider.id"
                class="settings-view__provider-item"
              >
                <div class="settings-view__provider-info">
                  <div class="settings-view__provider-name-wrapper">
                    <span class="settings-view__provider-name">{{ provider.name }}</span>
                    <span v-if="provider.nsfw" class="settings-view__provider-badge settings-view__provider-badge--nsfw">
                      🔞 NSFW
                    </span>
                  </div>
                  <span class="settings-view__provider-url">{{ provider.base_url }}</span>
                  <div class="settings-view__provider-meta">
                    <span class="settings-view__provider-languages">
                      {{ (provider.languages || []).map(l => getLanguageFlag(l)).join(' ') }}
                    </span>
                    <span class="settings-view__provider-version">v{{ provider.version }}</span>
                  </div>
                </div>
                <div class="settings-view__provider-toggle-wrapper">
                  <label class="settings-view__toggle">
                    <input
                      type="checkbox"
                      :checked="provider.enabled"
                      @change="toggleProviderState(provider.id, $event.target.checked)"
                    />
                    <span class="settings-view__toggle-slider" />
                  </label>
                </div>
              </div>

              <div
                v-if="filteredSettingsProviders.length === 0"
                class="settings-view__providers-empty"
              >
                <span aria-hidden="true">📭</span>
                <p>Aucun provider ne correspond à votre recherche</p>
              </div>
            </div>
          </section>

          <!-- =========================================================
            SECTION 5 : Cache
          ========================================================= -->
          <section
            v-else-if="activeSection === 'cache'"
            key="cache"
            class="settings-view__section"
          >
            <header class="settings-view__section-header">
              <h2 class="settings-view__section-title">
                <span aria-hidden="true">🗄️</span>
                Cache
              </h2>
              <p class="settings-view__section-desc">
                Gérez le cache pour améliorer les performances
              </p>
            </header>

            <!-- Activer le cache -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Activer le cache
                </label>
                <p class="settings-view__setting-desc">
                  Mettre en cache les pages et images pour accélérer les analyses
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.cache.enabled"
                    type="checkbox"
                    @change="markChanged('cache')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>

            <!-- Taille max -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-cache-size" class="settings-view__setting-label">
                  Taille maximale du cache
                </label>
                <p class="settings-view__setting-desc">
                  Nombre maximum d'entrées conservées en mémoire
                </p>
              </div>
              <div class="settings-view__setting-control">
                <select
                  id="setting-cache-size"
                  v-model.number="settings.cache.maxSize"
                  class="settings-view__select"
                  :disabled="!settings.cache.enabled"
                  @change="markChanged('cache')"
                >
                  <option :value="100">100 entrées</option>
                  <option :value="300">300 entrées</option>
                  <option :value="500">500 entrées</option>
                  <option :value="1000">1000 entrées</option>
                  <option :value="2000">2000 entrées</option>
                  <option :value="5000">5000 entrées</option>
                </select>
              </div>
            </div>

            <!-- TTL -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-cache-ttl" class="settings-view__setting-label">
                  Durée de vie (TTL)
                </label>
                <p class="settings-view__setting-desc">
                  Durée avant expiration des entrées du cache
                </p>
              </div>
              <div class="settings-view__setting-control">
                <select
                  id="setting-cache-ttl"
                  v-model.number="settings.cache.ttl"
                  class="settings-view__select"
                  :disabled="!settings.cache.enabled"
                  @change="markChanged('cache')"
                >
                  <option :value="300">5 minutes</option>
                  <option :value="900">15 minutes</option>
                  <option :value="3600">1 heure</option>
                  <option :value="21600">6 heures</option>
                  <option :value="86400">24 heures</option>
                  <option :value="604800">7 jours</option>
                </select>
              </div>
            </div>

            <!-- Actions de cache -->
            <div class="settings-view__cache-actions">
              <NexusButton
                variant="warning"
                size="md"
                :loading="clearingCache"
                :disabled="!settings.cache.enabled"
                @click="confirmClearCache"
              >
                🗑️ Vider le cache maintenant
              </NexusButton>

              <NexusButton
                variant="error"
                size="md"
                :loading="clearingTemp"
                @click="confirmClearTemp"
              >
                🧹 Vider les fichiers temporaires
              </NexusButton>
            </div>

            <!-- Statistiques du cache -->
            <div v-if="cacheStats" class="settings-view__cache-stats">
              <h3 class="settings-view__cache-stats-title">📊 Statistiques du cache</h3>
              <dl class="settings-view__cache-stats-list">
                <div class="settings-view__cache-stats-item">
                  <dt>Entrées</dt>
                  <dd>{{ cacheStats.size || 0 }} / {{ settings.cache.maxSize }}</dd>
                </div>
                <div class="settings-view__cache-stats-item">
                  <dt>Taux de succès</dt>
                  <dd>{{ ((cacheStats.hit_rate || 0) * 100).toFixed(1) }}%</dd>
                </div>
                <div class="settings-view__cache-stats-item">
                  <dt>Hits / Misses</dt>
                  <dd>{{ cacheStats.hits || 0 }} / {{ cacheStats.misses || 0 }}</dd>
                </div>
              </dl>
            </div>
          </section>

          <!-- =========================================================
            SECTION 6 : Notifications
          ========================================================= -->
          <section
            v-else-if="activeSection === 'notifications'"
            key="notifications"
            class="settings-view__section"
          >
            <header class="settings-view__section-header">
              <h2 class="settings-view__section-title">
                <span aria-hidden="true">🔔</span>
                Notifications
              </h2>
              <p class="settings-view__section-desc">
                Choisissez les notifications à recevoir
              </p>
            </header>

            <!-- Notifications de téléchargement -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Téléchargements terminés
                </label>
                <p class="settings-view__setting-desc">
                  Notifier quand un téléchargement est terminé
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.notifications.downloadComplete"
                    type="checkbox"
                    @change="markChanged('notifications')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>

            <!-- Notifications d'erreur -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Erreurs de téléchargement
                </label>
                <p class="settings-view__setting-desc">
                  Notifier quand un téléchargement échoue
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.notifications.downloadError"
                    type="checkbox"
                    @change="markChanged('notifications')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>

            <!-- Notifications de nouveaux chapitres -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Nouveaux chapitres
                </label>
                <p class="settings-view__setting-desc">
                  Notifier quand de nouveaux chapitres sont disponibles
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.notifications.newChapters"
                    type="checkbox"
                    @change="markChanged('notifications')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>

            <!-- Durée des notifications -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label for="setting-notif-duration" class="settings-view__setting-label">
                  Durée d'affichage
                </label>
                <p class="settings-view__setting-desc">
                  Durée pendant laquelle les notifications restent visibles
                </p>
              </div>
              <div class="settings-view__setting-control">
                <select
                  id="setting-notif-duration"
                  v-model.number="settings.notifications.duration"
                  class="settings-view__select"
                  @change="markChanged('notifications')"
                >
                  <option :value="2000">2 secondes</option>
                  <option :value="4000">4 secondes</option>
                  <option :value="6000">6 secondes</option>
                  <option :value="10000">10 secondes</option>
                  <option :value="0">Ne pas disparaître automatiquement</option>
                </select>
              </div>
            </div>

            <!-- Sons -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Sons de notification
                </label>
                <p class="settings-view__setting-desc">
                  Jouer un son lors des notifications
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.notifications.sound"
                    type="checkbox"
                    @change="markChanged('notifications')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>
          </section>

          <!-- =========================================================
            SECTION 7 : Système
          ========================================================= -->
          <section
            v-else-if="activeSection === 'system'"
            key="system"
            class="settings-view__section"
          >
            <header class="settings-view__section-header">
              <h2 class="settings-view__section-title">
                <span aria-hidden="true">🔧</span>
                Système
              </h2>
              <p class="settings-view__section-desc">
                Informations système et options avancées
              </p>
            </header>

            <!-- Informations système -->
            <div class="settings-view__system-info">
              <div class="settings-view__system-item">
                <span class="settings-view__system-label">Version</span>
                <span class="settings-view__system-value">v{{ appVersion }}</span>
              </div>
              <div class="settings-view__system-item">
                <span class="settings-view__system-label">Environnement</span>
                <span class="settings-view__system-value">{{ environment }}</span>
              </div>
              <div class="settings-view__system-item">
                <span class="settings-view__system-label">Navigateur</span>
                <span class="settings-view__system-value">{{ browserInfo }}</span>
              </div>
              <div class="settings-view__system-item">
                <span class="settings-view__system-label">Résolution</span>
                <span class="settings-view__system-value">{{ screenResolution }}</span>
              </div>
              <div class="settings-view__system-item">
                <span class="settings-view__system-label">Langue navigateur</span>
                <span class="settings-view__system-value">{{ browserLanguage }}</span>
              </div>
              <div class="settings-view__system-item">
                <span class="settings-view__system-label">Stockage utilisé</span>
                <span class="settings-view__system-value">{{ storageUsage }}</span>
              </div>
            </div>

            <!-- Actions système -->
            <div class="settings-view__system-actions">
              <NexusButton
                variant="warning"
                size="md"
                @click="confirmResetSettings"
              >
                ↺ Réinitialiser tous les paramètres
              </NexusButton>

              <NexusButton
                variant="error"
                size="md"
                @click="confirmClearLocalStorage"
              >
                🗑️ Vider le stockage local
              </NexusButton>

              <NexusButton
                variant="neutral"
                size="md"
                @click="exportSettings"
              >
                📤 Exporter mes paramètres
              </NexusButton>

              <NexusButton
                variant="neutral"
                size="md"
                @click="triggerImportSettings"
              >
                📥 Importer des paramètres
              </NexusButton>

              <input
                ref="importInputRef"
                type="file"
                accept=".json,application/json"
                class="settings-view__import-input"
                @change="importSettings"
              />
            </div>

            <!-- Mode développeur -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Mode développeur
                </label>
                <p class="settings-view__setting-desc">
                  Afficher les options avancées et les logs de débogage
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.system.developerMode"
                    type="checkbox"
                    @change="markChanged('system')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>

            <!-- Logs verbeux -->
            <div class="settings-view__setting">
              <div class="settings-view__setting-info">
                <label class="settings-view__setting-label">
                  Logs verbeux
                </label>
                <p class="settings-view__setting-desc">
                  Afficher tous les logs dans la console (développement)
                </p>
              </div>
              <div class="settings-view__setting-control">
                <label class="settings-view__toggle">
                  <input
                    v-model="settings.system.verboseLogs"
                    type="checkbox"
                    :disabled="!settings.system.developerMode"
                    @change="markChanged('system')"
                  />
                  <span class="settings-view__toggle-slider" />
                </label>
              </div>
            </div>
          </section>

          <!-- =========================================================
            SECTION 8 : À propos
          ========================================================= -->
          <section
            v-else-if="activeSection === 'about'"
            key="about"
            class="settings-view__section settings-view__section--about"
          >
            <div class="settings-view__about">
              <!-- Logo animé -->
              <div class="settings-view__about-logo">
                <span class="settings-view__about-icon" aria-hidden="true">🧬</span>
              </div>

              <h2 class="settings-view__about-title">
                NexusDL {{ appVersion }}
              </h2>
              <p class="settings-view__about-tagline">
                Moteur universel de téléchargement de scans
              </p>

              <div class="settings-view__about-info">
                <div class="settings-view__about-row">
                  <span class="settings-view__about-label">Version</span>
                  <span class="settings-view__about-value">{{ appVersion }}</span>
                </div>
                <div class="settings-view__about-row">
                  <span class="settings-view__about-label">Build</span>
                  <span class="settings-view__about-value">{{ buildDate }}</span>
                </div>
                <div class="settings-view__about-row">
                  <span class="settings-view__about-label">Licence</span>
                  <span class="settings-view__about-value">GNU GPL v3.0</span>
                </div>
                <div class="settings-view__about-row">
                  <span class="settings-view__about-label">Backend</span>
                  <span class="settings-view__about-value">FastAPI + Python 3.10</span>
                </div>
                <div class="settings-view__about-row">
                  <span class="settings-view__about-label">Frontend</span>
                  <span class="settings-view__about-value">Vue.js 3 + Vite</span>
                </div>
                <div class="settings-view__about-row">
                  <span class="settings-view__about-label">Providers</span>
                  <span class="settings-view__about-value">{{ totalProvidersCount }} sites supportés</span>
                </div>
              </div>

              <!-- Fonctionnalités -->
              <div class="settings-view__about-features">
                <h3 class="settings-view__about-features-title">
                  ✨ Fonctionnalités principales
                </h3>
                <ul class="settings-view__about-features-list">
                  <li>🌍 Support de 50+ sites de scan</li>
                  <li>⚡ Téléchargement parallèle asynchrone</li>
                  <li>📦 Export CBZ avec ComicInfo.xml</li>
                  <li>🛡️ Support Playwright pour sites JS/Cloudflare</li>
                  <li>🔐 Authentification JWT sécurisée</li>
                  <li>📡 WebSocket pour le temps réel</li>
                  <li>📚 Gestion complète de bibliothèque</li>
                  <li>🌓 Thème sombre et clair</li>
                </ul>
              </div>

              <!-- Liens -->
              <div class="settings-view__about-links">
                <a
                  href="https://github.com/nexus-dl/nexus-dl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="settings-view__about-link"
                >
                  📖 Documentation
                </a>
                <a
                  href="https://github.com/nexus-dl/nexus-dl/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="settings-view__about-link"
                >
                  🐛 Signaler un bug
                </a>
                <a
                  href="https://discord.gg/nexusdl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="settings-view__about-link"
                >
                  💬 Discord
                </a>
              </div>

              <!-- Copyright -->
              <p class="settings-view__about-copyright">
                © {{ currentYear }} NexusDL Community — Fait avec ❤️
              </p>
            </div>
          </section>
        </Transition>
      </main>
    </div>

    <!-- ====================================================================
      MODALES DE CONFIRMATION
    ==================================================================== -->

    <!-- Confirmation de réinitialisation -->
    <NexusModal
      v-model="showResetModal"
      title="↺ Réinitialiser les paramètres"
      size="sm"
      confirmable
      confirm-text="Réinitialiser"
      cancel-text="Annuler"
      confirm-variant="warning"
      :loading="resetting"
      @confirm="resetSettings"
      @cancel="showResetModal = false"
    >
      <p>
        Êtes-vous sûr de vouloir annuler toutes vos modifications non enregistrées ?
      </p>
      <p class="settings-view__modal-warning">
        ⚠️ Vous perdrez les changements effectués depuis la dernière sauvegarde.
      </p>
    </NexusModal>

    <!-- Confirmation vidage cache -->
    <NexusModal
      v-model="showClearCacheModal"
      title="🗑️ Vider le cache"
      size="sm"
      confirmable
      confirm-text="Vider le cache"
      cancel-text="Annuler"
      confirm-variant="warning"
      :loading="clearingCache"
      @confirm="clearCache"
      @cancel="showClearCacheModal = false"
    >
      <p>Êtes-vous sûr de vouloir vider tout le cache ?</p>
      <p class="settings-view__modal-warning">
        ⚠️ Les prochaines analyses seront plus lentes jusqu'à ce que le cache se recharge.
      </p>
    </NexusModal>

    <!-- Confirmation vidage temp -->
    <NexusModal
      v-model="showClearTempModal"
      title="🧹 Vider les fichiers temporaires"
      size="sm"
      confirmable
      confirm-text="Supprimer"
      cancel-text="Annuler"
      confirm-variant="error"
      :loading="clearingTemp"
      @confirm="clearTemp"
      @cancel="showClearTempModal = false"
    >
      <p>Êtes-vous sûr de vouloir supprimer tous les fichiers temporaires ?</p>
      <p class="settings-view__modal-warning">
        ⚠️ Les téléchargements incomplets seront perdus.
      </p>
    </NexusModal>

    <!-- Confirmation reset complet -->
    <NexusModal
      v-model="showResetSettingsModal"
      title="↺ Réinitialiser tous les paramètres"
      size="sm"
      confirmable
      confirm-text="Réinitialiser tout"
      cancel-text="Annuler"
      confirm-variant="error"
      :loading="resetting"
      @confirm="resetAllSettings"
      @cancel="showResetSettingsModal = false"
    >
      <p>
        Êtes-vous sûr de vouloir réinitialiser <strong>TOUS</strong> les paramètres ?
      </p>
      <p class="settings-view__modal-warning">
        ⚠️ Tous vos paramètres seront restaurés aux valeurs par défaut. Cette
        action est irréversible.
      </p>
    </NexusModal>

    <!-- Confirmation clear localStorage -->
    <NexusModal
      v-model="showClearLocalStorageModal"
      title="🗑️ Vider le stockage local"
      size="sm"
      confirmable
      confirm-text="Vider"
      cancel-text="Annuler"
      confirm-variant="error"
      @confirm="clearLocalStorage"
      @cancel="showClearLocalStorageModal = false"
    >
      <p>
        Êtes-vous sûr de vouloir vider tout le stockage local ?
      </p>
      <p class="settings-view__modal-warning">
        ⚠️ Vous serez déconnecté et tous vos paramètres seront perdus.
      </p>
    </NexusModal>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useTheme } from '@/composables/useTheme'
import { useAuthStore } from '@/stores/auth'
import { useProvidersStore } from '@/stores/providers'
import { useAppStore } from '@/stores/app'
import NexusButton from '@/components/common/NexusButton.vue'
import NexusModal from '@/components/common/NexusModal.vue'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const router = useRouter()
const api = useApi()
const toast = useToast()
const { currentTheme, setTheme: applyTheme } = useTheme()
const authStore = useAuthStore()
const providersStore = useProvidersStore()
const appStore = useAppStore()

// ==========================================================================
//  État réactif
// ==========================================================================

const activeSection = ref('general')
const saving = ref(false)
const resetting = ref(false)
const error = ref(null)
const successMessage = ref('')
const lastUpdated = ref(null)

// Cache
const clearingCache = ref(false)
const clearingTemp = ref(false)
const cacheStats = ref(null)

// Providers
const providerSearch = ref('')
const providerFilter = ref('all')
const settingsProviders = ref([])

// Modales
const showResetModal = ref(false)
const showClearCacheModal = ref(false)
const showClearTempModal = ref(false)
const showResetSettingsModal = ref(false)
const showClearLocalStorageModal = ref(false)

const importInputRef = ref(null)

// Settings par défaut
const defaultSettings = {
  general: {
    language: 'fr',
    dateFormat: 'DD/MM/YYYY',
    timezone: 'Europe/Paris',
    showNsfw: false,
    showLoadingScreen: true,
  },
  appearance: {
    theme: 'system',
    accentColor: '#00d4ff',
    fontSize: 16,
    animations: true,
    compactMode: false,
    backgroundEffects: true,
  },
  downloads: {
    maxThreads: 10,
    timeout: 30,
    maxRetries: 3,
    format: 'cbz',
    imageQuality: 'high',
    resizeLargeImages: true,
    downloadPath: './data/downloads',
  },
  cache: {
    enabled: true,
    maxSize: 500,
    ttl: 3600,
  },
  notifications: {
    downloadComplete: true,
    downloadError: true,
    newChapters: false,
    duration: 4000,
    sound: false,
  },
  system: {
    developerMode: false,
    verboseLogs: false,
  },
}

// Settings réactifs
const settings = reactive(JSON.parse(JSON.stringify(defaultSettings)))

// Settings sauvegardés (pour détecter les changements)
const savedSettings = ref(JSON.parse(JSON.stringify(defaultSettings)))

// Sections
const sections = [
  {
    id: 'general',
    label: 'Général',
    description: 'Langue et préférences',
    icon: '🎯',
  },
  {
    id: 'appearance',
    label: 'Apparence',
    description: 'Thème et style',
    icon: '🎨',
  },
  {
    id: 'downloads',
    label: 'Téléchargements',
    description: 'Configuration de téléchargement',
    icon: '⬇️',
  },
  {
    id: 'providers',
    label: 'Providers',
    description: 'Sites de scan',
    icon: '🌐',
  },
  {
    id: 'cache',
    label: 'Cache',
    description: 'Performance et stockage',
    icon: '🗄️',
  },
  {
    id: 'notifications',
    label: 'Notifications',
    description: 'Alertes et sons',
    icon: '🔔',
  },
  {
    id: 'system',
    label: 'Système',
    description: 'Options avancées',
    icon: '🔧',
  },
  {
    id: 'about',
    label: 'À propos',
    description: 'Informations',
    icon: 'ℹ️',
  },
]

// Options de thème
const themeOptions = [
  { value: 'light', label: 'Clair', icon: '☀️' },
  { value: 'dark', label: 'Sombre', icon: '🌙' },
  { value: 'system', label: 'Auto', icon: '🖥️' },
]

// Couleurs d'accentuation
const accentColors = [
  { value: '#00d4ff', label: 'Cyan NexusDL' },
  { value: '#0066ff', label: 'Bleu' },
  { value: '#4caf50', label: 'Vert' },
  { value: '#ff9800', label: 'Orange' },
  { value: '#f44336', label: 'Rouge' },
  { value: '#9c27b0', label: 'Violet' },
  { value: '#e91e63', label: 'Rose' },
  { value: '#00bcd4', label: 'Turquoise' },
]

// Filtres providers
const providerFilters = [
  { value: 'all', label: 'Tous', icon: '📋' },
  { value: 'enabled', label: 'Activés', icon: '✅' },
  { value: 'disabled', label: 'Désactivés', icon: '⛔' },
  { value: 'nsfw', label: 'NSFW', icon: '🔞' },
]

// ==========================================================================
//  Computed
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')
const environment = computed(() => import.meta.env.MODE || 'production')
const buildDate = computed(() => {
  const date = import.meta.env.VITE_BUILD_DATE
  if (!date) return 'N/A'
  try {
    return dayjs(date).format('DD/MM/YYYY')
  } catch (_) {
    return 'N/A'
  }
})
const currentYear = computed(() => new Date().getFullYear())

const hasUnsavedChanges = computed(() => {
  return JSON.stringify(settings) !== JSON.stringify(savedSettings.value)
})

const totalProvidersCount = computed(() => settingsProviders.value.length)
const enabledProvidersCount = computed(
  () => settingsProviders.value.filter((p) => p.enabled).length
)

const filteredSettingsProviders = computed(() => {
  let result = settingsProviders.value

  // Filtre par statut
  if (providerFilter.value === 'enabled') {
    result = result.filter((p) => p.enabled)
  } else if (providerFilter.value === 'disabled') {
    result = result.filter((p) => !p.enabled)
  } else if (providerFilter.value === 'nsfw') {
    result = result.filter((p) => p.nsfw)
  }

  // Recherche
  if (providerSearch.value.trim()) {
    const q = providerSearch.value.trim().toLowerCase()
    result = result.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.id.toLowerCase().includes(q) ||
        (p.base_url && p.base_url.toLowerCase().includes(q))
    )
  }

  return result
})

// Info navigateur
const browserInfo = computed(() => {
  const ua = navigator.userAgent
  if (ua.includes('Chrome')) return 'Chrome'
  if (ua.includes('Firefox')) return 'Firefox'
  if (ua.includes('Safari') && !ua.includes('Chrome')) return 'Safari'
  if (ua.includes('Edge')) return 'Edge'
  return 'Navigateur inconnu'
})

const screenResolution = computed(() => {
  if (typeof window === 'undefined') return 'N/A'
  return `${window.innerWidth}×${window.innerHeight}`
})

const browserLanguage = computed(() => {
  return navigator.language || 'fr-FR'
})

const storageUsage = computed(() => {
  try {
    let total = 0
    for (const key in localStorage) {
      if (Object.prototype.hasOwnProperty.call(localStorage, key)) {
        total += (localStorage[key]?.length || 0) * 2
      }
    }
    if (total < 1024) return `${total} B`
    if (total < 1024 * 1024) return `${(total / 1024).toFixed(1)} KB`
    return `${(total / (1024 * 1024)).toFixed(2)} MB`
  } catch (_) {
    return 'N/A'
  }
})

// ==========================================================================
//  Méthodes — Persistance
// ==========================================================================

function markChanged(section) {
  // Marquer la section comme modifiée (visuel)
  // La détection globale se fait via hasUnsavedChanges
}

function getSectionChanges(sectionId) {
  // Compter les changements d'une section
  const current = settings[sectionId]
  const saved = savedSettings.value[sectionId]
  if (!current || !saved) return 0

  let changes = 0
  for (const key in current) {
    if (current[key] !== saved[key]) changes++
  }
  return changes
}

async function saveAllSettings() {
  if (!hasUnsavedChanges.value) {
    toast.info('Aucune modification à sauvegarder', 'ℹ️')
    return
  }

  saving.value = true
  error.value = null
  successMessage.value = ''

  try {
    // Sauvegarder dans localStorage
    localStorage.setItem('nexus-settings', JSON.stringify(settings))
    savedSettings.value = JSON.parse(JSON.stringify(settings))
    lastUpdated.value = new Date().toISOString()

    // Appliquer les changements de thème immédiatement
    if (settings.appearance.theme && currentTheme.value !== settings.appearance.theme) {
      applyTheme(settings.appearance.theme)
    }

    // Essayer de synchroniser avec le serveur (optionnel)
    try {
      await api.patch('/auth/profile', {
        preferences: {
          ...(authStore.user?.preferences || {}),
          settings: settings,
        },
      })
    } catch (err) {
      console.warn('Synchronisation serveur impossible:', err.message)
      // Non bloquant : la sauvegarde locale suffit
    }

    successMessage.value = 'Paramètres sauvegardés avec succès'
    toast.success('Paramètres sauvegardés', '💾')

    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (err) {
    console.error('Erreur sauvegarde:', err)
    error.value = `Impossible de sauvegarder : ${err.message}`
    toast.error(error.value, '❌')
  } finally {
    saving.value = false
  }
}

function confirmReset() {
  showResetModal.value = true
}

function resetSettings() {
  resetting.value = true
  try {
    // Restaurer les valeurs sauvegardées
    Object.keys(savedSettings.value).forEach((section) => {
      settings[section] = JSON.parse(JSON.stringify(savedSettings.value[section]))
    })
    showResetModal.value = false
    toast.info('Modifications annulées', '↺')
  } finally {
    resetting.value = false
  }
}

function confirmResetSettings() {
  showResetSettingsModal.value = true
}

function resetAllSettings() {
  resetting.value = true
  try {
    // Restaurer les valeurs par défaut
    Object.keys(defaultSettings).forEach((section) => {
      settings[section] = JSON.parse(JSON.stringify(defaultSettings[section]))
    })
    localStorage.removeItem('nexus-settings')
    showResetSettingsModal.value = false
    toast.success('Paramètres réinitialisés', '↺')
  } finally {
    resetting.value = false
  }
}

function loadSettings() {
  try {
    const stored = localStorage.getItem('nexus-settings')
    if (stored) {
      const parsed = JSON.parse(stored)
      // Fusion avec les valeurs par défaut (pour ajouter les nouvelles clés)
      Object.keys(defaultSettings).forEach((section) => {
        if (parsed[section]) {
          Object.assign(settings[section], parsed[section])
        }
      })
      savedSettings.value = JSON.parse(JSON.stringify(settings))
    }
  } catch (err) {
    console.warn('Erreur chargement paramètres:', err)
  }
}

// ==========================================================================
//  Méthodes — Cache
// ====================================================================*)

function confirmClearCache() {
  showClearCacheModal.value = true
}

async function clearCache() {
  clearingCache.value = true
  try {
    await api.delete('/admin/cache')
    toast.success('Cache vidé avec succès', '🗑️')
    showClearCacheModal.value = false
    await fetchCacheStats()
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    clearingCache.value = false
  }
}

function confirmClearTemp() {
  showClearTempModal.value = true
}

async function clearTemp() {
  clearingTemp.value = true
  try {
    await api.delete('/admin/downloads', { params: { confirm: true } })
    toast.success('Fichiers temporaires supprimés', '🧹')
    showClearTempModal.value = false
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    clearingTemp.value = false
  }
}

async function fetchCacheStats() {
  try {
    const response = await api.get('/system/metrics')
    cacheStats.value = {
      size: response.data?.cache_size || 0,
      hit_rate: 0,
      hits: 0,
      misses: 0,
    }
  } catch (_) {
    // Silencieux
  }
}

// ==========================================================================
//  Méthodes — Providers
// ==========================================================================

async function loadProviders() {
  try {
    // Charger depuis l'API admin
    const response = await api.get('/admin/providers', {
      params: { include_disabled: true },
    })

    let rawProviders = []
    if (Array.isArray(response)) {
      rawProviders = response
    } else if (Array.isArray(response.providers)) {
      rawProviders = response.providers
    }

    settingsProviders.value = rawProviders.map((p) => ({
      id: p.id || p.provider_id,
      name: p.name || 'Sans nom',
      base_url: p.base_url || '',
      enabled: p.enabled !== undefined ? p.enabled : true,
      nsfw: p.nsfw || false,
      languages: Array.isArray(p.languages) ? p.languages : [],
      version: p.version || '1.0.0',
    }))
  } catch (err) {
    console.warn('Impossible de charger les providers:', err.message)
    // Fallback : utiliser le store global
    settingsProviders.value = (providersStore.providerList || []).map((p) => ({
      id: p.id,
      name: p.name,
      base_url: p.base_url,
      enabled: p.enabled,
      nsfw: p.nsfw,
      languages: p.languages || [],
      version: p.version || '1.0.0',
    }))
  }
}

async function toggleProviderState(providerId, enabled) {
  const provider = settingsProviders.value.find((p) => p.id === providerId)
  if (!provider) return

  const previous = provider.enabled
  provider.enabled = enabled

  try {
    await api.patch(`/admin/providers/${providerId}`, { enabled })
    toast.success(
      `Provider "${provider.name}" ${enabled ? 'activé' : 'désactivé'}`,
      enabled ? '✅' : '⛔',
      2000
    )

    // Synchroniser avec le store global
    if (providersStore && typeof providersStore.updateProviderFromWs === 'function') {
      providersStore.updateProviderFromWs({ ...provider, enabled })
    }
  } catch (err) {
    provider.enabled = previous
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

async function enableAllProviders() {
  const targets = settingsProviders.value.filter((p) => !p.enabled)
  if (targets.length === 0) {
    toast.info('Tous les providers sont déjà activés', 'ℹ️')
    return
  }

  for (const provider of targets) {
    await toggleProviderState(provider.id, true)
  }
  toast.success(`${targets.length} provider(s) activé(s)`, '✅')
}

async function disableAllProviders() {
  const targets = settingsProviders.value.filter((p) => p.enabled)
  if (targets.length === 0) {
    toast.info('Tous les providers sont déjà désactivés', 'ℹ️')
    return
  }

  for (const provider of targets) {
    await toggleProviderState(provider.id, false)
  }
  toast.success(`${targets.length} provider(s) désactivé(s)`, '⛔')
}

// ==========================================================================
//  Méthodes — Système
// ==========================================================================

function confirmClearLocalStorage() {
  showClearLocalStorageModal.value = true
}

function clearLocalStorage() {
  try {
    localStorage.clear()
    sessionStorage.clear()
    showClearLocalStorageModal.value = false
    toast.success('Stockage local vidé. Redirection...', '🗑️')

    setTimeout(() => {
      authStore.logout('/login')
    }, 1000)
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

function exportSettings() {
  const data = {
    exported_at: new Date().toISOString(),
    version: appVersion.value,
    settings: settings,
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `nexusdl-settings-${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  toast.success('Paramètres exportés', '📤')
}

function triggerImportSettings() {
  importInputRef.value?.click()
}

async function importSettings(event) {
  const file = event.target.files?.[0]
  if (!file) return

  try {
    const text = await file.text()
    const data = JSON.parse(text)

    if (!data.settings) {
      throw new Error('Format invalide')
    }

    // Fusionner les paramètres importés
    Object.keys(defaultSettings).forEach((section) => {
      if (data.settings[section]) {
        Object.assign(settings[section], data.settings[section])
      }
    })

    toast.success('Paramètres importés. N\'oubliez pas de sauvegarder.', '📥', 4000)
  } catch (err) {
    toast.error(`Erreur d'importation : ${err.message}`, '❌')
  } finally {
    if (importInputRef.value) {
      importInputRef.value.value = ''
    }
  }
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

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  // Charger les paramètres
  loadSettings()

  // Appliquer le thème sauvegardé
  if (settings.appearance.theme && settings.appearance.theme !== currentTheme.value) {
    applyTheme(settings.appearance.theme)
  }

  // Charger les providers
  await loadProviders()

  // Charger les stats de cache
  await fetchCacheStats()

  console.log('⚙️ [SettingsView] Chargée')
})

onUnmounted(() => {
  // Rien de spécial
})

// ==========================================================================
//  Watchers
// ==========================================================================

// Appliquer la taille de police en temps réel
watch(
  () => settings.appearance.fontSize,
  (size) => {
    if (typeof document !== 'undefined') {
      document.documentElement.style.fontSize = `${size}px`
    }
  }
)

// Appliquer la couleur d'accentuation en temps réel
watch(
  () => settings.appearance.accentColor,
  (color) => {
    if (typeof document !== 'undefined') {
      document.documentElement.style.setProperty('--color-primary', color)
    }
  }
)

// Appliquer le mode compact
watch(
  () => settings.appearance.compactMode,
  (compact) => {
    if (typeof document !== 'undefined') {
      document.body.classList.toggle('compact-mode', compact)
    }
  }
)

// Empêcher la fermeture de la page si modifications non sauvegardées
function handleBeforeUnload(event) {
  if (hasUnsavedChanges.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.settings-view {
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

.settings-view__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.settings-view__header-left {
  flex: 1;
  min-width: 200px;
}

.settings-view__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.settings-view__subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.settings-view__header-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

// ==========================================================================
//  Unsaved badge
// ==========================================================================

.settings-view__unsaved-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.7rem;
  background: rgba(255, 152, 0, 0.1);
  border: 1px solid rgba(255, 152, 0, 0.35);
  border-radius: var(--radius-full, 9999px);
  color: var(--color-warning, #ff9800);
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;

  span:first-child {
    animation: settingsPulse 1.5s infinite;
  }
}

@keyframes settingsPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

// ==========================================================================
//  Boutons
// ==========================================================================

.settings-view__btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.5rem 0.9rem;
  font-size: 0.78rem;
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

  &--reset:hover:not(:disabled) {
    border-color: var(--color-warning, #ff9800);
    color: var(--color-warning, #ff9800);
  }

  &--save {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);

    &:hover:not(:disabled) {
      filter: brightness(1.1);
      color: var(--color-text-inverse, #0a0e1a);
    }
  }
}

.settings-view__spinner {
  display: inline-block;
  animation: settingsSpin 0.8s linear infinite;
}

@keyframes settingsSpin {
  to { transform: rotate(360deg); }
}

// ==========================================================================
//  Success / Error
// ==========================================================================

.settings-view__success {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.85rem;
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.35);
  border-radius: var(--radius-md, 8px);
  color: var(--color-success, #4caf50);
  font-size: 0.82rem;
  animation: settingsSuccessIn 0.3s ease;
}

@keyframes settingsSuccessIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.settings-view__success-icon {
  font-size: 1rem;
}

.settings-view__success-text {
  font-weight: 500;
}

.settings-view__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.85rem;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.35);
  border-radius: var(--radius-md, 8px);
  color: var(--color-error, #f44336);
  font-size: 0.82rem;
}

.settings-view__error-icon {
  flex-shrink: 0;
}

.settings-view__error-text {
  flex: 1;
}

.settings-view__error-close {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0 0.2rem;
  opacity: 0.7;

  &:hover {
    opacity: 1;
  }
}

// ==========================================================================
//  Layout
// ==========================================================================

.settings-view__layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 1.5rem;
  align-items: start;
}

// ==========================================================================
//  Sidebar
// ==========================================================================

.settings-view__sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
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

.settings-view__nav {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  flex: 1;
}

.settings-view__nav-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.7rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
  position: relative;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &--active {
    background: rgba(0, 212, 255, 0.1);
    border-color: rgba(0, 212, 255, 0.3);
    color: var(--color-primary, #00d4ff);

    &::before {
      content: '';
      position: absolute;
      left: -0.5rem;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 60%;
      background: var(--color-primary, #00d4ff);
      border-radius: 0 3px 3px 0;
    }
  }
}

.settings-view__nav-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.settings-view__nav-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.settings-view__nav-label {
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1.2;
}

.settings-view__nav-desc {
  font-size: 0.68rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.3;
}

.settings-view__nav-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 0.35rem;
  background: var(--color-warning, #ff9800);
  color: var(--color-text-inverse, #0a0e1a);
  font-size: 0.6rem;
  font-weight: 700;
  border-radius: 9999px;
  flex-shrink: 0;
}

.settings-view__sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
  margin-top: 0.5rem;
}

.settings-view__sidebar-footer-info {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 0.68rem;
}

.settings-view__sidebar-footer-label {
  color: var(--color-text-muted, #6a7a9a);
}

.settings-view__sidebar-footer-value {
  color: var(--color-text-secondary, #b0c0d8);
  font-weight: 500;

  &--env {
    padding: 0.05rem 0.35rem;
    border-radius: var(--radius-sm, 4px);
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  &--env-production {
    background: rgba(76, 175, 80, 0.15);
    color: #4caf50;
  }
  &--env-development {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
  }
  &--env-test {
    background: rgba(33, 150, 243, 0.15);
    color: #2196f3;
  }
}

// ==========================================================================
//  Content
// ==========================================================================

.settings-view__content {
  min-width: 0;
}

.settings-view__section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.5rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
}

.settings-view__section-header {
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
  margin-bottom: 0.5rem;
}

.settings-view__section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.2rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.settings-view__section-desc {
  margin: 0;
  font-size: 0.82rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Setting
// ==========================================================================

.settings-view__setting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-border, #1a2538);

  &:last-of-type {
    border-bottom: none;
  }
}

.settings-view__setting-info {
  flex: 1;
  min-width: 0;
}

.settings-view__setting-label {
  display: block;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
  margin-bottom: 0.15rem;
}

.settings-view__setting-desc {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.4;
}

.settings-view__setting-control {
  flex-shrink: 0;

  &--wide {
    flex: 1;
    max-width: 400px;
  }
}

// ==========================================================================
//  Inputs
// ==========================================================================

.settings-view__select,
.settings-view__input {
  padding: 0.5rem 0.7rem;
  font-size: 0.82rem;
  font-family: inherit;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  cursor: pointer;
  min-width: 180px;
  transition: all 0.15s ease;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.settings-view__input {
  cursor: text;
  width: 100%;
  min-width: 0;
}

.settings-view__range {
  width: 200px;
  height: 5px;
  appearance: none;
  background: var(--color-bg-input, #1e2a40);
  border-radius: 9999px;
  outline: none;
  cursor: pointer;

  &::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    background: var(--color-primary, #00d4ff);
    border: 2px solid #ffffff;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.15s ease;

    &:hover {
      transform: scale(1.15);
    }
  }

  &::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background: var(--color-primary, #00d4ff);
    border: 2px solid #ffffff;
    border-radius: 50%;
    cursor: pointer;
  }
}

// ==========================================================================
//  Toggle
// ==========================================================================

.settings-view__toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;

  input {
    opacity: 0;
    width: 0;
    height: 0;

    &:checked + .settings-view__toggle-slider {
      background: var(--color-primary, #00d4ff);
      border-color: var(--color-primary, #00d4ff);

      &::before {
        transform: translateX(20px);
        background: #ffffff;
      }
    }

    &:focus-visible + .settings-view__toggle-slider {
      box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.25);
    }

    &:disabled + .settings-view__toggle-slider {
      opacity: 0.4;
      cursor: not-allowed;
    }
  }
}

.settings-view__toggle-slider {
  position: absolute;
  inset: 0;
  background: var(--color-bg-input, #1e2a40);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s ease;

  &::before {
    content: '';
    position: absolute;
    height: 18px;
    width: 18px;
    left: 2px;
    top: 50%;
    transform: translateY(-50%);
    background: var(--color-text-muted, #6a7a9a);
    border-radius: 50%;
    transition: all 0.2s ease;
  }
}

// ==========================================================================
//  Theme options
// ==========================================================================

.settings-view__theme-options {
  display: flex;
  gap: 0.35rem;
}

.settings-view__theme-option {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.5rem 0.8rem;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 2px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 500;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-border-light, #253254);
  }

  &--active {
    background: rgba(0, 212, 255, 0.1);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-primary, #00d4ff);
  }
}

.settings-view__theme-option-icon {
  font-size: 1rem;
}

// ==========================================================================
//  Colors
// ==========================================================================

.settings-view__color-options {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.settings-view__color-option {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 3px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);

  &:hover {
    transform: scale(1.1);
  }

  &--active {
    border-color: var(--color-text-primary, #e8edf5);
    box-shadow: 0 0 0 2px var(--color-bg-card, #1a2538), 0 0 0 4px currentColor;
  }
}

.settings-view__color-check {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 700;
  font-size: 1rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

// ==========================================================================
//  Providers
// ==========================================================================

.settings-view__providers-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.settings-view__search-wrapper {
  position: relative;
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
}

.settings-view__search-icon {
  position: absolute;
  left: 0.6rem;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
}

.settings-view__search-input {
  width: 100%;
  padding: 0.5rem 0.5rem 0.5rem 2rem;
  font-size: 0.82rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
  }

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.settings-view__provider-filters {
  display: flex;
  gap: 0.25rem;
}

.settings-view__provider-filter {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.35rem 0.65rem;
  font-size: 0.72rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }

  &--active {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
  }
}

.settings-view__providers-actions {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.settings-view__provider-action {
  padding: 0.35rem 0.75rem;
  font-size: 0.72rem;
  font-weight: 500;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  transition: all 0.15s ease;

  &--success {
    color: var(--color-success, #4caf50);
    border-color: rgba(76, 175, 80, 0.3);

    &:hover {
      background: rgba(76, 175, 80, 0.1);
      border-color: var(--color-success, #4caf50);
    }
  }

  &--danger {
    color: var(--color-error, #f44336);
    border-color: rgba(244, 67, 54, 0.3);

    &:hover {
      background: rgba(244, 67, 54, 0.1);
      border-color: var(--color-error, #f44336);
    }
  }
}

.settings-view__providers-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  max-height: 600px;
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

.settings-view__provider-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--color-border-light, #253254);
  }
}

.settings-view__provider-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.settings-view__provider-name-wrapper {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.settings-view__provider-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.settings-view__provider-badge {
  font-size: 0.6rem;
  font-weight: 600;
  padding: 0.1rem 0.4rem;
  border-radius: 9999px;

  &--nsfw {
    background: rgba(244, 67, 54, 0.15);
    color: #e57373;
    border: 1px solid rgba(244, 67, 54, 0.3);
  }
}

.settings-view__provider-url {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.settings-view__provider-meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.65rem;
  color: var(--color-text-muted, #6a7a9a);
  margin-top: 0.1rem;
}

.settings-view__provider-toggle-wrapper {
  flex-shrink: 0;
}

.settings-view__providers-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem 1rem;
  color: var(--color-text-muted, #6a7a9a);
  text-align: center;

  span {
    font-size: 2.5rem;
    opacity: 0.5;
  }

  p {
    margin: 0;
    font-size: 0.82rem;
  }
}

// ==========================================================================
//  Cache
// ==========================================================================

.settings-view__cache-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding-top: 0.5rem;
}

.settings-view__cache-stats {
  padding: 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
}

.settings-view__cache-stats-title {
  margin: 0 0 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.settings-view__cache-stats-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.5rem;
  margin: 0;
}

.settings-view__cache-stats-item {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.4rem 0.6rem;
  background: var(--color-bg-card, #1a2538);
  border-radius: var(--radius-sm, 4px);

  dt {
    font-size: 0.65rem;
    color: var(--color-text-muted, #6a7a9a);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  dd {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--color-text-primary, #e8edf5);
    font-variant-numeric: tabular-nums;
  }
}

// ==========================================================================
//  Système
// ==========================================================================

.settings-view__system-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
}

.settings-view__system-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  background: var(--color-bg-card, #1a2538);
  border-radius: var(--radius-sm, 4px);
  font-size: 0.75rem;
}

.settings-view__system-label {
  color: var(--color-text-muted, #6a7a9a);
}

.settings-view__system-value {
  color: var(--color-text-primary, #e8edf5);
  font-weight: 500;
  text-align: right;
}

.settings-view__system-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding-top: 0.5rem;
}

.settings-view__import-input {
  display: none;
}

// ==========================================================================
//  About
// ==========================================================================

.settings-view__section--about {
  padding: 2rem 1.5rem;
}

.settings-view__about {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
  max-width: 600px;
  margin: 0 auto;
}

.settings-view__about-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(0, 102, 255, 0.1));
  border: 2px solid rgba(0, 212, 255, 0.3);
  animation: settingsAboutFloat 3s ease-in-out infinite;
}

@keyframes settingsAboutFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.settings-view__about-icon {
  font-size: 3rem;
  filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.5));
}

.settings-view__about-title {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 800;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
}

.settings-view__about-tagline {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.settings-view__about-info {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: 0.75rem 1rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  text-align: left;
  margin-top: 0.5rem;
}

.settings-view__about-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
  padding: 0.3rem 0;
  font-size: 0.78rem;
  border-bottom: 1px solid var(--color-border, #1a2538);

  &:last-child {
    border-bottom: none;
  }
}

.settings-view__about-label {
  color: var(--color-text-muted, #6a7a9a);
}

.settings-view__about-value {
  color: var(--color-text-primary, #e8edf5);
  font-weight: 500;
  text-align: right;
}

.settings-view__about-features {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  text-align: left;
}

.settings-view__about-features-title {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.settings-view__about-features-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.25rem;
  font-size: 0.78rem;
  color: var(--color-text-secondary, #b0c0d8);

  li {
    padding: 0.1rem 0;
  }
}

.settings-view__about-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 0.5rem;
}

.settings-view__about-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.8rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  color: var(--color-primary, #00d4ff);
  text-decoration: none;
  font-size: 0.78rem;
  font-weight: 500;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-primary, #00d4ff);
    transform: translateY(-1px);
  }
}

.settings-view__about-copyright {
  margin: 0.5rem 0 0;
  font-size: 0.72rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Modal warning
// ==========================================================================

.settings-view__modal-warning {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: rgba(255, 152, 0, 0.1);
  border-left: 3px solid var(--color-warning, #ff9800);
  border-radius: var(--radius-sm, 4px);
  font-size: 0.78rem;
  color: var(--color-warning, #ff9800);
  line-height: 1.5;
}

// ==========================================================================
//  Transitions
// ==========================================================================

.settings-view-fade-enter-active,
.settings-view-fade-leave-active {
  transition: all 0.25s ease;
}

.settings-view-fade-enter-from,
.settings-view-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.settings-view-section-enter-active,
.settings-view-section-leave-active {
  transition: all 0.2s ease;
}

.settings-view-section-enter-from {
  opacity: 0;
  transform: translateX(8px);
}

.settings-view-section-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 900px) {
  .settings-view__layout {
    grid-template-columns: 1fr;
  }

  .settings-view__sidebar {
    position: static;
    max-height: none;
    flex-direction: row;
    flex-wrap: wrap;
    padding: 0.4rem;
  }

  .settings-view__nav {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 0.15rem;
  }

  .settings-view__nav-item {
    padding: 0.4rem 0.6rem;

    &::before {
      display: none;
    }
  }

  .settings-view__nav-content {
    display: none;
  }

  .settings-view__nav-icon {
    font-size: 1.2rem;
  }

  .settings-view__sidebar-footer {
    display: none;
  }

  .settings-view__setting {
    flex-direction: column;
    align-items: stretch;
    gap: 0.6rem;
  }

  .settings-view__setting-control {
    width: 100%;
    max-width: 100%;
  }

  .settings-view__select,
  .settings-view__input {
    width: 100%;
    min-width: 0;
  }

  .settings-view__range {
    width: 100%;
  }
}

@media (max-width: 600px) {
  .settings-view {
    padding: 0.5rem;
  }

  .settings-view__title {
    font-size: 1.2rem;
  }

  .settings-view__header-right {
    width: 100%;
  }

  .settings-view__section {
    padding: 1rem;
  }

  .settings-view__section-title {
    font-size: 1rem;
  }

  .settings-view__theme-options {
    flex-direction: column;
  }

  .settings-view__theme-option {
    justify-content: center;
  }

  .settings-view__color-options {
    justify-content: center;
  }

  .settings-view__cache-actions,
  .settings-view__system-actions {
    flex-direction: column;

    > * {
      width: 100%;
      justify-content: center;
    }
  }

  .settings-view__about-info {
    padding: 0.6rem 0.75rem;
  }

  .settings-view__about-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.1rem;
  }

  .settings-view__about-value {
    text-align: left;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .settings-view__sidebar,
  .settings-view__section {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .settings-view__title,
  .settings-view__section-title,
  .settings-view__setting-label,
  .settings-view__about-title,
  .settings-view__provider-name,
  .settings-view__system-value {
    color: var(--color-text-primary, #1a1a2e);
  }

  .settings-view__subtitle,
  .settings-view__section-desc,
  .settings-view__setting-desc,
  .settings-view__about-tagline,
  .settings-view__provider-url {
    color: var(--color-text-muted, #7a8a9a);
  }

  .settings-view__select,
  .settings-view__input,
  .settings-view__search-input {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .settings-view__range {
    background: var(--color-bg-input, #f0f2f5);
  }

  .settings-view__toggle-slider {
    background: var(--color-bg-input, #f0f2f5);
    border-color: var(--color-border, #d0d8e0);

    &::before {
      background: var(--color-text-muted, #7a8a9a);
    }
  }

  .settings-view__theme-option,
  .settings-view__provider-filter {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);

    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
    }
  }

  .settings-view__provider-item,
  .settings-view__system-info,
  .settings-view__cache-stats,
  .settings-view__about-info,
  .settings-view__about-features {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .settings-view__system-item,
  .settings-view__cache-stats-item {
    background: var(--color-bg-card, #ffffff);
  }

  .settings-view__about-link {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .settings-view__btn {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .settings-view__about-logo,
  .settings-view__nav-badge span:first-child,
  .settings-view__spinner {
    animation: none !important;
  }

  .settings-view__theme-option,
  .settings-view__provider-item,
  .settings-view__about-link {
    transition: none;
  }
}
</style>
