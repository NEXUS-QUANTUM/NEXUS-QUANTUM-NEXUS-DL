// ==========================================================================
//  NexusDL 2.0 - Vite Configuration
//  Fichier : frontend/vite.config.js
//  Description : Configuration complète de Vite pour l'application Vue.js 3
// ==========================================================================

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import compression from 'vite-plugin-compression'
import { VitePWA } from 'vite-plugin-pwa'
import autoprefixer from 'autoprefixer'
import cssnano from 'cssnano'

// ==========================================================================
//  Configuration de base
// ==========================================================================

export default defineConfig(({ mode }) => {
  // Charger les variables d'environnement
  const env = loadEnv(mode, process.cwd(), '')
  const apiProxyTarget = env.VITE_API_BACKEND_URL || 'http://localhost:8000'
  const isProduction = mode === 'production'
  const isDevelopment = mode === 'development'

  return {
    // ======================================================================
    //  Plugins
    // ======================================================================
    plugins: [
      // Vue 3 avec Composition API
      vue({
        template: {
          transformAssetUrls: {
            includeAbsolute: false
          }
        },
        script: {
          defineModel: true,
          propsDestructure: true
        }
      }),

      // Compression gzip
      compression({
        algorithm: 'gzip',
        ext: '.gz',
        threshold: 1024,
        deleteOriginalAssets: false
      }),

      // Compression brotli
      compression({
        algorithm: 'brotliCompress',
        ext: '.br',
        threshold: 1024,
        deleteOriginalAssets: false
      }),

      // PWA (Progressive Web App) - activé en production
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.svg', 'robots.txt', 'apple-touch-icon.png'],
        manifest: false, // Utiliser le manifest.json existant
        workbox: {
          globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
          runtimeCaching: [
            {
              urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
              handler: 'CacheFirst',
              options: {
                cacheName: 'google-fonts-cache',
                expiration: {
                  maxEntries: 10,
                  maxAgeSeconds: 60 * 60 * 24 * 365 // 1 an
                }
              }
            },
            {
              urlPattern: /^https:\/\/api\./i,
              handler: 'NetworkFirst',
              options: {
                cacheName: 'api-cache',
                networkTimeoutSeconds: 10,
                expiration: {
                  maxEntries: 50,
                  maxAgeSeconds: 60 * 60 // 1 heure
                }
              }
            }
          ]
        },
        devOptions: {
          enabled: isDevelopment,
          type: 'module'
        }
      })
    ],

    // ======================================================================
    //  Résolution des alias
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
        '@types': path.resolve(__dirname, './src/types')
      },
      extensions: ['.vue', '.js', '.ts', '.jsx', '.tsx', '.json']
    },

    // ======================================================================
    //  Serveur de développement
    // ======================================================================
    server: {
      port: 5173,
      host: '0.0.0.0',
      strictPort: false,
      open: false,
      cors: true,
      proxy: {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, ''),
          configure: (proxy) => {
            proxy.on('error', (err) => {
              console.error('Proxy error:', err)
            })
          }
        },
        '/docs': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        },
        '/redoc': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        },
        '/openapi.json': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        },
        '/health': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        }
      },
      watch: {
        usePolling: false,
        ignored: ['**/node_modules/**', '**/dist/**']
      },
      hmr: {
        overlay: true,
        protocol: 'ws',
        host: 'localhost',
        port: 5173
      }
    },

    // ======================================================================
    //  Preview (production)
    // ======================================================================
    preview: {
      port: 4173,
      host: '0.0.0.0',
      strictPort: false,
      cors: true
    },

    // ======================================================================
    //  Build (production)
    // ======================================================================
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: !isProduction,
      minify: 'esbuild',
      target: 'es2020',
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, 'index.html')
        },
        output: {
          manualChunks: {
            // Frameworks principaux
            'vendor-vue': ['vue', 'vue-router', 'pinia'],
            'vendor-utils': ['axios', 'dayjs', '@vueuse/core'],
            // UI et composants
            'vendor-ui': ['@vueuse/core'],
            // Séparer les dépendances tierces lourdes
            'vendor-other': (id) => {
              if (id.includes('node_modules')) {
                return 'vendor-other'
              }
            }
          },
          // Noms de fichiers avec hash pour cache busting
          entryFileNames: 'assets/js/[name].[hash].js',
          chunkFileNames: 'assets/js/[name].[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const ext = info[info.length - 1]
            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
              return 'assets/images/[name].[hash].[ext]'
            }
            if (/woff2?|ttf|eot/i.test(ext)) {
              return 'assets/fonts/[name].[hash].[ext]'
            }
            if (/css/i.test(ext)) {
              return 'assets/css/[name].[hash].[ext]'
            }
            return 'assets/[name].[hash].[ext]'
          }
        }
      },
      // Optimisations supplémentaires
      commonjsOptions: {
        transformMixedEsModules: true
      },
      // Augmenter la taille limite pour les chunks
      chunkSizeWarningLimit: 1000,
      // Minifier les CSS
      cssMinify: true,
      // Empty outDir before build
      emptyOutDir: true,
      // Copier les fichiers public
      copyPublicDir: true,
      // Polyfill pour les navigateurs plus anciens
      polyfillModulePreload: true
    },

    // ======================================================================
    //  CSS
    // ======================================================================
    css: {
      modules: {
        localsConvention: 'camelCase',
        scopeBehaviour: 'local'
      },
      preprocessorOptions: {
        scss: {
          // Ajouter automatiquement les styles globaux à tous les fichiers SCSS
          additionalData: `
            @import "@assets/styles/nexus-theme.scss";
            @import "@assets/styles/global.scss";
          `,
          api: 'modern-compiler',
          quietDeps: true,
          silenceDeprecations: ['legacy-js-api']
        }
      },
      postcss: {
        plugins: [
          autoprefixer({
            overrideBrowserslist: ['> 1%', 'last 2 versions', 'not dead']
          }),
          cssnano({
            preset: [
              'default',
              {
                discardComments: { removeAll: true },
                normalizeWhitespace: true,
                mergeRules: true,
                reduceTransforms: true
              }
            ]
          })
        ]
      },
      devSourcemap: isDevelopment
    },

    // ======================================================================
    //  Optimisations de performance
    // ======================================================================
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'axios',
        'dayjs',
        '@vueuse/core'
      ],
      exclude: [],
      esbuildOptions: {
        target: 'es2020',
        treeShaking: true
      },
      force: false
    },

    // ======================================================================
    //  Variables d'environnement exposées au client
    // ======================================================================
    define: {
      __APP_VERSION__: JSON.stringify(env.VITE_APP_VERSION || '2.0.0'),
      __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
      __DEV__: isDevelopment,
      __PROD__: isProduction
    },

    // ======================================================================
    //  Options ESBuild (pour le transpile)
    // ======================================================================
    esbuild: {
      // Supprimer les console.log en production
      drop: isProduction ? ['console', 'debugger'] : [],
      target: 'es2020',
      legalComments: 'none',
      treeShaking: true,
      minifySyntax: true,
      minifyIdentifiers: true,
      minifyWhitespace: true
    },

    // ======================================================================
    //  Cache
    // ======================================================================
    cacheDir: '.vite-cache',

    // ======================================================================
    //  Logs
    // ======================================================================
    logLevel: isProduction ? 'warn' : 'info',
    clearScreen: true,

    // ======================================================================
    //  Mode legacy (optionnel)
    // ======================================================================
    // build: {
    //   rollupOptions: {
    //     plugins: [
    //       // Pour la compatibilité avec les navigateurs plus anciens
    //       // legacy({
    //       //   targets: ['defaults', 'not IE 11']
    //       // })
    //     ]
    //   }
    // }
  }
})
