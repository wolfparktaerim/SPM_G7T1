<template>
  <NavigationBar />
  <div>
    This is the dashboard view
  </div>
</template>

<script setup>
import { onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from 'vue-toastification'
import NavigationBar from '@/components/NavigationBar.vue'

const route = useRoute()
const toast = useToast()

onMounted(async () => {
  // Check if user just registered
  console.log('Dashboard mounted, route query:', route.query)

  await nextTick()

  if (route.query.newUser === 'true') {
    console.log('Showing welcome toast for new user')
    // Small delay to ensure everything is loaded
    setTimeout(() => {
      toast.success('Account created successfully! Welcome to Smart Task Management System.', {
        timeout: 5000,
        closeOnClick: true,
        pauseOnFocusLoss: false,
        pauseOnHover: true,
        draggable: true,
        draggablePercent: 0.6,
        showCloseButtonOnHover: false,
        hideProgressBar: false,
        closeButton: "button",
        icon: true
      })
    }, 500)
  }
})
</script>

<style scoped></style>
