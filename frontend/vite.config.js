// ==========================================================================
//  NexusDL 2.0 - Vite Configuration (version complète et corrigée)
//  Fichier : frontend/vite.config.js
//  Description : Configuration Vite pour Vue.js 3, avec PWA, compression,
//                proxy API, et correction de l'import circulaire SCSS.
//  Version : 2.0.0
// ==========================================================================

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import compression from 'vite-plugin-compression'
import { VitePWA } from 'vite-plugin-pwa'
import autoprefixer from 'autoprefixer'
import cssnano from 'cssnano'

// ==========================================================================
//  Configuration principale
// ==========================================================================

export default defineConfig(({ mode }) => {
  // Chargement des variables d'environnement (VITE_*)
  const env = loadEnv(mode, process.cwd(), '')
  const apiProxyTarget = env.VITE_API_BACKEND_URL || 'http://localhost:8000'
  const isProduction = mode === 'production'
  const isDevelopment = mode === 'development'

  return {
    // ======================================================================
    //  PLUGINS
    // ======================================================================
    plugins: [
      // --------------------------------------------------------------------
      //  Vue 3 - Support SFC et Composition API
      // --------------------------------------------------------------------
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

      // --------------------------------------------------------------------
      //  Compression Gzip (production uniquement)
      // --------------------------------------------------------------------
      compression({
        algorithm: 'gzip',
        ext: '.gz',
        threshold: 1024,
        deleteOriginalAssets: false,
        disable: !isProduction
      }),

      // --------------------------------------------------------------------
      //  Compression Brotli (production uniquement)
      // --------------------------------------------------------------------
      compression({
        algorithm: 'brotliCompress',
        ext: '.br',
        threshold: 1024,
        deleteOriginalAssets: false,
        disable: !isProduction
      }),

      // --------------------------------------------------------------------
      //  PWA (Progressive Web App)
      // --------------------------------------------------------------------
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.svg', 'robots.txt', 'apple-touch-icon.png'],
        manifest: false, // Utilise /public/manifest.json
        workbox: {
          globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
          cleanupOutdatedCaches: true,
          runtimeCaching: [
            // --- Google Fonts ---
            {
              urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
              handler: 'CacheFirst',
              options: {
                cacheName: 'google-fonts-cache',
                expiration: {
                  maxEntries: 10,
                  maxAgeSeconds: 60 * 60 * 24 * 365 // 1 an
                },
                cacheableResponse: {
                  statuses: [0, 200]
                }
              }
            },
            {
              urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
              handler: 'CacheFirst',
              options: {
                cacheName: 'gstatic-fonts-cache',
                expiration: {
                  maxEntries: 10,
                  maxAgeSeconds: 60 * 60 * 24 * 365
                },
                cacheableResponse: {
                  statuses: [0, 200]
                }
              }
            },
            // --- API NexusDL ---
            {
              urlPattern: /\/api\/.*/i,
              handler: 'NetworkFirst',
              options: {
                cacheName: 'nexusdl-api-cache',
                networkTimeoutSeconds: 10,
                expiration: {
                  maxEntries: 100,
                  maxAgeSeconds: 60 * 60 // 1 heure
                },
                cacheableResponse: {
                  statuses: [0, 200]
                }
              }
            },
            // --- Images distantes (couvertures) ---
            {
              urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/i,
              handler: 'CacheFirst',
              options: {
                cacheName: 'images-cache',
                expiration: {
                  maxEntries: 200,
                  maxAgeSeconds: 60 * 60 * 24 * 30 // 30 jours
                }
              }
            }
          ]
        },
        devOptions: {
          enabled: false // Désactivé en dev pour éviter les conflits
        }
      })
    ],

    // ======================================================================
    //  RÉSOLUTION DES ALIAS
    //  ⚠️ Doit correspondre à `paths` dans tsconfig.json
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
    //  SERVEUR DE DÉVELOPPEMENT
    // ======================================================================
    server: {
      port: 5173,
      host: '0.0.0.0',
      strictPort: false,
      open: false,
      cors: true,
      proxy: {
        // --- API REST ---
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, ''),
          configure: (proxy) => {
            proxy.on('error', (err) => {
              console.error('❌ [Proxy] Erreur API :', err.message)
            })
          }
        },
        // --- Documentation Swagger ---
        '/docs': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        },
        // --- Documentation ReDoc ---
        '/redoc': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        },
        // --- Schéma OpenAPI ---
        '/openapi.json': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        },
        // --- Healthcheck ---
        '/health': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
        },
        // --- WebSocket ---
        '/ws': {
          target: apiProxyTarget.replace(/^http/, 'ws'),
          changeOrigin: true,
          ws: true,
          secure: false
        }
      },
      watch: {
        usePolling: false,
        ignored: ['**/node_modules/**', '**/dist/**', '**/.vite-cache/**']
      }
    },

    // ======================================================================
    //  APERÇU DU BUILD (preview)
    // ======================================================================
    preview: {
      port: 4173,
      host: '0.0.0.0',
      strictPort: false,
      cors: true,
      proxy: {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false
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
        },
        '/ws': {
          target: apiProxyTarget.replace(/^http/, 'ws'),
          changeOrigin: true,
          ws: true
        }
      }
    },

    // ======================================================================
    //  BUILD (PRODUCTION)
    // ======================================================================
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: !isProduction,
      minify: 'esbuild',
      target: 'es2020',
      chunkSizeWarningLimit: 1000,
      assetsInlineLimit: 4096, // 4 KB
      cssCodeSplit: true,
      reportCompressedSize: false,
      emptyOutDir: true,
      copyPublicDir: true,
      modulePreload: {
        polyfill: false
      },
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, 'index.html')
        },
        output: {
          // --- Découpage manuel des chunks ---
          manualChunks: {
            'vendor-vue': ['vue', 'vue-router', 'pinia'],
            'vendor-utils': ['axios', 'dayjs', '@vueuse/core']
          },
          // --- Nommage des fichiers avec hash ---
          entryFileNames: 'assets/js/[name].[hash].js',
          chunkFileNames: 'assets/js/[name].[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const ext = info[info.length - 1]
            if (/png|jpe?g|svg|gif|tiff|bmp|ico|webp|avif/i.test(ext)) {
              return 'assets/images/[name].[hash].[ext]'
            }
            if (/woff2?|ttf|eot|otf/i.test(ext)) {
              return 'assets/fonts/[name].[hash].[ext]'
            }
            if (/css/i.test(ext)) {
              return 'assets/css/[name].[hash].[ext]'
            }
            return 'assets/[name].[hash].[ext]'
          }
        }
      },
      commonjsOptions: {
        transformMixedEsModules: true
      }
    },

    // ======================================================================
    //  CSS / SCSS
    //  ⚠️ CORRECTION CRITIQUE :
    //  NE PAS injecter `nexus-theme.scss` ou `global.scss` via `additionalData`
    //  car cela crée un import circulaire → erreur "This file is already being loaded".
    //
    //  Les styles globaux sont importés explicitement dans `src/main.js`.
    // ======================================================================
    css: {
      modules: {
        localsConvention: 'camelCase',
        scopeBehaviour: 'local'
      },
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler',
          quietDeps: true,
          silenceDeprecations: ['legacy-js-api']
          // ✅ Pas de `additionalData` ici (voir commentaire ci-dessus)
        }
      },
      postcss: {
        plugins: [
          autoprefixer({
            overrideBrowserslist: ['> 1%', 'last 2 versions', 'not dead']
          }),
          ...(isProduction
            ? [
                cssnano({
                  preset: [
                    'default',
                    {
                      discardComments: { removeAll: true },
                      normalizeWhitespace: true,
                      mergeRules: true,
                      reduceTransforms: true,
                      minifyFontValues: true,
                      minifySelectors: true
                    }
                  ]
                })
              ]
            : [])
        ]
      },
      devSourcemap: isDevelopment
    },

    // ======================================================================
    //  OPTIMISATION DES DÉPENDANCES
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
        treeShaking: true,
        legalComments: 'none'
      },
      force: false
    },

    // ======================================================================
    //  VARIABLES GLOBALES EXPOSÉES AU CLIENT
    // ======================================================================
    define: {
      __APP_VERSION__: JSON.stringify(env.VITE_APP_VERSION || '2.0.0'),
      __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
      __DEV__: isDevelopment,
      __PROD__: isProduction
    },

    // ======================================================================
    //  OPTIONS ESBUILD (transpilation)
    // ======================================================================
    esbuild: {
      drop: isProduction ? ['console', 'debugger'] : [],
      target: 'es2020',
      legalComments: 'none',
      treeShaking: true,
      minifySyntax: isProduction,
      minifyIdentifiers: isProduction,
      minifyWhitespace: isProduction
    },

    // ======================================================================
    //  CACHE
    // ======================================================================
    cacheDir: '.vite-cache',

    // ======================================================================
    //  LOGS
    // ======================================================================
    logLevel: isProduction ? 'warn' : 'info',
    clearScreen: true
  }
})
