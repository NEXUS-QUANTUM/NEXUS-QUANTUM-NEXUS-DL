<!-- ==========================================================================
  NexusDL 2.0 - NexusButton Component
  Fichier : frontend/src/components/common/NexusButton.vue
  Description : Composant de bouton ultra-complet (variantes, tailles, icônes,
                chargement, badge, tooltip, router-link, block, etc.)
  Version : 2.0.0
  Licence : GNU GPL v3.0
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
        'nexus-btn--with-badge': !!badge,
        'nexus-btn--active': active,
        'nexus-btn--flat': flat,
      },
    ]"
    :type="tag === 'button' ? type : undefined"
    :disabled="tag === 'button' ? disabled || loading : undefined"
    :aria-busy="loading"
    :aria-disabled="disabled || loading"
    :aria-label="ariaLabel || (iconOnly ? label : undefined)"
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
    <!-- Contenu : loading OU contenu normal -->
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
      <span v-else-if="!iconOnly" class="nexus-btn__loading-text">
        <slot name="loading">Chargement...</slot>
      </span>
    </template>

    <!-- Contenu normal -->
    <template v-else>
      <!-- Icône gauche -->
      <span
        v-if="hasIcon"
        class="nexus-btn__icon nexus-btn__icon--left"
        aria-hidden="true"
      >
        <slot name="icon">
          <component :is="icon" v-if="typeof icon === 'object'" />
          <span v-else>{{ icon }}</span>
        </slot>
      </span>

      <!-- Texte / Slot principal -->
      <span v-if="!iconOnly" class="nexus-btn__text">
        <slot>{{ label }}</slot>
      </span>

      <!-- Icône droite -->
      <span
        v-if="hasRightIcon"
        class="nexus-btn__icon nexus-btn__icon--right"
        aria-hidden="true"
      >
        <slot name="right-icon">
          <component :is="rightIcon" v-if="typeof rightIcon === 'object'" />
          <span v-else>{{ rightIcon }}</span>
        </slot>
      </span>
    </template>

    <!-- Badge (compteur) -->
    <span
      v-if="badge && !loading"
      class="nexus-btn__badge"
      :class="`nexus-btn__badge--${badgeVariant}`"
      aria-hidden="true"
    >
      {{ badge > maxBadge ? `${maxBadge}+` : badge }}
    </span>

    <!-- Tooltip natif -->
    <span v-if="tooltip && !iconOnly" class="nexus-btn__tooltip" role="tooltip">
      {{ tooltip }}
    </span>
  </component>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { computed, useSlots, ref, onMounted } from 'vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Variante de couleur */
  variant: {
    type: String,
    default: 'primary',
    validator: (val) =>
      [
        'primary',
        'secondary',
        'success',
        'warning',
        'error',
        'info',
        'neutral',
        'dark',
        'light',
        'ghost',
      ].includes(val),
  },
  /** Taille */
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['xs', 'sm', 'md', 'lg', 'xl'].includes(val),
  },
  /** Type HTML */
  type: {
    type: String,
    default: 'button',
    validator: (val) => ['button', 'submit', 'reset'].includes(val),
  },
  /** Tag HTML */
  tag: {
    type: String,
    default: 'button',
    validator: (val) => ['button', 'a', 'router-link', 'div', 'span'].includes(val),
  },
  /** Texte du bouton */
  label: {
    type: String,
    default: '',
  },
  /** Icône à gauche */
  icon: {
    type: [String, Object],
    default: null,
  },
  /** Icône à droite */
  rightIcon: {
    type: [String, Object],
    default: null,
  },
  /** Icône seulement */
  iconOnly: {
    type: Boolean,
    default: false,
  },
  /** Style outline */
  outline: {
    type: Boolean,
    default: false,
  },
  /** Style ghost (sans fond) */
  ghost: {
    type: Boolean,
    default: false,
  },
  /** Style pilule */
  pill: {
    type: Boolean,
    default: false,
  },
  /** Largeur pleine */
  block: {
    type: Boolean,
    default: false,
  },
  /** Majuscules */
  uppercase: {
    type: Boolean,
    default: false,
  },
  /** Style plat (sans ombre) */
  flat: {
    type: Boolean,
    default: false,
  },
  /** État actif */
  active: {
    type: Boolean,
    default: false,
  },
  /** État de chargement */
  loading: {
    type: Boolean,
    default: false,
  },
  /** Texte pendant le chargement */
  loadingText: {
    type: String,
    default: '',
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
  /** Maximum du badge */
  maxBadge: {
    type: Number,
    default: 99,
  },
  /** Variante du badge */
  badgeVariant: {
    type: String,
    default: 'error',
    validator: (val) =>
      ['primary', 'success', 'warning', 'error', 'info', 'neutral'].includes(val),
  },
  /** URL (tag="a") */
  href: {
    type: String,
    default: '',
  },
  /** Target (tag="a") */
  target: {
    type: String,
    default: '_self',
  },
  /** Rel (tag="a") */
  rel: {
    type: String,
    default: '',
  },
  /** To (tag="router-link") */
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
  /** Tooltip (affiché en dessous) */
  tooltip: {
    type: String,
    default: '',
  },
  /** Couleur personnalisée */
  customColor: {
    type: String,
    default: '',
  },
  /** Arrière-plan personnalisé */
  customBackground: {
    type: String,
    default: '',
  },
  /** Bordure personnalisée */
  customBorder: {
    type: String,
    default: '',
  },
})

// ==========================================================================
//  Émits
// ==========================================================================

const emit = defineEmits([
  'click',
  'focus',
  'blur',
  'mouseenter',
  'mouseleave',
])

// ==========================================================================
//  Slots
// ==========================================================================

const slots = useSlots()
const hasIcon = computed(() => !!props.icon || !!slots.icon)
const hasRightIcon = computed(() => !!props.rightIcon || !!slots['right-icon'])

// ==========================================================================
//  Références
// ==========================================================================

const buttonRef = ref(null)

// ==========================================================================
//  Computed
// ==========================================================================

const customStyle = computed(() => {
  const style = {}
  if (props.customColor) style.color = props.customColor
  if (props.customBackground) style.backgroundColor = props.customBackground
  if (props.customBorder) style.borderColor = props.customBorder
  return style
})

// ==========================================================================
//  Méthodes — Événements
// ==========================================================================

function handleClick(event) {
  if (props.disabled || props.loading) {
    event.preventDefault()
    event.stopPropagation()
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
//  Cycle de vie
// ==========================================================================

onMounted(() => {
  // Rien à faire, préparation pour futures extensions
})

// ==========================================================================
//  Exposition
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
//  Variables
// ==========================================================================

$btn-transition: all var(--transition-fast, 150ms) ease;

// ==========================================================================
//  Bouton principal
// ==========================================================================

.nexus-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-family: var(--font-family, inherit);
  font-weight: var(--font-weight-medium, 500);
  line-height: 1.4;
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
  overflow: hidden;

  // ========================================================================
  //  Tailles
  // ========================================================================

  &--xs {
    padding: 0.15rem 0.5rem;
    font-size: 0.65rem;
    border-radius: var(--radius-sm, 4px);
    min-height: 24px;
    min-width: 24px;
    gap: 0.25rem;

    &.nexus-btn--pill { border-radius: var(--radius-full, 9999px); }

    .nexus-btn__icon { font-size: 0.7rem; }
  }

  &--sm {
    padding: 0.3rem 0.8rem;
    font-size: 0.75rem;
    border-radius: var(--radius-sm, 4px);
    min-height: 32px;
    min-width: 32px;
    gap: 0.35rem;

    &.nexus-btn--pill { border-radius: var(--radius-full, 9999px); }

    .nexus-btn__icon { font-size: 0.8rem; }
  }

  &--md {
    padding: 0.5rem 1.2rem;
    font-size: 0.9rem;
    border-radius: var(--radius-md, 8px);
    min-height: 40px;
    min-width: 40px;

    &.nexus-btn--pill { border-radius: var(--radius-full, 9999px); }

    .nexus-btn__icon { font-size: 1rem; }
  }

  &--lg {
    padding: 0.65rem 1.6rem;
    font-size: 1rem;
    border-radius: var(--radius-lg, 12px);
    min-height: 48px;
    min-width: 48px;

    &.nexus-btn--pill { border-radius: var(--radius-full, 9999px); }

    .nexus-btn__icon { font-size: 1.15rem; }
  }

  &--xl {
    padding: 0.85rem 2rem;
    font-size: 1.1rem;
    border-radius: var(--radius-lg, 12px);
    min-height: 56px;
    min-width: 56px;

    &.nexus-btn--pill { border-radius: var(--radius-full, 9999px); }

    .nexus-btn__icon { font-size: 1.3rem; }
  }

  // ========================================================================
  //  Variantes (remplissage)
  // ========================================================================

  &--primary {
    background-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
    border-color: var(--color-primary, #00d4ff);

    &:hover:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      background-color: var(--color-primary-dark, #0099cc);
      border-color: var(--color-primary-dark, #0099cc);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
    }

    &:active:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      transform: translateY(0);
      box-shadow: 0 2px 6px rgba(0, 212, 255, 0.2);
    }
  }

  &--secondary {
    background-color: var(--color-secondary, #0066ff);
    color: #ffffff;
    border-color: var(--color-secondary, #0066ff);

    &:hover:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      background-color: var(--color-secondary-dark, #0044cc);
      border-color: var(--color-secondary-dark, #0044cc);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 102, 255, 0.3);
    }

    &:active:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      transform: translateY(0);
    }
  }

  &--success {
    background-color: var(--color-success, #4caf50);
    color: #ffffff;
    border-color: var(--color-success, #4caf50);

    &:hover:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      background-color: var(--color-success-dark, #388e3c);
      border-color: var(--color-success-dark, #388e3c);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }

    &:active:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      transform: translateY(0);
    }
  }

  &--warning {
    background-color: var(--color-warning, #ff9800);
    color: #ffffff;
    border-color: var(--color-warning, #ff9800);

    &:hover:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      background-color: var(--color-warning-dark, #f57c00);
      border-color: var(--color-warning-dark, #f57c00);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3);
    }

    &:active:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      transform: translateY(0);
    }
  }

  &--error {
    background-color: var(--color-error, #f44336);
    color: #ffffff;
    border-color: var(--color-error, #f44336);

    &:hover:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      background-color: var(--color-error-dark, #c62828);
      border-color: var(--color-error-dark, #c62828);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(244, 67, 54, 0.3);
    }

    &:active:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      transform: translateY(0);
    }
  }

  &--info {
    background-color: var(--color-info, #2196f3);
    color: #ffffff;
    border-color: var(--color-info, #2196f3);

    &:hover:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      background-color: var(--color-info-dark, #1565c0);
      border-color: var(--color-info-dark, #1565c0);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
    }

    &:active:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      transform: translateY(0);
    }
  }

  &--neutral {
    background-color: var(--color-bg-secondary, #141a2b);
    color: var(--color-text-secondary, #b0c0d8);
    border-color: var(--color-border, #1a2538);

    &:hover:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      background-color: var(--color-bg-hover, #253254);
      border-color: var(--color-border-light, #253254);
      color: var(--color-text-primary, #e8edf5);
      transform: translateY(-1px);
    }

    &:active:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      transform: translateY(0);
    }
  }

  &--dark {
    background-color: var(--color-bg-primary, #0a0e1a);
    color: var(--color-text-primary, #e8edf5);
    border-color: var(--color-border, #1a2538);

    &:hover:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      background-color: var(--color-bg-secondary, #141a2b);
      border-color: var(--color-border-light, #253254);
      transform: translateY(-1px);
    }
  }

  &--light {
    background-color: #ffffff;
    color: var(--color-text-primary, #1a1a2e);
    border-color: #d0d8e0;

    &:hover:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      background-color: #f4f6fa;
      transform: translateY(-1px);
    }
  }

  &--ghost {
    background-color: transparent;
    color: var(--color-text-secondary, #b0c0d8);
    border-color: transparent;

    &:hover:not(:disabled):not(.nexus-btn--loading):not(.nexus-btn--disabled) {
      background-color: var(--color-bg-hover, #253254);
      color: var(--color-text-primary, #e8edf5);
    }
  }

  // ========================================================================
  //  Modificateurs
  // ========================================================================

  &.nexus-btn--outline {
    background: transparent !important;
    border-width: 1.5px;

    &.nexus-btn--primary {
      color: var(--color-primary, #00d4ff);
      border-color: var(--color-primary, #00d4ff);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(0, 212, 255, 0.1) !important;
      }
    }

    &.nexus-btn--secondary {
      color: var(--color-secondary, #0066ff);
      border-color: var(--color-secondary, #0066ff);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(0, 102, 255, 0.1) !important;
      }
    }

    &.nexus-btn--success {
      color: var(--color-success, #4caf50);
      border-color: var(--color-success, #4caf50);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(76, 175, 80, 0.1) !important;
      }
    }

    &.nexus-btn--warning {
      color: var(--color-warning, #ff9800);
      border-color: var(--color-warning, #ff9800);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(255, 152, 0, 0.1) !important;
      }
    }

    &.nexus-btn--error {
      color: var(--color-error, #f44336);
      border-color: var(--color-error, #f44336);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(244, 67, 54, 0.1) !important;
      }
    }

    &.nexus-btn--info {
      color: var(--color-info, #2196f3);
      border-color: var(--color-info, #2196f3);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: rgba(33, 150, 243, 0.1) !important;
      }
    }

    &.nexus-btn--neutral {
      color: var(--color-text-secondary, #b0c0d8);
      border-color: var(--color-border, #1a2538);
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: var(--color-bg-hover, #253254) !important;
        color: var(--color-text-primary, #e8edf5);
      }
    }
  }

  &.nexus-btn--ghost {
    background: transparent !important;
    border-color: transparent !important;
  }

  &.nexus-btn--block {
    display: flex;
    width: 100%;
    justify-content: center;
  }

  &.nexus-btn--uppercase {
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  &.nexus-btn--active {
    background-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
    border-color: var(--color-primary, #00d4ff);
  }

  &.nexus-btn--flat {
    box-shadow: none !important;
  }

  &--disabled,
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
    transform: none !important;
    box-shadow: none !important;
  }

  &--loading {
    cursor: wait;
    pointer-events: none;

    .nexus-btn__text,
    .nexus-btn__icon,
    .nexus-btn__loading-text {
      opacity: 0.75;
    }
  }

  // ========================================================================
  //  Icon only
  // ========================================================================

  &--icon-only {
    padding: 0;

    &.nexus-btn--xs { width: 24px; height: 24px; }
    &.nexus-btn--sm { width: 32px; height: 32px; }
    &.nexus-btn--md { width: 40px; height: 40px; }
    &.nexus-btn--lg { width: 48px; height: 48px; }
    &.nexus-btn--xl { width: 56px; height: 56px; }

    &.nexus-btn--pill { border-radius: var(--radius-full, 9999px); }

    .nexus-btn__icon { margin: 0; }
  }

  // ========================================================================
  //  Éléments internes
  // ========================================================================

  &__text {
    display: inline-flex;
    align-items: center;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    line-height: 1;

    &--left { margin-right: 0.1rem; }
    &--right { margin-left: 0.1rem; }
  }

  &.nexus-btn--icon-only &__icon { margin: 0; }

  // ========================================================================
  //  Spinner
  // ========================================================================

  &__spinner {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.1em;
    height: 1.1em;
    flex-shrink: 0;
    animation: nexusBtnSpin 0.8s linear infinite;
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
    animation: nexusBtnSpinnerDash 1.5s ease-in-out infinite;
  }

  &__loading-text {
    display: inline-block;
  }

  // ========================================================================
  //  Badge
  // ========================================================================

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
    border: 2px solid var(--color-bg-primary, #0a0e1a);
    pointer-events: none;

    &--primary {
      background-color: var(--color-primary, #00d4ff);
      color: var(--color-text-inverse, #0a0e1a);
    }

    &--success {
      background-color: var(--color-success, #4caf50);
      color: #ffffff;
    }

    &--warning {
      background-color: var(--color-warning, #ff9800);
      color: #ffffff;
    }

    &--error {
      background-color: var(--color-error, #f44336);
      color: #ffffff;
    }

    &--info {
      background-color: var(--color-info, #2196f3);
      color: #ffffff;
    }

    &--neutral {
      background-color: var(--color-bg-secondary, #141a2b);
      color: var(--color-text-secondary, #b0c0d8);
      border-color: var(--color-border, #1a2538);
    }
  }

  // ========================================================================
  //  Tooltip natif (title)
  // ========================================================================

  &__tooltip {
    display: none;
  }

  // ========================================================================
  //  Focus
  // ========================================================================

  &:focus-visible {
    outline: 2px solid var(--color-primary, #00d4ff);
    outline-offset: 2px;
  }
}

// ==========================================================================
//  Animations
// ==========================================================================

@keyframes nexusBtnSpin {
  100% { transform: rotate(360deg); }
}

@keyframes nexusBtnSpinnerDash {
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
//  Support du thème clair
// ==========================================================================

.light-mode {
  .nexus-btn {
    &--neutral {
      background-color: #e9ecf2;
      color: var(--color-text-secondary, #3d4a5c);
      border-color: #d0d8e0;

      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: #e3e8ef;
        color: var(--color-text-primary, #1a1a2e);
      }
    }

    &--dark {
      background-color: #1a1a2e;
      color: #ffffff;
      border-color: #1a1a2e;

      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: #2a2a3e;
      }
    }

    &--light {
      background-color: #ffffff;
      color: var(--color-text-primary, #1a1a2e);
      border-color: #d0d8e0;

      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: #f4f6fa;
      }
    }

    &--ghost {
      &:hover:not(:disabled):not(.nexus-btn--loading) {
        background-color: #e3e8ef;
        color: var(--color-text-primary, #1a1a2e);
      }
    }

    &__badge {
      border-color: #ffffff;

      &--neutral {
        background-color: #e9ecf2;
        color: var(--color-text-secondary, #3d4a5c);
        border-color: #d0d8e0;
      }
    }
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .nexus-btn {
    transition: none !important;

    &:hover:not(:disabled):not(.nexus-btn--loading) {
      transform: none !important;
    }

    &__spinner,
    &__spinner-path {
      animation: none !important;
    }
  }
}
</style>
