// ==========================================================================
//  NexusDL 2.0 - Vite Environment Types
//  Fichier : frontend/src/vite-env.d.ts
//  Description : Définitions de types pour l'environnement Vite et l'application
//  Version : 2.0.0
// ==========================================================================

/// <reference types="vite/client" />

// ==========================================================================
//  Types des variables d'environnement Vite
// ==========================================================================

interface ImportMetaEnv {
  /** Mode de l'application (development, production, test) */
  readonly MODE: string
  /** Base URL pour l'API */
  readonly VITE_API_BASE: string
  /** Backend URL pour le proxy (développement) */
  readonly VITE_API_BACKEND_URL: string
  /** Version de l'application */
  readonly VITE_APP_VERSION: string
  /** Date de construction */
  readonly VITE_BUILD_DATE: string
  /** Base URL pour les WebSockets */
  readonly VITE_WS_BASE: string
  /** URL de base pour l'application (pour les assets) */
  readonly BASE_URL: string
  /** Flag de développement */
  readonly DEV: boolean
  /** Flag de production */
  readonly PROD: boolean
  /** Flag de test */
  readonly TEST: boolean
  // Variables personnalisées
  readonly VITE_DEBUG: string
  readonly VITE_SENTRY_DSN: string
  readonly VITE_ANALYTICS_ID: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// ==========================================================================
//  Déclaration des modules (pour les importations de fichiers non-JS)
// ==========================================================================

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '*.svg' {
  const content: string
  export default content
}

declare module '*.png' {
  const content: string
  export default content
}

declare module '*.jpg' {
  const content: string
  export default content
}

declare module '*.jpeg' {
  const content: string
  export default content
}

declare module '*.gif' {
  const content: string
  export default content
}

declare module '*.webp' {
  const content: string
  export default content
}

declare module '*.scss' {
  const content: Record<string, string>
  export default content
}

declare module '*.css' {
  const content: Record<string, string>
  export default content
}

declare module '*.json' {
  const value: any
  export default value
}

// ==========================================================================
//  Types globaux pour l'application
// ==========================================================================

declare global {
  // --------------------------------------------------------------------------
  //  Interfaces pour les données de l'application
  // --------------------------------------------------------------------------

  /** Rôle utilisateur */
  type UserRole = 'admin' | 'user' | 'guest'

  /** Statut de l'utilisateur */
  type UserStatus = 'active' | 'inactive' | 'banned' | 'pending'

  /** Informations utilisateur */
  interface User {
    id: number
    username: string
    email: string
    full_name?: string
    role: UserRole
    status: UserStatus
    avatar_url?: string
    preferences?: string
    created_at: string
    updated_at: string
    last_login?: string
  }

  /** Statut d'un job */
  type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'waiting' | 'paused'

  /** Priorité d'un job */
  type JobPriority = 'low' | 'normal' | 'high' | 'critical'

  /** Type de job */
  type JobType = 'download' | 'analyze' | 'extract' | 'convert' | 'cleanup'

  /** Entrée de log */
  interface LogEntry {
    timestamp: string
    level: 'debug' | 'info' | 'warning' | 'error'
    message: string
  }

  /** Informations d'un job */
  interface Job {
    id: string
    title: string
    url: string
    type: JobType
    priority: JobPriority
    status: JobStatus
    provider_id?: string
    total_chapters: number
    done_chapters: number
    total_pages: number
    done_pages: number
    progress: number
    current_chapter?: string
    current_chapter_id?: string
    data?: Record<string, any>
    logs: LogEntry[]
    errors: LogEntry[]
    created_at: string
    updated_at: string
    started_at?: string
    completed_at?: string
    cancelled_at?: string
    user_id?: number
    result_path?: string
    result_size?: number
  }

  /** Provider (site de scan) */
  interface Provider {
    id: string
    provider_id: string
    name: string
    base_url: string
    enabled: boolean
    nsfw: boolean
    languages: string[]
    version: string
    description: string
    priority: number
    last_used?: string
    created_at: string
    updated_at: string
    supported_languages?: string[]
  }

  /** Élément de bibliothèque */
  interface LibraryItem {
    id: string
    title: string
    filename: string
    file_path: string
    size_bytes: number
    size_formatted: string
    created_at: string
    updated_at: string
    last_read?: string
    read_count: number
    is_favorite: boolean
    rating: number
    metadata: {
      author?: string
      series?: string
      genre?: string
      description?: string
      volume?: string
      chapters?: number
      pages?: number
      year?: number
      language?: string
    }
    tags: string[]
    cover_path?: string
  }

  /** Métadonnées de bibliothèque extraites */
  interface LibraryMetadata {
    title: string
    series?: string
    author?: string
    publisher?: string
    genre?: string
    description?: string
    volume?: string
    chapters?: number
    pages?: number
    year?: number
    language?: string
  }

  /** Chapitre */
  interface Chapter {
    id: string
    title: string
    number: number
    volume?: number
    release_date?: string
    upload_date?: string
    url: string
    page_count?: number
    pages?: number
    language?: string
    is_available: boolean
    read?: boolean
    disabled?: boolean
  }

  /** Résultat d'analyse d'une série */
  interface AnalysisResult {
    title: string
    url: string
    provider_id: string
    chapters: Chapter[]
    author?: string
    description?: string
    cover_url?: string
    genre: string[]
    status: string
    year?: number
    language: string
    nsfw: boolean
    total_chapters: number
  }

  /** Résultat de recherche */
  interface SearchResult {
    series_id: string
    title: string
    alt_titles: string[]
    author?: string
    cover_url?: string
    url: string
    provider_id: string
    provider_name: string
    genre: string[]
    status: string
    nsfw: boolean
    language: string
  }

  /** Notification */
  interface Notification {
    id: string
    message: string
    type: 'success' | 'error' | 'warning' | 'info' | 'system'
    icon?: string
    read: boolean
    dismissed: boolean
    duration: number
    created_at: string
    meta?: Record<string, any>
    onAction?: (notification: Notification) => void
    onClose?: (notification: Notification) => void
  }

  // --------------------------------------------------------------------------
  //  Types pour les utilitaires globaux (dayjs, axios, etc.)
  // --------------------------------------------------------------------------

  // dayjs est déjà typé via la déclaration de module, mais on peut ajouter des extensions
  // si nécessaire.

  // Variables globales exposées via Vite
  const __APP_VERSION__: string
  const __BUILD_DATE__: string
  const __DEV__: boolean
  const __PROD__: boolean
}

// ==========================================================================
//  Export vide pour que le fichier soit considéré comme un module
// ==========================================================================

export {}
