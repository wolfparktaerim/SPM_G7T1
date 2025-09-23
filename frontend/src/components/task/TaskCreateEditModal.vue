<template>
  <div v-if="show" class="modal-overlay" @click="handleBackdropClick">
    <div class="modal" @click.stop>
      <div class="modal-header">
        <div class="modal-title-section">
          <h3 class="modal-title">
            {{ getModalTitle() }}
          </h3>
          <p class="modal-subtitle">{{ getModalSubtitle() }}</p>
        </div>
        <button @click="$emit('close')" class="modal-close-btn">
          <X class="w-5 h-5" />
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="modal-form">
        <!-- Title Field -->
        <div class="form-group">
          <label class="form-label required">
            {{ isSubtask ? 'Subtask' : 'Task' }} Title
          </label>
          <input v-model="formData.title" type="text" required maxlength="100"
            placeholder="Enter a descriptive title..." class="form-input" :class="{ 'error': errors.title }" />
          <span v-if="errors.title" class="error-message">{{ errors.title }}</span>
        </div>

        <!-- Deadline Field -->
        <div class="form-group">
          <label class="form-label required">Deadline</label>
          <input v-model="deadlineInput" type="datetime-local" required :min="minDateTime" class="form-input"
            :class="{ 'error': errors.deadline }" />
          <span v-if="errors.deadline" class="error-message">{{ errors.deadline }}</span>
        </div>

        <!-- Project ID Field (Tasks only) -->
        <div v-if="!isSubtask" class="form-group">
          <label class="form-label">Project</label>
          <input v-model="formData.projectId" type="text" placeholder="Optional project name..." class="form-input" />
          <p class="form-hint">Link this task to a specific project (optional)</p>
        </div>

        <!-- Status Field -->
        <div class="form-group">
          <label class="form-label">Status</label>
          <select v-model="formData.status" class="form-input">
            <option value="ongoing">Ongoing</option>
            <option value="unassigned">Unassigned</option>
            <option value="under_review">Under Review</option>
            <option value="completed">Completed</option>
          </select>
          <p class="form-hint">
            {{ getStatusHint() }}
          </p>
        </div>

        <!-- Owner Assignment (Managers/Directors only) -->
        <div v-if="canAssignOwner" class="form-group">
          <label class="form-label">Assign Owner</label>
          <select v-model="formData.ownerId" class="form-input">
            <option value="">Select owner...</option>
            <option v-for="user in subordinateUsers" :key="user.uid" :value="user.uid">
              {{ getUserDisplayName(user) }} ({{ formatRole(user.role) }})
            </option>
          </select>
          <p class="form-hint">
            Assign this {{ isSubtask ? 'subtask' : 'task' }} to a team member
          </p>
        </div>

        <!-- Collaborators Field -->
        <div class="form-group">
          <label class="form-label">Collaborators</label>
          <div class="collaborators-input">
            <select v-model="selectedCollaborator" @change="addCollaborator" class="form-input">
              <option value="">Select a collaborator...</option>
              <option v-for="user in availableCollaborators" :key="user.uid" :value="user.uid">
                {{ getUserDisplayName(user) }} ({{ formatRole(user.role) }})
              </option>
            </select>
          </div>

          <!-- Selected Collaborators -->
          <div v-if="formData.collaborators.length > 0" class="collaborators-list">
            <div v-for="(collaboratorId, index) in formData.collaborators" :key="collaboratorId"
              class="collaborator-tag">
              <div class="collaborator-avatar">
                {{ getInitials(collaboratorId) }}
              </div>
              <div class="collaborator-info">
                <span class="collaborator-name">{{ getUserDisplayName(collaboratorId) }}</span>
                <span class="collaborator-role">{{ getUserRole(collaboratorId) }}</span>
              </div>
              <button type="button" @click="removeCollaborator(index)" class="remove-collaborator">
                <X class="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>

        <!-- Notes Field -->
        <div class="form-group">
          <label class="form-label">Notes</label>
          <textarea v-model="formData.notes" rows="4" maxlength="500"
            placeholder="Add any additional notes or instructions..." class="form-textarea"></textarea>
          <div class="char-counter">{{ formData.notes.length }}/500</div>
        </div>

        <!-- Attachments Field -->
        <div class="form-group">
          <label class="form-label">Attachments</label>
          <div class="file-upload-area" @click="$refs.fileInput.click()">
            <input ref="fileInput" type="file" multiple @change="handleFileUpload"
              accept="image/*,application/pdf,.doc,.docx,.txt,.csv,.xlsx" class="file-input" />
            <div class="upload-content">
              <Upload class="w-8 h-8 text-gray-400" />
              <div class="upload-text">
                <span class="upload-title">Add attachments</span>
                <span class="upload-subtitle">
                  Click to select files (PNG, JPG, PDF, DOC, TXT, CSV, XLSX - max 2MB each)
                </span>
              </div>
            </div>
          </div>

          <!-- Existing Attachments -->
          <div v-if="existingAttachments.length > 0" class="attachments-section">
            <h4 class="attachments-title">Current Attachments</h4>
            <div class="attachments-list">
              <div v-for="(attachment, index) in existingAttachments" :key="index" class="attachment-item">
                <div class="attachment-info">
                  <FileText class="w-4 h-4 text-gray-500" />
                  <span class="attachment-name">{{ getAttachmentName(attachment, index) }}</span>
                </div>
                <button type="button" @click="removeExistingAttachment(index)" class="remove-attachment">
                  <X class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <!-- New Attachments -->
          <div v-if="newAttachments.length > 0" class="attachments-section">
            <h4 class="attachments-title">New Attachments</h4>
            <div class="attachments-list">
              <div v-for="(file, index) in newAttachments" :key="index" class="attachment-item">
                <div class="attachment-info">
                  <component :is="getFileIcon(file.type)" class="w-4 h-4 text-gray-500" />
                  <div class="attachment-details">
                    <span class="attachment-name">{{ file.name }}</span>
                    <span class="attachment-size">{{ formatFileSize(file.size) }}</span>
                  </div>
                </div>
                <button type="button" @click="removeNewAttachment(index)" class="remove-attachment">
                  <X class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="form-actions">
          <button type="button" @click="$emit('close')" class="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" :disabled="loading || !isFormValid" class="btn btn-primary">
            <Loader2 v-if="loading" class="w-4 h-4 animate-spin mr-2" />
            {{ isEditing ? 'Update' : 'Create' }} {{ isSubtask ? 'Subtask' : 'Task' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usersService } from '@/services/users'
import { useToast } from 'vue-toastification'
import {
  X,
  Upload,
  FileText,
  Image,
  FileIcon,
  Loader2
} from 'lucide-vue-next'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  taskData: {
    type: Object,
    default: null
  },
  isEditing: {
    type: Boolean,
    default: false
  },
  isSubtask: {
    type: Boolean,
    default: false
  },
  parentTaskId: {
    type: String,
    default: null
  },
  allUsers: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'save'])

// Composables
const authStore = useAuthStore()
const toast = useToast()

// Reactive data
const loading = ref(false)
const allUsers = ref([])
const selectedCollaborator = ref('')
const deadlineInput = ref('')
const newAttachments = ref([])
const existingAttachments = ref([])
const errors = ref({})

// Form data
const formData = ref({
  title: '',
  deadline: 0,
  status: 'ongoing',
  notes: '',
  projectId: '',
  ownerId: '',
  collaborators: []
})

// Computed properties
const currentUser = computed(() => authStore.user)

const canAssignOwner = computed(() => {
  const userRole = currentUser.value?.role
  return userRole === 'manager' || userRole === 'director'
})

const subordinateUsers = computed(() => {
  const currentUserRole = currentUser.value?.role
  if (!currentUserRole) return []

  return props.allUsers.filter(user => {
    if (currentUserRole === 'director') {
      return user.role === 'manager' || user.role === 'staff'
    } else if (currentUserRole === 'manager') {
      return user.role === 'staff'
    }
    return false
  })
})

const availableCollaborators = computed(() => {
  return props.allUsers.filter(user =>
    user.uid !== currentUser.value?.uid &&
    !formData.value.collaborators.includes(user.uid)
  )
})

const minDateTime = computed(() => {
  const now = new Date()
  return now.toISOString().slice(0, 16)
})

const isFormValid = computed(() => {
  return formData.value.title.trim() &&
    formData.value.deadline > 0 &&
    !Object.keys(errors.value).length
})

// Methods
function getModalTitle() {
  if (props.isEditing) {
    return `Edit ${props.isSubtask ? 'Subtask' : 'Task'}`
  }
  return `Create New ${props.isSubtask ? 'Subtask' : 'Task'}`
}

function getModalSubtitle() {
  if (props.isSubtask && props.parentTaskId) {
    const parentTask = props.allUsers.find(task => task.taskId === props.parentTaskId)
    return `Adding subtask to task: ${parentTask?.title || 'Parent Task'}`
  }
  return props.isEditing ? 'Update the details below' : 'Fill in the details below'
}

function getStatusHint() {
  if (canAssignOwner.value) {
    return 'Set to "Unassigned" if you want to assign it later, or "Ongoing" if taking ownership'
  }
  return 'Status will be set to "Ongoing" as you are the owner'
}

function getUserDisplayName(userOrId) {
  if (typeof userOrId === 'string') {
    // It's a user ID
    const user = props.allUsers.find(u => u.uid === userOrId)
    return user ? (user.name || user.displayName || user.email || 'Unknown User') : 'Unknown User'
  } else {
    // It's a user object
    return userOrId.name || userOrId.displayName || userOrId.email || 'Unknown User'
  }
}

function getUserRole(userId) {
  const user = props.allUsers.find(u => u.uid === userId)
  return user?.role ? formatRole(user.role) : ''
}

function formatRole(role) {
  if (!role) return ''
  return role.charAt(0).toUpperCase() + role.slice(1)
}

function getInitials(userId) {
  if (!userId) return '?'
  if (userId === currentUser.value?.uid) return 'Y'

  const user = props.allUsers.find(u => u.uid === userId)
  if (user) {
    const name = user.name || user.displayName || user.email
    if (name) {
      const parts = name.split(' ')
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase()
      }
      return name.slice(0, 2).toUpperCase()
    }
  }

  return userId.slice(0, 2).toUpperCase()
}

function addCollaborator() {
  if (selectedCollaborator.value && !formData.value.collaborators.includes(selectedCollaborator.value)) {
    formData.value.collaborators.push(selectedCollaborator.value)
    selectedCollaborator.value = ''
  }
}

function removeCollaborator(index) {
  formData.value.collaborators.splice(index, 1)
}

function epochToDateTime(epoch) {
  if (!epoch) return ''
  const date = new Date(epoch * 1000)
  return date.toISOString().slice(0, 16)
}

function dateTimeToEpoch(dateTimeLocal) {
  if (!dateTimeLocal) return 0
  return Math.floor(new Date(dateTimeLocal).getTime() / 1000)
}

async function handleFileUpload(event) {
  const files = Array.from(event.target.files)

  for (const file of files) {
    if (!validateFile(file)) continue

    try {
      const base64 = await fileToBase64(file)
      newAttachments.value.push({
        name: file.name,
        size: file.size,
        type: file.type,
        base64: base64
      })
    } catch (error) {
      toast.error(`Failed to process file: ${file.name}`)
    }
  }

  // Reset input
  event.target.value = ''
}

function validateFile(file) {
  const maxSize = 2 * 1024 * 1024 // 2MB
  if (file.size > maxSize) {
    toast.error(`File "${file.name}" is too large. Maximum size is 2MB.`)
    return false
  }
  return true
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => {
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
  })
}

function getFileIcon(type) {
  if (type.startsWith('image/')) return Image
  return FileIcon
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function getAttachmentName(attachment, index) {
  // Try to detect file type from base64 data and generate a meaningful name
  const header = attachment.slice(0, 10).toLowerCase()

  if (header.includes('ivbor')) return `Image_${index + 1}.png`
  if (header.includes('/9j/')) return `Image_${index + 1}.jpg`
  if (header.includes('jvber')) return `Document_${index + 1}.pdf`
  if (header.includes('uesdb')) return `Document_${index + 1}.docx`
  if (header.includes('pk')) return `Spreadsheet_${index + 1}.xlsx`

  return `Attachment_${index + 1}`
}

function removeNewAttachment(index) {
  newAttachments.value.splice(index, 1)
}

function removeExistingAttachment(index) {
  existingAttachments.value.splice(index, 1)
}

function validateForm() {
  errors.value = {}

  if (!formData.value.title.trim()) {
    errors.value.title = 'Title is required'
  }

  if (!formData.value.deadline) {
    errors.value.deadline = 'Deadline is required'
  } else if (formData.value.deadline * 1000 < Date.now()) {
    errors.value.deadline = 'Deadline cannot be in the past'
  }

  return Object.keys(errors.value).length === 0
}

async function handleSubmit() {
  if (!validateForm()) return

  loading.value = true

  try {
    const submitData = { ...formData.value }

    // Handle attachments
    const allAttachments = [
      ...existingAttachments.value,
      ...newAttachments.value.map(file => file.base64)
    ]

    if (allAttachments.length > 0) {
      submitData.attachments = allAttachments
    }

    // Set owner logic
    if (!submitData.ownerId) {
      if (canAssignOwner.value && submitData.status === 'unassigned') {
        // Manager/Director creating unassigned task
        submitData.ownerId = currentUser.value.uid
      } else {
        // Staff or assigned task
        submitData.ownerId = currentUser.value.uid
        if (!canAssignOwner.value) {
          submitData.status = 'ongoing'
        }
      }
    }

    // Add creator as collaborator if not already included
    if (!submitData.collaborators.includes(currentUser.value.uid)) {
      submitData.collaborators.push(currentUser.value.uid)
    }

    emit('save', submitData)

  } catch (error) {
    console.error('Error submitting form:', error)
    toast.error('Failed to save. Please try again.')
  } finally {
    loading.value = false
  }
}

function handleBackdropClick() {
  if (!loading.value) {
    emit('close')
  }
}

function resetForm() {
  formData.value = {
    title: '',
    deadline: 0,
    status: 'ongoing',
    notes: '',
    projectId: '',
    ownerId: '',
    collaborators: []
  }
  deadlineInput.value = ''
  newAttachments.value = []
  existingAttachments.value = []
  selectedCollaborator.value = ''
  errors.value = {}
}

// Watchers
watch(() => props.show, (newVal) => {
  if (newVal) {
    if (props.isEditing && props.taskData) {
      // Populate form with existing data
      formData.value = {
        title: props.taskData.title || '',
        deadline: props.taskData.deadline || 0,
        status: props.taskData.status || 'ongoing',
        notes: props.taskData.notes || '',
        projectId: props.taskData.projectId || '',
        ownerId: props.taskData.ownerId || '',
        collaborators: [...(props.taskData.collaborators || [])]
      }
      deadlineInput.value = epochToDateTime(props.taskData.deadline)
      existingAttachments.value = props.taskData.attachments || []
    } else {
      resetForm()
    }
  }
})

watch(deadlineInput, (newVal) => {
  formData.value.deadline = dateTimeToEpoch(newVal)
})

// Initialize users if not passed as prop
onMounted(async () => {
  if (props.allUsers.length === 0) {
    try {
      const users = await usersService.getAllUsers()
      allUsers.value = users
    } catch (error) {
      console.error('Error fetching users:', error)
      toast.error('Failed to load user list')
    }
  } else {
    allUsers.value = props.allUsers
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 1rem;
}

.modal {
  background-color: white;
  border-radius: 1rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  width: 100%;
  max-width: 42rem;
  max-height: 90vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title-section {
  flex: 1;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.25rem;
}

.modal-subtitle {
  font-size: 0.875rem;
  color: #4b5563;
}

.modal-close-btn {
  padding: 0.5rem;
  color: #9ca3af;
  border-radius: 0.5rem;
  transition: all 0.15s ease;
}

.modal-close-btn:hover {
  color: #4b5563;
  background-color: #f3f4f6;
}

.modal-form {
  padding: 1.5rem;
  overflow-y: auto;
  max-height: calc(90vh - 80px);
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-label.required::after {
  content: '*';
  color: #ef4444;
  margin-left: 0.25rem;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  transition: all 0.15s ease;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
  border-color: #3b82f6;
}

.form-input.error,
.form-textarea.error {
  border-color: #ef4444;
}

.form-input.error:focus,
.form-textarea.error:focus {
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.5);
  border-color: #ef4444;
}

.error-message {
  font-size: 0.875rem;
  color: #dc2626;
  margin-top: 0.25rem;
}

.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.char-counter {
  font-size: 0.75rem;
  color: #6b7280;
  text-align: right;
  margin-top: 0.25rem;
}

.collaborators-input {
  margin-bottom: 0.75rem;
}

.collaborators-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.collaborator-tag {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 0.75rem;
  border-radius: 0.5rem;
}

.collaborator-avatar {
  width: 2rem;
  height: 2rem;
  background-color: #dbeafe;
  color: #1d4ed8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.collaborator-info {
  flex: 1;
  min-width: 0;
}

.collaborator-name {
  display: block;
  font-weight: 500;
  color: #111827;
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.collaborator-role {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-collaborator {
  color: #6b7280;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.remove-collaborator:hover {
  color: #dc2626;
  background-color: #fef2f2;
}

.file-upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 0.5rem;
  padding: 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.file-upload-area:hover {
  border-color: #60a5fa;
  background-color: rgba(239, 246, 255, 0.5);
}

.file-input {
  display: none;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.upload-text {
  text-align: center;
}

.upload-title {
  font-weight: 500;
  color: #374151;
  display: block;
}

.upload-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
}

.attachments-section {
  margin-top: 1rem;
}

.attachments-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.attachments-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.attachment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  background-color: #f9fafb;
  border-radius: 0.5rem;
}

.attachment-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  min-width: 0;
}

.attachment-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.attachment-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-size {
  font-size: 0.75rem;
  color: #6b7280;
}

.remove-attachment {
  padding: 0.25rem;
  color: #9ca3af;
  border-radius: 0.25rem;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.remove-attachment:hover {
  color: #dc2626;
  background-color: #fef2f2;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
}

.btn-primary {
  background-color: #2563eb;
  color: white;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
