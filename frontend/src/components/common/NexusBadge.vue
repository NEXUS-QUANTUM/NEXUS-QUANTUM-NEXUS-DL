<!-- ==========================================================================
  NexusDL 2.0 - NexusBadge Component
  Fichier : frontend/src/components/common/NexusBadge.vue
  Description : Composant de badge ultra-complet (étiquettes, statuts, tags,
                compteurs, notifications, etc.) avec support du thème,
                animations, icônes, dots, et multiples variantes.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <component
    :is="tag"
    class="nexus-badge"
    :class="[
      `nexus-badge--${variant}`,
      `nexus-badge--${size}`,
      {
        'nexus-badge--pill': pill,
        'nexus-badge--outline': outline,
        'nexus-badge--rounded': rounded,
        'nexus-badge--closable': closable,
        'nexus-badge--clickable': clickable,
        'nexus-badge--dot': dot,
        'nexus-badge--with-icon': hasIcon,
        'nexus-badge--only-icon': iconOnly,
        'nexus-badge--block': block,
        'nexus-badge--uppercase': uppercase,
        'nexus-badge--pulse': pulse,
        'nexus-badge--glow': glow,
      },
    ]"
    :style="customStyle"
    :role="clickable ? 'button' : undefined"
    :tabindex="clickable ? 0 : undefined"
    :aria-label="ariaLabel || text || label"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >
    <!-- Indicateur dot -->
    <span v-if="dot" class="nexus-badge__dot" aria-hidden="true" />

    <!-- Icône -->
    <span v-if="hasIcon" class="nexus-badge__icon" aria-hidden="true">
      <component :is="icon" v-if="typeof icon === 'object'" />
      <span v-else>{{ icon }}</span>
    </span>

    <!-- Contenu -->
    <span v-if="!iconOnly" class="nexus-badge__content">
      <slot>{{ text || label }}</slot>
    </span>

    <!-- Compteur -->
    <span
      v-if="count !== null && count !== undefined"
      class="nexus-badge__count"
      :class="`nexus-badge__count--${countVariant}`"
    >
      {{ formattedCount }}
    </span>

    <!-- Bouton de fermeture -->
    <button
      v-if="closable"
      type="button"
      class="nexus-badge__close"
      :aria-label="closeLabel || 'Fermer'"
      @click.stop="handleClose"
    >
      <span aria-hidden="true">&times;</span>
    </button>
  </component>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { computed, useSlots } from 'vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Tag HTML à utiliser */
  tag: {
    type: String,
    default: 'span',
    validator: (val) => ['span', 'div', 'button', 'a', 'li', 'label'].includes(val),
  },
  /** Variante de couleur */
  variant: {
    type: String,
    default: 'neutral',
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
        'accent',
      ].includes(val),
  },
  /** Taille du badge */
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['xs', 'sm', 'md', 'lg', 'xl'].includes(val),
  },
  /** Texte du badge */
  text: {
    type: String,
    default: '',
  },
  /** Alias de text */
  label: {
    type: String,
    default: '',
  },
  /** Icône (emoji, chaîne ou composant) */
  icon: {
    type: [String, Object],
    default: null,
  },
  /** Afficher uniquement l'icône */
  iconOnly: {
    type: Boolean,
    default: false,
  },
  /** Style pilule */
  pill: {
    type: Boolean,
    default: false,
  },
  /** Style contour */
  outline: {
    type: Boolean,
    default: false,
  },
  /** Coins arrondis */
  rounded: {
    type: Boolean,
    default: true,
  },
  /** Bouton de fermeture */
  closable: {
    type: Boolean,
    default: false,
  },
  /** Rendre cliquable */
  clickable: {
    type: Boolean,
    default: false,
  },
  /** Indicateur dot */
  dot: {
    type: Boolean,
    default: false,
  },
  /** Largeur pleine */
  block: {
    type: Boolean,
    default: false,
  },
  /** Texte en majuscules */
  uppercase: {
    type: Boolean,
    default: false,
  },
  /** Animation pulse */
  pulse: {
    type: Boolean,
    default: false,
  },
  /** Effet glow */
  glow: {
    type: Boolean,
    default: false,
  },
  /** Compteur numérique */
  count: {
    type: [String, Number],
    default: null,
  },
  /** Variante du compteur */
  countVariant: {
    type: String,
    default: 'error',
    validator: (val) =>
      ['primary', 'success', 'warning', 'error', 'info', 'neutral'].includes(val),
  },
  /** Nombre maximum avant "99+" */
  maxCount: {
    type: Number,
    default: 99,
  },
  /** Label ARIA */
  ariaLabel: {
    type: String,
    default: '',
  },
  /** Label du bouton de fermeture */
  closeLabel: {
    type: String,
    default: 'Fermer',
  },
  /** Couleur personnalisée (texte) */
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

const emit = defineEmits(['click', 'close'])

// ==========================================================================
//  Slots
// ==========================================================================

const slots = useSlots()
const hasIcon = computed(() => !!props.icon || !!slots.icon)

// ==========================================================================
//  Computed
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

const formattedCount = computed(() => {
  if (props.count === null || props.count === undefined) return ''
  const num = Number(props.count)
  if (isNaN(num)) return String(props.count)
  if (num > props.maxCount) return `${props.maxCount}+`
  return String(num)
})

// ==========================================================================
//  Méthodes
// ==========================================================================

function handleClick(event) {
  if (props.clickable || props.tag === 'button') {
    emit('click', event)
  }
}

function handleClose(event) {
  emit('close', event)
}
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$badge-transition: all var(--transition-fast, 150ms) ease;

// ==========================================================================
//  Badge principal
// ==========================================================================

.nexus-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  font-weight: var(--font-weight-medium, 500);
  line-height: 1.4;
  white-space: nowrap;
  transition: $badge-transition;
  user-select: none;
  position: relative;
  border: 1px solid transparent;

  // ========================================================================
  //  Tailles
  // ========================================================================

  &--xs {
    padding: 0.1rem 0.35rem;
    font-size: 0.6rem;
    border-radius: var(--radius-sm, 4px);
    min-height: 16px;

    &.nexus-badge--pill {
      border-radius: var(--radius-full, 9999px);
    }

    .nexus-badge__icon {
      font-size: 0.65rem;
    }

    .nexus-badge__count {
      font-size: 0.55rem;
      min-width: 14px;
      height: 14px;
    }
  }

  &--sm {
    padding: 0.15rem 0.45rem;
    font-size: 0.68rem;
    border-radius: var(--radius-sm, 4px);
    min-height: 20px;

    &.nexus-badge--pill {
      border-radius: var(--radius-full, 9999px);
    }

    .nexus-badge__icon {
      font-size: 0.72rem;
    }

    .nexus-badge__count {
      font-size: 0.6rem;
      min-width: 16px;
      height: 16px;
    }
  }

  &--md {
    padding: 0.2rem 0.6rem;
    font-size: 0.75rem;
    border-radius: var(--radius-md, 8px);
    min-height: 24px;

    &.nexus-badge--pill {
      border-radius: var(--radius-full, 9999px);
    }

    .nexus-badge__icon {
      font-size: 0.82rem;
    }

    .nexus-badge__count {
      font-size: 0.65rem;
      min-width: 18px;
      height: 18px;
    }
  }

  &--lg {
    padding: 0.28rem 0.85rem;
    font-size: 0.85rem;
    border-radius: var(--radius-lg, 12px);
    min-height: 28px;

    &.nexus-badge--pill {
      border-radius: var(--radius-full, 9999px);
    }

    .nexus-badge__icon {
      font-size: 0.95rem;
    }

    .nexus-badge__count {
      font-size: 0.7rem;
      min-width: 20px;
      height: 20px;
    }
  }

  &--xl {
    padding: 0.35rem 1.1rem;
    font-size: 0.95rem;
    border-radius: var(--radius-lg, 12px);
    min-height: 34px;

    &.nexus-badge--pill {
      border-radius: var(--radius-full, 9999px);
    }

    .nexus-badge__icon {
      font-size: 1.05rem;
    }

    .nexus-badge__count {
      font-size: 0.75rem;
      min-width: 22px;
      height: 22px;
    }
  }

  // ========================================================================
  //  Variantes - Remplissage
  // ========================================================================

  &--primary {
    background-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
    border-color: var(--color-primary, #00d4ff);

    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-primary, #00d4ff);
      border-color: var(--color-primary, #00d4ff);
    }
  }

  &--secondary {
    background-color: var(--color-secondary, #0066ff);
    color: #ffffff;
    border-color: var(--color-secondary, #0066ff);

    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-secondary, #0066ff);
      border-color: var(--color-secondary, #0066ff);
    }
  }

  &--success {
    background-color: var(--color-success, #4caf50);
    color: #ffffff;
    border-color: var(--color-success, #4caf50);

    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-success, #4caf50);
      border-color: var(--color-success, #4caf50);
    }
  }

  &--warning {
    background-color: var(--color-warning, #ff9800);
    color: #ffffff;
    border-color: var(--color-warning, #ff9800);

    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-warning, #ff9800);
      border-color: var(--color-warning, #ff9800);
    }
  }

  &--error {
    background-color: var(--color-error, #f44336);
    color: #ffffff;
    border-color: var(--color-error, #f44336);

    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-error, #f44336);
      border-color: var(--color-error, #f44336);
    }
  }

  &--info {
    background-color: var(--color-info, #2196f3);
    color: #ffffff;
    border-color: var(--color-info, #2196f3);

    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-info, #2196f3);
      border-color: var(--color-info, #2196f3);
    }
  }

  &--neutral {
    background-color: var(--color-bg-secondary, #141a2b);
    color: var(--color-text-secondary, #b0c0d8);
    border-color: var(--color-border, #1a2538);

    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-text-secondary, #b0c0d8);
      border-color: var(--color-border, #1a2538);
    }
  }

  &--dark {
    background-color: var(--color-bg-primary, #0a0e1a);
    color: var(--color-text-primary, #e8edf5);
    border-color: var(--color-border, #1a2538);

    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-text-primary, #e8edf5);
      border-color: var(--color-text-primary, #e8edf5);
    }
  }

  &--light {
    background-color: #ffffff;
    color: #1a1a2e;
    border-color: #d0d8e0;

    &.nexus-badge--outline {
      background: transparent;
      color: #1a1a2e;
      border-color: #1a1a2e;
    }
  }

  &--accent {
    background-color: var(--color-accent, #ff4081);
    color: #ffffff;
    border-color: var(--color-accent, #ff4081);

    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-accent, #ff4081);
      border-color: var(--color-accent, #ff4081);
    }
  }

  // ========================================================================
  //  Modificateurs
  // ========================================================================

  &--rounded {
    border-radius: var(--radius-md, 8px);
  }

  &--block {
    display: flex;
    width: 100%;
    justify-content: center;
  }

  &--uppercase {
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  &--icon-only {
    padding: 0.3rem;
    aspect-ratio: 1 / 1;

    .nexus-badge__content {
      display: none;
    }
  }

  // Cliquable
  &--clickable {
    cursor: pointer;

    &:hover {
      transform: translateY(-1px);
      filter: brightness(1.1);
      box-shadow: var(--shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.3));
    }

    &:active {
      transform: translateY(0);
    }

    &:focus-visible {
      outline: 2px solid var(--color-primary, #00d4ff);
      outline-offset: 2px;
    }
  }

  // Closable
  &--closable {
    padding-right: 0.2rem;
  }

  // Pulse
  &--pulse {
    animation: nexusBadgePulse 2s ease-in-out infinite;
  }

  // Glow
  &--glow {
    box-shadow: 0 0 8px currentColor;
  }

  // ========================================================================
  //  Éléments internes
  // ========================================================================

  &__dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    flex-shrink: 0;
    animation: nexusBadgeDotPulse 1.5s ease-in-out infinite;

    .nexus-badge--sm & {
      width: 5px;
      height: 5px;
    }

    .nexus-badge--xs & {
      width: 4px;
      height: 4px;
    }

    .nexus-badge--lg & {
      width: 8px;
      height: 8px;
    }

    .nexus-badge--xl & {
      width: 10px;
      height: 10px;
    }
  }

  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    line-height: 1;
  }

  &__content {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
    font-size: 0.6rem;
    font-weight: var(--font-weight-bold, 700);
    line-height: 1;
    border-radius: var(--radius-full, 9999px);
    flex-shrink: 0;
    margin-left: 0.15rem;

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
      background-color: var(--color-bg-hover, #253254);
      color: var(--color-text-primary, #e8edf5);
    }
  }

  &__close {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    padding: 0;
    margin-left: 0.15rem;
    background: transparent;
    border: none;
    color: inherit;
    opacity: 0.7;
    cursor: pointer;
    border-radius: var(--radius-full, 9999px);
    transition: $badge-transition;
    font-size: 0.9em;
    line-height: 1;
    flex-shrink: 0;

    &:hover {
      opacity: 1;
      background: rgba(0, 0, 0, 0.15);
    }

    &:focus-visible {
      outline: 2px solid var(--color-primary, #00d4ff);
      outline-offset: 2px;
    }
  }
}

// ==========================================================================
//  Animations
// ==========================================================================

@keyframes nexusBadgePulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.75;
    transform: scale(1.02);
  }
}

@keyframes nexusBadgeDotPulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.3);
  }
}

// ==========================================================================
//  Support du thème clair
// ==========================================================================

.light-mode {
  .nexus-badge {
    &--neutral {
      background-color: var(--color-bg-card, #ffffff);
      color: var(--color-text-secondary, #3d4a5c);
      border-color: var(--color-border, #d0d8e0);

      &.nexus-badge--outline {
        background: transparent;
        color: var(--color-text-secondary, #3d4a5c);
        border-color: var(--color-border, #d0d8e0);
      }
    }

    &--dark {
      background-color: #1a1a2e;
      color: #ffffff;
      border-color: #1a1a2e;

      &.nexus-badge--outline {
        background: transparent;
        color: #1a1a2e;
        border-color: #1a1a2e;
      }
    }

    &__close:hover {
      background: rgba(0, 0, 0, 0.1);
    }
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .nexus-badge {
    &--pulse,
    &--glow {
      animation: none !important;
    }

    &__dot {
      animation: none !important;
    }

    &--clickable:hover {
      transform: none;
    }
  }
}
</style>
