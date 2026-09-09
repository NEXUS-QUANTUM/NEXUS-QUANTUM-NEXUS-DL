// ==========================================================================
//  NexusDL 2.0 - focus Directive
//  Fichier : frontend/src/directives/focus.js
//  Description : Directive Vue pour gérer le focus sur les éléments
//  Version : 2.0.0
// ==========================================================================

/**
 * Directive personnalisée Vue pour gérer automatiquement le focus sur un élément.
 *
 * Utilisation :
 * ```vue
 * <!-- Focus automatique au montage -->
 * <input v-focus />
 *
 * <!-- Focus conditionnel (si la condition est vraie) -->
 * <input v-focus="isVisible" />
 *
 * <!-- Focus avec sélection du texte -->
 * <input v-focus.select />
 *
 * <!-- Focus avec délai (en millisecondes) -->
 * <input v-focus.delay="300" />
 *
 * <!-- Focus avec sélection et délai -->
 * <input v-focus.select.delay="200" />
 *
 * <!-- Focus sans défilement -->
 * <input v-focus.prevent-scroll />
 *
 * <!-- Focus sur un composant personnalisé (avec méthode focus) -->
 * <MyCustomInput v-focus />
 * ```
 *
 * Modificateurs disponibles :
 * - .select          : Sélectionne tout le contenu du champ après le focus
 * - .delay           : Ajoute un délai avant de mettre le focus (valeur en ms)
 * - .prevent-scroll  : Empêche le défilement vers l'élément (option scrollIntoView)
 * - .no-scroll       : Alias pour .prevent-scroll
 * - .once            : Ne met le focus qu'une seule fois (après le montage)
 * - .immediate       : Focus immédiat (même comportement que sans modificateur)
 *
 * Si la valeur passée est une promesse, le focus sera déclenché après résolution.
 */

/**
 * Vérifie si un élément peut recevoir le focus.
 * @param {HTMLElement} el - Élément à vérifier
 * @returns {boolean}
 */
function isFocusable(el) {
  if (!el) return false
  const tag = el.tagName.toLowerCase()
  const type = el.getAttribute('type')
  // Éléments pouvant recevoir le focus
  if (tag === 'input' && type !== 'hidden') return true
  if (tag === 'textarea') return true
  if (tag === 'select') return true
  if (tag === 'button') return true
  if (tag === 'a' && el.hasAttribute('href')) return true
  if (el.hasAttribute('tabindex')) return true
  if (el.isContentEditable) return true
  // Vérifier si c'est un composant avec une méthode focus (custom element)
  if (typeof el.focus === 'function') return true
  return false
}

/**
 * Trouve le premier élément focusable dans un composant.
 * @param {HTMLElement} el - Élément racine
 * @returns {HTMLElement|null}
 */
function findFocusableElement(el) {
  // Si l'élément lui-même est focusable, le retourner
  if (isFocusable(el)) return el

  // Chercher parmi les enfants un élément input, textarea, select, button, a, ou avec tabindex
  const focusableSelectors = [
    'input:not([type="hidden"])',
    'textarea',
    'select',
    'button',
    'a[href]',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
  ]
  for (const selector of focusableSelectors) {
    const child = el.querySelector(selector)
    if (child && isFocusable(child)) return child
  }
  // Si aucun trouvé, on tente de trouver un élément avec un rôle de champ
  const roleFields = el.querySelectorAll('[role="textbox"], [role="searchbox"], [role="spinbutton"]')
  for (const field of roleFields) {
    if (isFocusable(field)) return field
  }
  return null
}

/**
 * Applique le focus sur un élément (ou son premier enfant focusable).
 * @param {HTMLElement} el - Élément cible
 * @param {Object} options - Options (select, preventScroll, delay)
 * @returns {Promise<void>}
 */
function applyFocus(el, options = {}) {
  return new Promise((resolve) => {
    const { select = false, preventScroll = false, delay = 0 } = options

    // Trouver l'élément focusable
    let focusable = isFocusable(el) ? el : findFocusableElement(el)

    // Si on a un composant personnalisé avec une méthode focus, l'utiliser
    if (el && typeof el.focus === 'function' && !isFocusable(el)) {
      focusable = el
    }

    if (!focusable) {
      console.warn('[v-focus] Aucun élément focusable trouvé dans', el)
      return resolve()
    }

    // Appliquer le délai
    setTimeout(() => {
      try {
        // Focus
        focusable.focus({ preventScroll })

        // Sélectionner le texte si demandé
        if (select && (focusable.tagName === 'INPUT' || focusable.tagName === 'TEXTAREA')) {
          focusable.select()
        }

        // Si c'est un composant personnalisé, on appelle sa méthode select si elle existe
        if (select && typeof focusable.select === 'function' && focusable !== el) {
          // Ne pas appeler si on l'a déjà fait pour input/textarea
          if (focusable.tagName !== 'INPUT' && focusable.tagName !== 'TEXTAREA') {
            focusable.select()
          }
        }

        // Émettre un événement personnalisé pour notifier que le focus a été appliqué
        el.dispatchEvent(new CustomEvent('focus-applied', {
          detail: { element: focusable, options },
          bubbles: true,
        }))

        resolve()
      } catch (err) {
        console.warn('[v-focus] Erreur lors de l\'application du focus:', err)
        resolve()
      }
    }, delay)
  })
}

// ==========================================================================
//  Hooks de la directive
// ==========================================================================

/**
 * Hook mounted : applique le focus au montage si la condition est remplie.
 * @param {HTMLElement} el - Élément DOM
 * @param {Object} binding - Objet de liaison de la directive
 */
function mounted(el, binding) {
  // Analyser les modificateurs
  const modifiers = binding.modifiers || {}
  const value = binding.value

  // Déterminer si le focus doit être appliqué immédiatement ou conditionnellement
  let shouldFocus = true

  // Si une valeur est fournie et que ce n'est pas un nombre pour delay
  if (value !== undefined && value !== null && !modifiers.delay) {
    // Si la valeur est un booléen, l'utiliser comme condition
    if (typeof value === 'boolean') {
      shouldFocus = value
    }
    // Si c'est une fonction, l'exécuter pour obtenir la condition
    else if (typeof value === 'function') {
      shouldFocus = !!value()
    }
    // Si c'est une promesse, on va la résoudre plus tard
    else if (typeof value === 'object' && typeof value.then === 'function') {
      // Gérer la promesse plus tard
      shouldFocus = false // on va gérer plus tard
      value.then((result) => {
        if (result) {
          el._vFocusShouldFocus = true
          if (!el._vFocusApplied) {
            applyFocus(el, {
              select: modifiers.select || false,
              preventScroll: modifiers['prevent-scroll'] || modifiers['no-scroll'] || false,
              delay: getDelayValue(binding),
            }).then(() => {
              el._vFocusApplied = true
            })
          }
        }
      }).catch(() => {
        // Ignorer les erreurs de promesse
      })
      // On stocke la promesse pour une utilisation ultérieure
      el._vFocusPromise = value
    }
    // Si la valeur est un nombre, c'est un délai
  }

  // Gérer le délai via modificateur .delay="nombre" ou en utilisant binding.arg ?
  // La valeur peut être un nombre pour le délai si .delay est présent ou via la valeur elle-même

  // Si le modificateur .once est présent, on stocke le fait qu'on a déjà appliqué le focus
  if (modifiers.once) {
    el._vFocusOnce = true
  }

  // Appliquer le focus si la condition est vraie et que ce n'est pas un focus conditionnel en attente
  if (shouldFocus && !el._vFocusPromise) {
    const delay = getDelayValue(binding)
    applyFocus(el, {
      select: modifiers.select || false,
      preventScroll: modifiers['prevent-scroll'] || modifiers['no-scroll'] || false,
      delay,
    }).then(() => {
      el._vFocusApplied = true
    })
  }

  // Si on a .once, on s'assure que le focus ne sera réappliqué que si non appliqué
  if (modifiers.once && el._vFocusApplied) {
    // Déjà appliqué, on ne fera rien de plus
  }

  // Stocker les options pour l'update
  el._vFocusBinding = binding
  el._vFocusModifiers = modifiers
  el._vFocusShouldFocus = shouldFocus
}

/**
 * Hook updated : réapplique le focus si la condition change.
 * @param {HTMLElement} el - Élément DOM
 * @param {Object} binding - Objet de liaison de la directive
 */
function updated(el, binding) {
  // Si .once est présent et que le focus a déjà été appliqué, on ne refait rien
  if (binding.modifiers.once && el._vFocusApplied) return

  // Si la valeur n'a pas changé, on ne fait rien sauf si la condition est vraie et que le focus n'a pas été appliqué
  if (binding.value === el._vFocusPreviousValue) {
    // Si la valeur est vraie et que le focus n'a pas été appliqué, on l'applique
    if (binding.value && !el._vFocusApplied) {
      applyFocus(el, {
        select: binding.modifiers.select || false,
        preventScroll: binding.modifiers['prevent-scroll'] || binding.modifiers['no-scroll'] || false,
        delay: getDelayValue(binding),
      }).then(() => {
        el._vFocusApplied = true
      })
    }
    return
  }

  // Mémoriser l'ancienne valeur
  el._vFocusPreviousValue = binding.value

  // Évaluer la nouvelle condition
  let shouldFocus = false
  const value = binding.value

  if (typeof value === 'boolean') {
    shouldFocus = value
  } else if (typeof value === 'function') {
    shouldFocus = !!value()
  } else if (value !== undefined && value !== null && !binding.modifiers.delay) {
    // Toute valeur truthy
    shouldFocus = !!value
  }

  // Si on a un délai via modificateur .delay, c'est toujours actif
  if (binding.modifiers.delay) {
    // On peut avoir une condition booléenne dans la valeur pour déterminer si on focus
    // Ici on utilise la valeur comme condition
    if (typeof value === 'boolean') {
      shouldFocus = value
    }
  }

  if (shouldFocus && !el._vFocusApplied) {
    const delay = getDelayValue(binding)
    applyFocus(el, {
      select: binding.modifiers.select || false,
      preventScroll: binding.modifiers['prevent-scroll'] || binding.modifiers['no-scroll'] || false,
      delay,
    }).then(() => {
      el._vFocusApplied = true
    })
  } else if (!shouldFocus) {
    // Si la condition devient fausse, on peut permettre de refocuser plus tard
    el._vFocusApplied = false
  }

  // Stocker les options
  el._vFocusBinding = binding
}

/**
 * Hook unmounted : nettoyage.
 * @param {HTMLElement} el - Élément DOM
 */
function unmounted(el) {
  delete el._vFocusBinding
  delete el._vFocusModifiers
  delete el._vFocusShouldFocus
  delete el._vFocusApplied
  delete el._vFocusPreviousValue
  delete el._vFocusPromise
  delete el._vFocusOnce
}

// ==========================================================================
//  Fonctions utilitaires
// ==========================================================================

/**
 * Récupère la valeur du délai depuis le binding.
 * @param {Object} binding - Objet de liaison de la directive
 * @returns {number}
 */
function getDelayValue(binding) {
  const { value, modifiers } = binding
  // Si .delay est présent, on utilise la valeur comme délai (si c'est un nombre) ou une valeur par défaut
  if (modifiers.delay) {
    if (typeof value === 'number') return value
    if (typeof value === 'string' && !isNaN(Number(value))) return Number(value)
    return 150 // délai par défaut pour .delay
  }
  return 0
}

// ==========================================================================
//  Définition de la directive
// ==========================================================================

/**
 * Directive Vue pour gérer automatiquement le focus.
 * @type {import('vue').Directive}
 */
export const focus = {
  mounted,
  updated,
  unmounted,
}

// ==========================================================================
//  Plugin pour enregistrer la directive
// ==========================================================================

/**
 * Plugin pour enregistrer la directive focus dans une application Vue.
 * @param {import('vue').App} app - Instance Vue
 * @param {Object} options - Options (non utilisées)
 */
export function installFocus(app, options = {}) {
  app.directive('focus', focus)
  console.log('✅ Directive focus installée')
}

// ==========================================================================
//  Export par défaut (pour utilisation avec `app.use`)
// ==========================================================================

export default {
  install: installFocus,
  directive: focus,
}

// ==========================================================================
//  Notes
// ==========================================================================
//  - Cette directive est compatible avec Vue 3 et la Composition API.
//  - Elle gère les composants personnalisés qui exposent une méthode focus().
//  - Elle supporte le focus conditionnel, les délais, la sélection de texte,
//    et l'option de ne pas scroller vers l'élément.
//  - La directive émet un événement personnalisé 'focus-applied' sur l'élément
//    après que le focus a été appliqué.
//  - En cas d'absence d'élément focusable, un avertissement est émis (non bloquant).
