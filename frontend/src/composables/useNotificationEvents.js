// Composable for notification event handling
// Provides a simple event bus for triggering notification badge updates

import { ref } from 'vue'

// Create a reactive event emitter
const notificationUpdateTrigger = ref(0)

export function useNotificationEvents() {
  // Trigger a notification update (increments counter to trigger reactivity)
  const triggerNotificationUpdate = () => {
    notificationUpdateTrigger.value++
  }

  // Subscribe to notification updates (returns the reactive ref)
  const onNotificationUpdate = () => {
    return notificationUpdateTrigger
  }

  return {
    triggerNotificationUpdate,
    onNotificationUpdate
  }
}
