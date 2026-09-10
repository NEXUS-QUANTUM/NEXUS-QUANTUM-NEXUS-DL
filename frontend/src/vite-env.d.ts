// ==========================================================================
//  NexusDL 2.0 - Vite Environment TypeScript Declarations
//  Fichier : frontend/src/vite-env.d.ts
//  Description : Déclarations TypeScript complètes pour Vite, les variables
//                d'environnement, les modules Vue, les assets statiques,
//                et les types globaux de l'application NexusDL.
//  Version : 2.0.0
//  Licence : GNU GPL v3.0
// ==========================================================================

/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />
/// <reference types="vue/dist/vue.d.ts" />

// ==========================================================================
//  SECTION 1 — DÉCLARATION DES MODULES VUE
// ==========================================================================

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// ==========================================================================
//  SECTION 2 — DÉCLARATION DES FICHIERS STATIQUES
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
  import type { DefineComponent } from 'vue'
  const src: string
  export default src
  // Alternative : export par défaut comme composant Vue
  // export const VueComponent: DefineComponent
}

declare module '*.svg?raw' {
  const content: string
  export default content
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

declare module '*.tiff' {
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

declare module '*.styl' {
  const css: string
  export default css
}

// --- Styles modules ---
declare module '*.module.css' {
  const classes: { readonly [key: string]: string }
  export default classes
}

declare module '*.module.scss' {
  const classes: { readonly [key: string]: string }
  export default classes
}

declare module '*.module.sass' {
  const classes: { readonly [key: string]: string }
  export default classes
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

declare module '*.toml' {
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

declare module '*.md?raw' {
  const content: string
  export default content
}

// --- Workers ---
declare module '*?worker' {
  const workerConstructor: {
    new (): Worker
  }
  export default workerConstructor
}

declare module '*?worker&inline' {
  const workerConstructor: {
    new (): Worker
  }
  export default workerConstructor
}

// --- URL ---
declare module '*?url' {
  const src: string
  export default src
}

// --- Raw ---
declare module '*?raw' {
  const content: string
  export default content
}

// ==========================================================================
//  SECTION 3 — VARIABLES D'ENVIRONNEMENT VITE (import.meta.env)
// ==========================================================================

interface ImportMetaEnv {
  // ----------------------------------------------------------------------
  //  Configuration de l'application
  // ----------------------------------------------------------------------
  /** Version de l'application (ex: "2.0.0") */
  readonly VITE_APP_VERSION: string

  /** Nom de l'application */
  readonly VITE_APP_NAME?: string

  /** Description de l'application */
  readonly VITE_APP_DESCRIPTION?: string

  /** Date de build au format ISO 8601 */
  readonly VITE_BUILD_DATE?: string

  // ----------------------------------------------------------------------
  //  API Backend
  // ----------------------------------------------------------------------
  /** URL de base de l'API côté client (ex: "/api") */
  readonly VITE_API_BASE: string

  /** URL complète du backend (utilisée pour le proxy de dev) */
  readonly VITE_API_BACKEND_URL?: string

  /** URL de base WebSocket (ex: "ws://localhost:8000/api/ws") */
  readonly VITE_WS_BASE?: string

  /** Timeout par défaut des requêtes API (ms) */
  readonly VITE_API_TIMEOUT?: string

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

  /** Nom de base (URL de base de l'app) */
  readonly BASE_URL: string

  // ----------------------------------------------------------------------
  //  Fonctionnalités optionnelles
  // ----------------------------------------------------------------------
  /** Activer les fonctionnalités NSFW */
  readonly VITE_ENABLE_NSFW?: string

  /** Activer les analytics */
  readonly VITE_ENABLE_ANALYTICS?: string

  /** Afficher les identifiants de démo */
  readonly VITE_SHOW_DEMO?: string

  /** Activer les DevTools Vue */
  readonly VITE_ENABLE_DEVTOOLS?: string

  /** Activer le debug des WebSockets */
  readonly VITE_DEBUG_WS?: string

  /** Activer le mode PWA */
  readonly VITE_ENABLE_PWA?: string

  // ----------------------------------------------------------------------
  //  Analytics & Monitoring
  // ----------------------------------------------------------------------
  /** ID Google Analytics (optionnel) */
  readonly VITE_GA_ID?: string

  /** URL de l'API Sentry (optionnel) */
  readonly VITE_SENTRY_DSN?: string

  /** Nom de l'environnement Sentry */
  readonly VITE_SENTRY_ENV?: string

  /** URL de l'API Umami (optionnel) */
  readonly VITE_UMAMI_URL?: string

  /** ID du site Umami */
  readonly VITE_UMAMI_SITE_ID?: string

  /** Clé d'API publique (optionnel) */
  readonly VITE_API_KEY?: string

  // ----------------------------------------------------------------------
  //  Playwright / Browser Automation (backend)
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
    acceptExports: (
      deps: string | string[],
      callback?: (module: any) => void
    ) => void
    dispose: (callback: (data: any) => void) => void
    prune: (callback: (data: any) => void) => void
    invalidate: () => void
    on: (event: string, callback: (...args: any[]) => void) => void
    off: (event: string, callback: (...args: any[]) => void) => void
    send: (event: string, data?: any) => void
    data: any
    decline: () => void
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
//  SECTION 4 — DÉCLARATION DES CONSTANTES GLOBALES (define dans vite.config.js)
// ==========================================================================

declare const __APP_VERSION__: string
declare const __BUILD_DATE__: string
declare const __DEV__: boolean
declare const __PROD__: boolean
declare const __TEST__: boolean

// ==========================================================================
//  SECTION 5 — DÉCLARATION DES TYPES POUR LES LIBRAIRIES EXTERNES
// ==========================================================================

// --- Day.js plugins ---
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

declare module 'dayjs/plugin/isBetween' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/weekday' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/isoWeek' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/quarterOfYear' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/toObject' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/arraySupport' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/objectSupport' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/advancedFormat' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/badMutable' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/plugin/calendar' {
  import { PluginFunc } from 'dayjs'
  const plugin: PluginFunc
  export default plugin
}

declare module 'dayjs/locale/fr' {
  const locale: any
  export default locale
}

declare module 'dayjs/locale/*' {
  const locale: any
  export default locale
}

// --- Vite plugins ---
declare module 'vite-plugin-compression' {
  import { Plugin } from 'vite'
  interface CompressionOptions {
    algorithm?: string
    ext?: string
    threshold?: number
    deleteOriginalAssets?: boolean
    disable?: boolean
    verbose?: boolean
  }
  export default function compression(options?: CompressionOptions): Plugin
}

// --- PWA types (compléments) ---
declare module 'virtual:pwa-register' {
  export interface RegisterSWOptions {
    immediate?: boolean
    onNeedRefresh?: () => void
    onOfflineReady?: () => void
    onRegistered?: (registration: ServiceWorkerRegistration | undefined) => void
    onRegisterError?: (error: any) => void
  }
  export function registerSW(
    options?: RegisterSWOptions
  ): (reloadPage?: boolean) => Promise<void>
}

declare module 'virtual:pwa-register/vue' {
  import { Ref } from 'vue'
  export interface RegisterSWOptions {
    immediate?: boolean
    onNeedRefresh?: () => void
    onOfflineReady?: () => void
    onRegistered?: (registration: ServiceWorkerRegistration | undefined) => void
    onRegisterError?: (error: any) => void
  }
  export function useRegisterSW(options?: RegisterSWOptions): {
    needRefresh: Ref<boolean>
    offlineReady: Ref<boolean>
    updateServiceWorker: (reloadPage?: boolean) => Promise<void>
  }
}

// ==========================================================================
//  SECTION 6 — TYPES GLOBAUX POUR NEXUSDL
// ==========================================================================

/**
 * Élément de la bibliothèque NexusDL
 */
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
  metadata?: NexusLibraryMetadata | null
  tags?: string[]
  cover_path?: string | null
}

/**
 * Métadonnées d'un élément de bibliothèque
 */
interface NexusLibraryMetadata {
  title?: string
  author?: string
  artist?: string
  series?: string
  genre?: string | string[]
  description?: string
  volume?: string
  chapters?: number
  pages?: number
  year?: number
  language?: string
  publisher?: string
}

/**
 * Provider de site de scan
 */
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

/**
 * Job de téléchargement
 */
interface NexusJob {
  id: string
  title: string
  url: string
  status: NexusJobStatus
  progress: number
  total_chapters: number
  done_chapters: number
  total_pages?: number
  done_pages?: number
  current_chapter: string
  logs: NexusJobLog[]
  errors: NexusJobError[]
  created_at: string
  updated_at: string
  started_at?: string | null
  completed_at?: string | null
  cancelled_at?: string | null
  provider_id?: string | null
  result_path?: string | null
  result_size?: number | null
  user_id?: number | null
}

type NexusJobStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'paused'
  | 'waiting'

interface NexusJobLog {
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'debug'
  message: string
}

interface NexusJobError {
  timestamp: string
  message: string
}

/**
 * Chapitre d'une série
 */
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

/**
 * Résultat d'analyse d'une série
 */
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

/**
 * Résultat de recherche
 */
interface NexusSearchResult {
  series_id: string
  title: string
  alt_titles?: string[]
  author?: string
  cover_url?: string
  url: string
  provider_id: string
  provider_name: string
  genre?: string[]
  status?: string
  nsfw: boolean
  language?: string
}

/**
 * Utilisateur NexusDL
 */
interface NexusUser {
  id: number
  username: string
  email: string
  full_name?: string
  role: 'admin' | 'user' | 'guest'
  status: 'active' | 'inactive' | 'banned' | 'pending'
  avatar_url?: string | null
  preferences?: Record<string, any>
  created_at: string
  updated_at: string
  last_login?: string | null
}

/**
 * Notification NexusDL
 */
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

/**
 * Session utilisateur
 */
interface NexusSession {
  id: number
  user_id: number
  user_agent?: string
  ip_address?: string
  expires_at: string
  created_at: string
  is_revoked: boolean
  isCurrent?: boolean
}

/**
 * Statistiques système
 */
interface NexusSystemMetrics {
  cpu_percent: number
  cpu_cores: number
  cpu_freq_current?: number
  cpu_freq_min?: number
  cpu_freq_max?: number
  memory_total: number
  memory_available: number
  memory_used: number
  memory_percent: number
  disk_total: number
  disk_used: number
  disk_free: number
  disk_percent: number
  process_memory: number
  process_cpu_percent: number
  process_threads: number
  process_open_files: number
  connections_count: number
}

/**
 * Info système
 */
interface NexusSystemInfo {
  app_name: string
  app_version: string
  build_date: string
  python_version: string
  platform: string
  os_name: string
  os_version: string
  architecture: string
  hostname: string
  environment: string
  debug_mode: boolean
  uptime_seconds: number
  server_time: string
}

/**
 * Healthcheck
 */
interface NexusHealthCheck {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  checks: Record<string, {
    status: 'ok' | 'error'
    [key: string]: any
  }>
}

// ==========================================================================
//  SECTION 7 — DÉCLARATION GLOBALE POUR WINDOW
// ==========================================================================

declare global {
  interface Window {
    /** Fonction utilitaire pour masquer le loader initial */
    __nexusHideLoader?: () => void

    /** API du loader initial */
    __nexusLoader?: {
      hide: (remove?: boolean) => void
      progress: (percent: number) => void
      setText: (text: string) => void
    }

    /** Application Vue (dev uniquement) */
    __nexusApp?: any

    /** Router Vue (dev uniquement) */
    __nexusRouter?: any

    /** Pinia (dev uniquement) */
    __nexusPinia?: any

    /** Client API (dev uniquement) */
    __nexusApi?: any

    /** Version de l'application (dev uniquement) */
    __nexusVersion?: string

    /** Day.js (dev uniquement) */
    __nexusDayjs?: any

    /** Options Vue globales */
    __VUE_OPTIONS_API__?: boolean

    /** Mode production Vue */
    __VUE_PROD_DEVTOOLS__?: boolean

    /** Hydratation Vue */
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__?: boolean

    /** Sentry (optionnel) */
    __nexusSentry?: {
      captureException: (error: any) => void
      captureMessage: (message: string) => void
    }

    /** Umami analytics (optionnel) */
    umami?: {
      track: (event: string, data?: Record<string, any>) => void
    }
  }

  // === Événements personnalisés ===
  interface WindowEventMap {
    'nexus:ready': CustomEvent<void>
    'nexus:logout': CustomEvent<void>
    'nexus:online': CustomEvent<void>
    'nexus:offline': CustomEvent<void>
    'nexus:error': CustomEvent<{
      message: string
      details?: string
      status?: number
      critical?: boolean
    }>
    'nexus:pwa-update': CustomEvent<void>
    'nexus:pwa-install-available': CustomEvent<void>
    'nexus:pwa-installed': CustomEvent<void>
  }
}

// ==========================================================================
//  SECTION 8 — DÉCLARATION DES TYPES POUR LES MODULES INTERNES
// ==========================================================================

// --- Utils ---
declare module '@/utils/formatters' {
  export function formatDate(date: any, format?: string): string
  export function formatDateShort(date: any): string
  export function formatDateLong(date: any): string
  export function formatTime(date: any): string
  export function formatDateTime(date: any): string
  export function formatRelativeTime(date: any, withoutSuffix?: boolean): string
  export function formatDateContextual(date: any): string
  export function formatDuration(ms: number, short?: boolean): string
  export function formatNumber(num: number, decimals?: number, locale?: string): string
  export function formatPercent(num: number, decimals?: number): string
  export function formatFileSize(bytes: number, decimals?: number, locale?: string): string
  export function truncate(text: string, maxLength?: number, suffix?: string): string
  export function capitalize(text: string): string
  export function titleCase(text: string): string
  export function slugify(text: string, separator?: string): string
  export function formatStars(rating: number, maxStars?: number): string
  export function formatJobStatus(status: string): string
  export function getJobStatusIcon(status: string): string
}

declare module '@/utils/validators' {
  export function isNotEmpty(value: any): boolean
  export function isNumber(value: any, allowNaN?: boolean): boolean
  export function isValidEmail(email: string): boolean
  export function isValidUrl(url: string, protocols?: string[]): boolean
  export function isValidScanUrl(url: string): boolean
  export function validatePasswordStrength(password: string, options?: any): {
    valid: boolean
    errors: string[]
    score: number
    strength: string
  }
  export function doPasswordsMatch(password: string, confirm: string): boolean
  export function validateUsername(username: string, options?: any): {
    valid: boolean
    errors: string[]
  }
  export function validateChapterNumber(value: any, options?: any): {
    valid: boolean
    errors: string[]
  }
}

// --- Composables ---
declare module '@/composables/useApi' {
  export function useApi(options?: any): any
  export default useApi
}

declare module '@/composables/useAuth' {
  export function useAuth(options?: any): any
  export default useAuth
}

declare module '@/composables/useTheme' {
  export function useTheme(options?: any): {
    currentTheme: any
    isDark: any
    isLight: any
    systemPrefersDark: any
    isLoading: any
    error: any
    themeLabel: any
    themeIcon: any
    setTheme: (theme: string) => void
    toggleTheme: () => void
    enableDark: () => void
    enableLight: () => void
    enableSystem: () => void
    refresh: () => void
    applyTheme: () => void
    initTheme: () => void
    getSystemPreference: () => boolean
    THEME_DARK: string
    THEME_LIGHT: string
    THEME_SYSTEM: string
  }
  export default useTheme
}

declare module '@/composables/useToast' {
  export function useToast(options?: any): any
  export function installToastPlugin(app: any, options?: any): void
  export default useToast
}

// --- Directives ---
declare module '@/directives/click-outside' {
  export const clickOutside: any
  export function installClickOutside(app: any, options?: any): void
  const defaultExport: {
    install: typeof installClickOutside
    directive: any
  }
  export default defaultExport
}

declare module '@/directives/focus' {
  export const focus: any
  export function installFocus(app: any, options?: any): void
  const defaultExport: {
    install: typeof installFocus
    directive: any
  }
  export default defaultExport
}

// ==========================================================================
//  SECTION 9 — STYLES SCSS (modules types)
// ==========================================================================

declare module '@/assets/styles/global.scss' {
  const content: string
  export default content
}

declare module '@/assets/styles/nexus-theme.scss' {
  const content: string
  export default content
}

// ==========================================================================
//  SECTION 10 — EXPORT POUR UTILISATION DANS LES MODULES
// ==========================================================================

export {}

// ==========================================================================
//  NOTES
// ==========================================================================
//  - Ce fichier fournit toutes les déclarations de types nécessaires pour
//    que TypeScript reconnaisse les imports de :
//    * Variables d'environnement Vite (import.meta.env)
//    * Assets statiques (images, fonts, styles)
//    * Modules Vue (.vue)
//    * Bibliothèques externes (dayjs plugins, vite-plugins, etc.)
//    * Modules internes du projet (utils, composables, directives)
//    * Événements personnalisés (nexus:*)
//    * Types métier NexusDL (Job, LibraryItem, Provider, User, etc.)
//  - Ce fichier est automatiquement inclus par TypeScript grâce au
//    `include` dans tsconfig.json.
//  - Les types sont exportés globalement pour éviter d'avoir à les
//    importer dans chaque fichier.
// ==========================================================================
