// Password Reset Cleanup Utility
// Removes expired password reset requests from the database

import { ref as dbRef, get, remove, query, orderByChild, endAt } from 'firebase/database'
import { database } from '@/firebase/firebaseConfig'

/**
 * Cleans up expired password reset requests from the database
 * This helps maintain database hygiene and prevents accumulation of old data
 *
 * @returns {Promise<Object>} - Object containing cleanup statistics
 */
export const cleanupExpiredResetRequests = async () => {
  try {
    const now = Date.now()
    const resetRequestsRef = dbRef(database, 'passwordResetRequests')

    // Get all password reset requests
    const snapshot = await get(resetRequestsRef)

    if (!snapshot.exists()) {
      return {
        success: true,
        deletedCount: 0,
        message: 'No password reset requests found',
      }
    }

    const requests = snapshot.val()
    const expiredKeys = []

    // Find all expired requests
    Object.keys(requests).forEach((key) => {
      const request = requests[key]
      if (request.expiresAt && request.expiresAt < now) {
        expiredKeys.push(key)
      }
    })

    // Delete expired requests
    const deletionPromises = expiredKeys.map((key) => {
      const requestRef = dbRef(database, `passwordResetRequests/${key}`)
      return remove(requestRef)
    })

    await Promise.all(deletionPromises)

    return {
      success: true,
      deletedCount: expiredKeys.length,
      message: `Successfully deleted ${expiredKeys.length} expired password reset request(s)`,
    }
  } catch (error) {
    console.error('Error cleaning up expired reset requests:', error)
    return {
      success: false,
      deletedCount: 0,
      error: error.message,
      message: 'Failed to clean up expired password reset requests',
    }
  }
}

/**
 * Schedules automatic cleanup of expired password reset requests
 * Runs every hour by default
 *
 * @param {number} intervalMinutes - How often to run cleanup (default: 60 minutes)
 * @returns {number} - Interval ID that can be used to clear the interval
 */
export const scheduleAutoCleanup = (intervalMinutes = 60) => {
  const intervalMs = intervalMinutes * 60 * 1000

  // Run cleanup immediately on schedule
  cleanupExpiredResetRequests().then((result) => {
    console.log('Password reset cleanup:', result.message)
  })

  // Schedule recurring cleanup
  const intervalId = setInterval(async () => {
    const result = await cleanupExpiredResetRequests()
    console.log('Password reset cleanup:', result.message)
  }, intervalMs)

  console.log(`Password reset cleanup scheduled every ${intervalMinutes} minutes`)

  return intervalId
}

/**
 * Stops the automatic cleanup schedule
 * @param {number} intervalId - The interval ID returned by scheduleAutoCleanup
 */
export const stopAutoCleanup = (intervalId) => {
  if (intervalId) {
    clearInterval(intervalId)
    console.log('Password reset cleanup schedule stopped')
  }
}
