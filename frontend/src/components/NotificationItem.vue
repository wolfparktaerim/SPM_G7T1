<!-- src/components/NotificationItem.vue -->

<template>
  <div @click="handleClick" :class="[
    'group relative p-4 rounded-xl transition-all duration-300 cursor-pointer',
    'border-2',
    notification.isUnread()
      ? 'bg-blue-50/50 border-blue-200 hover:bg-blue-100/50'
      : 'bg-white border-gray-200 hover:bg-gray-50',
    'hover:shadow-md'
  ]">
    <!-- Notification content -->
    <div class="flex items-start space-x-3">
      <!-- Icon based on type/urgency -->
      <div :class="[
        'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center',
        'transition-all duration-300 group-hover:scale-110',
        getIconBg()
      ]">
        <component :is="getIcon()" :class="['w-5 h-5', getIconColor()]" :stroke-width="2" />
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <!-- Title -->
        <div class="flex items-start justify-between">
          <h4 :class="[
            'text-sm font-semibold',
            notification.isUnread() ? 'text-gray-900' : 'text-gray-600'
          ]">
            {{ getNotificationTitle() }}
          </h4>
        </div>

        <!-- Task/Item title -->
        <p :class="[
          'mt-1 text-sm font-medium',
          notification.isUnread() ? 'text-gray-700' : 'text-gray-500'
        ]">
          {{ notification.taskTitle || notification.itemTitle }}
        </p>

        <!-- Parent task (for subtasks only) -->
        <p v-if="notification.parentTaskTitle" class="mt-1 text-xs text-gray-500">
          Part of task: <span class="font-medium text-gray-700">{{ notification.parentTaskTitle }}</span>
        </p>

        <!-- Extension Request Display -->
        <div v-if="notification.isExtensionRequest()" class="mt-3" @click.stop>

          <ExtensionRequestAction v-if="notification.actionable && extensionRequestData"
            :extension-request="extensionRequestData" :requester-name="notification.requesterName || 'User'"
            :item-title="notification.itemTitle || notification.taskTitle || 'Untitled'"
            @responded="handleExtensionResponse" />

          <!-- Loading state -->
          <div v-else-if="notification.actionable && !extensionRequestData" class="text-sm text-gray-500 italic">
            Loading extension request details...
          </div>
        </div>

        <!-- Extension Response Display -->
        <div v-else-if="notification.isExtensionResponse()" class="mt-2">
          <div :class="[
            'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium',
            notification.status === 'approved'
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          ]">
            <Check v-if="notification.status === 'approved'" class="w-4 h-4" />
            <X v-else class="w-4 h-4" />
            <span>{{ notification.status === 'approved' ? 'Approved' : 'Rejected' }}</span>
          </div>
          <div v-if="notification.rejectionReason" class="mt-2 text-xs text-gray-600 italic">
            Reason: {{ notification.rejectionReason }}
          </div>
        </div>

        <!-- Deadline Changed Display -->
        <div v-else-if="notification.isDeadlineChanged()" class="mt-2">
          <div
            class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium bg-blue-50 text-blue-800 border border-blue-200">
            <Calendar class="w-4 h-4" />
            <span>New Deadline: {{ getFormattedDeadline() }}</span>
          </div>
        </div>

        <!-- Status Update Info (for task/subtask status updates) -->
        <div v-else-if="isStatusUpdateNotification()" class="mt-2 flex items-center space-x-2 text-xs">
          <!-- Old status (crossed out) -->
          <span class="px-2 py-1 bg-gray-100 text-gray-500 rounded-lg line-through font-medium">
            {{ formatStatus(notification.oldStatus) }}
          </span>

          <!-- Arrow -->
          <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>

          <!-- New status -->
          <span :class="['px-2 py-1 rounded-lg font-medium', getStatusBadgeClasses(notification.newStatus)]">
            {{ formatStatus(notification.newStatus) }}
          </span>
        </div>

        <!-- Comment Info (for comment notifications) -->
        <div v-else-if="isCommentNotification()" class="mt-2 text-xs">
          <!-- Commenter name -->
          <div class="text-gray-600 mb-1">
            Comment by <span class="font-medium">{{ notification.commenterName }}</span>
          </div>

          <!-- Comment preview -->
          <div class="text-gray-500 line-clamp-2 italic">
            "{{ getCommentPreview() }}"
          </div>
        </div>

        <!-- Deadline info (for deadline reminders only) -->
        <div
          v-else-if="!notification.isExtensionRequest() && !notification.isExtensionResponse() && !notification.isDeadlineChanged()"
          class="mt-2 space-y-1 text-xs">
          <!-- Due date -->
          <div v-if="notification.taskDeadline" class="flex items-center space-x-1 text-gray-600">
            <Calendar class="w-3.5 h-3.5" :stroke-width="2" />
            <span>{{ notification.getFormattedDeadline() }}</span>
          </div>

          <!-- Time remaining with urgency badge -->
          <div v-if="notification.daysUntilDeadline !== null" :class="[
            'flex items-center space-x-1 px-2 py-0.5 rounded-full font-medium w-fit',
            getUrgencyBadgeClasses()
          ]">
            <Clock class="w-3.5 h-3.5" :stroke-width="2" />
            <span>{{ notification.getTimeRemainingText() }}</span>
          </div>
        </div>

        <!-- Message (for deadline changed and approved extension responses) -->
        <div
          v-if="notification.message && (notification.isDeadlineChanged() || (notification.isExtensionResponse() && notification.status === 'approved'))"
          class="mt-2 text-xs text-gray-600">
          {{ notification.message }}
        </div>
      </div>

      <!-- Action button (Mark as read or Delete) -->
      <button v-if="notification.isUnread()" @click.stop="handleMarkAsRead"
        class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 p-1.5 rounded-lg hover:bg-blue-100 text-gray-400 hover:text-blue-600"
        title="Mark as read">
        <Eye class="w-4 h-4" :stroke-width="2" />
      </button>
      <button v-else @click.stop="handleDelete"
        class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 p-1.5 rounded-lg hover:bg-red-100 text-gray-400 hover:text-red-600"
        title="Delete notification">
        <X class="w-4 h-4" :stroke-width="2" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Clock, Calendar, X, Eye, AlertCircle, Bell, AlertTriangle, MessageCircle, Check } from 'lucide-vue-next'
import { Notification } from '@/models/notification'
import ExtensionRequestAction from './task/ExtensionRequestAction.vue'

const props = defineProps({
  notification: {
    type: Notification,
    required: true
  }
})

const emit = defineEmits(['click', 'delete', 'markAsRead', 'extensionResponded'])

const API_BASE = (import.meta.env.VITE_BACKEND_API || '').replace(/\/+$/, '')

const extensionRequestData = ref(null)

onMounted(async () => {

  try {

    console.log("notification.extensionRequestId", props.notification.extensionRequestId)
    // Fetch extension request details
    const response = await axios.get(
      `${API_BASE}/extension-requests/${props.notification.extensionRequestId}`
    )
    extensionRequestData.value = response.data
    console.log("response data", response.data)
  } catch (error) {
    console.error('Failed to fetch extension request:', error)
  }
}
)

const handleClick = () => {
  emit('click', props.notification)
}

const handleDelete = () => {
  emit('delete', props.notification)
}

const handleMarkAsRead = () => {
  emit('markAsRead', props.notification)
}

const handleExtensionResponse = (response) => {
  emit('extensionResponded', response)
  // Mark as read after response
  emit('markAsRead', props.notification)
}

const getNotificationTitle = () => {
  if (props.notification.title) {
    return props.notification.title
  }

  // Generate title based on type
  if (props.notification.isExtensionRequest()) {
    return 'Deadline Extension Request'
  } else if (props.notification.isExtensionResponse()) {
    return props.notification.status === 'approved'
      ? 'Extension Request Approved'
      : 'Extension Request Rejected'
  } else if (props.notification.isDeadlineChanged()) {
    return 'Deadline Extended'
  } else if (isStatusUpdateNotification()) {
    return 'Status Updated'
  } else if (isCommentNotification()) {
    return 'New Comment'
  }

  return 'Notification'
}

const getFormattedDeadline = () => {
  // For deadline_changed notifications, use newDeadline
  const deadline = props.notification.isDeadlineChanged()
    ? props.notification.newDeadline
    : props.notification.taskDeadline

  if (!deadline) return 'N/A'
  const date = new Date(deadline * 1000)
  return date.toLocaleDateString('en-SG', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const isStatusUpdateNotification = () => {
  return props.notification.type === 'task_status_update' ||
    props.notification.type === 'subtask_status_update'
}

const isCommentNotification = () => {
  return props.notification.type === 'task_comment_notification' ||
    props.notification.type === 'subtask_comment_notification'
}

const getCommentPreview = () => {
  if (!props.notification.commentText) return ''
  const maxLength = 100
  return props.notification.commentText.length > maxLength
    ? props.notification.commentText.substring(0, maxLength) + '...'
    : props.notification.commentText
}

const formatStatus = (status) => {
  if (!status) return ''
  return status.replace(/_/g, ' ').split(' ').map(word =>
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

const getStatusBadgeClasses = (status) => {
  const statusColors = {
    'completed': 'bg-green-100 text-green-700',
    'ongoing': 'bg-blue-100 text-blue-700',
    'under_review': 'bg-purple-100 text-purple-700',
    'unassigned': 'bg-yellow-100 text-yellow-700'
  }
  return statusColors[status] || 'bg-gray-100 text-gray-700'
}

const getIcon = () => {
  // For extension requests, use clock icon
  if (props.notification.isExtensionRequest()) {
    return Clock
  }

  // For extension responses, use check/x icon
  if (props.notification.isExtensionResponse()) {
    return props.notification.status === 'approved' ? Check : X
  }

  // For deadline changed, use calendar icon
  if (props.notification.isDeadlineChanged()) {
    return Calendar
  }

  // For comment notifications, use message icon
  if (isCommentNotification()) {
    return MessageCircle
  }

  // For status updates, use bell icon
  if (isStatusUpdateNotification()) {
    return Bell
  }

  const urgency = props.notification.getUrgencyLevel()

  switch (urgency) {
    case 'overdue':
    case 'critical':
      return AlertCircle
    case 'urgent':
      return AlertTriangle
    default:
      return Bell
  }
}

const getIconBg = () => {
  // For extension requests, use amber background
  if (props.notification.isExtensionRequest()) {
    return 'bg-amber-100 group-hover:bg-amber-200'
  }

  // For extension responses, use appropriate color
  if (props.notification.isExtensionResponse()) {
    return props.notification.status === 'approved'
      ? 'bg-emerald-100 group-hover:bg-emerald-200'
      : 'bg-red-100 group-hover:bg-red-200'
  }

  // For deadline changed, use blue background
  if (props.notification.isDeadlineChanged()) {
    return 'bg-blue-100 group-hover:bg-blue-200'
  }

  // For comment notifications, use green background
  if (isCommentNotification()) {
    return 'bg-green-100 group-hover:bg-green-200'
  }

  // For status updates, use purple background
  if (isStatusUpdateNotification()) {
    return 'bg-purple-100 group-hover:bg-purple-200'
  }

  const urgency = props.notification.getUrgencyLevel()

  switch (urgency) {
    case 'overdue':
      return 'bg-red-100 group-hover:bg-red-200'
    case 'critical':
      return 'bg-orange-100 group-hover:bg-orange-200'
    case 'urgent':
      return 'bg-yellow-100 group-hover:bg-yellow-200'
    case 'warning':
      return 'bg-blue-100 group-hover:bg-blue-200'
    default:
      return 'bg-gray-100 group-hover:bg-gray-200'
  }
}

const getIconColor = () => {
  // For extension requests, use amber color
  if (props.notification.isExtensionRequest()) {
    return 'text-amber-600'
  }

  // For extension responses, use appropriate color
  if (props.notification.isExtensionResponse()) {
    return props.notification.status === 'approved'
      ? 'text-emerald-600'
      : 'text-red-600'
  }

  // For deadline changed, use blue color
  if (props.notification.isDeadlineChanged()) {
    return 'text-blue-600'
  }

  // For comment notifications, use green color
  if (isCommentNotification()) {
    return 'text-green-600'
  }

  // For status updates, use purple color
  if (isStatusUpdateNotification()) {
    return 'text-purple-600'
  }

  const urgency = props.notification.getUrgencyLevel()

  switch (urgency) {
    case 'overdue':
      return 'text-red-600'
    case 'critical':
      return 'text-orange-600'
    case 'urgent':
      return 'text-yellow-600'
    case 'warning':
      return 'text-blue-600'
    default:
      return 'text-gray-600'
  }
}

const getUrgencyBadgeClasses = () => {
  const urgency = props.notification.getUrgencyLevel()

  switch (urgency) {
    case 'overdue':
      return 'bg-red-100 text-red-700'
    case 'critical':
      return 'bg-orange-100 text-orange-700'
    case 'urgent':
      return 'bg-yellow-100 text-yellow-700'
    case 'warning':
      return 'bg-blue-100 text-blue-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}


</script>

<style scoped>
/* Smooth transitions */
* {
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
