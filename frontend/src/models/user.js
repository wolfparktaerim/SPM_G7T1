// src/models/users.js

/**
 * User role constants
 */
export const USER_ROLES = {
  STAFF: 'staff',
  MANAGER: 'manager',
  DIRECTOR: 'director',
}

/**
 * Valid user roles array for validation
 */
export const VALID_ROLES = Object.values(USER_ROLES)

/**
 * Department constants
 */
export const DEPARTMENTS = {
  SALES: 'Sales',
  CONSULTANCY: 'Consultancy',
  SYSTEM_SOLUTIONING: 'System Solutioning',
  ENGINEERING_OPERATION: 'Engineering Operation',
  HR_AND_ADMIN: 'HR and Admin',
  FINANCE: 'Finance',
  IT: 'IT',
}

/**
 * Valid departments array for validation
 */
export const VALID_DEPARTMENTS = Object.values(DEPARTMENTS)

/**
 * User class definition
 */
export class User {
  constructor({
    uid = '',
    name = '',
    title = '',
    department = '',
    role = USER_ROLES.STAFF,
    email = '',
    displayName = '',
    photoURL = '',
    createdAt = Date.now(),
    lastLoginAt = Date.now(),
    updatedAt = Date.now(),
  } = {}) {
    // Firebase Auth fields
    this.uid = uid
    this.email = email
    this.displayName = displayName
    this.photoURL = photoURL
    this.createdAt = createdAt
    this.lastLoginAt = lastLoginAt

    // Custom user fields
    this.name = name
    this.title = title
    this.department = department
    this.role = this.validateRole(role)
    this.updatedAt = updatedAt
  }

  /**
   * Validate user role
   * @param {string} role - The role to validate
   * @returns {string} Valid role or default to STAFF
   */
  validateRole(role) {
    return VALID_ROLES.includes(role) ? role : USER_ROLES.STAFF
  }

  /**
   * Check if user is a staff member
   * @returns {boolean}
   */
  isStaff() {
    return this.role === USER_ROLES.STAFF
  }

  /**
   * Check if user is a manager
   * @returns {boolean}
   */
  isManager() {
    return this.role === USER_ROLES.MANAGER
  }

  /**
   * Check if user is a director
   * @returns {boolean}
   */
  isDirector() {
    return this.role === USER_ROLES.DIRECTOR
  }

  /**
   * Check if user has management privileges (manager or director)
   * @returns {boolean}
   */
  hasManagementAccess() {
    return this.isManager() || this.isDirector()
  }

  /**
   * Get user's full display name
   * @returns {string}
   */
  getFullDisplayName() {
    return this.name || this.displayName || this.email?.split('@')[0] || 'Unknown User'
  }

  /**
   * Get user's role display name (capitalized)
   * @returns {string}
   */
  getRoleDisplayName() {
    return this.role.charAt(0).toUpperCase() + this.role.slice(1)
  }

  /**
   * Convert user instance to plain object for Firebase storage
   * @returns {Object}
   */
  toFirebaseObject() {
    return {
      uid: this.uid,
      name: this.name,
      title: this.title,
      department: this.department,
      role: this.role,
      email: this.email,
      displayName: this.displayName,
      photoURL: this.photoURL,
      createdAt: this.createdAt,
      lastLoginAt: this.lastLoginAt,
      updatedAt: Date.now(),
    }
  }

  /**
   * Create User instance from Firebase data
   * @param {Object} data - Firebase user data
   * @returns {User}
   */
  static fromFirebaseData(data) {
    return new User(data)
  }

  /**
   * Validate user data object
   * @param {Object} userData - User data to validate
   * @returns {Object} Validation result with isValid and errors
   */
  static validate(userData) {
    const errors = []

    if (!userData.name || typeof userData.name !== 'string' || userData.name.trim().length === 0) {
      errors.push('Name is required and must be a non-empty string')
    }

    if (!userData.email || typeof userData.email !== 'string' || !userData.email.includes('@')) {
      errors.push('Valid email address is required')
    }

    if (userData.role && !VALID_ROLES.includes(userData.role)) {
      errors.push(`Role must be one of: ${VALID_ROLES.join(', ')}`)
    }

    if (userData.title && typeof userData.title !== 'string') {
      errors.push('Title must be a string')
    }

    if (userData.department && typeof userData.department !== 'string') {
      errors.push('Department must be a string')
    }

    return {
      isValid: errors.length === 0,
      errors,
    }
  }

  /**
   * Create a user with default values
   * @returns {User}
   */
  static createDefault() {
    return new User()
  }

  /**
   * Update user data
   * @param {Object} updates - Fields to update
   * @returns {User} Updated user instance
   */
  update(updates) {
    const allowedFields = ['name', 'title', 'department', 'role', 'displayName', 'photoURL']

    allowedFields.forEach((field) => {
      if (updates.hasOwnProperty(field)) {
        if (field === 'role') {
          this[field] = this.validateRole(updates[field])
        } else {
          this[field] = updates[field]
        }
      }
    })

    this.updatedAt = Date.now()
    return this
  }

  /**
   * Clone user instance
   * @returns {User}
   */
  clone() {
    return new User(this.toFirebaseObject())
  }
}

/**
 * Factory function to create a new User instance
 * @param {Object} userData - User data
 * @returns {User}
 */
export const createUser = (userData = {}) => {
  return new User(userData)
}

/**
 * Default user template for forms
 */
export const DEFAULT_USER = {
  name: '',
  title: '',
  department: '',
  role: USER_ROLES.STAFF,
  email: '',
  displayName: '',
  photoURL: '',
}
