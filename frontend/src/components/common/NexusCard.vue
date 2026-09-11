<!-- ==========================================================================
  NexusDL 2.0 - NexusCard Component
  Fichier : frontend/src/components/common/NexusCard.vue
  Description : Composant de carte ultra-complet (conteneur, layout, variantes,
                header, footer, media, badges, actions, hover effects, etc.)
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <component
    :is="tag"
    ref="cardRef"
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
        'nexus-card--horizontal': horizontal,
        'nexus-card--loading': loading,
        'nexus-card--selected': selected,
        'nexus-card--disabled': disabled,
      },
    ]"
    :style="customStyle"
    :role="clickable ? 'button' : undefined"
    :tabindex="clickable ? 0 : undefined"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- Loader overlay -->
    <Transition name="nexus-card-fade">
      <div v-if="loading" class="nexus-card__loading-overlay">
        <NexusSpinner size="md" variant="gradient" />
        <span v-if="loadingText" class="nexus-card__loading-text">
          {{ loadingText }}
        </span>
      </div>
    </Transition>

    <!-- ==================================================================
      HEADER
    =================================================================== -->
    <header v-if="hasHeader" class="nexus-card__header">
      <slot name="header">
        <div class="nexus-card__header-content">
          <h3 v-if="title" class="nexus-card__title">
            {{ title }}
            <span v-if="subtitle" class="nexus-card__subtitle">
              {{ subtitle }}
            </span>
          </h3>
          <div v-if="$slots['header-left']" class="nexus-card__header-left">
            <slot name="header-left" />
          </div>
        </div>
        <div v-if="$slots['header-actions']" class="nexus-card__header-actions">
          <slot name="header-actions" />
        </div>
      </slot>
    </header>

    <!-- ==================================================================
      MEDIA (image, vidéo, contenu en couverture)
    =================================================================== -->
    <div v-if="$slots.media || coverUrl" class="nexus-card__media">
      <slot name="media">
        <img
          v-if="coverUrl"
          :src="coverUrl"
          :alt="coverAlt || title || 'Media'"
          class="nexus-card__media-image"
          loading="lazy"
          @error="handleMediaError"
        />
      </slot>

      <!-- Badges superposés -->
      <div v-if="$slots.badge || badges.length" class="nexus-card__badges">
        <slot name="badge">
          <span
            v-for="(badge, idx) in badges"
            :key="idx"
            class="nexus-card__badge"
            :class="`nexus-card__badge--${badge.variant || 'primary'}`"
          >
            {{ badge.label }}
          </span>
        </slot>
      </div>
    </div>

    <!-- ==================================================================
      BODY (contenu principal)
    =================================================================== -->
    <div class="nexus-card__body">
      <slot>{{ content }}</slot>
    </div>

    <!-- ==================================================================
      FOOTER
    =================================================================== -->
    <footer v-if="hasFooter" class="nexus-card__footer">
      <slot name="footer">
        <div class="nexus-card__footer-content">
          <slot name="footer-content" />
        </div>
        <div v-if="$slots['footer-actions']" class="nexus-card__footer-actions">
          <slot name="footer-actions" />
        </div>
      </slot>
    </footer>

    <!-- ==================================================================
      OVERLAY (effet au survol)
    =================================================================== -->
    <Transition name="nexus-card-fade">
      <div v-if="overlay && isHovered" class="nexus-card__overlay">
        <slot name="overlay">
          <div class="nexus-card__overlay-content">
            <slot name="overlay-content" />
          </div>
        </slot>
      </div>
    </Transition>

    <!-- ==================================================================
      SELECTED INDICATOR
    =================================================================== -->
    <span v-if="selected" class="nexus-card__selected-indicator" aria-hidden="true">
      ✓
    </span>
  </component>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, useSlots } from 'vue'
import NexusSpinner from './NexusSpinner.vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Tag HTML à utiliser */
  tag: {
    type: String,
    default: 'article',
    validator: (val) => ['article', 'div', 'section', 'li', 'a'].includes(val),
  },
  /** Titre de la carte */
  title: {
    type: String,
    default: '',
  },
  /** Sous-titre de la carte */
  subtitle: {
    type: String,
    default: '',
  },
  /** Contenu texte */
  content: {
    type: String,
    default: '',
  },
  /** Variante de style */
  variant: {
    type: String,
    default: 'default',
    validator: (val) =>
      [
        'default',
        'primary',
        'secondary',
        'success',
        'warning',
        'error',
        'info',
        'neutral',
        'dark',
        'light',
      ].includes(val),
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
    default: true,
  },
  /** Effet hover (surélévation) */
  hoverable: {
    type: Boolean,
    default: false,
  },
  /** Carte cliquable (émet @click) */
  clickable: {
    type: Boolean,
    default: false,
  },
  /** Style plat (sans ombre) */
  flat: {
    type: Boolean,
    default: false,
  },
  /** Style contour */
  outlined: {
    type: Boolean,
    default: false,
  },
  /** Style avec ombre */
  elevated: {
    type: Boolean,
    default: false,
  },
  /** Supprime le padding intérieur */
  noPadding: {
    type: Boolean,
    default: false,
  },
  /** Hauteur 100% */
  fullHeight: {
    type: Boolean,
    default: false,
  },
  /** Disposition horizontale */
  horizontal: {
    type: Boolean,
    default: false,
  },
  /** Overlay au survol */
  overlay: {
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
  /** État sélectionné */
  selected: {
    type: Boolean,
    default: false,
  },
  /** État désactivé */
  disabled: {
    type: Boolean,
    default: false,
  },
  /** URL de couverture */
  coverUrl: {
    type: String,
    default: '',
  },
  /** Alt de la couverture */
  coverAlt: {
    type: String,
    default: '',
  },
  /** Badges superposés */
  badges: {
    type: Array,
    default: () => [],
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
  'mouseenter',
  'mouseleave',
  'media-error',
])

// ==========================================================================
//  Slots
// ==========================================================================

const slots = useSlots()

const hasHeader = computed(
  () =>
    !!slots.header ||
    !!slots['header-left'] ||
    !!slots['header-actions'] ||
    !!(props.title || props.subtitle)
)

const hasFooter = computed(
  () =>
    !!slots.footer ||
    !!slots['footer-content'] ||
    !!slots['footer-actions']
)

// ==========================================================================
//  État local
// ==========================================================================

const cardRef = ref(null)
const isHovered = ref(false)

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
//  Méthodes
// ==========================================================================

function handleClick(event) {
  if (props.disabled) {
    event.preventDefault()
    event.stopPropagation()
    return
  }
  if (props.clickable || props.tag === 'a') {
    emit('click', event)
  }
}

function handleMouseEnter(event) {
  isHovered.value = true
  emit('mouseenter', event)
}

function handleMouseLeave(event) {
  isHovered.value = false
  emit('mouseleave', event)
}

function handleMediaError(event) {
  emit('media-error', event)
}

// ==========================================================================
//  Exposition
// ==========================================================================

defineExpose({
  focus: () => cardRef.value?.focus(),
  blur: () => cardRef.value?.blur(),
  $el: cardRef,
  isHovered,
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$card-radius-sm: var(--radius-sm, 4px);
$card-radius-md: var(--radius-md, 8px);
$card-radius-lg: var(--radius-lg, 12px);
$card-radius-xl: var(--radius-xl, 16px);
$card-transition: all var(--transition-base, 300ms) ease;

// ==========================================================================
//  Carte principale
// ==========================================================================

.nexus-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: var(--color-bg-card, #1a2538);
  color: var(--color-text-primary, #e8edf5);
  border-radius: $card-radius-lg;
  overflow: hidden;
  transition: $card-transition;
  min-height: 80px;
  isolation: isolate;

  // ========================================================================
  //  Tailles
  // ========================================================================

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
      font-size: 0.95rem;
    }

    .nexus-card__subtitle {
      font-size: 0.72rem;
    }
  }

  &--md {
    border-radius: $card-radius-md;

    .nexus-card__header {
      padding: 0.75rem 1rem;
    }

    .nexus-card__body {
      padding: 0.85rem 1rem;
    }

    .nexus-card__footer {
      padding: 0.65rem 1rem;
    }

    .nexus-card__title {
      font-size: 1.1rem;
    }

    .nexus-card__subtitle {
      font-size: 0.8rem;
    }
  }

  &--lg {
    border-radius: $card-radius-xl;

    .nexus-card__header {
      padding: 1rem 1.25rem;
    }

    .nexus-card__body {
      padding: 1.1rem 1.25rem;
    }

    .nexus-card__footer {
      padding: 0.85rem 1.25rem;
    }

    .nexus-card__title {
      font-size: 1.3rem;
    }

    .nexus-card__subtitle {
      font-size: 0.9rem;
    }
  }

  // ========================================================================
  //  Sans padding
  // ========================================================================

  &--no-padding {
    .nexus-card__header,
    .nexus-card__body,
    .nexus-card__footer {
      padding: 0;
    }
  }

  // ========================================================================
  //  Variantes
  // ========================================================================

  &--default {
    background-color: var(--color-bg-card, #1a2538);
    color: var(--color-text-primary, #e8edf5);
    border: 1px solid var(--color-border, #1a2538);

    &.nexus-card--elevated {
      box-shadow: var(--shadow-md, 0 4px 12px rgba(0, 0, 0, 0.4));
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

  &--secondary {
    background-color: var(--color-secondary, #0066ff);
    color: #ffffff;
    border-color: var(--color-secondary-dark, #0044cc);

    &.nexus-card--elevated {
      box-shadow: 0 4px 12px rgba(0, 102, 255, 0.3);
    }
  }

  &--success {
    background-color: var(--color-success, #4caf50);
    color: #ffffff;
    border-color: var(--color-success-dark, #388e3c);

    &.nexus-card--elevated {
      box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }
  }

  &--warning {
    background-color: var(--color-warning, #ff9800);
    color: #ffffff;
    border-color: var(--color-warning-dark, #f57c00);

    &.nexus-card--elevated {
      box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3);
    }
  }

  &--error {
    background-color: var(--color-error, #f44336);
    color: #ffffff;
    border-color: var(--color-error-dark, #c62828);

    &.nexus-card--elevated {
      box-shadow: 0 4px 12px rgba(244, 67, 54, 0.3);
    }
  }

  &--info {
    background-color: var(--color-info, #2196f3);
    color: #ffffff;
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
      box-shadow: var(--shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.3));
    }
  }

  &--dark {
    background-color: var(--color-bg-primary, #0a0e1a);
    color: var(--color-text-primary, #e8edf5);
    border-color: var(--color-border, #1a2538);

    &.nexus-card--elevated {
      box-shadow: var(--shadow-lg, 0 8px 24px rgba(0, 0, 0, 0.5));
    }
  }

  &--light {
    background-color: #ffffff;
    color: #1a1a2e;
    border-color: #d0d8e0;

    &.nexus-card--elevated {
      box-shadow: var(--shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
    }
  }

  // ========================================================================
  //  Outlined
  // ========================================================================

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

    &.nexus-card--secondary {
      border-color: var(--color-secondary, #0066ff);
      color: var(--color-secondary, #0066ff);
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
      border-color: #d0d8e0;
      color: #1a1a2e;
    }
  }

  // ========================================================================
  //  Flat
  // ========================================================================

  &--flat {
    box-shadow: none !important;
    border: none !important;
  }

  // ========================================================================
  //  Bordered
  // ========================================================================

  &--bordered {
    border: 1px solid var(--color-border, #1a2538);
  }

  // ========================================================================
  //  Hoverable
  // ========================================================================

  &--hoverable {
    &:hover {
      transform: translateY(-4px);
      box-shadow: var(--shadow-lg, 0 8px 24px rgba(0, 0, 0, 0.5));
      border-color: var(--color-primary, #00d4ff);
    }
  }

  // ========================================================================
  //  Clickable
  // ========================================================================

  &--clickable {
    cursor: pointer;

    &:focus-visible {
      outline: 2px solid var(--color-primary, #00d4ff);
      outline-offset: 2px;
    }

    &:hover {
      border-color: var(--color-primary, #00d4ff);
    }

    &:active {
      transform: scale(0.99);
    }
  }

  // ========================================================================
  //  Full height
  // ========================================================================

  &--full-height {
    height: 100%;
  }

  // ========================================================================
  //  Horizontal
  // ========================================================================

  &--horizontal {
    flex-direction: row;

    .nexus-card__media {
      width: 40%;
      max-width: 300px;
      flex-shrink: 0;
    }

    .nexus-card__body {
      flex: 1;
      min-width: 0;
    }

    @media (max-width: 640px) {
      flex-direction: column;

      .nexus-card__media {
        width: 100%;
        max-width: none;
      }
    }
  }

  // ========================================================================
  //  Loading
  // ========================================================================

  &--loading {
    pointer-events: none;

    > *:not(.nexus-card__loading-overlay) {
      opacity: 0.5;
    }
  }

  // ========================================================================
  //  Selected
  // ========================================================================

  &--selected {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
  }

  // ========================================================================
  //  Disabled
  // ========================================================================

  &--disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }

  // ========================================================================
  //  Éléments internes
  // ========================================================================

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    border-bottom: 1px solid var(--color-border, #1a2538);
    flex-shrink: 0;
    flex-wrap: wrap;
  }

  &__header-content {
    flex: 1;
    min-width: 0;
    overflow: hidden;
  }

  &__header-left {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  &__title {
    margin: 0;
    font-weight: var(--font-weight-semibold, 600);
    line-height: 1.3;
    color: inherit;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: flex;
    align-items: baseline;
    gap: 0.4rem;
  }

  &__subtitle {
    display: inline;
    font-size: 0.8em;
    font-weight: var(--font-weight-normal, 400);
    color: var(--color-text-muted, #6a7a9a);
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
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    background-color: var(--color-bg-secondary, #141a2b);
    flex-shrink: 0;

    > img,
    > video {
      width: 100%;
      height: auto;
      object-fit: cover;
      display: block;
      transition: transform 0.4s ease;
    }

    .nexus-card--hoverable:hover & > img {
      transform: scale(1.05);
    }
  }

  &__media-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  &__badges {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    left: 0.5rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    pointer-events: none;
    z-index: 2;
  }

  &__badge {
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
    padding: 0.15rem 0.5rem;
    font-size: 0.65rem;
    font-weight: var(--font-weight-semibold, 600);
    border-radius: var(--radius-full, 9999px);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    white-space: nowrap;

    &--primary {
      background-color: rgba(0, 212, 255, 0.9);
      color: var(--color-text-inverse, #0a0e1a);
    }

    &--secondary {
      background-color: rgba(0, 102, 255, 0.9);
      color: #ffffff;
    }

    &--success {
      background-color: rgba(76, 175, 80, 0.9);
      color: #ffffff;
    }

    &--warning {
      background-color: rgba(255, 152, 0, 0.9);
      color: #ffffff;
    }

    &--error {
      background-color: rgba(244, 67, 54, 0.9);
      color: #ffffff;
    }

    &--info {
      background-color: rgba(33, 150, 243, 0.9);
      color: #ffffff;
    }

    &--neutral {
      background-color: rgba(20, 26, 43, 0.9);
      color: var(--color-text-secondary, #b0c0d8);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
  }

  &__body {
    flex: 1;
    min-height: 0;
    overflow: auto;
    color: inherit;
    line-height: 1.5;

    > :last-child {
      margin-bottom: 0;
    }

    > :first-child {
      margin-top: 0;
    }

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }

    &::-webkit-scrollbar-thumb {
      background: var(--color-border, #1a2538);
      border-radius: 3px;

      &:hover {
        background: var(--color-text-muted, #6a7a9a);
      }
    }
  }

  &__footer {
    border-top: 1px solid var(--color-border, #1a2538);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  &__footer-content {
    flex: 1;
    min-width: 0;
  }

  &__footer-actions {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    flex-shrink: 0;
  }

  // ========================================================================
  //  Overlay
  // ========================================================================

  &__overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(2px);
    -webkit-backdrop-filter: blur(2px);
    border-radius: inherit;
    z-index: 10;
    pointer-events: none;
  }

  &__overlay-content {
    text-align: center;
    color: #ffffff;
    padding: 1rem;
    pointer-events: auto;
  }

  // ========================================================================
  //  Loading overlay
  // ========================================================================

  &__loading-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    background: rgba(10, 14, 26, 0.85);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    border-radius: inherit;
    z-index: 20;
  }

  &__loading-text {
    font-size: 0.8rem;
    color: var(--color-text-secondary, #b0c0d8);
    font-weight: var(--font-weight-medium, 500);
  }

  // ========================================================================
  //  Selected indicator
  // ========================================================================

  &__selected-indicator {
    position: absolute;
    top: 0.5rem;
    left: 0.5rem;
    z-index: 15;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    background: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
    border-radius: var(--radius-full, 9999px);
    font-size: 0.75rem;
    font-weight: var(--font-weight-bold, 700);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    animation: nexusCardPopIn 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
}

// ==========================================================================
//  Animations
// ==========================================================================

@keyframes nexusCardPopIn {
  from {
    opacity: 0;
    transform: scale(0.5);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.nexus-card-fade-enter-active,
.nexus-card-fade-leave-active {
  transition: opacity var(--transition-fast, 150ms) ease;
}

.nexus-card-fade-enter-from,
.nexus-card-fade-leave-to {
  opacity: 0;
}

// ==========================================================================
//  Support du thème clair
// ==========================================================================

.light-mode {
  .nexus-card {
    &--default {
      background-color: #ffffff;
      color: #1a1a2e;
      border-color: #d0d8e0;

      &.nexus-card--elevated {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      }
    }

    &--neutral {
      background-color: #e9ecf2;
      color: #3d4a5c;
      border-color: #d0d8e0;
    }

    &--dark {
      background-color: #0a0e1a;
      color: #e8edf5;
      border-color: #1a2538;
    }

    &--light {
      background-color: #ffffff;
      color: #1a1a2e;
      border-color: #d0d8e0;
    }

    &.nexus-card--outlined {
      &.nexus-card--dark {
        border-color: #0a0e1a;
        color: #0a0e1a;
      }
      &.nexus-card--light {
        border-color: #d0d8e0;
        color: #1a1a2e;
      }
    }

    &__header,
    &__footer {
      border-color: #d0d8e0;
    }

    &__media {
      background-color: #e9ecf2;
    }

    &__subtitle {
      color: #7a8a9a;
    }

    &__loading-overlay {
      background: rgba(244, 246, 250, 0.85);
    }

    &__loading-text {
      color: #3d4a5c;
    }

    &__badge--neutral {
      background-color: rgba(233, 236, 242, 0.95);
      color: #3d4a5c;
      border-color: rgba(0, 0, 0, 0.1);
    }
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .nexus-card {
    transition: none !important;

    &--hoverable:hover {
      transform: none !important;
    }

    &--clickable:active {
      transform: none !important;
    }

    &__media > img {
      transition: none !important;
    }

    &__selected-indicator {
      animation: none !important;
    }
  }

  .nexus-card-fade-enter-active,
  .nexus-card-fade-leave-active {
    transition: none !important;
  }
}
</style>
