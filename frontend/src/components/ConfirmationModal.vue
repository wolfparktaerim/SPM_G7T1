<!-- src/components/ConfirmationModal.vue -->

<!--
  USAGE INSTRUCTIONS:

  1. Import in your component:
  import ConfirmationModal from '@/components/ConfirmationModal.vue'

  2. Register in components (Options API):
  components: {
    ConfirmationModal
  }

  3. Use in template:
  <ConfirmationModal
    :show="showModal"
    title="Delete Item"
    description="This action cannot be undone"
    warning-text="All associated data will be permanently removed"
    confirm-text="Delete"
    cancel-text="Cancel"
    loading-text="Deleting..."
    :loading="isDeleting"
    variant="danger"
    icon="trash"
    @confirm="handleDelete"
    @cancel="showModal = false"
    @update:show="showModal = $event"
  >
   Optional custom
   <p>Are you sure you want to delete this item?</p>
  </ConfirmationModal>

  4. Handle in your component data/methods:
  data() {
    return {
      showModal: false,
      isDeleting: false
    }
  },
  methods: {
    async handleDelete() {
      this.isDeleting = true
      try {
        // Your delete logic here
        await deleteItem()
        this.showModal = false
      } finally {
        this.isDeleting = false
      }
    }
  }

  PROPS:
  - show: Boolean (required) - Controls modal visibility
  - title: String (required) - Modal title
  - description: String - Optional description under title
  - warningText: String - Optional warning message
  - confirmText: String - Confirm button text (default: "Confirm")
  - cancelText: String - Cancel button text (default: "Cancel")
  - loadingText: String - Loading button text (default: "Please wait...")
  - loading: Boolean - Shows loading state (default: false)
  - variant: String - Visual variant: 'danger', 'warning', 'info', 'success', 'primary' (default: 'danger')
  - icon: String - Icon type: 'trash', 'logout', 'warning', 'info', 'check', 'alert', 'mail', 'key' (default: 'warning')
  - allowBackdropClose: Boolean - Allow closing by clicking backdrop (default: true)

  EVENTS:
  - @confirm - Emitted when confirm button is clicked
  - @cancel - Emitted when cancel button is clicked
  - @update:show - Emitted to update show prop (for v-model support)
-->

<template>
  <teleport to="body">
    <transition name="modal">
      <div v-if="show" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 px-4"
        @click="handleBackdropClick">
        <div
          class="bg-white/95 backdrop-blur-xl rounded-2xl p-6 sm:p-8 max-w-md w-full mx-4 animate-scale-in shadow-2xl border border-white/50"
          @click.stop>
          <!-- Header with Icon -->
          <div class="flex items-center space-x-4 mb-6">
            <div class="w-12 h-12 sm:w-14 sm:h-14 rounded-xl flex items-center justify-center"
              :class="iconBackgroundClass">
              <component :is="iconComponent" class="w-6 h-6 sm:w-7 sm:h-7 text-white" :stroke-width="2" />
            </div>
            <div class="flex-1">
              <h3 class="text-lg sm:text-xl font-bold text-gray-900">{{ title }}</h3>
              <p class="text-sm text-gray-600 mt-1" v-if="description">{{ description }}</p>
            </div>
          </div>

          <!-- Custom Content Slot -->
          <div v-if="$slots.default" class="mb-6">
            <slot />
          </div>

          <!-- Warning Text -->
          <div v-if="warningText" class="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl">
            <div class="flex items-start space-x-3">
              <AlertTriangle class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <p class="text-sm text-amber-800">{{ warningText }}</p>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex flex-col sm:flex-row gap-3">
            <button @click="handleCancel" :disabled="loading"
              class="flex-1 order-2 sm:order-1 px-4 sm:px-6 py-3 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl font-semibold transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100">
              {{ cancelText }}
            </button>
            <button @click="handleConfirm" :disabled="loading"
              class="flex-1 order-1 sm:order-2 px-4 sm:px-6 py-3 rounded-xl font-semibold transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              :class="confirmButtonClass">
              <div class="flex items-center justify-center space-x-2">
                <component v-if="loading" :is="LoaderIcon" class="w-4 h-4 animate-spin" />
                <span>{{ loading ? loadingText : confirmText }}</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script>
import { computed } from 'vue'
import {
  AlertTriangle,
  Trash,
  LogOut,
  AlertCircle,
  CheckCircle,
  Info,
  Mail,
  Key,
  Loader2
} from 'lucide-vue-next'

export default {
  name: 'ConfirmationModal',

  props: {
    show: {
      type: Boolean,
      required: true
    },
    title: {
      type: String,
      required: true
    },
    description: {
      type: String,
      default: ''
    },
    warningText: {
      type: String,
      default: ''
    },
    confirmText: {
      type: String,
      default: 'Confirm'
    },
    cancelText: {
      type: String,
      default: 'Cancel'
    },
    loadingText: {
      type: String,
      default: 'Please wait...'
    },
    loading: {
      type: Boolean,
      default: false
    },
    variant: {
      type: String,
      default: 'danger',
      validator: (value) => ['danger', 'warning', 'info', 'success', 'primary'].includes(value)
    },
    icon: {
      type: String,
      default: 'warning',
      validator: (value) => ['trash', 'logout', 'log-out', 'warning', 'info', 'check', 'alert', 'mail', 'key'].includes(value)
    },
    allowBackdropClose: {
      type: Boolean,
      default: true
    }
  },

  emits: ['confirm', 'cancel', 'update:show'],

  setup(props, { emit }) {
    // Icon mapping
    const iconComponents = {
      trash: Trash,
      logout: LogOut,
      'log-out': LogOut,
      warning: AlertTriangle,
      info: Info,
      check: CheckCircle,
      alert: AlertCircle,
      mail: Mail,
      key: Key
    }

    const LoaderIcon = Loader2

    const iconComponent = computed(() => iconComponents[props.icon])

    const iconBackgroundClass = computed(() => {
      const baseClasses = 'shadow-lg transition-all duration-300'

      switch (props.variant) {
        case 'danger':
          return `${baseClasses} bg-gradient-to-r from-red-500 to-red-600`
        case 'warning':
          return `${baseClasses} bg-gradient-to-r from-amber-500 to-amber-600`
        case 'info':
          return `${baseClasses} bg-gradient-to-r from-blue-500 to-blue-600`
        case 'primary':
          return `${baseClasses} bg-gradient-to-r from-blue-500 to-blue-600`
        case 'success':
          return `${baseClasses} bg-gradient-to-r from-green-500 to-green-600`
        default:
          return `${baseClasses} bg-gradient-to-r from-gray-500 to-gray-600`
      }
    })

    const confirmButtonClass = computed(() => {
      const baseClasses = 'text-white shadow-lg'

      switch (props.variant) {
        case 'danger':
          return `${baseClasses} bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700`
        case 'warning':
          return `${baseClasses} bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700`
        case 'info':
          return `${baseClasses} bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700`
        case 'primary':
          return `${baseClasses} bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700`
        case 'success':
          return `${baseClasses} bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700`
        default:
          return `${baseClasses} bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700`
      }
    })

    const handleConfirm = () => {
      if (props.loading) return
      emit('confirm')
    }

    const handleCancel = () => {
      if (props.loading) return
      emit('cancel')
      emit('update:show', false)
    }

    const handleBackdropClick = () => {
      if (props.allowBackdropClose && !props.loading) {
        handleCancel()
      }
    }

    return {
      iconComponent,
      LoaderIcon,
      iconBackgroundClass,
      confirmButtonClass,
      handleConfirm,
      handleCancel,
      handleBackdropClick,
      AlertTriangle
    }
  }
}
</script>

<style scoped>
/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .animate-scale-in,
.modal-leave-to .animate-scale-in {
  transform: scale(0.9) translateY(10px);
}

/* Scale animation for modal content */
.animate-scale-in {
  animation: scaleIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes scaleIn {
  0% {
    opacity: 0;
    transform: scale(0.9) translateY(10px);
  }

  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Enhanced hover effects */
button:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

button:active:not(:disabled) {
  transform: scale(0.98);
}

/* Enhanced focus states for accessibility */
button:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Backdrop blur support */
.backdrop-blur-sm {
  backdrop-filter: blur(4px);
}

.backdrop-blur-xl {
  backdrop-filter: blur(24px);
}

/* Enhanced loading state */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .animate-scale-in {
    margin: 1rem;
  }
}
</style>
