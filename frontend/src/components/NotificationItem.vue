<!-- src/components/NotificationItem.vue -->

<template>
  <div
    @click="handleClick"
    :class="[
      'group relative p-4 rounded-xl transition-all duration-300 cursor-pointer',
      'border-2',
      notification.isUnread()
        ? 'bg-blue-50/50 border-blue-200 hover:bg-blue-100/50'
        : 'bg-white border-gray-200 hover:bg-gray-50',
      'hover:shadow-md'
    ]"
  >
    <!-- Unread indicator dot -->
    <div
      v-if="notification.isUnread()"
      class="absolute top-4 right-4 w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse"
    ></div>

    <!-- Notification content -->
    <div class="flex items-start space-x-3">
      <!-- Icon based on urgency -->
      <div
        :class="[
          'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center',
          'transition-all duration-300 group-hover:scale-110',
          getUrgencyIconBg()
        ]"
      >
        <component
          :is="getUrgencyIcon()"
          :class="['w-5 h-5', getUrgencyIconColor()]"
          :stroke-width="2"
        />
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <!-- Title -->
        <div class="flex items-start justify-between">
          <h4
            :class="[
              'text-sm font-semibold',
              notification.isUnread() ? 'text-gray-900' : 'text-gray-600'
            ]"
          >
            {{ notification.title }}
          </h4>
        </div>

        <!-- Task title -->
        <p
          :class="[
            'mt-1 text-sm font-medium',
            notification.isUnread() ? 'text-gray-700' : 'text-gray-500'
          ]"
        >
          {{ notification.taskTitle }}
        </p>

        <!-- Deadline info -->
        <div class="mt-2 flex flex-wrap items-center gap-2 text-xs">
          <!-- Due date -->
          <div class="flex items-center space-x-1 text-gray-600">
            <Calendar class="w-3.5 h-3.5" :stroke-width="2" />
            <span>{{ notification.getFormattedDeadline() }}</span>
          </div>

          <!-- Time remaining with urgency badge -->
          <div
            :class="[
              'flex items-center space-x-1 px-2 py-0.5 rounded-full font-medium',
              getUrgencyBadgeClasses()
            ]"
          >
            <Clock class="w-3.5 h-3.5" :stroke-width="2" />
            <span>{{ notification.getTimeRemainingText() }}</span>
          </div>
        </div>

        <!-- Timestamp -->
        <div class="mt-2 flex items-center text-xs text-gray-400">
          <span>{{ notification.getFormattedCreatedAt() }}</span>
        </div>
      </div>

      <!-- Action button (Mark as read or Delete) -->
      <button
        v-if="notification.isUnread()"
        @click.stop="handleMarkAsRead"
        class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 p-1.5 rounded-lg hover:bg-blue-100 text-gray-400 hover:text-blue-600"
        title="Mark as read"
      >
        <Eye class="w-4 h-4" :stroke-width="2" />
      </button>
      <button
        v-else
        @click.stop="handleDelete"
        class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 p-1.5 rounded-lg hover:bg-red-100 text-gray-400 hover:text-red-600"
        title="Delete notification"
      >
        <X class="w-4 h-4" :stroke-width="2" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { Clock, Calendar, X, Eye, AlertCircle, Bell, AlertTriangle } from 'lucide-vue-next'
import { Notification } from '@/models/notification'

const props = defineProps({
  notification: {
    type: Notification,
    required: true
  }
})

const emit = defineEmits(['click', 'delete', 'markAsRead'])

const handleClick = () => {
  emit('click', props.notification)
}

const handleDelete = () => {
  emit('delete', props.notification)
}

const handleMarkAsRead = () => {
  emit('markAsRead', props.notification)
}

const getUrgencyIcon = () => {
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

const getUrgencyIconBg = () => {
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

const getUrgencyIconColor = () => {
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

/* Pulse animation for unread indicator */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
