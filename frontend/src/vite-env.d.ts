// ==========================================================================
//  NexusDL 2.0 - TypeScript Environment Declarations
//  Fichier : frontend/src/vite-env.d.ts
//  Description : Déclarations de types TypeScript pour Vite, les variables
//                d'environnement et les modules Vue.
//  Version : 2.0.0
// ==========================================================================

/// <reference types="vite/client" />
/// <reference types="vue/dist/vue.d.ts" />

// ==========================================================================
//  Déclaration des modules Vue
// ==========================================================================

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// ==========================================================================
//  Déclaration des fichiers statiques
// ==========================================================================

// --- Images ---
declare module '*.png' {
  const src: string
  export default src
}

declare module '*.jpg' {
  const src: string
  export default src
}

declare module '*.jpeg' {
  const src: string
  export default src
}

declare module '*.gif' {
  const src: string
  export default src
}

declare module '*.svg' {
  const src: string
  export default src
}

declare module '*.webp' {
  const src: string
  export default src
}

declare module '*.avif' {
  const src: string
  export default src
}

declare module '*.ico' {
  const src: string
  export default src
}

declare module '*.bmp' {
  const src: string
  export default src
}

// --- Fonts ---
declare module '*.woff' {
  const src: string
  export default src
}

declare module '*.woff2' {
  const src: string
  export default src
}

declare module '*.ttf' {
  const src: string
  export default src
}

declare module '*.otf' {
  const src: string
  export default src
}

declare module '*.eot' {
  const src: string
  export default src
}

// --- Styles ---
declare module '*.css' {
  const css: string
  export default css
}

declare module '*.scss' {
  const css: string
  export default css
}

declare module '*.sass' {
  const css: string
  export default css
}

declare module '*.less' {
  const css: string
  export default css
}

// --- Données ---
declare module '*.json' {
  const value: any
  export default value
}

declare module '*.yaml' {
  const value: any
  export default value
}

declare module '*.yml' {
  const value: any
  export default value
}

// --- Documents ---
declare module '*.txt' {
  const content: string
  export default content
}

declare module '*.md' {
  const content: string
  export default content
}

// ==========================================================================
//  Variables d'environnement Vite (import.meta.env)
// ==========================================================================

interface ImportMetaEnv {
  // ----------------------------------------------------------------------
  //  Configuration de l'application
  // ----------------------------------------------------------------------
  /** Version de l'application */
  readonly VITE_APP_VERSION: string

  /** Nom de l'application */
  readonly VITE_APP_NAME?: string

  /** Description de l'application */
  readonly VITE_APP_DESCRIPTION?: string

  /** Date de build (ISO 8601) */
  readonly VITE_BUILD_DATE?: string

  // ----------------------------------------------------------------------
  //  API Backend
  // ----------------------------------------------------------------------
  /** URL de base de l'API (côté client) */
  readonly VITE_API_BASE: string

  /** URL complète du backend (pour proxy de dev) */
  readonly VITE_API_BACKEND_URL?: string

  /** URL de base WebSocket */
  readonly VITE_WS_BASE?: string

  // ----------------------------------------------------------------------
  //  Environnement
  // ----------------------------------------------------------------------
  /** Mode de l'application ('development', 'production', 'test') */
  readonly MODE: string

  /** Est-ce le build de production ? */
  readonly PROD: boolean

  /** Est-ce le build de développement ? */
  readonly DEV: boolean

  /** Est-ce un build SSR ? */
  readonly SSR: boolean

  // ----------------------------------------------------------------------
  //  Fonctionnalités optionnelles
  // ----------------------------------------------------------------------
  /** Activer les fonctionnalités NSFW */
  readonly VITE_ENABLE_NSFW?: string

  /** Activer les analytics */
  readonly VITE_ENABLE_ANALYTICS?: string

  /** ID Google Analytics (optionnel) */
  readonly VITE_GA_ID?: string

  /** URL de l'API Sentry (optionnel) */
  readonly VITE_SENTRY_DSN?: string

  /** Clé d'API (optionnel) */
  readonly VITE_API_KEY?: string

  // ----------------------------------------------------------------------
  //  Playwright / Browser Automation (backend-side, mais exposé pour info)
  // ----------------------------------------------------------------------
  /** Chemin des navigateurs Playwright */
  readonly VITE_PLAYWRIGHT_BROWSERS_PATH?: string

  // ----------------------------------------------------------------------
  //  Autres variables personnalisées
  // ----------------------------------------------------------------------
  /** N'importe quelle autre variable VITE_* */
  readonly [key: `VITE_${string}`]: string | boolean | undefined
}

interface ImportMeta {
  readonly env: ImportMetaEnv

  // ----------------------------------------------------------------------
  //  Helpers Vite
  // ----------------------------------------------------------------------
  readonly hot?: {
    accept: (callback?: (module: any) => void) => void
    acceptExports: (deps: string | string[], callback?: (module: any) => void) => void
    dispose: (callback: (data: any) => void) => void
    prune: (callback: (data: any) => void) => void
    invalidate: () => void
    on: (event: string, callback: (...args: any[]) => void) => void
    off: (event: string, callback: (...args: any[]) => void) => void
    send: (event: string, data?: any) => void
    data: any
  }

  readonly glob: <T = unknown>(
    pattern: string | string[],
    options?: {
      eager?: boolean
      import?: string
      query?: string | Record<string, string | number | boolean>
      as?: string
    }
  ) => Record<string, T>

  readonly globEager: <T = unknown>(
    pattern: string | string[]
  ) => Record<string, T>
}

// ==========================================================================
//  Déclaration des constantes globales (via define dans vite.config.js)
// ==========================================================================

declare const __APP_VERSION__: string
declare const __BUILD_DATE__: string
declare const __DEV__: boolean
declare const __PROD__: boolean

// ==========================================================================
//  Déclaration des types pour les librairies externes
// ==========================================================================

// --- dayjs ---
declare module 'dayjs/plugin/relativeTime' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/duration' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/localizedFormat' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/customParseFormat' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/utc' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/timezone' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/locale/fr' {
  const locale: any
  export default locale
}

// ==========================================================================
//  Types globaux pour l'application NexusDL
// ==========================================================================

// --- Type pour un élément de la bibliothèque ---
interface NexusLibraryItem {
  id: string
  title: string
  filename: string
  file_path: string
  size_bytes: number
  size_formatted?: string
  created_at: string
  updated_at: string
  last_read?: string | null
  read_count: number
  is_favorite: boolean
  rating: number
  metadata?: {
    title?: string
    author?: string
    artist?: string
    series?: string
    genre?: string
    description?: string
    volume?: string
    chapters?: number
    pages?: number
    year?: number
    language?: string
    publisher?: string
  } | null
  tags?: string[]
  cover_path?: string | null
}

// --- Type pour un provider ---
interface NexusProvider {
  id: string
  name: string
  base_url: string
  enabled: boolean
  nsfw: boolean
  languages: string[]
  version: string
  description: string
  priority: number
  last_used?: string | null
}

// --- Type pour un job de téléchargement ---
interface NexusJob {
  id: string
  title: string
  url: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'waiting'
  progress: number
  total_chapters: number
  done_chapters: number
  current_chapter: string
  logs: Array<{
    timestamp: string
    level: string
    message: string
  }>
  errors: Array<{
    timestamp: string
    message: string
  }>
  created_at: string
  updated_at: string
  started_at?: string | null
  completed_at?: string | null
  cancelled_at?: string | null
  provider_id?: string | null
  result_path?: string | null
  result_size?: number | null
}

// --- Type pour un chapitre ---
interface NexusChapter {
  id: string
  title: string
  number: number
  url: string
  pages?: number
  release_date?: string
  language?: string
  is_available: boolean
  is_read?: boolean
}

// --- Type pour une analyse ---
interface NexusAnalysisResult {
  title: string
  url: string
  provider_id: string
  chapters: NexusChapter[]
  author?: string
  description?: string
  cover_url?: string
  genre?: string[]
  status?: string
  year?: number | null
  language?: string
  nsfw: boolean
  total_chapters: number
}

// --- Type pour un utilisateur ---
interface NexusUser {
  id: number
  username: string
  email: string
  full_name?: string
  role: 'admin' | 'user' | 'guest'
  status: 'active' | 'inactive' | 'banned' | 'pending'
  avatar_url?: string | null
  created_at: string
  updated_at: string
  last_login?: string | null
}

// --- Type pour une notification ---
interface NexusNotification {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info' | 'system'
  icon?: string
  duration: number
  read: boolean
  dismissed: boolean
  created_at: string
  action?: string | null
  onAction?: ((notif: NexusNotification) => void) | null
  onClose?: ((notif: NexusNotification) => void) | null
  meta?: Record<string, any> | null
}

// ==========================================================================
//  Déclaration du module global pour l'application
// ==========================================================================

declare global {
  interface Window {
    /** Fonction utilitaire pour masquer le loader initial */
    __nexusHideLoader?: () => void

    /** Loader initial de l'application */
    __nexusLoader?: {
      hide: (remove?: boolean) => void
      progress: (percent: number) => void
      setText: (text: string) => void
    }

    /** Client API exposé globalement (pour debugging) */
    __nexusApi?: any

    /** Version de l'application */
    __nexusVersion?: string
  }
}

// ==========================================================================
//  Export pour utilisation éventuelle dans les modules
// ==========================================================================

export {}
