<template>
  <div id="app">
    <RouterView />
    <SessionTimeoutWarning
      :show-warning="showWarning"
      :time-left="timeLeft"
      :countdown-duration="COUNTDOWN_DURATION"
      @extend-session="extendSession"
      @logout-now="logoutNow"
    />
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import { onMounted, watch } from 'vue'
import SessionTimeoutWarning from '@/components/SessionTimeoutWarning.vue'
import { useSessionTimeout } from '@/composables/useSessionTimeout'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const {
  showWarning,
  timeLeft,
  COUNTDOWN_DURATION,
  startSessionTimeout,
  stopSessionTimeout,
  setupActivityListeners,
  extendSession,
  logoutNow
} = useSessionTimeout()

// Setup activity listeners to reset session timeout on user activity
let removeActivityListeners = null

onMounted(() => {
  // Temporarily disable activity listeners for testing
  // removeActivityListeners = setupActivityListeners()
  console.log('Activity listeners disabled for testing')
})

// Watch authentication state and manage session timeout
watch(() => authStore.isAuthenticated, (isAuth) => {
  console.log('Auth state changed:', isAuth)
  if (isAuth) {
    // User logged in - start session timeout
    console.log('User is authenticated, starting session timeout')
    startSessionTimeout()
  } else {
    // User logged out - stop session timeout
    console.log('User is not authenticated, stopping session timeout')
    stopSessionTimeout()
  }
}, { immediate: true })

// Cleanup on unmount
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (removeActivityListeners) {
    removeActivityListeners()
  }
  stopSessionTimeout()
})
</script>

<style scoped>
#app {
  height: 100vh;
  width: 100vw;
}
</style>
