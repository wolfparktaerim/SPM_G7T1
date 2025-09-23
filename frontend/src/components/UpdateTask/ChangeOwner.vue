<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal" @click.stop>
      <div class="modal-header">
        <h3>Change Task Owner</h3>
        <button @click="close" class="modal-closebutton">×</button>
      </div>
      <form @submit.prevent="save" class="modal-form">
        <div class="form-group">
          <label class="form-label">Task Information</label>
          <div class="task-info">
            <div class="task-detail">
              <span class="detail-label">Title:</span>
              <span class="detail-value">{{ taskData?.title || 'Unknown Task' }}</span>
            </div>
            <div class="task-detail">
              <span class="detail-label">Status:</span>
              <span :class="['status-badge', taskData?.status]">
                {{ formatStatus(taskData?.status) }}
              </span>
            </div>
            <div class="task-detail">
              <span class="detail-label">Current Owner:</span>
              <span class="detail-value current-owner">
                {{ isCurrentUser(taskData?.ownerId) ? 'You' : taskData?.ownerId }}
              </span>
            </div>
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label required">New Owner</label>
          <input
            v-model="newOwnerId"
            placeholder="Enter new owner user ID"
            required
            class="form-input"
            :class="{ 'input-error': validationError }"
          />
          <div v-if="validationError" class="validation-error">
            {{ validationError }}
          </div>
          <div class="form-hint">
            The new owner will have full control over this task
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Transfer Options</label>
          <div class="transfer-options">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="addCurrentAsCollaborator"
                class="checkbox-input"
              />
              <span class="checkbox-text">
                Add current owner as collaborator
              </span>
            </label>
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="notifyNewOwner"
                class="checkbox-input"
                disabled
              />
              <span class="checkbox-text checkbox-disabled">
                Notify new owner (Coming soon)
              </span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Transfer Note</label>
          <textarea
            v-model="transferNote"
            placeholder="Optional note about the ownership transfer..."
            rows="3"
            maxlength="200"
            class="form-textarea"
          ></textarea>
          <div class="char-count">{{ transferNote.length }}/200</div>
        </div>

        <div class="form-group">
          <div class="warning-box">
            <div class="warning-icon">⚠️</div>
            <div class="warning-content">
              <div class="warning-title">Ownership Transfer</div>
              <div class="warning-text">
                This action will immediately transfer ownership of the task. 
                The new owner will have full control, including the ability to modify, 
                delete, or reassign the task.
              </div>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button type="button" @click="close" class="btn btn-outline">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary" :disabled="loading || !newOwnerId.trim() || validationError">
            <span v-if="loading" class="spinner"></span> 
            Transfer Ownership
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { useAuthStore } from "@/stores/auth";

const props = defineProps({
  show: Boolean,
  taskData: Object,
});

const emit = defineEmits(["close", "save"]);

const authStore = useAuthStore();
const loading = ref(false);
const newOwnerId = ref('');
const addCurrentAsCollaborator = ref(true);
const notifyNewOwner = ref(false);
const transferNote = ref('');

// Validation
const validationError = computed(() => {
  if (!newOwnerId.value.trim()) return null;
  
  if (newOwnerId.value === props.taskData?.ownerId) {
    return "New owner cannot be the same as current owner";
  }
  
  if (newOwnerId.value === authStore.user?.uid) {
    return "You are already managing this task";
  }
  
  // Basic validation for user ID format
  if (newOwnerId.value.length < 3) {
    return "User ID must be at least 3 characters";
  }
  
  return null;
});

// Watch for task data changes
watch(
  () => props.taskData,
  (newVal) => {
    if (newVal) {
      // Reset form when task changes
      newOwnerId.value = '';
      transferNote.value = '';
      addCurrentAsCollaborator.value = true;
    }
  },
  { immediate: true }
);

function formatStatus(status) {
  const statusMap = {
    'ongoing': 'Ongoing',
    'unassigned': 'Unassigned',
    'under_review': 'Under Review',
    'completed': 'Completed'
  };
  return statusMap[status] || status;
}

function isCurrentUser(userId) {
  return userId === authStore.user?.uid;
}

async function save() {
  if (validationError.value || !newOwnerId.value.trim()) return;
  
  loading.value = true;
  
  try {
    // Prepare the updated data
    const updatedData = {
      ownerId: newOwnerId.value.trim()
    };
    
    // Add current owner as collaborator if requested
    if (addCurrentAsCollaborator.value && props.taskData?.ownerId) {
      const currentCollaborators = Array.isArray(props.taskData.collaborators) 
        ? [...props.taskData.collaborators] 
        : [];
      
      // Add current owner to collaborators if not already there
      if (!currentCollaborators.includes(props.taskData.ownerId)) {
        currentCollaborators.push(props.taskData.ownerId);
        updatedData.collaborators = currentCollaborators;
      }
    }
    
    // Add transfer note to task notes if provided
    if (transferNote.value.trim()) {
      const timestamp = new Date().toLocaleString();
      const transferInfo = `\n\n--- Ownership Transfer (${timestamp}) ---\nTransferred to: ${newOwnerId.value}\nNote: ${transferNote.value.trim()}`;
      updatedData.notes = (props.taskData?.notes || '') + transferInfo;
    }
    
    emit("save", updatedData);
    
  } catch (error) {
    console.error('Error transferring ownership:', error);
  } finally {
    loading.value = false;
    close();
  }
}

function close() {
  // Reset form data
  newOwnerId.value = '';
  transferNote.value = '';
  addCurrentAsCollaborator.value = true;
  emit("close");
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.modal {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 550px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 24px 0 24px;
  margin-bottom: 20px;
}
.modal-closebutton {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #9ca3af;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
}
.modal-closebutton:hover {
  background: #f3f4f6;
  color: #6b7280;
}
.modal-form {
  padding: 0 24px 24px 24px;
}
.form-group {
  margin-bottom: 20px;
}
.form-label {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
  display: block;
  margin-bottom: 6px;
}
.form-label.required::after {
  content: "*";
  color: #ef4444;
  margin-left: 2px;
}
.task-info {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}
.task-detail {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.task-detail:last-child {
  margin-bottom: 0;
}
.detail-label {
  font-weight: 500;
  color: #6b7280;
  min-width: 80px;
}
.detail-value {
  color: #374151;
}
.current-owner {
  font-weight: 600;
  color: #667eea;
}
.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}
.status-badge.ongoing {
  background: #dbeafe;
  color: #1e40af;
}
.status-badge.unassigned {
  background: #fef3c7;
  color: #92400e;
}
.status-badge.under_review {
  background: #e0e7ff;
  color: #5b21b6;
}
.status-badge.completed {
  background: #d1fae5;
  color: #065f46;
}
.form-input,
.form-textarea {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s ease;
  background: white;
  width: 100%;
  font-family: inherit;
}
.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}
.input-error {
  border-color: #ef4444 !important;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
}
.validation-error {
  color: #ef4444;
  font-size: 0.75rem;
  margin-top: 4px;
  font-weight: 500;
}
.form-textarea {
  resize: vertical;
}
.char-count {
  font-size: 0.75rem;
  color: #9ca3af;
  text-align: right;
  margin-top: 4px;
}
.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 4px;
}
.transfer-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.checkbox-input {
  width: 16px;
  height: 16px;
}
.checkbox-text {
  font-size: 0.875rem;
  color: #374151;
}
.checkbox-disabled {
  color: #9ca3af !important;
  cursor: not-allowed !important;
}
.warning-box {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #fef3c7;
  border: 1px solid #fde68a;
  border-radius: 8px;
}
.warning-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}
.warning-content {
  flex: 1;
}
.warning-title {
  font-weight: 600;
  color: #92400e;
  margin-bottom: 4px;
}
.warning-text {
  font-size: 0.875rem;
  color: #a16207;
  line-height: 1.4;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}
.btn {
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
}
.btn-outline {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}
.btn-outline:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #9ca3af;
}
.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
