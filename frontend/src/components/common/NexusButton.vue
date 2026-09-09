<!-- ==========================================================================
  NexusDL 2.0 - NexusButton Component
  Fichier : frontend/src/components/common/NexusButton.vue
  Description : Composant de bouton ultra-complet (variantes, tailles, icônes, chargement, etc.)
  Version : 2.0.0
========================================================================== -->

<template>
  <component
    :is="tag"
    ref="buttonRef"
    class="nexus-btn"
    :class="[
      `nexus-btn--${variant}`,
      `nexus-btn--${size}`,
      {
        'nexus-btn--outline': outline,
        'nexus-btn--ghost': ghost,
        'nexus-btn--pill': pill,
        'nexus-btn--icon-only': iconOnly,
        'nexus-btn--loading': loading,
        'nexus-btn--disabled': disabled || loading,
        'nexus-btn--block': block,
        'nexus-btn--uppercase': uppercase,
        'nexus-btn--with-icon': hasIcon,
        'nexus-btn--with-right-icon': hasRightIcon,
      }
    ]"
    :type="tag === 'button' ? type : undefined"
    :disabled="disabled || loading"
    :aria-busy="loading"
    :aria-disabled="disabled || loading"
    :aria-label="ariaLabel || label"
    :tabindex="disabled || loading ? -1 : tabindex"
    :to="tag === 'router-link' ? to : undefined"
    :href="tag === 'a' ? href : undefined"
    :target="tag === 'a' ? target : undefined"
    :rel="tag === 'a' ? rel : undefined"
    :style="customStyle"
    @click="handleClick"
    @focus="handleFocus"
    @blur="handleBlur"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- Indicateur de chargement (remplace le contenu si loading) -->
    <template v-if="loading">
      <span class="nexus-btn__spinner" aria-hidden="true">
        <svg
          class="nexus-btn__spinner-icon"
          viewBox="0 0 50 50"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            class="nexus-btn__spinner-path"
            cx="25"
            cy="25"
            r="20"
            fill="none"
            stroke-width="4"
          />
        </svg>
      </span>
      <span v-if="loadingText" class="nexus-btn__loading-text">
        {{ loadingText }}
      </span>
      <span v-else class="nexus-btn__loading-text">
        <slot name="loading">{{ defaultLoadingText }}</slot>
      </span>
    </template>

    <!-- Contenu normal -->
    <template v-else>
      <!-- Icône gauche -->
      <span v-if="icon" class="nexus-btn__icon nexus-btn__icon--left" aria-hidden="true">
        <component :is="icon" v-if="typeof icon === 'object'" />
        <span v-else>{{ icon }}</span>
      </span>

      <!-- Texte / Slot principal -->
      <span class="nexus-btn__text">
        <slot>{{ label }}</slot>
      </span>

      <!-- Icône droite -->
      <span v-if="rightIcon" class="nexus-btn__icon nexus-btn__icon--right" aria-hidden="true">
        <component :is="rightIcon" v-if="typeof rightIcon === 'object'" />
        <span v-else>{{ rightIcon }}</span>
      </span>
    </template>

    <!-- Badge optionnel (ex: compteur) -->
    <span
      v-if="badge && !loading"
      class="nexus-btn__badge"
      :class="`nexus-btn__badge--${badgeVariant}`"
    >
      {{ badge }}
    </span>

    <!-- Tooltip (via slot) -->
    <span v-if="$slots.tooltip" class="nexus-btn__tooltip">
      <slot name="tooltip" />
    </span>
  </component>
</template>

<script setup>
import { computed, useSlots, ref } from 'vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Variante du bouton */
  variant: {
    type: String,
    default: 'primary',
    validator: (val) =>
      ['primary', 'secondary', 'success', 'warning', 'error', 'info', 'neutral', 'dark', 'light'].includes(val),
  },
  /** Taille du bouton */
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['xs', 'sm', 'md', 'lg', 'xl'].includes(val),
  },
  /** Type HTML (pour les boutons) */
  type: {
    type: String,
    default: 'button',
    validator: (val) => ['button', 'submit', 'reset'].includes(val),
  },
  /** Tag HTML à utiliser (button, a, router-link) */
  tag: {
    type: String,
    default: 'button',
    validator: (val) => ['button', 'a', 'router-link', 'NuxtLink'].includes(val),
  },
  /** Texte du bouton (utilisé si slot vide) */
  label: {
    type: String,
    default: '',
  },
  /** Icône à gauche (emoji, chaîne, ou composant) */
  icon: {
    type: [String, Object],
    default: null,
  },
  /** Icône à droite (emoji, chaîne, ou composant) */
  rightIcon: {
    type: [String, Object],
    default: null,
  },
  /** Affiche uniquement l'icône (cache le texte) */
  iconOnly: {
    type: Boolean,
    default: false,
  },
  /** Style contour (transparent avec bordure) */
  outline: {
    type: Boolean,
    default: false,
  },
  /** Style ghost (transparent, pas de bordure) */
  ghost: {
    type: Boolean,
    default: false,
  },
  /** Style pilule (coins très arrondis) */
  pill: {
    type: Boolean,
    default: false,
  },
  /** Largeur pleine (block) */
  block: {
    type: Boolean,
    default: false,
  },
  /** Texte en majuscules */
  uppercase: {
    type: Boolean,
    default: false,
  },
  /** État de chargement */
  loading: {
    type: Boolean,
    default: false,
  },
  /** Texte affiché pendant le chargement (si non spécifié, garde le texte normal) */
  loadingText: {
    type: String,
    default: '',
  },
  /** Texte par défaut pendant le chargement (si slot loading vide) */
  defaultLoadingText: {
    type: String,
    default: 'Chargement...',
  },
  /** Désactivé */
  disabled: {
    type: Boolean,
    default: false,
  },
  /** Badge (compteur) */
  badge: {
    type: [String, Number],
    default: null,
  },
  /** Variante du badge */
  badgeVariant: {
    type: String,
    default: 'error',
    validator: (val) =>
      ['primary', 'success', 'warning', 'error', 'info', 'neutral'].includes(val),
  },
  /** URL (pour tag="a") */
  href: {
    type: String,
    default: '',
  },
  /** Target (pour tag="a") */
  target: {
    type: String,
    default: '_self',
  },
  /** Rel (pour tag="a") */
  rel: {
    type: String,
    default: '',
  },
  /** To (pour router-link) */
  to: {
    type: [String, Object],
    default: '',
  },
  /** Tabindex */
  tabindex: {
    type: [String, Number],
    default: 0,
  },
  /** Label ARIA personnalisé */
  ariaLabel: {
    type: String,
    default: '',
  },
  /** Couleur personnalisée (surcharge la variante) */
  customColor: {
    type: String,
    default: '',
  },
  /** Arrière-plan personnalisé */
  customBackground: {
    type: String,
    default: '',
  },
  /** Bordures personnalisées */
  customBorder: {
    type: String,
    default: '',
  },
})

// ==========================================================================
//  Émits
// ==========================================================================

const emit = defineEmits(['click', 'focus', 'blur', 'mouseenter', 'mouseleave'])

// ==========================================================================
//  Slots
// ==========================================================================

const slots = useSlots()
const hasIcon = computed(() => !!props.icon || !!slots.icon)
const hasRightIcon = computed(() => !!props.rightIcon || !!slots['right-icon'])

// ==========================================================================
//  Référence
// ==========================================================================

const buttonRef = ref(null)

// ==========================================================================
//  Styles calculés
// ==========================================================================

const customStyle = computed(() => {
  const style = {}
  if (props.customColor) {
    style.color = props.customColor
  }
  if (props.customBackground) {
    style.backgroundColor = props.customBackground
  }
  if (props.customBorder) {
    style.borderColor = props.customBorder
  }
  return style
})

// ==========================================================================
//  Gestionnaires d'événements
// ==========================================================================

function handleClick(event) {
  if (props.disabled || props.loading) {
    event.preventDefault()
    return
  }
  emit('click', event)
}

function handleFocus(event) {
  emit('focus', event)
}

function handleBlur(event) {
  emit('blur', event)
}

function handleMouseEnter(event) {
  emit('mouseenter', event)
}

function handleMouseLeave(event) {
  emit('mouseleave', event)
}

// ==========================================================================
//  Exposer la référence pour les méthodes natives (focus, etc.)
// ==========================================================================

defineExpose({
  focus: () => buttonRef.value?.focus(),
  blur: () => buttonRef.value?.blur(),
  click: () => buttonRef.value?.click(),
  $el: buttonRef,
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables du composant
// ==========================================================================

$btn-transition: all var(--transition-fast, 150ms) ease;
$btn-radius-sm: var(--radius-sm, 4px);
$btn-radius-md: var(--radius-md, 8px);
$btn-radius-lg: var(--radius-lg, 12px);
$btn-radius-full: var(--radius-full, 9999px);

// ==========================================================================
//  Styles du bouton
// ==========================================================================

.nexus-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-family: var(--font-family, inherit);
  font-weight: var(--font-weight-medium, 500);
  line-height: 1.5;
  text-align: center;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  user-select: none;
  border: 1px solid transparent;
  transition: $btn-transition;
  appearance: none;
  background: none;
  outline: none;
  vertical-align: middle;
  min-width: 40px;
  min-height: 40px;

  // --- Tailles ---
  &--xs {
    padding: 0.15rem 0.5rem;
    font-size: 0.65rem;
    border-radius: $btn-radius-sm;
    min-height: 24px;
    min-width: 24px;
    &.nexus-btn--pill {
      border-radius: $btn-radius-full;
    }
    .nexus-btn__icon {
      font-size: 0.7rem;
    }
  }

  &--sm {
    padding: 0.3rem 0.8rem;
    font-size: 0.75rem;
    border-radius: $btn-radius-sm;
    min-height: 32px;
    min-width: 32px;
    &.nexus-btn--pill {
      border-radius: $btn-radius-full;
    }
    .nexus-btn__icon {
      font-size: 0.8rem;
    }
  }

  &--md {
    padding: 0.5rem 1.2rem;
    font-size: 0.9rem;
    border-radius: $btn-radius-md;
    min-height: 40px;
    min-width: 40px;
    &.nexus-btn--pill {
      border-radius: $btn-radius-full;
    }
    .nexus-btn__icon {
      font-size: 1rem;
    }
  }

  &--lg {
    padding: 0.65rem 1.6rem;
    font-size: 1rem;
    border-radius: $btn-radius-lg;
    min-height: 48px;
    min-width: 48px;
    &.nexus-btn--pill {
      border-radius: $btn-radius-full;
    }
    .nexus-btn__icon {
      font-size: 1.1rem;
    }
  }

  &--xl {
    padding: 0.8rem 2rem;
    font-size: 1.1rem;
    border-radius: $btn-radius-lg;
    min-height: 56px;
    min-width: 56px;
    &.nexus-btn--pill {
      border-radius: $btn-radius-full;
    }
    .nexus-btn__icon {
      font-size: 1.2rem;
    }
  }

  // --- Variantes (remplissage) ---
  &--primary {
    background-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
    border-color: var(--color-primary, #00d4ff);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-primary-dark, #0099cc);
      border-color: var(--color-primary-dark, #0099cc);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
    }
    &:active:not(:disabled):not(.nexus-btn--loading) {
      transform: translateY(0);
    }
  }

  &--secondary {
    background-color: var(--color-secondary, #0066ff);
    color: var(--color-text-inverse, #ffffff);
    border-color: var(--color-secondary, #0066ff);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-secondary-dark, #0044cc);
      border-color: var(--color-secondary-dark, #0044cc);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 102, 255, 0.3);
    }
    &:active:not(:disabled):not(.nexus-btn--loading) {
      transform: translateY(0);
    }
  }

  &--success {
    background-color: var(--color-success, #4caf50);
    color: var(--color-text-inverse, #ffffff);
    border-color: var(--color-success, #4caf50);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-success-dark, #388e3c);
      border-color: var(--color-success-dark, #388e3c);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }
    &:active:not(:disabled):not(.nexus-btn--loading) {
      transform: translateY(0);
    }
  }

  &--warning {
    background-color: var(--color-warning, #ff9800);
    color: var(--color-text-inverse, #0a0e1a);
    border-color: var(--color-warning, #ff9800);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-warning-dark, #f57c00);
      border-color: var(--color-warning-dark, #f57c00);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3);
    }
    &:active:not(:disabled):not(.nexus-btn--loading) {
      transform: translateY(0);
    }
  }

  &--error {
    background-color: var(--color-error, #f44336);
    color: var(--color-text-inverse, #ffffff);
    border-color: var(--color-error, #f44336);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-error-dark, #c62828);
      border-color: var(--color-error-dark, #c62828);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(244, 67, 54, 0.3);
    }
    &:active:not(:disabled):not(.nexus-btn--loading) {
      transform: translateY(0);
    }
  }

  &--info {
    background-color: var(--color-info, #2196f3);
    color: var(--color-text-inverse, #ffffff);
    border-color: var(--color-info, #2196f3);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-info-dark, #1565c0);
      border-color: var(--color-info-dark, #1565c0);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
    }
    &:active:not(:disabled):not(.nexus-btn--loading) {
      transform: translateY(0);
    }
  }

  &--neutral {
    background-color: var(--color-bg-secondary, #141a2b);
    color: var(--color-text-secondary, #b0c0d8);
    border-color: var(--color-border, #1a2538);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-bg-hover, #253254);
      border-color: var(--color-border-light, #253254);
      transform: translateY(-1px);
    }
    &:active:not(:disabled):not(.nexus-btn--loading) {
      transform: translateY(0);
    }
  }

  &--dark {
    background-color: var(--color-bg-primary, #0a0e1a);
    color: var(--color-text-primary, #e8edf5);
    border-color: var(--color-border, #1a2538);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-bg-secondary, #141a2b);
      border-color: var(--color-border-light, #253254);
      transform: translateY(-1px);
    }
    &:active:not(:disabled):not(.nexus-btn--loading) {
      transform: translateY(0);
    }
  }

  &--light {
    background-color: var(--color-bg-card, #ffffff);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-bg-secondary, #e9ecf2);
      transform: translateY(-1px);
    }
    &:active:not(:disabled):not(.nexus-btn--loading) {
      transform: translateY(0);
    }
  }

  // --- Outline ---
  &.nexus-btn--outline {
    background: transparent !important;
    border-width: 1px;
    &.nexus-btn--primary {
      color: var(--color-primary, #00d4ff);
      border-color: var(--color-primary, #00d4ff);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(0, 212, 255, 0.1);
      }
    }
    &.nexus-btn--secondary {
      color: var(--color-secondary, #0066ff);
      border-color: var(--color-secondary, #0066ff);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(0, 102, 255, 0.1);
      }
    }
    &.nexus-btn--success {
      color: var(--color-success, #4caf50);
      border-color: var(--color-success, #4caf50);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(76, 175, 80, 0.1);
      }
    }
    &.nexus-btn--warning {
      color: var(--color-warning, #ff9800);
      border-color: var(--color-warning, #ff9800);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(255, 152, 0, 0.1);
      }
    }
    &.nexus-btn--error {
      color: var(--color-error, #f44336);
      border-color: var(--color-error, #f44336);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(244, 67, 54, 0.1);
      }
    }
    &.nexus-btn--info {
      color: var(--color-info, #2196f3);
      border-color: var(--color-info, #2196f3);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(33, 150, 243, 0.1);
      }
    }
    &.nexus-btn--neutral {
      color: var(--color-text-secondary, #b0c0d8);
      border-color: var(--color-border, #1a2538);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: var(--color-bg-hover, #253254);
      }
    }
  }

  // --- Ghost ---
  &.nexus-btn--ghost {
    background: transparent !important;
    border-color: transparent !important;
    color: var(--color-text-secondary, #b0c0d8);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-bg-hover, #253254);
      color: var(--color-text-primary, #e8edf5);
    }
    &.nexus-btn--primary {
      color: var(--color-primary, #00d4ff);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(0, 212, 255, 0.1);
      }
    }
    &.nexus-btn--secondary {
      color: var(--color-secondary, #0066ff);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(0, 102, 255, 0.1);
      }
    }
    &.nexus-btn--success {
      color: var(--color-success, #4caf50);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(76, 175, 80, 0.1);
      }
    }
    &.nexus-btn--warning {
      color: var(--color-warning, #ff9800);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(255, 152, 0, 0.1);
      }
    }
    &.nexus-btn--error {
      color: var(--color-error, #f44336);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(244, 67, 54, 0.1);
      }
    }
    &.nexus-btn--info {
      color: var(--color-info, #2196f3);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(33, 150, 243, 0.1);
      }
    }
  }

  // --- États ---
  &--block {
    display: flex;
    width: 100%;
    justify-content: center;
  }

  &--uppercase {
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  &--disabled,
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }

  &--loading {
    cursor: wait;
    pointer-events: none;
    .nexus-btn__text,
    .nexus-btn__icon {
      opacity: 0.5;
    }
  }

  &--icon-only {
    padding: 0;
    min-width: 0;
    width: auto;
    justify-content: center;
    .nexus-btn__text {
      display: none;
    }
    &.nexus-btn--xs {
      width: 24px;
      height: 24px;
      padding: 0;
    }
    &.nexus-btn--sm {
      width: 32px;
      height: 32px;
      padding: 0;
    }
    &.nexus-btn--md {
      width: 40px;
      height: 40px;
      padding: 0;
    }
    &.nexus-btn--lg {
      width: 48px;
      height: 48px;
      padding: 0;
    }
    &.nexus-btn--xl {
      width: 56px;
      height: 56px;
      padding: 0;
    }
    .nexus-btn__icon {
      margin: 0;
    }
  }

  // --- Badge ---
  &__badge {
    position: absolute;
    top: -6px;
    right: -6px;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    padding: 0 4px;
    font-size: 0.6rem;
    font-weight: var(--font-weight-bold, 700);
    border-radius: var(--radius-full, 9999px);
    line-height: 1;
    background-color: var(--color-error, #f44336);
    color: var(--color-text-inverse, #ffffff);
    border: 2px solid var(--color-bg-primary, #0a0e1a);
    pointer-events: none;

    &--primary {
      background-color: var(--color-primary, #00d4ff);
      color: var(--color-text-inverse, #0a0e1a);
    }
    &--success {
      background-color: var(--color-success, #4caf50);
      color: var(--color-text-inverse, #ffffff);
    }
    &--warning {
      background-color: var(--color-warning, #ff9800);
      color: var(--color-text-inverse, #0a0e1a);
    }
    &--error {
      background-color: var(--color-error, #f44336);
      color: var(--color-text-inverse, #ffffff);
    }
    &--info {
      background-color: var(--color-info, #2196f3);
      color: var(--color-text-inverse, #ffffff);
    }
    &--neutral {
      background-color: var(--color-bg-secondary, #141a2b);
      color: var(--color-text-secondary, #b0c0d8);
      border-color: var(--color-border, #1a2538);
    }
  }

  // --- Icônes ---
  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &--left {
      margin-right: 0.1rem;
    }
    &--right {
      margin-left: 0.1rem;
    }
  }

  &.nexus-btn--icon-only &__icon {
    margin: 0;
  }

  // --- Spinner ---
  &__spinner {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.2em;
    height: 1.2em;
    flex-shrink: 0;
    animation: nexus-btn-spin 0.8s linear infinite;
  }

  &__spinner-icon {
    width: 100%;
    height: 100%;
  }

  &__spinner-path {
    stroke: currentColor;
    stroke-linecap: round;
    stroke-dasharray: 90, 150;
    stroke-dashoffset: 0;
    animation: nexus-btn-spinner-dash 1.5s ease-in-out infinite;
  }

  &__loading-text {
    margin-left: 0.3rem;
  }

  // --- Tooltip ---
  &__tooltip {
    display: none;
  }

  // --- Focus ---
  &:focus-visible {
    outline: 2px solid var(--color-primary, #00d4ff);
    outline-offset: 2px;
  }
}

// ==========================================================================
//  Animations
// ==========================================================================

@keyframes nexus-btn-spin {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes nexus-btn-spinner-dash {
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
//  Support du thème sombre/clair (déjà géré via variables CSS)
// ==========================================================================

.dark-mode .nexus-btn {
  &--light {
    background-color: var(--color-bg-card, #1a2538);
    color: var(--color-text-primary, #e8edf5);
    border-color: var(--color-border, #1a2538);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-bg-secondary, #141a2b);
    }
  }
}

.light-mode .nexus-btn {
  &--dark {
    background-color: var(--color-bg-secondary, #e9ecf2);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);
    &:hover:not(:disabled):not(.nexus-btn--loading) {
      background-color: var(--color-bg-card, #ffffff);
    }
  }
}
</style>
