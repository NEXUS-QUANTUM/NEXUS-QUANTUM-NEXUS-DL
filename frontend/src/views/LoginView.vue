<!-- ==========================================================================
  NexusDL 2.0 - Login View (version complète) 
  Fichier : frontend/src/views/LoginView.vue
  Description : Page de connexion avec support complet : formulaire, validation,
                gestion d'erreurs, "se souvenir de moi", OAuth (optionnel),
                mot de passe oublié, redirection post-login, animations,
                thème clair/sombre et accessibilité.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="login-view">
    <!-- ====================================================================
      DÉCORATIONS DE FOND
    ==================================================================== -->
    <div class="login-view__bg" aria-hidden="true">
      <div class="login-view__bg-grid" />
      <div class="login-view__bg-glow login-view__bg-glow--1" />
      <div class="login-view__bg-glow login-view__bg-glow--2" />
    </div>

    <!-- ====================================================================
      CONTENU PRINCIPAL
    ==================================================================== -->
    <div class="login-view__content">
      <!-- ================================================================
        BRAND
      ================================================================ -->
      <div class="login-view__brand">
        <router-link to="/" class="login-view__brand-link" aria-label="Accueil NexusDL">
          <span class="login-view__brand-icon" aria-hidden="true">🧬</span>
          <span class="login-view__brand-name">NexusDL</span>
        </router-link>
        <p class="login-view__brand-tagline">
          Moteur universel de téléchargement de scans
        </p>
      </div>

      <!-- ================================================================
        CARTE DE CONNEXION
      ================================================================ -->
      <div class="login-view__card" :class="{ 'login-view__card--shake': shakeForm }">
        <!-- En-tête -->
        <header class="login-view__header">
          <h1 class="login-view__title">Connexion</h1>
          <p class="login-view__subtitle">
            Accédez à votre compte NexusDL
          </p>
        </header>

        <!-- Message d'erreur global -->
        <div
          v-if="errorMessage"
          class="login-view__alert login-view__alert--error"
          role="alert"
        >
          <span class="login-view__alert-icon" aria-hidden="true">❌</span>
          <span class="login-view__alert-text">{{ errorMessage }}</span>
          <button
            type="button"
            class="login-view__alert-close"
            @click="clearError"
            aria-label="Fermer le message d'erreur"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <!-- Message d'information -->
        <div
          v-if="infoMessage"
          class="login-view__alert login-view__alert--info"
          role="status"
        >
          <span class="login-view__alert-icon" aria-hidden="true">ℹ️</span>
          <span class="login-view__alert-text">{{ infoMessage }}</span>
          <button
            type="button"
            class="login-view__alert-close"
            @click="infoMessage = ''"
            aria-label="Fermer le message"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <!-- Formulaire -->
        <form
          class="login-view__form"
          @submit.prevent="handleLogin"
          novalidate
          autocomplete="on"
        >
          <!-- Champ : nom d'utilisateur -->
          <div class="login-view__field">
            <label for="username" class="login-view__label">
              Nom d'utilisateur ou email
              <span class="login-view__label-required" aria-hidden="true">*</span>
            </label>
            <div class="login-view__input-wrapper">
              <span class="login-view__input-icon" aria-hidden="true">👤</span>
              <input
                id="username"
                ref="usernameInputRef"
                v-model="form.username"
                type="text"
                class="login-view__input"
                :class="{ 'login-view__input--error': fieldErrors.username }"
                placeholder="Entrez votre nom d'utilisateur"
                autocomplete="username"
                autofocus
                required
                :disabled="loading"
                aria-describedby="username-error"
                :aria-invalid="!!fieldErrors.username"
                @input="clearFieldError('username')"
              />
            </div>
            <p
              v-if="fieldErrors.username"
              id="username-error"
              class="login-view__field-error"
              role="alert"
            >
              ❌ {{ fieldErrors.username }}
            </p>
          </div>

          <!-- Champ : mot de passe -->
          <div class="login-view__field">
            <label for="password" class="login-view__label">
              Mot de passe
              <span class="login-view__label-required" aria-hidden="true">*</span>
            </label>
            <div class="login-view__input-wrapper">
              <span class="login-view__input-icon" aria-hidden="true">🔒</span>
              <input
                id="password"
                ref="passwordInputRef"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                class="login-view__input login-view__input--with-action"
                :class="{ 'login-view__input--error': fieldErrors.password }"
                placeholder="Entrez votre mot de passe"
                autocomplete="current-password"
                required
                :disabled="loading"
                aria-describedby="password-error"
                :aria-invalid="!!fieldErrors.password"
                @input="clearFieldError('password')"
              />
              <button
                type="button"
                class="login-view__input-action"
                @click="togglePasswordVisibility"
                :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
                :title="showPassword ? 'Masquer' : 'Afficher'"
                tabindex="-1"
              >
                <span aria-hidden="true">{{ showPassword ? '🙈' : '👁️' }}</span>
              </button>
            </div>
            <p
              v-if="fieldErrors.password"
              id="password-error"
              class="login-view__field-error"
              role="alert"
            >
              ❌ {{ fieldErrors.password }}
            </p>
          </div>

          <!-- Options : remember me + mot de passe oublié -->
          <div class="login-view__options">
            <label class="login-view__checkbox">
              <input
                v-model="form.remember"
                type="checkbox"
                :disabled="loading"
              />
              <span class="login-view__checkbox-mark" aria-hidden="true" />
              <span class="login-view__checkbox-label">Se souvenir de moi</span>
            </label>

            <router-link
              to="/forgot-password"
              class="login-view__forgot-link"
            >
              Mot de passe oublié ?
            </router-link>
          </div>

          <!-- Bouton de connexion -->
          <NexusButton
            type="submit"
            variant="primary"
            size="lg"
            block
            :loading="loading"
            :disabled="!isFormValid"
            class="login-view__submit"
          >
            <span v-if="loading">Connexion en cours...</span>
            <span v-else>🔐 Se connecter</span>
          </NexusButton>
        </form>

        <!-- ==============================================================
          SÉPARATEUR (si OAuth activé)
        ============================================================== -->
        <template v-if="oauthEnabled">
          <div class="login-view__divider">
            <span>ou continuer avec</span>
          </div>

          <div class="login-view__oauth">
            <button
              v-for="provider in oauthProviders"
              :key="provider.id"
              type="button"
              class="login-view__oauth-btn"
              :class="`login-view__oauth-btn--${provider.id}`"
              @click="handleOAuth(provider.id)"
              :disabled="loading"
              :aria-label="`Se connecter avec ${provider.name}`"
            >
              <span class="login-view__oauth-icon" aria-hidden="true">{{ provider.icon }}</span>
              <span class="login-view__oauth-label">{{ provider.name }}</span>
            </button>
          </div>
        </template>

        <!-- ==============================================================
          PIED DE CARTE - Inscription
        ============================================================== -->
        <div class="login-view__footer">
          <p class="login-view__footer-text">
            Pas encore de compte ?
            <router-link
              to="/register"
              class="login-view__footer-link"
            >
              Créer un compte
            </router-link>
          </p>
        </div>
      </div>

      <!-- ================================================================
        INFORMATIONS SUPPLÉMENTAIRES
      ================================================================ -->
      <div class="login-view__info">
        <p class="login-view__info-text">
          🔒 Connexion sécurisée (HTTPS + JWT)
        </p>
        <p v-if="redirectPath && redirectPath !== '/'" class="login-view__info-redirect">
          Vous serez redirigé vers <code>{{ redirectPath }}</code>
        </p>
      </div>

      <!-- ================================================================
        COMPTE DE DÉMONSTRATION (si activé)
      ================================================================ -->
      <div v-if="showDemoCredentials" class="login-view__demo">
        <button
          type="button"
          class="login-view__demo-toggle"
          @click="demoExpanded = !demoExpanded"
          :aria-expanded="demoExpanded"
        >
          <span aria-hidden="true">{{ demoExpanded ? '▼' : '▶' }}</span>
          💡 Identifiants de démonstration
        </button>

        <div v-if="demoExpanded" class="login-view__demo-content">
          <div class="login-view__demo-item">
            <span class="login-view__demo-role">👑 Admin</span>
            <code class="login-view__demo-code">admin / admin123</code>
            <button
              type="button"
              class="login-view__demo-fill"
              @click="fillDemo('admin', 'admin123')"
              aria-label="Remplir avec les identifiants admin"
            >
              Utiliser
            </button>
          </div>
          <div class="login-view__demo-item">
            <span class="login-view__demo-role">👤 Utilisateur</span>
            <code class="login-view__demo-code">test / test123</code>
            <button
              type="button"
              class="login-view__demo-fill"
              @click="fillDemo('test', 'test123')"
              aria-label="Remplir avec les identifiants test"
            >
              Utiliser
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ====================================================================
      FOOTER
    ==================================================================== -->
    <footer class="login-view__bottom-footer">
      <span class="login-view__bottom-footer-brand">
        🧬 NexusDL {{ appVersion }}
      </span>
      <span class="login-view__bottom-footer-sep" aria-hidden="true">•</span>
      <span class="login-view__bottom-footer-copy">
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
  password: '',
  remember: true,
})

const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const infoMessage = ref('')
const shakeForm = ref(false)
const demoExpanded = ref(false)

const fieldErrors = reactive({
  username: '',
  password: '',
})

const usernameInputRef = ref(null)
const passwordInputRef = ref(null)

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
//  Configuration démo
// ==========================================================================

const showDemoCredentials = computed(() => {
  return import.meta.env.DEV || import.meta.env.VITE_SHOW_DEMO === 'true'
})

// ==========================================================================
//  Computed
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')
const currentYear = computed(() => new Date().getFullYear())

const redirectPath = computed(() => {
  const redirect = route.query.redirect
  if (typeof redirect === 'string') {
    // Sécurité : ne pas rediriger vers une URL externe
    if (redirect.startsWith('/') && !redirect.startsWith('//')) {
      return redirect
    }
  }
  return '/'
})

const isFormValid = computed(() => {
  return form.username.trim().length >= 3 && form.password.length >= 1
})

// ==========================================================================
//  Méthodes
// ==========================================================================

/**
 * Nettoie le message d'erreur global.
 */
function clearError() {
  errorMessage.value = ''
}

/**
 * Nettoie l'erreur d'un champ.
 * @param {string} field
 */
function clearFieldError(field) {
  if (fieldErrors[field]) {
    fieldErrors[field] = ''
  }
  if (errorMessage.value) {
    errorMessage.value = ''
  }
}

/**
 * Toggle la visibilité du mot de passe.
 */
function togglePasswordVisibility() {
  showPassword.value = !showPassword.value
  nextTick(() => {
    passwordInputRef.value?.focus()
  })
}

/**
 * Valide le formulaire.
 * @returns {boolean}
 */
function validateForm() {
  let valid = true

  fieldErrors.username = ''
  fieldErrors.password = ''

  if (!form.username.trim()) {
    fieldErrors.username = "Veuillez saisir votre nom d'utilisateur."
    valid = false
  } else if (form.username.trim().length < 3) {
    fieldErrors.username = "Le nom d'utilisateur doit contenir au moins 3 caractères."
    valid = false
  }

  if (!form.password) {
    fieldErrors.password = 'Veuillez saisir votre mot de passe.'
    valid = false
  }

  return valid
}

/**
 * Soumet le formulaire de connexion.
 */
async function handleLogin() {
  clearError()
  infoMessage.value = ''

  if (!validateForm()) {
    triggerShake()
    // Focus sur le premier champ en erreur
    nextTick(() => {
      if (fieldErrors.username) {
        usernameInputRef.value?.focus()
      } else if (fieldErrors.password) {
        passwordInputRef.value?.focus()
      }
    })
    return
  }

  loading.value = true

  try {
    const user = await authStore.login(
      form.username.trim(),
      form.password,
      form.remember
    )

    toast.success(`Bienvenue ${user?.username || ''} !`, '👋', 2500)

    // Redirection vers la page demandée ou l'accueil
    await router.push(redirectPath.value)
  } catch (err) {
    handleLoginError(err)
  } finally {
    loading.value = false
  }
}

/**
 * Gère les erreurs de connexion.
 * @param {Error} err
 */
function handleLoginError(err) {
  const status = err.response?.status
  const detail = err.response?.data?.detail

  if (status === 401) {
    errorMessage.value = 'Nom d\'utilisateur ou mot de passe incorrect.'
    fieldErrors.password = 'Mot de passe incorrect'
    triggerShake()
  } else if (status === 403) {
    errorMessage.value = 'Votre compte est désactivé. Contactez un administrateur.'
  } else if (status === 429) {
    const retryAfter = err.response?.headers?.['retry-after'] || 60
    errorMessage.value = `Trop de tentatives. Réessayez dans ${retryAfter} secondes.`
  } else if (status >= 500) {
    errorMessage.value = 'Le serveur est temporairement indisponible.'
  } else if (!err.response) {
    errorMessage.value = 'Impossible de contacter le serveur. Vérifiez votre connexion.'
  } else {
    errorMessage.value = detail || 'Une erreur est survenue lors de la connexion.'
  }

  // Focus sur le champ mot de passe en cas d'erreur d'authentification
  if (status === 401) {
    nextTick(() => {
      passwordInputRef.value?.focus()
      passwordInputRef.value?.select?.()
    })
  }
}

/**
 * Déclenche l'animation de "shake" sur la carte.
 */
function triggerShake() {
  shakeForm.value = true
  setTimeout(() => {
    shakeForm.value = false
  }, 500)
}

/**
 * Gère la connexion OAuth (placeholder).
 * @param {string} provider
 */
function handleOAuth(provider) {
  infoMessage.value = `Connexion via ${provider} bientôt disponible.`
  toast.info(`OAuth ${provider} à venir`, 'ℹ️')
}

/**
 * Remplit le formulaire avec des identifiants de démonstration.
 * @param {string} username
 * @param {string} password
 */
function fillDemo(username, password) {
  form.username = username
  form.password = password
  errorMessage.value = ''
  fieldErrors.username = ''
  fieldErrors.password = ''
  toast.info('Identifiants remplis', '💡', 1500)
}

/**
 * Gestion du clavier (Entrée pour soumettre).
 * @param {KeyboardEvent} event
 */
function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey && !loading.value) {
    // Le formulaire gère déjà l'Enter via @submit
  }
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(() => {
  // Afficher un message si l'utilisateur vient d'être déconnecté
  if (route.query.logout === 'true') {
    infoMessage.value = 'Vous avez été déconnecté avec succès.'
  }

  // Afficher un message si la session a expiré
  if (route.query.expired === 'true') {
    infoMessage.value = 'Votre session a expiré. Veuillez vous reconnecter.'
  }

  // Focus automatique sur le champ username
  nextTick(() => {
    usernameInputRef.value?.focus()
  })

  // Log de débogage
  console.log('🔐 [LoginView] Chargée — redirection post-login :', redirectPath.value)
})

onUnmounted(() => {
  // Nettoyage
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.login-view {
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

.login-view__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.login-view__bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at center, #000 30%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse at center, #000 30%, transparent 75%);
}

.login-view__bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: loginGlow 8s ease-in-out infinite alternate;

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

@keyframes loginGlow {
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

.login-view__content {
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

.login-view__brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  text-align: center;
}

.login-view__brand-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  transition: opacity 0.2s ease;

  &:hover {
    opacity: 0.85;
  }
}

.login-view__brand-icon {
  font-size: 2.2rem;
  filter: drop-shadow(0 0 12px rgba(0, 212, 255, 0.4));
  animation: loginIconFloat 3s ease-in-out infinite;
}

@keyframes loginIconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.login-view__brand-name {
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.login-view__brand-tagline {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
  letter-spacing: 0.02em;
}

// ==========================================================================
//  Carte de connexion
// ==========================================================================

.login-view__card {
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
    animation: loginShake 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97);
  }
}

@keyframes loginShake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-6px); }
  20%, 40%, 60%, 80% { transform: translateX(6px); }
}

// ==========================================================================
//  Header
// ==========================================================================

.login-view__header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.25rem;
  margin-bottom: 1.5rem;
}

.login-view__title {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  letter-spacing: -0.02em;
}

.login-view__subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Alertes
// ==========================================================================

.login-view__alert {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  margin-bottom: 1rem;
  border-radius: var(--radius-md, 8px);
  font-size: 0.8rem;
  animation: loginAlertIn 0.3s ease;

  &--error {
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid rgba(244, 67, 54, 0.35);
    color: var(--color-error, #f44336);
  }

  &--info {
    background: rgba(33, 150, 243, 0.1);
    border: 1px solid rgba(33, 150, 243, 0.3);
    color: var(--color-info, #2196f3);
  }
}

@keyframes loginAlertIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-view__alert-icon {
  flex-shrink: 0;
  font-size: 0.9rem;
}

.login-view__alert-text {
  flex: 1;
  line-height: 1.45;
}

.login-view__alert-close {
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

.login-view__form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.login-view__field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.login-view__label {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-secondary, #b0c0d8);
}

.login-view__label-required {
  color: var(--color-error, #f44336);
}

.login-view__input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.login-view__input-icon {
  position: absolute;
  left: 0.75rem;
  font-size: 0.95rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
  transition: color 0.15s ease;
}

.login-view__input {
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

  &--with-action {
    padding-right: 2.4rem;
  }

  &:focus {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15);
    background: var(--color-bg-hover, #253254);

    & + .login-view__input-action {
      opacity: 1;
    }
  }

  &:focus ~ .login-view__input-icon,
  &:focus + .login-view__input-icon {
    color: var(--color-primary, #00d4ff);
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
}

.login-view__input-action {
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

.login-view__field-error {
  margin: 0;
  font-size: 0.72rem;
  color: var(--color-error, #f44336);
  animation: loginFieldErrorIn 0.25s ease;
}

@keyframes loginFieldErrorIn {
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
//  Options
// ==========================================================================

.login-view__options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.login-view__checkbox {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
  position: relative;

  input[type='checkbox'] {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  input:checked + .login-view__checkbox-mark {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);

    &::after {
      opacity: 1;
      transform: scale(1);
    }
  }

  input:focus-visible + .login-view__checkbox-mark {
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.25);
  }

  &:hover .login-view__checkbox-mark {
    border-color: var(--color-primary, #00d4ff);
  }
}

.login-view__checkbox-mark {
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

.login-view__checkbox-label {
  font-size: 0.8rem;
  color: var(--color-text-secondary, #b0c0d8);
}

.login-view__forgot-link {
  font-size: 0.8rem;
  color: var(--color-primary, #00d4ff);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.15s ease;

  &:hover {
    color: var(--color-primary-light, #66e5ff);
    text-decoration: underline;
  }
}

// ==========================================================================
//  Submit
// ==========================================================================

.login-view__submit {
  margin-top: 0.25rem;
}

// ==========================================================================
//  OAuth
// ==========================================================================

.login-view__divider {
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

.login-view__oauth {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.login-view__oauth-btn {
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

.login-view__oauth-icon {
  font-size: 1.3rem;
}

.login-view__oauth-label {
  font-size: 0.65rem;
  font-weight: 500;
}

// ==========================================================================
//  Footer
// ==========================================================================

.login-view__footer {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--color-border, #1a2538);
  text-align: center;
}

.login-view__footer-text {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.login-view__footer-link {
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

.login-view__info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
  text-align: center;
}

.login-view__info-text {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  opacity: 0.8;
}

.login-view__info-redirect {
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
//  Démo
// ==========================================================================

.login-view__demo {
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(255, 152, 0, 0.05);
  border: 1px dashed rgba(255, 152, 0, 0.35);
  border-radius: var(--radius-md, 8px);
}

.login-view__demo-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  width: 100%;
  background: transparent;
  border: none;
  color: var(--color-warning, #ff9800);
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0;
  text-align: left;

  &:hover {
    text-decoration: underline;
  }
}

.login-view__demo-content {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-top: 0.6rem;
  padding-top: 0.6rem;
  border-top: 1px dashed rgba(255, 152, 0, 0.25);
  animation: loginAlertIn 0.2s ease;
}

.login-view__demo-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
}

.login-view__demo-role {
  flex-shrink: 0;
  color: var(--color-text-muted, #6a7a9a);
  min-width: 90px;
}

.login-view__demo-code {
  flex: 1;
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 0.72rem;
  color: var(--color-text-primary, #e8edf5);
  background: var(--color-bg-secondary, #141a2b);
  padding: 0.15rem 0.45rem;
  border-radius: var(--radius-sm, 4px);
  border: 1px solid var(--color-border, #1a2538);
}

.login-view__demo-fill {
  background: transparent;
  border: 1px solid var(--color-warning, #ff9800);
  color: var(--color-warning, #ff9800);
  border-radius: var(--radius-sm, 4px);
  padding: 0.15rem 0.5rem;
  font-size: 0.68rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-warning, #ff9800);
    color: var(--color-text-inverse, #0a0e1a);
  }
}

// ==========================================================================
//  Bottom footer
// ==========================================================================

.login-view__bottom-footer {
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

.login-view__bottom-footer-brand {
  font-weight: 600;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.login-view__bottom-footer-sep {
  opacity: 0.4;
}

.login-view__bottom-footer-copy {
  opacity: 0.75;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 480px) {
  .login-view {
    padding: 1rem 0.75rem;
  }

  .login-view__card {
    padding: 1.5rem 1.25rem;
  }

  .login-view__title {
    font-size: 1.35rem;
  }

  .login-view__brand-name {
    font-size: 1.5rem;
  }

  .login-view__brand-icon {
    font-size: 1.9rem;
  }

  .login-view__oauth {
    grid-template-columns: 1fr;
  }

  .login-view__oauth-btn {
    flex-direction: row;
    gap: 0.5rem;
    padding: 0.55rem;
  }

  .login-view__oauth-label {
    font-size: 0.75rem;
  }

  .login-view__demo-item {
    flex-wrap: wrap;
  }

  .login-view__demo-role {
    min-width: auto;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .login-view {
    background: var(--color-bg-primary, #f4f6fa);
  }

  .login-view__bg-grid {
    background-image:
      linear-gradient(rgba(0, 102, 204, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 102, 204, 0.03) 1px, transparent 1px);
  }

  .login-view__bg-glow {
    &--1 {
      background: radial-gradient(circle, rgba(0, 102, 204, 0.35) 0%, transparent 70%);
    }
    &--2 {
      background: radial-gradient(circle, rgba(0, 68, 179, 0.3) 0%, transparent 70%);
    }
  }

  .login-view__card {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    box-shadow:
      0 20px 60px rgba(0, 0, 0, 0.1),
      0 0 0 1px rgba(0, 102, 204, 0.05) inset;
  }

  .login-view__title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .login-view__subtitle,
  .login-view__brand-tagline,
  .login-view__info-text,
  .login-view__info-redirect,
  .login-view__footer-text {
    color: var(--color-text-muted, #7a8a9a);
  }

  .login-view__label {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .login-view__input {
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

  .login-view__checkbox-mark {
    background: var(--color-bg-input, #f0f2f5);
    border-color: var(--color-border, #d0d8e0);
  }

  .login-view__checkbox-label {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .login-view__divider {
    &::before,
    &::after {
      background: var(--color-border, #d0d8e0);
    }
  }

  .login-view__oauth-btn {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
    color: var(--color-text-secondary, #3d4a5c);

    &:hover:not(:disabled) {
      background: var(--color-bg-hover, #e3e8ef);
      color: var(--color-text-primary, #1a1a2e);
    }
  }

  .login-view__footer {
    border-color: var(--color-border, #d0d8e0);
  }

  .login-view__info-redirect code {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .login-view__demo {
    background: rgba(230, 81, 0, 0.05);
    border-color: rgba(230, 81, 0, 0.3);
  }

  .login-view__demo-toggle {
    color: var(--color-warning, #e65100);
  }

  .login-view__demo-code {
    background: var(--color-bg-secondary, #e9ecf2);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);
  }

  .login-view__demo-fill {
    border-color: var(--color-warning, #e65100);
    color: var(--color-warning, #e65100);

    &:hover {
      background: var(--color-warning, #e65100);
      color: #ffffff;
    }
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .login-view__brand-icon,
  .login-view__bg-glow,
  .login-view__card--shake,
  .login-view__alert,
  .login-view__field-error {
    animation: none !important;
  }
}
</style>
