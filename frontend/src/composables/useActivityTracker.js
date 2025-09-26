import { onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth.js'

export function useActivityTracker() {
  const authStore = useAuthStore()

  const activityEvents = [
    'mousedown',
    'mousemove',
    'keypress',
    'scroll',
    'touchstart',
    'click'
  ]

  let throttleTimer = null

  const handleUserActivity = () => {
    // Throttle activity detection to avoid excessive resets
    if (throttleTimer) return

    throttleTimer = setTimeout(() => {
      throttleTimer = null
    }, 1000) // Throttle for 1 second

    // Reset session timeout if user is authenticated
    if (authStore.isAuthenticated) {
      authStore.resetSessionTimeout()
    }
  }

  const startTracking = () => {
    activityEvents.forEach(event => {
      document.addEventListener(event, handleUserActivity, { passive: true })
    })
  }

  const stopTracking = () => {
    activityEvents.forEach(event => {
      document.removeEventListener(event, handleUserActivity)
    })

    if (throttleTimer) {
      clearTimeout(throttleTimer)
      throttleTimer = null
    }
  }

  onMounted(startTracking)
  onUnmounted(stopTracking)

  return {
    startTracking,
    stopTracking
  }
}