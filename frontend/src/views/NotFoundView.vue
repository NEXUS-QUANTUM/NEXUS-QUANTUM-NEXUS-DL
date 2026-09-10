<!-- ==========================================================================
  NexusDL 2.0 - Not Found View (version complète)
  Fichier : frontend/src/views/NotFoundView.vue
  Description : Page 404 — Ressource introuvable. Affiche un message clair,
                propose des actions (retour, accueil, recherche), un mini
                moteur de recherche interne, suggestions de navigation,
                historique de navigation récente et informations techniques
                pliables pour le support.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="not-found-view">
    <!-- ====================================================================
      DÉCORATIONS DE FOND
    ==================================================================== -->
    <div class="not-found-view__bg" aria-hidden="true">
      <div class="not-found-view__bg-grid" />
      <div class="not-found-view__bg-glow" />
      <div class="not-found-view__particles">
        <span
          v-for="i in 20"
          :key="i"
          class="not-found-view__particle"
          :style="getParticleStyle(i)"
        />
      </div>
    </div>

    <!-- ====================================================================
      CONTENU PRINCIPAL
    ==================================================================== -->
    <div class="not-found-view__content">
      <!-- Icône principale -->
      <div class="not-found-view__icon-wrapper" aria-hidden="true">
        <span class="not-found-view__icon">🔍</span>
        <div class="not-found-view__icon-ring" />
        <div class="not-found-view__icon-ring not-found-view__icon-ring--delay" />
      </div>

      <!-- Code HTTP -->
      <h1 class="not-found-view__code">404</h1>

      <!-- Titre -->
      <h2 class="not-found-view__title">Page introuvable</h2>

      <!-- Message -->
      <p class="not-found-view__message">
        La page que vous recherchez n'existe pas, a été déplacée ou a été
        supprimée.
      </p>

      <!-- Chemin tenté -->
      <div v-if="currentPath" class="not-found-view__path">
        <span class="not-found-view__path-label">Chemin demandé :</span>
        <code class="not-found-view__path-value">{{ currentPath }}</code>
        <button
          type="button"
          class="not-found-view__path-copy"
          @click="copyPath"
          aria-label="Copier le chemin"
          title="Copier le chemin"
        >
          📋
        </button>
      </div>

      <!-- ================================================================
        MINI RECHERCHE INTERNE
      ================================================================ -->
      <div class="not-found-view__search">
        <p class="not-found-view__search-hint">
          Ou recherchez ce que vous cherchiez :
        </p>
        <form class="not-found-view__search-form" @submit.prevent="handleQuickSearch">
          <div class="not-found-view__search-wrapper">
            <span class="not-found-view__search-icon" aria-hidden="true">🔍</span>
            <input
              ref="searchInputRef"
              v-model="quickSearch"
              type="text"
              class="not-found-view__search-input"
              placeholder="Rechercher une série, un manga, une URL..."
              aria-label="Rechercher dans NexusDL"
              maxlength="200"
            />
            <button
              v-if="quickSearch"
              type="button"
              class="not-found-view__search-clear"
              @click="quickSearch = ''"
              aria-label="Effacer la recherche"
            >
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <NexusButton
            type="submit"
            variant="primary"
            size="md"
            :disabled="!quickSearch.trim()"
          >
            Rechercher
          </NexusButton>
        </form>
      </div>

      <!-- ================================================================
        ACTIONS PRINCIPALES
      ================================================================ -->
      <div class="not-found-view__actions">
        <NexusButton
          variant="primary"
          size="lg"
          @click="goHome"
          aria-label="Retourner à l'accueil"
        >
          🏠 Accueil
        </NexusButton>

        <NexusButton
          variant="neutral"
          size="lg"
          @click="goBack"
          :disabled="!canGoBack"
          aria-label="Retourner à la page précédente"
        >
          ← Retour
        </NexusButton>

        <NexusButton
          variant="info"
          size="lg"
          @click="goToSearch"
          aria-label="Aller à la recherche"
        >
          🔍 Rechercher
        </NexusButton>

        <NexusButton
          variant="ghost"
          size="lg"
          @click="goToLibrary"
          aria-label="Aller à la bibliothèque"
        >
          📚 Bibliothèque
        </NexusButton>
      </div>

      <!-- ================================================================
        SUGGESTIONS DE NAVIGATION
      ================================================================ -->
      <div class="not-found-view__suggestions">
        <h3 class="not-found-view__suggestions-title">
          🔗 Liens utiles
        </h3>
        <div class="not-found-view__suggestions-grid">
          <router-link
            v-for="link in usefulLinks"
            :key="link.to"
            :to="link.to"
            class="not-found-view__suggestion"
          >
            <span class="not-found-view__suggestion-icon" aria-hidden="true">{{ link.icon }}</span>
            <div class="not-found-view__suggestion-content">
              <span class="not-found-view__suggestion-title">{{ link.title }}</span>
              <span class="not-found-view__suggestion-desc">{{ link.description }}</span>
            </div>
            <span class="not-found-view__suggestion-arrow" aria-hidden="true">→</span>
          </router-link>
        </div>
      </div>

      <!-- ================================================================
        HISTORIQUE DE NAVIGATION
      ================================================================ -->
      <div v-if="recentRoutes.length > 0" class="not-found-view__history">
        <h3 class="not-found-view__history-title">
          🕐 Pages récemment visitées
        </h3>
        <ul class="not-found-view__history-list">
          <li
            v-for="(route, idx) in recentRoutes"
            :key="idx"
            class="not-found-view__history-item"
          >
            <button
              type="button"
              class="not-found-view__history-link"
              @click="navigateTo(route.path)"
            >
              <span class="not-found-view__history-icon" aria-hidden="true">📄</span>
              <span class="not-found-view__history-path">{{ route.path }}</span>
              <span class="not-found-view__history-name">{{ route.name }}</span>
            </button>
          </li>
        </ul>
      </div>

      <!-- ================================================================
        INFORMATIONS TECHNIQUES (pliables)
      ================================================================ -->
      <div class="not-found-view__technical-toggle">
        <button
          type="button"
          class="not-found-view__technical-btn"
          @click="showTechnical = !showTechnical"
          :aria-expanded="showTechnical"
        >
          <span aria-hidden="true">{{ showTechnical ? '▼' : '▶' }}</span>
          🔧 Informations techniques
        </button>
      </div>

      <div v-if="showTechnical" class="not-found-view__technical">
        <dl class="not-found-view__technical-list">
          <div class="not-found-view__technical-row">
            <dt>Code HTTP</dt>
            <dd>404 Not Found</dd>
          </div>
          <div class="not-found-view__technical-row">
            <dt>URL demandée</dt>
            <dd><code>{{ currentPath }}</code></dd>
          </div>
          <div class="not-found-view__technical-row">
            <dt>Timestamp</dt>
            <dd>{{ timestamp }}</dd>
          </div>
          <div class="not-found-view__technical-row">
            <dt>User Agent</dt>
            <dd class="not-found-view__technical-ua">{{ truncate(userAgent, 100) }}</dd>
          </div>
          <div v-if="referer" class="not-found-view__technical-row">
            <dt>Référent</dt>
            <dd><code>{{ truncate(referer, 80) }}</code></dd>
          </div>
          <div class="not-found-view__technical-row">
            <dt>Résolution</dt>
            <dd>{{ screenSize }}</dd>
          </div>
        </dl>
        <button
          type="button"
          class="not-found-view__technical-copy"
          @click="copyTechnicalInfo"
        >
          📋 Copier le rapport
        </button>
      </div>
    </div>

    <!-- ====================================================================
      FOOTER
    ==================================================================== -->
    <footer class="not-found-view__footer">
      <span class="not-found-view__footer-brand">
        🧬 NexusDL {{ appVersion }}
      </span>
      <span class="not-found-view__footer-sep" aria-hidden="true">•</span>
      <span class="not-found-view__footer-error">
        Erreur 404 — Page introuvable
      </span>
      <span class="not-found-view__footer-sep" aria-hidden="true">•</span>
      <span class="not-found-view__footer-copy">
        © {{ currentYear }} NexusDL Community — GNU GPL v3.0
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
import { useToast } from '@/composables/useToast'
import NexusButton from '@/components/common/NexusButton.vue'
import { truncate } from '@/utils/formatters'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables
// ==========================================================================

const router = useRouter()
const route = useRoute()
const toast = useToast()

// ==========================================================================
//  État réactif
// ==========================================================================

const quickSearch = ref('')
const showTechnical = ref(false)
const timestamp = ref(dayjs().format('DD/MM/YYYY HH:mm:ss'))
const userAgent = ref('')
const referer = ref('')
const screenSize = ref('')
const searchInputRef = ref(null)
const recentRoutes = ref([])

// ==========================================================================
//  Computed
// ==========================================================================

const appVersion = computed(() => import.meta.env.VITE_APP_VERSION || '2.0.0')
const currentYear = computed(() => new Date().getFullYear())

const currentPath = computed(() => {
  return route.fullPath || route.path || '/'
})

const canGoBack = computed(() => {
  return window.history.length > 1
})

const usefulLinks = [
  {
    to: '/',
    icon: '🏠',
    title: 'Accueil',
    description: 'Retourner à la page principale',
  },
  {
    to: '/search',
    icon: '🔍',
    title: 'Recherche',
    description: 'Rechercher et télécharger des séries',
  },
  {
    to: '/library',
    icon: '📚',
    title: 'Bibliothèque',
    description: 'Consulter vos téléchargements',
  },
  {
    to: '/queue',
    icon: '⏳',
    title: 'File d\'attente',
    description: 'Voir les téléchargements en cours',
  },
  {
    to: '/settings',
    icon: '⚙️',
    title: 'Paramètres',
    description: 'Configurer l\'application',
  },
  {
    to: '/login',
    icon: '🔐',
    title: 'Connexion',
    description: 'Se connecter à votre compte',
  },
]

// ==========================================================================
//  Méthodes — Navigation
// ==========================================================================

/**
 * Retour à la page précédente.
 */
function goBack() {
  if (canGoBack.value) {
    router.back()
  } else {
    goHome()
  }
}

/**
 * Retour à l'accueil.
 */
function goHome() {
  router.push('/')
}

/**
 * Aller à la recherche.
 */
function goToSearch() {
  router.push('/search')
}

/**
 * Aller à la bibliothèque.
 */
function goToLibrary() {
  router.push('/library')
}

/**
 * Navigue vers un chemin donné.
 * @param {string} path
 */
function navigateTo(path) {
  if (!path) return
  router.push(path).catch(() => {
    toast.error('Impossible de naviguer vers cette page', '❌')
  })
}

/**
 * Gère la recherche rapide.
 */
function handleQuickSearch() {
  const query = quickSearch.value.trim()
  if (!query) return

  // Si c'est une URL, aller sur /search avec l'URL
  if (query.startsWith('http://') || query.startsWith('https://')) {
    router.push({
      path: '/search',
      query: { q: query },
    })
  } else {
    router.push({
      path: '/library',
      query: { q: query },
    })
  }
  toast.info(`Recherche : "${truncate(query, 40)}"`, '🔍', 2000)
}

// ==========================================================================
//  Méthodes — Utilitaires
// ==========================================================================

/**
 * Copie le chemin dans le presse-papiers.
 */
async function copyPath() {
  try {
    await navigator.clipboard.writeText(currentPath.value)
    toast.success('Chemin copié', '📋')
  } catch (err) {
    toast.error('Impossible de copier', '❌')
  }
}

/**
 * Copie le rapport technique.
 */
async function copyTechnicalInfo() {
  const info = [
    '=== NexusDL 404 Not Found ===',
    `URL        : ${currentPath.value}`,
    `Timestamp  : ${timestamp.value}`,
    `User Agent : ${userAgent.value}`,
    `Referer    : ${referer.value || 'N/A'}`,
    `Résolution : ${screenSize.value}`,
  ].join('\n')

  try {
    await navigator.clipboard.writeText(info)
    toast.success('Rapport copié', '📋')
  } catch (err) {
    toast.error('Impossible de copier', '❌')
  }
}

/**
 * Génère un style pour une particule de fond.
 * @param {number} i
 * @returns {Object}
 */
function getParticleStyle(i) {
  const seed = i * 7.13
  const left = `${(seed * 13) % 100}%`
  const delay = `${(seed * 1.7) % 8}s`
  const duration = `${8 + (seed % 6)}s`
  const size = `${2 + (seed % 3)}px`
  return {
    left,
    animationDelay: delay,
    animationDuration: duration,
    width: size,
    height: size,
  }
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(() => {
  // Récupérer les infos techniques
  userAgent.value = navigator.userAgent || ''
  referer.value = document.referrer || ''
  screenSize.value = `${window.innerWidth}×${window.innerHeight} @ ${window.devicePixelRatio}x`

  // Récupérer les pages récemment visitées depuis sessionStorage
  try {
    const stored = sessionStorage.getItem('nexus-recent-routes')
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed)) {
        recentRoutes.value = parsed
          .filter((r) => r && r.path && r.path !== currentPath.value)
          .slice(0, 5)
      }
    }
  } catch (_) {
    // Ignorer
  }

  // Log pour le débogage
  console.warn('🔍 [404 Not Found]', {
    path: currentPath.value,
    fullPath: route.fullPath,
    query: route.query,
    referer: referer.value,
  })
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.not-found-view {
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
  text-align: center;
}

// ==========================================================================
//  Décorations de fond
// ==========================================================================

.not-found-view__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.not-found-view__bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at center, #000 30%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse at center, #000 30%, transparent 70%);
}

.not-found-view__bg-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 700px;
  height: 700px;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.1) 0%, transparent 70%);
  animation: notFoundGlow 4s ease-in-out infinite alternate;
}

@keyframes notFoundGlow {
  0% {
    opacity: 0.5;
    transform: translate(-50%, -50%) scale(1);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.1);
  }
}

.not-found-view__particles {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.not-found-view__particle {
  position: absolute;
  bottom: -10px;
  background: var(--color-primary, #00d4ff);
  border-radius: 50%;
  opacity: 0.5;
  animation: notFoundFloat linear infinite;
  filter: drop-shadow(0 0 4px rgba(0, 212, 255, 0.6));
}

@keyframes notFoundFloat {
  0% {
    transform: translateY(0) scale(1);
    opacity: 0;
  }
  10% {
    opacity: 0.6;
  }
  90% {
    opacity: 0.6;
  }
  100% {
    transform: translateY(-100vh) scale(0.4);
    opacity: 0;
  }
}

// ==========================================================================
//  Contenu
// ==========================================================================

.not-found-view__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  max-width: 720px;
  width: 100%;
}

// ==========================================================================
//  Icône principale
// ==========================================================================

.not-found-view__icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 130px;
  height: 130px;
  margin-bottom: 0.5rem;
}

.not-found-view__icon {
  font-size: 5rem;
  z-index: 2;
  animation: notFoundBounce 2.5s ease-in-out infinite;
  filter: drop-shadow(0 4px 16px rgba(0, 212, 255, 0.5));
}

.not-found-view__icon-ring {
  position: absolute;
  inset: 0;
  border: 3px solid rgba(0, 212, 255, 0.3);
  border-radius: 50%;
  animation: notFoundRingPulse 2.5s ease-in-out infinite;

  &--delay {
    animation-delay: -1.25s;
    border-color: rgba(0, 102, 255, 0.25);
  }
}

@keyframes notFoundBounce {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-10px) rotate(-5deg);
  }
}

@keyframes notFoundRingPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.25);
    opacity: 0.1;
  }
}

// ==========================================================================
//  Code HTTP
// ==========================================================================

.not-found-view__code {
  margin: 0;
  font-size: 5rem;
  font-weight: 900;
  line-height: 1;
  letter-spacing: -0.06em;
  background: linear-gradient(135deg, #00d4ff 0%, #0066ff 50%, #00d4ff 100%);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: notFoundGradient 4s ease-in-out infinite;
  filter: drop-shadow(0 2px 12px rgba(0, 212, 255, 0.3));
}

@keyframes notFoundGradient {
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

.not-found-view__title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  letter-spacing: -0.02em;
}

.not-found-view__message {
  margin: 0;
  max-width: 520px;
  font-size: 1rem;
  line-height: 1.6;
  color: var(--color-text-secondary, #b0c0d8);
}

// ==========================================================================
//  Chemin
// ==========================================================================

.not-found-view__path {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.9rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  font-size: 0.8rem;
  max-width: 100%;
}

.not-found-view__path-label {
  color: var(--color-text-muted, #6a7a9a);
  white-space: nowrap;
  flex-shrink: 0;
}

.not-found-view__path-value {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.75rem;
  color: var(--color-primary, #00d4ff);
  background: rgba(0, 212, 255, 0.08);
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-sm, 4px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}

.not-found-view__path-copy {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  padding: 0.15rem 0.35rem;
  border-radius: var(--radius-sm, 4px);
  font-size: 0.9rem;
  transition: all 0.15s ease;

  &:hover {
    color: var(--color-primary, #00d4ff);
    background: var(--color-bg-hover, #253254);
  }
}

// ==========================================================================
//  Recherche rapide
// ==========================================================================

.not-found-view__search {
  width: 100%;
  max-width: 560px;
  margin-top: 0.5rem;
}

.not-found-view__search-hint {
  margin: 0 0 0.5rem;
  font-size: 0.8rem;
  color: var(--color-text-muted, #6a7a9a);
}

.not-found-view__search-form {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.not-found-view__search-wrapper {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
}

.not-found-view__search-icon {
  position: absolute;
  left: 0.6rem;
  font-size: 0.9rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
}

.not-found-view__search-input {
  width: 100%;
  padding: 0.6rem 0.5rem 0.6rem 2.1rem;
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

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.not-found-view__search-clear {
  position: absolute;
  right: 0.3rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0 0.3rem;
  border-radius: var(--radius-sm, 4px);

  &:hover {
    color: var(--color-text-primary, #e8edf5);
  }
}

// ==========================================================================
//  Actions
// ==========================================================================

.not-found-view__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 0.75rem;
}

// ==========================================================================
//  Suggestions
// ==========================================================================

.not-found-view__suggestions {
  width: 100%;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border, #1a2538);
  text-align: left;
}

.not-found-view__suggestions-title {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
  text-align: center;
}

.not-found-view__suggestions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.6rem;
}

.not-found-view__suggestion {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 0.85rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  text-decoration: none;
  color: inherit;
  transition: all 0.2s ease;
  text-align: left;

  &:hover {
    transform: translateY(-2px);
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);

    .not-found-view__suggestion-arrow {
      transform: translateX(4px);
      opacity: 1;
      color: var(--color-primary, #00d4ff);
    }
  }
}

.not-found-view__suggestion-icon {
  font-size: 1.4rem;
  flex-shrink: 0;
}

.not-found-view__suggestion-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.not-found-view__suggestion-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.not-found-view__suggestion-desc {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  line-height: 1.35;
}

.not-found-view__suggestion-arrow {
  font-size: 1rem;
  color: var(--color-text-muted, #6a7a9a);
  opacity: 0.5;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

// ==========================================================================
//  Historique
// ==========================================================================

.not-found-view__history {
  width: 100%;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border, #1a2538);
  text-align: left;
}

.not-found-view__history-title {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-secondary, #b0c0d8);
  text-align: center;
}

.not-found-view__history-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.not-found-view__history-item {
  margin: 0;
}

.not-found-view__history-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.4rem 0.6rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text-secondary, #b0c0d8);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;

  &:hover {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-primary, #e8edf5);
  }
}

.not-found-view__history-icon {
  flex-shrink: 0;
  opacity: 0.6;
}

.not-found-view__history-path {
  flex: 1;
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 0.7rem;
  color: var(--color-primary, #00d4ff);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.not-found-view__history-name {
  flex-shrink: 0;
  font-size: 0.65rem;
  color: var(--color-text-muted, #6a7a9a);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

// ==========================================================================
//  Techniques
// ==========================================================================

.not-found-view__technical-toggle {
  margin-top: 1rem;
}

.not-found-view__technical-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.7rem;
  background: transparent;
  border: 1px dashed var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  font-size: 0.72rem;
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--color-text-muted, #6a7a9a);
    color: var(--color-text-secondary, #b0c0d8);
  }
}

.not-found-view__technical {
  width: 100%;
  margin-top: 0.6rem;
  padding: 0.85rem 1rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  text-align: left;
  animation: notFoundSlideIn 0.2s ease;
}

@keyframes notFoundSlideIn {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.not-found-view__technical-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin: 0;
}

.not-found-view__technical-row {
  display: grid;
  grid-template-columns: 130px 1fr;
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

.not-found-view__technical-ua {
  font-size: 0.7rem;
  line-height: 1.4;
}

.not-found-view__technical-copy {
  display: inline-flex;
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

// ==========================================================================
//  Footer
// ==========================================================================

.not-found-view__footer {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: center;
  margin-top: 2rem;
  padding-top: 1.25rem;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

.not-found-view__footer-brand {
  font-weight: 600;
  background: linear-gradient(135deg, #00d4ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.not-found-view__footer-sep {
  opacity: 0.4;
}

.not-found-view__footer-error {
  padding: 0.15rem 0.6rem;
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: var(--radius-full, 9999px);
  color: var(--color-primary, #00d4ff);
  font-weight: 500;
  font-size: 0.68rem;
}

.not-found-view__footer-copy {
  opacity: 0.75;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 640px) {
  .not-found-view__code {
    font-size: 3.5rem;
  }

  .not-found-view__title {
    font-size: 1.35rem;
  }

  .not-found-view__message {
    font-size: 0.9rem;
  }

  .not-found-view__icon-wrapper {
    width: 100px;
    height: 100px;
  }

  .not-found-view__icon {
    font-size: 3.5rem;
  }

  .not-found-view__search-form {
    flex-direction: column;
  }

  .not-found-view__actions {
    flex-direction: column;
    width: 100%;

    > * {
      width: 100%;
      justify-content: center;
    }
  }

  .not-found-view__suggestions-grid {
    grid-template-columns: 1fr;
  }

  .not-found-view__path {
    flex-direction: column;
    gap: 0.25rem;
    align-items: stretch;
  }

  .not-found-view__path-value {
    max-width: 100%;
  }

  .not-found-view__technical-row {
    grid-template-columns: 1fr;
    gap: 0.15rem;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .not-found-view {
    background: var(--color-bg-primary, #f4f6fa);
  }

  .not-found-view__bg-grid {
    background-image:
      linear-gradient(rgba(0, 102, 204, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 102, 204, 0.03) 1px, transparent 1px);
  }

  .not-found-view__bg-glow {
    background: radial-gradient(circle, rgba(0, 102, 204, 0.08) 0%, transparent 70%);
  }

  .not-found-view__title,
  .not-found-view__suggestion-title,
  .not-found-view__suggestions-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .not-found-view__message,
  .not-found-view__history-name {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .not-found-view__path,
  .not-found-view__suggestion,
  .not-found-view__history-link,
  .not-found-view__technical {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .not-found-view__search-input {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .not-found-view__path-value {
    background: rgba(0, 102, 204, 0.08);
    color: var(--color-primary, #0066cc);
  }

  .not-found-view__history-path {
    color: var(--color-primary, #0066cc);
  }

  .not-found-view__technical-row dd code {
    background: var(--color-bg-secondary, #e9ecf2);
  }

  .not-found-view__footer-error {
    background: rgba(0, 102, 204, 0.08);
    border-color: rgba(0, 102, 204, 0.25);
    color: var(--color-primary, #0066cc);
  }

  .not-found-view__technical-btn {
    border-color: var(--color-border, #d0d8e0);
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .not-found-view__icon,
  .not-found-view__icon-ring,
  .not-found-view__code,
  .not-found-view__bg-glow,
  .not-found-view__particle,
  .not-found-view__technical {
    animation: none !important;
  }

  .not-found-view__particles {
    display: none;
  }
}
</style>
