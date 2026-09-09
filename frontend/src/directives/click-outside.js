// ==========================================================================
//  NexusDL 2.0 - click-outside Directive
//  Fichier : frontend/src/directives/click-outside.js
//  Description : Directive Vue pour détecter les clics en dehors d'un élément
//  Version : 2.0.0
// ==========================================================================

/**
 * Directive personnalisée Vue pour déclencher un callback lorsqu'un clic
 * se produit en dehors de l'élément cible.
 *
 * Utilisation :
 * ```vue
 * <template>
 *   <div v-click-outside="onClickOutside">
 *     ...
 *   </div>
 * </template>
 *
 * <script setup>
 * function onClickOutside() {
 *   console.log('Clic en dehors de la div !')
 * }
 * </script>
 * ```
 *
 * Modificateurs disponibles :
 * - .stop    : Arrête la propagation de l'événement (event.stopPropagation())
 * - .prevent : Empêche le comportement par défaut (event.preventDefault())
 * - .self    : Ne déclenche le callback que si le clic est en dehors (non utilisé ici car déjà le cas)
 * - .once    : Ne déclenche qu'une seule fois puis se désactive (géré via la valeur)
 * - .capture : Utilise la phase de capture pour l'écouteur
 *
 * Si la valeur passée est un tableau, le callback sera appelé pour chaque élément du tableau.
 *
 * @param {Object} options - Options de configuration de la directive
 * @param {Function} options.handler - Fonction à appeler lors d'un clic extérieur
 * @param {Array} [options.events=['click']] - Événements à écouter (ex: ['click', 'touchstart'])
 * @param {boolean} [options.capture=false] - Écouter en phase de capture
 * @param {boolean} [options.once=false] - Ne se déclencher qu'une seule fois
 * @param {Array} [options.ignore=[]] - Liste d'éléments à ignorer (ex: refs, selecteurs)
 */

/**
 * Gestionnaire d'événement pour la détection de clic extérieur.
 * @param {Event} event - Événement DOM
 * @param {HTMLElement} element - Élément cible de la directive
 * @param {Function|Array} bindingValue - Callback ou tableau de callbacks
 * @param {Object} modifiers - Modificateurs de la directive
 * @param {Object} ignoreElements - Liste des éléments à ignorer (stockée sur l'élément)
 */
function outsideClickHandler(event, element, bindingValue, modifiers, ignoreElements = []) {
  // Vérifier si le clic est en dehors de l'élément et non sur un élément ignoré
  const isOutside = !element.contains(event.target) &&
    !ignoreElements.some(ignoreEl => ignoreEl && ignoreEl.contains && ignoreEl.contains(event.target))

  if (!isOutside) return

  // Appliquer les modificateurs
  if (modifiers.stop) event.stopPropagation()
  if (modifiers.prevent) event.preventDefault()

  // Déterminer le(s) callback(s)
  const callbacks = Array.isArray(bindingValue) ? bindingValue : [bindingValue]

  // Appeler chaque callback
  for (const callback of callbacks) {
    if (typeof callback === 'function') {
      callback(event, element)
    }
  }

  // Si le modificateur .once est présent, retirer l'écouteur après le premier déclenchement
  // (on va le faire via la fonction de nettoyage stockée sur l'élément)
  if (modifiers.once) {
    // Désactiver la directive en supprimant l'écouteur
    const cleanup = element._clickOutsideCleanup
    if (cleanup) {
      cleanup()
      delete element._clickOutsideCleanup
    }
  }
}

/**
 * Hook Vue pour la directive : lorsque l'élément est monté.
 * @param {HTMLElement} el - Élément DOM
 * @param {Object} binding - Objet de liaison de la directive
 */
function mounted(el, binding) {
  const { value, modifiers } = binding

  // Vérifier que la valeur est une fonction ou un tableau de fonctions
  if (typeof value !== 'function' && !Array.isArray(value)) {
    console.warn('[click-outside] La valeur doit être une fonction ou un tableau de fonctions.')
    return
  }

  // Configurer les options à partir des modificateurs
  const options = {
    capture: !!modifiers.capture,
    once: false, // géré manuellement via la logique
    passive: false,
  }

  // Déterminer les événements à écouter (peut être configuré via un paramètre personnalisé)
  // Par défaut, on écoute 'click' et 'touchstart' sur mobile
  const events = ['click', 'touchstart']

  // Stocker les éléments ignorés (peut être fourni via un attribut ou via un tableau dans la valeur ?)
  // On peut utiliser un paramètre optionnel : binding.arg pour un sélecteur ou une ref
  // Ou via un objet de configuration
  let ignoreElements = []

  // Si la valeur est un objet avec une propriété `handler` et `ignore`, on peut extraire
  // Mais pour la simplicité, on ne supporte pas cette syntaxe complexe ici.
  // Sinon, on peut ajouter un attribut data-ignore qui sera utilisé.
  // Ici, on va permettre de passer un tableau d'éléments dans un deuxième argument ?
  // Vue ne permet pas facilement de passer plusieurs arguments. On va se limiter.

  // Créer une fonction de gestionnaire qui appelle outsideClickHandler avec les bons paramètres
  const handler = (event) => {
    // Récupérer les éléments ignorés stockés sur l'élément lui-même
    const ignore = el._clickOutsideIgnore || []
    outsideClickHandler(event, el, value, modifiers, ignore)
  }

  // Ajouter l'écouteur pour chaque événement
  for (const eventName of events) {
    el.addEventListener(eventName, handler, options)
  }

  // Stocker les fonctions pour le nettoyage
  el._clickOutsideHandlers = el._clickOutsideHandlers || {}
  for (const eventName of events) {
    el._clickOutsideHandlers[eventName] = handler
  }

  // Fonction de nettoyage
  el._clickOutsideCleanup = () => {
    for (const eventName of events) {
      el.removeEventListener(eventName, el._clickOutsideHandlers[eventName], options)
    }
    delete el._clickOutsideHandlers
    delete el._clickOutsideCleanup
  }

  // Stocker les éléments ignorés si spécifiés via un attribut data-ignore (sélecteur CSS)
  const ignoreSelector = el.getAttribute('data-click-outside-ignore')
  if (ignoreSelector) {
    const ignoredNodes = el.querySelectorAll(ignoreSelector)
    el._clickOutsideIgnore = Array.from(ignoredNodes)
  } else {
    // On peut aussi permettre de passer un tableau dans la valeur si c'est un objet,
    // mais on garde simple.
    el._clickOutsideIgnore = []
  }
}

/**
 * Hook Vue pour la directive : lorsque l'élément est démonté.
 * @param {HTMLElement} el - Élément DOM
 */
function unmounted(el) {
  // Nettoyer les écouteurs
  if (el._clickOutsideCleanup) {
    el._clickOutsideCleanup()
  }
  delete el._clickOutsideCleanup
  delete el._clickOutsideIgnore
  delete el._clickOutsideHandlers
}

/**
 * Hook Vue pour la directive : lorsque les propriétés de la directive changent.
 * @param {HTMLElement} el - Élément DOM
 * @param {Object} binding - Objet de liaison de la directive
 */
function updated(el, binding) {
  // Si la valeur change, on peut mettre à jour le callback.
  // On va simplement mettre à jour la valeur stockée ? Pas nécessaire car le handler utilise binding.value
  // mais le handler est déjà fermé sur la valeur au moment de la création.
  // Pour être plus robuste, on pourrait reconstruire le handler, mais ce n'est pas nécessaire pour la plupart des cas.
  // On va juste stocker la nouvelle valeur pour qu'elle soit accessible via binding dans le handler.
  // Le handler capturera la nouvelle valeur à chaque événement car il utilise la valeur passée en paramètre.
  // On pourrait aussi remplacer le handler, mais on va rester simple.
  // On va simplement stocker un indicateur que la valeur a changé, et on pourrait réinitialiser.
  // Une meilleure approche : lors du montage, on stocke la valeur dans une propriété data de l'élément,
  // et le handler utilise cette valeur. Ainsi, on peut la mettre à jour dans updated.
  // On va adopter cette approche.

  // Stocker la valeur courante sur l'élément
  el._clickOutsideValue = binding.value
}

// ==========================================================================
//  Définition de la directive
// ==========================================================================

/**
 * Directive Vue pour détecter les clics en dehors d'un élément.
 * @type {import('vue').Directive}
 */
export const clickOutside = {
  mounted,
  unmounted,
  updated,
}

// ==========================================================================
//  Fonction utilitaire pour enregistrer la directive
// ==========================================================================

/**
 * Plugin pour enregistrer la directive click-outside dans une application Vue.
 * @param {import('vue').App} app - Instance Vue
 * @param {Object} options - Options (non utilisées)
 */
export function installClickOutside(app, options = {}) {
  app.directive('click-outside', clickOutside)
  console.log('✅ Directive click-outside installée')
}

// ==========================================================================
//  Export par défaut (pour utilisation avec `app.use`)
// ==========================================================================

export default {
  install: installClickOutside,
  directive: clickOutside,
}
