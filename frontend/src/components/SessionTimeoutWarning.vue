<template>
  <div v-if="showWarning" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 transform transition-all duration-300 scale-100">
      <div class="flex items-center mb-4">
        <div class="bg-yellow-100 p-3 rounded-full">
          <Clock class="h-6 w-6 text-yellow-600" />
        </div>
        <h3 class="ml-3 text-lg font-semibold text-gray-900">Session Expiring Soon</h3>
      </div>

      <p class="text-gray-600 mb-6">
        Your session will expire in <strong class="text-red-600">{{ Math.ceil(timeLeft / 1000) }} seconds</strong> due to inactivity.
        Do you want to stay logged in?
      </p>

      <div class="flex space-x-3">
        <button
          @click="extendSession"
          class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Yes, Stay Logged In
        </button>
        <button
          @click="logoutNow"
          class="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors font-medium focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
        >
          Log Out Now
        </button>
      </div>

      <!-- Progress bar showing time remaining -->
      <div class="mt-4 bg-gray-200 rounded-full overflow-hidden">
        <div
          class="bg-gradient-to-r from-yellow-400 to-red-500 h-2 transition-all duration-1000"
          :style="{ width: `${(timeLeft / COUNTDOWN_DURATION) * 100}%` }"
        ></div>
      </div>

      <!-- Time remaining display -->
      <div class="mt-2 text-center">
        <span class="text-sm text-gray-500">
          Time remaining: {{ Math.ceil(timeLeft / 1000) }}s
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Clock } from 'lucide-vue-next'
import { useSessionTimeout } from '@/composables/useSessionTimeout'

// Use the session timeout composable
const {
  showWarning,
  timeLeft,
  COUNTDOWN_DURATION,
  extendSession,
  logoutNow
} = useSessionTimeout()
</script>