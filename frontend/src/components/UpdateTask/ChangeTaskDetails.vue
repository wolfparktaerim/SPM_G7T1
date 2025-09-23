<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal" @click.stop>
      <div class="modal-header">
        <h3>Edit Task</h3>
        <button @click="close" class="modal-closebutton">×</button>
      </div>
      <form @submit.prevent="save" class="modal-form">
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

// Watch for task data changes
watch(
  () => props.taskData,
  (newVal) => {
    if (newVal) {
      localData.value = { ...newVal };
      localDeadline.value = epochToDateTime(newVal.deadline);
      attachments.value = [];
    }
  },
  { immediate: true }
);

// Date conversion functions with proper rounding
function dateTimeToEpoch(dateTimeLocal) {
  if (!dateTimeLocal) return 0;
  const epoch = Math.floor(new Date(dateTimeLocal).getTime() / 1000);
  return Math.floor(epoch / 60) * 60; // Round down to nearest minute
}

function epochToDateTime(epoch) {
  if (!epoch) return "";
  // Round the epoch to maintain consistency
  const roundedEpoch = Math.floor(epoch / 60) * 60;
  const date = new Date(roundedEpoch * 1000);
  return date.toISOString().slice(0, 16);
}

const minDateTime = computed(() => {
  const now = new Date();
  return now.toISOString().slice(0, 16);
});

// File handling functions (keep existing)
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

// Modified save function to emit data instead of handling API directly
async function save() {
  loading.value = true;
  
  // Prepare the updated data in the format expected by the main file
  const updatedData = {
    ...localData.value,
    deadline: dateTimeToEpoch(localDeadline.value), // Convert to epoch
    attachments: [...(localData.value.attachments || []), ...attachments.value.map(file => file.base64)] // Combine existing and new attachments as base64 strings
  };
  
  // Emit the save event with the prepared data
  // The parent component will handle the actual API call
  emit("save", updatedData);
  
  loading.value = false;
  close();
}

function close() {
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
  max-width: 500px;
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
.form-textarea {
  resize: vertical;
}
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
