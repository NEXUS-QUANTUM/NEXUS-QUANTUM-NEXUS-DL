<!-- ==========================================================================
  NexusDL 2.0 - Profile View (version complète)
  Fichier : frontend/src/views/ProfileView.vue
  Description : Page de profil utilisateur. Affiche les informations du
                compte, permet la modification du profil, le changement de
                mot de passe, la gestion des sessions, les préférences et
                la suppression du compte.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="profile-view">
    <!-- ====================================================================
      ÉTAT DE CHARGEMENT
    ==================================================================== -->
    <div v-if="!user" class="profile-view__loading">
      <NexusSpinner size="xl" variant="gradient" label="Chargement du profil..." />
    </div>

    <template v-else>
      <!-- ================================================================
        EN-TÊTE DU PROFIL
      ================================================================ -->
      <header class="profile-view__header">
        <div class="profile-view__header-bg" aria-hidden="true" />

        <div class="profile-view__header-content">
          <div class="profile-view__avatar-wrapper">
            <div
              class="profile-view__avatar"
              :class="`profile-view__avatar--${user.role}`"
            >
              <img
                v-if="user.avatar_url"
                :src="user.avatar_url"
                :alt="`Avatar de ${user.username}`"
                class="profile-view__avatar-img"
                @error="onAvatarError"
              />
              <span v-else class="profile-view__avatar-initials">
                {{ getInitials(user.username) }}
              </span>
            </div>
            <button
              type="button"
              class="profile-view__avatar-edit"
              @click="triggerAvatarUpload"
              aria-label="Changer l'avatar"
              title="Changer l'avatar"
            >
              📷
            </button>
            <input
              ref="avatarInputRef"
              type="file"
              accept="image/*"
              class="profile-view__avatar-input"
              @change="handleAvatarUpload"
            />
          </div>

          <div class="profile-view__header-info">
            <h1 class="profile-view__name">
              {{ user.full_name || user.username }}
            </h1>
            <p class="profile-view__username">@{{ user.username }}</p>
            <div class="profile-view__header-badges">
              <span
                class="profile-view__badge"
                :class="`profile-view__badge--role-${user.role}`"
              >
                {{ getRoleIcon(user.role) }} {{ getRoleLabel(user.role) }}
              </span>
              <span
                class="profile-view__badge"
                :class="`profile-view__badge--status-${user.status}`"
              >
                {{ getStatusIcon(user.status) }} {{ getStatusLabel(user.status) }}
              </span>
            </div>
          </div>

          <div class="profile-view__header-actions">
            <NexusButton
              variant="neutral"
              size="sm"
              @click="refreshProfile"
              :disabled="loading"
            >
              <span v-if="loading" class="profile-view__spinner" aria-hidden="true">⟳</span>
              <span v-else aria-hidden="true">↻</span>
              Rafraîchir
            </NexusButton>
            <NexusButton
              variant="error"
              size="sm"
              @click="handleLogout"
            >
              🚪 Déconnexion
            </NexusButton>
          </div>
        </div>
      </header>

      <!-- ================================================================
        CONTENU PRINCIPAL
      ================================================================ -->
      <div class="profile-view__body">
        <!-- ============================================================
          COLONNE GAUCHE — Statistiques & Actions rapides
        ============================================================ -->
        <aside class="profile-view__sidebar">
          <!-- Statistiques du compte -->
          <section class="profile-view__card">
            <header class="profile-view__card-header">
              <h2 class="profile-view__card-title">
                <span aria-hidden="true">📊</span>
                Statistiques
              </h2>
            </header>
            <div class="profile-view__card-body">
              <dl class="profile-view__stats">
                <div class="profile-view__stat">
                  <dt class="profile-view__stat-label">Membre depuis</dt>
                  <dd class="profile-view__stat-value">
                    {{ formatDate(user.created_at, 'DD/MM/YYYY') }}
                  </dd>
                </div>
                <div class="profile-view__stat">
                  <dt class="profile-view__stat-label">Dernière connexion</dt>
                  <dd class="profile-view__stat-value">
                    {{ user.last_login ? formatRelativeTime(user.last_login) : '—' }}
                  </dd>
                </div>
                <div class="profile-view__stat">
                  <dt class="profile-view__stat-label">ID utilisateur</dt>
                  <dd class="profile-view__stat-value">#{{ user.id }}</dd>
                </div>
                <div class="profile-view__stat">
                  <dt class="profile-view__stat-label">Sessions actives</dt>
                  <dd class="profile-view__stat-value">{{ sessions.length }}</dd>
                </div>
              </dl>
            </div>
          </section>

          <!-- Accès rapides -->
          <section class="profile-view__card">
            <header class="profile-view__card-header">
              <h2 class="profile-view__card-title">
                <span aria-hidden="true">⚡</span>
                Accès rapides
              </h2>
            </header>
            <div class="profile-view__card-body">
              <div class="profile-view__quick-links">
                <router-link to="/library" class="profile-view__quick-link">
                  <span aria-hidden="true">📚</span>
                  <span>Ma bibliothèque</span>
                  <span aria-hidden="true">→</span>
                </router-link>
                <router-link to="/queue" class="profile-view__quick-link">
                  <span aria-hidden="true">⏳</span>
                  <span>File d'attente</span>
                  <span aria-hidden="true">→</span>
                </router-link>
                <router-link to="/settings" class="profile-view__quick-link">
                  <span aria-hidden="true">⚙️</span>
                  <span>Paramètres</span>
                  <span aria-hidden="true">→</span>
                </router-link>
                <router-link
                  v-if="isAdmin"
                  to="/admin"
                  class="profile-view__quick-link profile-view__quick-link--admin"
                >
                  <span aria-hidden="true">🛠️</span>
                  <span>Administration</span>
                  <span aria-hidden="true">→</span>
                </router-link>
              </div>
            </div>
          </section>

          <!-- Danger zone -->
          <section class="profile-view__card profile-view__card--danger">
            <header class="profile-view__card-header">
              <h2 class="profile-view__card-title">
                <span aria-hidden="true">⚠️</span>
                Zone de danger
              </h2>
            </header>
            <div class="profile-view__card-body">
              <p class="profile-view__danger-text">
                Une fois votre compte supprimé, toutes vos données seront
                définitivement effacées. Cette action est irréversible.
              </p>
              <NexusButton
                variant="error"
                size="sm"
                block
                @click="confirmDeleteAccount"
              >
                🗑️ Supprimer mon compte
              </NexusButton>
            </div>
          </section>
        </aside>

        <!-- ============================================================
          COLONNE DROITE — Sections principales
        ============================================================ -->
        <main class="profile-view__main">
          <!-- Onglets -->
          <nav class="profile-view__tabs" role="tablist" aria-label="Sections du profil">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              type="button"
              role="tab"
              class="profile-view__tab"
              :class="{ 'profile-view__tab--active': activeTab === tab.id }"
              :aria-selected="activeTab === tab.id"
              :aria-controls="`tabpanel-${tab.id}`"
              @click="activeTab = tab.id"
            >
              <span aria-hidden="true">{{ tab.icon }}</span>
              <span>{{ tab.label }}</span>
            </button>
          </nav>

          <!-- =========================================================
            Onglet : Informations personnelles
          ========================================================= -->
          <section
            v-if="activeTab === 'info'"
            id="tabpanel-info"
            class="profile-view__section"
            role="tabpanel"
          >
            <div class="profile-view__section-header">
              <h2 class="profile-view__section-title">
                👤 Informations personnelles
              </h2>
              <p class="profile-view__section-desc">
                Gérez vos informations de profil
              </p>
            </div>

            <form class="profile-view__form" @submit.prevent="saveProfile">
              <div class="profile-view__form-row">
                <div class="profile-view__form-group">
                  <label for="profile-username" class="profile-view__form-label">
                    Nom d'utilisateur
                  </label>
                  <input
                    id="profile-username"
                    :value="user.username"
                    type="text"
                    class="profile-view__form-input"
                    disabled
                    readonly
                  />
                  <p class="profile-view__form-hint">
                    Le nom d'utilisateur ne peut pas être modifié.
                  </p>
                </div>

                <div class="profile-view__form-group">
                  <label for="profile-email" class="profile-view__form-label">
                    Adresse email
                  </label>
                  <input
                    id="profile-email"
                    v-model="profileForm.email"
                    type="email"
                    class="profile-view__form-input"
                    placeholder="votre@email.com"
                    autocomplete="email"
                    required
                    :disabled="savingProfile"
                  />
                </div>
              </div>

              <div class="profile-view__form-group">
                <label for="profile-fullname" class="profile-view__form-label">
                  Nom complet
                </label>
                <input
                  id="profile-fullname"
                  v-model="profileForm.fullName"
                  type="text"
                  class="profile-view__form-input"
                  placeholder="Votre nom complet (optionnel)"
                  autocomplete="name"
                  :disabled="savingProfile"
                  maxlength="100"
                />
              </div>

              <div class="profile-view__form-group">
                <label for="profile-bio" class="profile-view__form-label">
                  Biographie
                </label>
                <textarea
                  id="profile-bio"
                  v-model="profileForm.bio"
                  class="profile-view__form-textarea"
                  placeholder="Parlez-nous de vous..."
                  rows="4"
                  maxlength="500"
                  :disabled="savingProfile"
                />
                <p class="profile-view__form-hint">
                  {{ profileForm.bio.length }} / 500 caractères
                </p>
              </div>

              <div class="profile-view__form-actions">
                <NexusButton
                  type="submit"
                  variant="primary"
                  size="md"
                  :loading="savingProfile"
                  :disabled="!profileChanged"
                >
                  💾 Sauvegarder les modifications
                </NexusButton>
                <NexusButton
                  type="button"
                  variant="neutral"
                  size="md"
                  @click="resetProfileForm"
                  :disabled="!profileChanged || savingProfile"
                >
                  ↺ Annuler
                </NexusButton>
              </div>
            </form>
          </section>

          <!-- =========================================================
            Onglet : Sécurité
          ========================================================= -->
          <section
            v-if="activeTab === 'security'"
            id="tabpanel-security"
            class="profile-view__section"
            role="tabpanel"
          >
            <div class="profile-view__section-header">
              <h2 class="profile-view__section-title">
                🔐 Sécurité
              </h2>
              <p class="profile-view__section-desc">
                Modifiez votre mot de passe et gérez vos sessions
              </p>
            </div>

            <!-- Changement de mot de passe -->
            <div class="profile-view__subsection">
              <h3 class="profile-view__subsection-title">
                🔑 Changer le mot de passe
              </h3>
              <form class="profile-view__form" @submit.prevent="changePassword">
                <div class="profile-view__form-group">
                  <label for="current-password" class="profile-view__form-label">
                    Mot de passe actuel
                  </label>
                  <input
                    id="current-password"
                    v-model="passwordForm.current"
                    type="password"
                    class="profile-view__form-input"
                    placeholder="Votre mot de passe actuel"
                    autocomplete="current-password"
                    required
                    :disabled="savingPassword"
                  />
                </div>

                <div class="profile-view__form-row">
                  <div class="profile-view__form-group">
                    <label for="new-password" class="profile-view__form-label">
                      Nouveau mot de passe
                    </label>
                    <input
                      id="new-password"
                      v-model="passwordForm.newPassword"
                      type="password"
                      class="profile-view__form-input"
                      placeholder="Minimum 6 caractères"
                      autocomplete="new-password"
                      required
                      :disabled="savingPassword"
                      minlength="6"
                    />
                  </div>

                  <div class="profile-view__form-group">
                    <label for="confirm-password" class="profile-view__form-label">
                      Confirmer le mot de passe
                    </label>
                    <input
                      id="confirm-password"
                      v-model="passwordForm.confirm"
                      type="password"
                      class="profile-view__form-input"
                      placeholder="Retapez le mot de passe"
                      autocomplete="new-password"
                      required
                      :disabled="savingPassword"
                    />
                  </div>
                </div>

                <!-- Indicateur de force -->
                <div v-if="passwordForm.newPassword" class="profile-view__password-strength">
                  <div class="profile-view__password-strength-bar">
                    <div
                      class="profile-view__password-strength-fill"
                      :class="`profile-view__password-strength-fill--${passwordStrength.level}`"
                      :style="{ width: `${passwordStrength.percent}%` }"
                    />
                  </div>
                  <span class="profile-view__password-strength-label">
                    Force : {{ passwordStrength.label }}
                  </span>
                </div>

                <p
                  v-if="passwordError"
                  class="profile-view__form-error"
                  role="alert"
                >
                  ❌ {{ passwordError }}
                </p>

                <div class="profile-view__form-actions">
                  <NexusButton
                    type="submit"
                    variant="primary"
                    size="md"
                    :loading="savingPassword"
                    :disabled="!isPasswordFormValid"
                  >
                    🔐 Changer le mot de passe
                  </NexusButton>
                </div>
              </form>
            </div>

            <!-- Sessions actives -->
            <div class="profile-view__subsection">
              <h3 class="profile-view__subsection-title">
                💻 Sessions actives
                <span v-if="sessions.length > 0" class="profile-view__subsection-count">
                  ({{ sessions.length }})
                </span>
              </h3>

              <div v-if="sessionsLoading" class="profile-view__sessions-loading">
                <NexusSpinner size="sm" label="Chargement des sessions..." />
              </div>

              <div v-else-if="sessions.length === 0" class="profile-view__sessions-empty">
                Aucune session active
              </div>

              <ul v-else class="profile-view__sessions">
                <li
                  v-for="session in sessions"
                  :key="session.id"
                  class="profile-view__session"
                  :class="{ 'profile-view__session--current': session.isCurrent }"
                >
                  <div class="profile-view__session-icon" aria-hidden="true">
                    {{ getDeviceIcon(session.user_agent) }}
                  </div>
                  <div class="profile-view__session-info">
                    <div class="profile-view__session-header">
                      <span class="profile-view__session-device">
                        {{ getDeviceName(session.user_agent) }}
                        <span v-if="session.isCurrent" class="profile-view__session-current-badge">
                          Session actuelle
                        </span>
                      </span>
                    </div>
                    <div class="profile-view__session-meta">
                      <span class="profile-view__session-ip">
                        📍 {{ session.ip_address || 'IP inconnue' }}
                      </span>
                      <span class="profile-view__session-date">
                        🕐 {{ formatRelativeTime(session.created_at) }}
                      </span>
                    </div>
                  </div>
                  <button
                    v-if="!session.isCurrent"
                    type="button"
                    class="profile-view__session-revoke"
                    @click="revokeSession(session)"
                    :disabled="revokingSessionId === session.id"
                    :aria-label="`Révoquer la session ${session.id}`"
                    title="Révoquer cette session"
                  >
                    <span v-if="revokingSessionId === session.id" class="profile-view__spinner">⟳</span>
                    <span v-else>✖</span>
                  </button>
                </li>
              </ul>

              <NexusButton
                v-if="sessions.length > 1"
                variant="error"
                size="sm"
                @click="confirmRevokeAllSessions"
                :disabled="revokingAll"
              >
                🚫 Révoquer toutes les autres sessions
              </NexusButton>
            </div>
          </section>

          <!-- =========================================================
            Onglet : Préférences
          ========================================================= -->
          <section
            v-if="activeTab === 'preferences'"
            id="tabpanel-preferences"
            class="profile-view__section"
            role="tabpanel"
          >
            <div class="profile-view__section-header">
              <h2 class="profile-view__section-title">
                ⚙️ Préférences
              </h2>
              <p class="profile-view__section-desc">
                Personnalisez votre expérience NexusDL
              </p>
            </div>

            <div class="profile-view__preferences">
              <!-- Thème -->
              <div class="profile-view__preference">
                <div class="profile-view__preference-info">
                  <span class="profile-view__preference-label">Thème de l'interface</span>
                  <span class="profile-view__preference-desc">
                    Choisissez entre le mode clair, sombre ou automatique
                  </span>
                </div>
                <div class="profile-view__preference-control">
                  <div class="profile-view__theme-options">
                    <button
                      v-for="option in themeOptions"
                      :key="option.value"
                      type="button"
                      class="profile-view__theme-option"
                      :class="{ 'profile-view__theme-option--active': currentTheme === option.value }"
                      @click="setTheme(option.value)"
                      :aria-pressed="currentTheme === option.value"
                      :title="option.label"
                    >
                      <span aria-hidden="true">{{ option.icon }}</span>
                      <span>{{ option.label }}</span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Langue -->
              <div class="profile-view__preference">
                <div class="profile-view__preference-info">
                  <span class="profile-view__preference-label">Langue</span>
                  <span class="profile-view__preference-desc">
                    Langue de l'interface et des recherches
                  </span>
                </div>
                <div class="profile-view__preference-control">
                  <select
                    v-model="preferences.language"
                    class="profile-view__select"
                    @change="savePreference('language')"
                  >
                    <option value="fr">🇫🇷 Français</option>
                    <option value="en">🇬🇧 English</option>
                    <option value="es">🇪🇸 Español</option>
                    <option value="de">🇩🇪 Deutsch</option>
                  </select>
                </div>
              </div>

              <!-- Contenu NSFW -->
              <div class="profile-view__preference">
                <div class="profile-view__preference-info">
                  <span class="profile-view__preference-label">Contenu pour adultes</span>
                  <span class="profile-view__preference-desc">
                    Afficher les résultats NSFW dans les recherches
                  </span>
                </div>
                <div class="profile-view__preference-control">
                  <label class="profile-view__toggle">
                    <input
                      type="checkbox"
                      v-model="preferences.showNsfw"
                      @change="savePreference('showNsfw')"
                    />
                    <span class="profile-view__toggle-slider" />
                  </label>
                </div>
              </div>

              <!-- Notifications -->
              <div class="profile-view__preference">
                <div class="profile-view__preference-info">
                  <span class="profile-view__preference-label">Notifications</span>
                  <span class="profile-view__preference-desc">
                    Recevoir des notifications pour les téléchargements terminés
                  </span>
                </div>
                <div class="profile-view__preference-control">
                  <label class="profile-view__toggle">
                    <input
                      type="checkbox"
                      v-model="preferences.notifications"
                      @change="savePreference('notifications')"
                    />
                    <span class="profile-view__toggle-slider" />
                  </label>
                </div>
              </div>

              <!-- Auto-play -->
              <div class="profile-view__preference">
                <div class="profile-view__preference-info">
                  <span class="profile-view__preference-label">Lecture automatique</span>
                  <span class="profile-view__preference-desc">
                    Ouvrir automatiquement le prochain chapitre en lecture
                  </span>
                </div>
                <div class="profile-view__preference-control">
                  <label class="profile-view__toggle">
                    <input
                      type="checkbox"
                      v-model="preferences.autoPlay"
                      @change="savePreference('autoPlay')"
                    />
                    <span class="profile-view__toggle-slider" />
                  </label>
                </div>
              </div>

              <!-- Nombre de téléchargements parallèles -->
              <div class="profile-view__preference">
                <div class="profile-view__preference-info">
                  <span class="profile-view__preference-label">Téléchargements parallèles</span>
                  <span class="profile-view__preference-desc">
                    Nombre maximum de téléchargements simultanés
                  </span>
                </div>
                <div class="profile-view__preference-control">
                  <select
                    v-model.number="preferences.maxThreads"
                    class="profile-view__select"
                    @change="savePreference('maxThreads')"
                  >
                    <option :value="2">2</option>
                    <option :value="4">4</option>
                    <option :value="8">8</option>
                    <option :value="10">10</option>
                    <option :value="16">16</option>
                    <option :value="20">20</option>
                  </select>
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>
    </template>

    <!-- ====================================================================
      MODALE DE CONFIRMATION — Suppression de compte
    ==================================================================== -->
    <NexusModal
      v-model="showDeleteAccountModal"
      title="🗑️ Supprimer le compte"
      size="sm"
      :loading="deletingAccount"
      :show-footer="true"
    >
      <div class="profile-view__delete-account">
        <p>
          Êtes-vous sûr de vouloir supprimer votre compte
          <strong>@{{ user?.username }}</strong> ?
        </p>
        <p class="profile-view__delete-account-warning">
          ⚠️ Cette action supprimera <strong>définitivement</strong> :
        </p>
        <ul class="profile-view__delete-account-list">
          <li>Votre profil et toutes vos données personnelles</li>
          <li>Votre historique de téléchargements</li>
          <li>Vos favoris et vos notes</li>
        </ul>
        <p class="profile-view__delete-account-warning">
          Les fichiers CBZ déjà téléchargés ne seront pas supprimés du serveur.
        </p>

        <div class="profile-view__delete-account-confirm">
          <label class="profile-view__form-label">
            Tapez <code>SUPPRIMER</code> pour confirmer :
          </label>
          <input
            v-model="deleteConfirmText"
            type="text"
            class="profile-view__form-input"
            placeholder="SUPPRIMER"
            :disabled="deletingAccount"
          />
        </div>
      </div>

      <template #footer>
        <NexusButton
          variant="neutral"
          @click="showDeleteAccountModal = false"
          :disabled="deletingAccount"
        >
          Annuler
        </NexusButton>
        <NexusButton
          variant="error"
          :loading="deletingAccount"
          :disabled="deleteConfirmText !== 'SUPPRIMER'"
          @click="deleteAccount"
        >
          Supprimer définitivement
        </NexusButton>
      </template>
    </NexusModal>

    <!-- ====================================================================
      MODALE DE CONFIRMATION — Révocation de sessions
    ==================================================================== -->
    <NexusModal
      v-model="showRevokeAllModal"
      title="🚫 Révoquer toutes les sessions"
      size="sm"
      confirmable
      confirm-text="Tout révoquer"
      cancel-text="Annuler"
      confirm-variant="error"
      :loading="revokingAll"
      @confirm="revokeAllSessions"
      @cancel="showRevokeAllModal = false"
    >
      <p>
        Êtes-vous sûr de vouloir révoquer toutes les sessions
        <strong>sauf la session actuelle</strong> ?
      </p>
      <p class="profile-view__delete-account-warning">
        Vous devrez vous reconnecter sur les autres appareils.
      </p>
    </NexusModal>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { useApi } from '@/composables/useApi'
import { useTheme } from '@/composables/useTheme'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusButton from '@/components/common/NexusButton.vue'
import NexusModal from '@/components/common/NexusModal.vue'
import {
  formatDateTime as fmtDateTime,
  formatRelativeTime as fmtRelativeTime,
} from '@/utils/formatters'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()
const api = useApi()
const { currentTheme, setTheme: applyTheme } = useTheme()

// ==========================================================================
//  État réactif
// ==========================================================================

const loading = ref(false)
const savingProfile = ref(false)
const savingPassword = ref(false)
const passwordError = ref('')
const activeTab = ref('info')

const avatarInputRef = ref(null)

// Formulaire profil
const profileForm = reactive({
  email: '',
  fullName: '',
  bio: '',
})

// Formulaire mot de passe
const passwordForm = reactive({
  current: '',
  newPassword: '',
  confirm: '',
})

// Préférences
const preferences = reactive({
  language: 'fr',
  showNsfw: false,
  notifications: true,
  autoPlay: false,
  maxThreads: 10,
})

// Sessions
const sessions = ref([])
const sessionsLoading = ref(false)
const revokingSessionId = ref(null)
const revokingAll = ref(false)
const showRevokeAllModal = ref(false)

// Suppression de compte
const showDeleteAccountModal = ref(false)
const deleteConfirmText = ref('')
const deletingAccount = ref(false)

// ==========================================================================
//  Computed
// ==========================================================================

const user = computed(() => authStore.user)
const isAdmin = computed(() => authStore.isAdmin)

const tabs = [
  { id: 'info', label: 'Informations', icon: '👤' },
  { id: 'security', label: 'Sécurité', icon: '🔐' },
  { id: 'preferences', label: 'Préférences', icon: '⚙️' },
]

const themeOptions = [
  { value: 'light', label: 'Clair', icon: '☀️' },
  { value: 'dark', label: 'Sombre', icon: '🌙' },
  { value: 'system', label: 'Auto', icon: '🖥️' },
]

const profileChanged = computed(() => {
  if (!user.value) return false
  return (
    profileForm.email !== (user.value.email || '') ||
    profileForm.fullName !== (user.value.full_name || '') ||
    profileForm.bio !== (user.value.preferences?.bio || '')
  )
})

const isPasswordFormValid = computed(() => {
  return (
    passwordForm.current.length > 0 &&
    passwordForm.newPassword.length >= 6 &&
    passwordForm.newPassword === passwordForm.confirm
  )
})

const passwordStrength = computed(() => {
  const pwd = passwordForm.newPassword
  if (!pwd) return { level: 'none', percent: 0, label: '—' }

  let score = 0
  if (pwd.length >= 6) score++
  if (pwd.length >= 10) score++
  if (/[a-z]/.test(pwd)) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/[0-9]/.test(pwd)) score++
  if (/[^A-Za-z0-9]/.test(pwd)) score++

  if (score <= 2) return { level: 'weak', percent: 33, label: 'Faible' }
  if (score <= 4) return { level: 'medium', percent: 66, label: 'Moyen' }
  return { level: 'strong', percent: 100, label: 'Fort' }
})

// ==========================================================================
//  Méthodes — Récupération
// ==========================================================================

async function refreshProfile() {
  loading.value = true
  try {
    await authStore.fetchUser(true)
    syncProfileForm()
    await loadSessions()
    toast.info('Profil actualisé', '🔄', 1500)
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    loading.value = false
  }
}

async function loadSessions() {
  sessionsLoading.value = true
  try {
    const response = await api.get('/auth/sessions')
    const data = response.data || response
    sessions.value = Array.isArray(data)
      ? data.map((s) => ({ ...s, isCurrent: false }))
      : []
  } catch (err) {
    console.warn('Erreur chargement sessions:', err.message)
    sessions.value = []
  } finally {
    sessionsLoading.value = false
  }
}

// ==========================================================================
//  Méthodes — Formulaire profil
// ==========================================================================

function syncProfileForm() {
  if (!user.value) return
  profileForm.email = user.value.email || ''
  profileForm.fullName = user.value.full_name || ''
  profileForm.bio = user.value.preferences?.bio || ''
}

function resetProfileForm() {
  syncProfileForm()
}

async function saveProfile() {
  if (!profileChanged.value) {
    toast.info('Aucune modification à sauvegarder', 'ℹ️')
    return
  }

  savingProfile.value = true
  try {
    const payload = {
      email: profileForm.email,
      full_name: profileForm.fullName,
      preferences: {
        ...(user.value?.preferences || {}),
        bio: profileForm.bio,
      },
    }
    await api.patch('/auth/profile', payload)
    // Rafraîchir les données utilisateur
    await authStore.fetchUser(true)
    toast.success('Profil mis à jour avec succès', '✅')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    savingProfile.value = false
  }
}

// ==========================================================================
//  Méthodes — Avatar
// ==========================================================================

function triggerAvatarUpload() {
  avatarInputRef.value?.click()
}

async function handleAvatarUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return

  // Validation
  if (!file.type.startsWith('image/')) {
    toast.error('Le fichier doit être une image', '❌')
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    toast.error('L\'image ne doit pas dépasser 2 MB', '❌')
    return
  }

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('avatar', file)

    const response = await api.upload('/auth/avatar', formData)
    const avatarUrl = response.avatar_url || response.data?.avatar_url

    if (avatarUrl && user.value) {
      user.value.avatar_url = avatarUrl
      toast.success('Avatar mis à jour', '📷')
    }

    // Reset input
    if (avatarInputRef.value) {
      avatarInputRef.value.value = ''
    }
  } catch (err) {
    toast.error(`Erreur upload avatar : ${err.message}`, '❌')
  } finally {
    loading.value = false
  }
}

function onAvatarError(event) {
  event.target.style.display = 'none'
}

// ==========================================================================
//  Méthodes — Mot de passe
// ==========================================================================

async function changePassword() {
  passwordError.value = ''

  if (passwordForm.newPassword !== passwordForm.confirm) {
    passwordError.value = 'Les mots de passe ne correspondent pas.'
    return
  }
  if (passwordForm.newPassword.length < 6) {
    passwordError.value = 'Le mot de passe doit contenir au moins 6 caractères.'
    return
  }

  savingPassword.value = true
  try {
    await api.post('/auth/change-password', {
      old_password: passwordForm.current,
      new_password: passwordForm.newPassword,
    })
    toast.success('Mot de passe modifié avec succès', '🔐')

    // Reset
    passwordForm.current = ''
    passwordForm.newPassword = ''
    passwordForm.confirm = ''
  } catch (err) {
    const detail = err.response?.data?.detail
    passwordError.value = detail || 'Impossible de changer le mot de passe.'
    toast.error(passwordError.value, '❌')
  } finally {
    savingPassword.value = false
  }
}

// ==========================================================================
//  Méthodes — Sessions
// ==========================================================================

async function revokeSession(session) {
  revokingSessionId.value = session.id
  try {
    await api.delete(`/auth/sessions/${session.id}`)
    sessions.value = sessions.value.filter((s) => s.id !== session.id)
    toast.success('Session révoquée', '🚫')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    revokingSessionId.value = null
  }
}

function confirmRevokeAllSessions() {
  showRevokeAllModal.value = true
}

async function revokeAllSessions() {
  revokingAll.value = true
  try {
    await api.delete('/auth/sessions')
    sessions.value = sessions.value.filter((s) => s.isCurrent)
    toast.success('Toutes les autres sessions ont été révoquées', '🚫')
    showRevokeAllModal.value = false
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    revokingAll.value = false
  }
}

function getDeviceIcon(userAgent) {
  if (!userAgent) return '💻'
  const ua = userAgent.toLowerCase()
  if (ua.includes('mobile') || ua.includes('android')) return '📱'
  if (ua.includes('iphone') || ua.includes('ipad')) return '📱'
  if (ua.includes('mac')) return '🖥️'
  if (ua.includes('linux')) return '🐧'
  if (ua.includes('windows')) return '🪟'
  return '💻'
}

function getDeviceName(userAgent) {
  if (!userAgent) return 'Appareil inconnu'
  const ua = userAgent.toLowerCase()
  if (ua.includes('chrome')) return 'Chrome'
  if (ua.includes('firefox')) return 'Firefox'
  if (ua.includes('safari') && !ua.includes('chrome')) return 'Safari'
  if (ua.includes('edge')) return 'Edge'
  if (ua.includes('opera')) return 'Opera'
  return 'Navigateur inconnu'
}

// ==========================================================================
//  Méthodes — Préférences
// ==========================================================================

function setTheme(theme) {
  applyTheme(theme)
  savePreference('theme')
}

async function savePreference(key) {
  try {
    const payload = {
      preferences: {
        ...(user.value?.preferences || {}),
        ...preferences,
        theme: currentTheme.value,
      },
    }
    await api.patch('/auth/profile', payload)
    toast.success('Préférence enregistrée', '✅', 1500)
  } catch (err) {
    console.warn('Erreur sauvegarde préférence:', err.message)
  }
}

// ==========================================================================
//  Méthodes — Suppression de compte
// ==========================================================================

function confirmDeleteAccount() {
  deleteConfirmText.value = ''
  showDeleteAccountModal.value = true
}

async function deleteAccount() {
  if (deleteConfirmText.value !== 'SUPPRIMER') return

  deletingAccount.value = true
  try {
    await api.delete('/auth/account', {
      data: { confirm: 'SUPPRIMER' },
    })
    toast.success('Compte supprimé', '🗑️')
    showDeleteAccountModal.value = false

    // Déconnexion + redirection
    await authStore.logout('/')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    deletingAccount.value = false
  }
}

// ==========================================================================
//  Méthodes — Déconnexion
// ==========================================================================

async function handleLogout() {
  if (!confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) return
  await authStore.logout('/login')
  toast.info('Vous êtes déconnecté', '👋')
}

// ==========================================================================
//  Méthodes — Utilitaires
// ==========================================================================

function getInitials(name) {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

function getRoleIcon(role) {
  const map = { admin: '🛠️', user: '👤', guest: '👁️' }
  return map[role] || '👤'
}

function getRoleLabel(role) {
  const map = { admin: 'Administrateur', user: 'Utilisateur', guest: 'Invité' }
  return map[role] || role
}

function getStatusIcon(status) {
  const map = {
    active: '✅',
    inactive: '⏸️',
    banned: '🚫',
    pending: '⏳',
  }
  return map[status] || '❓'
}

function getStatusLabel(status) {
  const map = {
    active: 'Actif',
    inactive: 'Inactif',
    banned: 'Banni',
    pending: 'En attente',
  }
  return map[status] || status
}

function formatRelativeTime(date) {
  if (!date) return '—'
  try {
    return fmtRelativeTime(date)
  } catch (_) {
    return '—'
  }
}

function formatDate(date, format = 'DD/MM/YYYY') {
  if (!date) return '—'
  try {
    const d = dayjs(date)
    return d.isValid() ? d.format(format) : '—'
  } catch (_) {
    return '—'
  }
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  // Charger les données utilisateur
  if (!user.value) {
    try {
      await authStore.fetchUser(true)
    } catch (err) {
      toast.error('Impossible de charger le profil', '❌')
      router.push('/login')
      return
    }
  }

  // Initialiser le formulaire
  syncProfileForm()

  // Charger les préférences
  if (user.value?.preferences) {
    Object.assign(preferences, user.value.preferences)
  }

  // Charger les sessions
  await loadSessions()
})

// Surveiller les changements d'utilisateur
watch(
  () => user.value,
  (newUser) => {
    if (newUser) {
      syncProfileForm()
      if (newUser.preferences) {
        Object.assign(preferences, newUser.preferences)
      }
    }
  }
)
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.profile-view {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  min-height: calc(100vh - 100px);
}

.profile-view__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  width: 100%;
}

// ==========================================================================
//  Header du profil
// ==========================================================================

.profile-view__header {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-xl, 16px);
  border: 1px solid var(--color-border, #1a2538);
  background: var(--color-bg-card, #1a2538);
}

.profile-view__header-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 30%, rgba(0, 212, 255, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(0, 102, 255, 0.12) 0%, transparent 50%);
  z-index: 0;
  pointer-events: none;
}

.profile-view__header-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
}

// ==========================================================================
//  Avatar
// ==========================================================================

.profile-view__avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.profile-view__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 90px;
  height: 90px;
  border-radius: 50%;
  overflow: hidden;
  font-weight: 700;
  font-size: 2.2rem;
  color: #ffffff;
  border: 3px solid var(--color-bg-card, #1a2538);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  position: relative;

  &--admin {
    background: linear-gradient(135deg, #ff9800, #f57c00);
  }
  &--user {
    background: linear-gradient(135deg, #00d4ff, #0066ff);
  }
  &--guest {
    background: linear-gradient(135deg, #6a7a9a, #4a5a72);
  }
}

.profile-view__avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-view__avatar-initials {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.profile-view__avatar-edit {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
  border: 2px solid var(--color-bg-card, #1a2538);
  cursor: pointer;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;

  &:hover {
    transform: scale(1.1);
    filter: brightness(1.1);
  }
}

.profile-view__avatar-input {
  display: none;
}

// ==========================================================================
//  Header infos
// ==========================================================================

.profile-view__header-info {
  flex: 1;
  min-width: 200px;
}

.profile-view__name {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  line-height: 1.2;
}

.profile-view__username {
  margin: 0.15rem 0 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.profile-view__header-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.5rem;
}

.profile-view__badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: var(--radius-full, 9999px);
  white-space: nowrap;

  &--role-admin {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
    border: 1px solid rgba(255, 152, 0, 0.3);
  }
  &--role-user {
    background: rgba(33, 150, 243, 0.15);
    color: #2196f3;
    border: 1px solid rgba(33, 150, 243, 0.3);
  }
  &--role-guest {
    background: rgba(106, 122, 154, 0.15);
    color: #8899b0;
    border: 1px solid rgba(106, 122, 154, 0.3);
  }

  &--status-active {
    background: rgba(76, 175, 80, 0.15);
    color: #4caf50;
    border: 1px solid rgba(76, 175, 80, 0.3);
  }
  &--status-inactive {
    background: rgba(106, 122, 154, 0.15);
    color: #8899b0;
  }
  &--status-banned {
    background: rgba(244, 67, 54, 0.15);
    color: #f44336;
  }
  &--status-pending {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
  }
}

// ==========================================================================
//  Header actions
// ==========================================================================

.profile-view__header-actions {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.profile-view__spinner {
  display: inline-block;
  animation: profileSpin 0.8s linear infinite;
}

@keyframes profileSpin {
  to { transform: rotate(360deg); }
}

// ==========================================================================
//  Body layout
// ==========================================================================

.profile-view__body {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 1.5rem;
  align-items: start;
}

// ==========================================================================
//  Sidebar
// ==========================================================================

.profile-view__sidebar {
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
//  Cards
// ==========================================================================

.profile-view__card {
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;

  &--danger {
    border-color: rgba(244, 67, 54, 0.4);
  }
}

.profile-view__card-header {
  padding: 0.75rem 1rem;
  background: var(--color-bg-secondary, #141a2b);
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.profile-view__card-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.profile-view__card-body {
  padding: 0.85rem 1rem;
}

// ==========================================================================
//  Stats
// ==========================================================================

.profile-view__stats {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
}

.profile-view__stat {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
  font-size: 0.8rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--color-border, #1a2538);

  &:last-child {
    border-bottom: none;
  }
}

.profile-view__stat-label {
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.7rem;
}

.profile-view__stat-value {
  margin: 0;
  color: var(--color-text-primary, #e8edf5);
  font-weight: 500;
  text-align: right;
}

// ==========================================================================
//  Quick links
// ==========================================================================

.profile-view__quick-links {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.profile-view__quick-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.6rem;
  background: transparent;
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-secondary, #b0c0d8);
  text-decoration: none;
  font-size: 0.8rem;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);

    span:last-child {
      transform: translateX(3px);
    }
  }

  span:last-child {
    margin-left: auto;
    transition: transform 0.15s ease;
  }

  &--admin {
    color: var(--color-warning, #ff9800);

    &:hover {
      background: rgba(255, 152, 0, 0.1);
      color: var(--color-warning, #ff9800);
    }
  }
}

// ==========================================================================
//  Danger zone
// ==========================================================================

.profile-view__danger-text {
  margin: 0 0 0.75rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.5;
}

// ==========================================================================
//  Main
// ==========================================================================

.profile-view__main {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 0;
}

// ==========================================================================
//  Tabs
// ==========================================================================

.profile-view__tabs {
  display: flex;
  gap: 0.25rem;
  padding: 0.35rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  overflow-x: auto;

  &::-webkit-scrollbar {
    height: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
  }
}

.profile-view__tab {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.5rem 0.9rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &--active {
    background: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);

    &:hover {
      background: var(--color-primary, #00d4ff);
      color: var(--color-text-inverse, #0a0e1a);
    }
  }
}

// ==========================================================================
//  Sections
// ==========================================================================

.profile-view__section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.25rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  animation: profileSectionIn 0.25s ease;
}

@keyframes profileSectionIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.profile-view__section-header {
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.profile-view__section-title {
  margin: 0 0 0.2rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.profile-view__section-desc {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
}

.profile-view__subsection {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 0.5rem;

  &:not(:last-child) {
    padding-bottom: 1.25rem;
    border-bottom: 1px solid var(--color-border, #1a2538);
  }
}

.profile-view__subsection-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.profile-view__subsection-count {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Formulaire
// ==========================================================================

.profile-view__form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.profile-view__form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.profile-view__form-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.profile-view__form-label {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--color-text-secondary, #b0c0d8);
}

.profile-view__form-input,
.profile-view__form-textarea {
  width: 100%;
  padding: 0.55rem 0.75rem;
  font-size: 0.85rem;
  font-family: inherit;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  transition: all 0.15s ease;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15);
  }

  &:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.profile-view__form-textarea {
  resize: vertical;
  min-height: 90px;
  line-height: 1.5;
}

.profile-view__form-hint {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

.profile-view__form-error {
  margin: 0;
  padding: 0.5rem 0.75rem;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.35);
  border-radius: var(--radius-md, 8px);
  color: var(--color-error, #f44336);
  font-size: 0.78rem;
}

.profile-view__form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding-top: 0.5rem;
}

// ==========================================================================
//  Force du mot de passe
// ==========================================================================

.profile-view__password-strength {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.profile-view__password-strength-bar {
  width: 100%;
  height: 6px;
  background: var(--color-bg-input, #1e2a40);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
}

.profile-view__password-strength-fill {
  height: 100%;
  border-radius: var(--radius-full, 9999px);
  transition: width 0.3s ease, background 0.3s ease;

  &--weak { background: linear-gradient(90deg, #f44336, #e57373); }
  &--medium { background: linear-gradient(90deg, #ff9800, #ffb74d); }
  &--strong { background: linear-gradient(90deg, #4caf50, #81c784); }
}

.profile-view__password-strength-label {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  text-align: right;
}

// ==========================================================================
//  Sessions
// ==========================================================================

.profile-view__sessions-loading,
.profile-view__sessions-empty {
  padding: 1rem;
  text-align: center;
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
}

.profile-view__sessions {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.profile-view__session {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  transition: all 0.15s ease;

  &--current {
    border-color: var(--color-primary, #00d4ff);
    background: rgba(0, 212, 255, 0.05);
  }
}

.profile-view__session-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
}

.profile-view__session-info {
  flex: 1;
  min-width: 0;
}

.profile-view__session-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  margin-bottom: 0.2rem;
}

.profile-view__session-device {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-primary, #e8edf5);
}

.profile-view__session-current-badge {
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.1rem 0.4rem;
  border-radius: var(--radius-full, 9999px);
  background: var(--color-success, #4caf50);
  color: #ffffff;
}

.profile-view__session-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

.profile-view__session-revoke {
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  color: var(--color-text-muted, #6a7a9a);
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full, 9999px);
  cursor: pointer;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  flex-shrink: 0;

  &:hover:not(:disabled) {
    background: var(--color-error, #f44336);
    border-color: var(--color-error, #f44336);
    color: #ffffff;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// ==========================================================================
//  Préférences
// ==========================================================================

.profile-view__preferences {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.profile-view__preference {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--color-border-light, #253254);
  }
}

.profile-view__preference-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.profile-view__preference-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text-primary, #e8edf5);
}

.profile-view__preference-desc {
  font-size: 0.72rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.4;
}

.profile-view__preference-control {
  flex-shrink: 0;
}

.profile-view__select {
  padding: 0.4rem 0.7rem;
  font-size: 0.8rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  outline: none;
  min-width: 140px;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
  }
}

// ==========================================================================
//  Thème
// ==========================================================================

.profile-view__theme-options {
  display: flex;
  gap: 0.25rem;
}

.profile-view__theme-option {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.7rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }

  &--active {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
  }
}

// ==========================================================================
//  Toggle
// ==========================================================================

.profile-view__toggle {
  position: relative;
  display: inline-block;
  width: 42px;
  height: 24px;
  flex-shrink: 0;

  input {
    opacity: 0;
    width: 0;
    height: 0;

    &:checked + .profile-view__toggle-slider {
      background: var(--color-primary, #00d4ff);
      border-color: var(--color-primary, #00d4ff);

      &::before {
        transform: translateX(18px);
        background: #ffffff;
      }
    }

    &:focus-visible + .profile-view__toggle-slider {
      box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.25);
    }
  }
}

.profile-view__toggle-slider {
  position: absolute;
  inset: 0;
  background: var(--color-bg-input, #1e2a40);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-full, 9999px);
  cursor: pointer;
  transition: all 0.2s ease;

  &::before {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    left: 2px;
    top: 50%;
    transform: translateY(-50%);
    background: var(--color-text-muted, #6a7a9a);
    border-radius: 50%;
    transition: all 0.2s ease;
  }
}

// ==========================================================================
//  Delete account modal
// ==========================================================================

.profile-view__delete-account {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.profile-view__delete-account-warning {
  margin: 0;
  padding: 0.5rem 0.75rem;
  background: rgba(244, 67, 54, 0.1);
  border-left: 3px solid var(--color-error, #f44336);
  border-radius: var(--radius-sm, 4px);
  font-size: 0.78rem;
  color: var(--color-error, #f44336);
  line-height: 1.5;
}

.profile-view__delete-account-list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.8rem;
  color: var(--color-text-secondary, #b0c0d8);
  line-height: 1.6;
}

.profile-view__delete-account-confirm {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border, #1a2538);

  code {
    padding: 0.1rem 0.4rem;
    background: rgba(244, 67, 54, 0.1);
    color: var(--color-error, #f44336);
    border-radius: var(--radius-sm, 4px);
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 0.78rem;
  }
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 900px) {
  .profile-view__body {
    grid-template-columns: 1fr;
  }

  .profile-view__sidebar {
    position: static;
    max-height: none;
  }

  .profile-view__form-row {
    grid-template-columns: 1fr;
  }

  .profile-view__preference {
    flex-direction: column;
    align-items: stretch;
    gap: 0.6rem;
  }

  .profile-view__preference-control {
    width: 100%;
  }

  .profile-view__select {
    width: 100%;
  }

  .profile-view__theme-options {
    width: 100%;
  }

  .profile-view__theme-option {
    flex: 1;
    justify-content: center;
  }
}

@media (max-width: 600px) {
  .profile-view__header-content {
    flex-direction: column;
    align-items: flex-start;
    padding: 1.25rem;
  }

  .profile-view__header-actions {
    width: 100%;
  }

  .profile-view__header-actions > * {
    flex: 1;
  }

  .profile-view__avatar {
    width: 72px;
    height: 72px;
    font-size: 1.75rem;
  }

  .profile-view__name {
    font-size: 1.25rem;
  }

  .profile-view__tabs {
    gap: 0.15rem;
  }

  .profile-view__tab {
    padding: 0.4rem 0.6rem;
    font-size: 0.72rem;
  }

  .profile-view__section {
    padding: 1rem;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .profile-view__header,
  .profile-view__card,
  .profile-view__section {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .profile-view__card-header,
  .profile-view__tabs {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .profile-view__card-title,
  .profile-view__name,
  .profile-view__section-title,
  .profile-view__subsection-title,
  .profile-view__preference-label,
  .profile-view__stat-value {
    color: var(--color-text-primary, #1a1a2e);
  }

  .profile-view__form-input,
  .profile-view__form-textarea,
  .profile-view__select,
  .profile-view__theme-option {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .profile-view__quick-link:hover {
    background: var(--color-bg-hover, #e3e8ef);
  }

  .profile-view__tab:hover {
    background: var(--color-bg-hover, #e3e8ef);
    color: var(--color-text-primary, #1a1a2e);
  }

  .profile-view__session,
  .profile-view__preference {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .profile-view__session-device {
    color: var(--color-text-primary, #1a1a2e);
  }

  .profile-view__toggle-slider {
    background: var(--color-bg-input, #f0f2f5);
    border-color: var(--color-border, #d0d8e0);

    &::before {
      background: var(--color-text-muted, #7a8a9a);
    }
  }

  .profile-view__stat {
    border-color: var(--color-border, #d0d8e0);
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .profile-view__section,
  .profile-view__spinner {
    animation: none !important;
  }
}
</style>
