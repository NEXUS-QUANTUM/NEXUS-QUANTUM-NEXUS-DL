// ==========================================================================
//  NexusDL 2.0 - Vitest Configuration (version complète et corrigée)
//  Fichier : frontend/vitest.config.js
//  Description : Configuration complète pour les tests unitaires et
//                d'intégration avec Vitest + Vue Test Utils.
//  Version : 2.0.0
// ==========================================================================

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// ==========================================================================
//  Configuration principale
// ==========================================================================

export default defineConfig(({ mode }) => {
  // Chargement des variables d'environnement pour les tests
  const env = loadEnv(mode || 'test', process.cwd(), '')

  return {
    // ======================================================================
    //  PLUGINS
    // ======================================================================
    plugins: [
      // Vue 3 - Support des SFC (Single File Components)
      vue({
        template: {
          compilerOptions: {
            // Autoriser les composants custom (ex: Web Components) sans warning
            isCustomElement: (tag) => tag.startsWith('test-')
          }
        }
      })
    ],

    // ======================================================================
    //  RÉSOLUTION DES ALIAS
    //  ⚠️ Doit correspondre à vite.config.js et tsconfig.json
    // ======================================================================
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@components': path.resolve(__dirname, './src/components'),
        '@common': path.resolve(__dirname, './src/components/common'),
        '@stores': path.resolve(__dirname, './src/stores'),
        '@composables': path.resolve(__dirname, './src/composables'),
        '@assets': path.resolve(__dirname, './src/assets'),
        '@utils': path.resolve(__dirname, './src/utils'),
        '@directives': path.resolve(__dirname, './src/directives'),
        '@router': path.resolve(__dirname, './src/router'),
        '@views': path.resolve(__dirname, './src/views'),
        '@types': path.resolve(__dirname, './src/types')
      },
      extensions: ['.vue', '.js', '.ts', '.jsx', '.tsx', '.json']
    },

    // ======================================================================
    //  CONFIGURATION DE VITEST
    // ======================================================================
    test: {
      // ------------------------------------------------------------------
      //  Environnement de test
      // ------------------------------------------------------------------
      // 'jsdom' pour simuler un navigateur (DOM API, window, document)
      environment: 'jsdom',

      // ------------------------------------------------------------------
      //  Fichiers de test à inclure
      // ------------------------------------------------------------------
      include: [
        'src/**/*.{test,spec}.{js,ts,jsx,tsx}',
        'tests/**/*.{test,spec}.{js,ts,jsx,tsx}',
        '**/__tests__/**/*.{js,ts,jsx,tsx}'
      ],

      // ------------------------------------------------------------------
      //  Fichiers à exclure
      // ------------------------------------------------------------------
      exclude: [
        'node_modules',
        'dist',
        'build',
        'coverage',
        '.vite-cache',
        '.idea',
        '.git',
        '.cache',
        '**/*.stories.{js,ts,jsx,tsx}'
      ],

      // ------------------------------------------------------------------
      //  Pattern de correspondance des fichiers de test
      // ------------------------------------------------------------------
      testMatch: [
        '**/*.spec.{js,ts,jsx,tsx}',
        '**/*.test.{js,ts,jsx,tsx}'
      ],

      // ------------------------------------------------------------------
      //  Globales (describe, it, expect, beforeEach, etc.)
      // ------------------------------------------------------------------
      globals: true,

      // ------------------------------------------------------------------
      //  Fichiers de configuration avant chaque test
      // ------------------------------------------------------------------
      setupFiles: [
        './src/test/setup.js'
      ],

      // ------------------------------------------------------------------
      //  Timeouts
      // ------------------------------------------------------------------
      testTimeout: 10000,     // Timeout par test (10s)
      hookTimeout: 10000,     // Timeout pour les hooks (10s)
      teardownTimeout: 5000,  // Timeout pour le teardown (5s)

      // ------------------------------------------------------------------
      //  Mode d'exécution
      // ------------------------------------------------------------------
      // 'forks' : isole les tests dans des processus séparés (plus sûr)
      // 'threads' : plus rapide mais moins isolé
      pool: 'forks',
      poolOptions: {
        forks: {
          singleFork: false,
          isolate: true,
          minForks: 1,
          maxForks: 4
        }
      },

      // ------------------------------------------------------------------
      //  Isolation des tests
      // ------------------------------------------------------------------
      isolate: true,

      // ------------------------------------------------------------------
      //  Séquentialité
      // ------------------------------------------------------------------
      sequence: {
        shuffle: false,      // Ne pas mélanger les tests
        concurrent: false,   // Ne pas exécuter les tests en parallèle
        hooks: 'stack'       // Ordre d'exécution des hooks
      },

      // ------------------------------------------------------------------
      //  Reporter
      // ------------------------------------------------------------------
      reporters: [
        'default',
        'json',
        'html'
      ],

      // ------------------------------------------------------------------
      //  Sortie des rapports
      // ------------------------------------------------------------------
      outputFile: {
        json: './coverage/test-results.json',
        html: './coverage/test-report/index.html'
      },

      // ------------------------------------------------------------------
      //  COUVERTURE DE CODE
      // ------------------------------------------------------------------
      coverage: {
        provider: 'v8',      // ou 'istanbul' (plus lent mais plus précis)
        enabled: true,
        all: true,
        include: [
          'src/**/*.{vue,js,ts,jsx,tsx}'
        ],
        exclude: [
          'src/main.js',
          'src/**/*.d.ts',
          'src/**/*.spec.{js,ts}',
          'src/**/*.test.{js,ts}',
          'src/test/**/*',
          'src/**/__tests__/**/*',
          'src/**/__mocks__/**/*',
          'src/types/**/*',
          'src/**/index.js',
          'src/assets/**/*',
          'src/router/**/*'
        ],
        reporter: ['text', 'text-summary', 'lcov', 'html', 'json-summary', 'clover'],
        reportsDirectory: './coverage',
        thresholds: {
          lines: 60,
          functions: 60,
          branches: 50,
          statements: 60,
          // Seuils par fichier (optionnel)
          'src/utils/**/*.js': {
            lines: 80,
            functions: 80,
            branches: 70,
            statements: 80
          }
        },
        clean: true,
        cleanOnRerun: true,
        skipFull: false
      },

      // ------------------------------------------------------------------
      //  MOCK ET DÉPENDANCES
      // ------------------------------------------------------------------
      deps: {
        // Interop ESM/CJS
        interopDefault: true,
        // Enregistrer automatiquement les mocks
        register: true,
        // Modules à inline (nécessaire pour certains packages)
        inline: [
          'vue',
          'vue-router',
          'pinia',
          '@vueuse/core'
        ],
        // Modules à exclure de l'inline
        external: [
          'node_modules/**'
        ]
      },

      // ------------------------------------------------------------------
      //  VARIABLES D'ENVIRONNEMENT POUR LES TESTS
      // ------------------------------------------------------------------
      env: {
        NODE_ENV: 'test',
        VITE_API_BASE: '/api',
        VITE_APP_VERSION: '2.0.0-test',
        VITE_API_BACKEND_URL: 'http://localhost:8000'
      },

      // ------------------------------------------------------------------
      //  TypeScript
      // ------------------------------------------------------------------
      typecheck: {
        enabled: false, // Activer si vous voulez vérifier les types pendant les tests
        checker: 'vue-tsc',
        include: ['src/**/*.{ts,tsx,vue}'],
        exclude: ['src/**/*.spec.ts', 'src/**/*.test.ts']
      },

      // ------------------------------------------------------------------
      //  OPTIONS DE DÉBOGAGE
      // ------------------------------------------------------------------
      logHeapUsage: true,     // Afficher l'usage mémoire
      silent: false,          // Ne pas silencer les console.log
      verbose: true,          // Afficher plus de détails

      // ------------------------------------------------------------------
      //  API
      // ------------------------------------------------------------------
      api: {
        port: 51204,          // Port pour l'API Vitest
        host: '0.0.0.0'
      },

      // ------------------------------------------------------------------
      //  UI (facultatif, nécessite @vitest/ui)
      // ------------------------------------------------------------------
      ui: false,              // Activer pour l'interface graphique

      // ------------------------------------------------------------------
      //  BROWSER MODE (facultatif, nécessite @vitest/browser)
      // ------------------------------------------------------------------
      browser: {
        enabled: false,
        name: 'jsdom',
        headless: true,
        viewport: {
          width: 1280,
          height: 720
        }
      }
    },

    // ======================================================================
    //  SERVEUR DE DÉVELOPPEMENT POUR LES TESTS
    // ======================================================================
    server: {
      port: 5174,
      host: '0.0.0.0',
      watch: {
        // Désactiver le polling en CI
        usePolling: process.env.CI === 'true',
        interval: 1000,
        ignored: ['**/node_modules/**', '**/dist/**', '**/coverage/**']
      }
    },

    // ======================================================================
    //  BUILD POUR LES TESTS
    // ======================================================================
    build: {
      sourcemap: true,
      target: 'esnext',
      minify: false,
      rollupOptions: {
        external: ['vue']
      }
    },

    // ======================================================================
    //  CSS POUR LES TESTS
    //  ⚠️ Pas d'`additionalData` (cohérent avec vite.config.js)
    // ======================================================================
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler',
          quietDeps: true,
          silenceDeprecations: ['legacy-js-api']
        }
      }
    },

    // ======================================================================
    //  DÉFINITIONS GLOBALES
    // ======================================================================
    define: {
      __TEST__: true,
      __DEV__: false,
      __PROD__: false,
      __APP_VERSION__: JSON.stringify('2.0.0-test'),
      __BUILD_DATE__: JSON.stringify(new Date().toISOString())
    },

    // ======================================================================
    //  LOGS
    // ======================================================================
    logLevel: 'info',
    clearScreen: false
  }
})
