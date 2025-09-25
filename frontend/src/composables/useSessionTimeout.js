// src/composables/useSessionTimeout.js
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

export function useSessionTimeout() {
  const authStore = useAuthStore()
  const router = useRouter()
  const toast = useToast()

  // Session configuration (2 minutes = 120,000 ms)
  const SESSION_DURATION = 2 * 60 * 1000 // 2 minutes
  const WARNING_TIME = 1 * 60 * 1000 // 1 minute (1 minute before expiry)
  const COUNTDOWN_DURATION = 60 * 1000 // 1 minute countdown

  // State
  const showWarning = ref(false)
  const timeLeft = ref(0)
  const sessionStartTime = ref(null)

  // Timers
  let sessionTimer = null
  let warningTimer = null
  let countdownTimer = null

  // Start session timeout
  const startSessionTimeout = () => {
    if (!authStore.isAuthenticated) return

    sessionStartTime.value = Date.now()

    // Clear any existing timers
    clearAllTimers()

    // Set timer to show warning at 14 minutes
    warningTimer = setTimeout(() => {
      showSessionWarning()
    }, WARNING_TIME)
  }

  // Show session warning popup
  const showSessionWarning = () => {
    if (!authStore.isAuthenticated) return

    showWarning.value = true
    timeLeft.value = COUNTDOWN_DURATION

    // Start countdown timer
    countdownTimer = setInterval(() => {
      timeLeft.value -= 1000

      if (timeLeft.value <= 0) {
        // Time's up - auto logout
        handleSessionExpiry()
      }
    }, 1000)
  }

  // Handle user clicking "Stay Logged In"
  const extendSession = () => {
    hideWarning()
    startSessionTimeout() // Restart the session timer
    toast.success('Session extended successfully!')
  }

  // Handle user clicking "Log Out Now"
  const logoutNow = async () => {
    hideWarning()
    clearAllTimers()

    try {
      await authStore.signOutUser()
      toast.success('Signed out successfully!')
      router.push('/')
    } catch (error) {
      console.error('Logout failed:', error)
      toast.error('Failed to sign out. Please try again.')
    }
  }

  // Handle session expiry (automatic logout)
  const handleSessionExpiry = async () => {
    hideWarning()
    clearAllTimers()

    try {
      await authStore.signOutUser()
      toast.warning('Session expired. Please sign in again.')
      router.push('/')
    } catch (error) {
      console.error('Session expiry logout failed:', error)
      router.push('/')
    }
  }

  // Hide warning popup
  const hideWarning = () => {
    showWarning.value = false
    timeLeft.value = 0

    if (countdownTimer) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }

  // Clear all timers
  const clearAllTimers = () => {
    if (sessionTimer) {
      clearTimeout(sessionTimer)
      sessionTimer = null
    }
    if (warningTimer) {
      clearTimeout(warningTimer)
      warningTimer = null
    }
    if (countdownTimer) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }

  // Reset session timeout (called when user is active)
  const resetSessionTimeout = () => {
    if (authStore.isAuthenticated) {
      startSessionTimeout()
    }
  }

  // Stop session timeout
  const stopSessionTimeout = () => {
    clearAllTimers()
    hideWarning()
    sessionStartTime.value = null
  }

  // Activity detection - reset timer on user activity
  const handleUserActivity = () => {
    if (authStore.isAuthenticated && sessionStartTime.value && !showWarning.value) {
      // Only reset if not currently showing warning
      resetSessionTimeout()
    }
  }

  // Setup activity listeners
  const setupActivityListeners = () => {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']

    events.forEach(event => {
      document.addEventListener(event, handleUserActivity, { passive: true })
    })

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleUserActivity)
      })
    }
  }

  // Cleanup function
  onUnmounted(() => {
    clearAllTimers()
  })

  return {
    // State
    showWarning,
    timeLeft,
    sessionStartTime,

    // Configuration
    SESSION_DURATION,
    WARNING_TIME,
    COUNTDOWN_DURATION,

    // Methods
    startSessionTimeout,
    stopSessionTimeout,
    resetSessionTimeout,
    extendSession,
    logoutNow,
    handleSessionExpiry,
    setupActivityListeners
  }
}