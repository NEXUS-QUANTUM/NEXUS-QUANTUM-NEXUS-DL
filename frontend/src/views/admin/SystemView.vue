<!-- ==========================================================================
  NexusDL 2.0 - Admin System View (version complète)
  Fichier : frontend/src/views/admin/SystemView.vue
  Description : Console d'administration pour surveiller l'état du système :
                informations système, métriques en temps réel (CPU, RAM, disque),
                statut de la base de données, healthcheck, logs rapides,
                ressources, et statistiques globales.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="admin-system">
    <!-- ====================================================================
      EN-TÊTE — Titre, actions, statut global
    ==================================================================== -->
    <header class="admin-system__header">
      <div class="admin-system__header-left">
        <h1 class="admin-system__title">
          <span aria-hidden="true">⚙️</span>
          Système
        </h1>
        <p class="admin-system__subtitle">
          Surveillance et diagnostic du serveur NexusDL
        </p>
      </div>

      <div class="admin-system__header-right">
        <!-- Statut global -->
        <div
          class="admin-system__global-status"
          :class="`admin-system__global-status--${globalStatusClass}`"
        >
          <span class="admin-system__global-status-dot" aria-hidden="true" />
          <span class="admin-system__global-status-text">{{ globalStatusLabel }}</span>
        </div>

        <!-- Auto-refresh toggle -->
        <button
          type="button"
          class="admin-system__btn admin-system__btn--auto"
          :class="{ 'admin-system__btn--active': autoRefreshEnabled }"
          @click="toggleAutoRefresh"
          :aria-label="autoRefreshEnabled ? 'Désactiver l\'auto-refresh' : 'Activer l\'auto-refresh'"
          :title="autoRefreshEnabled ? 'Désactiver l\'auto-refresh' : 'Activer l\'auto-refresh'"
        >
          <span aria-hidden="true">{{ autoRefreshEnabled ? '⏸️' : '▶️' }}</span>
          Auto
        </button>

        <!-- Intervalle auto-refresh -->
        <NexusSelect
          v-model.number="autoRefreshInterval"
          :options="autoRefreshOptions"
          placeholder="Intervalle"
          size="sm"
          style="min-width: 130px"
        />

        <!-- Bouton rafraîchir -->
        <button
          type="button"
          class="admin-system__btn admin-system__btn--refresh"
          :disabled="loading"
          @click="refreshAll"
          aria-label="Rafraîchir"
          title="Rafraîchir maintenant"
        >
          <span v-if="loading" class="admin-system__spinner" aria-hidden="true">⟳</span>
          <span v-else aria-hidden="true">↻</span>
          Rafraîchir
        </button>
      </div>
    </header>

    <!-- ====================================================================
      BARRE D'ERREUR
    ==================================================================== -->
    <div v-if="error" class="admin-system__error" role="alert">
      <span class="admin-system__error-icon" aria-hidden="true">❌</span>
      <span class="admin-system__error-text">{{ error }}</span>
      <button
        type="button"
        class="admin-system__error-close"
        @click="error = null"
        aria-label="Fermer"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>

    <!-- ====================================================================
      GRILLE PRINCIPALE
    ==================================================================== -->
    <div class="admin-system__grid">
      <!-- ================================================================
        CARTE 1 — Informations système
      ================================================================= -->
      <section class="admin-system__card admin-system__card--info">
        <header class="admin-system__card-header">
          <h2 class="admin-system__card-title">
            <span aria-hidden="true">💻</span>
            Informations système
          </h2>
          <span v-if="systemInfo" class="admin-system__card-version">
            v{{ systemInfo.app_version }}
          </span>
        </header>

        <div class="admin-system__card-body">
          <div v-if="systemInfoLoading" class="admin-system__card-loading">
            <NexusSpinner size="sm" />
          </div>

          <div v-else-if="!systemInfo" class="admin-system__card-empty">
            Données indisponibles
          </div>

          <dl v-else class="admin-system__info-list">
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Application</dt>
              <dd class="admin-system__info-value">{{ systemInfo.app_name }}</dd>
            </div>
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Version</dt>
              <dd class="admin-system__info-value">{{ systemInfo.app_version }}</dd>
            </div>
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Build</dt>
              <dd class="admin-system__info-value">
                {{ formatDateTime(systemInfo.build_date) }}
              </dd>
            </div>
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Environnement</dt>
              <dd class="admin-system__info-value">
                <span
                  class="admin-system__env-badge"
                  :class="`admin-system__env-badge--${systemInfo.environment}`"
                >
                  {{ systemInfo.environment }}
                </span>
              </dd>
            </div>
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Debug</dt>
              <dd class="admin-system__info-value">
                {{ systemInfo.debug_mode ? '✅ Activé' : '⛔ Désactivé' }}
              </dd>
            </div>
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Plateforme</dt>
              <dd class="admin-system__info-value" :title="systemInfo.platform">
                {{ systemInfo.os_name }} {{ systemInfo.architecture }}
              </dd>
            </div>
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Hostname</dt>
              <dd class="admin-system__info-value">{{ systemInfo.hostname }}</dd>
            </div>
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Python</dt>
              <dd class="admin-system__info-value" :title="systemInfo.python_version">
                {{ truncate(systemInfo.python_version, 30) }}
              </dd>
            </div>
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Uptime</dt>
              <dd class="admin-system__info-value">
                {{ formatUptime(systemInfo.uptime_seconds) }}
              </dd>
            </div>
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Heure serveur</dt>
              <dd class="admin-system__info-value">
                {{ formatDateTime(systemInfo.server_time) }}
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <!-- ================================================================
        CARTE 2 — CPU
      ================================================================= -->
      <section class="admin-system__card admin-system__card--cpu">
        <header class="admin-system__card-header">
          <h2 class="admin-system__card-title">
            <span aria-hidden="true">🔥</span>
            CPU
          </h2>
          <span v-if="metrics" class="admin-system__card-badge">
            {{ metrics.cpu_cores }} cœurs
          </span>
        </header>

        <div class="admin-system__card-body">
          <div v-if="!metrics" class="admin-system__card-empty">—</div>
          <template v-else>
            <!-- Gauge CPU -->
            <div class="admin-system__gauge">
              <div class="admin-system__gauge-track">
                <div
                  class="admin-system__gauge-bar"
                  :class="getGaugeClass(metrics.cpu_percent)"
                  :style="{ width: `${metrics.cpu_percent}%` }"
                  role="progressbar"
                  :aria-valuenow="Math.round(metrics.cpu_percent)"
                  aria-valuemin="0"
                  aria-valuemax="100"
                />
              </div>
              <span class="admin-system__gauge-value">
                {{ metrics.cpu_percent.toFixed(1) }}%
              </span>
            </div>

            <!-- Détails CPU -->
            <dl class="admin-system__metrics-list">
              <div class="admin-system__metrics-row">
                <dt>Cœurs</dt>
                <dd>{{ metrics.cpu_cores }}</dd>
              </div>
              <div v-if="metrics.cpu_freq_current" class="admin-system__metrics-row">
                <dt>Fréquence</dt>
                <dd>{{ metrics.cpu_freq_current.toFixed(0) }} MHz</dd>
              </div>
              <div v-if="metrics.cpu_freq_min && metrics.cpu_freq_max" class="admin-system__metrics-row">
                <dt>Plage</dt>
                <dd>
                  {{ metrics.cpu_freq_min.toFixed(0) }} – {{ metrics.cpu_freq_max.toFixed(0) }} MHz
                </dd>
              </div>
            </dl>
          </template>
        </div>
      </section>

      <!-- ================================================================
        CARTE 3 — Mémoire
      ================================================================= -->
      <section class="admin-system__card admin-system__card--memory">
        <header class="admin-system__card-header">
          <h2 class="admin-system__card-title">
            <span aria-hidden="true">🧠</span>
            Mémoire
          </h2>
          <span v-if="metrics" class="admin-system__card-badge">
            {{ metrics.memory_percent.toFixed(1) }}%
          </span>
        </header>

        <div class="admin-system__card-body">
          <div v-if="!metrics" class="admin-system__card-empty">—</div>
          <template v-else>
            <!-- Gauge mémoire -->
            <div class="admin-system__gauge">
              <div class="admin-system__gauge-track">
                <div
                  class="admin-system__gauge-bar"
                  :class="getGaugeClass(metrics.memory_percent)"
                  :style="{ width: `${metrics.memory_percent}%` }"
                  role="progressbar"
                  :aria-valuenow="Math.round(metrics.memory_percent)"
                  aria-valuemin="0"
                  aria-valuemax="100"
                />
              </div>
              <span class="admin-system__gauge-value">
                {{ metrics.memory_percent.toFixed(1) }}%
              </span>
            </div>

            <dl class="admin-system__metrics-list">
              <div class="admin-system__metrics-row">
                <dt>Utilisée</dt>
                <dd>{{ formatFileSize(metrics.memory_used) }}</dd>
              </div>
              <div class="admin-system__metrics-row">
                <dt>Disponible</dt>
                <dd>{{ formatFileSize(metrics.memory_available) }}</dd>
              </div>
              <div class="admin-system__metrics-row">
                <dt>Totale</dt>
                <dd>{{ formatFileSize(metrics.memory_total) }}</dd>
              </div>
              <div class="admin-system__metrics-row">
                <dt>Processus</dt>
                <dd>{{ formatFileSize(metrics.process_memory) }}</dd>
              </div>
              <div class="admin-system__metrics-row">
                <dt>Threads</dt>
                <dd>{{ metrics.process_threads }}</dd>
              </div>
            </dl>
          </template>
        </div>
      </section>

      <!-- ================================================================
        CARTE 4 — Disque
      ================================================================= -->
      <section class="admin-system__card admin-system__card--disk">
        <header class="admin-system__card-header">
          <h2 class="admin-system__card-title">
            <span aria-hidden="true">💾</span>
            Disque
          </h2>
          <span v-if="metrics" class="admin-system__card-badge">
            {{ metrics.disk_percent.toFixed(1) }}%
          </span>
        </header>

        <div class="admin-system__card-body">
          <div v-if="!metrics" class="admin-system__card-empty">—</div>
          <template v-else>
            <div class="admin-system__gauge">
              <div class="admin-system__gauge-track">
                <div
                  class="admin-system__gauge-bar"
                  :class="getGaugeClass(metrics.disk_percent)"
                  :style="{ width: `${metrics.disk_percent}%` }"
                  role="progressbar"
                  :aria-valuenow="Math.round(metrics.disk_percent)"
                  aria-valuemin="0"
                  aria-valuemax="100"
                />
              </div>
              <span class="admin-system__gauge-value">
                {{ metrics.disk_percent.toFixed(1) }}%
              </span>
            </div>

            <dl class="admin-system__metrics-list">
              <div class="admin-system__metrics-row">
                <dt>Utilisé</dt>
                <dd>{{ formatFileSize(metrics.disk_used) }}</dd>
              </div>
              <div class="admin-system__metrics-row">
                <dt>Libre</dt>
                <dd>{{ formatFileSize(metrics.disk_free) }}</dd>
              </div>
              <div class="admin-system__metrics-row">
                <dt>Total</dt>
                <dd>{{ formatFileSize(metrics.disk_total) }}</dd>
              </div>
            </dl>
          </template>
        </div>
      </section>

      <!-- ================================================================
        CARTE 5 — Base de données
      ================================================================= -->
      <section class="admin-system__card admin-system__card--database">
        <header class="admin-system__card-header">
          <h2 class="admin-system__card-title">
            <span aria-hidden="true">🗄️</span>
            Base de données
          </h2>
          <span
            v-if="databaseStatus"
            class="admin-system__card-badge"
            :class="databaseStatus.connected ? 'admin-system__card-badge--success' : 'admin-system__card-badge--error'"
          >
            {{ databaseStatus.connected ? '✅ Connectée' : '❌ Hors ligne' }}
          </span>
        </header>

        <div class="admin-system__card-body">
          <div v-if="!databaseStatus" class="admin-system__card-empty">—</div>
          <dl v-else class="admin-system__info-list">
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">Moteur</dt>
              <dd class="admin-system__info-value">{{ databaseStatus.engine }}</dd>
            </div>
            <div class="admin-system__info-row">
              <dt class="admin-system__info-label">URL</dt>
              <dd class="admin-system__info-value admin-system__info-value--mono" :title="databaseStatus.url">
                {{ truncate(databaseStatus.url, 40) }}
              </dd>
            </div>
            <div v-if="databaseStatus.size_formatted" class="admin-system__info-row">
              <dt class="admin-system__info-label">Taille</dt>
              <dd class="admin-system__info-value">{{ databaseStatus.size_formatted }}</dd>
            </div>
          </dl>
        </div>
      </section>

      <!-- ================================================================
        CARTE 6 — Healthcheck
      ================================================================= -->
      <section class="admin-system__card admin-system__card--health">
        <header class="admin-system__card-header">
          <h2 class="admin-system__card-title">
            <span aria-hidden="true">❤️</span>
            Healthcheck
          </h2>
          <button
            type="button"
            class="admin-system__card-action"
            @click="runHealthCheck"
            :disabled="healthLoading"
            title="Relancer le healthcheck"
          >
            <span v-if="healthLoading" class="admin-system__spinner" aria-hidden="true">⟳</span>
            <span v-else aria-hidden="true">🧪</span>
          </button>
        </header>

        <div class="admin-system__card-body">
          <div v-if="healthLoading && !healthCheck" class="admin-system__card-loading">
            <NexusSpinner size="sm" />
          </div>

          <div v-else-if="!healthCheck" class="admin-system__card-empty">
            Aucune donnée
          </div>

          <div v-else class="admin-system__health">
            <div
              class="admin-system__health-global"
              :class="`admin-system__health-global--${healthCheck.status}`"
            >
              <span class="admin-system__health-global-icon">
                {{ healthCheck.status === 'healthy' ? '✅' : '❌' }}
              </span>
              <span class="admin-system__health-global-text">
                {{ healthCheck.status === 'healthy' ? 'Système sain' : 'Système en erreur' }}
              </span>
            </div>

            <ul class="admin-system__health-checks">
              <li
                v-for="(check, name) in healthCheck.checks"
                :key="name"
                class="admin-system__health-check"
                :class="`admin-system__health-check--${check.status}`"
              >
                <span class="admin-system__health-check-icon" aria-hidden="true">
                  {{ check.status === 'ok' ? '✅' : '❌' }}
                </span>
                <span class="admin-system__health-check-name">{{ name }}</span>
                <span class="admin-system__health-check-status">{{ check.status }}</span>
              </li>
            </ul>

            <p class="admin-system__health-timestamp">
              Dernière vérification : {{ formatDateTime(healthCheck.timestamp) }}
            </p>
          </div>
        </div>
      </section>

      <!-- ================================================================
        CARTE 7 — Statistiques NexusDL
      ================================================================= -->
      <section class="admin-system__card admin-system__card--stats">
        <header class="admin-system__card-header">
          <h2 class="admin-system__card-title">
            <span aria-hidden="true">📊</span>
            Statistiques
          </h2>
        </header>

        <div class="admin-system__card-body">
          <div class="admin-system__stats-grid">
            <div class="admin-system__stat-tile admin-system__stat-tile--primary">
              <span class="admin-system__stat-tile-value">{{ stats.total_jobs || 0 }}</span>
              <span class="admin-system__stat-tile-label">Jobs totaux</span>
            </div>
            <div class="admin-system__stat-tile admin-system__stat-tile--info">
              <span class="admin-system__stat-tile-value">{{ stats.active_jobs || 0 }}</span>
              <span class="admin-system__stat-tile-label">Jobs actifs</span>
            </div>
            <div class="admin-system__stat-tile admin-system__stat-tile--success">
              <span class="admin-system__stat-tile-value">{{ stats.library_count || 0 }}</span>
              <span class="admin-system__stat-tile-label">Bibliothèque</span>
            </div>
            <div class="admin-system__stat-tile admin-system__stat-tile--warning">
              <span class="admin-system__stat-tile-value">{{ stats.cache_size || 0 }}</span>
              <span class="admin-system__stat-tile-label">Cache</span>
            </div>
            <div class="admin-system__stat-tile">
              <span class="admin-system__stat-tile-value">{{ metrics?.connections_count || 0 }}</span>
              <span class="admin-system__stat-tile-label">Connexions</span>
            </div>
            <div class="admin-system__stat-tile">
              <span class="admin-system__stat-tile-value">{{ metrics?.process_open_files || 0 }}</span>
              <span class="admin-system__stat-tile-label">Fichiers ouverts</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ================================================================
        CARTE 8 — Actions système
      ================================================================= -->
      <section class="admin-system__card admin-system__card--actions">
        <header class="admin-system__card-header">
          <h2 class="admin-system__card-title">
            <span aria-hidden="true">🛠️</span>
            Actions système
          </h2>
        </header>

        <div class="admin-system__card-body">
          <div class="admin-system__actions-grid">
            <button
              type="button"
              class="admin-system__action-btn admin-system__action-btn--warning"
              @click="clearCache"
              :disabled="actionLoading"
              aria-label="Vider le cache"
              title="Vider le cache (pages + images)"
            >
              <span aria-hidden="true">🗑️</span>
              <span>Vider le cache</span>
            </button>

            <button
              type="button"
              class="admin-system__action-btn admin-system__action-btn--danger"
              @click="clearTemp"
              :disabled="actionLoading"
              aria-label="Vider les fichiers temporaires"
              title="Vider les fichiers temporaires"
            >
              <span aria-hidden="true">🧹</span>
              <span>Vider les temporaires</span>
            </button>

            <button
              type="button"
              class="admin-system__action-btn admin-system__action-btn--info"
              @click="showResourceLimits"
              :disabled="actionLoading"
              aria-label="Afficher les limites de ressources"
              title="Limites de ressources du conteneur"
            >
              <span aria-hidden="true">📋</span>
              <span>Limites de ressources</span>
            </button>

            <button
              type="button"
              class="admin-system__action-btn admin-system__action-btn--neutral"
              @click="exportMetrics"
              aria-label="Exporter les métriques"
              title="Télécharger un rapport JSON"
            >
              <span aria-hidden="true">📥</span>
              <span>Exporter</span>
            </button>
          </div>

          <!-- Limites de ressources (si affichées) -->
          <div v-if="resourceLimits" class="admin-system__resource-limits">
            <h4 class="admin-system__resource-limits-title">Limites de ressources</h4>
            <dl class="admin-system__metrics-list">
              <div class="admin-system__metrics-row">
                <dt>CPU</dt>
                <dd>{{ resourceLimits.cpu_limit ? `${resourceLimits.cpu_limit} cœurs` : 'Illimité' }}</dd>
              </div>
              <div class="admin-system__metrics-row">
                <dt>Mémoire</dt>
                <dd>
                  {{
                    resourceLimits.memory_limit
                      ? formatFileSize(resourceLimits.memory_limit)
                      : 'Illimité'
                  }}
                </dd>
              </div>
              <div class="admin-system__metrics-row">
                <dt>Disque</dt>
                <dd>
                  {{
                    resourceLimits.disk_limit
                      ? formatFileSize(resourceLimits.disk_limit)
                      : 'Illimité'
                  }}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </section>
    </div>

    <!-- ====================================================================
      PIED DE PAGE
    ==================================================================== -->
    <footer class="admin-system__footer">
      <span class="admin-system__footer-info">
        <span v-if="lastUpdated">
          Dernière mise à jour : {{ formatDateTime(lastUpdated) }}
        </span>
        <span v-if="autoRefreshEnabled" class="admin-system__footer-auto">
          · Auto-refresh actif ({{ autoRefreshInterval / 1000 }}s)
        </span>
      </span>
      <span class="admin-system__footer-build">
        NexusDL {{ systemInfo?.app_version || '2.0.0' }} — GNU GPL v3.0
      </span>
    </footer>

    <!-- ====================================================================
      MODALE DE CONFIRMATION
    ==================================================================== -->
    <NexusModal
      v-model="showConfirmModal"
      :title="confirmModalTitle"
      size="sm"
      confirmable
      :confirm-text="confirmModalConfirmText"
      :cancel-text="'Annuler'"
      :confirm-variant="confirmModalVariant"
      :loading="actionLoading"
      @confirm="executeConfirmedAction"
      @cancel="cancelConfirmedAction"
    >
      <p>{{ confirmModalMessage }}</p>
    </NexusModal>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusSelect from '@/components/common/NexusSelect.vue'
import NexusModal from '@/components/common/NexusModal.vue'
import { formatFileSize, formatDateTime as fmtDateTime, truncate } from '@/utils/formatters'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables
// ==========================================================================

const api = useApi()
const toast = useToast()

// ==========================================================================
//  État réactif
// ==========================================================================

const systemInfo = ref(null)
const systemInfoLoading = ref(false)

const metrics = ref(null)
const metricsLoading = ref(false)

const databaseStatus = ref(null)
const databaseLoading = ref(false)

const healthCheck = ref(null)
const healthLoading = ref(false)

const resourceLimits = ref(null)

const stats = ref({
  total_jobs: 0,
  active_jobs: 0,
  library_count: 0,
  cache_size: 0,
})

const loading = ref(false)
const actionLoading = ref(false)
const error = ref(null)
const lastUpdated = ref(null)

const autoRefreshEnabled = ref(false)
const autoRefreshInterval = ref(5000)

// Modale de confirmation
const showConfirmModal = ref(false)
const confirmModalTitle = ref('')
const confirmModalMessage = ref('')
const confirmModalConfirmText = ref('Confirmer')
const confirmModalVariant = ref('primary')
let pendingAction = null

let autoRefreshTimer = null
let metricsHistory = []

// ==========================================================================
//  Options
// ==========================================================================

const autoRefreshOptions = [
  { value: 2000, label: '2 secondes' },
  { value: 5000, label: '5 secondes' },
  { value: 10000, label: '10 secondes' },
  { value: 30000, label: '30 secondes' },
  { value: 60000, label: '1 minute' },
]

// ==========================================================================
//  Computed
// ==========================================================================

/**
 * Classe du statut global.
 */
const globalStatusClass = computed(() => {
  if (error.value) return 'error'
  if (!metrics.value) return 'unknown'
  const load = Math.max(
    metrics.value.cpu_percent,
    metrics.value.memory_percent,
    metrics.value.disk_percent
  )
  if (load > 90) return 'critical'
  if (load > 75) return 'warning'
  return 'ok'
})

/**
 * Libellé du statut global.
 */
const globalStatusLabel = computed(() => {
  const cls = globalStatusClass.value
  const map = {
    ok: '✅ Opérationnel',
    warning: '⚠️ Charge élevée',
    critical: '🔥 Critique',
    error: '❌ Erreur',
    unknown: '⏳ Chargement...',
  }
  return map[cls] || 'Inconnu'
})

// ==========================================================================
//  Méthodes — Récupération des données
// ==========================================================================

/**
 * Récupère les informations système.
 */
async function fetchSystemInfo() {
  systemInfoLoading.value = true
  try {
    const response = await api.get('/system/info')
    systemInfo.value = response.data || response
  } catch (err) {
    console.warn('Erreur chargement system/info:', err.message)
  } finally {
    systemInfoLoading.value = false
  }
}

/**
 * Récupère les métriques système.
 */
async function fetchMetrics() {
  metricsLoading.value = true
  try {
    const response = await api.get('/system/metrics')
    const data = response.data || response

    // Ajouter à l'historique (limité à 60 points)
    metricsHistory.push({
      timestamp: Date.now(),
      cpu: data.cpu_percent,
      memory: data.memory_percent,
    })
    if (metricsHistory.length > 60) {
      metricsHistory.shift()
    }

    metrics.value = data
  } catch (err) {
    console.warn('Erreur chargement system/metrics:', err.message)
  } finally {
    metricsLoading.value = false
  }
}

/**
 * Récupère le statut de la base de données.
 */
async function fetchDatabaseStatus() {
  databaseLoading.value = true
  try {
    const response = await api.get('/system/database')
    databaseStatus.value = response.data || response
  } catch (err) {
    console.warn('Erreur chargement system/database:', err.message)
  } finally {
    databaseLoading.value = false
  }
}

/**
 * Récupère les statistiques rapides.
 */
async function fetchStats() {
  try {
    // Utiliser les métriques système comme source
    const response = await api.get('/system/metrics')
    const data = response.data || response
    stats.value = {
      total_jobs: data.total_jobs || 0,
      active_jobs: data.active_jobs || 0,
      library_count: data.library_count || 0,
      cache_size: data.cache_size || 0,
    }
  } catch (err) {
    console.warn('Erreur chargement statistiques:', err.message)
  }
}

/**
 * Lance le healthcheck.
 */
async function runHealthCheck() {
  healthLoading.value = true
  try {
    const response = await api.get('/system/health')
    healthCheck.value = response.data || response
  } catch (err) {
    console.warn('Erreur healthcheck:', err.message)
    healthCheck.value = {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      checks: { api: { status: 'error', error: err.message } },
    }
  } finally {
    healthLoading.value = false
  }
}

/**
 * Récupère les limites de ressources (à la demande).
 */
async function showResourceLimits() {
  actionLoading.value = true
  try {
    const response = await api.get('/system/resources')
    resourceLimits.value = response.data || response
    toast.info('Limites de ressources chargées', '📋')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    actionLoading.value = false
  }
}

/**
 * Rafraîchit toutes les données.
 */
async function refreshAll() {
  loading.value = true
  error.value = null
  try {
    await Promise.allSettled([
      fetchSystemInfo(),
      fetchMetrics(),
      fetchDatabaseStatus(),
      fetchStats(),
    ])
    lastUpdated.value = new Date().toISOString()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

// ==========================================================================
//  Méthodes — Actions système
// ==========================================================================

/**
 * Vide le cache.
 */
function clearCache() {
  confirmModalTitle.value = 'Vider le cache'
  confirmModalMessage.value =
    'Êtes-vous sûr de vouloir vider tout le cache (pages et images) ? Cette action est irréversible.'
  confirmModalConfirmText.value = 'Vider le cache'
  confirmModalVariant.value = 'warning'
  pendingAction = async () => {
    try {
      const response = await api.delete('/admin/cache')
      const cleared = response.cleared_count || response.data?.cleared_count || 0
      toast.success(`${cleared} éléments supprimés du cache`, '🗑️')
    } catch (err) {
      toast.error(`Erreur : ${err.message}`, '❌')
    }
  }
  showConfirmModal.value = true
}

/**
 * Vide les fichiers temporaires.
 */
function clearTemp() {
  confirmModalTitle.value = 'Vider les fichiers temporaires'
  confirmModalMessage.value =
    'Êtes-vous sûr de vouloir supprimer tous les fichiers temporaires ? Les téléchargements incomplets seront perdus.'
  confirmModalConfirmText.value = 'Supprimer'
  confirmModalVariant.value = 'error'
  pendingAction = async () => {
    try {
      await api.delete('/admin/downloads', { params: { confirm: true } })
      toast.success('Fichiers temporaires supprimés', '🧹')
    } catch (err) {
      toast.error(`Erreur : ${err.message}`, '❌')
    }
  }
  showConfirmModal.value = true
}

/**
 * Exécute l'action confirmée.
 */
async function executeConfirmedAction() {
  if (!pendingAction) return
  actionLoading.value = true
  try {
    await pendingAction()
  } finally {
    actionLoading.value = false
    pendingAction = null
    showConfirmModal.value = false
  }
}

/**
 * Annule l'action.
 */
function cancelConfirmedAction() {
  pendingAction = null
  showConfirmModal.value = false
}

/**
 * Exporte les métriques en JSON.
 */
function exportMetrics() {
  const data = {
    exported_at: new Date().toISOString(),
    system_info: systemInfo.value,
    metrics: metrics.value,
    database: databaseStatus.value,
    health: healthCheck.value,
    stats: stats.value,
    history: metricsHistory,
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `nexusdl-system-${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  toast.success('Rapport exporté', '📥')
}

// ==========================================================================
//  Méthodes — Auto-refresh
// ==========================================================================

function toggleAutoRefresh() {
  autoRefreshEnabled.value = !autoRefreshEnabled.value
  if (autoRefreshEnabled.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

function startAutoRefresh() {
  stopAutoRefresh()
  autoRefreshTimer = setInterval(() => {
    if (!loading.value && !actionLoading.value) {
      fetchMetrics()
      fetchStats()
    }
  }, autoRefreshInterval.value)
}

function stopAutoRefresh() {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

// ==========================================================================
//  Méthodes — Formatage & helpers
// ==========================================================================

/**
 * Formate un uptime en secondes.
 * @param {number} seconds
 * @returns {string}
 */
function formatUptime(seconds) {
  if (!seconds || seconds < 0) return '—'
  const d = dayjs.duration(seconds, 'seconds')
  const days = Math.floor(d.asDays())
  const hours = d.hours()
  const minutes = d.minutes()
  const parts = []
  if (days > 0) parts.push(`${days}j`)
  if (hours > 0) parts.push(`${hours}h`)
  if (minutes > 0) parts.push(`${minutes}m`)
  return parts.join(' ') || `${Math.round(seconds)}s`
}

/**
 * Formate une date.
 * @param {string} date
 * @returns {string}
 */
function formatDateTime(date) {
  if (!date) return '—'
  try {
    const d = dayjs(date)
    if (!d.isValid()) return date
    return d.format('DD/MM/YYYY HH:mm:ss')
  } catch (_) {
    return date
  }
}

/**
 * Retourne la classe de gauge selon le pourcentage.
 * @param {number} percent
 * @returns {string}
 */
function getGaugeClass(percent) {
  if (percent >= 90) return 'admin-system__gauge-bar--critical'
  if (percent >= 75) return 'admin-system__gauge-bar--warning'
  return 'admin-system__gauge-bar--ok'
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  await refreshAll()
  await runHealthCheck()
})

onUnmounted(() => {
  stopAutoRefresh()
})

watch(autoRefreshInterval, () => {
  if (autoRefreshEnabled.value) {
    startAutoRefresh()
  }
})
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.admin-system {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

// ==========================================================================
//  Header
// ==========================================================================

.admin-system__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.admin-system__header-left {
  flex: 1;
  min-width: 200px;
}

.admin-system__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.admin-system__subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.admin-system__header-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

// ==========================================================================
//  Statut global
// ==========================================================================

.admin-system__global-status {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.8rem;
  border-radius: var(--radius-full, 9999px);
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid var(--color-border, #1a2538);
  background: var(--color-bg-card, #1a2538);
  white-space: nowrap;

  &--ok {
    border-color: rgba(76, 175, 80, 0.3);
    background: rgba(76, 175, 80, 0.1);
    color: #4caf50;
    .admin-system__global-status-dot { background: #4caf50; }
  }
  &--warning {
    border-color: rgba(255, 152, 0, 0.3);
    background: rgba(255, 152, 0, 0.1);
    color: #ff9800;
    .admin-system__global-status-dot { background: #ff9800; }
  }
  &--critical {
    border-color: rgba(244, 67, 54, 0.3);
    background: rgba(244, 67, 54, 0.1);
    color: #f44336;
    .admin-system__global-status-dot { background: #f44336; animation: systemPulse 1s infinite; }
  }
  &--error {
    border-color: rgba(244, 67, 54, 0.3);
    background: rgba(244, 67, 54, 0.1);
    color: #f44336;
    .admin-system__global-status-dot { background: #f44336; }
  }
  &--unknown {
    color: var(--color-text-muted, #6a7a9a);
    .admin-system__global-status-dot { background: #6a7a9a; }
  }
}

.admin-system__global-status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

@keyframes systemPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

// ==========================================================================
//  Boutons
// ==========================================================================

.admin-system__btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 0.7rem;
  font-size: 0.75rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;

  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-border-light, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &--auto.admin-system__btn--active {
    background: rgba(0, 212, 255, 0.15);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-primary, #00d4ff);
  }

  &--refresh:hover:not(:disabled) {
    border-color: var(--color-info, #2196f3);
    color: var(--color-info, #2196f3);
  }
}

.admin-system__spinner {
  display: inline-block;
  animation: systemSpin 0.8s linear infinite;
}

@keyframes systemSpin {
  to { transform: rotate(360deg); }
}

// ==========================================================================
//  Barre d'erreur
// ==========================================================================

.admin-system__error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid var(--color-error, #f44336);
  border-radius: var(--radius-md, 8px);
  color: var(--color-error, #f44336);
  font-size: 0.85rem;
}

.admin-system__error-icon {
  flex-shrink: 0;
}

.admin-system__error-text {
  flex: 1;
}

.admin-system__error-close {
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0 0.3rem;
  border-radius: var(--radius-sm, 4px);
  &:hover {
    background: rgba(244, 67, 54, 0.15);
  }
}

// ==========================================================================
//  Grille principale
// ==========================================================================

.admin-system__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1rem;
}

// ==========================================================================
//  Cartes
// ==========================================================================

.admin-system__card {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
  transition: border-color 0.15s ease;

  &:hover {
    border-color: var(--color-border-light, #253254);
  }

  &--info { border-top: 3px solid #2196f3; }
  &--cpu { border-top: 3px solid #f44336; }
  &--memory { border-top: 3px solid #9c27b0; }
  &--disk { border-top: 3px solid #ff9800; }
  &--database { border-top: 3px solid #00bcd4; }
  &--health { border-top: 3px solid #4caf50; }
  &--stats { border-top: 3px solid #3f51b5; }
  &--actions { border-top: 3px solid #607d8b; }
}

.admin-system__card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.6rem 0.85rem;
  background: var(--color-bg-secondary, #141a2b);
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.admin-system__card-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.admin-system__card-version {
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

.admin-system__card-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.15rem 0.5rem;
  font-size: 0.65rem;
  font-weight: 600;
  border-radius: var(--radius-sm, 4px);
  background: var(--color-bg-card, #1a2538);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);

  &--success {
    background: rgba(76, 175, 80, 0.15);
    color: #4caf50;
    border-color: rgba(76, 175, 80, 0.3);
  }

  &--error {
    background: rgba(244, 67, 54, 0.15);
    color: #f44336;
    border-color: rgba(244, 67, 54, 0.3);
  }
}

.admin-system__card-action {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: var(--radius-sm, 4px);
  font-size: 0.9rem;
  transition: all 0.15s ease;

  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

.admin-system__card-body {
  padding: 0.75rem 0.85rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.admin-system__card-loading,
.admin-system__card-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80px;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.8rem;
}

// ==========================================================================
//  Info list (définitions)
// ==========================================================================

.admin-system__info-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin: 0;
}

.admin-system__info-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.2rem 0;
  border-bottom: 1px solid var(--color-border, #1a2538);
  font-size: 0.75rem;

  &:last-child {
    border-bottom: none;
  }
}

.admin-system__info-label {
  color: var(--color-text-muted, #6a7a9a);
  font-size: 0.7rem;
  flex-shrink: 0;
}

.admin-system__info-value {
  color: var(--color-text-secondary, #b0c0d8);
  text-align: right;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  &--mono {
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 0.7rem;
  }
}

.admin-system__env-badge {
  display: inline-block;
  padding: 0.1rem 0.4rem;
  font-size: 0.6rem;
  font-weight: 600;
  border-radius: var(--radius-sm, 4px);
  text-transform: uppercase;
  letter-spacing: 0.05em;

  &--production {
    background: rgba(76, 175, 80, 0.15);
    color: #4caf50;
  }

  &--development {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
  }

  &--test {
    background: rgba(33, 150, 243, 0.15);
    color: #2196f3;
  }
}

// ==========================================================================
//  Gauge (barres de progression)
// ==========================================================================

.admin-system__gauge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.admin-system__gauge-track {
  flex: 1;
  height: 8px;
  background: var(--color-bg-input, #1e2a40);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
}

.admin-system__gauge-bar {
  height: 100%;
  border-radius: var(--radius-full, 9999px);
  transition: width 0.4s ease, background 0.3s ease;

  &--ok { background: linear-gradient(90deg, #4caf50, #66bb6a); }
  &--warning { background: linear-gradient(90deg, #ff9800, #ffb74d); }
  &--critical { background: linear-gradient(90deg, #f44336, #ef5350); }
}

.admin-system__gauge-value {
  font-size: 0.8rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--color-text-primary, #e8edf5);
  min-width: 45px;
  text-align: right;
}

// ==========================================================================
//  Metrics list
// ==========================================================================

.admin-system__metrics-list {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  margin: 0;
}

.admin-system__metrics-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.75rem;
  padding: 0.1rem 0;

  dt {
    color: var(--color-text-muted, #6a7a9a);
    font-size: 0.7rem;
  }

  dd {
    margin: 0;
    color: var(--color-text-secondary, #b0c0d8);
    font-variant-numeric: tabular-nums;
  }
}

// ==========================================================================
//  Healthcheck
// ==========================================================================

.admin-system__health {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.admin-system__health-global {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.7rem;
  border-radius: var(--radius-md, 8px);
  font-size: 0.85rem;
  font-weight: 600;

  &--healthy {
    background: rgba(76, 175, 80, 0.1);
    border: 1px solid rgba(76, 175, 80, 0.3);
    color: #4caf50;
  }

  &--unhealthy {
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid rgba(244, 67, 54, 0.3);
    color: #f44336;
  }
}

.admin-system__health-global-icon {
  font-size: 1.1rem;
}

.admin-system__health-checks {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.admin-system__health-check {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm, 4px);
  font-size: 0.75rem;
  background: var(--color-bg-secondary, #141a2b);
  border-left: 3px solid var(--color-border, #1a2538);

  &--ok {
    border-left-color: #4caf50;
  }

  &--error {
    border-left-color: #f44336;
  }
}

.admin-system__health-check-icon {
  font-size: 0.8rem;
}

.admin-system__health-check-name {
  flex: 1;
  color: var(--color-text-secondary, #b0c0d8);
  text-transform: capitalize;
}

.admin-system__health-check-status {
  font-size: 0.65rem;
  color: var(--color-text-muted, #6a7a9a);
  text-transform: uppercase;
}

.admin-system__health-timestamp {
  margin: 0;
  font-size: 0.65rem;
  color: var(--color-text-muted, #6a7a9a);
  font-style: italic;
  text-align: right;
}

// ==========================================================================
//  Statistiques (tuiles)
// ==========================================================================

.admin-system__stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 0.5rem;
}

.admin-system__stat-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.6rem 0.5rem;
  border-radius: var(--radius-md, 8px);
  background: var(--color-bg-secondary, #141a2b);
  border: 1px solid var(--color-border, #1a2538);
  text-align: center;

  &--primary { border-left: 3px solid var(--color-primary, #00d4ff); }
  &--info { border-left: 3px solid #2196f3; }
  &--success { border-left: 3px solid #4caf50; }
  &--warning { border-left: 3px solid #ff9800; }
}

.admin-system__stat-tile-value {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.admin-system__stat-tile-label {
  margin-top: 0.1rem;
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #6a7a9a);
}

// ==========================================================================
//  Actions système
// ==========================================================================

.admin-system__actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.5rem;
}

.admin-system__action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.6rem 0.8rem;
  font-size: 0.75rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    border-color: var(--color-border-light, #253254);
    color: var(--color-text-primary, #e8edf5);
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &--warning:hover:not(:disabled) {
    border-color: #ff9800;
    color: #ff9800;
  }

  &--danger:hover:not(:disabled) {
    border-color: #f44336;
    color: #f44336;
  }

  &--info:hover:not(:disabled) {
    border-color: #2196f3;
    color: #2196f3;
  }

  &--neutral:hover:not(:disabled) {
    border-color: #607d8b;
    color: #90a4ae;
  }
}

.admin-system__resource-limits {
  margin-top: 0.5rem;
  padding: 0.5rem 0.7rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.admin-system__resource-limits-title {
  margin: 0 0 0.4rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary, #b0c0d8);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

// ==========================================================================
//  Footer
// ==========================================================================

.admin-system__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.admin-system__footer-info {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.admin-system__footer-auto {
  color: var(--color-primary, #00d4ff);
  font-weight: 500;
}

.admin-system__footer-build {
  font-style: italic;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 768px) {
  .admin-system__header {
    flex-direction: column;
  }

  .admin-system__header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .admin-system__grid {
    grid-template-columns: 1fr;
  }

  .admin-system__stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .admin-system__actions-grid {
    grid-template-columns: 1fr;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .admin-system__card {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-system__card-header {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-system__card-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .admin-system__info-row,
  .admin-system__metrics-row {
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-system__info-label,
  .admin-system__metrics-row dt {
    color: var(--color-text-muted, #7a8a9a);
  }

  .admin-system__info-value,
  .admin-system__metrics-row dd {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .admin-system__gauge-track {
    background: var(--color-bg-input, #f0f2f5);
  }

  .admin-system__gauge-value {
    color: var(--color-text-primary, #1a1a2e);
  }

  .admin-system__stat-tile {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .admin-system__stat-tile-value {
    color: var(--color-text-primary, #1a1a2e);
  }

  .admin-system__health-check {
    background: var(--color-bg-secondary, #e9ecf2);
  }

  .admin-system__health-check-name {
    color: var(--color-text-secondary, #3d4a5c);
  }

  .admin-system__action-btn {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
    color: var(--color-text-secondary, #3d4a5c);

    &:hover:not(:disabled) {
      background: var(--color-bg-hover, #e3e8ef);
      color: var(--color-text-primary, #1a1a2e);
    }
  }
}
</style>
