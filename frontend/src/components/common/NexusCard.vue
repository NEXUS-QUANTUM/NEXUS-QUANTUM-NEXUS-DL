<!-- ==========================================================================
  NexusDL 2.0 - NexusCard Component
  Fichier : frontend/src/components/common/NexusCard.vue
  Description : Composant de carte générique (conteneur, layout, variantes)
  Version : 2.0.0
========================================================================== -->

<template>
  <article
    class="nexus-card"
    :class="[
      `nexus-card--${variant}`,
      `nexus-card--${size}`,
      {
        'nexus-card--bordered': bordered,
        'nexus-card--hoverable': hoverable,
        'nexus-card--clickable': clickable,
        'nexus-card--flat': flat,
        'nexus-card--outlined': outlined,
        'nexus-card--elevated': elevated,
        'nexus-card--with-header': hasHeader,
        'nexus-card--with-footer': hasFooter,
        'nexus-card--no-padding': noPadding,
        'nexus-card--full-height': fullHeight,
      }
    ]"
    :style="customStyle"
    @click="handleClick"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- Header -->
    <header v-if="hasHeader" class="nexus-card__header">
      <slot name="header">
        <div class="nexus-card__header-content">
          <h3 v-if="title" class="nexus-card__title">
            {{ title }}
          </h3>
          <span v-if="subtitle" class="nexus-card__subtitle">
            {{ subtitle }}
          </span>
        </div>
        <div v-if="$slots['header-actions']" class="nexus-card__header-actions">
          <slot name="header-actions" />
        </div>
      </slot>
    </header>

    <!-- Media (image/vidéo en couverture) -->
    <div v-if="$slots.media" class="nexus-card__media">
      <slot name="media" />
    </div>

    <!-- Body (contenu principal) -->
    <div class="nexus-card__body">
      <slot>{{ content }}</slot>
    </div>

    <!-- Footer -->
    <footer v-if="hasFooter" class="nexus-card__footer">
      <slot name="footer" />
    </footer>

    <!-- Badge/étiquette superposée -->
    <div v-if="$slots.badge" class="nexus-card__badge">
      <slot name="badge" />
    </div>

    <!-- Overlay (pour les effets au survol) -->
    <div v-if="overlay" class="nexus-card__overlay">
      <slot name="overlay">
        <div class="nexus-card__overlay-content">
          <slot name="overlay-content" />
        </div>
      </slot>
    </div>
  </article>
</template>

<script setup>
import { computed, useSlots } from 'vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Titre de la carte (slot header) */
  title: {
    type: String,
    default: '',
  },
  /** Sous-titre (slot header) */
  subtitle: {
    type: String,
    default: '',
  },
  /** Contenu texte (slot body) */
  content: {
    type: String,
    default: '',
  },
  /** Variante de style */
  variant: {
    type: String,
    default: 'default',
    validator: (val) =>
      ['default', 'primary', 'success', 'warning', 'error', 'info', 'neutral', 'dark', 'light'].includes(val),
  },
  /** Taille de la carte */
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['sm', 'md', 'lg'].includes(val),
  },
  /** Affiche une bordure */
  bordered: {
    type: Boolean,
    default: false,
  },
  /** Effet hover (surélévation) */
  hoverable: {
    type: Boolean,
    default: false,
  },
  /** Rendre cliquable (émet @click) */
  clickable: {
    type: Boolean,
    default: false,
  },
  /** Style plat (pas d'ombre) */
  flat: {
    type: Boolean,
    default: false,
  },
  /** Style contour (outline) */
  outlined: {
    type: Boolean,
    default: false,
  },
  /** Style avec ombre portée */
  elevated: {
    type: Boolean,
    default: true,
  },
  /** Supprime le padding intérieur */
  noPadding: {
    type: Boolean,
    default: false,
  },
  /** Hauteur 100% (parent flex/grid) */
  fullHeight: {
    type: Boolean,
    default: false,
  },
  /** Affiche un overlay au survol */
  overlay: {
    type: Boolean,
    default: false,
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
  /** Bordure personnalisée */
  customBorder: {
    type: String,
    default: '',
  },
})

// ==========================================================================
//  Émits
// ==========================================================================

const emit = defineEmits(['click', 'mouseenter', 'mouseleave'])

// ==========================================================================
//  Slots
// ==========================================================================

const slots = useSlots()

const hasHeader = computed(() => !!slots.header || !!(props.title || props.subtitle))
const hasFooter = computed(() => !!slots.footer)

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
//  Gestionnaires
// ==========================================================================

function handleClick(event) {
  if (props.clickable) {
    emit('click', event)
  }
}

function handleMouseEnter(event) {
  emit('mouseenter', event)
}

function handleMouseLeave(event) {
  emit('mouseleave', event)
}
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables du composant
// ==========================================================================

$card-radius-sm: var(--radius-sm, 4px);
$card-radius-md: var(--radius-md, 8px);
$card-radius-lg: var(--radius-lg, 12px);
$card-transition: all var(--transition-base, 300ms) ease;

// ==========================================================================
//  Styles de la carte
// ==========================================================================

.nexus-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: var(--color-bg-card, #1a2538);
  border-radius: $card-radius-md;
  overflow: hidden;
  transition: $card-transition;
  min-height: 80px;

  // --- Tailles ---
  &--sm {
    border-radius: $card-radius-sm;
    .nexus-card__header {
      padding: 0.5rem 0.75rem;
    }
    .nexus-card__body {
      padding: 0.5rem 0.75rem;
    }
    .nexus-card__footer {
      padding: 0.5rem 0.75rem;
    }
    .nexus-card__title {
      font-size: 1rem;
    }
    .nexus-card__subtitle {
      font-size: 0.75rem;
    }
  }

  &--md {
    border-radius: $card-radius-md;
    .nexus-card__header {
      padding: 0.75rem 1rem;
    }
    .nexus-card__body {
      padding: 0.75rem 1rem;
    }
    .nexus-card__footer {
      padding: 0.75rem 1rem;
    }
    .nexus-card__title {
      font-size: 1.15rem;
    }
    .nexus-card__subtitle {
      font-size: 0.85rem;
    }
  }

  &--lg {
    border-radius: $card-radius-lg;
    .nexus-card__header {
      padding: 1rem 1.25rem;
    }
    .nexus-card__body {
      padding: 1rem 1.25rem;
    }
    .nexus-card__footer {
      padding: 1rem 1.25rem;
    }
    .nexus-card__title {
      font-size: 1.35rem;
    }
    .nexus-card__subtitle {
      font-size: 0.95rem;
    }
  }

  // --- Sans padding ---
  &--no-padding {
    .nexus-card__header,
    .nexus-card__body,
    .nexus-card__footer {
      padding: 0;
    }
  }

  // --- Variantes ---
  &--default {
    background-color: var(--color-bg-card, #1a2538);
    color: var(--color-text-primary, #e8edf5);
    border: 1px solid var(--color-border, #1a2538);
    &.nexus-card--elevated {
      box-shadow: var(--shadow-md, 0 4px 12px rgba(0,0,0,0.4));
    }
  }

  &--primary {
    background-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
    border-color: var(--color-primary-dark, #0099cc);
    &.nexus-card--elevated {
      box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
    }
  }

  &--success {
    background-color: var(--color-success, #4caf50);
    color: var(--color-text-inverse, #ffffff);
    border-color: var(--color-success-dark, #388e3c);
    &.nexus-card--elevated {
      box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }
  }

  &--warning {
    background-color: var(--color-warning, #ff9800);
    color: var(--color-text-inverse, #0a0e1a);
    border-color: var(--color-warning-dark, #f57c00);
    &.nexus-card--elevated {
      box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3);
    }
  }

  &--error {
    background-color: var(--color-error, #f44336);
    color: var(--color-text-inverse, #ffffff);
    border-color: var(--color-error-dark, #c62828);
    &.nexus-card--elevated {
      box-shadow: 0 4px 12px rgba(244, 67, 54, 0.3);
    }
  }

  &--info {
    background-color: var(--color-info, #2196f3);
    color: var(--color-text-inverse, #ffffff);
    border-color: var(--color-info-dark, #1565c0);
    &.nexus-card--elevated {
      box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
    }
  }

  &--neutral {
    background-color: var(--color-bg-secondary, #141a2b);
    color: var(--color-text-secondary, #b0c0d8);
    border-color: var(--color-border, #1a2538);
    &.nexus-card--elevated {
      box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.3));
    }
  }

  &--dark {
    background-color: var(--color-bg-primary, #0a0e1a);
    color: var(--color-text-primary, #e8edf5);
    border-color: var(--color-border, #1a2538);
    &.nexus-card--elevated {
      box-shadow: var(--shadow-lg, 0 8px 24px rgba(0,0,0,0.5));
    }
  }

  &--light {
    background-color: var(--color-bg-card, #ffffff);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);
    &.nexus-card--elevated {
      box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
    }
  }

  // --- Outlined ---
  &--outlined {
    background: transparent !important;
    border-width: 2px;
    &.nexus-card--default {
      border-color: var(--color-border, #1a2538);
      color: var(--color-text-primary, #e8edf5);
    }
    &.nexus-card--primary {
      border-color: var(--color-primary, #00d4ff);
      color: var(--color-primary, #00d4ff);
    }
    &.nexus-card--success {
      border-color: var(--color-success, #4caf50);
      color: var(--color-success, #4caf50);
    }
    &.nexus-card--warning {
      border-color: var(--color-warning, #ff9800);
      color: var(--color-warning, #ff9800);
    }
    &.nexus-card--error {
      border-color: var(--color-error, #f44336);
      color: var(--color-error, #f44336);
    }
    &.nexus-card--info {
      border-color: var(--color-info, #2196f3);
      color: var(--color-info, #2196f3);
    }
    &.nexus-card--neutral {
      border-color: var(--color-border, #1a2538);
      color: var(--color-text-secondary, #b0c0d8);
    }
    &.nexus-card--dark {
      border-color: var(--color-bg-primary, #0a0e1a);
      color: var(--color-text-primary, #e8edf5);
    }
    &.nexus-card--light {
      border-color: var(--color-border, #d0d8e0);
      color: var(--color-text-primary, #1a1a2e);
    }
  }

  // --- Flat ---
  &--flat {
    box-shadow: none !important;
    border: none !important;
  }

  // --- Bordered (ajoute une bordure si non déjà présente) ---
  &--bordered {
    border: 1px solid var(--color-border, #1a2538);
  }

  // --- Hoverable ---
  &--hoverable {
    &:hover {
      transform: translateY(-4px);
      box-shadow: var(--shadow-lg, 0 8px 24px rgba(0,0,0,0.5));
      border-color: var(--color-primary, #00d4ff);
    }
  }

  // --- Clickable ---
  &--clickable {
    cursor: pointer;
    &:hover {
      border-color: var(--color-primary, #00d4ff);
    }
  }

  // --- Full height ---
  &--full-height {
    height: 100%;
  }

  // ==========================================================================
  //  Éléments internes
  // ==========================================================================

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--color-border, #1a2538);
    flex-shrink: 0;
    gap: 0.5rem;
  }

  &__header-content {
    flex: 1;
    min-width: 0;
    overflow: hidden;
  }

  &__title {
    margin: 0;
    font-weight: var(--font-weight-semibold, 600);
    line-height: 1.3;
    color: inherit;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__subtitle {
    display: block;
    color: var(--color-text-muted, #6a7a9a);
    font-size: 0.8em;
    font-weight: var(--font-weight-normal, 400);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__header-actions {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  &__media {
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    background-color: var(--color-bg-secondary, #141a2b);
    > img,
    > video {
      width: 100%;
      height: auto;
      object-fit: cover;
      display: block;
    }
  }

  &__body {
    flex: 1;
    min-height: 0;
    overflow: auto;
    color: inherit;
    > :last-child {
      margin-bottom: 0;
    }
  }

  &__footer {
    border-top: 1px solid var(--color-border, #1a2538);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  // --- Badge ---
  &__badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    z-index: 2;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.2rem 0.6rem;
    border-radius: var(--radius-full, 9999px);
    font-size: 0.7rem;
    font-weight: var(--font-weight-medium, 500);
    background-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
    box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.3));
    pointer-events: none;
  }

  // --- Overlay ---
  &__overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.6);
    opacity: 0;
    transition: opacity var(--transition-base, 300ms) ease;
    pointer-events: none;
    border-radius: inherit;
    z-index: 3;
  }

  &:hover &__overlay {
    opacity: 1;
    pointer-events: auto;
  }

  &__overlay-content {
    text-align: center;
    color: var(--color-text-inverse, #ffffff);
    padding: 1rem;
  }

  // --- Support thème clair ---
  .light-mode & {
    &--default {
      background-color: var(--color-bg-card, #ffffff);
      color: var(--color-text-primary, #1a1a2e);
      border-color: var(--color-border, #d0d8e0);
      &.nexus-card--elevated {
        box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.05));
      }
    }
    &--neutral {
      background-color: var(--color-bg-secondary, #e9ecf2);
      color: var(--color-text-secondary, #3d4a5c);
      border-color: var(--color-border, #d0d8e0);
    }
    &--dark {
      background-color: var(--color-bg-primary, #f4f6fa);
      color: var(--color-text-primary, #1a1a2e);
      border-color: var(--color-border, #d0d8e0);
    }
    &--light {
      background-color: var(--color-bg-card, #ffffff);
      color: var(--color-text-primary, #1a1a2e);
      border-color: var(--color-border, #d0d8e0);
    }
    // Outlined (ajustement des couleurs pour le contraste)
    &.nexus-card--outlined {
      &.nexus-card--dark {
        border-color: var(--color-text-primary, #1a1a2e);
        color: var(--color-text-primary, #1a1a2e);
      }
      &.nexus-card--light {
        border-color: var(--color-border, #d0d8e0);
        color: var(--color-text-primary, #1a1a2e);
      }
    }
  }
}
</style>
