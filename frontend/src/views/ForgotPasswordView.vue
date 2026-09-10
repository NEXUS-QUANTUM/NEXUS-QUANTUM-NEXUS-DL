<!-- ==========================================================================
  NexusDL 2.0 - Forgot Password View (version complète)
  Fichier : frontend/src/views/ForgotPasswordView.vue
  Description : Page de demande de réinitialisation de mot de passe.
                Permet à l'utilisateur de saisir son email pour recevoir
                un lien de réinitialisation sécurisé.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="forgot-password-view">
    <!-- Décorations de fond -->
    <div class="forgot-password-view__bg" aria-hidden="true">
      <div class="forgot-password-view__bg-grid" />
      <div class="forgot-password-view__bg-glow" />
    </div>

    <!-- Contenu principal -->
    <div class="forgot-password-view__content">
      <!-- Logo / Brand -->
      <div class="forgot-password-view__brand">
        <router-link to="/" class="forgot-password-view__brand-link">
          <span class="forgot-password-view__brand-icon">🧬</span>
          <span class="forgot-password-view__brand-name">NexusDL</span>
        </router-link>
      </div>

      <!-- Carte -->
      <div class="forgot-password-view__card">
        <!-- Étape 1 : Saisie de l'email -->
        <template v-if="step === 'form'">
          <header class="forgot-password-view__header">
            <span class="forgot-password-view__header-icon" aria-hidden="true">🔑</span>
            <h1 class="forgot-password-view__title">Mot de passe oublié</h1>
            <p class="forgot-password-view__subtitle">
              Entrez votre adresse email pour recevoir un lien de
              réinitialisation.
            </p>
          </header>

          <form
            class="forgot-password-view__form"
            @submit.prevent="handleSubmit"
            novalidate
          >
            <div class="forgot-password-view__field">
              <label
                for="email"
                class="forgot-password-view__label"
              >
                Adresse email
                <span class="forgot-password-view__label-required" aria-hidden="true">*</span>
              </label>
              <div class="forgot-password-view__input-wrapper">
                <span class="forgot-password-view__input-icon" aria-hidden="true">📧</span>
                <input
                  id="email"
                  ref="emailInputRef"
                  v-model="email"
                  type="email"
                  class="forgot-password-view__input"
                  :class="{ 'forgot-password-view__input--error': errorMessage }"
                  placeholder="votre@email.com"
                  autocomplete="email"
                  autofocus
                  required
                  :disabled="loading"
                  aria-describedby="email-error"
                  :aria-invalid="!!errorMessage"
                  @input="clearError"
                />
              </div>
              <p
                v-if="errorMessage"
                id="email-error"
                class="forgot-password-view__error"
                role="alert"
              >
                ❌ {{ errorMessage }}
              </p>
            </div>

            <NexusButton
              type="submit"
              variant="primary"
              size="lg"
              block
              :loading="loading"
              :disabled="!isEmailValid"
            >
              📨 Envoyer le lien de réinitialisation
            </NexusButton>
          </form>

          <div class="forgot-password-view__divider">
            <span>ou</span>
          </div>

          <div class="forgot-password-view__links">
            <router-link
              to="/login"
              class="forgot-password-view__link"
            >
              ← Retour à la connexion
            </router-link>
          </div>
        </template>

        <!-- Étape 2 : Confirmation -->
        <template v-else-if="step === 'success'">
          <div class="forgot-password-view__success">
            <span class="forgot-password-view__success-icon" aria-hidden="true">✅</span>
            <h1 class="forgot-password-view__success-title">
              Email envoyé !
            </h1>
            <p class="forgot-password-view__success-text">
              Si un compte existe avec l'adresse
              <strong>{{ submittedEmail }}</strong>, vous recevrez un email
              contenant un lien pour réinitialiser votre mot de passe.
            </p>

            <div class="forgot-password-view__success-info">
              <div class="forgot-password-view__success-info-item">
                <span class="forgot-password-view__success-info-icon" aria-hidden="true">📬</span>
                <div>
                  <strong>Vérifiez votre boîte de réception</strong>
                  <p>L'email devrait arriver dans les 2 prochaines minutes.</p>
                </div>
              </div>
              <div class="forgot-password-view__success-info-item">
                <span class="forgot-password-view__success-info-icon" aria-hidden="true">📁</span>
                <div>
                  <strong>Vérifiez vos spams</strong>
                  <p>Si l'email n'apparaît pas, vérifiez le dossier spam.</p>
                </div>
              </div>
              <div class="forgot-password-view__success-info-item">
                <span class="forgot-password-view__success-info-icon" aria-hidden="true">⏱️</span>
                <div>
                  <strong>Le lien expire dans 1 heure</strong>
                  <p>Après ce délai, vous devrez refaire la demande.</p>
                </div>
              </div>
            </div>

            <div class="forgot-password-view__success-actions">
              <NexusButton
                variant="neutral"
                size="md"
                @click="resendEmail"
                :disabled="resendCooldown > 0 || loading"
                :loading="loading"
              >
                <span v-if="resendCooldown > 0">
                  🔄 Renvoyer dans {{ resendCooldown }}s
                </span>
                <span v-else>
                  🔄 Renvoyer l'email
                </span>
              </NexusButton>

              <NexusButton
                variant="primary"
                size="md"
                @click="goToLogin"
              >
                🔐 Retour à la connexion
              </NexusButton>
            </div>
          </div>
        </template>

        <!-- Étape 3 : Erreur -->
        <template v-else-if="step === 'error'">
          <div class="forgot-password-view__error-state">
            <span class="forgot-password-view__error-state-icon" aria-hidden="true">⚠️</span>
            <h1 class="forgot-password-view__error-state-title">
              Une erreur est survenue
            </h1>
            <p class="forgot-password-view__error-state-text">
              {{ errorMessage || 'Impossible d\'envoyer l\'email de réinitialisation.' }}
            </p>

            <div class="forgot-password-view__error-state-actions">
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
        </template>
      </div>

      <!-- Sécurité -->
      <div class="forgot-password-view__security">
        <p class="forgot-password-view__security-text">
          🔒 Vos données sont transmises de manière sécurisée (HTTPS)
        </p>
      </div>
    </div>

    <!-- Footer -->
    <footer class="forgot-password-view__footer">
      <span class="forgot-password-view__footer-brand">
        🧬 NexusDL {{ appVersion }}
      </span>
      <span class="forgot-password-view__footer-copy">
        © {{ currentYear }} NexusDL Community — GNU GPL v3.0
      </span>
    </footer>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
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

const email = ref('')
const submittedEmail = ref('')
const loading = ref(false)
const errorMessage = ref('')
const step = ref('form') // 'form' | 'success' | 'error'
const emailInputRef = ref(null)

const resendCooldown = ref(0)
let cooldownTimer = null

// ==========================================================================
//  Computed
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')
const currentYear = computed(() => new Date().getFullYear())

const isEmailValid = computed(() => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())
})

// ==========================================================================
//  Méthodes
// ==========================================================================

/**
 * Nettoie le message d'erreur.
 */
function clearError() {
  errorMessage.value = ''
}

/**
 * Valide l'email saisi.
 * @returns {boolean}
 */
function validateEmail() {
  const value = email.value.trim()
  if (!value) {
    errorMessage.value = 'Veuillez saisir votre adresse email.'
    return false
  }
  if (!isEmailValid.value) {
    errorMessage.value = 'Veuillez saisir une adresse email valide.'
    return false
  }
  return true
}

/**
 * Soumet la demande de réinitialisation.
 */
async function handleSubmit() {
  clearError()

  if (!validateEmail()) {
    nextTick(() => {
      emailInputRef.value?.focus()
    })
    return
  }

  loading.value = true
  try {
    const response = await api.post('/auth/forgot-password', {
      email: email.value.trim(),
    })

    submittedEmail.value = email.value.trim()
    step.value = 'success'
    toast.success('Email de réinitialisation envoyé !', '📬')

    // Démarrer le cooldown pour éviter le spam
    startResendCooldown()
  } catch (err) {
    // Pour la sécurité, on affiche le même message de succès,
    // sauf en cas d'erreur réseau/technique
    const status = err.response?.status
    if (status === 429) {
      errorMessage.value = 'Trop de tentatives. Veuillez réessayer plus tard.'
      step.value = 'error'
    } else if (status && status >= 500) {
      errorMessage.value = 'Le serveur est temporairement indisponible.'
      step.value = 'error'
    } else if (!err.response) {
      // Erreur réseau
      errorMessage.value = 'Impossible de contacter le serveur.'
      step.value = 'error'
    } else {
      // Pour éviter l'énumération des emails, on affiche le succès
      submittedEmail.value = email.value.trim()
      step.value = 'success'
      startResendCooldown()
    }
    console.warn('Forgot password error:', err.message)
  } finally {
    loading.value = false
  }
}

/**
 * Renvoie l'email de réinitialisation.
 */
async function resendEmail() {
  if (resendCooldown.value > 0) return
  if (!submittedEmail.value) {
    step.value = 'form'
    email.value = ''
    return
  }

  loading.value = true
  try {
    await api.post('/auth/forgot-password', {
      email: submittedEmail.value,
    })
    toast.success('Email renvoyé !', '📬')
    startResendCooldown()
  } catch (err) {
    toast.error('Impossible de renvoyer l\'email', '❌')
  } finally {
    loading.value = false
  }
}

/**
 * Démarre le compte à rebours avant renvoi possible.
 * @param {number} seconds
 */
function startResendCooldown(seconds = 60) {
  stopResendCooldown()
  resendCooldown.value = seconds

  cooldownTimer = setInterval(() => {
    resendCooldown.value -= 1
    if (resendCooldown.value <= 0) {
      stopResendCooldown()
    }
  }, 1000)
}

/**
 * Arrête le cooldown.
 */
function stopResendCooldown() {
  if (cooldownTimer) {
    clearInterval(cooldownTimer)
    cooldownTimer = null
  }
  if (resendCooldown.value < 0) {
    resendCooldown.value = 0
  }
}

/**
 * Réessayer après une erreur.
 */
function retry() {
  step.value = 'form'
  errorMessage.value = ''
}

/**
 * Redirige vers la page de connexion.
 */
function goToLogin() {
  router.push('/login')
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(() => {
  // Pré-remplir l'email depuis la query string (ex: après une redirection)
  const emailFromQuery = route.query.email
  if (emailFromQuery && typeof emailFromQuery === 'string') {
    email.value = emailFromQuery
  }

  // Focus sur l'input
  nextTick(() => {
    emailInputRef.value?.focus()
  })
})

onUnmounted(() => {
  stopResendCooldown()
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.forgot-password-view {
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

.forgot-password-view__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.forgot-password-view__bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at center, #000 30%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse at center, #000 30%, transparent 70%);
}

.forgot-password-view__bg-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.1) 0%, transparent 70%);
  animation: forgotGlow 4s ease-in-out infinite alternate;
}

@keyframes forgotGlow {
  0% {
    opacity: 0.5;
    transform: translate(-50%, -50%) scale(1);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.1);
  }
}

// ==========================================================================
//  Contenu
// ==========================================================================

.forgot-password-view__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  width: 100%;
  max-width: 440px;
}

// ==========================================================================
//  Brand
// ==========================================================================

.forgot-password-view__brand {
  display: flex;
  justify-content: center;
}

.forgot-password-view__brand-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  transition: opacity 0.2s ease;

  &:hover {
    opacity: 0.85;
  }
}

.forgot-password-view__brand-icon {
  font-size: 2rem;
}

.forgot-password-view__brand-name {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

// ==========================================================================
//  Carte
// ==========================================================================

.forgot-password-view__card {
  width: 100%;
  padding: 2rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  box-shadow: var(--shadow-xl, 0 16px 48px rgba(0, 0, 0, 0.5));
  transition: all 0.3s ease;
}

// ==========================================================================
//  Header
// ==========================================================================

.forgot-password-view__header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.forgot-password-view__header-icon {
  font-size: 2.5rem;
  animation: forgotIconFloat 3s ease-in-out infinite;
}

@keyframes forgotIconFloat {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-5px) rotate(5deg);
  }
}

.forgot-password-view__title {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.forgot-password-view__subtitle {
  margin: 0;
  max-width: 320px;
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Formulaire
// ==========================================================================

.forgot-password-view__form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.forgot-password-view__field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.forgot-password-view__label {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-secondary, #b0c0d8);
}

.forgot-password-view__label-required {
  color: var(--color-error, #f44336);
}

.forgot-password-view__input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.forgot-password-view__input-icon {
  position: absolute;
  left: 0.75rem;
  font-size: 0.95rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
}

.forgot-password-view__input {
  width: 100%;
  padding: 0.7rem 0.75rem 0.7rem 2.4rem;
  font-size: 0.9rem;
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

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &--error {
    border-color: var(--color-error, #f44336);

    &:focus {
      border-color: var(--color-error, #f44336);
      box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.15);
    }
  }
}

.forgot-password-view__error {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-error, #f44336);
  animation: forgotShake 0.3s ease;
}

@keyframes forgotShake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-3px); }
  75% { transform: translateX(3px); }
}

// ==========================================================================
//  Divider & Links
// ==========================================================================

.forgot-password-view__divider {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 1.25rem 0 0.75rem;

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
    letter-spacing: 0.1em;
  }
}

.forgot-password-view__links {
  display: flex;
  justify-content: center;
}

.forgot-password-view__link {
  font-size: 0.8rem;
  color: var(--color-primary, #00d4ff);
  text-decoration: none;
  transition: color 0.15s ease;

  &:hover {
    color: var(--color-primary-light, #66e5ff);
    text-decoration: underline;
  }
}

// ==========================================================================
//  Success
// ==========================================================================

.forgot-password-view__success {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
}

.forgot-password-view__success-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(76, 175, 80, 0.1);
  border: 2px solid rgba(76, 175, 80, 0.3);
  font-size: 2.2rem;
  animation: forgotSuccessBounce 0.6s ease;
}

@keyframes forgotSuccessBounce {
  0% { transform: scale(0); }
  50% { transform: scale(1.15); }
  100% { transform: scale(1); }
}

.forgot-password-view__success-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-success, #4caf50);
}

.forgot-password-view__success-text {
  margin: 0;
  max-width: 340px;
  font-size: 0.85rem;
  line-height: 1.55;
  color: var(--color-text-secondary, #b0c0d8);

  strong {
    color: var(--color-text-primary, #e8edf5);
    word-break: break-word;
  }
}

.forgot-password-view__success-info {
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

.forgot-password-view__success-info-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;

  > div {
    flex: 1;
    display: flex;
    flex-direction: column;

    strong {
      font-size: 0.8rem;
      color: var(--color-text-primary, #e8edf5);
    }

    p {
      margin: 0.1rem 0 0;
      font-size: 0.7rem;
      color: var(--color-text-muted, #6a7a9a);
      line-height: 1.4;
    }
  }
}

.forgot-password-view__success-info-icon {
  font-size: 1rem;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.forgot-password-view__success-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  width: 100%;
  margin-top: 0.5rem;
}

// ==========================================================================
//  Error State
// ==========================================================================

.forgot-password-view__error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
}

.forgot-password-view__error-state-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(244, 67, 54, 0.1);
  border: 2px solid rgba(244, 67, 54, 0.3);
  font-size: 2.2rem;
}

.forgot-password-view__error-state-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-error, #f44336);
}

.forgot-password-view__error-state-text {
  margin: 0;
  max-width: 320px;
  font-size: 0.85rem;
  line-height: 1.55;
  color: var(--color-text-secondary, #b0c0d8);
}

.forgot-password-view__error-state-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 0.5rem;
}

// ==========================================================================
//  Sécurité
// ==========================================================================

.forgot-password-view__security {
  display: flex;
  justify-content: center;
}

.forgot-password-view__security-text {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  text-align: center;
  opacity: 0.8;
}

// ==========================================================================
//  Footer
// ==========================================================================

.forgot-password-view__footer {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: center;
  margin-top: 2rem;
  padding-top: 1rem;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

.forgot-password-view__footer-brand {
  font-weight: 600;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.forgot-password-view__footer-copy {
  opacity: 0.7;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 480px) {
  .forgot-password-view {
    padding: 1rem 0.75rem;
  }

  .forgot-password-view__card {
    padding: 1.5rem 1.25rem;
  }

  .forgot-password-view__title {
    font-size: 1.2rem;
  }

  .forgot-password-view__brand-name {
    font-size: 1.25rem;
  }

  .forgot-password-view__success-title,
  .forgot-password-view__error-state-title {
    font-size: 1.15rem;
  }

  .forgot-password-view__success-actions,
  .forgot-password-view__error-state-actions {
    flex-direction: column;

    > * {
      width: 100%;
      justify-content: center;
    }
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .forgot-password-view {
    background: var(--color-bg-primary, #f4f6fa);
  }

  .forgot-password-view__bg-grid {
    background-image:
      linear-gradient(rgba(0, 102, 204, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 102, 204, 0.03) 1px, transparent 1px);
  }

  .forgot-password-view__bg-glow {
    background: radial-gradient(circle, rgba(0, 102, 204, 0.08) 0%, transparent 70%);
  }

  .forgot-password-view__card {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    box-shadow: var(--shadow-xl, 0 16px 48px rgba(0, 0, 0, 0.1));
  }

  .forgot-password-view__title,
  .forgot-password-view__success-info-item strong {
    color: var(--color-text-primary, #1a1a2e);
  }

  .forgot-password-view__subtitle,
  .forgot-password-view__success-text,
  .forgot-password-view__error-state-text,
  .forgot-password-view__success-info-item p {
    color: var(--color-text-muted, #7a8a9a);
  }

  .forgot-password-view__label {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .forgot-password-view__input {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .forgot-password-view__divider {
    &::before,
    &::after {
      background: var(--color-border, #d0d8e0);
    }
  }

  .forgot-password-view__success-info {
    background: var(--color-bg-secondary, #e9ecf2);
  }

  .forgot-password-view__footer-brand {
    background: linear-gradient(135deg, #0066cc, #0044b3);
    -webkit-background-clip: text;
    background-clip: text;
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .forgot-password-view__header-icon,
  .forgot-password-view__success-icon,
  .forgot-password-view__bg-glow,
  .forgot-password-view__error {
    animation: none !important;
  }
}
</style>
