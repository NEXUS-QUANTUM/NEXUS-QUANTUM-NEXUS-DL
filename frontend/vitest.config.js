// ==========================================================================
//  NexusDL 2.0 - Vitest Configuration
//  Fichier : frontend/vitest.config.js
//  Description : Configuration des tests unitaires avec Vitest
// ==========================================================================

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// Charger les variables d'environnement pour les tests
const env = loadEnv('test', process.cwd(), '')

export default defineConfig({
  plugins: [
    vue({
      // Options spécifiques pour les tests
      template: {
        compilerOptions: {
          // Permettre l'utilisation de composants non enregistrés pour les tests
          isCustomElement: tag => tag.startsWith('test-')
        }
      }
    })
  ],

  // Configuration des alias (identique à celle de vite.config.js)
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@stores': path.resolve(__dirname, './src/stores'),
      '@composables': path.resolve(__dirname, './src/composables'),
      '@assets': path.resolve(__dirname, './src/assets'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@common': path.resolve(__dirname, './src/components/common')
    }
  },

  // Configuration de Vitest
  test: {
    // Environnement de test (jsdom pour simuler un navigateur)
    environment: 'jsdom',
    
    // Fichiers de test
    include: [
      'src/**/*.{test,spec}.{js,ts,jsx,tsx}',
      'tests/**/*.{test,spec}.{js,ts,jsx,tsx}'
    ],
    
    // Exclure les dossiers de build et node_modules
    exclude: [
      'node_modules',
      'dist',
      'build',
      '.idea',
      '.git',
      '.cache'
    ],

    // Globals pour éviter les imports répétitifs (describe, it, expect, etc.)
    globals: true,

    // Setup avant les tests (fichier de configuration)
    setupFiles: [
      './src/test/setup.js'
    ],

    // Couverture de code
    coverage: {
      provider: 'v8', // ou 'istanbul' selon les préférences
      enabled: true,
      include: [
        'src/**/*.{vue,js,ts}'
      ],
      exclude: [
        'src/main.js',
        'src/**/*.d.ts',
        'src/test/**/*',
        'src/**/__tests__/**/*',
        'src/**/__mocks__/**/*'
      ],
      thresholds: {
        lines: 60,
        functions: 60,
        branches: 50,
        statements: 60
      },
      // Formatter pour les rapports
      reporter: ['text', 'lcov', 'html', 'json-summary'],
      reportsDirectory: './coverage'
    },

    // Reporter pour les résultats des tests
    reporters: [
      'default',
      'json',
      'html'
    ],

    // Dossiers de test
    testMatch: [
      '**/*.spec.js',
      '**/*.spec.ts',
      '**/*.test.js',
      '**/*.test.ts'
    ],

    // Options de test
    pool: 'forks', // Utiliser des processus forks pour l'isolation
    poolOptions: {
      forks: {
        singleFork: false,
        isolate: true
      }
    },

    // Timeout global des tests (10 secondes)
    testTimeout: 10000,

    // Hook timeout pour les tests asynchrones
    hookTimeout: 10000,

    // Mock des API externes
    mock: {
      // Si un module n'est pas trouvé, le mocker automatiquement
      default: true
    },

    // Mocker les composants importés (utile pour Vue)
    deps: {
      interopDefault: true,
      register: true
    },

    // Séquentiel ou parallèle
    sequence: {
      shuffle: false,
      concurrent: false
    },

    // Environnement global pour la simulation de navigateur
    env: {
      VITE_API_BASE: '/api',
      VITE_APP_VERSION: '2.0.0-test',
      NODE_ENV: 'test'
    },

    // Configurer la fenêtre de simulation pour les tests
    browser: {
      name: 'jsdom',
      headless: true
    }
  },

  // Configurer le serveur de développement pour les tests
  server: {
    port: 5174,
    host: '0.0.0.0',
    watch: {
      // Désactiver le watch en mode CI
      usePolling: process.env.CI === 'true',
      interval: 1000
    }
  },

  // Optimisation pour les tests
  build: {
    sourcemap: true,
    target: 'esnext',
    minify: false,
    rollupOptions: {
      // Ne pas inclure les dépendances inutiles
      external: ['vue']
    }
  },

  // CSS
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `
          @import "@assets/styles/nexus-theme.scss";
          @import "@assets/styles/global.scss";
        `
      }
    }
  },

  // Dépendances externes
  define: {
    __TEST__: true,
    __DEV__: false
  },

  // Options de débogage
  logLevel: 'info',
  silent: false
})
