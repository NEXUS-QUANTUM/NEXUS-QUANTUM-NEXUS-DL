<!-- ==========================================================================
  NexusDL 2.0 - NexusSpinner Component
  Fichier : frontend/src/components/common/NexusSpinner.vue
  Description : Composant de chargement/attente ultra-complet (spinner, variants, tailles, couleurs, overlay)
  Version : 2.0.0
========================================================================== -->

<template>
  <div
    class="nexus-spinner"
    :class="[
      `nexus-spinner--${variant}`,
      `nexus-spinner--${size}`,
      {
        'nexus-spinner--inline': inline,
        'nexus-spinner--overlay': overlay,
        'nexus-spinner--fixed': fixed,
        'nexus-spinner--fullscreen': fullscreen,
        'nexus-spinner--with-label': !!label || $slots.label,
        'nexus-spinner--centered': centered,
        'nexus-spinner--custom-color': !!color,
      }
    ]"
    :style="customStyle"
    :aria-label="ariaLabel || 'Chargement...'"
    :aria-busy="true"
    role="status"
  >
    <!-- Le spinner proprement dit -->
    <div class="nexus-spinner__container">
      <div class="nexus-spinner__animation">
        <!-- Différents types de spinner selon la variante -->
        <template v-if="variant === 'dots'">
          <span class="nexus-spinner__dot" v-for="i in 3" :key="i" :style="{ animationDelay: `${i * 0.15}s` }">
            <span class="nexus-spinner__dot-inner" />
          </span>
        </template>

        <template v-else-if="variant === 'pulse'">
          <div class="nexus-spinner__pulse-ring">
            <div class="nexus-spinner__pulse-ring--inner" />
            <div class="nexus-spinner__pulse-ring--outer" />
          </div>
        </template>

        <template v-else-if="variant === 'bar'">
          <div class="nexus-spinner__bar-track">
            <div class="nexus-spinner__bar-progress" />
          </div>
        </template>

        <template v-else-if="variant === 'dots-wave'">
          <div class="nexus-spinner__wave">
            <span class="nexus-spinner__wave-dot" v-for="i in 5" :key="i" :style="{ animationDelay: `${i * 0.1}s` }" />
          </div>
        </template>

        <template v-else-if="variant === 'gradient'">
          <svg class="nexus-spinner__gradient-ring" viewBox="0 0 50 50">
            <defs>
              <linearGradient :id="gradientId" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" :stop-color="gradientStartColor" />
                <stop offset="100%" :stop-color="gradientEndColor" />
              </linearGradient>
            </defs>
            <circle
              class="nexus-spinner__gradient-path"
              cx="25"
              cy="25"
              r="20"
              fill="none"
              :stroke="`url(#${gradientId})`"
              stroke-width="4"
              stroke-linecap="round"
            />
          </svg>
        </template>

        <!-- Par défaut : spinner circulaire (classique) -->
        <template v-else>
          <svg class="nexus-spinner__circle" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
            <circle
              class="nexus-spinner__circle-path"
              cx="25"
              cy="25"
              r="20"
              fill="none"
              :stroke="strokeColor"
              stroke-width="4"
              stroke-linecap="round"
            />
          </svg>
        </template>
      </div>

      <!-- Label -->
      <div v-if="label || $slots.label" class="nexus-spinner__label">
        <slot name="label">
          <span class="nexus-spinner__label-text">{{ label || 'Chargement...' }}</span>
        </slot>
      </div>
    </div>

    <!-- Si overlay, on ajoute un fond semi-transparent derrière -->
    <div v-if="overlay" class="nexus-spinner__overlay-backdrop" :style="overlayStyle" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Variante du spinner */
  variant: {
    type: String,
    default: 'circle',
    validator: (val) =>
      ['circle', 'dots', 'pulse', 'bar', 'dots-wave', 'gradient', 'logo'].includes(val),
  },
  /** Taille du spinner */
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['xs', 'sm', 'md', 'lg', 'xl'].includes(val),
  },
  /** Couleur personnalisée (surcharge la variante) */
  color: {
    type: String,
    default: '',
  },
  /** Couleur de début du gradient (pour variant='gradient') */
  gradientStart: {
    type: String,
    default: '#00d4ff',
  },
  /** Couleur de fin du gradient (pour variant='gradient') */
  gradientEnd: {
    type: String,
    default: '#0066ff',
  },
  /** Label affiché sous le spinner */
  label: {
    type: String,
    default: '',
  },
  /** Label ARIA (accessibilité) */
  ariaLabel: {
    type: String,
    default: '',
  },
  /** Mode inline (sans marge, s'aligne sur le texte) */
  inline: {
    type: Boolean,
    default: false,
  },
  /** Mode overlay (fond semi-transparent) */
  overlay: {
    type: Boolean,
    default: false,
  },
  /** Position fixe (par rapport à la fenêtre) */
  fixed: {
    type: Boolean,
    default: false,
  },
  /** Plein écran (avec overlay) */
  fullscreen: {
    type: Boolean,
    default: false,
  },
  /** Centrer le contenu (flex) */
  centered: {
    type: Boolean,
    default: true,
  },
  /** Couleur de l'overlay (si overlay activé) */
  overlayColor: {
    type: String,
    default: 'rgba(0, 0, 0, 0.5)',
  },
  /** Z-index du spinner (pour overlay) */
  zIndex: {
    type: [String, Number],
    default: 1000,
  },
})

// ==========================================================================
//  Émits (aucun)
// ==========================================================================

// ==========================================================================
//  Styles calculés
// ==========================================================================

const strokeColor = computed(() => {
  if (props.color) return props.color
  // Couleurs par défaut selon la variante
  const map = {
    circle: 'var(--color-primary, #00d4ff)',
    dots: 'var(--color-primary, #00d4ff)',
    pulse: 'var(--color-primary, #00d4ff)',
    bar: 'var(--color-primary, #00d4ff)',
    dotsWave: 'var(--color-primary, #00d4ff)',
    gradient: 'var(--color-primary, #00d4ff)',
    logo: 'var(--color-primary, #00d4ff)',
  }
  return map[props.variant] || 'var(--color-primary, #00d4ff)'
})

const gradientId = `nexus-spinner-gradient-${Math.random().toString(36).slice(2, 7)}`
const gradientStartColor = computed(() => props.gradientStart)
const gradientEndColor = computed(() => props.gradientEnd)

const customStyle = computed(() => {
  const style = {}
  if (props.color) {
    // Appliquer la couleur personnalisée sur les variables CSS
    style.setProperty('--nexus-spinner-color', props.color)
  }
  if (props.fullscreen || props.fixed) {
    style.position = props.fixed ? 'fixed' : 'fixed'
    style.top = 0
    style.left = 0
    style.right = 0
    style.bottom = 0
    style.zIndex = props.zIndex
    style.display = 'flex'
    style.alignItems = 'center'
    style.justifyContent = 'center'
  }
  if (props.fullscreen) {
    style.backgroundColor = props.overlayColor
  }
  return style
})

const overlayStyle = computed(() => {
  if (props.overlay || props.fullscreen) {
    return {
      backgroundColor: props.overlayColor,
    }
  }
  return {}
})

// ==========================================================================
//  Exposer les méthodes (aucune)
// ==========================================================================
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$spinner-transition: all var(--transition-fast, 150ms) ease;

// ==========================================================================
//  Spinner principal
// ==========================================================================

.nexus-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  --nexus-spinner-color: var(--color-primary, #00d4ff);
  --nexus-spinner-bg: var(--color-bg-card, #1a2538);

  // --- Tailles ---
  &--xs {
    .nexus-spinner__circle {
      width: 16px;
      height: 16px;
    }
    .nexus-spinner__circle-path {
      stroke-width: 3px;
    }
    .nexus-spinner__dot {
      width: 6px;
      height: 6px;
    }
    .nexus-spinner__pulse-ring {
      width: 20px;
      height: 20px;
    }
    .nexus-spinner__bar-track {
      width: 60px;
      height: 3px;
    }
    .nexus-spinner__wave-dot {
      width: 4px;
      height: 4px;
    }
    .nexus-spinner__gradient-ring {
      width: 20px;
      height: 20px;
    }
    .nexus-spinner__label-text {
      font-size: 0.6rem;
    }
  }

  &--sm {
    .nexus-spinner__circle {
      width: 24px;
      height: 24px;
    }
    .nexus-spinner__circle-path {
      stroke-width: 3px;
    }
    .nexus-spinner__dot {
      width: 8px;
      height: 8px;
    }
    .nexus-spinner__pulse-ring {
      width: 28px;
      height: 28px;
    }
    .nexus-spinner__bar-track {
      width: 80px;
      height: 4px;
    }
    .nexus-spinner__wave-dot {
      width: 5px;
      height: 5px;
    }
    .nexus-spinner__gradient-ring {
      width: 28px;
      height: 28px;
    }
    .nexus-spinner__label-text {
      font-size: 0.7rem;
    }
  }

  &--md {
    .nexus-spinner__circle {
      width: 40px;
      height: 40px;
    }
    .nexus-spinner__circle-path {
      stroke-width: 4px;
    }
    .nexus-spinner__dot {
      width: 10px;
      height: 10px;
    }
    .nexus-spinner__pulse-ring {
      width: 44px;
      height: 44px;
    }
    .nexus-spinner__bar-track {
      width: 120px;
      height: 5px;
    }
    .nexus-spinner__wave-dot {
      width: 6px;
      height: 6px;
    }
    .nexus-spinner__gradient-ring {
      width: 44px;
      height: 44px;
    }
    .nexus-spinner__label-text {
      font-size: 0.85rem;
    }
  }

  &--lg {
    .nexus-spinner__circle {
      width: 56px;
      height: 56px;
    }
    .nexus-spinner__circle-path {
      stroke-width: 5px;
    }
    .nexus-spinner__dot {
      width: 14px;
      height: 14px;
    }
    .nexus-spinner__pulse-ring {
      width: 60px;
      height: 60px;
    }
    .nexus-spinner__bar-track {
      width: 160px;
      height: 6px;
    }
    .nexus-spinner__wave-dot {
      width: 8px;
      height: 8px;
    }
    .nexus-spinner__gradient-ring {
      width: 60px;
      height: 60px;
    }
    .nexus-spinner__label-text {
      font-size: 1rem;
    }
  }

  &--xl {
    .nexus-spinner__circle {
      width: 72px;
      height: 72px;
    }
    .nexus-spinner__circle-path {
      stroke-width: 6px;
    }
    .nexus-spinner__dot {
      width: 18px;
      height: 18px;
    }
    .nexus-spinner__pulse-ring {
      width: 76px;
      height: 76px;
    }
    .nexus-spinner__bar-track {
      width: 200px;
      height: 8px;
    }
    .nexus-spinner__wave-dot {
      width: 10px;
      height: 10px;
    }
    .nexus-spinner__gradient-ring {
      width: 76px;
      height: 76px;
    }
    .nexus-spinner__label-text {
      font-size: 1.1rem;
    }
  }

  // --- Inline ---
  &--inline {
    display: inline-flex;
    vertical-align: middle;
    margin: 0 0.2rem;
  }

  // --- Centered (par défaut, via flex) ---
  &--centered {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
  }

  // --- Overlay ---
  &--overlay {
    position: relative;
    .nexus-spinner__overlay-backdrop {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 1;
      border-radius: inherit;
    }
    .nexus-spinner__container {
      position: relative;
      z-index: 2;
    }
  }

  // --- Fixed / Fullscreen (géré par le style inline) ---
  &--fixed,
  &--fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: v-bind(zIndex);
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: v-bind(overlayColor);
  }

  // --- Custom color (via CSS variable) ---
  &--custom-color {
    .nexus-spinner__circle-path {
      stroke: var(--nexus-spinner-color) !important;
    }
    .nexus-spinner__dot-inner {
      background: var(--nexus-spinner-color) !important;
    }
    .nexus-spinner__pulse-ring--inner,
    .nexus-spinner__pulse-ring--outer {
      border-color: var(--nexus-spinner-color) !important;
    }
    .nexus-spinner__bar-progress {
      background: var(--nexus-spinner-color) !important;
    }
    .nexus-spinner__wave-dot {
      background: var(--nexus-spinner-color) !important;
    }
    .nexus-spinner__gradient-path {
      stroke: var(--nexus-spinner-color) !important;
    }
  }

  // --- Avec label ---
  &--with-label {
    .nexus-spinner__label {
      margin-top: 0.5rem;
    }
  }
}

// ==========================================================================
//  Container
// ==========================================================================

.nexus-spinner__container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  max-width: 100%;
}

// ==========================================================================
//  Animation (circulaire) - par défaut
// ==========================================================================

.nexus-spinner__circle {
  display: block;
  animation: nexus-spinner-spin 1s linear infinite;
}

.nexus-spinner__circle-path {
  stroke: var(--nexus-spinner-color, #00d4ff);
  stroke-linecap: round;
  stroke-dasharray: 90, 150;
  stroke-dashoffset: 0;
  animation: nexus-spinner-dash 1.5s ease-in-out infinite;
}

@keyframes nexus-spinner-spin {
  100% { transform: rotate(360deg); }
}

@keyframes nexus-spinner-dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

// ==========================================================================
//  Variante : Dots (3 points qui s'allument en cascade)
// ==========================================================================

.nexus-spinner__dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--nexus-spinner-color, #00d4ff);
  opacity: 0.2;
  animation: nexus-spinner-dot-fade 1.2s ease-in-out infinite;
  margin: 0 0.15rem;

  .nexus-spinner__dot-inner {
    display: block;
    width: 100%;
    height: 100%;
    border-radius: inherit;
    background: inherit;
  }
}

@keyframes nexus-spinner-dot-fade {
  0%, 100% {
    opacity: 0.2;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}

// ==========================================================================
//  Variante : Pulse (anneaux pulsants)
// ==========================================================================

.nexus-spinner__pulse-ring {
  position: relative;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;

  &--inner,
  &--outer {
    position: absolute;
    border-radius: 50%;
    border: 3px solid var(--nexus-spinner-color, #00d4ff);
    opacity: 0.3;
    animation: nexus-spinner-pulse 1.2s ease-in-out infinite;
    &--inner {
      width: 60%;
      height: 60%;
      animation-delay: 0.2s;
      opacity: 0.5;
    }
    &--outer {
      width: 100%;
      height: 100%;
      animation-delay: 0s;
    }
  }
}

@keyframes nexus-spinner-pulse {
  0%, 100% {
    transform: scale(0.9);
    opacity: 0.3;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.7;
  }
}

// ==========================================================================
//  Variante : Barre de progression
// ==========================================================================

.nexus-spinner__bar-track {
  width: 120px;
  height: 5px;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
  position: relative;
}

.nexus-spinner__bar-progress {
  width: 0%;
  height: 100%;
  background: var(--nexus-spinner-color, #00d4ff);
  border-radius: inherit;
  animation: nexus-spinner-bar 1.5s ease-in-out infinite;
}

@keyframes nexus-spinner-bar {
  0% {
    width: 0%;
    transform: translateX(-100%);
  }
  50% {
    width: 70%;
    transform: translateX(0%);
  }
  100% {
    width: 100%;
    transform: translateX(100%);
  }
}

// ==========================================================================
//  Variante : Dots Wave (5 points en vague)
// ==========================================================================

.nexus-spinner__wave {
  display: flex;
  align-items: center;
  gap: 0.15rem;
}

.nexus-spinner__wave-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--nexus-spinner-color, #00d4ff);
  animation: nexus-spinner-wave 1.2s ease-in-out infinite;
}

@keyframes nexus-spinner-wave {
  0%, 100% {
    transform: translateY(0);
    opacity: 0.3;
  }
  50% {
    transform: translateY(-0.6rem);
    opacity: 1;
  }
}

// ==========================================================================
//  Variante : Gradient (anneau dégradé)
// ==========================================================================

.nexus-spinner__gradient-ring {
  display: block;
  animation: nexus-spinner-spin 1s linear infinite;
}

.nexus-spinner__gradient-path {
  stroke-linecap: round;
  stroke-dasharray: 90, 150;
  stroke-dashoffset: 0;
  animation: nexus-spinner-dash 1.5s ease-in-out infinite;
}

// ==========================================================================
//  Label
// ==========================================================================

.nexus-spinner__label {
  margin-top: 0.5rem;
  color: var(--color-text-muted, #6a7a9a);
  text-align: center;
}

.nexus-spinner__label-text {
  font-size: 0.85rem;
  font-weight: var(--font-weight-normal, 400);
  opacity: 0.8;
}

// ==========================================================================
//  Overlay Backdrop
// ==========================================================================

.nexus-spinner__overlay-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: v-bind(overlayColor);
  z-index: 1;
  border-radius: inherit;
}

// ==========================================================================
//  Support du thème clair
// ==========================================================================

.light-mode {
  .nexus-spinner__bar-track {
    background: var(--color-bg-secondary, #e9ecf2);
  }
  .nexus-spinner__label-text {
    color: var(--color-text-muted, #7a8a9a);
  }
  .nexus-spinner__overlay-backdrop {
    background: v-bind(overlayColor);
  }
}
</style>
