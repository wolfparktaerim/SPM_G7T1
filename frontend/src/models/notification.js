// src/models/notification.js

/**
 * Notification model class
 */
export class Notification {
  constructor({
    notificationId = '',
    userId = '',
    taskId = '',
    type = 'task_deadline_reminder',
    title = '',
    message = '',
    taskTitle = '',
    taskDeadline = null,
    daysUntilDeadline = null,
    read = false,
    createdAt = Date.now(),
    readAt = null,
    parentTaskTitle = null,
  } = {}) {
    this.notificationId = notificationId
    this.userId = userId
    this.taskId = taskId
    this.type = type
    this.title = title
    this.message = message
    this.taskTitle = taskTitle
    this.taskDeadline = taskDeadline
    this.daysUntilDeadline = daysUntilDeadline
    this.read = read
    this.createdAt = createdAt
    this.readAt = readAt
    this.parentTaskTitle = parentTaskTitle
  }

  /**
   * Check if notification is unread
   * @returns {boolean}
   */
  isUnread() {
    return !this.read
  }

  /**
   * Get formatted deadline date
   * @returns {string}
   */
  getFormattedDeadline() {
    if (!this.taskDeadline) return 'N/A'

    const date = new Date(this.taskDeadline * 1000) // Convert epoch to milliseconds
    return date.toLocaleDateString('en-SG', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  /**
   * Get formatted time remaining text
   * @returns {string}
   */
  getTimeRemainingText() {
    if (this.daysUntilDeadline === null || this.daysUntilDeadline === undefined) {
      return 'N/A'
    }

    const days = this.daysUntilDeadline

    if (days < 0) {
      const overdueDays = Math.abs(Math.floor(days))
      return overdueDays === 1 ? '1 day overdue' : `${overdueDays} days overdue`
    } else if (days < 1) {
      const hours = Math.floor(days * 24)
      if (hours === 0) {
        return 'Due now'
      }
      return hours === 1 ? '1 hour left' : `${hours} hours left`
    } else {
      const wholeDays = Math.floor(days)
      return wholeDays === 1 ? '1 day left' : `${wholeDays} days left`
    }
  }

  /**
   * Get urgency level based on days until deadline
   * @returns {string} - 'critical', 'urgent', 'warning', 'normal', 'overdue'
   */
  getUrgencyLevel() {
    if (this.daysUntilDeadline === null || this.daysUntilDeadline === undefined) {
      return 'normal'
    }

    const days = this.daysUntilDeadline

    if (days < 0) return 'overdue'
    if (days < 1) return 'critical'
    if (days <= 2) return 'urgent'
    if (days <= 7) return 'warning'
    return 'normal'
  }

  /**
   * Get formatted creation date
   * @returns {string}
   */
  getFormattedCreatedAt() {
    const date = new Date(this.createdAt)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`

    return date.toLocaleDateString('en-SG', {
      month: 'short',
      day: 'numeric',
    })
  }

  /**
   * Create from Firebase/API data
   * @param {Object} data
   * @returns {Notification}
   */
  static fromData(data) {
    return new Notification({
      notificationId: data.notificationId || data.id,
      userId: data.userId,
      taskId: data.taskId,
      type: data.type,
      title: data.title,
      message: data.message,
      taskTitle: data.taskTitle,
      taskDeadline: data.taskDeadline,
      daysUntilDeadline: data.daysUntilDeadline,
      read: data.read || false,
      createdAt: data.createdAt,
      readAt: data.readAt,
      parentTaskTitle: data.parentTaskTitle,
    })
  }

  /**
   * Convert to plain object
   * @returns {Object}
   */
  toObject() {
    return {
      notificationId: this.notificationId,
      userId: this.userId,
      taskId: this.taskId,
      type: this.type,
      title: this.title,
      message: this.message,
      taskTitle: this.taskTitle,
      taskDeadline: this.taskDeadline,
      daysUntilDeadline: this.daysUntilDeadline,
      read: this.read,
      createdAt: this.createdAt,
      readAt: this.readAt,
      parentTaskTitle: this.parentTaskTitle,
    }
  }
}

export default Notification
