<!-- TestConfirmationModal.vue - Use this to test the ConfirmationModal component -->

<template>
  <div class="min-h-screen bg-gray-50 p-8">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold text-gray-900 mb-8">ConfirmationModal Component Test</h1>

      <!-- Test Buttons Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <button @click="openModal('danger', 'trash')"
          class="p-4 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors">
          Delete Action (Danger)
        </button>

        <button @click="openModal('warning', 'warning')"
          class="p-4 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors">
          Warning Action
        </button>

        <button @click="openModal('info', 'info')"
          class="p-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
          Info Action
        </button>

        <button @click="openModal('success', 'check')"
          class="p-4 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors">
          Success Action
        </button>

        <button @click="openModal('primary', 'mail')"
          class="p-4 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors">
          Primary Action (Mail)
        </button>

        <button @click="openLogoutModal()"
          class="p-4 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors">
          Logout Action
        </button>
      </div>

      <!-- Current Settings Display -->
      <div class="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 class="text-xl font-semibold mb-4">Current Modal Settings</h2>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div><strong>Variant:</strong> {{ currentVariant }}</div>
          <div><strong>Icon:</strong> {{ currentIcon }}</div>
          <div><strong>Title:</strong> {{ currentTitle }}</div>
          <div><strong>Loading:</strong> {{ isLoading ? 'Yes' : 'No' }}</div>
        </div>
      </div>

      <!-- Action Log -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold mb-4">Action Log</h2>
        <div class="space-y-2 max-h-40 overflow-y-auto">
          <div v-for="(action, index) in actionLog" :key="index" class="text-sm p-2 bg-gray-50 rounded">
            <span class="text-gray-500">{{ action.time }}</span> - {{ action.message }}
          </div>
          <div v-if="actionLog.length === 0" class="text-gray-500 text-sm">
            No actions yet. Click a button above to test the modal.
          </div>
        </div>
        <button @click="clearLog"
          class="mt-4 px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors text-sm">
          Clear Log
        </button>
      </div>
    </div>

    <!-- The Modal Component -->
    <ConfirmationModal :show="showModal" :title="currentTitle" :description="currentDescription"
      :warning-text="currentWarningText" :confirm-text="currentConfirmText" :cancel-text="currentCancelText"
      :loading-text="currentLoadingText" :loading="isLoading" :variant="currentVariant" :icon="currentIcon"
      @confirm="handleConfirm" @cancel="handleCancel" @update:show="showModal = $event">
      <!-- Custom slot content for some examples -->
      <div v-if="showCustomContent">
        <p class="text-gray-600 mb-3">This is custom content in the modal slot.</p>
        <ul class="list-disc list-inside text-sm text-gray-500 space-y-1">
          <li>Custom bullet point 1</li>
          <li>Custom bullet point 2</li>
          <li>Custom bullet point 3</li>
        </ul>
      </div>
    </ConfirmationModal>
  </div>
</template>

<script>
import ConfirmationModal from '@/components/ConfirmationModal.vue'

export default {
  name: 'TestConfirmationModal',

  components: {
    ConfirmationModal
  },

  data() {
    return {
      showModal: false,
      isLoading: false,
      showCustomContent: false,
      currentVariant: 'danger',
      currentIcon: 'warning',
      currentTitle: '',
      currentDescription: '',
      currentWarningText: '',
      currentConfirmText: 'Confirm',
      currentCancelText: 'Cancel',
      currentLoadingText: 'Please wait...',
      actionLog: []
    }
  },

  methods: {
    openModal(variant, icon) {
      this.currentVariant = variant
      this.currentIcon = icon
      this.showCustomContent = variant === 'info'

      // Set different content based on variant
      switch (variant) {
        case 'danger':
          this.currentTitle = 'Delete Item'
          this.currentDescription = 'This action cannot be undone'
          this.currentWarningText = 'All associated data will be permanently removed from the system.'
          this.currentConfirmText = 'Delete Forever'
          this.currentLoadingText = 'Deleting...'
          break

        case 'warning':
          this.currentTitle = 'Unsaved Changes'
          this.currentDescription = 'You have unsaved changes'
          this.currentWarningText = 'Your changes will be lost if you continue without saving.'
          this.currentConfirmText = 'Continue Without Saving'
          this.currentLoadingText = 'Processing...'
          break

        case 'info':
          this.currentTitle = 'Additional Information'
          this.currentDescription = 'Please review the details below'
          this.currentWarningText = ''
          this.currentConfirmText = 'I Understand'
          this.currentLoadingText = 'Processing...'
          break

        case 'success':
          this.currentTitle = 'Operation Complete'
          this.currentDescription = 'The operation was successful'
          this.currentWarningText = ''
          this.currentConfirmText = 'Great!'
          this.currentLoadingText = 'Finishing...'
          break

        case 'primary':
          this.currentTitle = 'Send Email'
          this.currentDescription = 'Confirm email delivery'
          this.currentWarningText = 'This will send notifications to all selected recipients.'
          this.currentConfirmText = 'Send Now'
          this.currentLoadingText = 'Sending...'
          break
      }

      this.showModal = true
      this.logAction(`Opened ${variant} modal with ${icon} icon`)
    },

    openLogoutModal() {
      this.currentVariant = 'warning'
      this.currentIcon = 'logout'
      this.currentTitle = 'Sign Out'
      this.currentDescription = 'Are you sure you want to sign out?'
      this.currentWarningText = 'You will need to sign in again to access your account.'
      this.currentConfirmText = 'Sign Out'
      this.currentCancelText = 'Cancel'
      this.currentLoadingText = 'Signing out...'
      this.showCustomContent = false
      this.showModal = true
      this.logAction('Opened logout modal')
    },

    async handleConfirm() {
      this.logAction(`Confirm button clicked (${this.currentVariant})`)
      this.isLoading = true

      // Simulate async operation
      setTimeout(() => {
        this.isLoading = false
        this.showModal = false
        this.logAction(`${this.currentVariant} action completed`)
      }, 2000)
    },

    handleCancel() {
      this.logAction(`Cancel button clicked (${this.currentVariant})`)
      this.showModal = false
    },

    logAction(message) {
      const now = new Date()
      const time = now.toLocaleTimeString()
      this.actionLog.unshift({
        message,
        time
      })

      // Keep only last 10 actions
      if (this.actionLog.length > 10) {
        this.actionLog = this.actionLog.slice(0, 10)
      }
    },

    clearLog() {
      this.actionLog = []
      this.logAction('Action log cleared')
    }
  }
}
</script>

<style scoped>
/* Add any additional test-specific styles here */
</style>
