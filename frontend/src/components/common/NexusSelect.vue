<!-- ==========================================================================
  NexusDL 2.0 - NexusSelect Component
  Fichier : frontend/src/components/common/NexusSelect.vue
  Description : Composant de sélection ultra-complet (simple/multiple,
                recherche, groupes, tags, chargement, etc.)
  Version : 2.0.0
  Licence : GNU GPL v3.0
  ⚠️ CORRECTION : `sticky;` → `position: sticky;` (ligne ~504)
========================================================================== -->

<template>
  <div
    ref="wrapperRef"
    class="nexus-select-wrapper"
    :class="[
      `nexus-select-wrapper--${size}`,
      {
        'nexus-select-wrapper--disabled': disabled,
        'nexus-select-wrapper--error': error,
        'nexus-select-wrapper--success': success,
        'nexus-select-wrapper--loading': loading,
        'nexus-select-wrapper--focused': isFocused,
        'nexus-select-wrapper--open': isOpen,
        'nexus-select-wrapper--with-label': !!label,
        'nexus-select-wrapper--with-helper': hasHelper,
        'nexus-select-wrapper--block': block,
        'nexus-select-wrapper--rounded': rounded,
        'nexus-select-wrapper--multiple': multiple,
        'nexus-select-wrapper--clearable': clearable && hasValue,
        'nexus-select-wrapper--searchable': searchable,
      },
    ]"
    :style="customStyle"
  >
    <!-- ==================================================================
      LABEL
    =================================================================== -->
    <label
      v-if="label"
      :for="id"
      class="nexus-select__label"
      :class="{ 'nexus-select__label--required': required }"
    >
      {{ label }}
      <span
        v-if="required"
        class="nexus-select__label-required"
        aria-hidden="true"
      >
        *
      </span>
    </label>

    <!-- ==================================================================
      CONTRÔLE
    =================================================================== -->
    <div
      class="nexus-select__control"
      role="combobox"
      :aria-expanded="isOpen"
      :aria-controls="`${id}-listbox`"
      :aria-haspopup="'listbox'"
      :aria-label="ariaLabel || label"
      :aria-invalid="!!error"
      :aria-disabled="disabled"
      :aria-required="required"
      :aria-activedescendant="
        highlightedIndex >= 0 ? `${id}-option-${highlightedIndex}` : undefined
      "
      :tabindex="disabled ? -1 : 0"
      @click="toggleDropdown"
      @keydown="handleKeyDown"
      @focus="isFocused = true"
      @blur="isFocused = false"
    >
      <!-- Conteneur des valeurs -->
      <div class="nexus-select__value-container">
        <!-- Mode multiple : tags -->
        <template v-if="multiple && selectedItems.length">
          <span
            v-for="item in selectedItems"
            :key="item.value"
            class="nexus-select__tag"
          >
            <span class="nexus-select__tag-label">
              {{ item.label }}
            </span>
            <button
              type="button"
              class="nexus-select__tag-remove"
              :aria-label="`Retirer ${item.label}`"
              @mousedown.prevent
              @click.stop="removeItem(item)"
            >
              <span aria-hidden="true">&times;</span>
            </button>
          </span>
        </template>

        <!-- Mode simple : valeur sélectionnée -->
        <span
          v-else-if="selectedItems.length === 1"
          class="nexus-select__single-value"
        >
          {{ selectedItems[0].label }}
        </span>

        <!-- Placeholder -->
        <span v-else class="nexus-select__placeholder">
          {{ placeholder || 'Sélectionnez une option' }}
        </span>

        <!-- Champ de recherche -->
        <input
          v-if="searchable"
          ref="searchInputRef"
          v-model="searchQuery"
          type="text"
          class="nexus-select__search-input"
          :placeholder="searchPlaceholder || 'Rechercher...'"
          :disabled="disabled"
          :aria-label="`Rechercher dans ${label || 'les options'}`"
          autocomplete="off"
          spellcheck="false"
          @input="handleSearchInput"
          @focus="handleSearchFocus"
          @blur="handleSearchBlur"
          @keydown.stop="handleSearchKeydown"
        />
      </div>

      <!-- Indicateurs à droite -->
      <div class="nexus-select__indicators">
        <!-- Spinner de chargement -->
        <span v-if="loading" class="nexus-select__spinner" aria-hidden="true">
          <svg
            class="nexus-select__spinner-icon"
            viewBox="0 0 50 50"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle
              class="nexus-select__spinner-path"
              cx="25"
              cy="25"
              r="20"
              fill="none"
              stroke-width="4"
            />
          </svg>
        </span>

        <!-- Statuts succès/erreur -->
        <span
          v-if="success"
          class="nexus-select__status nexus-select__status--success"
          aria-hidden="true"
        >
          ✓
        </span>
        <span
          v-if="error"
          class="nexus-select__status nexus-select__status--error"
          aria-hidden="true"
        >
          ✕
        </span>

        <!-- Bouton d'effacement -->
        <button
          v-if="clearable && hasValue && !disabled"
          type="button"
          class="nexus-select__clear"
          aria-label="Effacer la sélection"
          @mousedown.prevent
          @click.stop="clearValue"
        >
          <span aria-hidden="true">&times;</span>
        </button>

        <!-- Flèche -->
        <span class="nexus-select__arrow" aria-hidden="true">
          <svg
            viewBox="0 0 12 8"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M1 1l5 5 5-5" />
          </svg>
        </span>
      </div>
    </div>

    <!-- ==================================================================
      HELPER / ERROR
    =================================================================== -->
    <div v-if="hasHelper" class="nexus-select__helper">
      <span v-if="error" class="nexus-select__error-message" role="alert">
        {{ error }}
      </span>
      <span v-else-if="helper" class="nexus-select__helper-text">
        {{ helper }}
      </span>
    </div>

    <!-- ==================================================================
      DROPDOWN (teleporté)
    =================================================================== -->
    <Teleport to="body">
      <Transition
        name="nexus-select-dropdown"
        @before-enter="beforeDropdownEnter"
        @after-enter="afterDropdownEnter"
        @before-leave="beforeDropdownLeave"
      >
        <div
          v-if="isOpen"
          :id="`${id}-listbox`"
          ref="dropdownRef"
          class="nexus-select__dropdown"
          :class="[
            `nexus-select__dropdown--${size}`,
            {
              'nexus-select__dropdown--scrollable':
                filteredOptions.length > 10,
            },
          ]"
          role="listbox"
          :aria-label="`Options pour ${label || 'sélection'}`"
          @mousedown.stop
        >
          <!-- Chargement -->
          <div v-if="loading" class="nexus-select__empty">
            <slot name="loading">
              <span class="nexus-select__empty-text">Chargement...</span>
            </slot>
          </div>

          <!-- Aucun résultat -->
          <div
            v-else-if="filteredOptions.length === 0"
            class="nexus-select__empty"
          >
            <slot name="empty">
              <span class="nexus-select__empty-text">{{ noResultsText }}</span>
            </slot>
          </div>

          <!-- Liste -->
          <template v-else>
            <!-- Options groupées -->
            <template v-if="groupedOptions.length > 0">
              <div
                v-for="(group, groupIndex) in groupedOptions"
                :key="group.group || `group-${groupIndex}`"
                class="nexus-select__option-group"
              >
                <div
                  v-if="group.group"
                  class="nexus-select__option-group-label"
                >
                  {{ group.group }}
                </div>
                <div
                  v-for="option in group.options"
                  :id="`${id}-option-${getOptionIndex(option)}`"
                  :key="option.value"
                  class="nexus-select__option"
                  :class="{
                    'nexus-select__option--highlighted':
                      getOptionIndex(option) === highlightedIndex,
                    'nexus-select__option--selected': isSelected(option),
                    'nexus-select__option--disabled': option.disabled,
                  }"
                  role="option"
                  :aria-selected="isSelected(option)"
                  :aria-disabled="option.disabled"
                  @click="selectOption(option)"
                  @mouseenter="highlightOption(getOptionIndex(option))"
                >
                  <slot name="option" :option="option">
                    <span
                      v-if="multiple"
                      class="nexus-select__option-checkbox"
                    >
                      <span
                        v-if="isSelected(option)"
                        class="nexus-select__option-checkmark"
                      >
                        ✓
                      </span>
                    </span>
                    <span class="nexus-select__option-label">
                      {{ option.label }}
                    </span>
                  </slot>
                </div>
              </div>
            </template>

            <!-- Options non groupées -->
            <div
              v-for="(option, index) in filteredOptions"
              :id="`${id}-option-${index}`"
              :key="option.value"
              class="nexus-select__option"
              :class="{
                'nexus-select__option--highlighted': index === highlightedIndex,
                'nexus-select__option--selected': isSelected(option),
                'nexus-select__option--disabled': option.disabled,
              }"
              role="option"
              :aria-selected="isSelected(option)"
              :aria-disabled="option.disabled"
              @click="selectOption(option)"
              @mouseenter="highlightOption(index)"
            >
              <slot name="option" :option="option">
                <span v-if="multiple" class="nexus-select__option-checkbox">
                  <span
                    v-if="isSelected(option)"
                    class="nexus-select__option-checkmark"
                  >
                    ✓
                  </span>
                </span>
                <span class="nexus-select__option-label">
                  {{ option.label }}
                </span>
              </slot>
            </div>
          </template>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import {
  ref,
  computed,
  watch,
  onMounted,
  onUnmounted,
  nextTick,
} from 'vue'

// ==========================================================================
//  Props
// ==========================================================================

const props = defineProps({
  /** Identifiant unique (auto-généré si non fourni) */
  id: {
    type: String,
    default: () => `nexus-select-${Math.random().toString(36).slice(2, 7)}`,
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
  /** Placeholder de la recherche */
  searchPlaceholder: {
    type: String,
    default: '',
  },
  /** Valeur liée (v-model) */
  modelValue: {
    type: [String, Number, Array],
    default: () => [],
  },
  /** Options : [{ value, label, group?, disabled? }] */
  options: {
    type: Array,
    default: () => [],
  },
  /** Mode multiple */
  multiple: {
    type: Boolean,
    default: false,
  },
  /** Activer la recherche */
  searchable: {
    type: Boolean,
    default: false,
  },
  /** Afficher un bouton pour effacer */
  clearable: {
    type: Boolean,
    default: false,
  },
  /** Désactivé */
  disabled: {
    type: Boolean,
    default: false,
  },
  /** État de chargement */
  loading: {
    type: Boolean,
    default: false,
  },
  /** Message d'erreur */
  error: {
    type: String,
    default: '',
  },
  /** Message d'aide */
  helper: {
    type: String,
    default: '',
  },
  /** État de succès */
  success: {
    type: Boolean,
    default: false,
  },
  /** Requis */
  required: {
    type: Boolean,
    default: false,
  },
  /** Taille */
  size: {
    type: String,
    default: 'md',
    validator: (val) => ['sm', 'md', 'lg'].includes(val),
  },
  /** Largeur pleine */
  block: {
    type: Boolean,
    default: true,
  },
  /** Coins arrondis */
  rounded: {
    type: Boolean,
    default: false,
  },
  /** Label ARIA */
  ariaLabel: {
    type: String,
    default: '',
  },
  /** Texte affiché quand aucun résultat */
  noResultsText: {
    type: String,
    default: 'Aucun résultat',
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
  'update:modelValue',
  'change',
  'focus',
  'blur',
  'search',
  'clear',
  'open',
  'close',
])

// ==========================================================================
//  Computed — Aides
// ==========================================================================

const hasHelper = computed(() => !!props.helper || !!props.error)

// ==========================================================================
//  Références DOM
// ==========================================================================

const wrapperRef = ref(null)
const dropdownRef = ref(null)
const searchInputRef = ref(null)

// ==========================================================================
//  État local
// ==========================================================================

const isOpen = ref(false)
const isFocused = ref(false)
const searchQuery = ref('')
const highlightedIndex = ref(-1)
const isMouseDown = ref(false)

// ==========================================================================
//  Computed — Options et valeurs
// ==========================================================================

const selectedValue = computed(() => {
  if (props.multiple) {
    return props.modelValue || []
  }
  return props.modelValue !== undefined && props.modelValue !== null
    ? props.modelValue
    : ''
})

const normalizedOptions = computed(() => {
  return props.options.map((opt, idx) => ({
    ...opt,
    value: opt.value ?? opt.id ?? idx,
    label: opt.label ?? opt.text ?? `Option ${idx + 1}`,
    disabled: opt.disabled || false,
    group: opt.group || null,
    _index: idx,
  }))
})

const filteredOptions = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return normalizedOptions.value
  return normalizedOptions.value.filter((opt) =>
    opt.label.toLowerCase().includes(query)
  )
})

const groupedOptions = computed(() => {
  const hasGroups = filteredOptions.value.some((opt) => opt.group)
  if (!hasGroups) return []

  const groups = {}
  for (const opt of filteredOptions.value) {
    const key = opt.group || ''
    if (!groups[key]) groups[key] = []
    groups[key].push(opt)
  }
  return Object.entries(groups).map(([group, options]) => ({
    group: group || null,
    options,
  }))
})

const selectedItems = computed(() => {
  if (props.multiple) {
    const values = Array.isArray(selectedValue.value)
      ? selectedValue.value
      : []
    return normalizedOptions.value.filter((opt) => values.includes(opt.value))
  }
  const val = selectedValue.value
  if (val === '' || val === null || val === undefined) return []
  const found = normalizedOptions.value.find((opt) => opt.value === val)
  return found ? [found] : []
})

const hasValue = computed(() => {
  if (props.multiple) {
    return (
      Array.isArray(selectedValue.value) && selectedValue.value.length > 0
    )
  }
  return (
    selectedValue.value !== '' &&
    selectedValue.value !== null &&
    selectedValue.value !== undefined
  )
})

// ==========================================================================
//  Méthodes utilitaires
// ==========================================================================

function isSelected(option) {
  if (props.multiple) {
    return (
      Array.isArray(selectedValue.value) &&
      selectedValue.value.includes(option.value)
    )
  }
  return selectedValue.value === option.value
}

function getOptionIndex(option) {
  return filteredOptions.value.findIndex((opt) => opt.value === option.value)
}

// ==========================================================================
//  Gestion de la sélection
// ==========================================================================

function selectOption(option) {
  if (option.disabled || props.disabled || props.loading) return

  if (props.multiple) {
    const current = Array.isArray(selectedValue.value)
      ? [...selectedValue.value]
      : []
    const index = current.indexOf(option.value)
    if (index > -1) {
      current.splice(index, 1)
    } else {
      current.push(option.value)
    }
    emit('update:modelValue', current)
    emit('change', current)
    if (searchInputRef.value) {
      searchInputRef.value.focus()
    }
  } else {
    emit('update:modelValue', option.value)
    emit('change', option.value)
    closeDropdown()
  }
}

function removeItem(item) {
  if (props.disabled || props.loading) return
  if (props.multiple) {
    const current = Array.isArray(selectedValue.value)
      ? [...selectedValue.value]
      : []
    const index = current.indexOf(item.value)
    if (index > -1) {
      current.splice(index, 1)
      emit('update:modelValue', current)
      emit('change', current)
    }
  } else {
    clearValue()
  }
}

function clearValue() {
  if (props.disabled || props.loading) return
  if (props.multiple) {
    emit('update:modelValue', [])
    emit('change', [])
  } else {
    emit('update:modelValue', '')
    emit('change', '')
  }
  emit('clear')
  searchQuery.value = ''
  closeDropdown()
}

// ==========================================================================
//  Gestion du dropdown
// ==========================================================================

function toggleDropdown() {
  if (props.disabled || props.loading) return
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    emit('open')
    searchQuery.value = ''
    highlightedIndex.value = -1
    nextTick(() => {
      if (searchInputRef.value) {
        searchInputRef.value.focus()
      }
      updateDropdownPosition()
    })
  } else {
    emit('close')
  }
}

function openDropdown() {
  if (isOpen.value || props.disabled || props.loading) return
  isOpen.value = true
  emit('open')
  if (searchInputRef.value) {
    nextTick(() => searchInputRef.value.focus())
  }
  updateDropdownPosition()
}

function closeDropdown() {
  if (!isOpen.value) return
  isOpen.value = false
  emit('close')
  highlightedIndex.value = -1
}

function updateDropdownPosition() {
  if (!wrapperRef.value || !dropdownRef.value) return
  const rect = wrapperRef.value.getBoundingClientRect()
  const dropdownEl = dropdownRef.value
  const scrollY = window.scrollY
  const scrollX = window.scrollX
  const top = rect.bottom + scrollY
  const left = rect.left + scrollX
  const width = rect.width

  dropdownEl.style.top = `${top}px`
  dropdownEl.style.left = `${left}px`
  dropdownEl.style.width = `${width}px`
  dropdownEl.style.maxHeight = '250px'
  dropdownEl.style.overflowY = 'auto'
}

// ==========================================================================
//  Recherche
// ==========================================================================

function handleSearchInput(event) {
  emit('search', event.target.value)
  highlightedIndex.value = -1
}

function handleSearchFocus(event) {
  isFocused.value = true
  emit('focus', event)
}

function handleSearchBlur(event) {
  setTimeout(() => {
    if (!isMouseDown.value) {
      closeDropdown()
    }
    isMouseDown.value = false
  }, 100)
  isFocused.value = false
  emit('blur', event)
}

function handleSearchKeydown(event) {
  if (event.key === 'Escape') {
    closeDropdown()
    event.preventDefault()
  } else if (event.key === 'ArrowDown') {
    event.preventDefault()
    highlightedIndex.value = Math.min(
      highlightedIndex.value + 1,
      filteredOptions.value.length - 1
    )
    scrollToHighlighted()
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    highlightedIndex.value = Math.max(highlightedIndex.value - 1, -1)
    scrollToHighlighted()
  } else if (event.key === 'Enter') {
    event.preventDefault()
    if (
      highlightedIndex.value >= 0 &&
      highlightedIndex.value < filteredOptions.value.length
    ) {
      const option = filteredOptions.value[highlightedIndex.value]
      if (option && !option.disabled) {
        selectOption(option)
      }
    }
  }
}

// ==========================================================================
//  Navigation clavier sur le contrôle
// ==========================================================================

function handleKeyDown(event) {
  if (event.key === 'Escape') {
    closeDropdown()
  } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    if (!isOpen.value) {
      openDropdown()
    } else {
      const direction = event.key === 'ArrowDown' ? 1 : -1
      const newIndex = highlightedIndex.value + direction
      if (newIndex >= 0 && newIndex < filteredOptions.value.length) {
        highlightedIndex.value = newIndex
        scrollToHighlighted()
      }
    }
  } else if (event.key === 'Enter') {
    event.preventDefault()
    if (
      isOpen.value &&
      highlightedIndex.value >= 0 &&
      highlightedIndex.value < filteredOptions.value.length
    ) {
      const option = filteredOptions.value[highlightedIndex.value]
      if (option && !option.disabled) {
        selectOption(option)
      }
    } else if (!isOpen.value) {
      openDropdown()
    }
  } else if (event.key === ' ' && !props.searchable) {
    event.preventDefault()
    toggleDropdown()
  }
}

function scrollToHighlighted() {
  if (highlightedIndex.value < 0) return
  const container = dropdownRef.value
  if (!container) return
  const items = container.querySelectorAll('.nexus-select__option')
  const item = items[highlightedIndex.value]
  if (item) {
    item.scrollIntoView({ block: 'nearest' })
  }
}

function highlightOption(index) {
  highlightedIndex.value = index
}

// ==========================================================================
//  Fermeture externe et redimensionnement
// ==========================================================================

function handleClickOutside(event) {
  if (
    wrapperRef.value &&
    !wrapperRef.value.contains(event.target) &&
    isOpen.value
  ) {
    if (dropdownRef.value && dropdownRef.value.contains(event.target)) return
    closeDropdown()
  }
}

function handleWindowResize() {
  if (isOpen.value) {
    updateDropdownPosition()
  }
}

// ==========================================================================
//  Transitions dropdown
// ==========================================================================

function beforeDropdownEnter() {}
function afterDropdownEnter() {
  updateDropdownPosition()
}
function beforeDropdownLeave() {}

// ==========================================================================
//  Styles calculés
// ==========================================================================

const customStyle = computed(() => {
  const style = {}
  if (props.customColor) {
    style.setProperty('--nexus-select-color', props.customColor)
  }
  if (props.customBackground) {
    style.setProperty('--nexus-select-bg', props.customBackground)
  }
  if (props.customBorder) {
    style.setProperty('--nexus-select-border', props.customBorder)
  }
  return style
})

// ==========================================================================
//  Watchers
// ==========================================================================

watch(
  () => props.options,
  () => {},
  { deep: true }
)

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('resize', handleWindowResize)
  if (isOpen.value) {
    updateDropdownPosition()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('resize', handleWindowResize)
})

// ==========================================================================
//  Exposer les méthodes
// ==========================================================================

defineExpose({
  open: openDropdown,
  close: closeDropdown,
  toggle: toggleDropdown,
  focus: () => wrapperRef.value?.focus(),
  clear: clearValue,
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Variables
// ==========================================================================

$select-radius-sm: var(--radius-sm, 4px);
$select-radius-md: var(--radius-md, 8px);
$select-radius-lg: var(--radius-lg, 12px);
$select-transition: all var(--transition-fast, 150ms) ease;

// ==========================================================================
//  Wrapper
// ==========================================================================

.nexus-select-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  width: 100%;
  max-width: 100%;
  --nexus-select-color: var(--color-primary, #00d4ff);
  --nexus-select-bg: var(--color-bg-input, #1e2a40);
  --nexus-select-border: var(--color-border, #1a2538);

  &--block {
    width: 100%;
  }

  // Tailles
  &--sm {
    .nexus-select__label {
      font-size: 0.75rem;
    }
    .nexus-select__control {
      min-height: 28px;
      font-size: 0.8rem;
      padding: 0.1rem 0.3rem;
      border-radius: $select-radius-sm;
    }
    .nexus-select__tag {
      font-size: 0.7rem;
      padding: 0.05rem 0.3rem;
    }
    .nexus-select__search-input {
      font-size: 0.8rem;
      padding: 0.1rem 0.2rem;
    }
    .nexus-select__placeholder,
    .nexus-select__single-value {
      font-size: 0.8rem;
    }
    .nexus-select__option {
      font-size: 0.8rem;
      padding: 0.2rem 0.6rem;
    }
    .nexus-select__option-group-label {
      font-size: 0.7rem;
    }
    .nexus-select__helper-text,
    .nexus-select__error-message {
      font-size: 0.7rem;
    }
  }

  &--md {
    .nexus-select__label {
      font-size: 0.85rem;
    }
    .nexus-select__control {
      min-height: 36px;
      font-size: 0.95rem;
      padding: 0.15rem 0.5rem;
      border-radius: $select-radius-md;
    }
    .nexus-select__tag {
      font-size: 0.8rem;
      padding: 0.1rem 0.4rem;
    }
    .nexus-select__search-input {
      font-size: 0.95rem;
      padding: 0.15rem 0.3rem;
    }
    .nexus-select__placeholder,
    .nexus-select__single-value {
      font-size: 0.95rem;
    }
    .nexus-select__option {
      font-size: 0.9rem;
      padding: 0.3rem 0.8rem;
    }
    .nexus-select__option-group-label {
      font-size: 0.75rem;
    }
    .nexus-select__helper-text,
    .nexus-select__error-message {
      font-size: 0.75rem;
    }
  }

  &--lg {
    .nexus-select__label {
      font-size: 1rem;
    }
    .nexus-select__control {
      min-height: 44px;
      font-size: 1.1rem;
      padding: 0.2rem 0.7rem;
      border-radius: $select-radius-lg;
    }
    .nexus-select__tag {
      font-size: 0.9rem;
      padding: 0.15rem 0.5rem;
    }
    .nexus-select__search-input {
      font-size: 1.1rem;
      padding: 0.2rem 0.4rem;
    }
    .nexus-select__placeholder,
    .nexus-select__single-value {
      font-size: 1.1rem;
    }
    .nexus-select__option {
      font-size: 1rem;
      padding: 0.4rem 1rem;
    }
    .nexus-select__option-group-label {
      font-size: 0.85rem;
    }
    .nexus-select__helper-text,
    .nexus-select__error-message {
      font-size: 0.85rem;
    }
  }

  // Arrondi
  &.nexus-select-wrapper--rounded {
    .nexus-select__control {
      border-radius: var(--radius-full, 9999px);
    }
    .nexus-select__dropdown {
      border-radius: var(--radius-full, 9999px);
    }
  }

  // États
  &.nexus-select-wrapper--disabled {
    opacity: 0.6;
    cursor: not-allowed;
    .nexus-select__control {
      cursor: not-allowed;
      pointer-events: none;
    }
  }

  &.nexus-select-wrapper--error {
    .nexus-select__control {
      border-color: var(--color-error, #f44336);
      &:focus {
        border-color: var(--color-error, #f44336);
        box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.15);
      }
    }
    .nexus-select__label {
      color: var(--color-error, #f44336);
    }
  }

  &.nexus-select-wrapper--success {
    .nexus-select__control {
      border-color: var(--color-success, #4caf50);
      &:focus {
        border-color: var(--color-success, #4caf50);
        box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.15);
      }
    }
  }

  &.nexus-select-wrapper--focused {
    .nexus-select__control {
      border-color: var(--nexus-select-color);
      box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15);
    }
  }

  &.nexus-select-wrapper--multiple {
    .nexus-select__control {
      flex-wrap: wrap;
      gap: 0.2rem;
    }
  }
}

// ==========================================================================
//  Label
// ==========================================================================

.nexus-select__label {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-weight: var(--font-weight-medium, 500);
  color: var(--color-text-secondary, #b0c0d8);
  cursor: pointer;
  user-select: none;

  &--required .nexus-select__label-required {
    color: var(--color-error, #f44336);
  }
}

// ==========================================================================
//  Control
// ==========================================================================

.nexus-select__control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--nexus-select-bg);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--nexus-select-border);
  transition: $select-transition;
  cursor: pointer;
  outline: none;
  position: relative;
  gap: 0.25rem;

  &:focus {
    border-color: var(--nexus-select-color);
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15);
  }

  &:hover:not(.nexus-select-wrapper--disabled) {
    border-color: var(--nexus-select-color);
  }
}

// ==========================================================================
//  Value container
// ==========================================================================

.nexus-select__value-container {
  display: flex;
  flex: 1;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.2rem;
  min-width: 0;
  overflow: hidden;
}

// ==========================================================================
//  Placeholder et valeur simple
// ==========================================================================

.nexus-select__placeholder {
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
}

.nexus-select__single-value {
  pointer-events: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

// ==========================================================================
//  Tags (mode multiple)
// ==========================================================================

.nexus-select__tag {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  background: var(--nexus-select-color);
  color: var(--color-text-inverse, #0a0e1a);
  border-radius: var(--radius-sm, 4px);
  padding: 0.1rem 0.4rem;
  font-weight: var(--font-weight-medium, 500);
  max-width: 100%;
}

.nexus-select__tag-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nexus-select__tag-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: inherit;
  font-size: 1em;
  line-height: 1;
  cursor: pointer;
  padding: 0 0.1rem;
  opacity: 0.7;
  transition: opacity var(--transition-fast, 150ms) ease;

  &:hover {
    opacity: 1;
  }

  &:focus-visible {
    outline: 2px solid var(--color-primary, #00d4ff);
    outline-offset: 2px;
  }
}

// ==========================================================================
//  Search input
// ==========================================================================

.nexus-select__search-input {
  flex: 1;
  min-width: 50px;
  background: transparent;
  border: none;
  outline: none;
  color: var(--color-text-primary, #e8edf5);
  font-family: inherit;
  padding: 0;
  margin: 0;

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }

  &:disabled {
    cursor: not-allowed;
  }
}

// ==========================================================================
//  Indicateurs (à droite)
// ==========================================================================

.nexus-select__indicators {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  flex-shrink: 0;
}

.nexus-select__spinner {
  display: inline-flex;
  width: 1em;
  height: 1em;
  animation: nexus-select-spin 0.8s linear infinite;
}

.nexus-select__spinner-icon {
  width: 100%;
  height: 100%;
}

.nexus-select__spinner-path {
  stroke: var(--nexus-select-color);
  stroke-linecap: round;
  stroke-dasharray: 90, 150;
  stroke-dashoffset: 0;
  animation: nexus-select-spinner-dash 1.5s ease-in-out infinite;
}

.nexus-select__status {
  display: inline-flex;
  align-items: center;
  font-weight: var(--font-weight-bold, 700);
  font-size: 0.9em;

  &--success {
    color: var(--color-success, #4caf50);
  }

  &--error {
    color: var(--color-error, #f44336);
  }
}

.nexus-select__clear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1.2em;
  line-height: 1;
  cursor: pointer;
  padding: 0 0.1rem;
  transition: $select-transition;

  &:hover {
    color: var(--color-text-primary, #e8edf5);
  }

  &:focus-visible {
    outline: 2px solid var(--nexus-select-color);
    outline-offset: 2px;
  }
}

.nexus-select__arrow {
  display: inline-flex;
  align-items: center;
  color: var(--color-text-muted, #6a7a9a);
  transition: transform var(--transition-fast, 150ms) ease;
  font-size: 0.8em;

  svg {
    width: 1em;
    height: 0.7em;
  }

  .nexus-select-wrapper--open & {
    transform: rotate(180deg);
  }
}

// ==========================================================================
//  Helper / Error
// ==========================================================================

.nexus-select__helper {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  min-height: 1.2rem;
  font-size: 0.75rem;
}

.nexus-select__error-message {
  color: var(--color-error, #f44336);
}

.nexus-select__helper-text {
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Dropdown (teleporté)
// ==========================================================================

.nexus-select__dropdown {
  position: fixed;
  z-index: 2000;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  box-shadow: var(--shadow-lg, 0 8px 24px rgba(0, 0, 0, 0.5));
  max-height: 250px;
  overflow-y: auto;
  padding: 0.2rem 0;
  min-width: 150px;

  &--sm {
    font-size: 0.8rem;
  }

  &--md {
    font-size: 0.95rem;
  }

  &--lg {
    font-size: 1.1rem;
  }

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: var(--color-bg-secondary, #141a2b);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #1a2538);
    border-radius: 3px;

    &:hover {
      background: var(--color-text-muted, #6a7a9a);
    }
  }

  scrollbar-width: thin;
  scrollbar-color: var(--color-border) var(--color-bg-secondary);
}

// ==========================================================================
//  Options
// ==========================================================================

.nexus-select__option-group {
  &:not(:last-child) {
    border-bottom: 1px solid var(--color-border, #1a2538);
    padding-bottom: 0.2rem;
    margin-bottom: 0.2rem;
  }
}

.nexus-select__option-group-label {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 0.3rem 0.8rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: var(--color-bg-secondary, #141a2b);
}

.nexus-select__option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.8rem;
  cursor: pointer;
  transition: background var(--transition-fast, 150ms) ease;
  color: var(--color-text-primary, #e8edf5);

  &--highlighted {
    background: var(--color-bg-hover, #253254);
  }

  &--selected {
    color: var(--nexus-select-color);
    font-weight: var(--font-weight-semibold, 600);
  }

  &--disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }

  &:hover:not(&--disabled) {
    background: var(--color-bg-hover, #253254);
  }
}

.nexus-select__option-checkbox {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1em;
  height: 1em;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  flex-shrink: 0;
  font-size: 0.7em;
  color: var(--nexus-select-color);

  .nexus-select__option-checkmark {
    font-weight: bold;
  }
}

.nexus-select__option-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

// ==========================================================================
//  Empty / Loading
// ==========================================================================

.nexus-select__empty {
  padding: 1rem;
  text-align: center;
  color: var(--color-text-muted, #6a7a9a);
}

.nexus-select__empty-text {
  font-style: italic;
}

// ==========================================================================
//  Animations du dropdown
// ==========================================================================

.nexus-select-dropdown-enter-active,
.nexus-select-dropdown-leave-active {
  transition: opacity var(--transition-fast, 150ms) ease,
    transform var(--transition-fast, 150ms) ease;
}

.nexus-select-dropdown-enter-from,
.nexus-select-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}

.nexus-select-dropdown-enter-to,
.nexus-select-dropdown-leave-from {
  opacity: 1;
  transform: translateY(0) scale(1);
}

// ==========================================================================
//  Animations (spinner)
// ==========================================================================

@keyframes nexus-select-spin {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes nexus-select-spinner-dash {
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
  .nexus-select-wrapper {
    --nexus-select-bg: var(--color-bg-input, #f0f2f5);
    --nexus-select-border: var(--color-border, #d0d8e0);
  }

  .nexus-select__control {
    color: var(--color-text-primary, #1a1a2e);
  }

  .nexus-select__search-input {
    color: var(--color-text-primary, #1a1a2e);

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .nexus-select__label {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .nexus-select__option {
    color: var(--color-text-primary, #1a1a2e);

    &--highlighted {
      background: var(--color-bg-hover, #e3e8ef);
    }

    &--selected {
      color: var(--nexus-select-color);
    }

    &:hover:not(&--disabled) {
      background: var(--color-bg-hover, #e3e8ef);
    }
  }

  .nexus-select__dropdown {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
    box-shadow: var(--shadow-lg, 0 8px 24px rgba(0, 0, 0, 0.12));
  }

  .nexus-select__option-group-label {
    background: var(--color-bg-secondary, #e9ecf2);
    color: var(--color-text-muted, #7a8a9a);
  }

  .nexus-select__tag {
    color: var(--color-text-inverse, #0a0e1a);
  }

  .nexus-select__clear:hover {
    color: var(--color-text-primary, #1a1a2e);
  }

  .nexus-select__placeholder {
    color: var(--color-text-muted, #7a8a9a);
  }

  .nexus-select__single-value {
    color: var(--color-text-primary, #1a1a2e);
  }
}
</style>
