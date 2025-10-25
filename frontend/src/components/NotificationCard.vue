<!-- src/components/NotificationCard.vue -->

<template>
  <transition enter-active-class="transition ease-out duration-200"
    enter-from-class="transform opacity-0 scale-95 translate-y-2"
    enter-to-class="transform opacity-100 scale-100 translate-y-0" leave-active-class="transition ease-in duration-150"
    leave-from-class="transform opacity-100 scale-100 translate-y-0"
    leave-to-class="transform opacity-0 scale-95 translate-y-2">
    <div v-if="show"
      class="absolute right-0 mt-3 mb-3 w-96 max-h-[calc(100vh-6rem)] bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/50 z-50 origin-top-right flex flex-col">
      <!-- Header -->
      <div class="p-6 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-600 rounded-t-2xl flex-shrink-0">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-white">Notifications</h3>
          <button v-if="hasUnreadNotifications && currentView === 'unread'" @click="handleMarkAllAsRead"
            :disabled="loading"
            class="text-xs font-medium text-white/90 hover:text-white bg-white/20 hover:bg-white/30 px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-50">
            Mark all read
          </button>
        </div>

        <!-- View Toggle -->
        <div class="flex bg-white/20 rounded-xl p-1 border border-white/30">
          <button @click="currentView = 'unread'" :class="[
            'flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all duration-300',
            currentView === 'unread'
              ? 'bg-white text-blue-600 shadow-md'
              : 'text-white/90 hover:text-white hover:bg-white/10'
          ]">
            <div class="flex items-center justify-center space-x-2">
              <span>Unread</span>
              <span v-if="unreadCount > 0" class="px-2 py-0.5 rounded-full text-xs font-bold"
                :class="currentView === 'unread' ? 'bg-blue-100 text-blue-600' : 'bg-white/20 text-white'">
                {{ unreadCount }}
              </span>
            </div>
          </button>
          <button @click="currentView = 'read'" :class="[
            'flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all duration-300',
            currentView === 'read'
              ? 'bg-white text-blue-600 shadow-md'
              : 'text-white/90 hover:text-white hover:bg-white/10'
          ]">
            Read
          </button>
        </div>
      </div>

      <!-- Notification List -->
      <div class="overflow-y-auto rounded-b-2xl flex-1 min-h-0">
        <!-- Loading state -->
        <div v-if="loading" class="p-8 text-center">
          <div class="animate-spin mx-auto w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          <p class="mt-3 text-sm text-gray-500">Loading notifications...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="p-8 text-center">
          <AlertCircle class="mx-auto w-12 h-12 text-red-500 mb-3" :stroke-width="1.5" />
          <p class="text-sm text-gray-600 mb-3">{{ error }}</p>
          <button @click="loadNotifications"
            class="text-xs font-medium text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 px-4 py-2 rounded-lg transition-colors">
            Try again
          </button>
        </div>

        <!-- Empty state -->
        <div v-else-if="displayedNotifications.length === 0" class="p-8 text-center">
          <Bell class="mx-auto w-12 h-12 text-gray-300 mb-3" :stroke-width="1.5" />
          <p class="text-sm font-medium text-gray-600">No notifications</p>
          <p class="text-xs text-gray-400 mt-1">{{ currentView === 'unread' ? "You're all caught up!"
            : "No read notifications yet" }}</p>
        </div>

        <!-- Notifications list -->
        <div v-else class="p-3 space-y-2">
          <NotificationItem v-for="notification in displayedNotifications" :key="notification.notificationId"
            :notification="notification" @click="handleNotificationClick" @delete="handleNotificationDelete"
            @mark-as-read="handleMarkAsRead" @extension-responded="handleExtensionResponded" />
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>

import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, AlertCircle } from 'lucide-vue-next'
import NotificationItem from './NotificationItem.vue'
import { Notification } from '@/models/notification'
import { notificationService } from '@/services/notificationService'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'vue-toastification'

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['update:show', 'unreadCountChange'])

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

// State
const currentView = ref('unread')
const allNotifications = ref([])
const loading = ref(false)
const error = ref(null)
let refreshInterval = null


// Computed
const unreadNotifications = computed(() => {
  return allNotifications.value.filter(n => n.isUnread())
})

const readNotifications = computed(() => {
  return allNotifications.value.filter(n => !n.isUnread())
})

const displayedNotifications = computed(() => {
  return currentView.value === 'unread' ? unreadNotifications.value : readNotifications.value
})

const unreadCount = computed(() => unreadNotifications.value.length)

const hasUnreadNotifications = computed(() => unreadCount.value > 0)

// Methods
const loadNotifications = async () => {
  if (!authStore.user?.uid) {
    return
  }

  loading.value = true
  error.value = null

  try {
    const notifications = await notificationService.getAllNotifications(authStore.user.uid)

    // DEBUG: Log raw data BEFORE conversion
    console.log('=== BEFORE Notification.fromData() ===')
    const extensionReq = notifications.find(n => n.type === 'deadline_extension_request')
    if (extensionReq) {
      console.log('Raw extension request from backend:', extensionReq)
      console.log('actionable:', extensionReq.actionable)
      console.log('extensionRequestId:', extensionReq.extensionRequestId)
      console.log('extension_request_id:', extensionReq.extension_request_id)
      console.log('All keys:', Object.keys(extensionReq))
    }

    allNotifications.value = notifications.map(n => Notification.fromData(n))

    // DEBUG: Log AFTER conversion
    console.log('=== AFTER Notification.fromData() ===')
    const convertedExtReq = allNotifications.value.find(n => n.type === 'deadline_extension_request')
    if (convertedExtReq) {
      console.log('Converted extension request:', convertedExtReq)
      console.log('actionable:', convertedExtReq.actionable)
      console.log('extensionRequestId:', convertedExtReq.extensionRequestId)
    }

    emit('unreadCountChange', unreadCount.value)
    error.value = null
  } catch (err) {
    console.error('Failed to load notifications:', err)
    error.value = 'Unable to load notifications. Please try again.'
  } finally {
    loading.value = false
  }
}

const handleNotificationClick = async (notification) => {
  try {
    if (notification.isUnread()) {
      await notificationService.markNotificationAsRead(
        authStore.user.uid,
        notification.notificationId
      )

      const index = allNotifications.value.findIndex(
        n => n.notificationId === notification.notificationId
      )
      if (index !== -1) {
        allNotifications.value[index].read = true
        allNotifications.value[index].readAt = Date.now()
      }

      emit('unreadCountChange', unreadCount.value)
    }

    // Don't navigate for actionable extension requests - let user interact with buttons
    if (notification.isExtensionRequest() && notification.actionable) {
      return
    }

    if (notification.taskId || notification.itemId) {
      emit('update:show', false)
      router.push(`/tasks?taskId=${notification.taskId || notification.itemId}`)
    }
  } catch (err) {
    console.error('Failed to handle notification click:', err)
    toast.error('Failed to update notification')
  }
}

const handleMarkAsRead = async (notification) => {
  try {
    await notificationService.markNotificationAsRead(
      authStore.user.uid,
      notification.notificationId
    )

    const index = allNotifications.value.findIndex(
      n => n.notificationId === notification.notificationId
    )
    if (index !== -1) {
      allNotifications.value[index].read = true
      allNotifications.value[index].readAt = Date.now()
    }

    emit('unreadCountChange', unreadCount.value)
    toast.success('Marked as read')
  } catch (err) {
    console.error('Failed to mark notification as read:', err)
    toast.error('Failed to mark notification as read')
  }
}

const handleExtensionResponded = async (response) => {
  try {
    // Wait a bit for backend to create all notifications
    setTimeout(async () => {
      await loadNotifications()
      emit('unreadCountChange', unreadCount.value)

      // Show appropriate message
      if (response.status === 'approved') {
        toast.success('Extension approved! Deadline has been updated.')
      } else {
        toast.info('Extension request rejected.')
      }
    }, 1000) // Wait 1 second for backend processing
  } catch (err) {
    console.error('Failed to refresh notifications after extension response:', err)
  }
}


const handleNotificationDelete = async (notification) => {
  try {
    await notificationService.deleteNotification(
      authStore.user.uid,
      notification.notificationId
    )

    // Remove from local state
    allNotifications.value = allNotifications.value.filter(
      n => n.notificationId !== notification.notificationId
    )

    // Emit unread count change
    emit('unreadCountChange', unreadCount.value)

    toast.success('Notification deleted')
  } catch (err) {
    console.error('Failed to delete notification:', err)
    toast.error('Failed to delete notification')
  }
}

const handleMarkAllAsRead = async () => {
  if (!hasUnreadNotifications.value) return

  try {
    await notificationService.markAllNotificationsAsRead(authStore.user.uid)

    // Update local state
    allNotifications.value.forEach(notification => {
      if (notification.isUnread()) {
        notification.read = true
        notification.readAt = Date.now()
      }
    })

    // Emit unread count change
    emit('unreadCountChange', 0)

    toast.success('All notifications marked as read')
  } catch (err) {
    console.error('Failed to mark all as read:', err)
    toast.error('Failed to mark all notifications as read')
  }
}

// Start auto-refresh when card is shown
const startAutoRefresh = () => {
  // Refresh every 60 seconds when card is open
  refreshInterval = setInterval(() => {
    loadNotifications()
  }, 60000)
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

// Watch for show prop changes
watch(() => props.show, (newValue) => {
  if (newValue) {
    loadNotifications()
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

// Initial load if shown
onMounted(() => {
  if (props.show) {
    loadNotifications()
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
/* Scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #3b82f6, #8b5cf6);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to bottom, #2563eb, #7c3aed);
}

/* Smooth transitions */
* {
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
