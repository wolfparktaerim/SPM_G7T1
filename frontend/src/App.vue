<template>
  <div id="app">
    <RouterView />
    <SessionTimeoutWarning />
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import { onMounted, watch } from 'vue'
import SessionTimeoutWarning from '@/components/SessionTimeoutWarning.vue'
import { useSessionTimeout } from '@/composables/useSessionTimeout'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { startSessionTimeout, stopSessionTimeout, setupActivityListeners } = useSessionTimeout()

// Setup activity listeners to reset session timeout on user activity
let removeActivityListeners = null

onMounted(() => {
  removeActivityListeners = setupActivityListeners()
})

// Watch authentication state and manage session timeout
watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth) {
    // User logged in - start session timeout
    startSessionTimeout()
  } else {
    // User logged out - stop session timeout
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
