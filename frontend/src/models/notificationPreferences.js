// src/models/notificationPreferences.js

/**
 * Notification channel constants
 */
export const NOTIFICATION_CHANNELS = {
  EMAIL: 'email',
  IN_APP: 'in-app',
  BOTH: 'both',
}

/**
 * Default reminder times (in days before deadline)
 */
export const DEFAULT_REMINDER_TIMES = [7, 3, 1]

/**
 * Valid notification channels array
 */
export const VALID_CHANNELS = Object.values(NOTIFICATION_CHANNELS)

/**
 * NotificationPreferences class definition
 */
export class NotificationPreferences {
  constructor({
    userId = '',
    channel = NOTIFICATION_CHANNELS.BOTH,
    reminderTimes = DEFAULT_REMINDER_TIMES,
    enabled = true,
    taskDeadlineReminders = true,
    taskUpdateReminders = true,
    taskCommentNotifications = true,
    createdAt = Date.now(),
    updatedAt = Date.now(),
  } = {}) {
    this.userId = userId
    this.channel = this.validateChannel(channel)
    this.reminderTimes = this.validateReminderTimes(reminderTimes)
    this.enabled = enabled
    this.taskDeadlineReminders = taskDeadlineReminders
    this.taskUpdateReminders = taskUpdateReminders
    this.taskCommentNotifications = taskCommentNotifications
    this.createdAt = createdAt
    this.updatedAt = updatedAt
  }

  /**
   * Validate notification channel
   * @param {string} channel - The channel to validate
   * @returns {string} Valid channel or default to BOTH
   */
  validateChannel(channel) {
    return VALID_CHANNELS.includes(channel) ? channel : NOTIFICATION_CHANNELS.BOTH
  }

  /**
   * Validate reminder times array
   * @param {Array<number>} times - The reminder times to validate
   * @returns {Array<number>} Valid times array in descending order
   */
  validateReminderTimes(times) {
    // Ensure times is an array
    if (!Array.isArray(times)) {
      return [...DEFAULT_REMINDER_TIMES]
    }

    // Filter valid times (1-365 days)
    const validTimes = times.filter(time =>
      typeof time === 'number' && time >= 1 && time <= 365
    )

    // If no valid times, return default
    if (validTimes.length === 0) {
      return [...DEFAULT_REMINDER_TIMES]
    }

    // Sort in descending order and remove duplicates
    const sortedTimes = [...new Set(validTimes)].sort((a, b) => b - a)

    return sortedTimes
  }

  /**
   * Check if email notifications are enabled
   * @returns {boolean}
   */
  hasEmailEnabled() {
    return this.enabled && (this.channel === NOTIFICATION_CHANNELS.EMAIL || this.channel === NOTIFICATION_CHANNELS.BOTH)
  }

  /**
   * Check if in-app notifications are enabled
   * @returns {boolean}
   */
  hasInAppEnabled() {
    return this.enabled && (this.channel === NOTIFICATION_CHANNELS.IN_APP || this.channel === NOTIFICATION_CHANNELS.BOTH)
  }

  /**
   * Get reminder times display text
   * @returns {string}
   */
  getReminderTimesDisplay() {
    if (!this.reminderTimes || this.reminderTimes.length === 0) {
      return 'No reminders set'
    }

    return this.reminderTimes
      .map(time => `${time} ${time === 1 ? 'day' : 'days'}`)
      .join(', ')
  }

  /**
   * Get channel display text
   * @returns {string}
   */
  getChannelDisplay() {
    const channelMap = {
      [NOTIFICATION_CHANNELS.EMAIL]: 'Email Only',
      [NOTIFICATION_CHANNELS.IN_APP]: 'In-App Only',
      [NOTIFICATION_CHANNELS.BOTH]: 'Email & In-App',
    }
    return channelMap[this.channel] || 'Email & In-App'
  }

  /**
   * Convert to Firebase object for storage
   * @returns {Object}
   */
  toFirebaseObject() {
    return {
      userId: this.userId,
      channel: this.channel,
      reminderTimes: this.reminderTimes,
      enabled: this.enabled,
      taskDeadlineReminders: this.taskDeadlineReminders,
      taskUpdateReminders: this.taskUpdateReminders,
      taskCommentNotifications: this.taskCommentNotifications,
      createdAt: this.createdAt,
      updatedAt: Date.now(),
    }
  }

  /**
   * Create NotificationPreferences instance from Firebase data
   * @param {Object} data - Firebase notification preferences data
   * @returns {NotificationPreferences}
   */
  static fromFirebaseData(data) {
    return new NotificationPreferences(data)
  }

  /**
   * Update preferences
   * @param {Object} updates - Fields to update
   * @returns {NotificationPreferences} Updated instance
   */
  update(updates) {
    const allowedFields = ['channel', 'reminderTimes', 'enabled', 'taskDeadlineReminders', 'taskUpdateReminders', 'taskCommentNotifications']

    allowedFields.forEach((field) => {
      if (updates.hasOwnProperty(field)) {
        if (field === 'channel') {
          this[field] = this.validateChannel(updates[field])
        } else if (field === 'reminderTimes') {
          this[field] = this.validateReminderTimes(updates[field])
        } else {
          this[field] = updates[field]
        }
      }
    })

    this.updatedAt = Date.now()
    return this
  }

  /**
   * Clone instance
   * @returns {NotificationPreferences}
   */
  clone() {
    return new NotificationPreferences(this.toFirebaseObject())
  }
}

/**
 * Factory function to create a new NotificationPreferences instance
 * @param {Object} data - Notification preferences data
 * @returns {NotificationPreferences}
 */
export const createNotificationPreferences = (data = {}) => {
  return new NotificationPreferences(data)
}

/**
 * Default notification preferences template
 */
export const DEFAULT_NOTIFICATION_PREFERENCES = {
  channel: NOTIFICATION_CHANNELS.BOTH,
  reminderTimes: DEFAULT_REMINDER_TIMES,
  enabled: true,
  taskDeadlineReminders: true,
  taskUpdateReminders: true,
  taskCommentNotifications: true,
}
