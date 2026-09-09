<!-- ==========================================================================
  NexusDL 2.0 - NexusBadge Component
  Fichier : frontend/src/components/common/NexusBadge.vue
  Description : Composant de badge (étiquette, statut, tag, compteur)
  Version : 2.0.0
========================================================================== -->

<template>
  <span
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
      }
    ]"
    :style="customStyle"
    @click="handleClick"
  >
    <!-- Icône (si fournie) -->
    <span v-if="icon" class="nexus-badge__icon">
      <component :is="icon" v-if="typeof icon === 'object'" />
      <span v-else>{{ icon }}</span>
    </span>

    <!-- Contenu du badge -->
    <span class="nexus-badge__content">
      <slot>{{ text || label }}</slot>
    </span>

    <!-- Bouton de fermeture -->
    <button
      v-if="closable"
      type="button"
      class="nexus-badge__close"
      @click.stop="handleClose"
      aria-label="Fermer"
    >
      <span aria-hidden="true">&times;</span>
    </button>
  </span>
</template>

<script setup>
import { computed, useSlots } from 'vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Variante du badge */
  variant: {
    type: String,
    default: 'neutral',
    validator: (val) => ['primary', 'success', 'warning', 'error', 'info', 'neutral'].includes(val),
  },
  /** Taille du badge */
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['sm', 'md', 'lg'].includes(val),
  },
  /** Texte du badge (utilisé si slot vide) */
  label: {
    type: String,
    default: '',
  },
  /** Texte alternatif (alias de label) */
  text: {
    type: String,
    default: '',
  },
  /** Icône (emoji, chaîne, ou composant) */
  icon: {
    type: [String, Object],
    default: null,
  },
  /** Style arrondi complet (pill) */
  pill: {
    type: Boolean,
    default: false,
  },
  /** Style contour (transparent avec bordure) */
  outline: {
    type: Boolean,
    default: false,
  },
  /** Coins arrondis (déjà par défaut) */
  rounded: {
    type: Boolean,
    default: true,
  },
  /** Affiche un bouton de fermeture */
  closable: {
    type: Boolean,
    default: false,
  },
  /** Rend le badge cliquable (change le curseur et émet un événement) */
  clickable: {
    type: Boolean,
    default: false,
  },
  /** Couleur personnalisée (surcharge la variante) au format CSS */
  customColor: {
    type: String,
    default: '',
  },
  /** Arrière-plan personnalisé */
  customBackground: {
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
  return style
})

// ==========================================================================
//  Gestionnaires d'événements
// ==========================================================================

function handleClick(event) {
  if (props.clickable) {
    emit('click', event)
  }
}

function handleClose(event) {
  emit('close', event)
}
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Styles du composant
// ==========================================================================

.nexus-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: var(--font-weight-medium, 500);
  line-height: 1.4;
  white-space: nowrap;
  transition: all var(--transition-fast, 150ms) ease;
  user-select: none;

  // Tailles
  &--sm {
    padding: 0.1rem 0.45rem;
    font-size: 0.65rem;
    border-radius: var(--radius-sm, 4px);
    &.nexus-badge--pill {
      border-radius: var(--radius-full, 9999px);
    }
    .nexus-badge__icon {
      font-size: 0.7rem;
    }
  }

  &--md {
    padding: 0.2rem 0.7rem;
    font-size: 0.75rem;
    border-radius: var(--radius-md, 8px);
    &.nexus-badge--pill {
      border-radius: var(--radius-full, 9999px);
    }
    .nexus-badge__icon {
      font-size: 0.8rem;
    }
  }

  &--lg {
    padding: 0.3rem 0.9rem;
    font-size: 0.9rem;
    border-radius: var(--radius-lg, 12px);
    &.nexus-badge--pill {
      border-radius: var(--radius-full, 9999px);
    }
    .nexus-badge__icon {
      font-size: 1rem;
    }
  }

  // Variantes (remplissage)
  &--primary {
    background-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-primary, #00d4ff);
      border: 1px solid var(--color-primary, #00d4ff);
    }
  }
  &--success {
    background-color: var(--color-success, #4caf50);
    color: var(--color-text-inverse, #0a0e1a);
    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-success, #4caf50);
      border: 1px solid var(--color-success, #4caf50);
    }
  }
  &--warning {
    background-color: var(--color-warning, #ff9800);
    color: var(--color-text-inverse, #0a0e1a);
    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-warning, #ff9800);
      border: 1px solid var(--color-warning, #ff9800);
    }
  }
  &--error {
    background-color: var(--color-error, #f44336);
    color: var(--color-text-inverse, #0a0e1a);
    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-error, #f44336);
      border: 1px solid var(--color-error, #f44336);
    }
  }
  &--info {
    background-color: var(--color-info, #2196f3);
    color: var(--color-text-inverse, #0a0e1a);
    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-info, #2196f3);
      border: 1px solid var(--color-info, #2196f3);
    }
  }
  &--neutral {
    background-color: var(--color-bg-secondary, #141a2b);
    color: var(--color-text-secondary, #b0c0d8);
    border: 1px solid var(--color-border, #1a2538);
    &.nexus-badge--outline {
      background: transparent;
      color: var(--color-text-secondary, #b0c0d8);
      border: 1px solid var(--color-border, #1a2538);
    }
  }

  // Arrondi (par défaut)
  &--rounded {
    border-radius: var(--radius-md, 8px);
  }

  // Cliquable
  &--clickable {
    cursor: pointer;
    &:hover {
      transform: translateY(-1px);
      box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.3));
      opacity: 0.85;
    }
    &:active {
      transform: translateY(0);
    }
  }

  // Closable
  &--closable {
    padding-right: 0.2rem;
  }

  // Contenu
  &__content {
    flex: 1;
    min-width: 0;
  }

  // Icône
  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  // Bouton de fermeture
  &__close {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    color: inherit;
    opacity: 0.6;
    padding: 0 0.15rem;
    font-size: 1.1em;
    line-height: 1;
    cursor: pointer;
    border-radius: var(--radius-full, 9999px);
    transition: opacity var(--transition-fast, 150ms) ease, background var(--transition-fast, 150ms) ease;
    &:hover {
      opacity: 1;
      background: rgba(0,0,0,0.1);
    }
    &:focus-visible {
      outline: 2px solid var(--color-primary, #00d4ff);
      outline-offset: 2px;
    }
  }
}

// ==========================================================================
//  Support du thème sombre/clair (déjà géré via variables CSS)
// ==========================================================================

.dark-mode .nexus-badge--neutral {
  background-color: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border-color: var(--color-border, #1a2538);
}

.light-mode .nexus-badge--neutral {
  background-color: var(--color-bg-card, #ffffff);
  color: var(--color-text-secondary, #3d4a5c);
  border-color: var(--color-border, #d0d8e0);
}
</style>
