// ==========================================================================
//  NexusDL 2.0 - Vite Configuration (version corrigée et complète)
//  Fichier : frontend/vite.config.js
//  Description : Configuration Vite pour Vue.js 3, avec correction de
//                l'import circulaire SCSS qui causait l'erreur de build.
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

      // Compression gzip (production uniquement)
      compression({
        algorithm: 'gzip',
        ext: '.gz',
        threshold: 1024,
        deleteOriginalAssets: false,
        disable: !isProduction
      }),

      // Compression brotli (production uniquement)
      compression({
        algorithm: 'brotliCompress',
        ext: '.br',
        threshold: 1024,
        deleteOriginalAssets: false,
        disable: !isProduction
      }),

      // PWA (Progressive Web App)
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.svg', 'robots.txt', 'apple-touch-icon.png'],
        manifest: false, // Utiliser /public/manifest.json
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
            {
              urlPattern: /\/api\/.*/i,
              handler: 'NetworkFirst',
              options: {
                cacheName: 'api-cache',
                networkTimeoutSeconds: 10,
                expiration: {
                  maxEntries: 50,
                  maxAgeSeconds: 60 * 60 // 1 heure
                },
                cacheableResponse: {
                  statuses: [0, 200]
                }
              }
            }
          ]
        },
        devOptions: {
          enabled: false // Désactiver en dev pour éviter les conflits
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
        '@views': path.resolve(__dirname, './src/views'),
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
              console.error('❌ Proxy error:', err.message)
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
        },
        '/ws': {
          target: apiProxyTarget.replace(/^http/, 'ws'),
          changeOrigin: true,
          ws: true
        }
      },
      watch: {
        usePolling: false,
        ignored: ['**/node_modules/**', '**/dist/**', '**/.vite-cache/**']
      }
    },

    // ======================================================================
    //  Preview (aperçu du build de production)
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
    //  Build (production)
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
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, 'index.html')
        },
        output: {
          manualChunks: {
            // Frameworks principaux
            'vendor-vue': ['vue', 'vue-router', 'pinia'],
            // Bibliothèques utilitaires
            'vendor-utils': ['axios', 'dayjs', '@vueuse/core']
          },
          // Nommage des fichiers avec hash pour cache busting
          entryFileNames: 'assets/js/[name].[hash].js',
          chunkFileNames: 'assets/js/[name].[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const ext = info[info.length - 1]
            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
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
      },
      emptyOutDir: true,
      copyPublicDir: true,
      // Désactiver le polyfill inutile
      modulePreload: {
        polyfill: false
      }
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
          // ✅ CORRECTION CRITIQUE :
          // Ne PAS injecter automatiquement `nexus-theme.scss` et `global.scss`
          // via `additionalData`, car cela cause un import circulaire
          // (le fichier s'importe lui-même) → erreur "This file is already being loaded".
          //
          // Les styles globaux sont importés explicitement dans `src/main.js`.
          //
          // Si vous souhaitez injecter uniquement des VARIABLES SCSS (sans règles CSS),
          // créez un fichier `src/assets/styles/variables.scss` et décommentez :
          // additionalData: `@import "@assets/styles/variables.scss";`,
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
    //  Optimisations des dépendances
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
    //  Variables d'environnement exposées au client
    // ======================================================================
    define: {
      __APP_VERSION__: JSON.stringify(env.VITE_APP_VERSION || '2.0.0'),
      __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
      __DEV__: isDevelopment,
      __PROD__: isProduction
    },

    // ======================================================================
    //  Options ESBuild (transpilation)
    // ======================================================================
    esbuild: {
      // Supprimer les console.log et debugger en production
      drop: isProduction ? ['console', 'debugger'] : [],
      target: 'es2020',
      legalComments: 'none',
      treeShaking: true,
      minifySyntax: isProduction,
      minifyIdentifiers: isProduction,
      minifyWhitespace: isProduction
    },

    // ======================================================================
    //  Cache
    // ======================================================================
    cacheDir: '.vite-cache',

    // ======================================================================
    //  Logs
    // ======================================================================
    logLevel: isProduction ? 'warn' : 'info',
    clearScreen: true
  }
})
