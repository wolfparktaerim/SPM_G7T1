<!-- frontend/src/components/task/ExtensionRequestAction.vue -->

<template>
  <div class="space-y-3">
    <!-- Request Info -->
    <div class="flex items-start gap-2 text-sm">
      <div class="flex-shrink-0 w-7 h-7 rounded-lg bg-amber-100 flex items-center justify-center">
        <MessageSquare class="w-4 h-4 text-amber-600" />
      </div>
      <div class="flex-1 min-w-0">
        <span class="font-medium text-gray-900">{{ requesterName }}</span>
        <span class="text-gray-600"> requests extension for </span>
        <span class="font-medium text-gray-900">{{ itemTitle }}</span>
      </div>
    </div>

    <!-- Extension Details - Compact Card -->
    <div class="bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg p-3 border border-amber-200/50">
      <!-- Current Deadline -->
      <div class="flex items-center justify-between text-xs mb-2">
        <span class="text-gray-600 font-medium">Current:</span>
        <span class="text-gray-700 font-medium">{{ formatDeadline(extensionRequest.currentDeadline) }}</span>
      </div>

      <!-- Extension Arrow -->
      <div class="flex items-center justify-center gap-2 py-1.5 mb-2">
        <div class="flex-1 h-px bg-gradient-to-r from-transparent via-amber-300 to-transparent"></div>
        <div class="flex items-center gap-1.5 px-2 py-1 bg-white rounded-full shadow-sm">
          <ArrowRight class="w-3.5 h-3.5 text-amber-600" />
          <span class="text-xs font-semibold text-amber-700">+{{ extensionDays }} days</span>
        </div>
        <div class="flex-1 h-px bg-gradient-to-r from-transparent via-amber-300 to-transparent"></div>
      </div>

      <!-- Proposed Deadline -->
      <div class="flex items-center justify-between text-xs">
        <span class="text-gray-600 font-medium">Proposed:</span>
        <span class="text-amber-700 font-semibold">{{ formatDeadline(extensionRequest.proposedDeadline) }}</span>
      </div>
    </div>

    <!-- Reason -->
    <div class="bg-gray-50 rounded-lg p-3 border border-gray-200">
      <div class="text-xs font-semibold text-gray-700 mb-1.5">Reason:</div>
      <div class="text-xs text-gray-900 leading-relaxed whitespace-pre-wrap">{{ extensionRequest.reason }}</div>
    </div>

    <!-- Info Banner -->
    <div v-if="extensionRequest.status === 'pending'"
      class="flex items-start gap-2 p-2.5 bg-blue-50 border border-blue-200 rounded-lg">
      <AlertCircle class="w-3.5 h-3.5 text-blue-600 flex-shrink-0 mt-0.5" />
      <div class="text-xs text-blue-800 leading-snug">
        Approving will instantly update the deadline to <strong>{{ formatDeadline(extensionRequest.proposedDeadline)
        }}</strong> and notify the team.
      </div>
    </div>

    <!-- Rejection Reason Input -->
    <div v-if="showRejectionInput" class="space-y-2">
      <label for="rejectionReason" class="block text-xs font-semibold text-gray-700">
        Reason for Rejection (Optional):
      </label>
      <textarea id="rejectionReason" v-model="rejectionReason" rows="3"
        placeholder="Explain why the extension cannot be granted..."
        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs resize-none focus:outline-none focus:border-red-400 focus:ring-2 focus:ring-red-400/20 transition-all"
        maxlength="300"></textarea>
      <p class="text-xs text-gray-500 text-right">{{ rejectionReason.length }}/300</p>
    </div>

    <!-- Action Buttons -->
    <div v-if="extensionRequest.status === 'pending'" class="flex gap-2">
      <!-- Approve Button -->
      <button v-if="!showRejectionInput" @click="handleApprove" :disabled="isProcessing"
        class="flex-1 px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 bg-emerald-500 text-white hover:bg-emerald-600 active:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow">
        <Loader v-if="isProcessing && actionType === 'approve'" class="w-3.5 h-3.5 animate-spin" />
        <Check v-else class="w-3.5 h-3.5" />
        <span>Approve</span>
      </button>

      <!-- Reject Button -->
      <button v-if="!showRejectionInput" @click="showRejectionInput = true" :disabled="isProcessing"
        class="flex-1 px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 bg-white text-red-600 border border-red-300 hover:bg-red-50 active:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
        <X class="w-3.5 h-3.5" />
        <span>Reject</span>
      </button>

      <!-- Rejection Confirm/Cancel -->
      <template v-if="showRejectionInput">
        <button @click="handleReject" :disabled="isProcessing"
          class="flex-1 px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 bg-red-500 text-white hover:bg-red-600 active:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow">
          <Loader v-if="isProcessing && actionType === 'reject'" class="w-3.5 h-3.5 animate-spin" />
          <span v-else>Confirm</span>
        </button>

        <button @click="cancelRejection" :disabled="isProcessing"
          class="flex-1 px-3 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 bg-gray-100 text-gray-700 hover:bg-gray-200 active:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
          Cancel
        </button>
      </template>
    </div>

    <!-- Status Badge (for already responded requests) -->
    <div v-else class="flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold" :class="extensionRequest.status === 'approved'
      ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
      : 'bg-red-100 text-red-800 border border-red-200'">
      <Check v-if="extensionRequest.status === 'approved'" class="w-3.5 h-3.5" />
      <X v-else class="w-3.5 h-3.5" />
      <span>{{ extensionRequest.status === 'approved' ? 'Approved' : 'Rejected' }}</span>
    </div>

    <!-- Error Message -->
    <div v-if="errorMessage" class="flex items-start gap-2 p-2.5 bg-red-50 border border-red-200 rounded-lg">
      <AlertCircle class="w-3.5 h-3.5 text-red-600 flex-shrink-0 mt-0.5" />
      <span class="text-xs text-red-800 leading-snug">{{ errorMessage }}</span>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { ArrowRight, MessageSquare, Check, X, Loader, AlertCircle } from 'lucide-vue-next';
import { useToast } from 'vue-toastification'
import { useAuthStore } from '@/stores/auth'

const API_BASE = (import.meta.env.VITE_BACKEND_API || '').replace(/\/+$/, '');

export default {
  name: 'ExtensionRequestAction',
  components: { ArrowRight, MessageSquare, Check, X, Loader, AlertCircle },
  setup() {
    const toast = useToast()
    const authStore = useAuthStore()
    return { toast, authStore, API_BASE }
  },
  props: {
    extensionRequest: { type: Object, required: true },
    requesterName: { type: String, required: true },
    itemTitle: { type: String, required: true }
  },
  data() {
    return {
      isProcessing: false,
      errorMessage: '',
      showRejectionInput: false,
      rejectionReason: '',
      actionType: null
    };
  },
  computed: {
    extensionDays() {
      const diff = this.extensionRequest.proposedDeadline - this.extensionRequest.currentDeadline;
      return Math.ceil(diff / 86400);
    }
  },
  methods: {
    async handleApprove() {
      if (this.isProcessing) return;
      this.isProcessing = true;
      this.errorMessage = '';
      this.actionType = 'approve';

      try {
        const userId = this.authStore.user?.uid;

        console.log('Approving extension request:', {
          requestId: this.extensionRequest.requestId,
          userId,
          extensionRequest: this.extensionRequest
        });

        const url = `${API_BASE}/extension-requests/${this.extensionRequest.requestId}/respond`;
        const payload = {
          responderId: userId,
          status: 'approved'
        };

        console.log('Sending payload:', payload);
        console.log('To URL:', url);

        const response = await axios.patch(url, payload);
        console.log('Response:', response.data);

        this.$emit('responded', {
          requestId: this.extensionRequest.requestId,
          status: 'approved',
          newDeadline: this.extensionRequest.proposedDeadline
        });

        this.toast.success('Extension request approved successfully');

      } catch (err) {
        console.error('Error approving extension request:', err);
        console.error('Error response:', err.response?.data);
        console.error('Error status:', err.response?.status);

        const msg = err.response?.data?.error || err.response?.data?.message || 'Failed to approve extension request';
        this.errorMessage = msg;
      } finally {
        this.isProcessing = false;
        this.actionType = null;
      }
    },

    async handleReject() {
      if (this.isProcessing) return;
      this.isProcessing = true;
      this.errorMessage = '';
      this.actionType = 'reject';

      try {
        const userId = this.authStore.user?.uid;

        const body = {
          responderId: userId,
          status: 'rejected'
        };
        if (this.rejectionReason.trim()) {
          body.rejectionReason = this.rejectionReason.trim();
        }

        console.log('Rejecting extension request:', {
          requestId: this.extensionRequest.requestId,
          body
        });

        const url = `${API_BASE}/extension-requests/${this.extensionRequest.requestId}/respond`;
        const response = await axios.patch(url, body);
        console.log('Response:', response.data);

        this.$emit('responded', {
          requestId: this.extensionRequest.requestId,
          status: 'rejected'
        });

        this.toast.success('Extension request rejected');

      } catch (err) {
        console.error('Error rejecting extension request:', err);
        console.error('Error response:', err.response?.data);

        const msg = err.response?.data?.error || err.response?.data?.message || 'Failed to reject extension request';
        this.errorMessage = msg;
      } finally {
        this.isProcessing = false;
        this.actionType = null;
      }
    },

    cancelRejection() {
      this.showRejectionInput = false;
      this.rejectionReason = '';
      this.errorMessage = '';
    },

    formatDeadline(timestamp) {
      const date = new Date(timestamp * 1000);
      return date.toLocaleDateString('en-SG', {
        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });
    }
  }
};
</script>
