// src/services/notificationPreferencesService.js

import { ref as dbRef, set, get, update } from 'firebase/database'
import { database } from '@/firebase/firebaseConfig'
import { NotificationPreferences } from '@/models/notificationPreferences'

/**
 * Save notification preferences to Firebase
 * @param {string} userId - The user ID
 * @param {NotificationPreferences} preferences - The notification preferences object
 * @returns {Promise<void>}
 */
export const saveNotificationPreferences = async (userId, preferences) => {
  if (!userId) {
    throw new Error('User ID is required')
  }

  try {
    const preferencesRef = dbRef(database, `notificationPreferences/${userId}`)
    const data = preferences.toFirebaseObject()
    await set(preferencesRef, data)
    console.log('Notification preferences saved successfully')
  } catch (error) {
    console.error('Error saving notification preferences:', error)
    throw error
  }
}

/**
 * Get notification preferences from Firebase
 * @param {string} userId - The user ID
 * @returns {Promise<NotificationPreferences|null>}
 */
export const getNotificationPreferences = async (userId) => {
  if (!userId) {
    throw new Error('User ID is required')
  }

  try {
    const preferencesRef = dbRef(database, `notificationPreferences/${userId}`)
    const snapshot = await get(preferencesRef)

    if (snapshot.exists()) {
      const data = snapshot.val()
      return NotificationPreferences.fromFirebaseData(data)
    }

    return null
  } catch (error) {
    console.error('Error fetching notification preferences:', error)
    throw error
  }
}

/**
 * Update specific fields of notification preferences
 * @param {string} userId - The user ID
 * @param {Object} updates - Fields to update
 * @returns {Promise<void>}
 */
export const updateNotificationPreferences = async (userId, updates) => {
  if (!userId) {
    throw new Error('User ID is required')
  }

  try {
    const preferencesRef = dbRef(database, `notificationPreferences/${userId}`)
    const updateData = {
      ...updates,
      updatedAt: Date.now()
    }
    await update(preferencesRef, updateData)
    console.log('Notification preferences updated successfully')
  } catch (error) {
    console.error('Error updating notification preferences:', error)
    throw error
  }
}

/**
 * Delete notification preferences from Firebase
 * @param {string} userId - The user ID
 * @returns {Promise<void>}
 */
export const deleteNotificationPreferences = async (userId) => {
  if (!userId) {
    throw new Error('User ID is required')
  }

  try {
    const preferencesRef = dbRef(database, `notificationPreferences/${userId}`)
    await set(preferencesRef, null)
    console.log('Notification preferences deleted successfully')
  } catch (error) {
    console.error('Error deleting notification preferences:', error)
    throw error
  }
}
