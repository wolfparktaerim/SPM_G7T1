<template>
  <div v-if="showWarning" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-lg shadow-2xl max-w-md w-full p-6">
      <div class="flex items-center mb-4">
        <div class="bg-yellow-100 p-2 rounded-full">
          <Clock class="h-6 w-6 text-yellow-600" />
        </div>
        <h3 class="ml-3 text-lg font-semibold text-gray-900">Session Expiring Soon</h3>
      </div>

      <p class="text-gray-600 mb-6">
        Your session will expire in <strong>{{ Math.ceil(timeLeft / 1000) }} seconds</strong> due to inactivity.
        Do you want to stay logged in?
      </p>

      <div class="flex space-x-3">
        <button
          @click="extendSession"
          class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          Stay Logged In
        </button>
        <button
          @click="logoutNow"
          class="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors font-medium"
        >
          Log Out Now
        </button>
      </div>

      <div class="mt-4 bg-gray-200 rounded-full overflow-hidden">
        <div
          class="bg-yellow-400 h-2 transition-all duration-1000"
          :style="{ width: `${(timeLeft / warningDuration) * 100}%` }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Clock } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth.js'

const authStore = useAuthStore()

const showWarning = ref(false)
const timeLeft = ref(0)
const warningTimer = ref(null)
const countdownTimer = ref(null)

const warningDuration = 60000 // Show warning 1 minute before expiry

const extendSession = () => {
  // Update last activity and restart session timeout
  authStore.lastActivity = Date.now()
  authStore.resetSessionTimeout()
  hideWarning()
}

const logoutNow = async () => {
  hideWarning()
  await authStore.signOutUser()
}

const hideWarning = () => {
  showWarning.value = false
  timeLeft.value = 0

  if (countdownTimer.value) {
    clearInterval(countdownTimer.value)
    countdownTimer.value = null
  }
}

const startCountdown = () => {
  timeLeft.value = warningDuration

  countdownTimer.value = setInterval(async () => {
    timeLeft.value -= 1000

    if (timeLeft.value <= 0) {
      hideWarning()
      // Auto logout when timer expires
      await authStore.signOutUser()
    }
  }, 1000)
}

const checkSessionTimeout = () => {
  if (!authStore.isAuthenticated || !authStore.lastActivity) return

  const timeSinceActivity = Date.now() - authStore.lastActivity
  const timeUntilExpiry = authStore.SESSION_TIMEOUT - timeSinceActivity

  if (timeUntilExpiry <= warningDuration && timeUntilExpiry > 0) {
    showWarning.value = true
    startCountdown()
  }
}

onMounted(() => {
  // Check every 10 seconds for potential session timeout
  warningTimer.value = setInterval(checkSessionTimeout, 10000)
})

onUnmounted(() => {
  if (warningTimer.value) {
    clearInterval(warningTimer.value)
  }
  if (countdownTimer.value) {
    clearInterval(countdownTimer.value)
  }
})
</script>