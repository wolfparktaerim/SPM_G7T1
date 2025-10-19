// Password Policy Validation Utility
// Enforces organizational password requirements

/**
 * Password policy requirements:
 * - Minimum 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one number
 * - At least one special character
 */

export const PASSWORD_POLICY = {
  minLength: 8,
  requireUppercase: true,
  requireLowercase: true,
  requireNumber: true,
  requireSpecialChar: true,
  specialChars: '!@#$%^&*(),.?":{}|<>',
}

/**
 * Validates a password against the organization's password policy
 * @param {string} password - The password to validate
 * @returns {Object} - Validation result with isValid flag and errors array
 */
export const validatePassword = (password) => {
  const errors = []

  if (!password || password.length < PASSWORD_POLICY.minLength) {
    errors.push(`Password must be at least ${PASSWORD_POLICY.minLength} characters long`)
  }

  if (PASSWORD_POLICY.requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter')
  }

  if (PASSWORD_POLICY.requireLowercase && !/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter')
  }

  if (PASSWORD_POLICY.requireNumber && !/\d/.test(password)) {
    errors.push('Password must contain at least one number')
  }

  if (PASSWORD_POLICY.requireSpecialChar && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>)')
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

/**
 * Calculates password strength on a scale of 0-4
 * @param {string} password - The password to evaluate
 * @returns {number} - Strength level (0=none, 1=weak, 2=fair, 3=good, 4=strong)
 */
export const calculatePasswordStrength = (password) => {
  if (!password) return 0

  // If password is less than minimum length, it's always weak (strength 1)
  if (password.length < PASSWORD_POLICY.minLength) return 1

  let strength = 0

  // Check each criterion
  if (password.length >= PASSWORD_POLICY.minLength) strength++
  if (/[A-Z]/.test(password)) strength++
  if (/[a-z]/.test(password)) strength++
  if (/\d/.test(password)) strength++
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++

  return Math.min(strength, 4)
}

/**
 * Gets a human-readable description of password strength
 * @param {number} strength - Strength level (0-4)
 * @returns {string} - Description of the strength level
 */
export const getStrengthDescription = (strength) => {
  switch (strength) {
    case 0:
      return 'No password'
    case 1:
      return 'Weak password'
    case 2:
      return 'Fair password'
    case 3:
      return 'Good password'
    case 4:
      return 'Strong password'
    default:
      return 'Unknown strength'
  }
}

/**
 * Gets the color class for password strength display
 * @param {number} strength - Strength level (0-4)
 * @returns {string} - Tailwind CSS color class
 */
export const getStrengthColor = (strength) => {
  if (strength <= 1) return 'bg-red-400'
  if (strength <= 2) return 'bg-yellow-400'
  if (strength <= 3) return 'bg-blue-400'
  return 'bg-green-400'
}

/**
 * Gets the text color class for password strength display
 * @param {number} strength - Strength level (0-4)
 * @returns {string} - Tailwind CSS text color class
 */
export const getStrengthTextColor = (strength) => {
  if (strength <= 1) return 'text-red-600'
  if (strength <= 2) return 'text-yellow-600'
  if (strength <= 3) return 'text-blue-600'
  return 'text-green-600'
}
