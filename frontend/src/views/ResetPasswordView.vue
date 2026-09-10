<!-- ==========================================================================
  NexusDL 2.0 - Reset Password View (version complète)
  Fichier : frontend/src/views/ResetPasswordView.vue
  Description : Page de réinitialisation de mot de passe. Permet à
                l'utilisateur de définir un nouveau mot de passe après avoir
                cliqué sur un lien reçu par email contenant un token unique.
                Validation du token, indicateur de force, confirmation,
                redirection après succès.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="reset-password-view">
    <!-- ====================================================================
      DÉCORATIONS DE FOND
    ==================================================================== -->
    <div class="reset-password-view__bg" aria-hidden="true">
      <div class="reset-password-view__bg-grid" />
      <div class="reset-password-view__bg-glow reset-password-view__bg-glow--1" />
      <div class="reset-password-view__bg-glow reset-password-view__bg-glow--2" />
    </div>

    <!-- ====================================================================
      CONTENU PRINCIPAL
    ==================================================================== -->
    <div class="reset-password-view__content">
      <!-- ================================================================
        BRAND
      ================================================================ -->
      <div class="reset-password-view__brand">
        <router-link to="/" class="reset-password-view__brand-link" aria-label="Accueil NexusDL">
          <span class="reset-password-view__brand-icon" aria-hidden="true">🧬</span>
          <span class="reset-password-view__brand-name">NexusDL</span>
        </router-link>
      </div>

      <!-- ================================================================
        ÉTAPE 1 — VÉRIFICATION DU TOKEN
      ================================================================ -->
      <div v-if="step === 'verifying'" class="reset-password-view__card">
        <div class="reset-password-view__verifying">
          <NexusSpinner size="lg" variant="gradient" />
          <h1 class="reset-password-view__verifying-title">
            Vérification du lien...
          </h1>
          <p class="reset-password-view__verifying-text">
            Nous vérifions la validité de votre lien de réinitialisation.
          </p>
        </div>
      </div>

      <!-- ================================================================
        ÉTAPE 2 — TOKEN INVALIDE / EXPIRÉ
      ================================================================ -->
      <div v-else-if="step === 'invalid'" class="reset-password-view__card">
        <div class="reset-password-view__invalid">
          <span class="reset-password-view__invalid-icon" aria-hidden="true">⚠️</span>
          <h1 class="reset-password-view__invalid-title">
            Lien invalide ou expiré
          </h1>
          <p class="reset-password-view__invalid-text">
            {{ invalidReason || 'Ce lien de réinitialisation n\'est plus valide. Il a peut-être expiré ou déjà été utilisé.' }}
          </p>

          <div class="reset-password-view__invalid-info">
            <div class="reset-password-view__invalid-info-item">
              <span class="reset-password-view__invalid-info-icon" aria-hidden="true">⏱️</span>
              <div>
                <strong>Le lien expire après 1 heure</strong>
                <p>Vous devrez refaire une demande si le délai est dépassé.</p>
              </div>
            </div>
            <div class="reset-password-view__invalid-info-item">
              <span class="reset-password-view__invalid-info-icon" aria-hidden="true">🔒</span>
              <div>
                <strong>Usage unique</strong>
                <p>Chaque lien ne peut être utilisé qu'une seule fois.</p>
              </div>
            </div>
          </div>

          <div class="reset-password-view__invalid-actions">
            <NexusButton
              variant="primary"
              size="md"
              @click="goToForgotPassword"
            >
              📨 Demander un nouveau lien
            </NexusButton>
            <NexusButton
              variant="neutral"
              size="md"
              @click="goToLogin"
            >
              ← Retour à la connexion
            </NexusButton>
          </div>
        </div>
      </div>

      <!-- ================================================================
        ÉTAPE 3 — FORMULAIRE DE NOUVEAU MOT DE PASSE
      ================================================================ -->
      <div
        v-else-if="step === 'form'"
        class="reset-password-view__card"
        :class="{ 'reset-password-view__card--shake': shakeForm }"
      >
        <!-- En-tête -->
        <header class="reset-password-view__header">
          <span class="reset-password-view__header-icon" aria-hidden="true">🔐</span>
          <h1 class="reset-password-view__title">
            Nouveau mot de passe
          </h1>
          <p class="reset-password-view__subtitle">
            Choisissez un nouveau mot de passe sécurisé pour votre compte.
          </p>
        </header>

        <!-- Alerte d'erreur -->
        <div
          v-if="errorMessage"
          class="reset-password-view__alert reset-password-view__alert--error"
          role="alert"
        >
          <span class="reset-password-view__alert-icon" aria-hidden="true">❌</span>
          <span class="reset-password-view__alert-text">{{ errorMessage }}</span>
          <button
            type="button"
            class="reset-password-view__alert-close"
            @click="clearError"
            aria-label="Fermer le message d'erreur"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <!-- Formulaire -->
        <form
          class="reset-password-view__form"
          @submit.prevent="handleReset"
          novalidate
        >
          <!-- Champ : nouveau mot de passe -->
          <div class="reset-password-view__field">
            <label for="new-password" class="reset-password-view__label">
              Nouveau mot de passe
              <span class="reset-password-view__label-required" aria-hidden="true">*</span>
            </label>
            <div class="reset-password-view__input-wrapper">
              <span class="reset-password-view__input-icon" aria-hidden="true">🔒</span>
              <input
                id="new-password"
                ref="passwordInputRef"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                class="reset-password-view__input reset-password-view__input--with-action"
                :class="{ 'reset-password-view__input--error': fieldErrors.password }"
                placeholder="Créez un mot de passe fort"
                autocomplete="new-password"
                autofocus
                required
                :disabled="loading"
                aria-describedby="password-error password-strength"
                :aria-invalid="!!fieldErrors.password"
                @input="onPasswordInput"
              />
              <button
                type="button"
                class="reset-password-view__input-action"
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
              class="reset-password-view__password-strength"
            >
              <div class="reset-password-view__password-strength-bars">
                <div
                  v-for="i in 4"
                  :key="i"
                  class="reset-password-view__password-strength-bar"
                  :class="{
                    'reset-password-view__password-strength-bar--filled': i <= passwordStrength.score,
                    [`reset-password-view__password-strength-bar--${passwordStrength.level}`]: i <= passwordStrength.score,
                  }"
                />
              </div>
              <span
                class="reset-password-view__password-strength-label"
                :class="`reset-password-view__password-strength-label--${passwordStrength.level}`"
              >
                Force : {{ passwordStrength.label }}
              </span>
            </div>

            <p
              v-if="fieldErrors.password"
              id="password-error"
              class="reset-password-view__field-error"
              role="alert"
            >
              ❌ {{ fieldErrors.password }}
            </p>

            <!-- Critères du mot de passe -->
            <ul v-if="form.password && passwordStrength.score < 4" class="reset-password-view__password-criteria">
              <li
                class="reset-password-view__password-criterion"
                :class="{ 'reset-password-view__password-criterion--ok': passwordCriteria.length }"
              >
                {{ passwordCriteria.length ? '✓' : '○' }} Au moins 6 caractères
              </li>
              <li
                class="reset-password-view__password-criterion"
                :class="{ 'reset-password-view__password-criterion--ok': passwordCriteria.uppercase }"
              >
                {{ passwordCriteria.uppercase ? '✓' : '○' }} Une majuscule
              </li>
              <li
                class="reset-password-view__password-criterion"
                :class="{ 'reset-password-view__password-criterion--ok': passwordCriteria.digit }"
              >
                {{ passwordCriteria.digit ? '✓' : '○' }} Un chiffre
              </li>
              <li
                class="reset-password-view__password-criterion"
                :class="{ 'reset-password-view__password-criterion--ok': passwordCriteria.special }"
              >
                {{ passwordCriteria.special ? '✓' : '○' }} Un caractère spécial
              </li>
            </ul>
          </div>

          <!-- Champ : confirmation -->
          <div class="reset-password-view__field">
            <label for="confirm-password" class="reset-password-view__label">
              Confirmer le mot de passe
              <span class="reset-password-view__label-required" aria-hidden="true">*</span>
            </label>
            <div class="reset-password-view__input-wrapper">
              <span class="reset-password-view__input-icon" aria-hidden="true">🔐</span>
              <input
                id="confirm-password"
                ref="confirmInputRef"
                v-model="form.confirmPassword"
                :type="showConfirm ? 'text' : 'password'"
                class="reset-password-view__input reset-password-view__input--with-action"
                :class="{
                  'reset-password-view__input--error': fieldErrors.confirmPassword,
                  'reset-password-view__input--valid': isConfirmValid && form.confirmPassword,
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
                class="reset-password-view__input-action"
                @click="toggleConfirmVisibility"
                :aria-label="showConfirm ? 'Masquer la confirmation' : 'Afficher la confirmation'"
                tabindex="-1"
              >
                <span aria-hidden="true">{{ showConfirm ? '🙈' : '👁️' }}</span>
              </button>
              <span
                v-if="isConfirmValid && form.confirmPassword"
                class="reset-password-view__input-status reset-password-view__input-status--valid"
                aria-hidden="true"
              >
                ✓
              </span>
            </div>
            <p
              v-if="fieldErrors.confirmPassword"
              id="confirm-error"
              class="reset-password-view__field-error"
              role="alert"
            >
              ❌ {{ fieldErrors.confirmPassword }}
            </p>
          </div>

          <!-- Bouton de validation -->
          <NexusButton
            type="submit"
            variant="primary"
            size="lg"
            block
            :loading="loading"
            :disabled="!isFormValid"
            class="reset-password-view__submit"
          >
            <span v-if="loading">Réinitialisation...</span>
            <span v-else>🔐 Réinitialiser mon mot de passe</span>
          </NexusButton>
        </form>

        <!-- Pied de carte -->
        <div class="reset-password-view__footer">
          <p class="reset-password-view__footer-text">
            Vous vous souvenez de votre mot de passe ?
            <router-link to="/login" class="reset-password-view__footer-link">
              Se connecter
            </router-link>
          </p>
        </div>
      </div>

      <!-- ================================================================
        ÉTAPE 4 — SUCCÈS
      ================================================================ -->
      <div v-else-if="step === 'success'" class="reset-password-view__card">
        <div class="reset-password-view__success">
          <span class="reset-password-view__success-icon" aria-hidden="true">🎉</span>
          <h1 class="reset-password-view__success-title">
            Mot de passe réinitialisé !
          </h1>
          <p class="reset-password-view__success-text">
            Votre mot de passe a été modifié avec succès. Vous pouvez maintenant
            vous connecter avec vos nouveaux identifiants.
          </p>

          <!-- Compte à rebours -->
          <div class="reset-password-view__success-countdown">
            <div class="reset-password-view__success-countdown-circle">
              <span class="reset-password-view__success-countdown-value">
                {{ redirectCountdown }}
              </span>
            </div>
            <p class="reset-password-view__success-countdown-text">
              Redirection vers la connexion...
            </p>
          </div>

          <div class="reset-password-view__success-actions">
            <NexusButton
              variant="primary"
              size="lg"
              @click="goToLogin"
            >
              🔐 Se connecter maintenant
            </NexusButton>
          </div>
        </div>
      </div>

      <!-- ================================================================
        ÉTAPE 5 — ERREUR SERVEUR
      ================================================================ -->
      <div v-else-if="step === 'error'" class="reset-password-view__card">
        <div class="reset-password-view__error-state">
          <span class="reset-password-view__error-state-icon" aria-hidden="true">⚠️</span>
          <h1 class="reset-password-view__error-state-title">
            Une erreur est survenue
          </h1>
          <p class="reset-password-view__error-state-text">
            {{ errorMessage || 'Impossible de réinitialiser le mot de passe.' }}
          </p>

          <div class="reset-password-view__error-state-actions">
            <NexusButton
              variant="primary"
              size="md"
              @click="retry"
            >
              🔄 Réessayer
            </NexusButton>
            <NexusButton
              variant="neutral"
              size="md"
              @click="goToLogin"
            >
              ← Retour à la connexion
            </NexusButton>
          </div>
        </div>
      </div>

      <!-- ================================================================
        SÉCURITÉ
      ================================================================ -->
      <div class="reset-password-view__security">
        <p class="reset-password-view__security-text">
          🔒 Lien sécurisé à usage unique — Expire après 1 heure
        </p>
      </div>
    </div>

    <!-- ====================================================================
      FOOTER
    ==================================================================== -->
    <footer class="reset-password-view__bottom-footer">
      <span class="reset-password-view__bottom-footer-brand">
        🧬 NexusDL {{ appVersion }}
      </span>
      <span class="reset-password-view__bottom-footer-sep" aria-hidden="true">•</span>
      <span class="reset-password-view__bottom-footer-copy">
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
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusButton from '@/components/common/NexusButton.vue'

// ==========================================================================
//  Composables
// ==========================================================================

const router = useRouter()
const route = useRoute()
const api = useApi()
const toast = useToast()

// ==========================================================================
//  État réactif
// ==========================================================================

const step = ref('verifying') // verifying | invalid | form | success | error
const form = reactive({
  password: '',
  confirmPassword: '',
})

const showPassword = ref(false)
const showConfirm = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const invalidReason = ref('')
const shakeForm = ref(false)
const redirectCountdown = ref(5)

const fieldErrors = reactive({
  password: '',
  confirmPassword: '',
})

const passwordInputRef = ref(null)
const confirmInputRef = ref(null)

let countdownTimer = null
let redirectTimer = null

// ==========================================================================
//  Computed
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')
const currentYear = computed(() => new Date().getFullYear())

const token = computed(() => route.params.token || route.query.token || '')

const passwordCriteria = computed(() => ({
  length: form.password.length >= 6,
  uppercase: /[A-Z]/.test(form.password),
  digit: /[0-9]/.test(form.password),
  special: /[^A-Za-z0-9]/.test(form.password),
}))

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

const isConfirmValid = computed(() => {
  return form.password.length > 0 && form.password === form.confirmPassword
})

const isFormValid = computed(() => {
  return (
    passwordCriteria.value.length &&
    passwordCriteria.value.uppercase &&
    passwordCriteria.value.digit &&
    isConfirmValid.value
  )
})

// ==========================================================================
//  Méthodes — Vérification du token
// ==========================================================================

/**
 * Vérifie la validité du token de réinitialisation.
 */
async function verifyToken() {
  step.value = 'verifying'
  invalidReason.value = ''

  if (!token.value) {
    step.value = 'invalid'
    invalidReason.value = 'Aucun token de réinitialisation fourni dans le lien.'
    return
  }

  try {
    // Appel à l'API pour vérifier le token
    await api.get(`/auth/reset-password/verify?token=${encodeURIComponent(token.value)}`)
    // Token valide → afficher le formulaire
    step.value = 'form'
    nextTick(() => {
      passwordInputRef.value?.focus()
    })
  } catch (err) {
    const status = err.response?.status
    const detail = err.response?.data?.detail

    if (status === 400 || status === 401 || status === 404) {
      step.value = 'invalid'
      invalidReason.value = detail || 'Ce lien de réinitialisation est invalide ou a expiré.'
    } else if (status === 410) {
      step.value = 'invalid'
      invalidReason.value = 'Ce lien a déjà été utilisé. Veuillez faire une nouvelle demande.'
    } else if (!err.response) {
      // Erreur réseau → on peut quand même afficher le formulaire et échouer à la soumission
      step.value = 'form'
      toast.warning('Impossible de vérifier le lien. Vous pouvez continuer.', '⚠️')
    } else {
      step.value = 'invalid'
      invalidReason.value = detail || 'Ce lien de réinitialisation n\'est pas valide.'
    }
  }
}

// ==========================================================================
//  Méthodes — Formulaire
// ==========================================================================

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

function toggleConfirmVisibility() {
  showConfirm.value = !showConfirm.value
  nextTick(() => {
    confirmInputRef.value?.focus()
  })
}

function clearError() {
  errorMessage.value = ''
}

function clearFieldError(field) {
  if (fieldErrors[field]) fieldErrors[field] = ''
  if (errorMessage.value) errorMessage.value = ''
}

function validateForm() {
  Object.keys(fieldErrors).forEach((k) => { fieldErrors[k] = '' })
  let valid = true

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

  if (!form.confirmPassword) {
    fieldErrors.confirmPassword = 'Veuillez confirmer votre mot de passe.'
    valid = false
  } else if (form.password !== form.confirmPassword) {
    fieldErrors.confirmPassword = 'Les mots de passe ne correspondent pas.'
    valid = false
  }

  return valid
}

async function handleReset() {
  clearError()

  if (!validateForm()) {
    triggerShake()
    nextTick(() => {
      if (fieldErrors.password) passwordInputRef.value?.focus()
      else if (fieldErrors.confirmPassword) confirmInputRef.value?.focus()
    })
    return
  }

  loading.value = true

  try {
    await api.post('/auth/reset-password', {
      token: token.value,
      new_password: form.password,
    })

    step.value = 'success'
    toast.success('Mot de passe réinitialisé avec succès !', '🎉')

    // Reset du formulaire
    form.password = ''
    form.confirmPassword = ''

    // Démarrer le compte à rebours pour la redirection
    startRedirectCountdown()
  } catch (err) {
    handleResetError(err)
  } finally {
    loading.value = false
  }
}

function handleResetError(err) {
  const status = err.response?.status
  const detail = err.response?.data?.detail

  if (status === 400 || status === 401) {
    // Token invalide / expiré
    step.value = 'invalid'
    invalidReason.value = detail || 'Le lien de réinitialisation est invalide ou a expiré.'
  } else if (status === 410) {
    step.value = 'invalid'
    invalidReason.value = 'Ce lien a déjà été utilisé.'
  } else if (status === 422) {
    errorMessage.value = 'Le mot de passe ne respecte pas les critères de sécurité.'
    triggerShake()
  } else if (status === 429) {
    const retryAfter = err.response?.headers?.['retry-after'] || 60
    errorMessage.value = `Trop de tentatives. Réessayez dans ${retryAfter} secondes.`
    triggerShake()
  } else if (status >= 500) {
    errorMessage.value = 'Le serveur est temporairement indisponible.'
    step.value = 'error'
  } else if (!err.response) {
    errorMessage.value = 'Impossible de contacter le serveur. Vérifiez votre connexion.'
    step.value = 'error'
  } else {
    errorMessage.value = detail || 'Une erreur est survenue lors de la réinitialisation.'
    triggerShake()
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
//  Compte à rebours de redirection
// ==========================================================================

function startRedirectCountdown() {
  stopRedirectCountdown()
  redirectCountdown.value = 5

  countdownTimer = setInterval(() => {
    redirectCountdown.value -= 1
    if (redirectCountdown.value <= 0) {
      stopRedirectCountdown()
    }
  }, 1000)

  redirectTimer = setTimeout(() => {
    goToLogin()
  }, 5000)
}

function stopRedirectCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  if (redirectTimer) {
    clearTimeout(redirectTimer)
    redirectTimer = null
  }
}

// ==========================================================================
//  Navigation
// ==========================================================================

function goToLogin() {
  stopRedirectCountdown()
  router.push('/login')
}

function goToForgotPassword() {
  router.push('/forgot-password')
}

function retry() {
  step.value = 'form'
  errorMessage.value = ''
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  console.log('🔐 [ResetPasswordView] Token:', token.value ? 'présent' : 'absent')

  if (!token.value) {
    step.value = 'invalid'
    invalidReason.value = 'Aucun token n\'a été fourni. Utilisez le lien reçu par email.'
    return
  }

  await verifyToken()
})

onUnmounted(() => {
  stopRedirectCountdown()
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.reset-password-view {
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

.reset-password-view__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.reset-password-view__bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at center, #000 30%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse at center, #000 30%, transparent 75%);
}

.reset-password-view__bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: resetGlow 8s ease-in-out infinite alternate;

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

@keyframes resetGlow {
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

.reset-password-view__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  width: 100%;
  max-width: 460px;
}

// ==========================================================================
//  Brand
// ==========================================================================

.reset-password-view__brand {
  display: flex;
  justify-content: center;
}

.reset-password-view__brand-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  transition: opacity 0.2s ease;

  &:hover {
    opacity: 0.85;
  }
}

.reset-password-view__brand-icon {
  font-size: 2rem;
  filter: drop-shadow(0 0 12px rgba(0, 212, 255, 0.4));
}

.reset-password-view__brand-name {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

// ==========================================================================
//  Carte
// ==========================================================================

.reset-password-view__card {
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

  &--shake {
    animation: resetShake 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97);
  }
}

@keyframes resetShake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-6px); }
  20%, 40%, 60%, 80% { transform: translateX(6px); }
}

// ==========================================================================
//  Header
// ==========================================================================

.reset-password-view__header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.35rem;
  margin-bottom: 1.5rem;
}

.reset-password-view__header-icon {
  font-size: 2.5rem;
  animation: resetIconFloat 3s ease-in-out infinite;
}

@keyframes resetIconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.reset-password-view__title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  letter-spacing: -0.02em;
}

.reset-password-view__subtitle {
  margin: 0;
  max-width: 340px;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Alertes
// ==========================================================================

.reset-password-view__alert {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  margin-bottom: 1rem;
  border-radius: var(--radius-md, 8px);
  font-size: 0.8rem;
  animation: resetAlertIn 0.3s ease;

  &--error {
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid rgba(244, 67, 54, 0.35);
    color: var(--color-error, #f44336);
  }
}

@keyframes resetAlertIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.reset-password-view__alert-icon {
  flex-shrink: 0;
  font-size: 0.9rem;
}

.reset-password-view__alert-text {
  flex: 1;
  line-height: 1.45;
}

.reset-password-view__alert-close {
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
//  Vérification
// ==========================================================================

.reset-password-view__verifying {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
  padding: 1rem 0;
}

.reset-password-view__verifying-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.reset-password-view__verifying-text {
  margin: 0;
  font-size: 0.82rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Token invalide
// ==========================================================================

.reset-password-view__invalid,
.reset-password-view__success,
.reset-password-view__error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.75rem;
}

.reset-password-view__invalid-icon,
.reset-password-view__success-icon,
.reset-password-view__error-state-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  font-size: 2.2rem;
  margin-bottom: 0.25rem;
}

.reset-password-view__invalid-icon {
  background: rgba(255, 152, 0, 0.1);
  border: 2px solid rgba(255, 152, 0, 0.3);
}

.reset-password-view__success-icon {
  background: rgba(76, 175, 80, 0.1);
  border: 2px solid rgba(76, 175, 80, 0.3);
  animation: resetSuccessBounce 0.6s ease;
}

.reset-password-view__error-state-icon {
  background: rgba(244, 67, 54, 0.1);
  border: 2px solid rgba(244, 67, 54, 0.3);
}

@keyframes resetSuccessBounce {
  0% { transform: scale(0); }
  50% { transform: scale(1.15); }
  100% { transform: scale(1); }
}

.reset-password-view__invalid-title {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-warning, #ff9800);
}

.reset-password-view__invalid-text {
  margin: 0;
  max-width: 340px;
  font-size: 0.85rem;
  line-height: 1.55;
  color: var(--color-text-secondary, #b0c0d8);
}

.reset-password-view__invalid-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  text-align: left;
}

.reset-password-view__invalid-info-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;

  > div {
    flex: 1;
    display: flex;
    flex-direction: column;

    strong {
      font-size: 0.78rem;
      color: var(--color-text-primary, #e8edf5);
      font-weight: 600;
    }

    p {
      margin: 0.1rem 0 0;
      font-size: 0.7rem;
      color: var(--color-text-muted, #6a7a9a);
      line-height: 1.4;
    }
  }
}

.reset-password-view__invalid-info-icon {
  font-size: 1rem;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.reset-password-view__invalid-actions,
.reset-password-view__success-actions,
.reset-password-view__error-state-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  width: 100%;
  margin-top: 0.75rem;
}

// ==========================================================================
//  Succès
// ==========================================================================

.reset-password-view__success-title {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-success, #4caf50);
}

.reset-password-view__success-text {
  margin: 0;
  max-width: 340px;
  font-size: 0.85rem;
  line-height: 1.55;
  color: var(--color-text-secondary, #b0c0d8);
}

.reset-password-view__success-countdown {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.reset-password-view__success-countdown-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(0, 212, 255, 0.1);
  border: 3px solid var(--color-primary, #00d4ff);
  animation: resetCountdownPulse 1s ease-in-out infinite;
}

.reset-password-view__success-countdown-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-primary, #00d4ff);
  font-variant-numeric: tabular-nums;
}

@keyframes resetCountdownPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.reset-password-view__success-countdown-text {
  margin: 0;
  font-size: 0.72rem;
  color: var(--color-text-muted, #6a7a9a);
  font-style: italic;
}

// ==========================================================================
//  Erreur
// ==========================================================================

.reset-password-view__error-state-title {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-error, #f44336);
}

.reset-password-view__error-state-text {
  margin: 0;
  max-width: 340px;
  font-size: 0.85rem;
  line-height: 1.55;
  color: var(--color-text-secondary, #b0c0d8);
}

// ==========================================================================
//  Formulaire
// ==========================================================================

.reset-password-view__form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.reset-password-view__field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.reset-password-view__label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--color-text-secondary, #b0c0d8);
}

.reset-password-view__label-required {
  color: var(--color-error, #f44336);
}

.reset-password-view__input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.reset-password-view__input-icon {
  position: absolute;
  left: 0.75rem;
  font-size: 0.9rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
  transition: color 0.15s ease;
}

.reset-password-view__input {
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

.reset-password-view__input-action {
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

.reset-password-view__input-status {
  position: absolute;
  right: 0.75rem;
  font-size: 0.9rem;
  font-weight: 700;
  pointer-events: none;

  &--valid {
    color: var(--color-success, #4caf50);
  }
}

.reset-password-view__field-error {
  margin: 0;
  font-size: 0.72rem;
  color: var(--color-error, #f44336);
  animation: resetFieldErrorIn 0.25s ease;
}

@keyframes resetFieldErrorIn {
  from {
    opacity: 0;
    transform: translateY(-3px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// ==========================================================================
//  Password strength
// ==========================================================================

.reset-password-view__password-strength {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 0.25rem;
}

.reset-password-view__password-strength-bars {
  display: flex;
  gap: 0.25rem;
  flex: 1;
}

.reset-password-view__password-strength-bar {
  flex: 1;
  height: 4px;
  background: var(--color-bg-input, #1e2a40);
  border-radius: 9999px;
  transition: all 0.3s ease;

  &--filled {
    &.reset-password-view__password-strength-bar--very-weak { background: #f44336; }
    &.reset-password-view__password-strength-bar--weak { background: #ff5722; }
    &.reset-password-view__password-strength-bar--medium { background: #ff9800; }
    &.reset-password-view__password-strength-bar--strong { background: #8bc34a; }
    &.reset-password-view__password-strength-bar--very-strong { background: #4caf50; }
  }
}

.reset-password-view__password-strength-label {
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

.reset-password-view__password-criteria {
  list-style: none;
  padding: 0;
  margin: 0.4rem 0 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.15rem 0.6rem;
  font-size: 0.7rem;
}

.reset-password-view__password-criterion {
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
//  Submit
// ==========================================================================

.reset-password-view__submit {
  margin-top: 0.5rem;
}

// ==========================================================================
//  Footer
// ==========================================================================

.reset-password-view__footer {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--color-border, #1a2538);
  text-align: center;
}

.reset-password-view__footer-text {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.reset-password-view__footer-link {
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
//  Sécurité
// ==========================================================================

.reset-password-view__security {
  display: flex;
  justify-content: center;
}

.reset-password-view__security-text {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  text-align: center;
  opacity: 0.8;
}

// ==========================================================================
//  Bottom footer
// ==========================================================================

.reset-password-view__bottom-footer {
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

.reset-password-view__bottom-footer-brand {
  font-weight: 600;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.reset-password-view__bottom-footer-sep {
  opacity: 0.4;
}

.reset-password-view__bottom-footer-copy {
  opacity: 0.75;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 480px) {
  .reset-password-view {
    padding: 1rem 0.75rem;
  }

  .reset-password-view__card {
    padding: 1.5rem 1.25rem;
  }

  .reset-password-view__title {
    font-size: 1.25rem;
  }

  .reset-password-view__brand-name {
    font-size: 1.25rem;
  }

  .reset-password-view__success-title,
  .reset-password-view__invalid-title,
  .reset-password-view__error-state-title {
    font-size: 1.15rem;
  }

  .reset-password-view__invalid-actions,
  .reset-password-view__success-actions,
  .reset-password-view__error-state-actions {
    flex-direction: column;

    > * {
      width: 100%;
      justify-content: center;
    }
  }

  .reset-password-view__password-criteria {
    grid-template-columns: 1fr;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .reset-password-view {
    background: var(--color-bg-primary, #f4f6fa);
  }

  .reset-password-view__bg-grid {
    background-image:
      linear-gradient(rgba(0, 102, 204, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 102, 204, 0.03) 1px, transparent 1px);
  }

  .reset-password-view__bg-glow {
    &--1 {
      background: radial-gradient(circle, rgba(0, 102, 204, 0.35) 0%, transparent 70%);
    }
    &--2 {
      background: radial-gradient(circle, rgba(0, 68, 179, 0.3) 0%, transparent 70%);
    }
  }

  .reset-password-view__card {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    box-shadow:
      0 20px 60px rgba(0, 0, 0, 0.1),
      0 0 0 1px rgba(0, 102, 204, 0.05) inset;
  }

  .reset-password-view__title,
  .reset-password-view__verifying-title,
  .reset-password-view__invalid-info-item strong {
    color: var(--color-text-primary, #1a1a2e);
  }

  .reset-password-view__subtitle,
  .reset-password-view__verifying-text,
  .reset-password-view__invalid-text,
  .reset-password-view__success-text,
  .reset-password-view__error-state-text,
  .reset-password-view__invalid-info-item p {
    color: var(--color-text-muted, #7a8a9a);
  }

  .reset-password-view__label {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .reset-password-view__input {
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

  .reset-password-view__footer {
    border-color: var(--color-border, #d0d8e0);
  }

  .reset-password-view__invalid-info {
    background: var(--color-bg-secondary, #e9ecf2);
  }

  .reset-password-view__password-strength-bar {
    background: var(--color-bg-input, #f0f2f5);
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .reset-password-view__header-icon,
  .reset-password-view__bg-glow,
  .reset-password-view__card--shake,
  .reset-password-view__alert,
  .reset-password-view__field-error,
  .reset-password-view__success-icon,
  .reset-password-view__success-countdown-circle {
    animation: none !important;
  }
}
</style>
