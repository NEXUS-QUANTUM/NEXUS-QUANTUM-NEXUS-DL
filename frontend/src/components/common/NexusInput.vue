<!-- ==========================================================================
  NexusDL 2.0 - NexusInput Component
  Fichier : frontend/src/components/common/NexusInput.vue
  Description : Composant de champ de saisie ultra-complet (texte, email, password, number, textarea, select, etc.)
  Version : 2.0.0
========================================================================== -->

<template>
  <div
    class="nexus-input-wrapper"
    :class="[
      `nexus-input-wrapper--${size}`,
      {
        'nexus-input-wrapper--disabled': disabled,
        'nexus-input-wrapper--error': error,
        'nexus-input-wrapper--success': success,
        'nexus-input-wrapper--loading': loading,
        'nexus-input-wrapper--focused': isFocused,
        'nexus-input-wrapper--filled': hasValue,
        'nexus-input-wrapper--with-icon': hasLeftIcon,
        'nexus-input-wrapper--with-right-icon': hasRightIcon,
        'nexus-input-wrapper--with-clear': clearable,
        'nexus-input-wrapper--with-counter': hasCounter,
        'nexus-input-wrapper--with-label': !!label,
        'nexus-input-wrapper--with-helper': hasHelper,
        'nexus-input-wrapper--block': block,
        'nexus-input-wrapper--rounded': rounded,
      }
    ]"
    :style="customStyle"
  >
    <!-- Label -->
    <label
      v-if="label"
      :for="id"
      class="nexus-input__label"
      :class="{ 'nexus-input__label--required': required }"
    >
      {{ label }}
      <span v-if="required" class="nexus-input__label-required" aria-hidden="true">*</span>
    </label>

    <!-- Champ de saisie -->
    <div class="nexus-input__field-wrapper">
      <!-- Icône gauche -->
      <span v-if="leftIcon" class="nexus-input__icon nexus-input__icon--left" aria-hidden="true">
        <component :is="leftIcon" v-if="typeof leftIcon === 'object'" />
        <span v-else>{{ leftIcon }}</span>
      </span>

      <!-- Input / Textarea / Select -->
      <component
        :is="tag"
        :id="id"
        ref="inputRef"
        class="nexus-input__field"
        :type="tag === 'input' ? type : undefined"
        :name="name"
        :placeholder="placeholder"
        :value="modelValue"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :autocomplete="autocomplete"
        :autofocus="autofocus"
        :min="min"
        :max="max"
        :step="step"
        :minlength="minlength"
        :maxlength="maxlength"
        :rows="rows"
        :cols="cols"
        :wrap="wrap"
        :spellcheck="spellcheck"
        :aria-label="ariaLabel || label"
        :aria-describedby="helperId"
        :aria-invalid="!!error"
        :aria-required="required"
        :aria-disabled="disabled"
        @input="onInput"
        @blur="onBlur"
        @focus="onFocus"
        @change="onChange"
        @keydown="onKeydown"
        @keyup="onKeyup"
        @keypress="onKeypress"
        @compositionstart="onCompositionStart"
        @compositionend="onCompositionEnd"
        v-bind="$attrs"
      />

      <!-- Indicateur de chargement -->
      <span v-if="loading" class="nexus-input__spinner" aria-hidden="true">
        <svg
          class="nexus-input__spinner-icon"
          viewBox="0 0 50 50"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            class="nexus-input__spinner-path"
            cx="25"
            cy="25"
            r="20"
            fill="none"
            stroke-width="4"
          />
        </svg>
      </span>

      <!-- Bouton de validation (succès/erreur) -->
      <span v-if="success" class="nexus-input__status nexus-input__status--success" aria-hidden="true">
        <span>✓</span>
      </span>
      <span v-if="error" class="nexus-input__status nexus-input__status--error" aria-hidden="true">
        <span>✕</span>
      </span>

      <!-- Bouton d'effacement -->
      <button
        v-if="clearable && hasValue && !disabled"
        type="button"
        class="nexus-input__clear"
        @click="clear"
        @mousedown.prevent
        aria-label="Effacer le texte"
      >
        <span aria-hidden="true">&times;</span>
      </button>

      <!-- Compteur de caractères -->
      <span v-if="hasCounter" class="nexus-input__counter" aria-live="polite">
        {{ modelValue ? modelValue.length : 0 }}{{ maxlength ? ` / ${maxlength}` : '' }}
      </span>

      <!-- Icône droite -->
      <span v-if="rightIcon" class="nexus-input__icon nexus-input__icon--right" aria-hidden="true">
        <component :is="rightIcon" v-if="typeof rightIcon === 'object'" />
        <span v-else>{{ rightIcon }}</span>
      </span>
    </div>

    <!-- Message d'erreur / Helper -->
    <div v-if="hasHelper" class="nexus-input__helper">
      <span v-if="error" class="nexus-input__error-message" role="alert">
        {{ error }}
      </span>
      <span v-else-if="helper" class="nexus-input__helper-text">
        {{ helper }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, useSlots, onMounted, watch } from 'vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Identifiant du champ (pour le label) */
  id: {
    type: String,
    default: () => `nexus-input-${Math.random().toString(36).slice(2, 7)}`,
  },
  /** Nom du champ (pour le formulaire) */
  name: {
    type: String,
    default: '',
  },
  /** Type d'input (pour tag="input") */
  type: {
    type: String,
    default: 'text',
    validator: (val) =>
      ['text', 'email', 'password', 'number', 'tel', 'url', 'search', 'date', 'time', 'datetime-local', 'month', 'week', 'color', 'file'].includes(
        val
      ),
  },
  /** Tag HTML à utiliser (input, textarea, select) */
  tag: {
    type: String,
    default: 'input',
    validator: (val) => ['input', 'textarea', 'select'].includes(val),
  },
  /** Label du champ */
  label: {
    type: String,
    default: '',
  },
  /** Placeholder */
  placeholder: {
    type: String,
    default: '',
  },
  /** Valeur liée (v-model) */
  modelValue: {
    type: [String, Number],
    default: '',
  },
  /** Désactivé */
  disabled: {
    type: Boolean,
    default: false,
  },
  /** Lecture seule */
  readonly: {
    type: Boolean,
    default: false,
  },
  /** Requis (affiche une étoile) */
  required: {
    type: Boolean,
    default: false,
  },
  /** Message d'erreur (met le champ en état d'erreur) */
  error: {
    type: String,
    default: '',
  },
  /** Message d'aide (information complémentaire) */
  helper: {
    type: String,
    default: '',
  },
  /** État de succès */
  success: {
    type: Boolean,
    default: false,
  },
  /** État de chargement */
  loading: {
    type: Boolean,
    default: false,
  },
  /** Icône à gauche (emoji, chaîne, composant) */
  leftIcon: {
    type: [String, Object],
    default: null,
  },
  /** Icône à droite (emoji, chaîne, composant) */
  rightIcon: {
    type: [String, Object],
    default: null,
  },
  /** Affiche un bouton pour effacer le contenu */
  clearable: {
    type: Boolean,
    default: false,
  },
  /** Largeur pleine (block) */
  block: {
    type: Boolean,
    default: true,
  },
  /** Coins arrondis */
  rounded: {
    type: Boolean,
    default: false,
  },
  /** Taille du champ */
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['sm', 'md', 'lg'].includes(val),
  },
  /** Autocomplete (ex: off, on, username, email, etc.) */
  autocomplete: {
    type: String,
    default: 'off',
  },
  /** Focus automatique au montage */
  autofocus: {
    type: Boolean,
    default: false,
  },
  /** Spellcheck (pour les champs texte) */
  spellcheck: {
    type: Boolean,
    default: false,
  },
  /** Longueur minimale (pour string) */
  minlength: {
    type: Number,
    default: null,
  },
  /** Longueur maximale (pour string) */
  maxlength: {
    type: Number,
    default: null,
  },
  /** Valeur minimale (pour number, date) */
  min: {
    type: [String, Number],
    default: null,
  },
  /** Valeur maximale (pour number, date) */
  max: {
    type: [String, Number],
    default: null,
  },
  /** Pas (pour number) */
  step: {
    type: [String, Number],
    default: null,
  },
  /** Nombre de lignes (textarea) */
  rows: {
    type: Number,
    default: 3,
  },
  /** Nombre de colonnes (textarea) */
  cols: {
    type: Number,
    default: 30,
  },
  /** Wrap (textarea) */
  wrap: {
    type: String,
    default: 'soft',
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
  'update:modelValue',
  'focus',
  'blur',
  'input',
  'change',
  'clear',
  'keydown',
  'keyup',
  'keypress',
  'compositionstart',
  'compositionend',
])

// ==========================================================================
//  Slots
// ==========================================================================

const slots = useSlots()
const hasLeftIcon = computed(() => !!props.leftIcon || !!slots['left-icon'])
const hasRightIcon = computed(() => !!props.rightIcon || !!slots['right-icon'])
const hasHelper = computed(() => !!props.helper || !!props.error)
const hasCounter = computed(() => props.maxlength !== null && props.tag === 'input')
const hasValue = computed(() => props.modelValue !== '' && props.modelValue !== null && props.modelValue !== undefined)

// ==========================================================================
//  Références et état
// ==========================================================================

const inputRef = ref(null)
const isFocused = ref(false)
const isComposing = ref(false)

// ==========================================================================
//  ID helper
// ==========================================================================

const helperId = computed(() => (hasHelper.value ? `${props.id}-helper` : undefined))

// ==========================================================================
//  Styles calculés
// ==========================================================================

const customStyle = computed(() => {
  const style = {}
  if (props.customColor) {
    style.setProperty('--nexus-input-color', props.customColor)
  }
  if (props.customBackground) {
    style.setProperty('--nexus-input-bg', props.customBackground)
  }
  if (props.customBorder) {
    style.setProperty('--nexus-input-border', props.customBorder)
  }
  return style
})

// ==========================================================================
//  Gestionnaires d'événements
// ==========================================================================

function onInput(event) {
  if (isComposing.value) return
  const value = event.target.value
  emit('update:modelValue', value)
  emit('input', value, event)
}

function onBlur(event) {
  isFocused.value = false
  emit('blur', event)
}

function onFocus(event) {
  isFocused.value = true
  emit('focus', event)
}

function onChange(event) {
  emit('change', event.target.value, event)
}

function onKeydown(event) {
  emit('keydown', event)
}

function onKeyup(event) {
  emit('keyup', event)
}

function onKeypress(event) {
  emit('keypress', event)
}

function onCompositionStart(event) {
  isComposing.value = true
  emit('compositionstart', event)
}

function onCompositionEnd(event) {
  isComposing.value = false
  // Après la composition, il faut déclencher un input
  const value = event.target.value
  emit('update:modelValue', value)
  emit('input', value, event)
  emit('compositionend', event)
}

function clear() {
  if (props.disabled) return
  emit('update:modelValue', '')
  emit('clear')
  // Focus après effacement
  if (inputRef.value) {
    inputRef.value.focus()
  }
}

// ==========================================================================
//  Focus / Blur programmatiques
// ==========================================================================

function focus() {
  if (inputRef.value) {
    inputRef.value.focus()
  }
}

function blur() {
  if (inputRef.value) {
    inputRef.value.blur()
  }
}

// ==========================================================================
//  Auto-focus au montage
// ==========================================================================

onMounted(() => {
  if (props.autofocus && inputRef.value) {
    inputRef.value.focus()
  }
})

// ==========================================================================
//  Exposer les méthodes
// ==========================================================================

defineExpose({
  focus,
  blur,
  clear,
  inputRef,
  isFocused,
})

// ==========================================================================
//  Watchers
// ==========================================================================

watch(
  () => props.error,
  () => {
    // Si erreur, on peut annoncer aux lecteurs d'écran
    if (props.error) {
      // L'aria-invalid est déjà géré via aria-invalid
    }
  }
)
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$input-radius-sm: var(--radius-sm, 4px);
$input-radius-md: var(--radius-md, 8px);
$input-radius-lg: var(--radius-lg, 12px);
$input-transition: all var(--transition-fast, 150ms) ease;

// ==========================================================================
//  Wrapper principal
// ==========================================================================

.nexus-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  width: 100%;
  max-width: 100%;
  --nexus-input-color: var(--color-primary, #00d4ff);
  --nexus-input-bg: var(--color-bg-input, #1e2a40);
  --nexus-input-border: var(--color-border, #1a2538);

  &--block {
    width: 100%;
  }

  // ==========================================================================
  //  Tailles
  // ==========================================================================

  &--sm {
    .nexus-input__label {
      font-size: 0.75rem;
    }
    .nexus-input__field {
      font-size: 0.8rem;
      padding: 0.25rem 0.5rem;
      min-height: 28px;
      border-radius: $input-radius-sm;
    }
    .nexus-input__icon {
      font-size: 0.8rem;
    }
    .nexus-input__helper-text,
    .nexus-input__error-message {
      font-size: 0.7rem;
    }
    .nexus-input__counter {
      font-size: 0.65rem;
    }
    .nexus-input__clear,
    .nexus-input__status {
      font-size: 0.7rem;
    }
  }

  &--md {
    .nexus-input__label {
      font-size: 0.85rem;
    }
    .nexus-input__field {
      font-size: 0.95rem;
      padding: 0.4rem 0.7rem;
      min-height: 36px;
      border-radius: $input-radius-md;
    }
    .nexus-input__icon {
      font-size: 1rem;
    }
    .nexus-input__helper-text,
    .nexus-input__error-message {
      font-size: 0.75rem;
    }
    .nexus-input__counter {
      font-size: 0.7rem;
    }
    .nexus-input__clear,
    .nexus-input__status {
      font-size: 0.8rem;
    }
  }

  &--lg {
    .nexus-input__label {
      font-size: 1rem;
    }
    .nexus-input__field {
      font-size: 1.1rem;
      padding: 0.6rem 1rem;
      min-height: 44px;
      border-radius: $input-radius-lg;
    }
    .nexus-input__icon {
      font-size: 1.2rem;
    }
    .nexus-input__helper-text,
    .nexus-input__error-message {
      font-size: 0.85rem;
    }
    .nexus-input__counter {
      font-size: 0.8rem;
    }
    .nexus-input__clear,
    .nexus-input__status {
      font-size: 0.9rem;
    }
  }

  // Arrondi
  &.nexus-input-wrapper--rounded {
    .nexus-input__field {
      border-radius: var(--radius-full, 9999px);
    }
  }

  // ==========================================================================
  //  États
  // ==========================================================================

  &.nexus-input-wrapper--disabled {
    opacity: 0.6;
    cursor: not-allowed;
    .nexus-input__field {
      cursor: not-allowed;
      pointer-events: none;
    }
    .nexus-input__icon,
    .nexus-input__clear {
      pointer-events: none;
    }
  }

  &.nexus-input-wrapper--error {
    .nexus-input__field {
      border-color: var(--color-error, #f44336);
      &:focus {
        border-color: var(--color-error, #f44336);
        box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.15);
      }
    }
    .nexus-input__label {
      color: var(--color-error, #f44336);
    }
  }

  &.nexus-input-wrapper--success {
    .nexus-input__field {
      border-color: var(--color-success, #4caf50);
      &:focus {
        border-color: var(--color-success, #4caf50);
        box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.15);
      }
    }
  }

  &.nexus-input-wrapper--loading {
    .nexus-input__field {
      padding-right: 2.2rem;
    }
  }

  &.nexus-input-wrapper--focused {
    .nexus-input__field {
      border-color: var(--nexus-input-color);
      box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15);
    }
  }

  &.nexus-input-wrapper--with-icon {
    .nexus-input__field {
      padding-left: 2rem;
    }
    &.nexus-input-wrapper--sm .nexus-input__field {
      padding-left: 1.6rem;
    }
    &.nexus-input-wrapper--lg .nexus-input__field {
      padding-left: 2.4rem;
    }
  }

  &.nexus-input-wrapper--with-right-icon {
    .nexus-input__field {
      padding-right: 2rem;
    }
    &.nexus-input-wrapper--sm .nexus-input__field {
      padding-right: 1.6rem;
    }
    &.nexus-input-wrapper--lg .nexus-input__field {
      padding-right: 2.4rem;
    }
  }

  &.nexus-input-wrapper--with-clear {
    .nexus-input__field {
      padding-right: 2rem;
    }
    &.nexus-input-wrapper--sm .nexus-input__field {
      padding-right: 1.6rem;
    }
    &.nexus-input-wrapper--lg .nexus-input__field {
      padding-right: 2.4rem;
    }
  }

  &.nexus-input-wrapper--with-counter {
    .nexus-input__field {
      padding-right: 3.5rem;
    }
    &.nexus-input-wrapper--sm .nexus-input__field {
      padding-right: 2.8rem;
    }
    &.nexus-input-wrapper--lg .nexus-input__field {
      padding-right: 4.2rem;
    }
  }

  &.nexus-input-wrapper--with-right-icon.nexus-input-wrapper--with-clear {
    .nexus-input__field {
      padding-right: 4rem;
    }
    &.nexus-input-wrapper--sm .nexus-input__field {
      padding-right: 3.2rem;
    }
    &.nexus-input-wrapper--lg .nexus-input__field {
      padding-right: 4.8rem;
    }
  }
}

// ==========================================================================
//  Label
// ==========================================================================

.nexus-input__label {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-weight: var(--font-weight-medium, 500);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  user-select: none;

  &--required .nexus-input__label-required {
    color: var(--color-error, #f44336);
  }
}

// ==========================================================================
//  Champ wrapper
// ==========================================================================

.nexus-input__field-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

// ==========================================================================
//  Champ
// ==========================================================================

.nexus-input__field {
  width: 100%;
  background-color: var(--nexus-input-bg);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--nexus-input-border);
  transition: $input-transition;
  outline: none;
  font-family: inherit;
  line-height: 1.5;

  &:focus {
    border-color: var(--nexus-input-color);
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
    opacity: 1;
  }
}

// --- Textarea spécifique ---
// NOTE : `textarea&` était invalide en SCSS ("&" doit être en début de
// sélecteur composé). Sélecteur sorti du bloc imbriqué.
textarea.nexus-input__field {
  resize: vertical;
  min-height: 60px;
}

// --- Select spécifique ---
// NOTE : idem pour `select&`.
select.nexus-input__field {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%236a7a9a' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.8rem center;
  padding-right: 2.5rem;
}

// ==========================================================================
//  Icônes
// ==========================================================================

.nexus-input__icon {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
  line-height: 1;

  &--left {
    left: 0.6rem;
  }
  &--right {
    right: 0.6rem;
    pointer-events: auto;
  }
}

// ==========================================================================
//  Spinner de chargement
// ==========================================================================

.nexus-input__spinner {
  position: absolute;
  right: 0.6rem;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.2em;
  height: 1.2em;
  animation: nexus-input-spin 0.8s linear infinite;
}

.nexus-input__spinner-icon {
  width: 100%;
  height: 100%;
}

.nexus-input__spinner-path {
  stroke: var(--nexus-input-color);
  stroke-linecap: round;
  stroke-dasharray: 90, 150;
  stroke-dashoffset: 0;
  animation: nexus-input-spinner-dash 1.5s ease-in-out infinite;
}

// ==========================================================================
//  Statut (succès/erreur)
// ==========================================================================

.nexus-input__status {
  position: absolute;
  right: 0.6rem;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-weight-bold, 700);
  pointer-events: none;
  line-height: 1;

  &--success {
    color: var(--color-success, #4caf50);
  }
  &--error {
    color: var(--color-error, #f44336);
  }
}

// ==========================================================================
//  Bouton d'effacement
// ==========================================================================

.nexus-input__clear {
  position: absolute;
  right: 0.6rem;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1.2em;
  line-height: 1;
  cursor: pointer;
  padding: 0.1rem;
  border-radius: var(--radius-full, 9999px);
  transition: $input-transition;

  &:hover {
    color: var(--color-text-primary, #e8edf5);
    background: var(--color-bg-hover, #253254);
  }
  &:active {
    transform: translateY(-50%) scale(0.9);
  }
  &:focus-visible {
    outline: 2px solid var(--nexus-input-color);
    outline-offset: 2px;
  }
}

// ==========================================================================
//  Compteur
// ==========================================================================

.nexus-input__counter {
  position: absolute;
  right: 0.6rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.7rem;
  pointer-events: none;
  user-select: none;
}

// ==========================================================================
//  Helper / Erreur
// ==========================================================================

.nexus-input__helper {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  min-height: 1.2rem;
  font-size: 0.75rem;
}

.nexus-input__error-message {
  color: var(--color-error, #f44336);
}

.nexus-input__helper-text {
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Animations
// ==========================================================================

@keyframes nexus-input-spin {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes nexus-input-spinner-dash {
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
  .nexus-input-wrapper {
    --nexus-input-bg: var(--color-bg-input, #f0f2f5);
    --nexus-input-border: var(--color-border, #d0d8e0);
  }
  .nexus-input__field {
    color: var(--color-text-primary, #1a1a2e);
    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }
  .nexus-input__label {
    color: var(--color-text-secondary, #3d4a5c);
  }
  .nexus-input__clear:hover {
    background: var(--color-bg-hover, #e3e8ef);
  }
}
</style>
