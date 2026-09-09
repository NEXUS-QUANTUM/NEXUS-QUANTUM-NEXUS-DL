// ==========================================================================
//  NexusDL 2.0 - Validators Utils
//  Fichier : frontend/src/utils/validators.js
//  Description : Utilitaires de validation (formulaires, données, URLs, etc.)
//  Version : 2.0.0
// ==========================================================================

// ==========================================================================
//  Validateurs de base
// ==========================================================================

/**
 * Vérifie si une valeur n'est pas vide (null, undefined, chaîne vide, tableau vide).
 * @param {*} value - Valeur à vérifier
 * @returns {boolean}
 */
export function isNotEmpty(value) {
  if (value === null || value === undefined) return false
  if (typeof value === 'string') return value.trim().length > 0
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === 'object') return Object.keys(value).length > 0
  return true
}

/**
 * Vérifie si une valeur est un nombre valide.
 * @param {*} value - Valeur à vérifier
 * @param {boolean} allowNaN - Autoriser NaN (défaut: false)
 * @returns {boolean}
 */
export function isNumber(value, allowNaN = false) {
  if (typeof value === 'number') {
    return allowNaN ? true : !isNaN(value) && isFinite(value)
  }
  if (typeof value === 'string') {
    const num = Number(value)
    return allowNaN ? !isNaN(num) : !isNaN(num) && isFinite(num)
  }
  return false
}

/**
 * Vérifie si une valeur est un entier valide.
 * @param {*} value - Valeur à vérifier
 * @param {boolean} positive - Autoriser uniquement les entiers positifs
 * @returns {boolean}
 */
export function isInteger(value, positive = false) {
  if (!isNumber(value)) return false
  const num = Number(value)
  if (!Number.isInteger(num)) return false
  if (positive && num < 0) return false
  return true
}

/**
 * Vérifie si une valeur est un booléen (vrai ou faux).
 * @param {*} value - Valeur à vérifier
 * @returns {boolean}
 */
export function isBoolean(value) {
  return typeof value === 'boolean'
}

/**
 * Vérifie si une valeur est une chaîne de caractères.
 * @param {*} value - Valeur à vérifier
 * @param {boolean} allowEmpty - Autoriser une chaîne vide
 * @returns {boolean}
 */
export function isString(value, allowEmpty = true) {
  if (typeof value !== 'string') return false
  if (!allowEmpty && value.trim().length === 0) return false
  return true
}

/**
 * Vérifie si une valeur est une date valide.
 * @param {*} value - Valeur à vérifier
 * @returns {boolean}
 */
export function isValidDate(value) {
  if (value instanceof Date) return !isNaN(value.getTime())
  if (typeof value === 'string') {
    const date = new Date(value)
    return !isNaN(date.getTime())
  }
  if (typeof value === 'number') {
    const date = new Date(value)
    return !isNaN(date.getTime())
  }
  return false
}

// ==========================================================================
//  Validateurs d'emails
// ==========================================================================

/**
 * Vérifie si une chaîne est un email valide.
 * @param {string} email - Email à vérifier
 * @returns {boolean}
 */
export function isValidEmail(email) {
  if (!email || typeof email !== 'string') return false
  // Regex conforme à la spécification RFC 5322 (version simplifiée)
  const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/
  return emailRegex.test(email)
}

// ==========================================================================
//  Validateurs d'URL
// ==========================================================================

/**
 * Vérifie si une chaîne est une URL valide.
 * @param {string} url - URL à vérifier
 * @param {string[]} protocols - Protocoles autorisés (ex: ['http:', 'https:'])
 * @returns {boolean}
 */
export function isValidUrl(url, protocols = ['http:', 'https:']) {
  if (!url || typeof url !== 'string') return false
  try {
    const parsed = new URL(url)
    if (protocols && protocols.length > 0 && !protocols.includes(parsed.protocol)) {
      return false
    }
    // Vérifier que le hostname est présent
    if (!parsed.hostname) return false
    return true
  } catch (_) {
    return false
  }
}

/**
 * Vérifie si une URL est une URL de site de scan (manga/manhwa/webtoon).
 * @param {string} url - URL à vérifier
 * @returns {boolean}
 */
export function isValidScanUrl(url) {
  if (!isValidUrl(url)) return false
  // Vérifier si l'URL appartient à un domaine connu ou a une structure de scan
  const scanPatterns = [
    /manga|scan|manhwa|webtoon|comic|chapter|series|title|read|lecture/i,
    /sushiscan|asurascan|mangadex|nhentai|hentaizone|mangakakalot|batoto|comick/i,
  ]
  return scanPatterns.some(pattern => pattern.test(url))
}

/**
 * Vérifie si une URL est une URL de chapitre.
 * @param {string} url - URL à vérifier
 * @returns {boolean}
 */
export function isChapterUrl(url) {
  if (!isValidUrl(url)) return false
  const chapterPatterns = [
    /\/chapter-?[0-9]+/i,
    /\/ch-?[0-9]+/i,
    /\/capitulo-?[0-9]+/i,
    /\/read\/.*?\/[0-9]+/i,
    /\/lecture\/.*?\/chapter-?[0-9]+/i,
  ]
  return chapterPatterns.some(pattern => pattern.test(url))
}

/**
 * Extrait l'ID d'une galerie nHentai depuis une URL.
 * @param {string} url - URL nHentai
 * @returns {string|null} - ID ou null
 */
export function extractNHentaiId(url) {
  if (!isValidUrl(url)) return null
  const match = url.match(/\/g\/([0-9]+)/)
  return match ? match[1] : null
}

// ==========================================================================
//  Validateurs de mots de passe
// ==========================================================================

/**
 * Vérifie la force d'un mot de passe.
 * @param {string} password - Mot de passe à vérifier
 * @param {Object} options - Options de validation
 * @param {number} options.minLength - Longueur minimale (défaut: 6)
 * @param {number} options.maxLength - Longueur maximale (défaut: 128)
 * @param {boolean} options.requireUppercase - Exiger une majuscule (défaut: true)
 * @param {boolean} options.requireLowercase - Exiger une minuscule (défaut: true)
 * @param {boolean} options.requireDigit - Exiger un chiffre (défaut: true)
 * @param {boolean} options.requireSpecial - Exiger un caractère spécial (défaut: false)
 * @param {number} options.minScore - Score minimum pour considérer le mot de passe comme fort (0-4)
 * @returns {Object} - { valid: boolean, errors: string[], score: number }
 */
export function validatePasswordStrength(password, options = {}) {
  const {
    minLength = 6,
    maxLength = 128,
    requireUppercase = true,
    requireLowercase = true,
    requireDigit = true,
    requireSpecial = false,
    minScore = 3,
  } = options

  const errors = []
  let score = 0

  if (!password || typeof password !== 'string') {
    return { valid: false, errors: ['Le mot de passe est requis'], score: 0 }
  }

  const len = password.length
  if (len < minLength) {
    errors.push(`Le mot de passe doit contenir au moins ${minLength} caractères`)
  } else if (len > maxLength) {
    errors.push(`Le mot de passe ne doit pas dépasser ${maxLength} caractères`)
  } else {
    score += 1
  }

  const hasUppercase = /[A-Z]/.test(password)
  const hasLowercase = /[a-z]/.test(password)
  const hasDigit = /[0-9]/.test(password)
  const hasSpecial = /[^a-zA-Z0-9]/.test(password)

  if (requireUppercase && !hasUppercase) {
    errors.push('Le mot de passe doit contenir au moins une majuscule')
  } else if (hasUppercase) {
    score += 1
  }

  if (requireLowercase && !hasLowercase) {
    errors.push('Le mot de passe doit contenir au moins une minuscule')
  } else if (hasLowercase) {
    score += 1
  }

  if (requireDigit && !hasDigit) {
    errors.push('Le mot de passe doit contenir au moins un chiffre')
  } else if (hasDigit) {
    score += 1
  }

  if (requireSpecial && !hasSpecial) {
    errors.push('Le mot de passe doit contenir au moins un caractère spécial')
  } else if (hasSpecial) {
    score += 1
  }

  // Évaluer la diversité des caractères
  const uniqueChars = new Set(password).size
  if (uniqueChars >= 8) score += 0.5
  if (uniqueChars >= 12) score += 0.5

  // Éviter les mots de passe courants (version simplifiée)
  const commonPasswords = [
    'password', '123456', '123456789', 'qwerty', 'abc123', 'password123',
    'admin', 'welcome', 'letmein', 'monkey', 'dragon', 'master',
  ]
  if (commonPasswords.includes(password.toLowerCase())) {
    errors.push('Ce mot de passe est trop courant')
    score = Math.min(score, 1)
  }

  const valid = errors.length === 0 && score >= minScore

  return {
    valid,
    errors,
    score: Math.min(score, 5),
    strength: score >= 4 ? 'fort' : score >= 3 ? 'moyen' : score >= 2 ? 'faible' : 'très faible',
  }
}

/**
 * Vérifie si deux mots de passe correspondent.
 * @param {string} password - Premier mot de passe
 * @param {string} confirm - Confirmation
 * @returns {boolean}
 */
export function doPasswordsMatch(password, confirm) {
  return password === confirm
}

// ==========================================================================
//  Validateurs de noms d'utilisateur
// ==========================================================================

/**
 * Vérifie si un nom d'utilisateur est valide.
 * @param {string} username - Nom d'utilisateur
 * @param {Object} options - Options
 * @param {number} options.minLength - Longueur minimale (défaut: 3)
 * @param {number} options.maxLength - Longueur maximale (défaut: 50)
 * @param {RegExp} options.pattern - Motif autorisé (défaut: lettres, chiffres, underscore, tiret)
 * @returns {Object} - { valid: boolean, errors: string[] }
 */
export function validateUsername(username, options = {}) {
  const {
    minLength = 3,
    maxLength = 50,
    pattern = /^[a-zA-Z0-9_-]+$/,
  } = options

  const errors = []
  if (!username || typeof username !== 'string') {
    errors.push('Le nom d\'utilisateur est requis')
    return { valid: false, errors }
  }

  const len = username.length
  if (len < minLength) {
    errors.push(`Le nom d'utilisateur doit contenir au moins ${minLength} caractères`)
  }
  if (len > maxLength) {
    errors.push(`Le nom d'utilisateur ne doit pas dépasser ${maxLength} caractères`)
  }
  if (!pattern.test(username)) {
    errors.push('Le nom d\'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores')
  }
  return { valid: errors.length === 0, errors }
}

// ==========================================================================
//  Validateurs de chapitres
// ==========================================================================

/**
 * Vérifie si un numéro de chapitre est valide.
 * @param {*} value - Valeur à vérifier
 * @param {Object} options - Options
 * @param {number} options.min - Numéro minimum (défaut: 0)
 * @param {number} options.max - Numéro maximum (défaut: Infinity)
 * @param {boolean} options.integerOnly - Uniquement des entiers (défaut: false)
 * @returns {Object} - { valid: boolean, errors: string[] }
 */
export function validateChapterNumber(value, options = {}) {
  const { min = 0, max = Infinity, integerOnly = false } = options
  const errors = []
  if (value === undefined || value === null || value === '') {
    errors.push('Le numéro de chapitre est requis')
    return { valid: false, errors }
  }

  const num = Number(value)
  if (isNaN(num) || !isFinite(num)) {
    errors.push('Le numéro de chapitre doit être un nombre valide')
    return { valid: false, errors }
  }
  if (integerOnly && !Number.isInteger(num)) {
    errors.push('Le numéro de chapitre doit être un nombre entier')
  }
  if (num < min) {
    errors.push(`Le numéro de chapitre doit être au moins ${min}`)
  }
  if (num > max) {
    errors.push(`Le numéro de chapitre ne doit pas dépasser ${max}`)
  }
  return { valid: errors.length === 0, errors }
}

// ==========================================================================
//  Validateurs d'IDs (UUID, etc.)
// ==========================================================================

/**
 * Vérifie si une chaîne est un UUID (v4).
 * @param {string} id - ID à vérifier
 * @returns {boolean}
 */
export function isValidUUID(id) {
  if (!id || typeof id !== 'string') return false
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
  return uuidRegex.test(id)
}

/**
 * Vérifie si une chaîne est un ID numérique (entier positif).
 * @param {string|number} id - ID à vérifier
 * @returns {boolean}
 */
export function isValidNumericId(id) {
  if (id === undefined || id === null) return false
  const num = Number(id)
  return !isNaN(num) && isFinite(num) && num >= 0 && Number.isInteger(num)
}

// ==========================================================================
//  Validateurs de plages et limites
// ==========================================================================

/**
 * Vérifie si une valeur est comprise entre une plage minimale et maximale.
 * @param {number} value - Valeur à vérifier
 * @param {number} min - Minimum
 * @param {number} max - Maximum
 * @param {boolean} inclusive - Inclure les bornes (défaut: true)
 * @returns {boolean}
 */
export function isBetween(value, min, max, inclusive = true) {
  if (!isNumber(value)) return false
  const num = Number(value)
  if (inclusive) {
    return num >= min && num <= max
  }
  return num > min && num < max
}

/**
 * Vérifie si une valeur est inférieure ou égale à une limite.
 * @param {number} value - Valeur à vérifier
 * @param {number} limit - Limite
 * @param {boolean} inclusive - Inclure la limite (défaut: true)
 * @returns {boolean}
 */
export function isAtMost(value, limit, inclusive = true) {
  if (!isNumber(value)) return false
  const num = Number(value)
  return inclusive ? num <= limit : num < limit
}

/**
 * Vérifie si une valeur est supérieure ou égale à une limite.
 * @param {number} value - Valeur à vérifier
 * @param {number} limit - Limite
 * @param {boolean} inclusive - Inclure la limite (défaut: true)
 * @returns {boolean}
 */
export function isAtLeast(value, limit, inclusive = true) {
  if (!isNumber(value)) return false
  const num = Number(value)
  return inclusive ? num >= limit : num > limit
}

// ==========================================================================
//  Validateurs de fichiers
// ==========================================================================

/**
 * Vérifie si un fichier a une extension autorisée.
 * @param {File} file - Fichier à vérifier
 * @param {string[]} allowedExtensions - Liste des extensions autorisées (ex: ['.cbz', '.zip'])
 * @returns {boolean}
 */
export function hasValidExtension(file, allowedExtensions) {
  if (!file || !file.name) return false
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  return allowedExtensions.includes(ext)
}

/**
 * Vérifie si un fichier a une taille valide (inférieure à une limite).
 * @param {File} file - Fichier à vérifier
 * @param {number} maxSizeBytes - Taille maximale en octets
 * @returns {boolean}
 */
export function hasValidFileSize(file, maxSizeBytes) {
  if (!file || !file.size) return false
  return file.size <= maxSizeBytes
}

/**
 * Vérifie si un fichier est une image (type MIME).
 * @param {File} file - Fichier à vérifier
 * @returns {boolean}
 */
export function isImageFile(file) {
  if (!file || !file.type) return false
  return file.type.startsWith('image/')
}

/**
 * Vérifie si un fichier est un CBZ (extension .cbz ou type application/zip).
 * @param {File} file - Fichier à vérifier
 * @returns {boolean}
 */
export function isCbzFile(file) {
  if (!file) return false
  return file.name.toLowerCase().endsWith('.cbz') || file.type === 'application/zip'
}

// ==========================================================================
//  Validateurs génériques pour formulaires
// ==========================================================================

/**
 * Crée un validateur pour un champ de formulaire avec une règle donnée.
 * @param {Function} rule - Fonction de validation (valeur -> booléen ou objet)
 * @param {string} message - Message d'erreur si la règle échoue
 * @returns {Function} - Validateur pour use avec Vee-Validate ou similaire
 */
export function createValidator(rule, message) {
  return (value) => {
    const result = rule(value)
    if (typeof result === 'boolean') {
      return result ? true : message
    }
    if (typeof result === 'object' && result !== null) {
      if (result.valid !== undefined) {
        return result.valid ? true : (result.errors?.join(', ') || message)
      }
    }
    return result ? true : message
  }
}

// ==========================================================================
//  Validateurs de champs spécifiques (pour Vee-Validate)
// ==========================================================================

/**
 * Règle : champ requis (non vide).
 * @param {*} value - Valeur à vérifier
 * @returns {boolean}
 */
export function required(value) {
  return isNotEmpty(value)
}

/**
 * Règle : email valide.
 * @param {string} value - Email à vérifier
 * @returns {boolean}
 */
export function email(value) {
  return isValidEmail(value)
}

/**
 * Règle : URL valide.
 * @param {string} value - URL à vérifier
 * @returns {boolean}
 */
export function url(value) {
  return isValidUrl(value)
}

/**
 * Règle : longueur minimale (chaîne).
 * @param {number} min - Longueur minimale
 * @returns {Function} - Fonction de validation
 */
export function minLength(min) {
  return (value) => {
    if (typeof value !== 'string') return false
    return value.length >= min
  }
}

/**
 * Règle : longueur maximale (chaîne).
 * @param {number} max - Longueur maximale
 * @returns {Function} - Fonction de validation
 */
export function maxLength(max) {
  return (value) => {
    if (typeof value !== 'string') return false
    return value.length <= max
  }
}

/**
 * Règle : taille minimale de fichier (octets).
 * @param {number} minBytes - Taille minimale
 * @returns {Function} - Fonction de validation
 */
export function minFileSize(minBytes) {
  return (file) => {
    if (!file || !file.size) return false
    return file.size >= minBytes
  }
}

/**
 * Règle : taille maximale de fichier (octets).
 * @param {number} maxBytes - Taille maximale
 * @returns {Function} - Fonction de validation
 */
export function maxFileSize(maxBytes) {
  return (file) => {
    if (!file || !file.size) return false
    return file.size <= maxBytes
  }
}

/**
 * Règle : extension de fichier autorisée.
 * @param {string[]} allowedExtensions - Liste des extensions (ex: ['.cbz', '.zip'])
 * @returns {Function} - Fonction de validation
 */
export function allowedExtensions(allowedExtensions) {
  return (file) => {
    if (!file) return false
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    return allowedExtensions.includes(ext)
  }
}

// ==========================================================================
//  Validateurs d'objet (schémas)
// ==========================================================================

/**
 * Vérifie qu'un objet contient toutes les clés requises avec des valeurs non vides.
 * @param {Object} obj - Objet à vérifier
 * @param {string[]} requiredKeys - Liste des clés requises
 * @returns {Object} - { valid: boolean, missingKeys: string[] }
 */
export function validateObjectKeys(obj, requiredKeys) {
  const missingKeys = requiredKeys.filter(key => {
    const val = obj[key]
    return val === undefined || val === null || (typeof val === 'string' && val.trim() === '')
  })
  return {
    valid: missingKeys.length === 0,
    missingKeys,
  }
}

/**
 * Valide un schéma d'objet avec des règles personnalisées.
 * @param {Object} obj - Objet à valider
 * @param {Object} schema - Schéma { champ: validateur(value) => true/string }
 * @returns {Object} - { valid: boolean, errors: Object }
 */
export function validateObjectSchema(obj, schema) {
  const errors = {}
  let valid = true
  for (const [key, validator] of Object.entries(schema)) {
    const value = obj[key]
    const result = validator(value)
    if (result !== true) {
      errors[key] = typeof result === 'string' ? result : 'Champ invalide'
      valid = false
    }
  }
  return { valid, errors }
}

// ==========================================================================
//  Fonctions d'aide pour l'affichage des erreurs
// ==========================================================================

/**
 * Génère un message d'erreur à partir d'une règle et d'un champ.
 * @param {string} field - Nom du champ
 * @param {string} rule - Règle violée
 * @param {Object} params - Paramètres de la règle
 * @returns {string} - Message d'erreur
 */
export function getErrorMessage(field, rule, params = {}) {
  const fieldName = field.charAt(0).toUpperCase() + field.slice(1)
  const messages = {
    required: `${fieldName} est requis(e).`,
    email: `${fieldName} doit être une adresse email valide.`,
    url: `${fieldName} doit être une URL valide.`,
    minLength: `${fieldName} doit contenir au moins ${params.min} caractères.`,
    maxLength: `${fieldName} ne doit pas dépasser ${params.max} caractères.`,
    min: `${fieldName} doit être au moins ${params.min}.`,
    max: `${fieldName} ne doit pas dépasser ${params.max}.`,
    between: `${fieldName} doit être compris entre ${params.min} et ${params.max}.`,
    integer: `${fieldName} doit être un nombre entier.`,
    numeric: `${fieldName} doit être un nombre valide.`,
    fileSize: `La taille du fichier ${fieldName} doit être inférieure à ${params.maxSize} Mo.`,
    extension: `Le fichier ${fieldName} doit avoir une extension autorisée.`,
  }
  return messages[rule] || `${fieldName} est invalide.`
}

// ==========================================================================
//  Export par défaut
// ==========================================================================

export default {
  // Base
  isNotEmpty,
  isNumber,
  isInteger,
  isBoolean,
  isString,
  isValidDate,

  // Email
  isValidEmail,

  // URL
  isValidUrl,
  isValidScanUrl,
  isChapterUrl,
  extractNHentaiId,

  // Password
  validatePasswordStrength,
  doPasswordsMatch,

  // Username
  validateUsername,

  // Chapter
  validateChapterNumber,

  // IDs
  isValidUUID,
  isValidNumericId,

  // Ranges
  isBetween,
  isAtMost,
  isAtLeast,

  // File
  hasValidExtension,
  hasValidFileSize,
  isImageFile,
  isCbzFile,

  // Form validators
  createValidator,
  required,
  email,
  url,
  minLength,
  maxLength,
  minFileSize,
  maxFileSize,
  allowedExtensions,

  // Object
  validateObjectKeys,
  validateObjectSchema,

  // Helpers
  getErrorMessage,
}
