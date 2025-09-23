<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal" @click.stop>
      <div class="modal-header">
        <h3>Manage Collaborators</h3>
        <button @click="close" class="modal-closebutton">×</button>
      </div>
      <form @submit.prevent="save" class="modal-form">
        <div class="form-group">
          <label class="form-label">Task Title</label>
          <div class="task-info">
            <span class="task-title">{{ taskData?.title || 'Unknown Task' }}</span>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Current Collaborators</label>
          <div v-if="currentCollaborators.length > 0" class="collaborators-list">
            <div 
              v-for="(collaborator, index) in currentCollaborators" 
              :key="index" 
              class="collaborator-item"
            >
              <div class="collaborator-info">
                <span class="collaborator-icon">👤</span>
                <span class="collaborator-id">{{ collaborator }}</span>
              </div>
              <button
                type="button"
                class="collaborator-remove"
                @click="removeCollaborator(index)"
                :title="'Remove ' + collaborator"
              >
                ×
              </button>
            </div>
          </div>
          <div v-else class="empty-collaborators">
            <span class="empty-icon">👥</span>
            <span class="empty-text">No collaborators assigned</span>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Add New Collaborators</label>
          <div class="add-collaborator-section">
            <input
              v-model="newCollaboratorId"
              placeholder="Enter user ID"
              class="form-input"
              @keyup.enter="addCollaborator"
            />
            <button 
              type="button" 
              @click="addCollaborator"
              class="btn btn-outline"
              :disabled="!newCollaboratorId.trim()"
            >
              Add
            </button>
          </div>
          <div class="form-hint">
            Enter individual user IDs and click "Add", or use bulk input below
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Bulk Add Collaborators</label>
          <textarea
            v-model="bulkCollaborators"
            placeholder="user1, user2, user3&#10;Or one user ID per line"
            rows="3"
            class="form-textarea"
          ></textarea>
          <div class="form-hint">
            Comma-separated or one per line. Will be merged with existing collaborators.
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Summary</label>
          <div class="summary-section">
            <div class="summary-item">
              <span class="summary-label">Total Collaborators:</span>
              <span class="summary-value">{{ getTotalCollaborators() }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Changes:</span>
              <span class="summary-value">
                {{ hasChanges() ? 'Modified' : 'No changes' }}
              </span>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" @click="close" class="btn btn-outline">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="spinner"></span> 
            Save Changes
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";

const props = defineProps({
  show: Boolean,
  taskData: Object,
});

const emit = defineEmits(["close", "save"]);

const loading = ref(false);
const currentCollaborators = ref([]);
const originalCollaborators = ref([]);
const newCollaboratorId = ref('');
const bulkCollaborators = ref('');

// Watch for task data changes
watch(
  () => props.taskData,
  (newVal) => {
    if (newVal) {
      const collaborators = Array.isArray(newVal.collaborators) ? [...newVal.collaborators] : [];
      currentCollaborators.value = collaborators;
      originalCollaborators.value = [...collaborators];
    }
  },
  { immediate: true }
);

function addCollaborator() {
  const userId = newCollaboratorId.value.trim();
  if (!userId) return;
  
  if (currentCollaborators.value.includes(userId)) {
    alert(`User "${userId}" is already a collaborator`);
    return;
  }
  
  currentCollaborators.value.push(userId);
  newCollaboratorId.value = '';
}

function removeCollaborator(index) {
  currentCollaborators.value.splice(index, 1);
}

function parseBulkCollaborators() {
  if (!bulkCollaborators.value.trim()) return [];
  
  // Split by comma or newline and clean up
  const collaborators = bulkCollaborators.value
    .split(/[,\n]/)
    .map(id => id.trim())
    .filter(id => id);
  
  return [...new Set(collaborators)]; // Remove duplicates
}

function getTotalCollaborators() {
  const bulk = parseBulkCollaborators();
  const current = currentCollaborators.value;
  const combined = [...new Set([...current, ...bulk])];
  return combined.length;
}

function hasChanges() {
  const bulk = parseBulkCollaborators();
  const finalCollaborators = [...new Set([...currentCollaborators.value, ...bulk])];
  
  // Check if arrays are different
  if (finalCollaborators.length !== originalCollaborators.value.length) return true;
  return !finalCollaborators.every(id => originalCollaborators.value.includes(id));
}

async function save() {
  loading.value = true;
  
  try {
    // Combine current and bulk collaborators
    const bulk = parseBulkCollaborators();
    const finalCollaborators = [...new Set([...currentCollaborators.value, ...bulk])];
    
    // Prepare the updated data
    const updatedData = {
      collaborators: finalCollaborators
    };
    
    emit("save", updatedData);
    
  } catch (error) {
    console.error('Error saving collaborators:', error);
  } finally {
    loading.value = false;
    close();
  }
}

function close() {
  // Reset form data
  newCollaboratorId.value = '';
  bulkCollaborators.value = '';
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
.task-info {
  padding: 12px 16px;
  background: #f3f4f6;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.task-title {
  font-weight: 500;
  color: #374151;
}
.collaborators-list {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}
.collaborator-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  background: white;
  transition: background 0.2s ease;
}
.collaborator-item:last-child {
  border-bottom: none;
}
.collaborator-item:hover {
  background: #f9fafb;
}
.collaborator-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.collaborator-icon {
  font-size: 1rem;
  color: #6b7280;
}
.collaborator-id {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}
.collaborator-remove {
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.collaborator-remove:hover {
  background: #dc2626;
  transform: scale(1.1);
}
.empty-collaborators {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: #9ca3af;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.empty-icon {
  font-size: 1.2rem;
}
.add-collaborator-section {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.add-collaborator-section .form-input {
  flex: 1;
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
.form-textarea {
  resize: vertical;
}
.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 4px;
}
.summary-section {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}
.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}
.summary-item:last-child {
  margin-bottom: 0;
}
.summary-label {
  font-weight: 500;
  color: #6b7280;
}
.summary-value {
  font-weight: 600;
  color: #374151;
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
