<!-- frontend/src/components/task/DeadlineExtensionRequestModal.vue -->

<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-[1000] p-4"
    @click="handleBackdropClick">
    <div class="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl" @click.stop>
      <!-- Modal Header -->
      <div class="p-6 border-b border-gray-200 flex items-center justify-between">
        <h2 class="text-2xl font-semibold text-gray-900">Request Deadline Extension</h2>
        <button @click="$emit('close')"
          class="p-2 rounded-md text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors border-none bg-transparent cursor-pointer">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Modal Content -->
      <div class="p-6 overflow-y-auto">
        <!-- Task/Subtask Info -->
        <div class="bg-gray-50 rounded-lg p-4 mb-6">
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-600 mb-1">{{ isSubtask ? 'Subtask' : 'Task' }}</label>
            <div class="text-sm text-gray-900 font-medium">{{ taskTitle }}</div>
          </div>
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-600 mb-1">Current Deadline</label>
            <div class="text-sm text-gray-900 font-medium">{{ formatDeadline(currentDeadline) }}</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Owner</label>
            <div class="text-sm text-gray-900 font-medium">{{ ownerName }}</div>
          </div>
        </div>

        <!-- Check for existing pending request -->
        <div v-if="hasPendingRequest"
          class="flex gap-3 p-4 bg-amber-100 border border-amber-400 rounded-lg text-amber-900 mb-6">
          <AlertCircle class="w-5 h-5 flex-shrink-0" />
          <div>
            <div class="font-semibold mb-1">Pending Request</div>
            <div class="text-sm">
              You already have a pending extension request for this {{ isSubtask ? 'subtask' : 'task' }}.
              Please wait for the owner to respond before submitting a new request.
            </div>
          </div>
        </div>

        <!-- Extension Form -->
        <form v-if="!hasPendingRequest" @submit.prevent="submitRequest" class="flex flex-col gap-5">
          <!-- Proposed New Deadline -->
          <div class="flex flex-col gap-2">
            <label for="proposedDeadline" class="text-sm font-medium text-gray-700 flex items-center gap-2">
              <Calendar class="w-4 h-4" />
              Proposed New Deadline
              <span class="text-red-500 ml-1">*</span>
            </label>
            <input id="proposedDeadline" v-model="proposedDeadline" type="datetime-local" :min="minDeadline" required
              class="w-full px-3 py-2.5 border border-gray-300 rounded-md text-sm transition-all focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10" />
            <p class="text-xs text-gray-600 m-0">Select a date after the current deadline</p>
          </div>

          <!-- Reason -->
          <div class="flex flex-col gap-2">
            <label for="reason" class="text-sm font-medium text-gray-700 flex items-center gap-2">
              <FileText class="w-4 h-4" />
              Reason for Extension
              <span class="text-red-500 ml-1">*</span>
            </label>
            <textarea id="reason" v-model="reason" rows="4" required
              placeholder="Please explain why you need more time..."
              class="w-full px-3 py-2.5 border border-gray-300 rounded-md text-sm resize-vertical transition-all focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10"
              maxlength="500"></textarea>
            <p class="text-xs text-gray-600 m-0">{{ reason.length }}/500 characters</p>
          </div>

          <!-- Error Message -->
          <div v-if="errorMessage"
            class="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
            <AlertCircle class="w-5 h-5" />
            {{ errorMessage }}
          </div>

          <!-- Action Buttons -->
          <div class="flex gap-3 justify-end pt-2">
            <button type="button" @click="$emit('close')"
              class="px-5 py-2.5 rounded-md text-sm font-medium transition-colors cursor-pointer bg-white text-gray-700 border border-gray-300 hover:bg-gray-50">
              Cancel
            </button>
            <button type="submit" :disabled="isSubmitting"
              class="px-5 py-2.5 rounded-md text-sm font-medium transition-colors cursor-pointer flex items-center gap-2 bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed border-none">
              <Loader v-if="isSubmitting" class="w-4 h-4 animate-spin" />
              <span v-else>Submit Request</span>
            </button>
          </div>
        </form>

        <!-- Pending Request Status -->
        <div v-else class="flex flex-col gap-4">
          <button @click="$emit('close')"
            class="w-full px-5 py-2.5 rounded-md text-sm font-medium transition-colors cursor-pointer bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 flex items-center justify-center">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { X, Calendar, FileText, AlertCircle, Loader } from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth'

const API_BASE = (import.meta.env.VITE_BACKEND_API || '').replace(/\/+$/, '');


export default {
  name: 'DeadlineExtensionRequestModal',
  components: { X, Calendar, FileText, AlertCircle, Loader },
  setup() {
    const authStore = useAuthStore()
    return { authStore, API_BASE }
  },
  props: {
    show: { type: Boolean, required: true },
    taskId: { type: String, required: true },
    taskTitle: { type: String, required: true },
    currentDeadline: { type: Number, required: true },
    isSubtask: { type: Boolean, default: false },
    ownerId: { type: String, required: true },
    ownerName: { type: String, required: true }
  },
  data() {
    return {
      proposedDeadline: '',
      reason: '',
      isSubmitting: false,
      errorMessage: '',
      hasPendingRequest: false,

    };
  },
  computed: {
    minDeadline() {
      const minDate = new Date((this.currentDeadline + 86400) * 1000);
      return this.formatDateTimeLocal(minDate);
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.resetForm();
        this.checkPendingRequests();
      }
    }
  },
  methods: {
    async checkPendingRequests() {
      try {
        const userId = this.authStore.user?.uid;
        if (!userId) return;

        const url = `${API_BASE}/extension-requests/item/${this.taskId}`;
        const { data } = await axios.get(url);

        this.hasPendingRequest = Array.isArray(data.requests)
          ? data.requests.some(req => req.requesterId === userId && req.status === 'pending')
          : false;
      } catch (error) {
        console.error('Error checking pending requests:', error);
      }
    },

    async submitRequest() {
      this.errorMessage = '';

      if (!this.proposedDeadline) {
        this.errorMessage = 'Please select a proposed deadline';
        return;
      }
      if (!this.reason.trim()) {
        this.errorMessage = 'Please provide a reason for the extension';
        return;
      }

      const proposedTimestamp = Math.floor(new Date(this.proposedDeadline).getTime() / 1000);
      if (proposedTimestamp <= this.currentDeadline) {
        this.errorMessage = 'Proposed deadline must be after the current deadline';
        return;
      }

      this.isSubmitting = true;

      try {
        const userId = this.authStore.user?.uid;

        const url = `${API_BASE}/extension-requests`;
        const { data } = await axios.post(url, {
          itemId: this.taskId,
          itemType: this.isSubtask ? 'subtask' : 'task',
          requesterId: userId,
          proposedDeadline: proposedTimestamp,
          reason: this.reason.trim()
        });

        this.$emit('success', data.request);
        this.$emit('close');

      } catch (err) {
        const msg = err.response?.data?.error || 'Failed to submit extension request';
        this.errorMessage = msg;
        console.error('Error submitting extension request:', err);
      } finally {
        this.isSubmitting = false;
      }
    },

    handleBackdropClick(event) {
      if (event.target.classList.contains('fixed')) {
        this.$emit('close');
      }
    },

    resetForm() {
      this.proposedDeadline = '';
      this.reason = '';
      this.errorMessage = '';
      this.isSubmitting = false;
      this.hasPendingRequest = false;
    },

    formatDeadline(timestamp) {
      const date = new Date(timestamp * 1000);
      return date.toLocaleDateString('en-US', {
        year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });
    },

    formatDateTimeLocal(date) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
  }
};
</script>
