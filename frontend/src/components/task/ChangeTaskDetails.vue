<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal" @click.stop>
      <div class="modal-header">
        <div class="modal-header-left">
          <h3>{{ getModalTitle() }}</h3>
        </div>
        <div class="modal-header-right">
          <div class="modal-tabs">
            <button 
              @click="setActiveModal('edit')" 
              :class="['tab-button', { 'tab-active': activeModal === 'edit' }]"
            >
              ✏️ Edit
            </button>
            <button 
              @click="setActiveModal('owner')" 
              :class="['tab-button', { 'tab-active': activeModal === 'owner' }]"
              :disabled="!canChangeOwner"
            >
              👤 Owner
            </button>
            <button 
              @click="setActiveModal('collaborators')" 
              :class="['tab-button', { 'tab-active': activeModal === 'collaborators' }]"
            >
              👥 Team
            </button>
          </div>
          <button @click="close" class="modal-closebutton">×</button>
        </div>
      </div>

      <!-- Edit Task Form -->
      <form v-if="activeModal === 'edit'" @submit.prevent="save" class="modal-form">
        <div class="form-group">
          <label class="form-label required">Title</label>
          <input
            v-model="localData.title"
            placeholder="Title"
            required
            maxlength="100"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label class="form-label required">Deadline</label>
          <input
            type="datetime-local"
            v-model="localDeadline"
            :min="minDateTime"
            required
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label class="form-label">Status</label>
          <select v-model="localData.status" class="form-input">
            <option value="unassigned">Unassigned</option>
            <option value="ongoing">Ongoing</option>
            <option value="underreview">Under Review</option>
            <option value="completed">Completed</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Notes</label>
          <textarea
            v-model="localData.notes"
            placeholder="Notes"
            maxlength="500"
            rows="4"
            class="form-textarea"
          ></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Attachments</label>
          <div class="file-upload-area">
            <input
              type="file"
              multiple
              @change="handleFileUpload"
              accept="image/*,application/pdf,.doc,.docx,.txt,.csv,.xlsx"
              class="file-input"
              ref="fileInput"
            />
            <div class="file-upload-content" @click="$refs.fileInput.click()">
              <div class="upload-icon"></div>
              <div class="upload-text">
                <span class="upload-title">Add more attachments</span>
                <span class="upload-subtitle">
                  PNG, JPG, PDF, DOC, TXT max 2MB each
                </span>
              </div>
            </div>
          </div>
          <div v-if="attachments.length > 0" class="file-list">
            <div
              v-for="(file, index) in attachments"
              :key="index"
              class="file-item"
            >
              <div class="file-info">
                <span class="file-icon">{{ getFileIcon(file.type) }}</span>
                <div class="file-details">
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                </div>
              </div>
              <button
                type="button"
                class="file-remove"
                @click="removeAttachment(index)"
              >
                ×
              </button>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" @click="close" class="btn btn-outline">
            Cancel
          </button>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="spinner"></span> Save Changes
          </button>
        </div>
      </form>

      <!-- Change Owner Form -->
      <form v-if="activeModal === 'owner'" @submit.prevent="saveOwnerChange" class="modal-form">
        <!-- Restriction Notice -->
        <div v-if="!canChangeOwner" class="restriction-notice">
          <div class="restriction-icon">🚫</div>
          <div class="restriction-content">
            <div class="restriction-title">Ownership Change Restricted</div>
            <div class="restriction-text">
              Task ownership can only be changed when the status is "Unassigned". 
              Current status: <strong>{{ formatStatus(taskData?.status) }}</strong>
            </div>
            <div class="restriction-hint">
              Change the task status to "Unassigned" in the Edit tab to enable ownership transfer.
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Task Information</label>
          <div class="task-info">
            <div class="task-detail">
              <span class="detail-label">Title:</span>
              <span class="detail-value">{{ taskData?.title || 'Unknown Task' }}</span>
            </div>
            <div class="task-detail">
              <span class="detail-label">Status:</span>
              <span :class="['status-badge', taskData?.status, { 'status-restricted': !canChangeOwner }]">
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
            :disabled="!canChangeOwner"
          />
          <div v-if="validationError" class="validation-error">
            {{ validationError }}
          </div>
          <div class="form-hint">
            <span v-if="canChangeOwner">
              The new owner will have full control over this task
            </span>
            <span v-else class="hint-disabled">
              Ownership transfer is disabled for tasks with assigned status
            </span>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Transfer Options</label>
          <div class="transfer-options">
            <label class="checkbox-label" :class="{ 'checkbox-disabled': !canChangeOwner }">
              <input 
                type="checkbox" 
                v-model="addCurrentAsCollaborator"
                class="checkbox-input"
                :disabled="!canChangeOwner"
              />
              <span class="checkbox-text">
                Add current owner as collaborator
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
            :disabled="!canChangeOwner"
          ></textarea>
          <div class="char-count">{{ transferNote.length }}/200</div>
        </div>

        <div class="form-group" v-if="canChangeOwner">
          <div class="warning-box">
            <div class="warning-icon">⚠️</div>
            <div class="warning-content">
              <div class="warning-title">Ownership Transfer</div>
              <div class="warning-text">
                This action will immediately transfer ownership of the task. 
                The new owner will have full control.
              </div>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button type="button" @click="close" class="btn btn-outline">
            Cancel
          </button>
          <button 
            type="submit" 
            class="btn btn-primary" 
            :disabled="loading || !newOwnerId.trim() || validationError || !canChangeOwner"
          >
            <span v-if="loading" class="spinner"></span> 
            Transfer Ownership
          </button>
        </div>
      </form>

      <!-- Manage Collaborators Form -->
      <form v-if="activeModal === 'collaborators'" @submit.prevent="saveCollaborators" class="modal-form">
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

// Modal state
const activeModal = ref('edit');
const loading = ref(false);

// Edit Task data
const localData = ref({
  title: "",
  deadline: 0,
  status: "unassigned", 
  notes: "",
  attachments: [],
});
const attachments = ref([]);
const fileInput = ref(null);
const localDeadline = ref("");

// Owner Change data
const newOwnerId = ref('');
const addCurrentAsCollaborator = ref(true);
const transferNote = ref('');

// Collaborators data
const currentCollaborators = ref([]);
const originalCollaborators = ref([]);
const newCollaboratorId = ref('');
const bulkCollaborators = ref('');

// Computed property to check if owner can be changed
const canChangeOwner = computed(() => {
  return props.taskData?.status === 'unassigned';
});

// Watch for task data changes
watch(
  () => props.taskData,
  (newVal) => {
    if (newVal) {
      localData.value = { ...newVal };
      localDeadline.value = epochToDateTime(newVal.deadline);
      attachments.value = [];
      
      // Reset owner change data
      newOwnerId.value = '';
      transferNote.value = '';
      addCurrentAsCollaborator.value = true;
      
      // Reset collaborators data
      const collaborators = Array.isArray(newVal.collaborators) ? [...newVal.collaborators] : [];
      currentCollaborators.value = collaborators;
      originalCollaborators.value = [...collaborators];
      newCollaboratorId.value = '';
      bulkCollaborators.value = '';
    }
  },
  { immediate: true }
);

// Auto-switch to edit tab if user tries to access owner tab when not allowed
watch(activeModal, (newModal) => {
  if (newModal === 'owner' && !canChangeOwner.value) {
    activeModal.value = 'edit';
  }
});

// Modal navigation functions
function setActiveModal(modalType) {
  // Prevent switching to owner tab if conditions aren't met
  if (modalType === 'owner' && !canChangeOwner.value) {
    return;
  }
  activeModal.value = modalType;
}

function getModalTitle() {
  const titles = {
    edit: 'Edit Task',
    owner: 'Change Task Owner',
    collaborators: 'Manage Collaborators'
  };
  return titles[activeModal.value] || 'Task Management';
}

// Enhanced validation for owner change that includes status check
const validationError = computed(() => {
  if (!canChangeOwner.value) {
    return "Ownership can only be changed when task status is 'Unassigned'";
  }
  
  if (!newOwnerId.value.trim()) return null;
  
  if (newOwnerId.value === props.taskData?.ownerId) {
    return "New owner cannot be the same as current owner";
  }
  
  if (newOwnerId.value.length < 3) {
    return "User ID must be at least 3 characters";
  }
  
  return null;
});

// Date conversion functions
function dateTimeToEpoch(dateTimeLocal) {
  if (!dateTimeLocal) return 0;
  const epoch = Math.floor(new Date(dateTimeLocal).getTime() / 1000);
  return Math.floor(epoch / 60) * 60;
}

function epochToDateTime(epoch) {
  if (!epoch) return "";
  const roundedEpoch = Math.floor(epoch / 60) * 60;
  const date = new Date(roundedEpoch * 1000);
  return date.toISOString().slice(0, 16);
}

const minDateTime = computed(() => {
  const now = new Date();
  return now.toISOString().slice(0, 16);
});

// File handling functions
function validateFile(file) {
  const MAXFILESIZE = 2 * 1024 * 1024;
  if (file.size > MAXFILESIZE) {
    alert(`File ${file.name} is too large. Maximum size is 2MB.`);
    return false;
  }
  return true;
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const base64 = reader.result.split(",")[1];
      resolve({ name: file.name, type: file.type, size: file.size, base64 });
    };
    reader.onerror = (error) => reject(error);
  });
}

async function handleFileUpload(event) {
  const files = Array.from(event.target.files);
  for (const file of files) {
    if (!validateFile(file)) continue;
    try {
      const base64File = await fileToBase64(file);
      attachments.value.push(base64File);
    } catch {
      alert(`Failed to process file ${file.name}`);
    }
  }
  event.target.value = null;
}

function removeAttachment(index) {
  attachments.value.splice(index, 1);
}

function getFileIcon(type) {
  if (type.startsWith("image")) return "🖼️";
  if (type.includes("pdf")) return "📄";
  if (type.includes("word") || type.includes("doc")) return "📝";
  if (type.includes("excel") || type.includes("sheet")) return "📊";
  if (type.includes("text")) return "📃";
  return "📁";
}

function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// Owner change functions
function formatStatus(status) {
  const statusMap = {
    'ongoing': 'Ongoing',
    'unassigned': 'Unassigned',
    'underreview': 'Under Review',
    'completed': 'Completed'
  };
  return statusMap[status] || status;
}

function isCurrentUser(userId) {
  // You'll need to implement this based on your auth system
  return false; // Replace with actual implementation
}

// Collaborator functions
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
  
  const collaborators = bulkCollaborators.value
    .split(/[,\n]/)
    .map(id => id.trim())
    .filter(id => id);
  
  return [...new Set(collaborators)];
}

// Save functions
async function save() {
  loading.value = true;
  
  const updatedData = {
    ...localData.value,
    deadline: dateTimeToEpoch(localDeadline.value),
    attachments: [...(localData.value.attachments || []), ...attachments.value.map(file => file.base64)]
  };
  
  emit("save", updatedData);
  loading.value = false;
  close();
}

async function saveOwnerChange() {
  if (!canChangeOwner.value || validationError.value || !newOwnerId.value.trim()) return;
  
  loading.value = true;
  
  try {
    const updatedData = {
      ownerId: newOwnerId.value.trim()
    };
    
    if (addCurrentAsCollaborator.value && props.taskData?.ownerId) {
      const currentCollaboratorsList = Array.isArray(props.taskData.collaborators) 
        ? [...props.taskData.collaborators] 
        : [];
      
      if (!currentCollaboratorsList.includes(props.taskData.ownerId)) {
        currentCollaboratorsList.push(props.taskData.ownerId);
        updatedData.collaborators = currentCollaboratorsList;
      }
    }
    
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

async function saveCollaborators() {
  loading.value = true;
  
  try {
    const bulk = parseBulkCollaborators();
    const finalCollaborators = [...new Set([...currentCollaborators.value, ...bulk])];
    
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
  activeModal.value = 'edit';
  newOwnerId.value = '';
  transferNote.value = '';
  addCurrentAsCollaborator.value = true;
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
  max-width: 600px;
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

.modal-header-left h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #374151;
}

.modal-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.modal-tabs {
  display: flex;
  gap: 4px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 8px;
}

.tab-button {
  background: transparent;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.tab-button:hover:not(:disabled) {
  background: #e5e7eb;
  color: #374151;
}

.tab-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  color: #9ca3af;
}

.tab-button.tab-active {
  background: white;
  color: #667eea;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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

/* Restriction Notice Styles */
.restriction-notice {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  margin-bottom: 20px;
}

.restriction-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.restriction-content {
  flex: 1;
}

.restriction-title {
  font-weight: 600;
  color: #dc2626;
  margin-bottom: 4px;
}

.restriction-text {
  font-size: 0.875rem;
  color: #b91c1c;
  line-height: 1.4;
  margin-bottom: 8px;
}

.restriction-hint {
  font-size: 0.75rem;
  color: #7f1d1d;
  font-style: italic;
}

.form-input,
.form-textarea,
.form-select {
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
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input:disabled,
.form-textarea:disabled {
  background: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
  border-color: #e5e7eb;
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

.hint-disabled {
  color: #9ca3af !important;
  font-style: italic;
}

/* Task Info Styles */
.task-info {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.task-title {
  font-weight: 500;
  color: #374151;
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

.status-badge.underreview {
  background: #e0e7ff;
  color: #5b21b6;
}

.status-badge.completed {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.status-restricted {
  background: #fecaca;
  color: #dc2626;
}

/* File Upload Styles */
.file-upload-area {
  position: relative;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  transition: all 0.2s ease;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  gap: 16px;
  padding: 20px;
  align-items: center;
}

.file-upload-area:hover {
  border-color: #667eea;
  background: #f8fafc;
}

.file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 1;
}

.upload-icon {
  font-size: 2rem;
  color: #9ca3af;
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.upload-title {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.upload-subtitle {
  font-size: 0.75rem;
  color: #6b7280;
}

.file-list {
  margin-top: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  background: white;
  transition: background 0.2s ease;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item:hover {
  background: #f9fafb;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  font-size: 1.2rem;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
  word-break: break-word;
}

.file-size {
  font-size: 0.75rem;
  color: #6b7280;
}

.file-remove {
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

.file-remove:hover {
  background: #dc2626;
  transform: scale(1.1);
}

/* Transfer Options */
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

.checkbox-label.checkbox-disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.checkbox-input {
  width: 16px;
  height: 16px;
}

.checkbox-input:disabled {
  cursor: not-allowed;
}

.checkbox-text {
  font-size: 0.875rem;
  color: #374151;
}

/* Warning Box */
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

/* Collaborators Styles */
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

/* Modal Actions */
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

/* Responsive Design */
@media (max-width: 640px) {
  .modal {
    width: 95%;
    max-height: 95vh;
  }
  
  .modal-tabs {
    flex-wrap: wrap;
  }
  
  .tab-button {
    font-size: 0.8rem;
    padding: 6px 8px;
  }
  
  .modal-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .modal-header-right {
    justify-content: space-between;
  }
}
</style>
