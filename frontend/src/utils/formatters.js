// ==========================================================================
//  NexusDL 2.0 - Formatters Utils
//  Fichier : frontend/src/utils/formatters.js
//  Description : Utilitaires de formatage (dates, nombres, tailles, durées, etc.)
//  Version : 2.0.0
// ==========================================================================

import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/duration'
import localizedFormat from 'dayjs/plugin/localizedFormat'
import 'dayjs/locale/fr'

// ==========================================================================
//  Configuration Day.js
// ==========================================================================

dayjs.extend(relativeTime)
dayjs.extend(duration)
dayjs.extend(localizedFormat)
dayjs.locale('fr')

// ==========================================================================
//  Formateurs de dates
// ==========================================================================

/**
 * Formate une date en chaîne lisible.
 * @param {string|Date|number} date - Date à formater
 * @param {string} format - Format de sortie (défaut: 'DD/MM/YYYY HH:mm')
 * @returns {string} - Date formatée
 */
export function formatDate(date, format = 'DD/MM/YYYY HH:mm') {
  if (!date) return ''
  const d = dayjs(date)
  if (!d.isValid()) return ''
  return d.format(format)
}

/**
 * Formate une date au format court (ex: 15/01/2025).
 * @param {string|Date|number} date - Date à formater
 * @returns {string} - Date formatée
 */
export function formatDateShort(date) {
  return formatDate(date, 'DD/MM/YYYY')
}

/**
 * Formate une date au format long (ex: 15 janvier 2025).
 * @param {string|Date|number} date - Date à formater
 * @returns {string} - Date formatée
 */
export function formatDateLong(date) {
  return formatDate(date, 'DD MMMM YYYY')
}

/**
 * Formate une heure (ex: 14:30).
 * @param {string|Date|number} date - Date à formater
 * @returns {string} - Heure formatée
 */
export function formatTime(date) {
  return formatDate(date, 'HH:mm')
}

/**
 * Formate une date ISO en chaîne lisible (ex: 15 janvier 2025 à 14:30).
 * @param {string|Date|number} date - Date à formater
 * @returns {string} - Date formatée
 */
export function formatDateTime(date) {
  return formatDate(date, 'DD MMMM YYYY à HH:mm')
}

/**
 * Formate une date au format relatif (ex: "il y a 2 heures", "dans 3 jours").
 * @param {string|Date|number} date - Date à formater
 * @param {boolean} withoutSuffix - Supprimer le suffixe ("il y a" / "dans")
 * @returns {string} - Date relative
 */
export function formatRelativeTime(date, withoutSuffix = false) {
  if (!date) return ''
  const d = dayjs(date)
  if (!d.isValid()) return ''
  return d.fromNow(withoutSuffix)
}

/**
 * Formate une date avec affichage conditionnel :
 * - Aujourd'hui : "Aujourd'hui à HH:mm"
 * - Hier : "Hier à HH:mm"
 * - Cette semaine : "Lundi à HH:mm"
 * - Cette année : "15 janvier à HH:mm"
 * - Autre : "15/01/2025 à HH:mm"
 * @param {string|Date|number} date - Date à formater
 * @returns {string} - Date formatée de manière contextuelle
 */
export function formatDateContextual(date) {
  if (!date) return ''
  const d = dayjs(date)
  if (!d.isValid()) return ''

  const now = dayjs()
  const diff = now.diff(d, 'day')

  if (diff === 0) {
    return `Aujourd'hui à ${d.format('HH:mm')}`
  }
  if (diff === 1) {
    return `Hier à ${d.format('HH:mm')}`
  }
  if (diff < 7) {
    return `${d.format('dddd')} à ${d.format('HH:mm')}`
  }
  if (d.year() === now.year()) {
    return `${d.format('D MMMM')} à ${d.format('HH:mm')}`
  }
  return d.format('DD/MM/YYYY à HH:mm')
}

/**
 * Formate une durée en millisecondes en chaîne lisible.
 * @param {number} ms - Durée en millisecondes
 * @param {boolean} short - Format court (ex: 2h 30m)
 * @returns {string} - Durée formatée
 */
export function formatDuration(ms, short = false) {
  if (!ms || ms < 0) return '0s'
  const dur = dayjs.duration(ms)
  const hours = Math.floor(dur.asHours())
  const minutes = dur.minutes()
  const seconds = dur.seconds()

  if (short) {
    const parts = []
    if (hours > 0) parts.push(`${hours}h`)
    if (minutes > 0) parts.push(`${minutes}m`)
    if (seconds > 0 && hours === 0) parts.push(`${seconds}s`)
    return parts.join(' ') || '0s'
  }

  const parts = []
  if (hours > 0) parts.push(`${hours} heure${hours > 1 ? 's' : ''}`)
  if (minutes > 0) parts.push(`${minutes} minute${minutes > 1 ? 's' : ''}`)
  if (seconds > 0 && hours === 0) parts.push(`${seconds} seconde${seconds > 1 ? 's' : ''}`)
  return parts.join(' ') || '0 seconde'
}

/**
 * Formate une durée en secondes en chaîne lisible.
 * @param {number} seconds - Durée en secondes
 * @param {boolean} short - Format court
 * @returns {string} - Durée formatée
 */
export function formatDurationSeconds(seconds, short = false) {
  return formatDuration(seconds * 1000, short)
}

// ==========================================================================
//  Formateurs de nombres
// ==========================================================================

/**
 * Formate un nombre avec séparateur de milliers.
 * @param {number} num - Nombre à formater
 * @param {number} decimals - Nombre de décimales
 * @param {string} locale - Locale (défaut: 'fr-FR')
 * @returns {string} - Nombre formaté
 */
export function formatNumber(num, decimals = 0, locale = 'fr-FR') {
  if (num === undefined || num === null) return ''
  if (isNaN(num)) return '0'
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num)
}

/**
 * Formate un nombre en pourcentage.
 * @param {number} num - Nombre (0-1)
 * @param {number} decimals - Nombre de décimales
 * @returns {string} - Pourcentage formaté
 */
export function formatPercent(num, decimals = 0) {
  if (num === undefined || num === null) return ''
  if (isNaN(num)) return '0%'
  const percent = num * 100
  return `${formatNumber(percent, decimals)}%`
}

/**
 * Formate une progression (0-100) avec une barre visuelle.
 * @param {number} progress - Progression (0-100)
 * @param {number} width - Largeur de la barre en caractères
 * @returns {string} - Barre de progression ASCII
 */
export function formatProgressBar(progress, width = 20) {
  const clamped = Math.max(0, Math.min(100, progress))
  const filled = Math.round((clamped / 100) * width)
  const empty = width - filled
  return `[${'█'.repeat(filled)}${'░'.repeat(empty)}] ${Math.round(clamped)}%`
}

// ==========================================================================
//  Formateurs de taille de fichiers
// ==========================================================================

/**
 * Formate une taille en octets en chaîne lisible (B, KB, MB, GB, TB).
 * @param {number} bytes - Taille en octets
 * @param {number} decimals - Nombre de décimales
 * @param {string} locale - Locale (défaut: 'fr-FR')
 * @returns {string} - Taille formatée
 */
export function formatFileSize(bytes, decimals = 1, locale = 'fr-FR') {
  if (bytes === 0 || bytes === undefined || bytes === null) return '0 B'
  if (isNaN(bytes) || bytes < 0) return '0 B'
  const k = 1024
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const size = bytes / Math.pow(k, i)
  const formatted = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(size)
  return `${formatted} ${units[i]}`
}

/**
 * Formate une taille de fichier avec notation plus naturelle.
 * @param {number} bytes - Taille en octets
 * @returns {string} - Taille formatée
 */
export function formatFileSizeNatural(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  if (bytes < 1024 * 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  return `${(bytes / (1024 * 1024 * 1024 * 1024)).toFixed(1)} TB`
}

// ==========================================================================
//  Formateurs de texte
// ==========================================================================

/**
 * Tronque un texte à une longueur maximale avec points de suspension.
 * @param {string} text - Texte à tronquer
 * @param {number} maxLength - Longueur maximale
 * @param {string} suffix - Suffixe ajouté si tronqué (défaut: '…')
 * @returns {string} - Texte tronqué
 */
export function truncate(text, maxLength = 50, suffix = '…') {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - suffix.length).trim() + suffix
}

/**
 * Capitalise la première lettre d'une chaîne.
 * @param {string} text - Texte à capitaliser
 * @returns {string} - Texte capitalisé
 */
export function capitalize(text) {
  if (!text) return ''
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase()
}

/**
 * Capitalise la première lettre de chaque mot.
 * @param {string} text - Texte à formater
 * @returns {string} - Texte en title case
 */
export function titleCase(text) {
  if (!text) return ''
  return text
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Convertit une chaîne en slug (pour les URLs, IDs).
 * @param {string} text - Texte à slugifier
 * @param {string} separator - Séparateur (défaut: '-')
 * @returns {string} - Slug
 */
export function slugify(text, separator = '-') {
  if (!text) return ''
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Supprime les accents
    .replace(/[^a-z0-9\s]/g, '') // Supprime les caractères spéciaux
    .trim()
    .replace(/\s+/g, separator)
}

/**
 * Convertit une chaîne en format kebab-case.
 * @param {string} text - Texte à convertir
 * @returns {string} - Texte en kebab-case
 */
export function kebabCase(text) {
  return slugify(text, '-')
}

/**
 * Convertit une chaîne en format snake_case.
 * @param {string} text - Texte à convertir
 * @returns {string} - Texte en snake_case
 */
export function snakeCase(text) {
  return slugify(text, '_')
}

/**
 * Échappe les caractères HTML spéciaux.
 * @param {string} text - Texte à échapper
 * @returns {string} - Texte échappé
 */
export function escapeHtml(text) {
  if (!text) return ''
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  }
  return text.replace(/[&<>"']/g, m => map[m])
}

// ==========================================================================
//  Formateurs de couleurs
// ==========================================================================

/**
 * Convertit une couleur hexadécimale en RGB.
 * @param {string} hex - Couleur hex (ex: #ff0000)
 * @returns {Object|null} - { r, g, b } ou null
 */
export function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!result) return null
  return {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16),
  }
}

/**
 * Convertit une couleur RGB en hexadécimale.
 * @param {number} r - Rouge (0-255)
 * @param {number} g - Vert (0-255)
 * @param {number} b - Bleu (0-255)
 * @returns {string} - Couleur hex
 */
export function rgbToHex(r, g, b) {
  const toHex = (c) => {
    const hex = Math.round(c).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

/**
 * Retourne une couleur de statut en fonction d'une valeur.
 * @param {number} value - Valeur (0-100)
 * @returns {string} - Couleur CSS
 */
export function getStatusColor(value) {
  if (value >= 90) return '#4caf50' // vert
  if (value >= 70) return '#8bc34a' // vert clair
  if (value >= 50) return '#ffeb3b' // jaune
  if (value >= 30) return '#ff9800' // orange
  return '#f44336' // rouge
}

// ==========================================================================
//  Formateurs de téléchargement
// ==========================================================================

/**
 * Formate une vitesse de téléchargement.
 * @param {number} bytesPerSecond - Vitesse en octets par seconde
 * @param {number} decimals - Nombre de décimales
 * @returns {string} - Vitesse formatée (ex: "2.5 MB/s")
 */
export function formatSpeed(bytesPerSecond, decimals = 1) {
  if (!bytesPerSecond || bytesPerSecond < 0) return '0 B/s'
  const speed = Math.abs(bytesPerSecond)
  const units = ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s']
  const i = Math.floor(Math.log(speed) / Math.log(1024))
  const formatted = (speed / Math.pow(1024, i)).toFixed(decimals)
  return `${formatted} ${units[i]}`
}

/**
 * Formate un temps restant estimé.
 * @param {number} seconds - Temps restant en secondes
 * @returns {string} - Temps formaté (ex: "2h 30m")
 */
export function formatETA(seconds) {
  if (!seconds || seconds < 0) return '--'
  const dur = dayjs.duration(seconds, 'seconds')
  const hours = Math.floor(dur.asHours())
  const minutes = dur.minutes()
  const secs = dur.seconds()

  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`
  }
  return `${Math.round(secs)}s`
}

// ==========================================================================
//  Formateurs divers
// ==========================================================================

/**
 * Formate un nombre de chapitres.
 * @param {number} count - Nombre de chapitres
 * @returns {string} - Nombre formaté avec libellé
 */
export function formatChapters(count) {
  if (!count || count < 0) return '0 chapitre'
  return `${count} chapitre${count > 1 ? 's' : ''}`
}

/**
 * Formate un nombre de pages.
 * @param {number} count - Nombre de pages
 * @returns {string} - Nombre formaté avec libellé
 */
export function formatPages(count) {
  if (!count || count < 0) return '0 page'
  return `${count} page${count > 1 ? 's' : ''}`
}

/**
 * Formate un nom de fichier (supprime l'extension).
 * @param {string} filename - Nom de fichier
 * @returns {string} - Nom sans extension
 */
export function formatFileName(filename) {
  if (!filename) return ''
  return filename.replace(/\.[^.]+$/, '')
}

/**
 * Retourne une note sous forme d'étoiles (0-10).
 * @param {number} rating - Note (0-10)
 * @param {number} maxStars - Nombre maximum d'étoiles (défaut: 5)
 * @returns {string} - Chaîne d'étoiles
 */
export function formatStars(rating, maxStars = 5) {
  if (!rating || rating < 0) return '☆☆☆☆☆'
  const stars = Math.round((rating / 10) * maxStars)
  const full = '★'.repeat(Math.min(stars, maxStars))
  const empty = '☆'.repeat(Math.max(0, maxStars - stars))
  return full + empty
}

/**
 * Retourne une note sous forme d'étoiles HTML.
 * @param {number} rating - Note (0-10)
 * @param {number} maxStars - Nombre maximum d'étoiles (défaut: 5)
 * @param {number} size - Taille en pixels
 * @returns {string} - HTML des étoiles
 */
export function formatStarsHtml(rating, maxStars = 5, size = 16) {
  if (!rating || rating < 0) rating = 0
  const starCount = Math.round((rating / 10) * maxStars)
  const full = starCount
  const empty = maxStars - starCount
  return `<span style="display:inline-flex;gap:2px;font-size:${size}px;color:#ffc107;">
    ${'★'.repeat(full)}${'☆'.repeat(empty)}
  </span>`
}

// ==========================================================================
//  Formateurs de statut
// ==========================================================================

/**
 * Retourne un libellé de statut pour un job.
 * @param {string} status - Statut du job
 * @returns {string} - Libellé traduit
 */
export function formatJobStatus(status) {
  const map = {
    pending: 'En attente',
    running: 'En cours',
    completed: 'Terminé',
    failed: 'Échec',
    cancelled: 'Annulé',
    waiting: 'En attente',
    paused: 'En pause',
  }
  return map[status] || status
}

/**
 * Retourne une classe CSS pour un statut de job.
 * @param {string} status - Statut du job
 * @returns {string} - Classe CSS
 */
export function getJobStatusClass(status) {
  const map = {
    pending: 'status-pending',
    running: 'status-running',
    completed: 'status-completed',
    failed: 'status-failed',
    cancelled: 'status-cancelled',
    waiting: 'status-waiting',
    paused: 'status-paused',
  }
  return map[status] || 'status-unknown'
}

/**
 * Retourne un icône pour un statut de job.
 * @param {string} status - Statut du job
 * @returns {string} - Emoji/icône
 */
export function getJobStatusIcon(status) {
  const map = {
    pending: '⏳',
    running: '🔄',
    completed: '✅',
    failed: '❌',
    cancelled: '⛔',
    waiting: '⏸️',
    paused: '⏸️',
  }
  return map[status] || '❓'
}

// ==========================================================================
//  Export par défaut
// ==========================================================================

export default {
  // Dates
  formatDate,
  formatDateShort,
  formatDateLong,
  formatTime,
  formatDateTime,
  formatRelativeTime,
  formatDateContextual,
  formatDuration,
  formatDurationSeconds,

  // Nombres
  formatNumber,
  formatPercent,
  formatProgressBar,

  // Fichiers
  formatFileSize,
  formatFileSizeNatural,

  // Texte
  truncate,
  capitalize,
  titleCase,
  slugify,
  kebabCase,
  snakeCase,
  escapeHtml,

  // Couleurs
  hexToRgb,
  rgbToHex,
  getStatusColor,

  // Téléchargement
  formatSpeed,
  formatETA,

  // Divers
  formatChapters,
  formatPages,
  formatFileName,
  formatStars,
  formatStarsHtml,

  // Statut
  formatJobStatus,
  getJobStatusClass,
  getJobStatusIcon,
}
