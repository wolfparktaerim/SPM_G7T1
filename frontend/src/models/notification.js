// src/models/notification.js

/**
 * Notification model class
 */
export class Notification {
  constructor({
    notificationId = '',
    userId = '',
    taskId = '',
    itemId = '', // For extension requests
    itemType = '', // 'task' or 'subtask' for extension requests
    itemTitle = '', // For extension requests
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
    oldStatus = null,
    newStatus = null,
    commentText = null,
    commenterName = null,
    commenterId = null,
    actionable = false, // For extension requests
    requesterId = null, // For extension requests
    requesterName = null, // For extension requests
    extensionRequestId = null, // For extension requests
    status = null, // For extension response (approved/rejected)
    rejectionReason = null, // For extension response
    newDeadline = null, // For deadline_changed notifications
  } = {}) {
    this.notificationId = notificationId
    this.userId = userId
    this.taskId = taskId || itemId // Support both formats
    this.itemId = itemId
    this.itemType = itemType
    this.itemTitle = itemTitle || taskTitle // Support both formats
    this.type = type
    this.title = title
    this.message = message
    this.taskTitle = taskTitle || itemTitle // Support both formats
    this.taskDeadline = taskDeadline
    this.daysUntilDeadline = daysUntilDeadline
    this.read = read
    this.createdAt = createdAt
    this.readAt = readAt
    this.parentTaskTitle = parentTaskTitle
    this.oldStatus = oldStatus
    this.newStatus = newStatus
    this.commentText = commentText
    this.commenterName = commenterName
    this.commenterId = commenterId
    this.actionable = actionable
    this.requesterId = requesterId
    this.requesterName = requesterName
    this.extensionRequestId = extensionRequestId
    this.status = status
    this.rejectionReason = rejectionReason
    this.newDeadline = newDeadline
  }

  /**
   * Check if notification is unread
   * @returns {boolean}
   */
  isUnread() {
    return !this.read
  }

  /**
   * Check if this is an extension request notification
   * @returns {boolean}
   */
  isExtensionRequest() {
    return this.type === 'deadline_extension_request'
  }

  /**
   * Check if this is an extension response notification
   * @returns {boolean}
   */
  isExtensionResponse() {
    return this.type === 'deadline_extension_response'
  }

  /**
   * Check if this is a deadline changed notification
   * @returns {boolean}
   */
  isDeadlineChanged() {
    return this.type === 'deadline_changed'
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
   * Handles both camelCase and snake_case field names
   * @param {Object} data
   * @returns {Notification}
   */
  static fromData(data) {
    // Helper function to get value from either camelCase or snake_case
    const get = (camelCase, snakeCase) => {
      return data[camelCase] ?? data[snakeCase] ?? null
    }

    return new Notification({
      notificationId: get('notificationId', 'notification_id') || data.id,
      userId: get('userId', 'user_id'),
      taskId: get('taskId', 'task_id') || get('itemId', 'item_id'),
      itemId: get('itemId', 'item_id'),
      itemType: get('itemType', 'item_type'),
      itemTitle: get('itemTitle', 'item_title'),
      type: data.type,
      title: data.title,
      message: data.message,
      taskTitle: get('taskTitle', 'task_title') || get('itemTitle', 'item_title'),
      taskDeadline: get('taskDeadline', 'task_deadline'),
      daysUntilDeadline: get('daysUntilDeadline', 'days_until_deadline'),
      read: data.read || false,
      createdAt: get('createdAt', 'created_at'),
      readAt: get('readAt', 'read_at'),
      parentTaskTitle: get('parentTaskTitle', 'parent_task_title'),
      oldStatus: get('oldStatus', 'old_status'),
      newStatus: get('newStatus', 'new_status'),
      commentText: get('commentText', 'comment_text'),
      commenterName: get('commenterName', 'commenter_name'),
      commenterId: get('commenterId', 'commenter_id'),
      actionable: data.actionable || false,
      requesterId: get('requesterId', 'requester_id'),
      requesterName: get('requesterName', 'requester_name'),
      extensionRequestId:
        get('extensionRequestId', 'extension_request_id') || get('requestId', 'request_id'),
      status: data.status,
      rejectionReason: get('rejectionReason', 'rejection_reason'),
      newDeadline: get('newDeadline', 'new_deadline'),
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
      itemId: this.itemId,
      itemType: this.itemType,
      itemTitle: this.itemTitle,
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
      oldStatus: this.oldStatus,
      newStatus: this.newStatus,
      commentText: this.commentText,
      commenterName: this.commenterName,
      commenterId: this.commenterId,
      actionable: this.actionable,
      requesterId: this.requesterId,
      requesterName: this.requesterName,
      extensionRequestId: this.extensionRequestId,
      status: this.status,
      rejectionReason: this.rejectionReason,
      newDeadline: this.newDeadline,
    }
  }
}

export default Notification
