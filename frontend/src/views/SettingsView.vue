<template>
  <NavigationBar />
  <div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Page Header -->
      <div class="mb-8">
        <div class="flex items-center space-x-3 mb-2">
          <Settings class="w-8 h-8 text-blue-600" :stroke-width="2" />
          <h1 class="text-3xl font-bold text-gray-900">Settings</h1>
        </div>
        <p class="text-gray-600">Manage your account preferences and notification settings</p>
      </div>

      <!-- Settings Sections -->
      <div class="space-y-6">
        <!-- Loading State -->
        <div v-if="isLoading" class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>

        <!-- Notification Settings Card -->
        <div v-else class="bg-white/95 backdrop-blur-xl rounded-2xl shadow-xl border border-white/50 overflow-hidden">
          <!-- Section Header -->
          <div class="p-6 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-600">
            <div class="flex items-center space-x-3">
              <div class="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
                <Bell class="w-6 h-6 text-white" :stroke-width="2" />
              </div>
              <div class="flex-1">
                <h2 class="text-xl font-bold text-white">Notification Preferences</h2>
                <p class="text-sm text-blue-100">Configure how and when you receive notifications</p>
              </div>
            </div>
          </div>

          <!-- Settings Content -->
          <div class="p-6 space-y-6">
            <!-- Enable/Disable Notifications Toggle -->
            <div class="flex items-center justify-between pb-6 border-b border-gray-200">
              <div class="flex-1">
                <label class="block text-base font-semibold text-gray-900">
                  Task Deadline Reminders
                </label>
                <p class="text-sm text-gray-500 mt-1">
                  Receive notifications for upcoming task deadlines
                </p>
              </div>
              <button @click="toggleNotifications" type="button"
                class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                :class="preferences.enabled ? 'bg-blue-600' : 'bg-gray-200'">
                <span class="sr-only">Enable notifications</span>
                <span
                  class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                  :class="preferences.enabled ? 'translate-x-5' : 'translate-x-0'">
                </span>
              </button>
            </div>

            <!-- Notification Channel Selection -->
            <div :class="{ 'opacity-50 pointer-events-none': !preferences.enabled }">
              <label class="block text-base font-semibold text-gray-900 mb-4">
                Notification Channel
              </label>
              <p class="text-sm text-gray-500 mb-4">Choose how you want to receive notifications</p>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <label v-for="channelOption in channelOptions" :key="channelOption.value"
                  class="relative flex flex-col p-5 rounded-xl border-2 transition-all duration-300 cursor-pointer group"
                  :class="getChannelClass(channelOption.value)">
                  <div class="flex items-center space-x-3 mb-2">
                    <input type="radio" :value="channelOption.value" v-model="preferences.channel"
                      @change="savePreferences"
                      class="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500">
                    <component :is="channelOption.icon" class="w-5 h-5"
                      :class="preferences.channel === channelOption.value ? 'text-blue-600' : 'text-gray-500'"
                      :stroke-width="2" />
                  </div>
                  <div class="ml-7">
                    <span class="block text-sm font-semibold mb-1"
                      :class="preferences.channel === channelOption.value ? 'text-blue-900' : 'text-gray-900'">
                      {{ channelOption.label }}
                    </span>
                    <p class="text-xs text-gray-500">{{ channelOption.description }}</p>
                  </div>
                </label>
              </div>
            </div>

            <!-- Reminder Times Selection -->
            <div :class="{ 'opacity-50 pointer-events-none': !preferences.enabled }">
              <label class="block text-base font-semibold text-gray-900 mb-4">
                Reminder Times
              </label>
              <p class="text-sm text-gray-500 mb-4">
                You will receive reminders at each of these intervals before the deadline. Add up to 5 reminders.
              </p>

              <!-- Current Reminder Times -->
              <div class="space-y-3 mb-4">
                <div
                  v-for="(time, index) in preferences.reminderTimes"
                  :key="`reminder-${index}`"
                  class="flex items-center space-x-3 p-4 rounded-xl border-2 border-blue-200 bg-blue-50">
                  <Clock class="w-5 h-5 text-blue-600 flex-shrink-0" :stroke-width="2" />

                  <div class="flex-1">
                    <label :for="`reminder-${index}`" class="block text-xs font-medium text-gray-600 mb-1">
                      Reminder {{ index + 1 }}
                    </label>
                    <div class="flex items-center space-x-2">
                      <input
                        :id="`reminder-${index}`"
                        type="number"
                        v-model.number="preferences.reminderTimes[index]"
                        @blur="validateAndSaveReminderTimes"
                        @keyup.enter="validateAndSaveReminderTimes"
                        :min="index < preferences.reminderTimes.length - 1 ? preferences.reminderTimes[index + 1] + 1 : 1"
                        max="365"
                        class="block w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300"
                      />
                      <span class="text-sm text-gray-700 font-medium">
                        {{ time === 1 ? 'day' : 'days' }} before deadline
                      </span>
                    </div>
                    <p v-if="index < preferences.reminderTimes.length - 1" class="text-xs text-gray-500 mt-1">
                      Must be greater than {{ preferences.reminderTimes[index + 1] }} days
                    </p>
                  </div>

                  <button
                    v-if="preferences.reminderTimes.length > 1"
                    @click="removeReminderTime(index)"
                    type="button"
                    class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-300 flex-shrink-0"
                    title="Remove this reminder">
                    <XCircle class="w-5 h-5" :stroke-width="2" />
                  </button>
                </div>
              </div>

              <!-- Add New Reminder -->
              <div v-if="preferences.reminderTimes.length < 5" class="p-5 rounded-xl border-2 border-dashed border-gray-300 bg-gray-50">
                <div class="flex items-start space-x-4">
                  <div class="flex-1">
                    <label class="block text-sm font-semibold text-gray-900 mb-2">
                      Add Another Reminder
                    </label>
                    <div class="flex items-center space-x-3">
                      <input
                        type="number"
                        v-model.number="newReminderDays"
                        @keyup.enter="addReminderTime"
                        min="1"
                        max="365"
                        step="1"
                        placeholder="Enter days"
                        class="block w-32 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300"
                        :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': addReminderError }"
                      />
                      <span class="text-sm text-gray-600 font-medium">days before deadline</span>
                      <button
                        @click="addReminderTime"
                        type="button"
                        :disabled="isAddButtonDisabled"
                        class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed">
                        Add
                      </button>
                    </div>

                    <!-- Error Message -->
                    <p v-if="addReminderError" class="text-xs text-red-600 font-medium mt-2">
                      {{ addReminderError }}
                    </p>

                    <!-- Info Message -->
                    <p v-else class="text-xs text-gray-500 mt-2">
                      Reminders will be automatically sorted in descending order
                    </p>
                  </div>
                </div>
              </div>

              <p v-if="preferences.reminderTimes.length >= 5" class="text-sm text-amber-600 font-medium">
                Maximum of 5 reminders reached
              </p>
            </div>
          </div>
        </div>

        <!-- Additional Settings Cards can be added here -->
        <!-- Example: Account Settings, Privacy Settings, etc. -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, watch } from 'vue'
import { Bell, Settings, Mail, MessageSquare, Layers, Clock, CheckCircle, XCircle } from 'lucide-vue-next'
import NavigationBar from '@/components/NavigationBar.vue'
import {
  NotificationPreferences,
  NOTIFICATION_CHANNELS,
  DEFAULT_NOTIFICATION_PREFERENCES
} from '@/models/notificationPreferences'
import { useAuthStore } from '@/stores/auth'
import {
  saveNotificationPreferences,
  getNotificationPreferences
} from '@/services/notificationPreferencesService'
import { useToast } from 'vue-toastification'

// Auth store
const authStore = useAuthStore()

// Toast
const toast = useToast()

// Component state
const saveStatus = ref(null)
const newReminderDays = ref(null)
const isLoading = ref(false)

// Notification preferences
const preferences = reactive(new NotificationPreferences({
  ...DEFAULT_NOTIFICATION_PREFERENCES,
  userId: authStore.user?.uid || ''
}))

// Channel options
const channelOptions = [
  {
    value: NOTIFICATION_CHANNELS.BOTH,
    label: 'Email & In-App',
    description: 'Receive notifications via both channels',
    icon: Layers
  },
  {
    value: NOTIFICATION_CHANNELS.EMAIL,
    label: 'Email Only',
    description: 'Receive notifications via email',
    icon: Mail
  },
  {
    value: NOTIFICATION_CHANNELS.IN_APP,
    label: 'In-App Only',
    description: 'Receive notifications in the app',
    icon: MessageSquare
  }
]

/**
 * Get channel selection class
 */
const getChannelClass = (value) => {
  return preferences.channel === value
    ? 'border-blue-500 bg-blue-50 shadow-md ring-2 ring-blue-200'
    : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 hover:shadow-sm'
}

/**
 * Computed: Check if add button should be disabled
 */
const isAddButtonDisabled = computed(() => {
  if (!newReminderDays.value) return true
  if (!Number.isInteger(newReminderDays.value)) return true
  if (newReminderDays.value < 1 || newReminderDays.value > 365) return true
  if (preferences.reminderTimes.includes(newReminderDays.value)) return true
  return false
})

/**
 * Computed: Error message for add reminder input
 */
const addReminderError = computed(() => {
  if (!newReminderDays.value) return null

  if (!Number.isInteger(newReminderDays.value)) {
    return 'Value must be a whole number'
  }

  if (newReminderDays.value < 1) {
    return 'Value must be at least 1 day'
  }

  if (newReminderDays.value > 365) {
    return 'Value must not exceed 365 days'
  }

  if (preferences.reminderTimes.includes(newReminderDays.value)) {
    return 'This reminder already exists'
  }

  return null
})

/**
 * Add a new reminder time
 */
const addReminderTime = () => {
  if (newReminderDays.value && Number.isInteger(newReminderDays.value) && newReminderDays.value >= 1 && newReminderDays.value <= 365 && !preferences.reminderTimes.includes(newReminderDays.value)) {
    // Add the new time and let the model validate and sort
    preferences.reminderTimes = [...preferences.reminderTimes, newReminderDays.value]
    preferences.reminderTimes = preferences.validateReminderTimes(preferences.reminderTimes)
    newReminderDays.value = null
    savePreferences()
  }
}

/**
 * Remove a reminder time
 */
const removeReminderTime = (index) => {
  if (preferences.reminderTimes.length > 1) {
    preferences.reminderTimes = preferences.reminderTimes.filter((_, i) => i !== index)
    savePreferences()
  }
}

/**
 * Validate and save reminder times (ensures descending order)
 */
const validateAndSaveReminderTimes = () => {
  // Re-validate to ensure proper order and no duplicates
  preferences.reminderTimes = preferences.validateReminderTimes(preferences.reminderTimes)
  savePreferences()
}

/**
 * Toggle notifications on/off
 */
const toggleNotifications = () => {
  preferences.enabled = !preferences.enabled
  savePreferences()
}

/**
 * Save preferences to Firebase
 */
const savePreferences = async () => {
  if (!authStore.user?.uid) {
    console.error('No user logged in')
    toast.error('You must be logged in to save preferences')
    return
  }

  try {
    saveStatus.value = null
    isLoading.value = true

    await saveNotificationPreferences(authStore.user.uid, preferences)

    saveStatus.value = 'success'
    toast.success('Notification preferences saved successfully!')

    // Clear success message after 3 seconds
    setTimeout(() => {
      saveStatus.value = null
    }, 3000)
  } catch (error) {
    console.error('Failed to save notification preferences:', error)
    saveStatus.value = 'error'
    toast.error('Failed to save notification preferences')

    // Clear error message after 5 seconds
    setTimeout(() => {
      saveStatus.value = null
    }, 5000)
  } finally {
    isLoading.value = false
  }
}

/**
 * Load preferences from Firebase
 */
const loadPreferences = async () => {
  if (!authStore.user?.uid) {
    console.error('No user logged in')
    return
  }

  try {
    isLoading.value = true

    const savedPreferences = await getNotificationPreferences(authStore.user.uid)

    if (savedPreferences) {
      // Update preferences with saved data
      Object.assign(preferences, savedPreferences)
      console.log('Notification preferences loaded from Firebase')
    } else {
      // No saved preferences, use defaults
      console.log('No saved preferences found, using defaults')
    }
  } catch (error) {
    console.error('Failed to load notification preferences:', error)
    toast.error('Failed to load notification preferences')
  } finally {
    isLoading.value = false
  }
}

// Watch for user changes
watch(() => authStore.user?.uid, (newUid) => {
  if (newUid) {
    preferences.userId = newUid
    loadPreferences()
  }
})

// Lifecycle
onMounted(() => {
  loadPreferences()
})
</script>

<style scoped>
/* Toggle switch animation */
button[type="button"]:focus {
  outline: none;
}

/* Enhanced hover effects */
.group:hover {
  transform: translateY(-1px);
}

/* Status message fade in animation */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

div[class*="bg-green-50"],
div[class*="bg-red-50"] {
  animation: fadeIn 0.3s ease-out;
}

/* Card shadow effects */
.bg-white\/95:hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}
</style>
