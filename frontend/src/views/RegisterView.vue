<!-- ==========================================================================
  NexusDL 2.0 - Register View (version complète)
  Fichier : frontend/src/views/RegisterView.vue
  Description : Page d'inscription avec validation complète, indicateur de
                force du mot de passe, acceptation des CGU, gestion d'erreurs,
                OAuth (optionnel), redirection post-inscription, animations,
                thème clair/sombre et accessibilité.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="register-view">
    <!-- ====================================================================
      DÉCORATIONS DE FOND
    ==================================================================== -->
    <div class="register-view__bg" aria-hidden="true">
      <div class="register-view__bg-grid" />
      <div class="register-view__bg-glow register-view__bg-glow--1" />
      <div class="register-view__bg-glow register-view__bg-glow--2" />
    </div>

    <!-- ====================================================================
      CONTENU PRINCIPAL
    ==================================================================== -->
    <div class="register-view__content">
      <!-- ================================================================
        BRAND
      ================================================================ -->
      <div class="register-view__brand">
        <router-link to="/" class="register-view__brand-link" aria-label="Accueil NexusDL">
          <span class="register-view__brand-icon" aria-hidden="true">🧬</span>
          <span class="register-view__brand-name">NexusDL</span>
        </router-link>
        <p class="register-view__brand-tagline">
          Créez votre compte en quelques secondes
        </p>
      </div>

      <!-- ================================================================
        CARTE D'INSCRIPTION
      ================================================================ -->
      <div class="register-view__card" :class="{ 'register-view__card--shake': shakeForm }">
        <!-- Barre de progression -->
        <div class="register-view__progress">
          <div
            class="register-view__progress-bar"
            :style="{ width: `${formCompletion}%` }"
          />
        </div>

        <!-- En-tête -->
        <header class="register-view__header">
          <h1 class="register-view__title">Inscription</h1>
          <p class="register-view__subtitle">
            Rejoignez NexusDL et commencez à télécharger vos scans préférés
          </p>
        </header>

        <!-- Alerte d'erreur -->
        <div
          v-if="errorMessage"
          class="register-view__alert register-view__alert--error"
          role="alert"
        >
          <span class="register-view__alert-icon" aria-hidden="true">❌</span>
          <span class="register-view__alert-text">{{ errorMessage }}</span>
          <button
            type="button"
            class="register-view__alert-close"
            @click="clearError"
            aria-label="Fermer le message d'erreur"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <!-- Alerte de succès -->
        <div
          v-if="successMessage"
          class="register-view__alert register-view__alert--success"
          role="status"
        >
          <span class="register-view__alert-icon" aria-hidden="true">✅</span>
          <span class="register-view__alert-text">{{ successMessage }}</span>
        </div>

        <!-- ==============================================================
          FORMULAIRE
        ============================================================== -->
        <form
          class="register-view__form"
          @submit.prevent="handleRegister"
          novalidate
          autocomplete="on"
        >
          <!-- Champ : nom d'utilisateur -->
          <div class="register-view__field">
            <label for="username" class="register-view__label">
              Nom d'utilisateur
              <span class="register-view__label-required" aria-hidden="true">*</span>
            </label>
            <div class="register-view__input-wrapper">
              <span class="register-view__input-icon" aria-hidden="true">👤</span>
              <input
                id="username"
                ref="usernameInputRef"
                v-model="form.username"
                type="text"
                class="register-view__input"
                :class="{ 'register-view__input--error': fieldErrors.username, 'register-view__input--valid': isUsernameValid }"
                placeholder="Choisissez un nom d'utilisateur"
                autocomplete="username"
                autofocus
                required
                :disabled="loading"
                aria-describedby="username-error"
                :aria-invalid="!!fieldErrors.username"
                maxlength="50"
                @input="onUsernameInput"
                @blur="validateUsername"
              />
              <span
                v-if="isUsernameValid && !fieldErrors.username"
                class="register-view__input-status register-view__input-status--valid"
                aria-hidden="true"
              >
                ✓
              </span>
            </div>
            <p
              v-if="fieldErrors.username"
              id="username-error"
              class="register-view__field-error"
              role="alert"
            >
              ❌ {{ fieldErrors.username }}
            </p>
            <p v-else class="register-view__field-hint">
              3 à 50 caractères. Lettres, chiffres, tirets et underscores uniquement.
            </p>
          </div>

          <!-- Champ : email -->
          <div class="register-view__field">
            <label for="email" class="register-view__label">
              Adresse email
              <span class="register-view__label-required" aria-hidden="true">*</span>
            </label>
            <div class="register-view__input-wrapper">
              <span class="register-view__input-icon" aria-hidden="true">📧</span>
              <input
                id="email"
                ref="emailInputRef"
                v-model="form.email"
                type="email"
                class="register-view__input"
                :class="{ 'register-view__input--error': fieldErrors.email, 'register-view__input--valid': isEmailValid }"
                placeholder="votre@email.com"
                autocomplete="email"
                required
                :disabled="loading"
                aria-describedby="email-error"
                :aria-invalid="!!fieldErrors.email"
                maxlength="100"
                @input="onEmailInput"
                @blur="validateEmail"
              />
              <span
                v-if="isEmailValid && !fieldErrors.email"
                class="register-view__input-status register-view__input-status--valid"
                aria-hidden="true"
              >
                ✓
              </span>
            </div>
            <p
              v-if="fieldErrors.email"
              id="email-error"
              class="register-view__field-error"
              role="alert"
            >
              ❌ {{ fieldErrors.email }}
            </p>
          </div>

          <!-- Champ : nom complet (optionnel) -->
          <div class="register-view__field">
            <label for="fullName" class="register-view__label">
              Nom complet
              <span class="register-view__label-optional">(optionnel)</span>
            </label>
            <div class="register-view__input-wrapper">
              <span class="register-view__input-icon" aria-hidden="true">📝</span>
              <input
                id="fullName"
                v-model="form.fullName"
                type="text"
                class="register-view__input"
                placeholder="Votre nom complet"
                autocomplete="name"
                :disabled="loading"
                maxlength="100"
              />
            </div>
          </div>

          <!-- Champ : mot de passe -->
          <div class="register-view__field">
            <label for="password" class="register-view__label">
              Mot de passe
              <span class="register-view__label-required" aria-hidden="true">*</span>
            </label>
            <div class="register-view__input-wrapper">
              <span class="register-view__input-icon" aria-hidden="true">🔒</span>
              <input
                id="password"
                ref="passwordInputRef"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                class="register-view__input register-view__input--with-action"
                :class="{ 'register-view__input--error': fieldErrors.password }"
                placeholder="Créez un mot de passe fort"
                autocomplete="new-password"
                required
                :disabled="loading"
                aria-describedby="password-error password-strength"
                :aria-invalid="!!fieldErrors.password"
                @input="onPasswordInput"
              />
              <button
                type="button"
                class="register-view__input-action"
                @click="togglePasswordVisibility"
                :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
                :title="showPassword ? 'Masquer' : 'Afficher'"
                tabindex="-1"
              >
                <span aria-hidden="true">{{ showPassword ? '🙈' : '👁️' }}</span>
              </button>
            </div>

            <!-- Indicateur de force -->
            <div
              v-if="form.password"
              id="password-strength"
              class="register-view__password-strength"
            >
              <div class="register-view__password-strength-bars">
                <div
                  v-for="i in 4"
                  :key="i"
                  class="register-view__password-strength-bar"
                  :class="{
                    'register-view__password-strength-bar--filled': i <= passwordStrength.score,
                    [`register-view__password-strength-bar--${passwordStrength.level}`]: i <= passwordStrength.score,
                  }"
                />
              </div>
              <span
                class="register-view__password-strength-label"
                :class="`register-view__password-strength-label--${passwordStrength.level}`"
              >
                Force : {{ passwordStrength.label }}
              </span>
            </div>

            <p
              v-if="fieldErrors.password"
              id="password-error"
              class="register-view__field-error"
              role="alert"
            >
              ❌ {{ fieldErrors.password }}
            </p>

            <!-- Critères du mot de passe -->
            <ul v-if="form.password && passwordStrength.score < 4" class="register-view__password-criteria">
              <li
                class="register-view__password-criterion"
                :class="{ 'register-view__password-criterion--ok': passwordCriteria.length }"
              >
                {{ passwordCriteria.length ? '✓' : '○' }} Au moins 6 caractères
              </li>
              <li
                class="register-view__password-criterion"
                :class="{ 'register-view__password-criterion--ok': passwordCriteria.uppercase }"
              >
                {{ passwordCriteria.uppercase ? '✓' : '○' }} Une majuscule
              </li>
              <li
                class="register-view__password-criterion"
                :class="{ 'register-view__password-criterion--ok': passwordCriteria.digit }"
              >
                {{ passwordCriteria.digit ? '✓' : '○' }} Un chiffre
              </li>
              <li
                class="register-view__password-criterion"
                :class="{ 'register-view__password-criterion--ok': passwordCriteria.special }"
              >
                {{ passwordCriteria.special ? '✓' : '○' }} Un caractère spécial
              </li>
            </ul>
          </div>

          <!-- Champ : confirmation du mot de passe -->
          <div class="register-view__field">
            <label for="confirmPassword" class="register-view__label">
              Confirmer le mot de passe
              <span class="register-view__label-required" aria-hidden="true">*</span>
            </label>
            <div class="register-view__input-wrapper">
              <span class="register-view__input-icon" aria-hidden="true">🔐</span>
              <input
                id="confirmPassword"
                ref="confirmPasswordInputRef"
                v-model="form.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                class="register-view__input register-view__input--with-action"
                :class="{
                  'register-view__input--error': fieldErrors.confirmPassword,
                  'register-view__input--valid': isConfirmValid && form.confirmPassword,
                }"
                placeholder="Retapez votre mot de passe"
                autocomplete="new-password"
                required
                :disabled="loading"
                aria-describedby="confirm-error"
                :aria-invalid="!!fieldErrors.confirmPassword"
                @input="clearFieldError('confirmPassword')"
              />
              <button
                type="button"
                class="register-view__input-action"
                @click="toggleConfirmPasswordVisibility"
                :aria-label="showConfirmPassword ? 'Masquer la confirmation' : 'Afficher la confirmation'"
                tabindex="-1"
              >
                <span aria-hidden="true">{{ showConfirmPassword ? '🙈' : '👁️' }}</span>
              </button>
              <span
                v-if="isConfirmValid && form.confirmPassword"
                class="register-view__input-status register-view__input-status--valid"
                aria-hidden="true"
              >
                ✓
              </span>
            </div>
            <p
              v-if="fieldErrors.confirmPassword"
              id="confirm-error"
              class="register-view__field-error"
              role="alert"
            >
              ❌ {{ fieldErrors.confirmPassword }}
            </p>
          </div>

          <!-- Acceptation des CGU -->
          <div class="register-view__field register-view__field--checkbox">
            <label class="register-view__checkbox">
              <input
                v-model="form.acceptTerms"
                type="checkbox"
                :disabled="loading"
                required
              />
              <span class="register-view__checkbox-mark" aria-hidden="true" />
              <span class="register-view__checkbox-label">
                J'accepte les
                <router-link to="/terms" class="register-view__checkbox-link" @click.stop>
                  conditions d'utilisation
                </router-link>
                et la
                <router-link to="/privacy" class="register-view__checkbox-link" @click.stop>
                  politique de confidentialité
                </router-link>
              </span>
            </label>
            <p
              v-if="fieldErrors.acceptTerms"
              class="register-view__field-error"
              role="alert"
            >
              ❌ {{ fieldErrors.acceptTerms }}
            </p>
          </div>

          <!-- Bouton d'inscription -->
          <NexusButton
            type="submit"
            variant="primary"
            size="lg"
            block
            :loading="loading"
            :disabled="!isFormValid"
            class="register-view__submit"
          >
            <span v-if="loading">Création du compte...</span>
            <span v-else>🎉 Créer mon compte</span>
          </NexusButton>
        </form>

        <!-- ==============================================================
          SÉPARATEUR (si OAuth activé)
        ============================================================== -->
        <template v-if="oauthEnabled">
          <div class="register-view__divider">
            <span>ou s'inscrire avec</span>
          </div>

          <div class="register-view__oauth">
            <button
              v-for="provider in oauthProviders"
              :key="provider.id"
              type="button"
              class="register-view__oauth-btn"
              :class="`register-view__oauth-btn--${provider.id}`"
              @click="handleOAuth(provider.id)"
              :disabled="loading"
              :aria-label="`S'inscrire avec ${provider.name}`"
            >
              <span class="register-view__oauth-icon" aria-hidden="true">{{ provider.icon }}</span>
              <span class="register-view__oauth-label">{{ provider.name }}</span>
            </button>
          </div>
        </template>

        <!-- ==============================================================
          PIED DE CARTE - Connexion
        ============================================================== -->
        <div class="register-view__footer">
          <p class="register-view__footer-text">
            Déjà un compte ?
            <router-link
              to="/login"
              class="register-view__footer-link"
            >
              Se connecter
            </router-link>
          </p>
        </div>
      </div>

      <!-- ================================================================
        INFORMATIONS SUPPLÉMENTAIRES
      ================================================================ -->
      <div class="register-view__info">
        <p class="register-view__info-text">
          🔒 Vos données sont chiffrées et sécurisées (HTTPS + JWT)
        </p>
        <p v-if="redirectPath && redirectPath !== '/'" class="register-view__info-redirect">
          Après inscription, vous serez redirigé vers <code>{{ redirectPath }}</code>
        </p>
      </div>

      <!-- ================================================================
        AVANTAGES
      ================================================================ -->
      <div class="register-view__benefits">
        <div class="register-view__benefit">
          <span class="register-view__benefit-icon" aria-hidden="true">📚</span>
          <div class="register-view__benefit-content">
            <strong>Bibliothèque personnelle</strong>
            <p>Gérez tous vos scans téléchargés</p>
          </div>
        </div>
        <div class="register-view__benefit">
          <span class="register-view__benefit-icon" aria-hidden="true">⚡</span>
          <div class="register-view__benefit-content">
            <strong>Téléchargement rapide</strong>
            <p>50+ sites supportés en parallèle</p>
          </div>
        </div>
        <div class="register-view__benefit">
          <span class="register-view__benefit-icon" aria-hidden="true">📦</span>
          <div class="register-view__benefit-content">
            <strong>Export CBZ</strong>
            <p>Compatible avec tous les lecteurs</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ====================================================================
      FOOTER
    ==================================================================== -->
    <footer class="register-view__bottom-footer">
      <span class="register-view__bottom-footer-brand">
        🧬 NexusDL {{ appVersion }}
      </span>
      <span class="register-view__bottom-footer-sep" aria-hidden="true">•</span>
      <span class="register-view__bottom-footer-copy">
        © {{ currentYear }} NexusDL Community — GNU GPL v3.0
      </span>
    </footer>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import NexusButton from '@/components/common/NexusButton.vue'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()

// ==========================================================================
//  État réactif
// ==========================================================================

const form = reactive({
  username: '',
  email: '',
  fullName: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false,
})

const showPassword = ref(false)
const showConfirmPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const shakeForm = ref(false)

const fieldErrors = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  acceptTerms: '',
})

const usernameInputRef = ref(null)
const emailInputRef = ref(null)
const passwordInputRef = ref(null)
const confirmPasswordInputRef = ref(null)

// ==========================================================================
//  Configuration OAuth (désactivé par défaut)
// ==========================================================================

const oauthEnabled = false // Mettre à true pour activer OAuth

const oauthProviders = [
  { id: 'github', name: 'GitHub', icon: '🐙' },
  { id: 'google', name: 'Google', icon: '🔴' },
  { id: 'discord', name: 'Discord', icon: '💬' },
]

// ==========================================================================
//  Computed
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')
const currentYear = computed(() => new Date().getFullYear())

const redirectPath = computed(() => {
  const redirect = route.query.redirect
  if (typeof redirect === 'string') {
    if (redirect.startsWith('/') && !redirect.startsWith('//')) {
      return redirect
    }
  }
  return '/'
})

// ==========================================================================
//  Validations
// ==========================================================================

const isUsernameValid = computed(() => {
  const username = form.username.trim()
  return username.length >= 3 && username.length <= 50 && /^[a-zA-Z0-9_-]+$/.test(username)
})

const isEmailValid = computed(() => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())
})

const isConfirmValid = computed(() => {
  return form.password.length > 0 && form.password === form.confirmPassword
})

// Critères du mot de passe
const passwordCriteria = computed(() => ({
  length: form.password.length >= 6,
  uppercase: /[A-Z]/.test(form.password),
  digit: /[0-9]/.test(form.password),
  special: /[^A-Za-z0-9]/.test(form.password),
}))

// Force du mot de passe
const passwordStrength = computed(() => {
  const pwd = form.password
  if (!pwd) {
    return { score: 0, level: 'none', label: '—', percent: 0 }
  }

  let score = 0
  const criteria = passwordCriteria.value
  if (criteria.length) score++
  if (criteria.uppercase) score++
  if (criteria.digit) score++
  if (criteria.special) score++

  // Bonus pour la longueur
  if (pwd.length >= 10) score = Math.min(4, score + 0.5)
  if (pwd.length >= 14) score = Math.min(4, score + 0.5)

  const rounded = Math.floor(score)
  const levels = {
    0: { level: 'very-weak', label: 'Très faible' },
    1: { level: 'weak', label: 'Faible' },
    2: { level: 'medium', label: 'Moyen' },
    3: { level: 'strong', label: 'Fort' },
    4: { level: 'very-strong', label: 'Très fort' },
  }

  return {
    score: rounded,
    ...levels[rounded],
    percent: (rounded / 4) * 100,
  }
})

// Complétion du formulaire (pour la barre de progression)
const formCompletion = computed(() => {
  const fields = [
    isUsernameValid.value,
    isEmailValid.value,
    form.password.length >= 6,
    isConfirmValid.value,
    form.acceptTerms,
  ]
  const filled = fields.filter(Boolean).length
  return Math.round((filled / fields.length) * 100)
})

// Validité globale
const isFormValid = computed(() => {
  return (
    isUsernameValid.value &&
    isEmailValid.value &&
    passwordCriteria.value.length &&
    passwordCriteria.value.uppercase &&
    passwordCriteria.value.digit &&
    isConfirmValid.value &&
    form.acceptTerms
  )
})

// ==========================================================================
//  Méthodes
// ==========================================================================

function clearError() {
  errorMessage.value = ''
}

function clearFieldError(field) {
  if (fieldErrors[field]) {
    fieldErrors[field] = ''
  }
  if (errorMessage.value) {
    errorMessage.value = ''
  }
}

// --- Handlers d'input (debounce/validation live) ---

let usernameCheckTimeout = null
function onUsernameInput() {
  clearFieldError('username')
  clearTimeout(usernameCheckTimeout)
  if (form.username.length >= 3) {
    usernameCheckTimeout = setTimeout(() => {
      validateUsername()
    }, 500)
  }
}

function validateUsername() {
  const username = form.username.trim()
  if (!username) {
    fieldErrors.username = ''
    return
  }
  if (username.length < 3) {
    fieldErrors.username = 'Le nom d\'utilisateur doit contenir au moins 3 caractères.'
    return
  }
  if (username.length > 50) {
    fieldErrors.username = 'Le nom d\'utilisateur ne doit pas dépasser 50 caractères.'
    return
  }
  if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
    fieldErrors.username = 'Seuls les lettres, chiffres, tirets et underscores sont autorisés.'
    return
  }
  fieldErrors.username = ''
}

let emailCheckTimeout = null
function onEmailInput() {
  clearFieldError('email')
  clearTimeout(emailCheckTimeout)
  if (form.email.includes('@')) {
    emailCheckTimeout = setTimeout(() => {
      validateEmail()
    }, 500)
  }
}

function validateEmail() {
  const email = form.email.trim()
  if (!email) {
    fieldErrors.email = ''
    return
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    fieldErrors.email = 'Veuillez saisir une adresse email valide.'
    return
  }
  fieldErrors.email = ''
}

function onPasswordInput() {
  clearFieldError('password')
  clearFieldError('confirmPassword')
  if (form.confirmPassword && form.password !== form.confirmPassword) {
    fieldErrors.confirmPassword = 'Les mots de passe ne correspondent pas.'
  }
}

function togglePasswordVisibility() {
  showPassword.value = !showPassword.value
  nextTick(() => {
    passwordInputRef.value?.focus()
  })
}

function toggleConfirmPasswordVisibility() {
  showConfirmPassword.value = !showConfirmPassword.value
  nextTick(() => {
    confirmPasswordInputRef.value?.focus()
  })
}

// ==========================================================================
//  Validation globale
// ==========================================================================

function validateForm() {
  // Reset
  Object.keys(fieldErrors).forEach((k) => { fieldErrors[k] = '' })
  let valid = true

  // Username
  const username = form.username.trim()
  if (!username) {
    fieldErrors.username = 'Le nom d\'utilisateur est requis.'
    valid = false
  } else if (username.length < 3) {
    fieldErrors.username = 'Le nom d\'utilisateur doit contenir au moins 3 caractères.'
    valid = false
  } else if (username.length > 50) {
    fieldErrors.username = 'Le nom d\'utilisateur ne doit pas dépasser 50 caractères.'
    valid = false
  } else if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
    fieldErrors.username = 'Seuls les lettres, chiffres, tirets et underscores sont autorisés.'
    valid = false
  }

  // Email
  const email = form.email.trim()
  if (!email) {
    fieldErrors.email = 'L\'adresse email est requise.'
    valid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    fieldErrors.email = 'Veuillez saisir une adresse email valide.'
    valid = false
  }

  // Password
  if (!form.password) {
    fieldErrors.password = 'Le mot de passe est requis.'
    valid = false
  } else if (form.password.length < 6) {
    fieldErrors.password = 'Le mot de passe doit contenir au moins 6 caractères.'
    valid = false
  } else if (!passwordCriteria.value.uppercase) {
    fieldErrors.password = 'Le mot de passe doit contenir au moins une majuscule.'
    valid = false
  } else if (!passwordCriteria.value.digit) {
    fieldErrors.password = 'Le mot de passe doit contenir au moins un chiffre.'
    valid = false
  }

  // Confirm password
  if (!form.confirmPassword) {
    fieldErrors.confirmPassword = 'Veuillez confirmer votre mot de passe.'
    valid = false
  } else if (form.password !== form.confirmPassword) {
    fieldErrors.confirmPassword = 'Les mots de passe ne correspondent pas.'
    valid = false
  }

  // Terms
  if (!form.acceptTerms) {
    fieldErrors.acceptTerms = 'Vous devez accepter les conditions d\'utilisation.'
    valid = false
  }

  return valid
}

// ==========================================================================
//  Soumission
// ==========================================================================

async function handleRegister() {
  clearError()
  successMessage.value = ''

  if (!validateForm()) {
    triggerShake()
    // Focus sur le premier champ en erreur
    nextTick(() => {
      if (fieldErrors.username) usernameInputRef.value?.focus()
      else if (fieldErrors.email) emailInputRef.value?.focus()
      else if (fieldErrors.password) passwordInputRef.value?.focus()
      else if (fieldErrors.confirmPassword) confirmPasswordInputRef.value?.focus()
    })
    return
  }

  loading.value = true

  try {
    const user = await authStore.register({
      username: form.username.trim(),
      email: form.email.trim(),
      password: form.password,
      full_name: form.fullName.trim() || null,
    })

    successMessage.value = 'Compte créé avec succès ! Redirection...'
    toast.success(`Bienvenue ${user?.username || ''} !`, '🎉', 2500)

    // Redirection après un court délai pour afficher le succès
    setTimeout(() => {
      router.push(redirectPath.value)
    }, 1200)
  } catch (err) {
    handleRegisterError(err)
  } finally {
    loading.value = false
  }
}

function handleRegisterError(err) {
  const status = err.response?.status
  const detail = err.response?.data?.detail

  if (status === 400) {
    if (typeof detail === 'string') {
      if (detail.toLowerCase().includes('username')) {
        fieldErrors.username = detail
      } else if (detail.toLowerCase().includes('email')) {
        fieldErrors.email = detail
      } else {
        errorMessage.value = detail
      }
    } else {
      errorMessage.value = 'Les informations fournies sont invalides.'
    }
    triggerShake()
  } else if (status === 409) {
    errorMessage.value = 'Ce nom d\'utilisateur ou cet email est déjà utilisé.'
    triggerShake()
  } else if (status === 422) {
    errorMessage.value = 'Veuillez vérifier les informations saisies.'
    triggerShake()
  } else if (status === 429) {
    const retryAfter = err.response?.headers?.['retry-after'] || 60
    errorMessage.value = `Trop de tentatives. Réessayez dans ${retryAfter} secondes.`
  } else if (status >= 500) {
    errorMessage.value = 'Le serveur est temporairement indisponible.'
  } else if (!err.response) {
    errorMessage.value = 'Impossible de contacter le serveur. Vérifiez votre connexion.'
  } else {
    errorMessage.value = detail || 'Une erreur est survenue lors de l\'inscription.'
  }

  toast.error(errorMessage.value, '❌')
}

function triggerShake() {
  shakeForm.value = true
  setTimeout(() => {
    shakeForm.value = false
  }, 500)
}

// ==========================================================================
//  OAuth
// ==========================================================================

function handleOAuth(provider) {
  toast.info(`Inscription via ${provider} bientôt disponible`, 'ℹ️')
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(() => {
  // Afficher un message si l'utilisateur vient d'être invité ou autre
  if (route.query.invite === 'true') {
    successMessage.value = 'Vous avez été invité à rejoindre NexusDL.'
  }

  // Focus automatique
  nextTick(() => {
    usernameInputRef.value?.focus()
  })

  console.log('📝 [RegisterView] Chargée — redirection :', redirectPath.value)
})

onUnmounted(() => {
  clearTimeout(usernameCheckTimeout)
  clearTimeout(emailCheckTimeout)
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.register-view {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  min-height: 100dvh;
  padding: 2rem 1rem;
  background: var(--color-bg-primary, #0a0e1a);
  overflow: hidden;
}

// ==========================================================================
//  Décorations de fond
// ==========================================================================

.register-view__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.register-view__bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at center, #000 30%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse at center, #000 30%, transparent 75%);
}

.register-view__bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: registerGlow 8s ease-in-out infinite alternate;

  &--1 {
    top: -20%;
    left: -10%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(0, 212, 255, 0.6) 0%, transparent 70%);
  }

  &--2 {
    bottom: -20%;
    right: -10%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(0, 102, 255, 0.5) 0%, transparent 70%);
    animation-delay: -4s;
  }
}

@keyframes registerGlow {
  0% {
    transform: scale(1) translate(0, 0);
    opacity: 0.3;
  }
  100% {
    transform: scale(1.15) translate(20px, -20px);
    opacity: 0.5;
  }
}

// ==========================================================================
//  Contenu
// ==========================================================================

.register-view__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  width: 100%;
  max-width: 480px;
}

// ==========================================================================
//  Brand
// ==========================================================================

.register-view__brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  text-align: center;
}

.register-view__brand-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  transition: opacity 0.2s ease;

  &:hover {
    opacity: 0.85;
  }
}

.register-view__brand-icon {
  font-size: 2.2rem;
  filter: drop-shadow(0 0 12px rgba(0, 212, 255, 0.4));
  animation: registerIconFloat 3s ease-in-out infinite;
}

@keyframes registerIconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.register-view__brand-name {
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.register-view__brand-tagline {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
  letter-spacing: 0.02em;
}

// ==========================================================================
//  Carte
// ==========================================================================

.register-view__card {
  position: relative;
  width: 100%;
  padding: 2rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-xl, 16px);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(0, 212, 255, 0.05) inset;
  transition: all 0.3s ease;
  backdrop-filter: blur(8px);
  overflow: hidden;

  &--shake {
    animation: registerShake 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97);
  }
}

@keyframes registerShake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-6px); }
  20%, 40%, 60%, 80% { transform: translateX(6px); }
}

// ==========================================================================
//  Progress bar
// ==========================================================================

.register-view__progress {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0, 212, 255, 0.1);
  overflow: hidden;
}

.register-view__progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #0066ff);
  transition: width 0.4s ease;
}

// ==========================================================================
//  Header
// ==========================================================================

.register-view__header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.25rem;
  margin-bottom: 1.5rem;
}

.register-view__title {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  letter-spacing: -0.02em;
}

.register-view__subtitle {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.4;
  max-width: 360px;
}

// ==========================================================================
//  Alertes
// ==========================================================================

.register-view__alert {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  margin-bottom: 1rem;
  border-radius: var(--radius-md, 8px);
  font-size: 0.8rem;
  animation: registerAlertIn 0.3s ease;

  &--error {
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid rgba(244, 67, 54, 0.35);
    color: var(--color-error, #f44336);
  }

  &--success {
    background: rgba(76, 175, 80, 0.1);
    border: 1px solid rgba(76, 175, 80, 0.35);
    color: var(--color-success, #4caf50);
  }
}

@keyframes registerAlertIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.register-view__alert-icon {
  flex-shrink: 0;
  font-size: 0.9rem;
}

.register-view__alert-text {
  flex: 1;
  line-height: 1.45;
}

.register-view__alert-close {
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
//  Formulaire
// ==========================================================================

.register-view__form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.register-view__field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;

  &--checkbox {
    margin-top: 0.25rem;
  }
}

.register-view__label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--color-text-secondary, #b0c0d8);
}

.register-view__label-required {
  color: var(--color-error, #f44336);
}

.register-view__label-optional {
  font-weight: 400;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

.register-view__input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.register-view__input-icon {
  position: absolute;
  left: 0.75rem;
  font-size: 0.9rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
  transition: color 0.15s ease;
}

.register-view__input {
  width: 100%;
  padding: 0.65rem 0.75rem 0.65rem 2.35rem;
  font-size: 0.88rem;
  font-family: inherit;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  transition: all 0.15s ease;

  &--with-action {
    padding-right: 2.4rem;
  }

  &:focus {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15);
    background: var(--color-bg-hover, #253254);

    & ~ .register-view__input-icon,
    & + .register-view__input-icon {
      color: var(--color-primary, #00d4ff);
    }
  }

  &:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
    opacity: 0.8;
  }

  &--error {
    border-color: var(--color-error, #f44336);
    background: rgba(244, 67, 54, 0.05);

    &:focus {
      border-color: var(--color-error, #f44336);
      box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.15);
    }
  }

  &--valid {
    border-color: var(--color-success, #4caf50);

    &:focus {
      border-color: var(--color-success, #4caf50);
      box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.15);
    }
  }
}

.register-view__input-action {
  position: absolute;
  right: 0.5rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 1rem;
  padding: 0.35rem;
  border-radius: var(--radius-sm, 4px);
  opacity: 0.7;
  transition: all 0.15s ease;

  &:hover {
    opacity: 1;
    color: var(--color-text-primary, #e8edf5);
    background: var(--color-bg-hover, #253254);
  }

  &:focus-visible {
    outline: 2px solid var(--color-primary, #00d4ff);
    outline-offset: 2px;
  }
}

.register-view__input-status {
  position: absolute;
  right: 0.75rem;
  font-size: 0.9rem;
  font-weight: 700;
  pointer-events: none;

  &--valid {
    color: var(--color-success, #4caf50);
  }
}

.register-view__field-error {
  margin: 0;
  font-size: 0.72rem;
  color: var(--color-error, #f44336);
  animation: registerFieldErrorIn 0.25s ease;
}

@keyframes registerFieldErrorIn {
  from {
    opacity: 0;
    transform: translateY(-3px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.register-view__field-hint {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.4;
}

// ==========================================================================
//  Password strength
// ==========================================================================

.register-view__password-strength {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 0.25rem;
}

.register-view__password-strength-bars {
  display: flex;
  gap: 0.25rem;
  flex: 1;
}

.register-view__password-strength-bar {
  flex: 1;
  height: 4px;
  background: var(--color-bg-input, #1e2a40);
  border-radius: 9999px;
  transition: all 0.3s ease;

  &--filled {
    &.register-view__password-strength-bar--very-weak { background: #f44336; }
    &.register-view__password-strength-bar--weak { background: #ff5722; }
    &.register-view__password-strength-bar--medium { background: #ff9800; }
    &.register-view__password-strength-bar--strong { background: #8bc34a; }
    &.register-view__password-strength-bar--very-strong { background: #4caf50; }
  }
}

.register-view__password-strength-label {
  font-size: 0.68rem;
  font-weight: 600;
  white-space: nowrap;
  transition: color 0.3s ease;

  &--very-weak { color: #f44336; }
  &--weak { color: #ff5722; }
  &--medium { color: #ff9800; }
  &--strong { color: #8bc34a; }
  &--very-strong { color: #4caf50; }
}

.register-view__password-criteria {
  list-style: none;
  padding: 0;
  margin: 0.4rem 0 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.15rem 0.6rem;
  font-size: 0.7rem;
}

.register-view__password-criterion {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: var(--color-text-muted, #6a7a9a);
  transition: color 0.2s ease;

  &--ok {
    color: var(--color-success, #4caf50);
  }
}

// ==========================================================================
//  Checkbox
// ==========================================================================

.register-view__checkbox {
  display: inline-flex;
  align-items: flex-start;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
  position: relative;
  font-size: 0.78rem;

  input[type='checkbox'] {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  input:checked + .register-view__checkbox-mark {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);

    &::after {
      opacity: 1;
      transform: scale(1);
    }
  }

  input:focus-visible + .register-view__checkbox-mark {
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.25);
  }

  &:hover .register-view__checkbox-mark {
    border-color: var(--color-primary, #00d4ff);
  }
}

.register-view__checkbox-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: var(--color-bg-input, #1e2a40);
  border: 1.5px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  transition: all 0.15s ease;
  flex-shrink: 0;
  margin-top: 0.05rem;
  position: relative;

  &::after {
    content: '✓';
    color: #ffffff;
    font-size: 0.7rem;
    font-weight: 700;
    line-height: 1;
    opacity: 0;
    transform: scale(0);
    transition: all 0.15s ease;
  }
}

.register-view__checkbox-label {
  flex: 1;
  line-height: 1.5;
  color: var(--color-text-secondary, #b0c0d8);
}

.register-view__checkbox-link {
  color: var(--color-primary, #00d4ff);
  text-decoration: none;
  font-weight: 500;

  &:hover {
    text-decoration: underline;
  }
}

// ==========================================================================
//  Submit
// ==========================================================================

.register-view__submit {
  margin-top: 0.5rem;
}

// ==========================================================================
//  OAuth
// ==========================================================================

.register-view__divider {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 1.5rem 0 1rem;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--color-border, #1a2538);
  }

  span {
    font-size: 0.7rem;
    color: var(--color-text-muted, #6a7a9a);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    white-space: nowrap;
  }
}

.register-view__oauth {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.register-view__oauth-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.6rem 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  font-size: 0.7rem;
  transition: all 0.15s ease;

  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-border-light, #253254);
    color: var(--color-text-primary, #e8edf5);
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.register-view__oauth-icon {
  font-size: 1.3rem;
}

.register-view__oauth-label {
  font-size: 0.65rem;
  font-weight: 500;
}

// ==========================================================================
//  Footer
// ==========================================================================

.register-view__footer {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--color-border, #1a2538);
  text-align: center;
}

.register-view__footer-text {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.register-view__footer-link {
  color: var(--color-primary, #00d4ff);
  text-decoration: none;
  font-weight: 600;
  margin-left: 0.25rem;

  &:hover {
    color: var(--color-primary-light, #66e5ff);
    text-decoration: underline;
  }
}

// ==========================================================================
//  Info
// ==========================================================================

.register-view__info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
  text-align: center;
}

.register-view__info-text {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  opacity: 0.8;
}

.register-view__info-redirect {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);

  code {
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 0.7rem;
    padding: 0.1rem 0.4rem;
    background: var(--color-bg-secondary, #141a2b);
    border: 1px solid var(--color-border, #1a2538);
    border-radius: var(--radius-sm, 4px);
    color: var(--color-primary, #00d4ff);
  }
}

// ==========================================================================
//  Benefits
// ==========================================================================

.register-view__benefits {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.4rem;
  width: 100%;
  margin-top: 0.5rem;
}

.register-view__benefit {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 212, 255, 0.04);
  border: 1px solid rgba(0, 212, 255, 0.1);
  border-radius: var(--radius-md, 8px);
  transition: all 0.15s ease;

  &:hover {
    background: rgba(0, 212, 255, 0.08);
    border-color: rgba(0, 212, 255, 0.2);
  }
}

.register-view__benefit-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
}

.register-view__benefit-content {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
  flex: 1;
  min-width: 0;

  strong {
    font-size: 0.78rem;
    color: var(--color-text-primary, #e8edf5);
    font-weight: 600;
  }

  p {
    margin: 0;
    font-size: 0.68rem;
    color: var(--color-text-muted, #6a7a9a);
    line-height: 1.3;
  }
}

// ==========================================================================
//  Bottom footer
// ==========================================================================

.register-view__bottom-footer {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: center;
  margin-top: 2rem;
  padding-top: 1rem;
  font-size: 0.68rem;
  color: var(--color-text-muted, #6a7a9a);
}

.register-view__bottom-footer-brand {
  font-weight: 600;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.register-view__bottom-footer-sep {
  opacity: 0.4;
}

.register-view__bottom-footer-copy {
  opacity: 0.75;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 480px) {
  .register-view {
    padding: 1rem 0.75rem;
  }

  .register-view__card {
    padding: 1.5rem 1.25rem;
  }

  .register-view__title {
    font-size: 1.35rem;
  }

  .register-view__brand-name {
    font-size: 1.5rem;
  }

  .register-view__brand-icon {
    font-size: 1.9rem;
  }

  .register-view__oauth {
    grid-template-columns: 1fr;
  }

  .register-view__oauth-btn {
    flex-direction: row;
    gap: 0.5rem;
    padding: 0.55rem;
  }

  .register-view__oauth-label {
    font-size: 0.75rem;
  }

  .register-view__password-criteria {
    grid-template-columns: 1fr;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .register-view {
    background: var(--color-bg-primary, #f4f6fa);
  }

  .register-view__bg-grid {
    background-image:
      linear-gradient(rgba(0, 102, 204, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 102, 204, 0.03) 1px, transparent 1px);
  }

  .register-view__bg-glow {
    &--1 {
      background: radial-gradient(circle, rgba(0, 102, 204, 0.35) 0%, transparent 70%);
    }
    &--2 {
      background: radial-gradient(circle, rgba(0, 68, 179, 0.3) 0%, transparent 70%);
    }
  }

  .register-view__card {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    box-shadow:
      0 20px 60px rgba(0, 0, 0, 0.1),
      0 0 0 1px rgba(0, 102, 204, 0.05) inset;
  }

  .register-view__title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .register-view__subtitle,
  .register-view__brand-tagline,
  .register-view__info-text,
  .register-view__info-redirect,
  .register-view__footer-text {
    color: var(--color-text-muted, #7a8a9a);
  }

  .register-view__label {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .register-view__input {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);

    &:focus {
      background: #ffffff;
      border-color: var(--color-primary, #0066cc);
    }

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }

    &--error {
      background: rgba(198, 40, 40, 0.05);
    }
  }

  .register-view__checkbox-mark {
    background: var(--color-bg-input, #f0f2f5);
    border-color: var(--color-border, #d0d8e0);
  }

  .register-view__checkbox-label {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .register-view__divider {
    &::before,
    &::after {
      background: var(--color-border, #d0d8e0);
    }
  }

  .register-view__oauth-btn {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
    color: var(--color-text-secondary, #3d4a5c);

    &:hover:not(:disabled) {
      background: var(--color-bg-hover, #e3e8ef);
      color: var(--color-text-primary, #1a1a2e);
    }
  }

  .register-view__footer {
    border-color: var(--color-border, #d0d8e0);
  }

  .register-view__info-redirect code {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .register-view__benefit {
    background: rgba(0, 102, 204, 0.04);
    border-color: rgba(0, 102, 204, 0.12);

    &:hover {
      background: rgba(0, 102, 204, 0.08);
    }

    strong {
      color: var(--color-text-primary, #1a1a2e);
    }
  }

  .register-view__password-strength-bar {
    background: var(--color-bg-input, #f0f2f5);
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .register-view__brand-icon,
  .register-view__bg-glow,
  .register-view__card--shake,
  .register-view__alert,
  .register-view__field-error {
    animation: none !important;
  }
}
</style>
