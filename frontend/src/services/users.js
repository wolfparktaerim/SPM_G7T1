// src/services/users.js

import {
  ref as dbRef,
  set,
  get,
  update,
  remove,
  query,
  orderByChild,
  equalTo,
  onValue,
  off,
} from 'firebase/database'
import { database } from '@/firebase/firebaseConfig'
import { User, createUser, USER_ROLES } from '@/models/user.js'

/**
 * Users service for Firebase Realtime Database operations
 */
export class UsersService {
  constructor() {
    this.usersRef = dbRef(database, 'users')
  }

  /**
   * Create a new user in the database
   * @param {Object} userData - User data
   * @returns {Promise<User>} Created user instance
   */
  async createUser(userData) {
    try {
      // Validate user data
      const validation = User.validate(userData)
      if (!validation.isValid) {
        throw new Error(`Validation failed: ${validation.errors.join(', ')}`)
      }

      const user = createUser(userData)
      const userRef = dbRef(database, `users/${user.uid}`)

      await set(userRef, user.toFirebaseObject())

      console.log('User created successfully:', user.uid)
      return user
    } catch (error) {
      console.error('Error creating user:', error)
      throw new Error(`Failed to create user: ${error.message}`)
    }
  }

  /**
   * Get user by UID
   * @param {string} uid - User unique identifier
   * @returns {Promise<User|null>} User instance or null if not found
   */
  async getUserById(uid) {
    try {
      const userRef = dbRef(database, `users/${uid}`)
      const snapshot = await get(userRef)

      if (snapshot.exists()) {
        const userData = snapshot.val()
        return User.fromFirebaseData(userData)
      } else {
        console.log('User not found:', uid)
        return null
      }
    } catch (error) {
      console.error('Error getting user by ID:', error)
      throw new Error(`Failed to get user: ${error.message}`)
    }
  }

  /**
   * Get all users
   * @returns {Promise<User[]>} Array of user instances
   */
  async getAllUsers() {
    try {
      const snapshot = await get(this.usersRef)
      const users = []

      if (snapshot.exists()) {
        const usersData = snapshot.val()
        Object.keys(usersData).forEach((uid) => {
          users.push(User.fromFirebaseData(usersData[uid]))
        })
      }

      console.log(`Retrieved ${users.length} users`)
      return users
    } catch (error) {
      console.error('Error getting all users:', error)
      throw new Error(`Failed to get users: ${error.message}`)
    }
  }

  /**
   * Get users by department
   * @param {string} department - Department name
   * @returns {Promise<User[]>} Array of user instances
   */
  async getUsersByDepartment(department) {
    try {
      const departmentQuery = query(this.usersRef, orderByChild('department'), equalTo(department))

      const snapshot = await get(departmentQuery)
      const users = []

      if (snapshot.exists()) {
        const usersData = snapshot.val()
        Object.keys(usersData).forEach((uid) => {
          users.push(User.fromFirebaseData(usersData[uid]))
        })
      }

      console.log(`Retrieved ${users.length} users from ${department} department`)
      return users
    } catch (error) {
      console.error('Error getting users by department:', error)
      throw new Error(`Failed to get users by department: ${error.message}`)
    }
  }

  /**
   * Get users by role
   * @param {string} role - User role (staff, manager, director)
   * @returns {Promise<User[]>} Array of user instances
   */
  async getUsersByRole(role) {
    try {
      if (!Object.values(USER_ROLES).includes(role)) {
        throw new Error(`Invalid role: ${role}`)
      }

      const roleQuery = query(this.usersRef, orderByChild('role'), equalTo(role))

      const snapshot = await get(roleQuery)
      const users = []

      if (snapshot.exists()) {
        const usersData = snapshot.val()
        Object.keys(usersData).forEach((uid) => {
          users.push(User.fromFirebaseData(usersData[uid]))
        })
      }

      console.log(`Retrieved ${users.length} users with role: ${role}`)
      return users
    } catch (error) {
      console.error('Error getting users by role:', error)
      throw new Error(`Failed to get users by role: ${error.message}`)
    }
  }

  /**
   * Update user data
   * @param {string} uid - User unique identifier
   * @param {Object} updates - Fields to update
   * @returns {Promise<User>} Updated user instance
   */
  async updateUser(uid, updates) {
    try {
      // Get existing user first
      const existingUser = await this.getUserById(uid)
      if (!existingUser) {
        throw new Error('User not found')
      }

      // Update user instance
      const updatedUser = existingUser.update(updates)

      // Validate updated user data
      const validation = User.validate(updatedUser.toFirebaseObject())
      if (!validation.isValid) {
        throw new Error(`Validation failed: ${validation.errors.join(', ')}`)
      }

      // Update in database
      const userRef = dbRef(database, `users/${uid}`)
      await update(userRef, updatedUser.toFirebaseObject())

      console.log('User updated successfully:', uid)
      return updatedUser
    } catch (error) {
      console.error('Error updating user:', error)
      throw new Error(`Failed to update user: ${error.message}`)
    }
  }

  /**
   * Update specific user fields
   * @param {string} uid - User unique identifier
   * @param {Object} fields - Specific fields to update
   * @returns {Promise<boolean>} Success status
   */
  async updateUserFields(uid, fields) {
    try {
      const userRef = dbRef(database, `users/${uid}`)
      const updatesWithTimestamp = {
        ...fields,
        updatedAt: Date.now(),
      }

      await update(userRef, updatesWithTimestamp)

      console.log('User fields updated successfully:', uid)
      return true
    } catch (error) {
      console.error('Error updating user fields:', error)
      throw new Error(`Failed to update user fields: ${error.message}`)
    }
  }

  /**
   * Delete user by UID
   * @param {string} uid - User unique identifier
   * @returns {Promise<boolean>} Success status
   */
  async deleteUser(uid) {
    try {
      const userRef = dbRef(database, `users/${uid}`)

      // Check if user exists first
      const snapshot = await get(userRef)
      if (!snapshot.exists()) {
        throw new Error('User not found')
      }

      await remove(userRef)

      console.log('User deleted successfully:', uid)
      return true
    } catch (error) {
      console.error('Error deleting user:', error)
      throw new Error(`Failed to delete user: ${error.message}`)
    }
  }

  /**
   * Check if user exists
   * @param {string} uid - User unique identifier
   * @returns {Promise<boolean>} Whether user exists
   */
  async userExists(uid) {
    try {
      const userRef = dbRef(database, `users/${uid}`)
      const snapshot = await get(userRef)
      return snapshot.exists()
    } catch (error) {
      console.error('Error checking user existence:', error)
      return false
    }
  }

  /**
   * Get user count by role
   * @returns {Promise<Object>} Object with role counts
   */
  async getUserCountByRole() {
    try {
      const users = await this.getAllUsers()
      const counts = {
        [USER_ROLES.STAFF]: 0,
        [USER_ROLES.MANAGER]: 0,
        [USER_ROLES.DIRECTOR]: 0,
        total: users.length,
      }

      users.forEach((user) => {
        counts[user.role]++
      })

      return counts
    } catch (error) {
      console.error('Error getting user count by role:', error)
      throw new Error(`Failed to get user count: ${error.message}`)
    }
  }

  /**
   * Get unique departments
   * @returns {Promise<string[]>} Array of department names
   */
  async getDepartments() {
    try {
      const users = await this.getAllUsers()
      const departments = new Set()

      users.forEach((user) => {
        if (user.department && user.department.trim()) {
          departments.add(user.department.trim())
        }
      })

      return Array.from(departments).sort()
    } catch (error) {
      console.error('Error getting departments:', error)
      throw new Error(`Failed to get departments: ${error.message}`)
    }
  }

  /**
   * Search users by name or email
   * @param {string} searchTerm - Search term
   * @returns {Promise<User[]>} Array of matching users
   */
  async searchUsers(searchTerm) {
    try {
      const users = await this.getAllUsers()
      const lowerSearchTerm = searchTerm.toLowerCase()

      const matchingUsers = users.filter(
        (user) =>
          user.name.toLowerCase().includes(lowerSearchTerm) ||
          user.email.toLowerCase().includes(lowerSearchTerm) ||
          (user.displayName && user.displayName.toLowerCase().includes(lowerSearchTerm)),
      )

      console.log(`Found ${matchingUsers.length} users matching "${searchTerm}"`)
      return matchingUsers
    } catch (error) {
      console.error('Error searching users:', error)
      throw new Error(`Failed to search users: ${error.message}`)
    }
  }

  /**
   * Listen to real-time user updates
   * @param {string} uid - User unique identifier
   * @param {Function} callback - Callback function to handle updates
   * @returns {Function} Unsubscribe function
   */
  listenToUser(uid, callback) {
    const userRef = dbRef(database, `users/${uid}`)

    const unsubscribe = onValue(
      userRef,
      (snapshot) => {
        if (snapshot.exists()) {
          const userData = snapshot.val()
          const user = User.fromFirebaseData(userData)
          callback(user)
        } else {
          callback(null)
        }
      },
      (error) => {
        console.error('Error listening to user:', error)
        callback(null, error)
      },
    )

    return () => off(userRef, 'value', unsubscribe)
  }

  /**
   * Listen to all users real-time updates
   * @param {Function} callback - Callback function to handle updates
   * @returns {Function} Unsubscribe function
   */
  listenToAllUsers(callback) {
    const unsubscribe = onValue(
      this.usersRef,
      (snapshot) => {
        const users = []

        if (snapshot.exists()) {
          const usersData = snapshot.val()
          Object.keys(usersData).forEach((uid) => {
            users.push(User.fromFirebaseData(usersData[uid]))
          })
        }

        callback(users)
      },
      (error) => {
        console.error('Error listening to all users:', error)
        callback([], error)
      },
    )

    return () => off(this.usersRef, 'value', unsubscribe)
  }
}

// Export singleton instance
export const usersService = new UsersService()

// Export individual functions for convenience
export const {
  createUser: createUserInDB,
  getUserById,
  getAllUsers,
  getUsersByDepartment,
  getUsersByRole,
  updateUser,
  updateUserFields,
  deleteUser,
  userExists,
  getUserCountByRole,
  getDepartments,
  searchUsers,
  listenToUser,
  listenToAllUsers,
} = usersService
