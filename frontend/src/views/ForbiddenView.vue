<!-- ==========================================================================
  NexusDL 2.0 - Forbidden View (version complète)
  Fichier : frontend/src/views/ForbiddenView.vue
  Description : Page 403 — Accès interdit. Affichée lorsqu'un utilisateur
                tente d'accéder à une ressource sans les permissions
                nécessaires (ex: admin, ressource protégée).
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="forbidden-view">
    <!-- Décorations de fond -->
    <div class="forbidden-view__bg" aria-hidden="true">
      <div class="forbidden-view__bg-grid" />
      <div class="forbidden-view__bg-glow" />
    </div>

    <!-- Contenu principal -->
    <div class="forbidden-view__content">
      <!-- Icône principale -->
      <div class="forbidden-view__icon-wrapper" aria-hidden="true">
        <span class="forbidden-view__icon">🚫</span>
        <div class="forbidden-view__icon-ring" />
      </div>

      <!-- Code HTTP -->
      <h1 class="forbidden-view__code">403</h1>

      <!-- Titre -->
      <h2 class="forbidden-view__title">Accès interdit</h2>

      <!-- Message -->
      <p class="forbidden-view__message">
        Vous n'avez pas les permissions nécessaires pour accéder à cette
        ressource.
      </p>

      <!-- Détails supplémentaires -->
      <div v-if="reason || currentPath" class="forbidden-view__details">
        <div v-if="currentPath" class="forbidden-view__detail">
          <span class="forbidden-view__detail-label">Ressource demandée :</span>
          <code class="forbidden-view__detail-value">{{ currentPath }}</code>
        </div>
        <div v-if="reason" class="forbidden-view__detail">
          <span class="forbidden-view__detail-label">Raison :</span>
          <code class="forbidden-view__detail-value">{{ reason }}</code>
        </div>
        <div v-if="requiredRole" class="forbidden-view__detail">
          <span class="forbidden-view__detail-label">Rôle requis :</span>
          <code class="forbidden-view__detail-value">{{ requiredRole }}</code>
        </div>
      </div>

      <!-- Actions -->
      <div class="forbidden-view__actions">
        <NexusButton
          variant="primary"
          size="lg"
          @click="goBack"
          aria-label="Retourner à la page précédente"
        >
          ← Retour
        </NexusButton>

        <NexusButton
          variant="neutral"
          size="lg"
          @click="goHome"
          aria-label="Retour à l'accueil"
        >
          🏠 Accueil
        </NexusButton>

        <NexusButton
          v-if="isAuthenticated"
          variant="ghost"
          size="lg"
          @click="goToDashboard"
          aria-label="Aller au tableau de bord"
        >
          📊 Tableau de bord
        </NexusButton>

        <NexusButton
          v-else
          variant="success"
          size="lg"
          @click="goToLogin"
          aria-label="Se connecter"
        >
          🔐 Se connecter
        </NexusButton>
      </div>

      <!-- Encart d'aide -->
      <div class="forbidden-view__help">
        <h3 class="forbidden-view__help-title">
          💡 Que faire ?
        </h3>
        <ul class="forbidden-view__help-list">
          <li>
            Vérifiez que vous êtes bien connecté avec le bon compte.
          </li>
          <li>
            Si vous pensez qu'il s'agit d'une erreur, contactez un
            administrateur.
          </li>
          <li>
            Retournez à la page précédente ou revenez à l'accueil pour
            continuer votre navigation.
          </li>
          <li v-if="isAuthenticated && !isAdmin">
            Certaines fonctionnalités sont réservées aux administrateurs.
          </li>
        </ul>
      </div>

      <!-- Informations utilisateur (si connecté) -->
      <div v-if="isAuthenticated" class="forbidden-view__user-info">
        <div class="forbidden-view__user-avatar">
          {{ getInitials(username) }}
        </div>
        <div class="forbidden-view__user-details">
          <span class="forbidden-view__user-name">{{ username }}</span>
          <span class="forbidden-view__user-role">
            Rôle : <strong>{{ userRole }}</strong>
          </span>
        </div>
      </div>

      <!-- Informations techniques -->
      <div v-if="showTechnicalInfo" class="forbidden-view__technical">
        <div class="forbidden-view__technical-header">
          <span class="forbidden-view__technical-title">🔍 Informations techniques</span>
          <button
            type="button"
            class="forbidden-view__technical-toggle"
            @click="showTechnicalInfo = false"
            aria-label="Masquer les informations techniques"
          >
            ▲
          </button>
        </div>
        <dl class="forbidden-view__technical-list">
          <div class="forbidden-view__technical-row">
            <dt>Code HTTP</dt>
            <dd>403 Forbidden</dd>
          </div>
          <div class="forbidden-view__technical-row">
            <dt>URL demandée</dt>
            <dd><code>{{ currentPath }}</code></dd>
          </div>
          <div class="forbidden-view__technical-row">
            <dt>Timestamp</dt>
            <dd>{{ timestamp }}</dd>
          </div>
          <div class="forbidden-view__technical-row">
            <dt>User Agent</dt>
            <dd class="forbidden-view__technical-ua">{{ truncate(userAgent, 80) }}</dd>
          </div>
          <div v-if="referer" class="forbidden-view__technical-row">
            <dt>Référent</dt>
            <dd><code>{{ truncate(referer, 60) }}</code></dd>
          </div>
        </dl>
        <button
          type="button"
          class="forbidden-view__technical-copy"
          @click="copyTechnicalInfo"
        >
          📋 Copier les informations
        </button>
      </div>

      <!-- Bouton pour afficher les infos techniques si masquées -->
      <button
        v-if="!showTechnicalInfo"
        type="button"
        class="forbidden-view__technical-show"
        @click="showTechnicalInfo = true"
      >
        🔍 Afficher les informations techniques
      </button>
    </div>

    <!-- Footer -->
    <footer class="forbidden-view__footer">
      <span class="forbidden-view__footer-brand">
        🧬 NexusDL {{ appVersion }}
      </span>
      <span class="forbidden-view__footer-error">
        Erreur 403 — Accès interdit
      </span>
    </footer>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import NexusButton from '@/components/common/NexusButton.vue'
import { truncate } from '@/utils/formatters'
import dayjs from 'dayjs'

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

const showTechnicalInfo = ref(false)
const timestamp = ref(dayjs().format('DD/MM/YYYY HH:mm:ss'))
const userAgent = ref('')
const referer = ref('')

// ==========================================================================
//  Computed
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')

const currentPath = computed(() => route.fullPath || route.path || '/')

const reason = computed(() => {
  return route.query.reason || route.meta?.reason || ''
})

const requiredRole = computed(() => {
  return route.query.required_role || route.meta?.requiredRole || ''
})

const isAuthenticated = computed(() => authStore.isAuthenticated)
const isAdmin = computed(() => authStore.isAdmin)
const username = computed(() => authStore.user?.username || 'Utilisateur')
const userRole = computed(() => authStore.user?.role || 'guest')

// ==========================================================================
//  Méthodes — Navigation
// ==========================================================================

/**
 * Retourne à la page précédente.
 * Si aucune page précédente n'existe, va à l'accueil.
 */
function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    goHome()
  }
}

/**
 * Retourne à l'accueil.
 */
function goHome() {
  router.push('/')
}

/**
 * Redirige vers le tableau de bord (si connecté).
 */
function goToDashboard() {
  router.push('/search')
}

/**
 * Redirige vers la page de connexion.
 */
function goToLogin() {
  router.push({
    name: 'login',
    query: { redirect: currentPath.value },
  })
}

// ==========================================================================
//  Méthodes — Utilitaires
// ==========================================================================

/**
 * Retourne les initiales d'un nom.
 * @param {string} name
 * @returns {string}
 */
function getInitials(name) {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

/**
 * Copie les informations techniques dans le presse-papiers.
 */
async function copyTechnicalInfo() {
  const info = [
    `=== NexusDL 403 Forbidden ===`,
    `URL        : ${currentPath.value}`,
    `Timestamp  : ${timestamp.value}`,
    `User Agent : ${userAgent.value}`,
    `Referer    : ${referer.value || 'N/A'}`,
    `Auth       : ${isAuthenticated.value ? 'Connecté' : 'Non connecté'}`,
    `Username   : ${isAuthenticated.value ? username.value : 'N/A'}`,
    `Role       : ${isAuthenticated.value ? userRole.value : 'N/A'}`,
    `Reason     : ${reason.value || 'N/A'}`,
    `Req Role   : ${requiredRole.value || 'N/A'}`,
  ].join('\n')

  try {
    await navigator.clipboard.writeText(info)
    toast.success('Informations copiées', '📋')
  } catch (err) {
    toast.error('Impossible de copier', '❌')
  }
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(() => {
  // Récupérer les informations techniques
  userAgent.value = navigator.userAgent || ''
  referer.value = document.referrer || ''

  // Log pour le débogage
  console.warn('🚫 [403 Forbidden]', {
    path: currentPath.value,
    reason: reason.value,
    requiredRole: requiredRole.value,
    isAuthenticated: isAuthenticated.value,
    userRole: userRole.value,
  })
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.forbidden-view {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem 1rem;
  background: var(--color-bg-primary, #0a0e1a);
  overflow: hidden;
  text-align: center;
}

// ==========================================================================
//  Décorations de fond
// ==========================================================================

.forbidden-view__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.forbidden-view__bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(244, 67, 54, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(244, 67, 54, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at center, #000 30%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse at center, #000 30%, transparent 70%);
}

.forbidden-view__bg-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(244, 67, 54, 0.15) 0%, transparent 70%);
  animation: forbiddenGlow 4s ease-in-out infinite alternate;
}

@keyframes forbiddenGlow {
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

.forbidden-view__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  max-width: 620px;
  width: 100%;
}

// ==========================================================================
//  Icône principale
// ==========================================================================

.forbidden-view__icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  margin-bottom: 0.5rem;
}

.forbidden-view__icon {
  font-size: 4.5rem;
  z-index: 2;
  animation: forbiddenBounce 2s ease-in-out infinite;
  filter: drop-shadow(0 4px 12px rgba(244, 67, 54, 0.4));
}

.forbidden-view__icon-ring {
  position: absolute;
  inset: 0;
  border: 3px solid rgba(244, 67, 54, 0.3);
  border-radius: 50%;
  animation: forbiddenRingPulse 2.5s ease-in-out infinite;
}

@keyframes forbiddenBounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

@keyframes forbiddenRingPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.2;
  }
}

// ==========================================================================
//  Code HTTP
// ==========================================================================

.forbidden-view__code {
  margin: 0;
  font-size: 5rem;
  font-weight: 900;
  line-height: 1;
  letter-spacing: -0.05em;
  background: linear-gradient(135deg, #f44336, #ff9800, #f44336);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: forbiddenGradient 3s ease-in-out infinite;
  filter: drop-shadow(0 2px 8px rgba(244, 67, 54, 0.3));
}

@keyframes forbiddenGradient {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

// ==========================================================================
//  Titre & Message
// ==========================================================================

.forbidden-view__title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.forbidden-view__message {
  margin: 0;
  max-width: 480px;
  font-size: 1rem;
  line-height: 1.6;
  color: var(--color-text-secondary, #b0c0d8);
}

// ==========================================================================
//  Détails
// ==========================================================================

.forbidden-view__details {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  width: 100%;
  max-width: 480px;
  padding: 0.75rem 1rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  text-align: left;
}

.forbidden-view__detail {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  font-size: 0.8rem;
}

.forbidden-view__detail-label {
  color: var(--color-text-muted, #6a7a9a);
  font-weight: 500;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.forbidden-view__detail-value {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.75rem;
  color: var(--color-error, #f44336);
  background: rgba(244, 67, 54, 0.08);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm, 4px);
  word-break: break-all;
}

// ==========================================================================
//  Actions
// ==========================================================================

.forbidden-view__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 0.75rem;
}

// ==========================================================================
//  Encart d'aide
// ==========================================================================

.forbidden-view__help {
  width: 100%;
  max-width: 480px;
  margin-top: 1rem;
  padding: 0.9rem 1.1rem;
  background: rgba(255, 152, 0, 0.05);
  border: 1px solid rgba(255, 152, 0, 0.2);
  border-radius: var(--radius-md, 8px);
  text-align: left;
}

.forbidden-view__help-title {
  margin: 0 0 0.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-warning, #ff9800);
}

.forbidden-view__help-list {
  margin: 0;
  padding-left: 1.2rem;
  font-size: 0.8rem;
  line-height: 1.7;
  color: var(--color-text-secondary, #b0c0d8);

  li {
    margin-bottom: 0.2rem;

    &:last-child {
      margin-bottom: 0;
    }
  }
}

// ==========================================================================
//  Info utilisateur
// ==========================================================================

.forbidden-view__user-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 0.9rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-full, 9999px);
  margin-top: 0.75rem;
}

.forbidden-view__user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f44336, #ff9800);
  color: #ffffff;
  font-weight: 700;
  font-size: 0.95rem;
  flex-shrink: 0;
}

.forbidden-view__user-details {
  display: flex;
  flex-direction: column;
  text-align: left;
}

.forbidden-view__user-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.forbidden-view__user-role {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);

  strong {
    color: var(--color-warning, #ff9800);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
}

// ==========================================================================
//  Informations techniques
// ==========================================================================

.forbidden-view__technical {
  width: 100%;
  max-width: 480px;
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  text-align: left;
}

.forbidden-view__technical-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.forbidden-view__technical-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.forbidden-view__technical-toggle {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 0.7rem;
  padding: 0.1rem 0.3rem;
  border-radius: var(--radius-sm, 4px);

  &:hover {
    color: var(--color-text-primary, #e8edf5);
    background: var(--color-bg-hover, #253254);
  }
}

.forbidden-view__technical-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin: 0;
}

.forbidden-view__technical-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 0.5rem;
  font-size: 0.75rem;
  align-items: baseline;

  dt {
    color: var(--color-text-muted, #6a7a9a);
    font-weight: 500;
  }

  dd {
    margin: 0;
    color: var(--color-text-secondary, #b0c0d8);
    word-break: break-all;

    code {
      font-family: 'SFMono-Regular', Consolas, monospace;
      font-size: 0.7rem;
      padding: 0.1rem 0.35rem;
      background: var(--color-bg-secondary, #141a2b);
      border-radius: var(--radius-sm, 4px);
    }
  }
}

.forbidden-view__technical-ua {
  font-size: 0.7rem;
  line-height: 1.4;
}

.forbidden-view__technical-copy {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  width: 100%;
  margin-top: 0.75rem;
  padding: 0.4rem 0.6rem;
  background: transparent;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-secondary, #b0c0d8);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-primary, #e8edf5);
  }
}

.forbidden-view__technical-show {
  margin-top: 0.5rem;
  padding: 0.3rem 0.7rem;
  background: transparent;
  border: 1px dashed var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--color-text-muted, #6a7a9a);
    color: var(--color-text-secondary, #b0c0d8);
  }
}

// ==========================================================================
//  Footer
// ==========================================================================

.forbidden-view__footer {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
  justify-content: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #6a7a9a);
}

.forbidden-view__footer-brand {
  font-weight: 600;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.forbidden-view__footer-error {
  padding: 0.15rem 0.6rem;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  border-radius: var(--radius-full, 9999px);
  color: var(--color-error, #f44336);
  font-weight: 500;
  font-size: 0.7rem;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 640px) {
  .forbidden-view__code {
    font-size: 3.5rem;
  }

  .forbidden-view__title {
    font-size: 1.35rem;
  }

  .forbidden-view__message {
    font-size: 0.9rem;
  }

  .forbidden-view__icon-wrapper {
    width: 90px;
    height: 90px;
  }

  .forbidden-view__icon {
    font-size: 3.5rem;
  }

  .forbidden-view__actions {
    flex-direction: column;
    width: 100%;

    > * {
      width: 100%;
      justify-content: center;
    }
  }

  .forbidden-view__technical-row {
    grid-template-columns: 1fr;
    gap: 0.15rem;
  }

  .forbidden-view__user-info {
    width: 100%;
    border-radius: var(--radius-md, 8px);
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .forbidden-view {
    background: var(--color-bg-primary, #f4f6fa);
  }

  .forbidden-view__bg-grid {
    background-image:
      linear-gradient(rgba(198, 40, 40, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(198, 40, 40, 0.03) 1px, transparent 1px);
  }

  .forbidden-view__bg-glow {
    background: radial-gradient(circle, rgba(198, 40, 40, 0.1) 0%, transparent 70%);
  }

  .forbidden-view__title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .forbidden-view__message {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .forbidden-view__details,
  .forbidden-view__user-info,
  .forbidden-view__technical {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .forbidden-view__detail-value {
    background: rgba(198, 40, 40, 0.08);
    color: var(--color-error, #c62828);
  }

  .forbidden-view__help {
    background: rgba(230, 81, 0, 0.05);
    border-color: rgba(230, 81, 0, 0.2);
  }

  .forbidden-view__help-title {
    color: var(--color-warning, #e65100);
  }

  .forbidden-view__help-list {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .forbidden-view__user-name {
    color: var(--color-text-primary, #1a1a2e);
  }

  .forbidden-view__user-role strong {
    color: var(--color-warning, #e65100);
  }

  .forbidden-view__technical-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .forbidden-view__technical-header {
    border-color: var(--color-border, #d0d8e0);
  }

  .forbidden-view__technical-row dt {
    color: var(--color-text-muted, #7a8a9a);
  }

  .forbidden-view__technical-row dd {
    color: var(--color-text-secondary, #3d4a5c);

    code {
      background: var(--color-bg-secondary, #e9ecf2);
    }
  }

  .forbidden-view__technical-toggle:hover,
  .forbidden-view__technical-copy:hover {
    background: var(--color-bg-hover, #e3e8ef);
  }

  .forbidden-view__footer-error {
    background: rgba(198, 40, 40, 0.08);
    border-color: rgba(198, 40, 40, 0.25);
    color: var(--color-error, #c62828);
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .forbidden-view__icon,
  .forbidden-view__icon-ring,
  .forbidden-view__code,
  .forbidden-view__bg-glow {
    animation: none !important;
  }
}
</style>
