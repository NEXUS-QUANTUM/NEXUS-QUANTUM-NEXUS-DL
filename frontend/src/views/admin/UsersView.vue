<!-- ==========================================================================
  NexusDL 2.0 - Admin Users View (version complète)
  Fichier : frontend/src/views/admin/UsersView.vue
  Description : Console d'administration pour gérer les utilisateurs NexusDL :
                liste, création, modification, suppression, rôles, statuts,
                permissions, recherche, filtres et actions groupées.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="admin-users">
    <!-- ====================================================================
      EN-TÊTE — Titre, actions, statistiques
    ==================================================================== -->
    <header class="admin-users__header">
      <div class="admin-users__header-left">
        <h1 class="admin-users__title">
          <span aria-hidden="true">👥</span>
          Utilisateurs
        </h1>
        <p class="admin-users__subtitle">
          Gérez les comptes, les rôles et les permissions des utilisateurs
        </p>
      </div>

      <div class="admin-users__header-right">
        <!-- Recherche -->
        <div class="admin-users__search-wrapper">
          <span class="admin-users__search-icon" aria-hidden="true">🔍</span>
          <input
            ref="searchInputRef"
            type="text"
            class="admin-users__search-input"
            v-model="searchQuery"
            placeholder="Rechercher (nom, email)..."
            aria-label="Rechercher un utilisateur"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="admin-users__search-clear"
            @click="clearSearch"
            aria-label="Effacer la recherche"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <!-- Rafraîchir -->
        <button
          type="button"
          class="admin-users__btn admin-users__btn--refresh"
          :disabled="loading"
          @click="refreshUsers"
          aria-label="Rafraîchir la liste"
          title="Rafraîchir"
        >
          <span v-if="loading" class="admin-users__spinner" aria-hidden="true">⟳</span>
          <span v-else aria-hidden="true">↻</span>
          Rafraîchir
        </button>

        <!-- Nouvel utilisateur -->
        <button
          type="button"
          class="admin-users__btn admin-users__btn--primary"
          @click="openCreateModal"
          aria-label="Créer un nouvel utilisateur"
          title="Créer un utilisateur"
        >
          <span aria-hidden="true">➕</span>
          Nouvel utilisateur
        </button>
      </div>
    </header>

    <!-- ====================================================================
      BARRE D'ERREUR
    ==================================================================== -->
    <div v-if="error" class="admin-users__error" role="alert">
      <span class="admin-users__error-icon" aria-hidden="true">❌</span>
      <span class="admin-users__error-text">{{ error }}</span>
      <button
        type="button"
        class="admin-users__error-close"
        @click="error = null"
        aria-label="Fermer"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>

    <!-- ====================================================================
      BARRE DE STATISTIQUES
    ==================================================================== -->
    <div class="admin-users__stats">
      <div class="admin-users__stat">
        <span class="admin-users__stat-value">{{ totalUsers }}</span>
        <span class="admin-users__stat-label">Total</span>
      </div>
      <div class="admin-users__stat admin-users__stat--active">
        <span class="admin-users__stat-value">{{ statsCount.active }}</span>
        <span class="admin-users__stat-label">Actifs</span>
      </div>
      <div class="admin-users__stat admin-users__stat--inactive">
        <span class="admin-users__stat-value">{{ statsCount.inactive }}</span>
        <span class="admin-users__stat-label">Inactifs</span>
      </div>
      <div class="admin-users__stat admin-users__stat--banned">
        <span class="admin-users__stat-value">{{ statsCount.banned }}</span>
        <span class="admin-users__stat-label">Bannis</span>
      </div>
      <div class="admin-users__stat admin-users__stat--admin">
        <span class="admin-users__stat-value">{{ statsCount.admin }}</span>
        <span class="admin-users__stat-label">Admins</span>
      </div>
      <div class="admin-users__stat admin-users__stat--user">
        <span class="admin-users__stat-value">{{ statsCount.user }}</span>
        <span class="admin-users__stat-label">Utilisateurs</span>
      </div>
      <div class="admin-users__stat admin-users__stat--filtered">
        <span class="admin-users__stat-value">{{ filteredUsers.length }}</span>
        <span class="admin-users__stat-label">Affichés</span>
      </div>
    </div>

    <!-- ====================================================================
      FILTRES
    ==================================================================== -->
    <div class="admin-users__filters">
      <div class="admin-users__filter-group">
        <span class="admin-users__filter-label">Rôle :</span>
        <button
          v-for="filter in roleFilters"
          :key="filter.value"
          type="button"
          class="admin-users__filter-btn"
          :class="{ 'admin-users__filter-btn--active': roleFilter === filter.value }"
          @click="roleFilter = filter.value"
          :aria-pressed="roleFilter === filter.value"
        >
          <span aria-hidden="true">{{ filter.icon }}</span>
          {{ filter.label }}
        </button>
      </div>

      <div class="admin-users__filter-group">
        <span class="admin-users__filter-label">Statut :</span>
        <button
          v-for="filter in statusFilters"
          :key="filter.value"
          type="button"
          class="admin-users__filter-btn"
          :class="{ 'admin-users__filter-btn--active': statusFilter === filter.value }"
          @click="statusFilter = filter.value"
          :aria-pressed="statusFilter === filter.value"
        >
          <span aria-hidden="true">{{ filter.icon }}</span>
          {{ filter.label }}
        </button>
      </div>

      <div class="admin-users__filter-group admin-users__filter-group--right">
        <span class="admin-users__filter-label">Trier :</span>
        <select
          v-model="sortBy"
          class="admin-users__sort-select"
          aria-label="Trier les utilisateurs"
        >
          <option value="created-desc">Plus récents</option>
          <option value="created-asc">Plus anciens</option>
          <option value="username">Nom d'utilisateur (A-Z)</option>
          <option value="username-desc">Nom d'utilisateur (Z-A)</option>
          <option value="email">Email (A-Z)</option>
          <option value="last-login">Dernière connexion</option>
        </select>
      </div>
    </div>

    <!-- ====================================================================
      TABLEAU DES UTILISATEURS
    ==================================================================== -->
    <div class="admin-users__body">
      <!-- État de chargement -->
      <div v-if="loading && users.length === 0" class="admin-users__loading">
        <NexusSpinner size="lg" label="Chargement des utilisateurs..." />
      </div>

      <!-- État vide -->
      <div v-else-if="filteredUsers.length === 0" class="admin-users__empty">
        <span class="admin-users__empty-icon" aria-hidden="true">📭</span>
        <p class="admin-users__empty-text">
          {{ users.length === 0 ? 'Aucun utilisateur' : 'Aucun utilisateur ne correspond à vos filtres' }}
        </p>
        <button
          v-if="users.length > 0"
          type="button"
          class="admin-users__empty-reset"
          @click="resetFilters"
        >
          Réinitialiser les filtres
        </button>
      </div>

      <!-- Tableau -->
      <div v-else class="admin-users__table-wrapper">
        <table class="admin-users__table">
          <thead>
            <tr>
              <th class="admin-users__th admin-users__th--check">
                <input
                  type="checkbox"
                  :checked="allSelected"
                  :indeterminate.prop="someSelected && !allSelected"
                  @change="toggleSelectAll"
                  aria-label="Tout sélectionner"
                />
              </th>
              <th class="admin-users__th">Utilisateur</th>
              <th class="admin-users__th">Email</th>
              <th class="admin-users__th admin-users__th--center">Rôle</th>
              <th class="admin-users__th admin-users__th--center">Statut</th>
              <th class="admin-users__th admin-users__th--center">Créé le</th>
              <th class="admin-users__th admin-users__th--center">Dernière connexion</th>
              <th class="admin-users__th admin-users__th--actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="user in filteredUsers"
              :key="user.id"
              class="admin-users__tr"
              :class="{ 'admin-users__tr--selected': isSelected(user.id) }"
            >
              <td class="admin-users__td admin-users__td--check">
                <input
                  type="checkbox"
                  :checked="isSelected(user.id)"
                  @change="toggleSelect(user.id)"
                  :aria-label="`Sélectionner ${user.username}`"
                />
              </td>
              <td class="admin-users__td">
                <div class="admin-users__user-cell">
                  <span class="admin-users__avatar" :class="`admin-users__avatar--${user.role}`">
                    {{ getInitials(user.username) }}
                  </span>
                  <div class="admin-users__user-info">
                    <span class="admin-users__user-name">
                      {{ user.full_name || user.username }}
                    </span>
                    <span class="admin-users__user-username">@{{ user.username }}</span>
                  </div>
                </div>
              </td>
              <td class="admin-users__td">
                <a
                  :href="`mailto:${user.email}`"
                  class="admin-users__email"
                  :title="user.email"
                >
                  {{ user.email }}
                </a>
              </td>
              <td class="admin-users__td admin-users__td--center">
                <span
                  class="admin-users__badge"
                  :class="`admin-users__badge--role-${user.role}`"
                >
                  {{ getRoleIcon(user.role) }} {{ getRoleLabel(user.role) }}
                </span>
              </td>
              <td class="admin-users__td admin-users__td--center">
                <span
                  class="admin-users__badge"
                  :class="`admin-users__badge--status-${user.status}`"
                >
                  {{ getStatusIcon(user.status) }} {{ getStatusLabel(user.status) }}
                </span>
              </td>
              <td class="admin-users__td admin-users__td--center">
                <span class="admin-users__date" :title="formatDateTime(user.created_at)">
                  {{ formatRelativeTime(user.created_at) }}
                </span>
              </td>
              <td class="admin-users__td admin-users__td--center">
                <span
                  v-if="user.last_login"
                  class="admin-users__date"
                  :title="formatDateTime(user.last_login)"
                >
                  {{ formatRelativeTime(user.last_login) }}
                </span>
                <span v-else class="admin-users__text-muted">Jamais</span>
              </td>
              <td class="admin-users__td admin-users__td--actions">
                <button
                  type="button"
                  class="admin-users__action"
                  @click="openEditModal(user)"
                  title="Modifier"
                  aria-label="Modifier"
                >
                  <span aria-hidden="true">✏️</span>
                </button>
                <button
                  type="button"
                  class="admin-users__action"
                  @click="toggleUserStatus(user)"
                  :title="user.status === 'active' ? 'Désactiver' : 'Activer'"
                  :aria-label="user.status === 'active' ? 'Désactiver' : 'Activer'"
                >
                  <span aria-hidden="true">{{ user.status === 'active' ? '⏸️' : '▶️' }}</span>
                </button>
                <button
                  type="button"
                  class="admin-users__action"
                  @click="confirmResetPassword(user)"
                  title="Réinitialiser le mot de passe"
                  aria-label="Réinitialiser le mot de passe"
                >
                  <span aria-hidden="true">🔑</span>
                </button>
                <button
                  type="button"
                  class="admin-users__action admin-users__action--danger"
                  @click="confirmDelete(user)"
                  title="Supprimer"
                  aria-label="Supprimer"
                >
                  <span aria-hidden="true">🗑️</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ====================================================================
      BARRE D'ACTIONS GROUPÉES
    ==================================================================== -->
    <Transition name="admin-users-slide">
      <div v-if="selectedIds.length > 0" class="admin-users__bulk-actions">
        <span class="admin-users__bulk-info">
          {{ selectedIds.length }} utilisateur(s) sélectionné(s)
        </span>
        <div class="admin-users__bulk-buttons">
          <button
            type="button"
            class="admin-users__bulk-btn admin-users__bulk-btn--success"
            @click="bulkActivate"
            :disabled="actionLoading"
          >
            <span aria-hidden="true">✅</span> Activer
          </button>
          <button
            type="button"
            class="admin-users__bulk-btn admin-users__bulk-btn--warning"
            @click="bulkDeactivate"
            :disabled="actionLoading"
          >
            <span aria-hidden="true">⏸️</span> Désactiver
          </button>
          <button
            type="button"
            class="admin-users__bulk-btn admin-users__bulk-btn--danger"
            @click="bulkDelete"
            :disabled="actionLoading"
          >
            <span aria-hidden="true">🗑️</span> Supprimer
          </button>
          <button
            type="button"
            class="admin-users__bulk-btn admin-users__bulk-btn--neutral"
            @click="clearSelection"
          >
            <span aria-hidden="true">✖</span> Annuler
          </button>
        </div>
      </div>
    </Transition>

    <!-- ====================================================================
      PIED DE PAGE
    ==================================================================== -->
    <footer class="admin-users__footer">
      <span class="admin-users__footer-info">
        {{ filteredUsers.length }} / {{ users.length }} utilisateurs affichés
        <span v-if="searchQuery" class="admin-users__footer-highlight">
          · recherche : "{{ searchQuery }}"
        </span>
        <span v-if="roleFilter !== 'all'" class="admin-users__footer-highlight">
          · rôle : {{ roleFilter }}
        </span>
        <span v-if="statusFilter !== 'all'" class="admin-users__footer-highlight">
          · statut : {{ statusFilter }}
        </span>
      </span>
      <span v-if="lastUpdated" class="admin-users__footer-updated">
        Dernière mise à jour : {{ formatDateTime(lastUpdated) }}
      </span>
    </footer>

    <!-- ====================================================================
      MODALE — Création / Édition utilisateur
    ==================================================================== -->
    <NexusModal
      v-model="showEditModal"
      :title="editMode === 'create' ? '➕ Nouvel utilisateur' : '✏️ Modifier l\'utilisateur'"
      size="md"
      :loading="actionLoading"
      :show-footer="true"
    >
      <form class="admin-users__form" @submit.prevent="saveUser">
        <div class="admin-users__form-row">
          <NexusInput
            v-model="form.username"
            label="Nom d'utilisateur *"
            placeholder="ex: john_doe"
            left-icon="👤"
            required
            :disabled="editMode === 'edit'"
            :error="formErrors.username"
          />
        </div>

        <div class="admin-users__form-row">
          <NexusInput
            v-model="form.email"
            label="Email *"
            type="email"
            placeholder="ex: john@example.com"
            left-icon="📧"
            required
            :error="formErrors.email"
          />
        </div>

        <div class="admin-users__form-row">
          <NexusInput
            v-model="form.fullName"
            label="Nom complet"
            placeholder="ex: John Doe"
            left-icon="📝"
            :error="formErrors.fullName"
          />
        </div>

        <div v-if="editMode === 'create'" class="admin-users__form-row">
          <NexusInput
            v-model="form.password"
            label="Mot de passe *"
            type="password"
            placeholder="Minimum 6 caractères"
            left-icon="🔒"
            required
            :error="formErrors.password"
          />
        </div>

        <div class="admin-users__form-row admin-users__form-row--inline">
          <div class="admin-users__form-field">
            <label class="admin-users__form-label">Rôle</label>
            <select v-model="form.role" class="admin-users__form-select">
              <option value="user">👤 Utilisateur</option>
              <option value="admin">🛠️ Administrateur</option>
              <option value="guest">👁️ Invité</option>
            </select>
          </div>

          <div class="admin-users__form-field">
            <label class="admin-users__form-label">Statut</label>
            <select v-model="form.status" class="admin-users__form-select">
              <option value="active">✅ Actif</option>
              <option value="inactive">⏸️ Inactif</option>
              <option value="banned">🚫 Banni</option>
              <option value="pending">⏳ En attente</option>
            </select>
          </div>
        </div>

        <p v-if="formErrors.global" class="admin-users__form-error">
          ❌ {{ formErrors.global }}
        </p>
      </form>

      <template #footer>
        <NexusButton variant="neutral" @click="closeEditModal" :disabled="actionLoading">
          Annuler
        </NexusButton>
        <NexusButton
          variant="primary"
          :loading="actionLoading"
          @click="saveUser"
        >
          {{ editMode === 'create' ? 'Créer' : 'Sauvegarder' }}
        </NexusButton>
      </template>
    </NexusModal>

    <!-- ====================================================================
      MODALE — Confirmation générique
    ==================================================================== -->
    <NexusModal
      v-model="showConfirmModal"
      :title="confirmModalTitle"
      size="sm"
      confirmable
      :confirm-text="confirmModalConfirmText"
      :cancel-text="'Annuler'"
      :confirm-variant="confirmModalVariant"
      :loading="actionLoading"
      @confirm="executeConfirmedAction"
      @cancel="cancelConfirmedAction"
    >
      <p>{{ confirmModalMessage }}</p>
    </NexusModal>

    <!-- ====================================================================
      MODALE — Mot de passe temporaire affiché après réinitialisation
    ==================================================================== -->
    <NexusModal
      v-model="showPasswordModal"
      title="🔑 Mot de passe réinitialisé"
      size="sm"
      :show-close="true"
      :show-footer="true"
    >
      <div class="admin-users__password-modal">
        <p>Voici le nouveau mot de passe temporaire pour <strong>{{ passwordModalUser }}</strong> :</p>
        <div class="admin-users__password-box">
          <code class="admin-users__password-code">{{ generatedPassword }}</code>
          <button
            type="button"
            class="admin-users__password-copy"
            @click="copyPassword"
            aria-label="Copier le mot de passe"
            title="Copier"
          >
            <span aria-hidden="true">📋</span>
          </button>
        </div>
        <p class="admin-users__password-warning">
          ⚠️ Communiquez ce mot de passe à l'utilisateur de manière sécurisée.
          Il devra le changer à la prochaine connexion.
        </p>
      </div>

      <template #footer>
        <NexusButton variant="primary" @click="showPasswordModal = false">
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

import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusModal from '@/components/common/NexusModal.vue'
import NexusInput from '@/components/common/NexusInput.vue'
import NexusButton from '@/components/common/NexusButton.vue'
import { formatRelativeTime as fmtRelativeTime, truncate } from '@/utils/formatters'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const api = useApi()
const toast = useToast()
const authStore = useAuthStore()

// ==========================================================================
//  État réactif
// ==========================================================================

const users = ref([])
const loading = ref(false)
const actionLoading = ref(false)
const lastUpdated = ref(null)
const error = ref(null)
const searchQuery = ref('')
const roleFilter = ref('all')
const statusFilter = ref('all')
const sortBy = ref('created-desc')
const selectedIds = ref([])
const searchInputRef = ref(null)

// Modale édition / création
const showEditModal = ref(false)
const editMode = ref('create') // 'create' | 'edit'
const editingUserId = ref(null)
const form = reactive({
  username: '',
  email: '',
  fullName: '',
  password: '',
  role: 'user',
  status: 'active',
})
const formErrors = reactive({
  username: '',
  email: '',
  fullName: '',
  password: '',
  global: '',
})

// Modale de confirmation
const showConfirmModal = ref(false)
const confirmModalTitle = ref('')
const confirmModalMessage = ref('')
const confirmModalConfirmText = ref('Confirmer')
const confirmModalVariant = ref('primary')
let pendingAction = null

// Modale de mot de passe
const showPasswordModal = ref(false)
const generatedPassword = ref('')
const passwordModalUser = ref('')

let searchTimeout = null

// ==========================================================================
//  Options
// ==========================================================================

const roleFilters = [
  { value: 'all', label: 'Tous', icon: '👥' },
  { value: 'admin', label: 'Admins', icon: '🛠️' },
  { value: 'user', label: 'Utilisateurs', icon: '👤' },
  { value: 'guest', label: 'Invités', icon: '👁️' },
]

const statusFilters = [
  { value: 'all', label: 'Tous', icon: '📋' },
  { value: 'active', label: 'Actifs', icon: '✅' },
  { value: 'inactive', label: 'Inactifs', icon: '⏸️' },
  { value: 'banned', label: 'Bannis', icon: '🚫' },
  { value: 'pending', label: 'En attente', icon: '⏳' },
]

// ==========================================================================
//  Computed
// ==========================================================================

const totalUsers = computed(() => users.value.length)

const statsCount = computed(() => {
  const counts = {
    active: 0,
    inactive: 0,
    banned: 0,
    pending: 0,
    admin: 0,
    user: 0,
    guest: 0,
  }
  for (const u of users.value) {
    if (counts[u.status] !== undefined) counts[u.status]++
    if (counts[u.role] !== undefined) counts[u.role]++
  }
  return counts
})

const filteredUsers = computed(() => {
  let result = [...users.value]

  // Filtre rôle
  if (roleFilter.value !== 'all') {
    result = result.filter((u) => u.role === roleFilter.value)
  }

  // Filtre statut
  if (statusFilter.value !== 'all') {
    result = result.filter((u) => u.status === statusFilter.value)
  }

  // Recherche
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter((u) => {
      return (
        (u.username || '').toLowerCase().includes(q) ||
        (u.email || '').toLowerCase().includes(q) ||
        (u.full_name || '').toLowerCase().includes(q)
      )
    })
  }

  // Tri
  const [field, order] = sortBy.value.split('-')
  result.sort((a, b) => {
    let cmp = 0
    switch (field) {
      case 'username':
        cmp = (a.username || '').localeCompare(b.username || '')
        break
      case 'email':
        cmp = (a.email || '').localeCompare(b.email || '')
        break
      case 'last-login': {
        const ta = a.last_login ? new Date(a.last_login).getTime() : 0
        const tb = b.last_login ? new Date(b.last_login).getTime() : 0
        cmp = tb - ta
        break
      }
      case 'created':
      default: {
        const ta = a.created_at ? new Date(a.created_at).getTime() : 0
        const tb = b.created_at ? new Date(b.created_at).getTime() : 0
        cmp = tb - ta
        break
      }
    }
    return order === 'asc' ? -cmp : cmp
  })

  return result
})

const allSelected = computed(() => {
  if (filteredUsers.value.length === 0) return false
  return filteredUsers.value.every((u) => selectedIds.value.includes(u.id))
})

const someSelected = computed(() => selectedIds.value.length > 0)

// ==========================================================================
//  Méthodes — Récupération
// ==========================================================================

async function fetchUsers() {
  loading.value = true
  error.value = null
  try {
    const response = await api.get('/admin/users')
    let raw = []
    if (Array.isArray(response)) raw = response
    else if (Array.isArray(response?.users)) raw = response.users
    else if (Array.isArray(response?.items)) raw = response.items
    users.value = raw.map((u) => normalizeUser(u))
    lastUpdated.value = new Date().toISOString()
  } catch (err) {
    console.error('Erreur chargement utilisateurs:', err)
    error.value = `Impossible de charger les utilisateurs : ${err.message}`
    toast.error(error.value, '❌')
  } finally {
    loading.value = false
  }
}

async function refreshUsers() {
  toast.info('Rafraîchissement des utilisateurs...', '🔄', 1500)
  await fetchUsers()
}

function normalizeUser(raw) {
  return {
    id: raw.id,
    username: raw.username || '',
    email: raw.email || '',
    full_name: raw.full_name || '',
    role: raw.role || 'user',
    status: raw.status || 'active',
    avatar_url: raw.avatar_url || null,
    created_at: raw.created_at || null,
    updated_at: raw.updated_at || null,
    last_login: raw.last_login || null,
  }
}

// ==========================================================================
//  Méthodes — Sélection
// ==========================================================================

function isSelected(id) {
  return selectedIds.value.includes(id)
}

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) selectedIds.value.push(id)
  else selectedIds.value.splice(idx, 1)
}

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = filteredUsers.value.map((u) => u.id)
  }
}

function clearSelection() {
  selectedIds.value = []
}

// ==========================================================================
//  Méthodes — CRUD
// ==========================================================================

function openCreateModal() {
  editMode.value = 'create'
  editingUserId.value = null
  Object.assign(form, {
    username: '',
    email: '',
    fullName: '',
    password: '',
    role: 'user',
    status: 'active',
  })
  resetFormErrors()
  showEditModal.value = true
}

function openEditModal(user) {
  editMode.value = 'edit'
  editingUserId.value = user.id
  Object.assign(form, {
    username: user.username,
    email: user.email,
    fullName: user.full_name || '',
    password: '',
    role: user.role,
    status: user.status,
  })
  resetFormErrors()
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  resetFormErrors()
}

function resetFormErrors() {
  formErrors.username = ''
  formErrors.email = ''
  formErrors.fullName = ''
  formErrors.password = ''
  formErrors.global = ''
}

function validateForm() {
  resetFormErrors()
  let valid = true

  if (!form.username || form.username.length < 3) {
    formErrors.username = "Le nom d'utilisateur doit contenir au moins 3 caractères"
    valid = false
  }
  if (!form.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    formErrors.email = 'Email invalide'
    valid = false
  }
  if (editMode.value === 'create') {
    if (!form.password || form.password.length < 6) {
      formErrors.password = 'Le mot de passe doit contenir au moins 6 caractères'
      valid = false
    }
  }
  return valid
}

async function saveUser() {
  if (!validateForm()) {
    formErrors.global = 'Veuillez corriger les erreurs ci-dessus'
    return
  }

  actionLoading.value = true
  try {
    if (editMode.value === 'create') {
      const payload = {
        username: form.username,
        email: form.email,
        password: form.password,
        full_name: form.fullName,
        role: form.role,
        status: form.status,
      }
      const response = await api.post('/admin/users', payload)
      const newUser = normalizeUser(response.user || response)
      users.value.unshift(newUser)
      toast.success(`Utilisateur "${newUser.username}" créé`, '✅')
    } else {
      const payload = {
        email: form.email,
        full_name: form.fullName,
        role: form.role,
        status: form.status,
      }
      const response = await api.patch(`/admin/users/${editingUserId.value}`, payload)
      const updated = normalizeUser(response.user || response)
      const idx = users.value.findIndex((u) => u.id === editingUserId.value)
      if (idx !== -1) users.value[idx] = updated
      toast.success(`Utilisateur "${updated.username}" mis à jour`, '✅')
    }
    closeEditModal()
  } catch (err) {
    formErrors.global = err.message || 'Une erreur est survenue'
    toast.error(formErrors.global, '❌')
  } finally {
    actionLoading.value = false
  }
}

async function toggleUserStatus(user) {
  const newStatus = user.status === 'active' ? 'inactive' : 'active'
  const previous = user.status
  user.status = newStatus

  try {
    await api.patch(`/admin/users/${user.id}`, { status: newStatus })
    toast.success(
      `Utilisateur "${user.username}" ${newStatus === 'active' ? 'activé' : 'désactivé'}`,
      newStatus === 'active' ? '✅' : '⏸️'
    )
  } catch (err) {
    user.status = previous
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

function confirmDelete(user) {
  confirmModalTitle.value = 'Supprimer un utilisateur'
  confirmModalMessage.value = `Êtes-vous sûr de vouloir supprimer définitivement "${user.username}" ? Cette action est irréversible.`
  confirmModalConfirmText.value = 'Supprimer'
  confirmModalVariant.value = 'error'
  pendingAction = async () => {
    try {
      await api.delete(`/admin/users/${user.id}`)
      const idx = users.value.findIndex((u) => u.id === user.id)
      if (idx !== -1) users.value.splice(idx, 1)
      toast.success(`Utilisateur "${user.username}" supprimé`, '🗑️')
    } catch (err) {
      toast.error(`Erreur : ${err.message}`, '❌')
    }
  }
  showConfirmModal.value = true
}

function confirmResetPassword(user) {
  confirmModalTitle.value = 'Réinitialiser le mot de passe'
  confirmModalMessage.value = `Générer un nouveau mot de passe temporaire pour "${user.username}" ?`
  confirmModalConfirmText.value = 'Réinitialiser'
  confirmModalVariant.value = 'warning'
  pendingAction = async () => {
    try {
      const response = await api.post(`/admin/users/${user.id}/reset-password`)
      const password = response.password || response.new_password || generateRandomPassword()
      generatedPassword.value = password
      passwordModalUser.value = user.username
      showPasswordModal.value = true
      toast.success('Mot de passe réinitialisé', '🔑')
    } catch (err) {
      toast.error(`Erreur : ${err.message}`, '❌')
    }
  }
  showConfirmModal.value = true
}

// ==========================================================================
//  Méthodes — Actions groupées
// ==========================================================================

async function bulkActivate() {
  if (selectedIds.value.length === 0) return
  actionLoading.value = true
  try {
    await Promise.all(
      selectedIds.value.map((id) =>
        api.patch(`/admin/users/${id}`, { status: 'active' }).catch(() => null)
      )
    )
    for (const u of users.value) {
      if (selectedIds.value.includes(u.id)) u.status = 'active'
    }
    toast.success(`${selectedIds.value.length} utilisateur(s) activé(s)`, '✅')
    clearSelection()
  } finally {
    actionLoading.value = false
  }
}

async function bulkDeactivate() {
  if (selectedIds.value.length === 0) return
  actionLoading.value = true
  try {
    await Promise.all(
      selectedIds.value.map((id) =>
        api.patch(`/admin/users/${id}`, { status: 'inactive' }).catch(() => null)
      )
    )
    for (const u of users.value) {
      if (selectedIds.value.includes(u.id)) u.status = 'inactive'
    }
    toast.success(`${selectedIds.value.length} utilisateur(s) désactivé(s)`, '⏸️')
    clearSelection()
  } finally {
    actionLoading.value = false
  }
}

function bulkDelete() {
  if (selectedIds.value.length === 0) return
  confirmModalTitle.value = 'Supprimer des utilisateurs'
  confirmModalMessage.value = `Êtes-vous sûr de vouloir supprimer définitivement ${selectedIds.value.length} utilisateur(s) ? Cette action est irréversible.`
  confirmModalConfirmText.value = 'Supprimer'
  confirmModalVariant.value = 'error'
  pendingAction = async () => {
    actionLoading.value = true
    try {
      await Promise.all(
        selectedIds.value.map((id) => api.delete(`/admin/users/${id}`).catch(() => null))
      )
      users.value = users.value.filter((u) => !selectedIds.value.includes(u.id))
      toast.success(`${selectedIds.value.length} utilisateur(s) supprimé(s)`, '🗑️')
      clearSelection()
    } finally {
      actionLoading.value = false
    }
  }
  showConfirmModal.value = true
}

// ==========================================================================
//  Méthodes — Confirmation
// ==========================================================================

async function executeConfirmedAction() {
  if (!pendingAction) return
  actionLoading.value = true
  try {
    await pendingAction()
  } finally {
    actionLoading.value = false
    pendingAction = null
    showConfirmModal.value = false
  }
}

function cancelConfirmedAction() {
  pendingAction = null
  showConfirmModal.value = false
}

// ==========================================================================
//  Méthodes — Filtres
// ==========================================================================

function clearSearch() {
  searchQuery.value = ''
  searchInputRef.value?.focus()
}

function resetFilters() {
  searchQuery.value = ''
  roleFilter.value = 'all'
  statusFilter.value = 'all'
  sortBy.value = 'created-desc'
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
  const map = { admin: 'Admin', user: 'Utilisateur', guest: 'Invité' }
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
  if (!date) return ''
  try {
    return fmtRelativeTime(date)
  } catch (_) {
    return ''
  }
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

function generateRandomPassword(length = 12) {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%'
  let pwd = ''
  for (let i = 0; i < length; i++) {
    pwd += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return pwd
}

async function copyPassword() {
  try {
    await navigator.clipboard.writeText(generatedPassword.value)
    toast.success('Mot de passe copié', '📋')
  } catch (_) {
    toast.error('Impossible de copier', '❌')
  }
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  await fetchUsers()
})

onUnmounted(() => {
  clearTimeout(searchTimeout)
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.admin-users {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  position: relative;
}

// ==========================================================================
//  Header
// ==========================================================================

.admin-users__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.admin-users__header-left {
  flex: 1;
  min-width: 200px;
}

.admin-users__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.admin-users__subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.admin-users__header-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

// ==========================================================================
//  Recherche
// ==========================================================================

.admin-users__search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 220px;
}

.admin-users__search-icon {
  position: absolute;
  left: 0.5rem;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
}

.admin-users__search-input {
  width: 100%;
  padding: 0.4rem 0.5rem 0.4rem 1.9rem;
  font-size: 0.8rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15);
  }

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.admin-users__search-clear {
  position: absolute;
  right: 0.3rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0 0.3rem;
  &:hover {
    color: var(--color-text-primary, #e8edf5);
  }
}

// ==========================================================================
//  Boutons
// ==========================================================================

.admin-users__btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.7rem;
  font-size: 0.75rem;
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

  &--refresh:hover:not(:disabled) {
    border-color: var(--color-info, #2196f3);
    color: var(--color-info, #2196f3);
  }

  &--primary {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);

    &:hover:not(:disabled) {
      filter: brightness(1.1);
      color: var(--color-text-inverse, #0a0e1a);
    }
  }
}

.admin-users__spinner {
  display: inline-block;
  animation: adminUsersSpin 0.8s linear infinite;
}

@keyframes adminUsersSpin {
  to {
    transform: rotate(360deg);
  }
}

// ==========================================================================
//  Barre d'erreur
// ==========================================================================

.admin-users__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid var(--color-error, #f44336);
  border-radius: var(--radius-md, 8px);
  color: var(--color-error, #f44336);
  font-size: 0.85rem;
}

.admin-users__error-icon {
  flex-shrink: 0;
}

.admin-users__error-text {
  flex: 1;
}

.admin-users__error-close {
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0 0.3rem;
  border-radius: var(--radius-sm, 4px);
  &:hover {
    background: rgba(244, 67, 54, 0.15);
  }
}

// ==========================================================================
//  Statistiques
// ==========================================================================

.admin-users__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.admin-users__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.3rem 0.7rem;
  border-radius: var(--radius-sm, 4px);
  background: var(--color-bg-card, #1a2538);
  min-width: 60px;

  &--active { border-left: 3px solid #4caf50; }
  &--inactive { border-left: 3px solid #6a7a9a; }
  &--banned { border-left: 3px solid #f44336; }
  &--admin { border-left: 3px solid #ff9800; }
  &--user { border-left: 3px solid #2196f3; }
  &--filtered { border-left: 3px solid var(--color-primary, #00d4ff); }
}

.admin-users__stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  font-variant-numeric: tabular-nums;
}

.admin-users__stat-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  color: var(--color-text-muted, #6a7a9a);
  letter-spacing: 0.05em;
}

// ==========================================================================
//  Filtres
// ==========================================================================

.admin-users__filters {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.admin-users__filter-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;

  &--right {
    margin-left: auto;
  }
}

.admin-users__filter-label {
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
  font-weight: 500;
  margin-right: 0.25rem;
}

.admin-users__filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.25rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--color-bg-card, #1a2538);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
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

.admin-users__sort-select {
  padding: 0.3rem 0.6rem;
  font-size: 0.75rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  outline: none;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
  }
}

// ==========================================================================
//  Tableau
// ==========================================================================

.admin-users__table-wrapper {
  overflow-x: auto;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
}

.admin-users__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.admin-users__th {
  padding: 0.6rem 0.75rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #6a7a9a);
  border-bottom: 1px solid var(--color-border, #1a2538);
  background: var(--color-bg-secondary, #141a2b);
  white-space: nowrap;

  &--center { text-align: center; }
  &--check { width: 40px; text-align: center; }
  &--actions { width: 160px; text-align: right; }
}

.admin-users__tr {
  transition: background 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }

  &--selected {
    background: rgba(0, 212, 255, 0.08);
  }

  &:last-child .admin-users__td {
    border-bottom: none;
  }
}

.admin-users__td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
  color: var(--color-text-secondary, #b0c0d8);
  vertical-align: middle;

  &--center { text-align: center; }
  &--check { text-align: center; }
  &--actions { text-align: right; white-space: nowrap; }
}

.admin-users__user-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.admin-users__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;

  &--admin {
    background: linear-gradient(135deg, #ff9800, #f57c00);
    color: #ffffff;
  }

  &--user {
    background: linear-gradient(135deg, #00d4ff, #0066ff);
    color: #ffffff;
  }

  &--guest {
    background: linear-gradient(135deg, #6a7a9a, #4a5a72);
    color: #ffffff;
  }
}

.admin-users__user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.admin-users__user-name {
  font-weight: 500;
  color: var(--color-text-primary, #e8edf5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.admin-users__user-username {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

.admin-users__email {
  color: var(--color-primary, #00d4ff);
  text-decoration: none;
  font-size: 0.75rem;
  &:hover {
    text-decoration: underline;
  }
}

.admin-users__badge {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.15rem 0.5rem;
  font-size: 0.65rem;
  font-weight: 600;
  border-radius: var(--radius-sm, 4px);
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
    border: 1px solid rgba(106, 122, 154, 0.3);
  }
  &--status-banned {
    background: rgba(244, 67, 54, 0.15);
    color: #f44336;
    border: 1px solid rgba(244, 67, 54, 0.3);
  }
  &--status-pending {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
    border: 1px solid rgba(255, 152, 0, 0.3);
  }
}

.admin-users__date {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  cursor: help;
}

.admin-users__text-muted {
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.75rem;
}

.admin-users__action {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.2rem 0.35rem;
  border-radius: var(--radius-sm, 4px);
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &--danger:hover {
    color: var(--color-error, #f44336);
  }
}

// ==========================================================================
//  États
// ==========================================================================

.admin-users__loading,
.admin-users__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: var(--color-text-muted, #6a7a9a);
  text-align: center;
  gap: 0.5rem;
  min-height: 250px;
}

.admin-users__empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.admin-users__empty-text {
  margin: 0;
  font-size: 0.95rem;
}

.admin-users__empty-reset {
  margin-top: 0.5rem;
  padding: 0.3rem 0.8rem;
  font-size: 0.75rem;
  background: var(--color-primary, #00d4ff);
  color: var(--color-text-inverse, #0a0e1a);
  border: none;
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  font-weight: 500;
  &:hover {
    filter: brightness(1.1);
  }
}

// ==========================================================================
//  Actions groupées
// ==========================================================================

.admin-users__bulk-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.6rem 0.9rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-primary, #00d4ff);
  border-radius: var(--radius-md, 8px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  position: sticky;
  bottom: 1rem;
  z-index: 10;
}

.admin-users__bulk-info {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-primary, #e8edf5);
}

.admin-users__bulk-buttons {
  display: flex;
  gap: 0.3rem;
  flex-wrap: wrap;
}

.admin-users__bulk-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &--success:hover:not(:disabled) {
    border-color: #4caf50;
    color: #4caf50;
  }
  &--warning:hover:not(:disabled) {
    border-color: #ff9800;
    color: #ff9800;
  }
  &--danger:hover:not(:disabled) {
    border-color: #f44336;
    color: #f44336;
  }
  &--neutral:hover:not(:disabled) {
    border-color: var(--color-border-light, #253254);
  }
}

.admin-users-slide-enter-active,
.admin-users-slide-leave-active {
  transition: all 0.25s ease;
}

.admin-users-slide-enter-from,
.admin-users-slide-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

// ==========================================================================
//  Formulaire (modale)
// ==========================================================================

.admin-users__form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.admin-users__form-row {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;

  &--inline {
    flex-direction: row;
    gap: 0.75rem;
  }
}

.admin-users__form-field {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.admin-users__form-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-secondary, #b0c0d8);
}

.admin-users__form-select {
  padding: 0.5rem 0.7rem;
  font-size: 0.85rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  cursor: pointer;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15);
  }
}

.admin-users__form-error {
  margin: 0;
  padding: 0.5rem 0.75rem;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid var(--color-error, #f44336);
  border-radius: var(--radius-md, 8px);
  color: var(--color-error, #f44336);
  font-size: 0.8rem;
}

// ==========================================================================
//  Modale mot de passe
// ==========================================================================

.admin-users__password-modal {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  text-align: center;
}

.admin-users__password-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.7rem 1rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px dashed var(--color-primary, #00d4ff);
  border-radius: var(--radius-md, 8px);
}

.admin-users__password-code {
  flex: 1;
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-primary, #00d4ff);
  letter-spacing: 0.05em;
  word-break: break-all;
  text-align: left;
}

.admin-users__password-copy {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  padding: 0.3rem;
  border-radius: var(--radius-sm, 4px);
  font-size: 1rem;

  &:hover {
    color: var(--color-primary, #00d4ff);
    background: var(--color-bg-hover, #253254);
  }
}

.admin-users__password-warning {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-warning, #ff9800);
  line-height: 1.5;
}

// ==========================================================================
//  Footer
// ==========================================================================

.admin-users__footer {
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

.admin-users__footer-info {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.admin-users__footer-highlight {
  color: var(--color-primary, #00d4ff);
  font-weight: 500;
}

.admin-users__footer-updated {
  font-style: italic;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 768px) {
  .admin-users__header {
    flex-direction: column;
  }

  .admin-users__header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .admin-users__search-wrapper {
    flex: 1;
    min-width: 0;
  }

  .admin-users__filters {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .admin-users__filter-group {
    width: 100%;
    overflow-x: auto;
    padding-bottom: 0.2rem;

    &--right {
      margin-left: 0;
    }
  }

  .admin-users__table {
    font-size: 0.7rem;
  }

  .admin-users__th,
  .admin-users__td {
    padding: 0.4rem 0.5rem;
  }

  .admin-users__bulk-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .admin-users__bulk-buttons {
    justify-content: center;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .admin-users__search-input,
  .admin-users__sort-select,
  .admin-users__form-select {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .admin-users__table-wrapper {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-users__th {
    background: var(--color-bg-secondary, #e9ecf2);
    color: var(--color-text-muted, #7a8a9a);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-users__td {
    border-color: var(--color-border, #d0d8e0);
    color: var(--color-text-secondary, #3d4a5c);
  }

  .admin-users__tr:hover {
    background: var(--color-bg-hover, #e3e8ef);
  }

  .admin-users__user-name {
    color: var(--color-text-primary, #1a1a2e);
  }

  .admin-users__filter-btn {
    background: var(--color-bg-card, #ffffff);
    color: var(--color-text-secondary, #3d4a5c);
    border-color: var(--color-border, #d0d8e0);

    &:hover {
      background: var(--color-bg-hover, #e3e8ef);
    }

    &--active {
      background: var(--color-primary, #0066cc);
      color: #ffffff;
    }
  }

  .admin-users__bulk-actions {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-primary, #0066cc);
  }

  .admin-users__bulk-btn {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-users__password-box {
    background: var(--color-bg-secondary, #e9ecf2);
  }
}
</style>
