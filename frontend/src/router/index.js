// ==========================================================================
//  NexusDL 2.0 - Router Configuration
//  Fichier : frontend/src/router/index.js
//  Description : Configuration complète du routeur Vue.js 4
//  Version : 2.0.0
// ==========================================================================

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { useToast } from '@/composables/useToast'

// ==========================================================================
//  Définition des routes
// ==========================================================================

const routes = [
  // ========================================================================
  //  Routes publiques (sans authentification)
  // ========================================================================
  {
    path: '/',
    name: 'home',
    redirect: '/search',
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      title: 'Connexion',
      layout: 'auth',
      requiresAuth: false,
      public: true,
    },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: {
      title: 'Inscription',
      layout: 'auth',
      requiresAuth: false,
      public: true,
    },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('@/views/ForgotPasswordView.vue'),
    meta: {
      title: 'Mot de passe oublié',
      layout: 'auth',
      requiresAuth: false,
      public: true,
    },
  },
  {
    path: '/reset-password/:token',
    name: 'reset-password',
    component: () => import('@/views/ResetPasswordView.vue'),
    meta: {
      title: 'Réinitialisation du mot de passe',
      layout: 'auth',
      requiresAuth: false,
      public: true,
    },
  },

  // ========================================================================
  //  Routes principales (layout app - authentifiées)
  // ========================================================================
  {
    path: '/search',
    name: 'search',
    component: () => import('@/views/SearchView.vue'),
    meta: {
      title: 'Recherche',
      layout: 'app',
      requiresAuth: false, // Les utilisateurs non connectés peuvent aussi utiliser la recherche
      icon: '🔍',
      tab: 'search',
    },
  },
  {
    path: '/library',
    name: 'library',
    component: () => import('@/views/LibraryView.vue'),
    meta: {
      title: 'Bibliothèque',
      layout: 'app',
      requiresAuth: false,
      icon: '📚',
      tab: 'library',
    },
  },
  {
    path: '/library/:id',
    name: 'library-detail',
    component: () => import('@/views/LibraryDetailView.vue'),
    meta: {
      title: 'Détail',
      layout: 'app',
      requiresAuth: false,
    },
  },
  {
    path: '/queue',
    name: 'queue',
    component: () => import('@/views/QueueView.vue'),
    meta: {
      title: 'File d\'attente',
      layout: 'app',
      requiresAuth: false,
      icon: '⏳',
      tab: 'queue',
    },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: {
      title: 'Paramètres',
      layout: 'app',
      requiresAuth: true,
      icon: '⚙️',
      tab: 'settings',
    },
  },

  // ========================================================================
  //  Routes administrateur
  // ========================================================================
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/AdminView.vue'),
    meta: {
      title: 'Administration',
      layout: 'app',
      requiresAuth: true,
      requiresAdmin: true,
      icon: '🛠️',
      tab: 'admin',
    },
  },
  {
    path: '/admin/providers',
    name: 'admin-providers',
    component: () => import('@/views/admin/ProvidersView.vue'),
    meta: {
      title: 'Providers',
      layout: 'app',
      requiresAuth: true,
      requiresAdmin: true,
    },
  },
  {
    path: '/admin/logs',
    name: 'admin-logs',
    component: () => import('@/views/admin/LogsView.vue'),
    meta: {
      title: 'Logs',
      layout: 'app',
      requiresAuth: true,
      requiresAdmin: true,
    },
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: () => import('@/views/admin/UsersView.vue'),
    meta: {
      title: 'Utilisateurs',
      layout: 'app',
      requiresAuth: true,
      requiresAdmin: true,
    },
  },
  {
    path: '/admin/system',
    name: 'admin-system',
    component: () => import('@/views/admin/SystemView.vue'),
    meta: {
      title: 'Système',
      layout: 'app',
      requiresAuth: true,
      requiresAdmin: true,
    },
  },

  // ========================================================================
  //  Route de lecture (viewer)
  // ========================================================================
  {
    path: '/reader/:jobId/:chapterId?',
    name: 'reader',
    component: () => import('@/views/ReaderView.vue'),
    meta: {
      title: 'Lecture',
      layout: 'reader',
      requiresAuth: false,
    },
  },

  // ========================================================================
  //  Routes d'erreur et redirection
  // ========================================================================
  {
    path: '/404',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: {
      title: 'Page non trouvée',
      layout: 'auth',
      requiresAuth: false,
      public: true,
    },
  },
  {
    path: '/forbidden',
    name: 'forbidden',
    component: () => import('@/views/ForbiddenView.vue'),
    meta: {
      title: 'Accès interdit',
      layout: 'auth',
      requiresAuth: false,
      public: true,
    },
  },
  {
    // Route catch-all pour rediriger vers 404
    path: '/:pathMatch(.*)*',
    redirect: '/404',
  },
]

// ==========================================================================
//  Création du routeur
// ==========================================================================

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Retourne à la position sauvegardée si elle existe (navigation avant/arrière)
    if (savedPosition) {
      return savedPosition
    }
    // Sinon, retourne en haut de la page
    return { top: 0, behavior: 'smooth' }
  },
  // Lien actif
  linkActiveClass: 'router-link-active',
  linkExactActiveClass: 'router-link-exact-active',
})

// ==========================================================================
//  Metadonnées et titres
// ==========================================================================

const DEFAULT_TITLE = 'NexusDL 2.0'
const TITLE_SUFFIX = ' | NexusDL'

/**
 * Définit le titre de la page à partir des meta de la route.
 * @param {import('vue-router').RouteLocationNormalized} to - Route de destination
 */
function setPageTitle(to) {
  let title = DEFAULT_TITLE
  if (to.meta?.title) {
    title = `${to.meta.title}${TITLE_SUFFIX}`
  }
  document.title = title
  // Mettre à jour la balise meta description si présente
  const description = to.meta?.description || 'NexusDL - Téléchargement de scans'
  const metaDesc = document.querySelector('meta[name="description"]')
  if (metaDesc) {
    metaDesc.setAttribute('content', description)
  }
}

// ==========================================================================
//  Guards de navigation
// ==========================================================================

/**
 * Vérifie si l'utilisateur est authentifié.
 * @param {import('vue-router').RouteLocationNormalized} to - Route de destination
 * @param {import('vue-router').RouteLocationNormalized} from - Route source
 * @param {Function} next - Fonction de navigation
 * @param {Object} authStore - Store d'authentification
 * @param {Object} appStore - Store applicatif
 * @param {Object} toast - Fonction de notification
 */
async function checkAuth(to, from, next, authStore, appStore, toast) {
  // Si la route ne nécessite pas d'authentification
  if (!to.meta.requiresAuth) {
    // Si l'utilisateur est déjà connecté et essaie d'accéder à /login ou /register
    if (authStore.isAuthenticated && (to.name === 'login' || to.name === 'register')) {
      next({ name: 'search' })
      return
    }
    next()
    return
  }

  // La route nécessite une authentification
  if (!authStore.isAuthenticated) {
    // L'utilisateur n'est pas connecté, rediriger vers login
    toast?.warning('Veuillez vous connecter pour accéder à cette page.', '🔐')
    next({
      name: 'login',
      query: { redirect: to.fullPath },
    })
    return
  }

  // Vérifier si le token est expiré (via la méthode du store)
  if (authStore.isTokenExpired && authStore.isTokenExpired()) {
    try {
      // Tentative de refresh automatique
      await authStore.refresh()
      // Refresh réussi, continuer
      next()
      return
    } catch (_) {
      // Refresh échoué, déconnecter et rediriger
      await authStore.logout()
      toast?.warning('Session expirée, veuillez vous reconnecter.', '🔐')
      next({
        name: 'login',
        query: { redirect: to.fullPath },
      })
      return
    }
  }

  // Vérifier le rôle administrateur si nécessaire
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    toast?.error('Accès réservé aux administrateurs.', '🚫')
    next({ name: 'forbidden' })
    return
  }

  // L'utilisateur est authentifié et autorisé
  next()
}

/**
 * Guard global de navigation.
 */
router.beforeEach(async (to, from, next) => {
  // 1. Récupérer les stores
  let authStore, appStore, toast
  try {
    authStore = useAuthStore()
    appStore = useAppStore()
    toast = useToast()
  } catch (_) {
    // En mode test ou sans stores, on continue quand même
    next()
    return
  }

  // 2. Mettre à jour le titre de la page
  setPageTitle(to)

  // 3. Enregistrer la route précédente dans le store (pour le retour)
  if (from.name && from.name !== to.name) {
    appStore.setPreviousRoute(from)
  }

  // 4. Vérifier l'authentification
  await checkAuth(to, from, next, authStore, appStore, toast)
})

/**
 * Guard après chaque navigation (pour les analytics, logs, etc.)
 */
router.afterEach((to, from) => {
  // Log en développement
  if (import.meta.env.DEV) {
    console.log(`🧭 Navigation: ${from.path} -> ${to.path}`)
  }

  // Mettre à jour l'onglet actif dans le store
  try {
    const appStore = useAppStore()
    if (to.meta?.tab) {
      appStore.setActiveTab(to.meta.tab)
    }
  } catch (_) {
    // Ignorer
  }

  // Si on arrive sur une route avec un hash, scroller vers l'élément
  if (to.hash) {
    setTimeout(() => {
      const element = document.querySelector(to.hash)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' })
      }
    }, 100)
  }

  // Gérer le focus sur l'élément principal pour l'accessibilité
  const main = document.querySelector('main')
  if (main && !document.activeElement?.closest?.('main')) {
    // Ne pas forcer le focus si un champ est déjà actif
    if (!document.activeElement || document.activeElement.tagName !== 'INPUT') {
      main.setAttribute('tabindex', '-1')
      // main.focus() // Désactivé car peut causer des problèmes de scroll
    }
  }
})

// ==========================================================================
//  Gestion des erreurs de navigation
// ==========================================================================

router.onError((error) => {
  console.error('Erreur de navigation:', error)
  // Si l'erreur est une erreur de chargement de composant (lazy loading)
  if (error.message?.includes('Failed to fetch') || error.message?.includes('Loading chunk')) {
    // Tenter de recharger la page
    if (confirm('Une erreur est survenue lors du chargement de la page. Voulez-vous recharger ?')) {
      window.location.reload()
    }
  }
})

// ==========================================================================
//  Fonctions utilitaires exportées
// ==========================================================================

/**
 * Vérifie si une route nécessite une authentification.
 * @param {import('vue-router').RouteLocationNormalized} route - Route à vérifier
 * @returns {boolean}
 */
export function requiresAuth(route) {
  return route.meta?.requiresAuth === true
}

/**
 * Vérifie si une route nécessite des privilèges administrateur.
 * @param {import('vue-router').RouteLocationNormalized} route - Route à vérifier
 * @returns {boolean}
 */
export function requiresAdmin(route) {
  return route.meta?.requiresAdmin === true
}

/**
 * Récupère le layout à utiliser pour une route.
 * @param {import('vue-router').RouteLocationNormalized} route - Route cible
 * @returns {string} - Nom du layout ('app', 'auth', 'reader')
 */
export function getLayout(route) {
  return route.meta?.layout || 'app'
}

/**
 * Récupère le titre d'une route.
 * @param {import('vue-router').RouteLocationNormalized} route - Route cible
 * @returns {string} - Titre de la page
 */
export function getTitle(route) {
  return route.meta?.title || DEFAULT_TITLE
}

// ==========================================================================
//  Export du routeur
// ==========================================================================

export default router

// ==========================================================================
//  Notes
// ==========================================================================
//  - Les routes utilisent le lazy loading pour réduire la taille initiale du bundle.
//  - Les guards gèrent l'authentification et les rôles.
//  - Le scrollBehavior assure une navigation fluide.
//  - Les meta-champs permettent de configurer facilement le comportement des routes.
//  - Le titre de la page est mis à jour automatiquement.
//  - Les erreurs de chargement sont capturées avec une option de rechargement.
