// src/services/notificationService.js

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const NOTIFICATION_SERVICE_URL = `${API_BASE_URL}/notification`

/**
 * Get all notifications for a user
 * @param {string} userId - The user ID
 * @returns {Promise<Array>} - Array of notification objects
 */
export const getAllNotifications = async (userId) => {
  if (!userId) {
    throw new Error('User ID is required')
  }

  try {
    const response = await axios.get(`${NOTIFICATION_SERVICE_URL}/notifications/${userId}`)
    return response.data.notifications || []
  } catch (error) {
    console.error('Error fetching notifications:', error)
    throw error
  }
}

/**
 * Get unread notifications for a user
 * @param {string} userId - The user ID
 * @returns {Promise<{notifications: Array, count: number}>}
 */
export const getUnreadNotifications = async (userId) => {
  if (!userId) {
    throw new Error('User ID is required')
  }

  try {
    const response = await axios.get(`${NOTIFICATION_SERVICE_URL}/notifications/${userId}/unread`)
    return {
      notifications: response.data.notifications || [],
      count: response.data.count || 0
    }
  } catch (error) {
    console.error('Error fetching unread notifications:', error)
    throw error
  }
}

/**
 * Mark a notification as read
 * @param {string} userId - The user ID
 * @param {string} notificationId - The notification ID
 * @returns {Promise<Object>} - Updated notification object
 */
export const markNotificationAsRead = async (userId, notificationId) => {
  if (!userId || !notificationId) {
    throw new Error('User ID and Notification ID are required')
  }

  try {
    const response = await axios.patch(
      `${NOTIFICATION_SERVICE_URL}/notifications/${userId}/${notificationId}/read`
    )
    return response.data.notification
  } catch (error) {
    console.error('Error marking notification as read:', error)
    throw error
  }
}

/**
 * Mark all notifications as read
 * @param {string} userId - The user ID
 * @returns {Promise<number>} - Count of notifications marked as read
 */
export const markAllNotificationsAsRead = async (userId) => {
  if (!userId) {
    throw new Error('User ID is required')
  }

  try {
    const response = await axios.patch(
      `${NOTIFICATION_SERVICE_URL}/notifications/${userId}/mark-all-read`
    )
    return response.data.count || 0
  } catch (error) {
    console.error('Error marking all notifications as read:', error)
    throw error
  }
}

/**
 * Delete a notification
 * @param {string} userId - The user ID
 * @param {string} notificationId - The notification ID
 * @returns {Promise<void>}
 */
export const deleteNotification = async (userId, notificationId) => {
  if (!userId || !notificationId) {
    throw new Error('User ID and Notification ID are required')
  }

  try {
    await axios.delete(
      `${NOTIFICATION_SERVICE_URL}/notifications/${userId}/${notificationId}`
    )
  } catch (error) {
    console.error('Error deleting notification:', error)
    throw error
  }
}

/**
 * Service object for easier imports
 */
export const notificationService = {
  getAllNotifications,
  getUnreadNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  deleteNotification
}

export default notificationService
