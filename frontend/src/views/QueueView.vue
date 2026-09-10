<!-- ==========================================================================
  NexusDL 2.0 - Queue View (version complète)
  Fichier : frontend/src/views/QueueView.vue
  Description : Page de gestion de la file d'attente des téléchargements.
                Affiche les jobs en cours, en attente, terminés et échoués,
                avec statistiques, filtres, actions (pause, reprise, annulation,
                suppression), logs détaillés et progression temps réel via
                WebSocket/polling.
  Version : 2.0.0
  Licence : GNU GPL v3.0
========================================================================== -->

<template>
  <div class="queue-view">
    <!-- ====================================================================
      EN-TÊTE
    ==================================================================== -->
    <header class="queue-view__header">
      <div class="queue-view__header-left">
        <h1 class="queue-view__title">
          <span aria-hidden="true">⏳</span>
          File d'attente
        </h1>
        <p class="queue-view__subtitle">
          Suivez et gérez vos téléchargements en temps réel
        </p>
      </div>

      <div class="queue-view__header-right">
        <!-- Connexion WebSocket -->
        <div
          class="queue-view__ws-status"
          :class="`queue-view__ws-status--${wsConnected ? 'connected' : 'disconnected'}`"
          :title="wsConnected ? 'Connecté au serveur' : 'Déconnecté'"
        >
          <span class="queue-view__ws-dot" aria-hidden="true" />
          <span class="queue-view__ws-text">
            {{ wsConnected ? 'En direct' : 'Hors ligne' }}
          </span>
        </div>

        <!-- Auto-refresh -->
        <button
          type="button"
          class="queue-view__btn"
          :class="{ 'queue-view__btn--active': autoRefreshEnabled }"
          @click="toggleAutoRefresh"
          :disabled="wsConnected"
          :title="wsConnected ? 'WebSocket actif' : (autoRefreshEnabled ? 'Désactiver l\'auto-refresh' : 'Activer l\'auto-refresh')"
        >
          <span aria-hidden="true">{{ autoRefreshEnabled ? '⏸️' : '▶️' }}</span>
          Auto
        </button>

        <!-- Rafraîchir -->
        <button
          type="button"
          class="queue-view__btn queue-view__btn--refresh"
          :disabled="loading"
          @click="refreshJobs"
          aria-label="Rafraîchir la file d'attente"
          title="Rafraîchir"
        >
          <span v-if="loading" class="queue-view__spinner" aria-hidden="true">⟳</span>
          <span v-else aria-hidden="true">↻</span>
          Rafraîchir
        </button>

        <!-- Actions globales -->
        <button
          v-if="activeJobsCount > 0"
          type="button"
          class="queue-view__btn queue-view__btn--warning"
          @click="togglePauseAll"
          :title="isPausedAll ? 'Reprendre tous les jobs' : 'Mettre en pause tous les jobs'"
        >
          <span aria-hidden="true">{{ isPausedAll ? '▶️' : '⏸️' }}</span>
          {{ isPausedAll ? 'Reprendre' : 'Pause' }}
        </button>

        <button
          v-if="activeJobsCount > 0"
          type="button"
          class="queue-view__btn queue-view__btn--danger"
          @click="confirmCancelAll"
          aria-label="Annuler tous les jobs actifs"
          title="Tout annuler"
        >
          <span aria-hidden="true">🚫</span>
          Tout annuler
        </button>

        <button
          v-if="completedJobs.length > 0"
          type="button"
          class="queue-view__btn queue-view__btn--neutral"
          @click="confirmClearCompleted"
          aria-label="Nettoyer les jobs terminés"
          title="Nettoyer"
        >
          <span aria-hidden="true">🧹</span>
          Nettoyer
        </button>
      </div>
    </header>

    <!-- ====================================================================
      BARRE D'ERREUR
    ==================================================================== -->
    <div v-if="error" class="queue-view__error" role="alert">
      <span class="queue-view__error-icon" aria-hidden="true">❌</span>
      <span class="queue-view__error-text">{{ error }}</span>
      <button
        type="button"
        class="queue-view__error-close"
        @click="error = null"
        aria-label="Fermer"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>

    <!-- ====================================================================
      STATISTIQUES
    ==================================================================== -->
    <div class="queue-view__stats">
      <div class="queue-view__stat">
        <span class="queue-view__stat-value">{{ totalJobs }}</span>
        <span class="queue-view__stat-label">Total</span>
      </div>
      <div class="queue-view__stat queue-view__stat--pending">
        <span class="queue-view__stat-value">{{ statsCount.pending }}</span>
        <span class="queue-view__stat-label">En attente</span>
      </div>
      <div class="queue-view__stat queue-view__stat--running">
        <span class="queue-view__stat-value">{{ statsCount.running }}</span>
        <span class="queue-view__stat-label">En cours</span>
      </div>
      <div class="queue-view__stat queue-view__stat--completed">
        <span class="queue-view__stat-value">{{ statsCount.completed }}</span>
        <span class="queue-view__stat-label">Terminés</span>
      </div>
      <div class="queue-view__stat queue-view__stat--failed">
        <span class="queue-view__stat-value">{{ statsCount.failed }}</span>
        <span class="queue-view__stat-label">Échecs</span>
      </div>
      <div class="queue-view__stat queue-view__stat--cancelled">
        <span class="queue-view__stat-value">{{ statsCount.cancelled }}</span>
        <span class="queue-view__stat-label">Annulés</span>
      </div>
      <div class="queue-view__stat queue-view__stat--filtered">
        <span class="queue-view__stat-value">{{ filteredJobs.length }}</span>
        <span class="queue-view__stat-label">Affichés</span>
      </div>
    </div>

    <!-- ====================================================================
      PROGRESSION GLOBALE
    ==================================================================== -->
    <div
      v-if="activeJobsCount > 0"
      class="queue-view__global-progress"
    >
      <div class="queue-view__global-progress-info">
        <span class="queue-view__global-progress-label">
          Progression globale ({{ activeJobsCount }} job(s) actif(s))
        </span>
        <span class="queue-view__global-progress-value">
          {{ overallProgress.toFixed(0) }}%
        </span>
      </div>
      <div class="queue-view__global-progress-track">
        <div
          class="queue-view__global-progress-bar"
          :style="{ width: `${overallProgress}%` }"
          role="progressbar"
          :aria-valuenow="overallProgress"
          aria-valuemin="0"
          aria-valuemax="100"
        />
      </div>
    </div>

    <!-- ====================================================================
      FILTRES ET RECHERCHE
    ==================================================================== -->
    <div class="queue-view__toolbar">
      <!-- Recherche -->
      <div class="queue-view__search-wrapper">
        <span class="queue-view__search-icon" aria-hidden="true">🔍</span>
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          type="text"
          class="queue-view__search-input"
          placeholder="Rechercher un job (titre, URL)..."
          aria-label="Rechercher dans la file d'attente"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="queue-view__search-clear"
          @click="searchQuery = ''"
          aria-label="Effacer la recherche"
        >
          <span aria-hidden="true">&times;</span>
        </button>
      </div>

      <!-- Filtres par statut -->
      <div class="queue-view__filters">
        <button
          v-for="filter in statusFilters"
          :key="filter.value"
          type="button"
          class="queue-view__filter-btn"
          :class="{ 'queue-view__filter-btn--active': statusFilter === filter.value }"
          @click="statusFilter = filter.value"
          :aria-pressed="statusFilter === filter.value"
          :title="`Filtrer : ${filter.label}`"
        >
          <span aria-hidden="true">{{ filter.icon }}</span>
          {{ filter.label }}
          <span v-if="filter.count !== undefined" class="queue-view__filter-count">
            {{ filter.count }}
          </span>
        </button>
      </div>

      <!-- Tri -->
      <select
        v-model="sortBy"
        class="queue-view__select"
        aria-label="Trier les jobs"
      >
        <option value="created-desc">Plus récents</option>
        <option value="created-asc">Plus anciens</option>
        <option value="progress-desc">Progression (desc)</option>
        <option value="progress-asc">Progression (asc)</option>
        <option value="title-asc">Titre (A-Z)</option>
      </select>
    </div>

    <!-- ====================================================================
      ACTIONS GROUPÉES
    ==================================================================== -->
    <Transition name="queue-view-slide">
      <div v-if="selectedIds.length > 0" class="queue-view__bulk-actions">
        <span class="queue-view__bulk-info">
          {{ selectedIds.length }} job(s) sélectionné(s)
        </span>
        <div class="queue-view__bulk-buttons">
          <button
            type="button"
            class="queue-view__bulk-btn queue-view__bulk-btn--warning"
            @click="bulkPause"
            :disabled="bulkLoading"
          >
            ⏸️ Pause
          </button>
          <button
            type="button"
            class="queue-view__bulk-btn queue-view__bulk-btn--success"
            @click="bulkResume"
            :disabled="bulkLoading"
          >
            ▶️ Reprendre
          </button>
          <button
            type="button"
            class="queue-view__bulk-btn queue-view__bulk-btn--danger"
            @click="bulkCancel"
            :disabled="bulkLoading"
          >
            🚫 Annuler
          </button>
          <button
            type="button"
            class="queue-view__bulk-btn queue-view__bulk-btn--neutral"
            @click="clearSelection"
          >
            ✖ Annuler
          </button>
        </div>
      </div>
    </Transition>

    <!-- ====================================================================
      CONTENU PRINCIPAL — Liste des jobs
    ==================================================================== -->
    <div class="queue-view__body">
      <!-- État de chargement -->
      <div v-if="loading && jobs.length === 0" class="queue-view__loading">
        <NexusSpinner size="lg" variant="gradient" label="Chargement de la file d'attente..." />
      </div>

      <!-- État vide -->
      <div v-else-if="filteredJobs.length === 0" class="queue-view__empty">
        <span class="queue-view__empty-icon" aria-hidden="true">📭</span>
        <h2 class="queue-view__empty-title">
          {{ jobs.length === 0 ? 'File d\'attente vide' : 'Aucun résultat' }}
        </h2>
        <p class="queue-view__empty-text">
          {{
            jobs.length === 0
              ? 'Lancez un téléchargement depuis la page de recherche pour le voir apparaître ici.'
              : 'Essayez de modifier vos filtres ou votre recherche.'
          }}
        </p>
        <div class="queue-view__empty-actions">
          <NexusButton
            v-if="hasActiveFilters"
            variant="neutral"
            @click="resetFilters"
          >
            ✖ Réinitialiser les filtres
          </NexusButton>
          <NexusButton
            v-else
            variant="primary"
            @click="goToSearch"
          >
            🔍 Rechercher des séries
          </NexusButton>
        </div>
      </div>

      <!-- Liste des jobs -->
      <div v-else class="queue-view__list">
        <article
          v-for="job in filteredJobs"
          :key="job.id"
          class="queue-view__job"
          :class="[
            `queue-view__job--${job.status}`,
            { 'queue-view__job--selected': selectedIds.includes(job.id) },
            { 'queue-view__job--expanded': expandedJobId === job.id },
          ]"
        >
          <!-- En-tête du job -->
          <div class="queue-view__job-header" @click="toggleExpand(job.id)">
            <!-- Checkbox de sélection -->
            <div class="queue-view__job-checkbox" @click.stop>
              <input
                type="checkbox"
                :checked="selectedIds.includes(job.id)"
                @change="toggleSelect(job.id)"
                :aria-label="`Sélectionner le job ${job.title}`"
              />
            </div>

            <!-- Icône de statut -->
            <span class="queue-view__job-status-icon" aria-hidden="true">
              {{ getStatusIcon(job.status) }}
            </span>

            <!-- Informations principales -->
            <div class="queue-view__job-info">
              <div class="queue-view__job-title-row">
                <h3 class="queue-view__job-title" :title="job.title">
                  {{ job.title || 'Sans titre' }}
                </h3>
                <span
                  class="queue-view__job-status-badge"
                  :class="`queue-view__job-status-badge--${job.status}`"
                >
                  {{ getStatusLabel(job.status) }}
                </span>
              </div>

              <div class="queue-view__job-meta">
                <span class="queue-view__job-meta-item" :title="job.url">
                  🔗 {{ truncate(job.url, 60) }}
                </span>
                <span class="queue-view__job-meta-item">
                  🕐 {{ formatRelativeTime(job.created_at) }}
                </span>
                <span v-if="job.provider_id" class="queue-view__job-meta-item">
                  🌐 {{ job.provider_id }}
                </span>
              </div>
            </div>

            <!-- Progression -->
            <div class="queue-view__job-progress">
              <div class="queue-view__job-progress-track">
                <div
                  class="queue-view__job-progress-bar"
                  :class="`queue-view__job-progress-bar--${job.status}`"
                  :style="{ width: `${job.progress || 0}%` }"
                  role="progressbar"
                  :aria-valuenow="Math.round(job.progress || 0)"
                  aria-valuemin="0"
                  aria-valuemax="100"
                />
              </div>
              <div class="queue-view__job-progress-text">
                <span class="queue-view__job-progress-percent">
                  {{ Math.round(job.progress || 0) }}%
                </span>
                <span v-if="job.total_chapters" class="queue-view__job-progress-chapters">
                  {{ job.done_chapters || 0 }} / {{ job.total_chapters }} chapitres
                </span>
              </div>
              <div v-if="job.current_chapter" class="queue-view__job-current">
                <span aria-hidden="true">📖</span>
                <span class="queue-view__job-current-text">
                  {{ truncate(job.current_chapter, 40) }}
                </span>
              </div>
            </div>

            <!-- Actions -->
            <div class="queue-view__job-actions" @click.stop>
              <!-- Pause / Reprendre -->
              <button
                v-if="job.status === 'running'"
                type="button"
                class="queue-view__job-action"
                @click="pauseJob(job)"
                :disabled="actionLoading === job.id"
                title="Pause"
                aria-label="Mettre en pause"
              >
                <span v-if="actionLoading === job.id" class="queue-view__spinner">⟳</span>
                <span v-else>⏸️</span>
              </button>

              <button
                v-if="job.status === 'paused' || job.status === 'waiting'"
                type="button"
                class="queue-view__job-action"
                @click="resumeJob(job)"
                :disabled="actionLoading === job.id"
                title="Reprendre"
                aria-label="Reprendre"
              >
                <span v-if="actionLoading === job.id" class="queue-view__spinner">⟳</span>
                <span v-else>▶️</span>
              </button>

              <!-- Annuler -->
              <button
                v-if="['pending', 'running', 'paused', 'waiting'].includes(job.status)"
                type="button"
                class="queue-view__job-action queue-view__job-action--danger"
                @click="confirmCancelJob(job)"
                :disabled="actionLoading === job.id"
                title="Annuler"
                aria-label="Annuler le job"
              >
                <span v-if="actionLoading === job.id" class="queue-view__spinner">⟳</span>
                <span v-else>🚫</span>
              </button>

              <!-- Retry -->
              <button
                v-if="['failed', 'cancelled'].includes(job.status)"
                type="button"
                class="queue-view__job-action queue-view__job-action--success"
                @click="retryJob(job)"
                :disabled="actionLoading === job.id"
                title="Relancer"
                aria-label="Relancer le job"
              >
                <span v-if="actionLoading === job.id" class="queue-view__spinner">⟳</span>
                <span v-else>🔄</span>
              </button>

              <!-- Télécharger le résultat -->
              <button
                v-if="job.status === 'completed' && job.result_path"
                type="button"
                class="queue-view__job-action queue-view__job-action--primary"
                @click="downloadResult(job)"
                title="Télécharger le CBZ"
                aria-label="Télécharger le résultat"
              >
                ⬇️
              </button>

              <!-- Supprimer -->
              <button
                v-if="['completed', 'failed', 'cancelled'].includes(job.status)"
                type="button"
                class="queue-view__job-action queue-view__job-action--danger"
                @click="confirmDeleteJob(job)"
                :disabled="actionLoading === job.id"
                title="Supprimer de la liste"
                aria-label="Supprimer"
              >
                🗑️
              </button>

              <!-- Expand / Collapse -->
              <button
                type="button"
                class="queue-view__job-action"
                @click="toggleExpand(job.id)"
                :aria-expanded="expandedJobId === job.id"
                :aria-label="expandedJobId === job.id ? 'Réduire les détails' : 'Afficher les détails'"
                :title="expandedJobId === job.id ? 'Réduire' : 'Détails'"
              >
                <span aria-hidden="true">{{ expandedJobId === job.id ? '▲' : '▼' }}</span>
              </button>
            </div>
          </div>

          <!-- Détails étendus -->
          <div v-if="expandedJobId === job.id" class="queue-view__job-details">
            <!-- Logs -->
            <div class="queue-view__job-logs">
              <div class="queue-view__job-logs-header">
                <span class="queue-view__job-logs-title">
                  📋 Logs
                  <span v-if="job.logs?.length" class="queue-view__job-logs-count">
                    ({{ job.logs.length }})
                  </span>
                </span>
                <div class="queue-view__job-logs-actions">
                  <button
                    type="button"
                    class="queue-view__job-logs-action"
                    @click="copyLogs(job)"
                    title="Copier les logs"
                  >
                    📄
                  </button>
                </div>
              </div>

              <div v-if="!job.logs || job.logs.length === 0" class="queue-view__job-logs-empty">
                Aucun log disponible
              </div>

              <div v-else class="queue-view__job-logs-content">
                <div
                  v-for="(log, idx) in job.logs.slice(-100)"
                  :key="idx"
                  class="queue-view__job-log"
                  :class="`queue-view__job-log--${log.level || 'info'}`"
                >
                  <span class="queue-view__job-log-time">
                    {{ formatTime(log.timestamp) }}
                  </span>
                  <span class="queue-view__job-log-level">
                    {{ (log.level || 'info').toUpperCase() }}
                  </span>
                  <span class="queue-view__job-log-message">{{ log.message }}</span>
                </div>
              </div>
            </div>

            <!-- Erreurs -->
            <div v-if="job.errors && job.errors.length > 0" class="queue-view__job-errors">
              <div class="queue-view__job-errors-title">
                ❌ Erreurs ({{ job.errors.length }})
              </div>
              <div class="queue-view__job-errors-content">
                <div
                  v-for="(err, idx) in job.errors"
                  :key="idx"
                  class="queue-view__job-error"
                >
                  <span class="queue-view__job-error-time">
                    {{ formatTime(err.timestamp) }}
                  </span>
                  <span class="queue-view__job-error-message">{{ err.message }}</span>
                </div>
              </div>
            </div>

            <!-- Informations techniques -->
            <div class="queue-view__job-technical">
              <div class="queue-view__job-technical-row">
                <span class="queue-view__job-technical-label">ID :</span>
                <code class="queue-view__job-technical-value">{{ job.id }}</code>
              </div>
              <div class="queue-view__job-technical-row">
                <span class="queue-view__job-technical-label">Créé :</span>
                <span class="queue-view__job-technical-value">{{ formatDateTime(job.created_at) }}</span>
              </div>
              <div v-if="job.started_at" class="queue-view__job-technical-row">
                <span class="queue-view__job-technical-label">Démarré :</span>
                <span class="queue-view__job-technical-value">{{ formatDateTime(job.started_at) }}</span>
              </div>
              <div v-if="job.completed_at" class="queue-view__job-technical-row">
                <span class="queue-view__job-technical-label">Terminé :</span>
                <span class="queue-view__job-technical-value">{{ formatDateTime(job.completed_at) }}</span>
              </div>
              <div v-if="job.result_size" class="queue-view__job-technical-row">
                <span class="queue-view__job-technical-label">Taille :</span>
                <span class="queue-view__job-technical-value">{{ formatFileSize(job.result_size) }}</span>
              </div>
            </div>

            <!-- Résultat (si terminé) -->
            <div v-if="job.status === 'completed' && job.result_path" class="queue-view__job-result">
              <NexusButton
                variant="success"
                size="sm"
                @click="downloadResult(job)"
              >
                📥 Télécharger le CBZ
              </NexusButton>
              <NexusButton
                variant="primary"
                size="sm"
                @click="openReader(job)"
              >
                📖 Lire maintenant
              </NexusButton>
            </div>
          </div>
        </article>
      </div>
    </div>

    <!-- ====================================================================
      PIED DE PAGE
    ==================================================================== -->
    <footer class="queue-view__footer">
      <span class="queue-view__footer-info">
        {{ filteredJobs.length }} / {{ totalJobs }} jobs affichés
        <span v-if="searchQuery" class="queue-view__footer-highlight">
          · recherche : "{{ searchQuery }}"
        </span>
        <span v-if="statusFilter !== 'all'" class="queue-view__footer-highlight">
          · statut : {{ statusFilter }}
        </span>
      </span>
      <span v-if="lastUpdated" class="queue-view__footer-updated">
        Dernière mise à jour : {{ formatDateTime(lastUpdated) }}
      </span>
    </footer>

    <!-- ====================================================================
      MODALES DE CONFIRMATION
    ==================================================================== -->

    <!-- Annulation de job -->
    <NexusModal
      v-model="showCancelJobModal"
      title="🚫 Annuler le job"
      size="sm"
      confirmable
      confirm-text="Annuler le job"
      cancel-text="Retour"
      confirm-variant="warning"
      :loading="actionLoading === jobToCancel?.id"
      @confirm="cancelJob"
      @cancel="showCancelJobModal = false; jobToCancel = null"
    >
      <p>
        Êtes-vous sûr de vouloir annuler le job
        <strong>"{{ jobToCancel?.title }}"</strong> ?
      </p>
      <p class="queue-view__modal-warning">
        ⚠️ Le téléchargement en cours sera interrompu et les fichiers temporaires
        seront supprimés.
      </p>
    </NexusModal>

    <!-- Suppression de job -->
    <NexusModal
      v-model="showDeleteJobModal"
      title="🗑️ Supprimer le job"
      size="sm"
      confirmable
      confirm-text="Supprimer"
      cancel-text="Annuler"
      confirm-variant="error"
      :loading="actionLoading === jobToDelete?.id"
      @confirm="deleteJob"
      @cancel="showDeleteJobModal = false; jobToDelete = null"
    >
      <p>
        Êtes-vous sûr de vouloir supprimer le job
        <strong>"{{ jobToDelete?.title }}"</strong> de la liste ?
      </p>
      <p class="queue-view__modal-warning">
        ⚠️ Le fichier CBZ généré (s'il existe) ne sera pas supprimé de la
        bibliothèque.
      </p>
    </NexusModal>

    <!-- Annulation globale -->
    <NexusModal
      v-model="showCancelAllModal"
      title="🚫 Annuler tous les jobs"
      size="sm"
      confirmable
      confirm-text="Tout annuler"
      cancel-text="Annuler"
      confirm-variant="error"
      :loading="bulkLoading"
      @confirm="cancelAllJobs"
      @cancel="showCancelAllModal = false"
    >
      <p>
        Êtes-vous sûr de vouloir annuler
        <strong>{{ activeJobsCount }} job(s) actif(s)</strong> ?
      </p>
      <p class="queue-view__modal-warning">
        ⚠️ Tous les téléchargements en cours seront interrompus.
      </p>
    </NexusModal>

    <!-- Nettoyage des jobs terminés -->
    <NexusModal
      v-model="showClearCompletedModal"
      title="🧹 Nettoyer les jobs terminés"
      size="sm"
      confirmable
      confirm-text="Nettoyer"
      cancel-text="Annuler"
      confirm-variant="warning"
      :loading="bulkLoading"
      @confirm="clearCompleted"
      @cancel="showClearCompletedModal = false"
    >
      <p>
        Supprimer tous les jobs terminés, échoués et annulés de la liste ?
      </p>
      <p class="queue-view__modal-warning">
        ⚠️ Les fichiers CBZ associés resteront dans votre bibliothèque.
      </p>
    </NexusModal>
  </div>
</template>

<script setup>
// ==========================================================================
//  Imports
// ==========================================================================

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useJobsStore } from '@/stores/jobs'
import { useToast } from '@/composables/useToast'
import { useApi } from '@/composables/useApi'
import NexusSpinner from '@/components/common/NexusSpinner.vue'
import NexusButton from '@/components/common/NexusButton.vue'
import NexusModal from '@/components/common/NexusModal.vue'
import {
  formatFileSize,
  formatRelativeTime as fmtRelativeTime,
  formatDateTime as fmtDateTime,
  truncate,
} from '@/utils/formatters'
import dayjs from 'dayjs'

// ==========================================================================
//  Composables & Stores
// ==========================================================================

const router = useRouter()
const jobsStore = useJobsStore()
const toast = useToast()
const api = useApi()

// ==========================================================================
//  État réactif
// ==========================================================================

const loading = ref(false)
const bulkLoading = ref(false)
const error = ref(null)
const lastUpdated = ref(null)
const searchQuery = ref('')
const statusFilter = ref('all')
const sortBy = ref('created-desc')
const expandedJobId = ref(null)
const selectedIds = ref([])
const actionLoading = ref(null)
const searchInputRef = ref(null)

// Modales
const showCancelJobModal = ref(false)
const showDeleteJobModal = ref(false)
const showCancelAllModal = ref(false)
const showClearCompletedModal = ref(false)
const jobToCancel = ref(null)
const jobToDelete = ref(null)

// Auto-refresh
const autoRefreshEnabled = ref(true)
let autoRefreshTimer = null

// Pause globale
const isPausedAll = ref(false)

// ==========================================================================
//  Computed
// ==========================================================================

const jobs = computed(() => jobsStore.jobsList || [])

const wsConnected = computed(() => jobsStore.wsConnected || false)

const totalJobs = computed(() => jobs.value.length)

const activeJobsCount = computed(() => {
  return jobs.value.filter((j) =>
    ['pending', 'running', 'paused', 'waiting'].includes(j.status)
  ).length
})

const completedJobs = computed(() => {
  return jobs.value.filter((j) =>
    ['completed', 'failed', 'cancelled'].includes(j.status)
  )
})

const statsCount = computed(() => {
  const counts = {
    pending: 0,
    running: 0,
    paused: 0,
    waiting: 0,
    completed: 0,
    failed: 0,
    cancelled: 0,
  }
  for (const job of jobs.value) {
    if (counts[job.status] !== undefined) counts[job.status]++
  }
  return counts
})

const overallProgress = computed(() => {
  const active = jobs.value.filter((j) => ['running', 'paused'].includes(j.status))
  if (active.length === 0) return 0
  const total = active.reduce((sum, j) => sum + (j.progress || 0), 0)
  return total / active.length
})

const filteredJobs = computed(() => {
  let result = [...jobs.value]

  // Recherche
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter((job) => {
      return (
        (job.title || '').toLowerCase().includes(q) ||
        (job.url || '').toLowerCase().includes(q) ||
        (job.id || '').toLowerCase().includes(q) ||
        (job.provider_id || '').toLowerCase().includes(q)
      )
    })
  }

  // Filtre statut
  if (statusFilter.value !== 'all') {
    if (statusFilter.value === 'active') {
      result = result.filter((j) =>
        ['pending', 'running', 'paused', 'waiting'].includes(j.status)
      )
    } else if (statusFilter.value === 'finished') {
      result = result.filter((j) =>
        ['completed', 'failed', 'cancelled'].includes(j.status)
      )
    } else {
      result = result.filter((j) => j.status === statusFilter.value)
    }
  }

  // Tri
  const [field, order] = sortBy.value.split('-')
  result.sort((a, b) => {
    let cmp = 0
    switch (field) {
      case 'title':
        cmp = (a.title || '').localeCompare(b.title || '')
        break
      case 'progress':
        cmp = (a.progress || 0) - (b.progress || 0)
        break
      case 'created':
      default: {
        const ta = a.created_at ? new Date(a.created_at).getTime() : 0
        const tb = b.created_at ? new Date(b.created_at).getTime() : 0
        cmp = ta - tb
        break
      }
    }
    return order === 'desc' ? -cmp : cmp
  })

  return result
})

const hasActiveFilters = computed(() => {
  return !!searchQuery.value || statusFilter.value !== 'all'
})

const statusFilters = computed(() => [
  { value: 'all', label: 'Tous', icon: '📋', count: totalJobs.value },
  {
    value: 'active',
    label: 'Actifs',
    icon: '⚡',
    count: jobs.value.filter((j) =>
      ['pending', 'running', 'paused', 'waiting'].includes(j.status)
    ).length,
  },
  { value: 'running', label: 'En cours', icon: '🔄', count: statsCount.value.running },
  { value: 'completed', label: 'Terminés', icon: '✅', count: statsCount.value.completed },
  { value: 'failed', label: 'Échecs', icon: '❌', count: statsCount.value.failed },
  { value: 'finished', label: 'Historique', icon: '📦' },
])

// ==========================================================================
//  Méthodes — Récupération
// ==========================================================================

async function refreshJobs() {
  loading.value = true
  error.value = null
  try {
    await jobsStore.fetchJobs()
    lastUpdated.value = new Date().toISOString()
  } catch (err) {
    console.error('Erreur chargement jobs:', err)
    error.value = `Impossible de charger les jobs : ${err.message}`
  } finally {
    loading.value = false
  }
}

// ==========================================================================
//  Méthodes — Actions sur les jobs
// ==========================================================================

async function pauseJob(job) {
  actionLoading.value = job.id
  try {
    await api.patch(`/downloads/jobs/${job.id}/pause`)
    job.status = 'paused'
    toast.success('Job mis en pause', '⏸️')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    actionLoading.value = null
  }
}

async function resumeJob(job) {
  actionLoading.value = job.id
  try {
    await api.patch(`/downloads/jobs/${job.id}/resume`)
    job.status = 'running'
    toast.success('Job repris', '▶️')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    actionLoading.value = null
  }
}

function confirmCancelJob(job) {
  jobToCancel.value = job
  showCancelJobModal.value = true
}

async function cancelJob() {
  if (!jobToCancel.value) return
  const job = jobToCancel.value
  actionLoading.value = job.id
  try {
    await jobsStore.cancelJob(job.id, true)
    toast.info(`"${job.title}" annulé`, '🚫')
    showCancelJobModal.value = false
    jobToCancel.value = null
    await refreshJobs()
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    actionLoading.value = null
  }
}

async function retryJob(job) {
  actionLoading.value = job.id
  try {
    await api.post(`/downloads/jobs/${job.id}/retry`)
    toast.success('Job relancé', '🔄')
    await refreshJobs()
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    actionLoading.value = null
  }
}

function confirmDeleteJob(job) {
  jobToDelete.value = job
  showDeleteJobModal.value = true
}

async function deleteJob() {
  if (!jobToDelete.value) return
  const job = jobToDelete.value
  actionLoading.value = job.id
  try {
    await api.delete(`/downloads/jobs/${job.id}`)
    jobsStore.removeJob(job.id)
    toast.success('Job supprimé', '🗑️')
    showDeleteJobModal.value = false
    jobToDelete.value = null
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    actionLoading.value = null
  }
}

async function downloadResult(job) {
  if (!job.result_path) return
  try {
    const filename = job.result_path.split('/').pop()
    await api.downloadAndSave(
      `/downloads/files/${encodeURIComponent(filename)}`,
      filename
    )
    toast.success('Téléchargement lancé', '⬇️')
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  }
}

function openReader(job) {
  router.push({
    name: 'reader',
    params: { jobId: job.id },
  })
}

// ==========================================================================
//  Méthodes — Actions globales
// ==========================================================================

function togglePauseAll() {
  isPausedAll.value = !isPausedAll.value
  toast.info(
    isPausedAll.value ? 'Tous les jobs sont en pause' : 'Tous les jobs sont repris',
    isPausedAll.value ? '⏸️' : '▶️'
  )
}

function confirmCancelAll() {
  showCancelAllModal.value = true
}

async function cancelAllJobs() {
  bulkLoading.value = true
  try {
    await jobsStore.cancelAllActive(true)
    toast.info('Tous les jobs ont été annulés', '🚫')
    showCancelAllModal.value = false
    await refreshJobs()
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    bulkLoading.value = false
  }
}

function confirmClearCompleted() {
  showClearCompletedModal.value = true
}

async function clearCompleted() {
  bulkLoading.value = true
  try {
    jobsStore.clearCompletedJobs(0)
    toast.success('Jobs terminés nettoyés', '🧹')
    showClearCompletedModal.value = false
  } catch (err) {
    toast.error(`Erreur : ${err.message}`, '❌')
  } finally {
    bulkLoading.value = false
  }
}

// ==========================================================================
//  Méthodes — Sélection
// ==========================================================================

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) selectedIds.value.push(id)
  else selectedIds.value.splice(idx, 1)
}

function clearSelection() {
  selectedIds.value = []
}

// ==========================================================================
//  Méthodes — Actions groupées
// ==========================================================================

async function bulkPause() {
  if (selectedIds.value.length === 0) return
  bulkLoading.value = true
  try {
    for (const id of selectedIds.value) {
      const job = jobs.value.find((j) => j.id === id)
      if (job && job.status === 'running') {
        await api.patch(`/downloads/jobs/${id}/pause`).catch(() => null)
      }
    }
    toast.success(`${selectedIds.value.length} job(s) mis en pause`, '⏸️')
    clearSelection()
    await refreshJobs()
  } finally {
    bulkLoading.value = false
  }
}

async function bulkResume() {
  if (selectedIds.value.length === 0) return
  bulkLoading.value = true
  try {
    for (const id of selectedIds.value) {
      const job = jobs.value.find((j) => j.id === id)
      if (job && ['paused', 'waiting'].includes(job.status)) {
        await api.patch(`/downloads/jobs/${id}/resume`).catch(() => null)
      }
    }
    toast.success(`${selectedIds.value.length} job(s) repris`, '▶️')
    clearSelection()
    await refreshJobs()
  } finally {
    bulkLoading.value = false
  }
}

async function bulkCancel() {
  if (selectedIds.value.length === 0) return
  bulkLoading.value = true
  try {
    for (const id of selectedIds.value) {
      await jobsStore.cancelJob(id, true).catch(() => null)
    }
    toast.info(`${selectedIds.value.length} job(s) annulé(s)`, '🚫')
    clearSelection()
    await refreshJobs()
  } finally {
    bulkLoading.value = false
  }
}

// ==========================================================================
//  Méthodes — Filtres
// ==========================================================================

function resetFilters() {
  searchQuery.value = ''
  statusFilter.value = 'all'
  sortBy.value = 'created-desc'
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
    if (!wsConnected.value && !loading.value) {
      refreshJobs()
    }
  }, 5000)
}

function stopAutoRefresh() {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

// ==========================================================================
//  Méthodes — Utilitaires
// ==========================================================================

function toggleExpand(jobId) {
  expandedJobId.value = expandedJobId.value === jobId ? null : jobId
}

function getStatusIcon(status) {
  const map = {
    pending: '⏳',
    running: '🔄',
    completed: '✅',
    failed: '❌',
    cancelled: '🚫',
    paused: '⏸️',
    waiting: '⏱️',
  }
  return map[status] || '❓'
}

function getStatusLabel(status) {
  const map = {
    pending: 'En attente',
    running: 'En cours',
    completed: 'Terminé',
    failed: 'Échec',
    cancelled: 'Annulé',
    paused: 'En pause',
    waiting: 'Attente',
  }
  return map[status] || status
}

function formatRelativeTime(date) {
  if (!date) return '—'
  try {
    return fmtRelativeTime(date)
  } catch (_) {
    return '—'
  }
}

function formatDateTime(date) {
  if (!date) return '—'
  try {
    const d = dayjs(date)
    return d.isValid() ? d.format('DD/MM/YYYY HH:mm:ss') : '—'
  } catch (_) {
    return '—'
  }
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  try {
    const d = dayjs(timestamp)
    return d.isValid() ? d.format('HH:mm:ss') : ''
  } catch (_) {
    return ''
  }
}

async function copyLogs(job) {
  if (!job.logs || job.logs.length === 0) return
  const text = job.logs
    .map((l) => `[${l.timestamp}] [${l.level || 'info'}] ${l.message}`)
    .join('\n')
  try {
    await navigator.clipboard.writeText(text)
    toast.success('Logs copiés', '📋')
  } catch (_) {
    toast.error('Impossible de copier', '❌')
  }
}

function goToSearch() {
  router.push('/search')
}

// ==========================================================================
//  Cycle de vie
// ==========================================================================

onMounted(async () => {
  await refreshJobs()

  if (autoRefreshEnabled.value && !wsConnected.value) {
    startAutoRefresh()
  }

  // Recharger si WebSocket déconnecté
  if (!wsConnected.value) {
    try {
      jobsStore.initWebSocket()
    } catch (_) {
      // Ignorer
    }
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})

// ==========================================================================
//  Watchers
// ==========================================================================

// Démarrer/arrêter l'auto-refresh selon la connexion WebSocket
watch(wsConnected, (connected) => {
  if (connected) {
    stopAutoRefresh()
  } else if (autoRefreshEnabled.value) {
    startAutoRefresh()
  }
})

// Mettre à jour lastUpdated quand les jobs changent
watch(
  () => jobsStore.lastUpdated,
  (val) => {
    if (val) lastUpdated.value = val
  }
)
</script>

<style lang="scss" scoped>
// ==========================================================================
//  Conteneur principal
// ==========================================================================

.queue-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  min-height: calc(100vh - 100px);
}

// ==========================================================================
//  Header
// ==========================================================================

.queue-view__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border, #1a2538);
}

.queue-view__header-left {
  flex: 1;
  min-width: 200px;
}

.queue-view__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.queue-view__subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
}

.queue-view__header-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

// ==========================================================================
//  WebSocket status
// ==========================================================================

.queue-view__ws-status {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.7rem;
  border-radius: var(--radius-full, 9999px);
  font-size: 0.7rem;
  font-weight: 600;
  border: 1px solid var(--color-border, #1a2538);
  white-space: nowrap;

  &--connected {
    background: rgba(76, 175, 80, 0.1);
    border-color: rgba(76, 175, 80, 0.35);
    color: #4caf50;

    .queue-view__ws-dot {
      background: #4caf50;
      animation: queuePulse 1.5s infinite;
    }
  }

  &--disconnected {
    background: rgba(106, 122, 154, 0.1);
    border-color: rgba(106, 122, 154, 0.3);
    color: #8899b0;

    .queue-view__ws-dot {
      background: #8899b0;
    }
  }
}

.queue-view__ws-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

@keyframes queuePulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

// ==========================================================================
//  Boutons
// ==========================================================================

.queue-view__btn {
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

  &--active {
    background: rgba(0, 212, 255, 0.15);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-primary, #00d4ff);
  }

  &--refresh:hover:not(:disabled) {
    border-color: var(--color-info, #2196f3);
    color: var(--color-info, #2196f3);
  }

  &--warning:hover:not(:disabled) {
    border-color: #ff9800;
    color: #ff9800;
  }

  &--danger:hover:not(:disabled) {
    border-color: #f44336;
    color: #f44336;
  }

  &--neutral:hover:not(:disabled) {
    border-color: var(--color-border-light, #253254);
  }
}

.queue-view__spinner {
  display: inline-block;
  animation: queueSpin 0.8s linear infinite;
}

@keyframes queueSpin {
  to { transform: rotate(360deg); }
}

// ==========================================================================
//  Barre d'erreur
// ==========================================================================

.queue-view__error {
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

.queue-view__error-icon {
  flex-shrink: 0;
}

.queue-view__error-text {
  flex: 1;
}

.queue-view__error-close {
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
//  Statistiques
// ==========================================================================

.queue-view__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--color-bg-secondary, #141a2b);
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #1a2538);
}

.queue-view__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.3rem 0.7rem;
  border-radius: var(--radius-sm, 4px);
  background: var(--color-bg-card, #1a2538);
  min-width: 65px;

  &--pending { border-left: 3px solid #ff9800; }
  &--running { border-left: 3px solid #2196f3; }
  &--completed { border-left: 3px solid #4caf50; }
  &--failed { border-left: 3px solid #f44336; }
  &--cancelled { border-left: 3px solid #6a7a9a; }
  &--filtered { border-left: 3px solid var(--color-primary, #00d4ff); }
}

.queue-view__stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
  font-variant-numeric: tabular-nums;
}

.queue-view__stat-label {
  font-size: 0.6rem;
  text-transform: uppercase;
  color: var(--color-text-muted, #6a7a9a);
  letter-spacing: 0.05em;
}

// ==========================================================================
//  Global progress
// ==========================================================================

.queue-view__global-progress {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.6rem 0.9rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
}

.queue-view__global-progress-info {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 0.8rem;
}

.queue-view__global-progress-label {
  color: var(--color-text-secondary, #b0c0d8);
}

.queue-view__global-progress-value {
  color: var(--color-primary, #00d4ff);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.queue-view__global-progress-track {
  width: 100%;
  height: 8px;
  background: var(--color-bg-input, #1e2a40);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
}

.queue-view__global-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #0066ff);
  border-radius: var(--radius-full, 9999px);
  transition: width 0.4s ease;
}

// ==========================================================================
//  Toolbar
// ==========================================================================

.queue-view__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.queue-view__search-wrapper {
  position: relative;
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
}

.queue-view__search-icon {
  position: absolute;
  left: 0.6rem;
  font-size: 0.85rem;
  color: var(--color-text-muted, #6a7a9a);
  pointer-events: none;
}

.queue-view__search-input {
  width: 100%;
  padding: 0.45rem 0.5rem 0.45rem 2rem;
  font-size: 0.85rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  outline: none;
  transition: all 0.15s ease;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.15);
  }

  &::placeholder {
    color: var(--color-text-muted, #6a7a9a);
  }
}

.queue-view__search-clear {
  position: absolute;
  right: 0.3rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #6a7a9a);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0 0.3rem;

  &:hover {
    color: var(--color-text-primary, #e8edf5);
  }
}

.queue-view__filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;
}

.queue-view__filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.3rem 0.6rem;
  font-size: 0.72rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;

  &:hover {
    background: var(--color-bg-hover, #253254);
  }

  &--active {
    background: var(--color-primary, #00d4ff);
    border-color: var(--color-primary, #00d4ff);
    color: var(--color-text-inverse, #0a0e1a);
  }
}

.queue-view__filter-count {
  font-size: 0.6rem;
  padding: 0 0.3rem;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.2);
  font-variant-numeric: tabular-nums;
  opacity: 0.9;
}

.queue-view__select {
  padding: 0.35rem 0.6rem;
  font-size: 0.75rem;
  background: var(--color-bg-input, #1e2a40);
  color: var(--color-text-primary, #e8edf5);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  outline: none;

  &:focus {
    border-color: var(--color-primary, #00d4ff);
  }
}

// ==========================================================================
//  Bulk actions
// ==========================================================================

.queue-view__bulk-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.6rem 0.9rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-primary, #00d4ff);
  border-radius: var(--radius-md, 8px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.queue-view__bulk-info {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-primary, #e8edf5);
}

.queue-view__bulk-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.queue-view__bulk-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--color-bg-secondary, #141a2b);
  color: var(--color-text-secondary, #b0c0d8);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-sm, 4px);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover:not(:disabled) {
    background: var(--color-bg-hover, #253254);
    color: var(--color-text-primary, #e8edf5);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &--warning:hover:not(:disabled) {
    border-color: #ff9800;
    color: #ff9800;
  }
  &--success:hover:not(:disabled) {
    border-color: #4caf50;
    color: #4caf50;
  }
  &--danger:hover:not(:disabled) {
    border-color: #f44336;
    color: #f44336;
  }
  &--neutral:hover:not(:disabled) {
    border-color: var(--color-border-light, #253254);
  }
}

.queue-view-slide-enter-active,
.queue-view-slide-leave-active {
  transition: all 0.25s ease;
}

.queue-view-slide-enter-from,
.queue-view-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

// ==========================================================================
//  Body
// ==========================================================================

.queue-view__body {
  flex: 1;
  min-height: 300px;
}

// ==========================================================================
//  Loading / Empty
// ==========================================================================

.queue-view__loading,
.queue-view__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  gap: 0.75rem;
  min-height: 350px;
  color: var(--color-text-muted, #6a7a9a);
}

.queue-view__empty-icon {
  font-size: 4rem;
  opacity: 0.5;
  margin-bottom: 0.5rem;
}

.queue-view__empty-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
}

.queue-view__empty-text {
  margin: 0;
  font-size: 0.9rem;
  max-width: 450px;
  line-height: 1.5;
}

.queue-view__empty-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 0.5rem;
}

// ==========================================================================
//  Liste des jobs
// ==========================================================================

.queue-view__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.queue-view__job {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--color-border-light, #253254);
  }

  &--selected {
    border-color: var(--color-primary, #00d4ff);
    background: rgba(0, 212, 255, 0.03);
  }

  &--expanded {
    border-color: var(--color-primary, #00d4ff);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  }

  // Bords colorés selon le statut
  &--pending { border-left: 4px solid #ff9800; }
  &--running { border-left: 4px solid #2196f3; }
  &--completed { border-left: 4px solid #4caf50; }
  &--failed { border-left: 4px solid #f44336; }
  &--cancelled { border-left: 4px solid #6a7a9a; }
  &--paused { border-left: 4px solid #ff9800; opacity: 0.85; }
  &--waiting { border-left: 4px solid #9c27b0; }
}

// ==========================================================================
//  Job header
// ==========================================================================

.queue-view__job-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 0.85rem;
  cursor: pointer;
  user-select: none;
}

.queue-view__job-checkbox {
  flex-shrink: 0;

  input[type='checkbox'] {
    width: 16px;
    height: 16px;
    cursor: pointer;
    accent-color: var(--color-primary, #00d4ff);
  }
}

.queue-view__job-status-icon {
  flex-shrink: 0;
  font-size: 1.2rem;
  line-height: 1;

  .queue-view__job--running & {
    animation: queueStatusSpin 1.5s linear infinite;
  }
}

@keyframes queueStatusSpin {
  to { transform: rotate(360deg); }
}

.queue-view__job-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.queue-view__job-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.queue-view__job-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary, #e8edf5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 400px;
}

.queue-view__job-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.1rem 0.5rem;
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: var(--radius-full, 9999px);
  white-space: nowrap;

  &--pending {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
    border: 1px solid rgba(255, 152, 0, 0.3);
  }
  &--running {
    background: rgba(33, 150, 243, 0.15);
    color: #2196f3;
    border: 1px solid rgba(33, 150, 243, 0.3);
  }
  &--completed {
    background: rgba(76, 175, 80, 0.15);
    color: #4caf50;
    border: 1px solid rgba(76, 175, 80, 0.3);
  }
  &--failed {
    background: rgba(244, 67, 54, 0.15);
    color: #f44336;
    border: 1px solid rgba(244, 67, 54, 0.3);
  }
  &--cancelled {
    background: rgba(106, 122, 154, 0.15);
    color: #8899b0;
    border: 1px solid rgba(106, 122, 154, 0.3);
  }
  &--paused {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
    border: 1px solid rgba(255, 152, 0, 0.3);
  }
  &--waiting {
    background: rgba(156, 39, 176, 0.15);
    color: #ba68c8;
    border: 1px solid rgba(156, 39, 176, 0.3);
  }
}

.queue-view__job-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  font-size: 0.7rem;
  color: var(--color-text-muted, #6a7a9a);
}

.queue-view__job-meta-item {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 320px;
}

// ==========================================================================
//  Job progress
// ==========================================================================

.queue-view__job-progress {
  flex-shrink: 0;
  width: 200px;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.queue-view__job-progress-track {
  height: 6px;
  background: var(--color-bg-input, #1e2a40);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
}

.queue-view__job-progress-bar {
  height: 100%;
  border-radius: var(--radius-full, 9999px);
  transition: width 0.4s ease;

  &--pending { background: linear-gradient(90deg, #ff9800, #ffb74d); }
  &--running { background: linear-gradient(90deg, #00d4ff, #0066ff); }
  &--completed { background: linear-gradient(90deg, #4caf50, #81c784); }
  &--failed { background: linear-gradient(90deg, #f44336, #e57373); }
  &--cancelled { background: linear-gradient(90deg, #6a7a9a, #8899b0); }
  &--paused { background: linear-gradient(90deg, #ff9800, #ffb74d); }
  &--waiting { background: linear-gradient(90deg, #9c27b0, #ba68c8); }
}

.queue-view__job-progress-text {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 0.68rem;
  font-variant-numeric: tabular-nums;
}

.queue-view__job-progress-percent {
  font-weight: 700;
  color: var(--color-text-primary, #e8edf5);
}

.queue-view__job-progress-chapters {
  color: var(--color-text-muted, #6a7a9a);
}

.queue-view__job-current {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.65rem;
  color: var(--color-text-muted, #6a7a9a);
  font-style: italic;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.queue-view__job-current-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// ==========================================================================
//  Job actions
// ==========================================================================

.queue-view__job-actions {
  display: flex;
  gap: 0.15rem;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.queue-view__job-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--color-text-muted, #6a7a9a);
  cursor: pointer;
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

  &--danger:hover:not(:disabled) {
    background: rgba(244, 67, 54, 0.1);
    color: #f44336;
    border-color: rgba(244, 67, 54, 0.3);
  }

  &--success:hover:not(:disabled) {
    background: rgba(76, 175, 80, 0.1);
    color: #4caf50;
    border-color: rgba(76, 175, 80, 0.3);
  }

  &--primary:hover:not(:disabled) {
    background: rgba(0, 212, 255, 0.1);
    color: #00d4ff;
    border-color: rgba(0, 212, 255, 0.3);
  }
}

// ==========================================================================
//  Job details
// ==========================================================================

.queue-view__job-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.75rem 0.85rem;
  border-top: 1px solid var(--color-border, #1a2538);
  background: var(--color-bg-secondary, #141a2b);
  animation: queueDetailsIn 0.2s ease;
}

@keyframes queueDetailsIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// ==========================================================================
//  Logs
// ==========================================================================

.queue-view__job-logs {
  background: #0d1117;
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
}

.queue-view__job-logs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 0.7rem;
  background: #161b22;
  border-bottom: 1px solid #30363d;
}

.queue-view__job-logs-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: #c9d1d9;
}

.queue-view__job-logs-count {
  color: #6a7a9a;
  font-weight: 400;
  font-size: 0.7rem;
}

.queue-view__job-logs-action {
  background: transparent;
  border: none;
  color: #6a7a9a;
  cursor: pointer;
  padding: 0.1rem 0.35rem;
  border-radius: var(--radius-sm, 4px);
  font-size: 0.85rem;

  &:hover {
    color: #c9d1d9;
    background: rgba(255, 255, 255, 0.05);
  }
}

.queue-view__job-logs-empty {
  padding: 1rem;
  text-align: center;
  font-size: 0.75rem;
  color: #6a7a9a;
  font-style: italic;
}

.queue-view__job-logs-content {
  max-height: 250px;
  overflow-y: auto;
  padding: 0.5rem 0.7rem;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.7rem;
  line-height: 1.6;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: #161b22;
  }
  &::-webkit-scrollbar-thumb {
    background: #30363d;
    border-radius: 3px;

    &:hover {
      background: #484f58;
    }
  }
}

.queue-view__job-log {
  display: flex;
  gap: 0.5rem;
  padding: 0.1rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  align-items: baseline;

  &:last-child {
    border-bottom: none;
  }

  &--info { color: #c9d1d9; }
  &--warning { color: #ffb74d; }
  &--error { color: #e57373; }
  &--debug { color: #8899b0; }
}

.queue-view__job-log-time {
  flex-shrink: 0;
  color: #6a7a9a;
  font-size: 0.65rem;
}

.queue-view__job-log-level {
  flex-shrink: 0;
  width: 55px;
  font-weight: 700;
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.queue-view__job-log-message {
  flex: 1;
  word-break: break-word;
}

// ==========================================================================
//  Errors
// ==========================================================================

.queue-view__job-errors {
  background: rgba(244, 67, 54, 0.05);
  border: 1px solid rgba(244, 67, 54, 0.25);
  border-radius: var(--radius-md, 8px);
  overflow: hidden;
}

.queue-view__job-errors-title {
  padding: 0.4rem 0.7rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #e57373;
  background: rgba(244, 67, 54, 0.08);
  border-bottom: 1px solid rgba(244, 67, 54, 0.15);
}

.queue-view__job-errors-content {
  max-height: 150px;
  overflow-y: auto;
  padding: 0.4rem 0.7rem;
}

.queue-view__job-error {
  display: flex;
  gap: 0.5rem;
  padding: 0.15rem 0;
  font-size: 0.72rem;
  color: #e57373;
  border-bottom: 1px solid rgba(244, 67, 54, 0.08);

  &:last-child {
    border-bottom: none;
  }
}

.queue-view__job-error-time {
  flex-shrink: 0;
  color: #6a7a9a;
  font-size: 0.65rem;
}

.queue-view__job-error-message {
  flex: 1;
  word-break: break-word;
}

// ==========================================================================
//  Technical
// ==========================================================================

.queue-view__job-technical {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem 0.7rem;
  background: var(--color-bg-card, #1a2538);
  border: 1px solid var(--color-border, #1a2538);
  border-radius: var(--radius-md, 8px);
}

.queue-view__job-technical-row {
  display: flex;
  gap: 0.5rem;
  align-items: baseline;
  font-size: 0.72rem;
}

.queue-view__job-technical-label {
  flex-shrink: 0;
  min-width: 70px;
  color: var(--color-text-muted, #6a7a9a);
}

.queue-view__job-technical-value {
  color: var(--color-text-secondary, #b0c0d8);
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 0.7rem;
  word-break: break-all;
}

// ==========================================================================
//  Result
// ==========================================================================

.queue-view__job-result {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  padding-top: 0.25rem;
}

// ==========================================================================
//  Modal warning
// ==========================================================================

.queue-view__modal-warning {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: rgba(255, 152, 0, 0.1);
  border-left: 3px solid #ff9800;
  border-radius: var(--radius-sm, 4px);
  font-size: 0.78rem;
  color: #ff9800;
  line-height: 1.5;
}

// ==========================================================================
//  Footer
// ==========================================================================

.queue-view__footer {
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

.queue-view__footer-info {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.queue-view__footer-highlight {
  color: var(--color-primary, #00d4ff);
  font-weight: 500;
}

.queue-view__footer-updated {
  font-style: italic;
}

// ==========================================================================
//  Responsive
// ==========================================================================

@media (max-width: 900px) {
  .queue-view__job-header {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .queue-view__job-progress {
    order: 10;
    width: 100%;
    margin-top: 0.25rem;
  }

  .queue-view__job-actions {
    order: 9;
  }

  .queue-view__job-title {
    max-width: 100%;
  }
}

@media (max-width: 640px) {
  .queue-view {
    padding: 0.5rem;
  }

  .queue-view__title {
    font-size: 1.2rem;
  }

  .queue-view__header-right {
    width: 100%;
  }

  .queue-view__toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .queue-view__filters {
    overflow-x: auto;
    padding-bottom: 0.25rem;
  }

  .queue-view__stat {
    min-width: 55px;
    padding: 0.25rem 0.5rem;
  }

  .queue-view__stat-value {
    font-size: 0.9rem;
  }

  .queue-view__job-action {
    width: 28px;
    height: 28px;
  }

  .queue-view__job-details {
    padding: 0.6rem;
  }

  .queue-view__bulk-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .queue-view__bulk-buttons {
    justify-content: center;
  }
}

// ==========================================================================
//  Light mode
// ==========================================================================

.light-mode {
  .queue-view__btn,
  .queue-view__filter-btn,
  .queue-view__bulk-btn {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);

    &:hover:not(:disabled) {
      background: var(--color-bg-hover, #e3e8ef);
    }
  }

  .queue-view__search-input,
  .queue-view__select {
    background: var(--color-bg-input, #f0f2f5);
    color: var(--color-text-primary, #1a1a2e);
    border-color: var(--color-border, #d0d8e0);

    &::placeholder {
      color: var(--color-text-muted, #7a8a9a);
    }
  }

  .queue-view__stat,
  .queue-view__stats {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .queue-view__stat-value {
    color: var(--color-text-primary, #1a1a2e);
  }

  .queue-view__job {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);

    &:hover {
      border-color: var(--color-border-light, #e3e8ef);
    }
  }

  .queue-view__job-title {
    color: var(--color-text-primary, #1a1a2e);
  }

  .queue-view__job-progress-track {
    background: var(--color-bg-input, #f0f2f5);
  }

  .queue-view__job-details {
    background: var(--color-bg-secondary, #e9ecf2);
  }

  .queue-view__global-progress {
    background: var(--color-bg-card, #ffffff);
  }

  .queue-view__global-progress-track {
    background: var(--color-bg-input, #f0f2f5);
  }

  .queue-view__footer {
    background: var(--color-bg-secondary, #e9ecf2);
    border-color: var(--color-border, #d0d8e0);
  }

  .queue-view__job-technical {
    background: var(--color-bg-card, #ffffff);
    border-color: var(--color-border, #d0d8e0);
  }

  .queue-view__job-technical-value {
    color: var(--color-text-secondary, #3d4a5c);
  }
}

// ==========================================================================
//  Réduction des animations
// ==========================================================================

@media (prefers-reduced-motion: reduce) {
  .queue-view__job-status-icon,
  .queue-view__ws-dot,
  .queue-view__spinner,
  .queue-view__job-details {
    animation: none !important;
  }
}
</style>
