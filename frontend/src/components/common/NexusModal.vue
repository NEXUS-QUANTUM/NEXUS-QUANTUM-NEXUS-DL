<!-- ==========================================================================
  NexusDL 2.0 - NexusModal Component
  Fichier : frontend/src/components/common/NexusModal.vue
  Description : Composant de modale ultra-complet (taille, position, animations, confirmation, etc.)
  Version : 2.0.0
========================================================================== -->

<template>
  <Teleport to="body">
    <Transition
      :name="transitionName"
      @before-enter="beforeEnter"
      @enter="enter"
      @after-enter="afterEnter"
      @before-leave="beforeLeave"
      @leave="leave"
      @after-leave="afterLeave"
    >
      <div
        v-if="modelValue"
        class="nexus-modal-overlay"
        :class="{
          'nexus-modal-overlay--dark': overlayDark,
          'nexus-modal-overlay--blur': overlayBlur,
          'nexus-modal-overlay--clickable': closeOnOverlayClick,
        }"
        @click="handleOverlayClick"
        @mousedown="handleOverlayMouseDown"
        @mouseup="handleOverlayMouseUp"
      >
        <div
          ref="modalRef"
          class="nexus-modal"
          :class="[
            `nexus-modal--${size}`,
            `nexus-modal--${position}`,
            {
              'nexus-modal--no-padding': noPadding,
              'nexus-modal--fullscreen': fullscreen,
              'nexus-modal--rounded': rounded,
            }
          ]"
          :style="customStyle"
          @click.stop
        >
          <!-- Header -->
          <header v-if="$slots.header || title || showClose" class="nexus-modal__header">
            <slot name="header">
              <h2 v-if="title" class="nexus-modal__title">
                {{ title }}
              </h2>
              <span v-if="subtitle" class="nexus-modal__subtitle">
                {{ subtitle }}
              </span>
            </slot>

            <button
              v-if="showClose"
              type="button"
              class="nexus-modal__close"
              @click="close"
              aria-label="Fermer"
              :disabled="loading"
            >
              <span aria-hidden="true">&times;</span>
            </button>
          </header>

          <!-- Body -->
          <section class="nexus-modal__body">
            <slot>
              <p v-if="content">{{ content }}</p>
            </slot>
          </section>

          <!-- Footer -->
          <footer v-if="$slots.footer || showFooter" class="nexus-modal__footer">
            <slot name="footer">
              <!-- Actions par défaut (si confirmation) -->
              <template v-if="confirmable">
                <NexusButton
                  v-if="showCancel"
                  variant="neutral"
                  :size="buttonSize"
                  :disabled="loading"
                  @click="cancel"
                >
                  {{ cancelText }}
                </NexusButton>
                <NexusButton
                  :variant="confirmVariant"
                  :size="buttonSize"
                  :loading="loading"
                  :disabled="loading"
                  @click="confirm"
                >
                  {{ confirmText }}
                </NexusButton>
              </template>
            </slot>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import NexusButton from './NexusButton.vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Contrôle l'ouverture/fermeture de la modale (v-model) */
  modelValue: {
    type: Boolean,
    default: false,
  },
  /** Titre de la modale (slot header) */
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
  /** Affiche le bouton de fermeture (croix) */
  showClose: {
    type: Boolean,
    default: true,
  },
  /** Taille de la modale */
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['xs', 'sm', 'md', 'lg', 'xl', 'full'].includes(val),
  },
  /** Position de la modale (verticale) */
  position: {
    type: String,
    default: 'center',
    validator: (val) => ['center', 'top', 'bottom'].includes(val),
  },
  /** Supprime le padding intérieur */
  noPadding: {
    type: Boolean,
    default: false,
  },
  /** Mode plein écran */
  fullscreen: {
    type: Boolean,
    default: false,
  },
  /** Coins arrondis */
  rounded: {
    type: Boolean,
    default: true,
  },
  /** Overlay plus sombre */
  overlayDark: {
    type: Boolean,
    default: true,
  },
  /** Flou de l'overlay */
  overlayBlur: {
    type: Boolean,
    default: true,
  },
  /** Fermeture au clic sur l'overlay */
  closeOnOverlayClick: {
    type: Boolean,
    default: true,
  },
  /** Fermeture avec la touche Echap */
  closeOnEscape: {
    type: Boolean,
    default: true,
  },
  /** Nom de la transition */
  transitionName: {
    type: String,
    default: 'nexus-modal',
  },
  /** Désactive le focus trap */
  disableFocusTrap: {
    type: Boolean,
    default: false,
  },
  /** Mode confirmation (affiche les boutons Ok/Annuler) */
  confirmable: {
    type: Boolean,
    default: false,
  },
  /** Texte du bouton de confirmation */
  confirmText: {
    type: String,
    default: 'Confirmer',
  },
  /** Texte du bouton d'annulation */
  cancelText: {
    type: String,
    default: 'Annuler',
  },
  /** Variante du bouton de confirmation */
  confirmVariant: {
    type: String,
    default: 'primary',
    validator: (val) =>
      ['primary', 'secondary', 'success', 'warning', 'error', 'info', 'neutral'].includes(val),
  },
  /** Taille des boutons */
  buttonSize: {
    type: String,
    default: 'md',
    validator: (val) => ['xs', 'sm', 'md', 'lg'].includes(val),
  },
  /** Affiche le bouton d'annulation */
  showCancel: {
    type: Boolean,
    default: true,
  },
  /** Affiche le footer (même si slot vide) */
  showFooter: {
    type: Boolean,
    default: true,
  },
  /** Désactive les boutons (loading) */
  loading: {
    type: Boolean,
    default: false,
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
})

// ==========================================================================
//  Émits
// ==========================================================================

const emit = defineEmits([
  'update:modelValue',
  'open',
  'close',
  'confirm',
  'cancel',
  'before-enter',
  'enter',
  'after-enter',
  'before-leave',
  'leave',
  'after-leave',
])

// ==========================================================================
//  Références et état
// ==========================================================================

const modalRef = ref(null)
const focusableElements = ref([])
const previousActiveElement = ref(null)
const isOpen = ref(false)

// ==========================================================================
//  Styles calculés
// ==========================================================================

const customStyle = computed(() => {
  const style = {}
  if (props.customColor) {
    style.setProperty('--nexus-modal-color', props.customColor)
  }
  if (props.customBackground) {
    style.setProperty('--nexus-modal-bg', props.customBackground)
  }
  return style
})

// ==========================================================================
//  Gestion de l'ouverture/fermeture
// ==========================================================================

function open() {
  isOpen.value = true
  emit('open')
  // Sauvegarder l'élément actif pour le restaurer
  previousActiveElement.value = document.activeElement
  // Focus trap
  if (!props.disableFocusTrap) {
    nextTick(() => {
      trapFocus()
    })
  }
  // Empêcher le scroll du body
  document.body.style.overflow = 'hidden'
}

function close() {
  if (props.loading) return
  isOpen.value = false
  emit('close')
  emit('update:modelValue', false)
  // Restaurer le scroll
  document.body.style.overflow = ''
  // Restaurer le focus
  if (previousActiveElement.value && typeof previousActiveElement.value.focus === 'function') {
    previousActiveElement.value.focus()
  }
}

function confirm() {
  if (props.loading) return
  emit('confirm')
  if (!props.confirmable) {
    close()
  }
}

function cancel() {
  if (props.loading) return
  emit('cancel')
  close()
}

function handleOverlayClick(event) {
  if (props.closeOnOverlayClick && event.target === event.currentTarget) {
    close()
  }
}

function handleOverlayMouseDown() {
  // no-op : conservé pour compatibilité avec le template
}

function handleOverlayMouseUp() {
  // no-op : conservé pour compatibilité avec le template
}

// ==========================================================================
//  Focus trap
// ==========================================================================

function trapFocus() {
  if (!modalRef.value) return
  // Récupérer tous les éléments focusables
  const selectors = [
    'a[href]:not([disabled])',
    'button:not([disabled])',
    'input:not([disabled])',
    'textarea:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"]):not([disabled])',
  ]
  focusableElements.value = Array.from(
    modalRef.value.querySelectorAll(selectors.join(', '))
  )
  if (focusableElements.value.length > 0) {
    focusableElements.value[0].focus()
  }
}

function handleKeydown(event) {
  if (props.closeOnEscape && event.key === 'Escape') {
    close()
  }
  // Focus trap (Tab)
  if (!props.disableFocusTrap && event.key === 'Tab' && focusableElements.value.length > 0) {
    const first = focusableElements.value[0]
    const last = focusableElements.value[focusableElements.value.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }
}

// ==========================================================================
//  Events de transition
// ==========================================================================

function beforeEnter() {
  emit('before-enter')
}

function enter() {
  emit('enter')
}

function afterEnter() {
  emit('after-enter')
}

function beforeLeave() {
  emit('before-leave')
}

function leave() {
  emit('leave')
}

function afterLeave() {
  emit('after-leave')
}

// ==========================================================================
//  Watchers
// ==========================================================================

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      open()
    } else if (isOpen.value) {
      // Fermeture pilotée par le parent : ne pas ré-émettre update:modelValue
      isOpen.value = false
      document.body.style.overflow = ''
      if (previousActiveElement.value && typeof previousActiveElement.value.focus === 'function') {
        previousActiveElement.value.focus()
      }
    }
  },
  { immediate: true }
)

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})

// ==========================================================================
//  Exposer les méthodes
// ==========================================================================

defineExpose({
  open,
  close,
  confirm,
  cancel,
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$modal-transition: all var(--transition-base, 300ms) ease;
$modal-radius-sm: var(--radius-sm, 4px);
$modal-radius-md: var(--radius-md, 8px);
$modal-radius-lg: var(--radius-lg, 12px);
$modal-radius-xl: var(--radius-xl, 16px);

// ==========================================================================
//  Overlay
// ==========================================================================

.nexus-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  padding: 1rem;
  transition: $modal-transition;

  &--dark {
    background: rgba(0, 0, 0, 0.7);
  }

  &--blur {
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
  }

  &--clickable {
    cursor: pointer;
  }
}

// ==========================================================================
//  Modale
// ==========================================================================

.nexus-modal {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  box-shadow: var(--shadow-xl, 0 16px 48px rgba(0, 0, 0, 0.6));
  max-height: 90vh;
  max-width: 90vw;
  width: 100%;
  transition: $modal-transition;
  cursor: default;
  overflow: hidden;
  --nexus-modal-color: var(--color-primary, #00d4ff);
  --nexus-modal-bg: var(--color-bg-card, #1a2538);

  // Tailles
  &--xs {
    max-width: 320px;
    border-radius: $modal-radius-sm;
  }
  &--sm {
    max-width: 440px;
    border-radius: $modal-radius-md;
  }
  &--md {
    max-width: 560px;
    border-radius: $modal-radius-md;
  }
  &--lg {
    max-width: 720px;
    border-radius: $modal-radius-lg;
  }
  &--xl {
    max-width: 900px;
    border-radius: $modal-radius-xl;
  }
  &--full {
    max-width: 98vw;
    border-radius: $modal-radius-xl;
  }

  // Positions
  &--center {
    align-self: center;
  }
  &--top {
    align-self: flex-start;
    margin-top: 2rem;
  }
  &--bottom {
    align-self: flex-end;
    margin-bottom: 2rem;
  }

  // Fullscreen
  &--fullscreen {
    max-width: 100vw !important;
    max-height: 100vh !important;
    width: 100vw !important;
    height: 100vh !important;
    border-radius: 0 !important;
    margin: 0 !important;
  }

  // No padding
  &--no-padding {
    .nexus-modal__header,
    .nexus-modal__body,
    .nexus-modal__footer {
      padding: 0;
    }
  }

  // Rounded (coins)
  &--rounded {
    border-radius: var(--modal-radius, #{$modal-radius-md});
  }
}

// ==========================================================================
//  Header
// ==========================================================================

.nexus-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
  flex-shrink: 0;
  gap: 0.5rem;
}

.nexus-modal__title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #e8edf5);
  line-height: 1.3;
}

.nexus-modal__subtitle {
  display: block;
  font-size: 0.85rem;
  font-weight: var(--font-weight-normal, 400);
  color: var(--color-text-muted, #6a7a9a);
  margin-top: 0.1rem;
}

.nexus-modal__close {
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: var(--radius-sm, 4px);
  transition: all var(--transition-fast, 150ms) ease;
  flex-shrink: 0;
  margin-top: -0.2rem;

  &:hover {
    color: var(--color-text-primary, #e8edf5);
    background: var(--color-bg-hover, #253254);
  }
  &:focus-visible {
    outline: 2px solid var(--nexus-modal-color);
    outline-offset: 2px;
  }
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// ==========================================================================
//  Body
// ==========================================================================

.nexus-modal__body {
  flex: 1;
  padding: 1.25rem;
  overflow-y: auto;
  color: var(--color-text-primary, #e8edf5);
  min-height: 0;

  // Style custom scrollbar
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: var(--color-bg-secondary, #141a2b);
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
    border-radius: 3px;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: var(--color-text-muted, #6a7a9a);
  }
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) var(--color-bg-secondary);
}

// ==========================================================================
//  Footer
// ==========================================================================

.nexus-modal__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-top: 1px solid var(--color-border, #1a2538);
  flex-shrink: 0;
  flex-wrap: wrap;

  // Boutons par défaut pour le mode confirmable
  > .nexus-btn {
    min-width: 80px;
  }
}

// ==========================================================================
//  Transitions
// ==========================================================================

// --- Fade + Scale (par défaut) ---
.nexus-modal-enter-active,
.nexus-modal-leave-active {
  transition: all var(--transition-base, 300ms) ease;
}

.nexus-modal-enter-from,
.nexus-modal-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(10px);
}

.nexus-modal-enter-to,
.nexus-modal-leave-from {
  opacity: 1;
  transform: scale(1) translateY(0);
}

// --- Fade only ---
.nexus-modal-fade-enter-active,
.nexus-modal-fade-leave-active {
  transition: opacity var(--transition-base, 300ms) ease;
}
.nexus-modal-fade-enter-from,
.nexus-modal-fade-leave-to {
  opacity: 0;
}
.nexus-modal-fade-enter-to,
.nexus-modal-fade-leave-from {
  opacity: 1;
}

// --- Slide (bottom to top) ---
.nexus-modal-slide-enter-active,
.nexus-modal-slide-leave-active {
  transition: all var(--transition-base, 300ms) ease;
}
.nexus-modal-slide-enter-from {
  opacity: 0;
  transform: translateY(30px);
}
.nexus-modal-slide-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
.nexus-modal-slide-enter-to,
.nexus-modal-slide-leave-from {
  opacity: 1;
  transform: translateY(0);
}

// --- Zoom ---
.nexus-modal-zoom-enter-active,
.nexus-modal-zoom-leave-active {
  transition: all var(--transition-base, 300ms) ease;
}
.nexus-modal-zoom-enter-from {
  opacity: 0;
  transform: scale(0.8);
}
.nexus-modal-zoom-leave-to {
  opacity: 0;
  transform: scale(0.8);
}
.nexus-modal-zoom-enter-to,
.nexus-modal-zoom-leave-from {
  opacity: 1;
  transform: scale(1);
}

// ==========================================================================
//  Support du thème clair
// ==========================================================================

.light-mode .nexus-modal {
  background: var(--color-bg-card, #ffffff);
  border-color: var(--color-border, #d0d8e0);
  box-shadow: var(--shadow-xl, 0 16px 48px rgba(0, 0, 0, 0.16));

  .nexus-modal__header {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-modal__title {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-modal__subtitle {
    color: var(--color-text-muted, #7a8a9a);
  }
  .nexus-modal__body {
    color: var(--color-text-primary, #1a1a2e);
  }
  .nexus-modal__footer {
    border-color: var(--color-border, #d0d8e0);
  }
  .nexus-modal__close {
    &:hover {
      color: var(--color-text-primary, #1a1a2e);
      background: var(--color-bg-hover, #e3e8ef);
    }
  }
}

.light-mode .nexus-modal-overlay {
  background: rgba(0, 0, 0, 0.4);
}
</style>
