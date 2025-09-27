<template>
  <div v-if="show" class="modal-overlay" @click="handleBackdropClick">
    <div class="modal" @click.stop>
      <!-- Loading Overlay -->
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <div class="loading-text">
            {{ isEditing ? 'Updating' : 'Creating' }} {{ isSubtask ? 'Subtask' : 'Task' }}...
          </div>
        </div>
      </div>

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
          <input v-model="deadlineInput" type="datetime-local" required class="form-input"
            :class="{ 'error': errors.deadline }" />
          <span v-if="errors.deadline" class="error-message">{{ errors.deadline }}</span>
        </div>
        <!-- Add this after the Deadline field and before the Project field -->
        <div v-if="isSubtask && isEditing" class="form-group">
          <label class="form-label required">Status</label>
          <select v-model="formData.status" required class="form-input" :class="{ 'error': errors.status }">
            <option value="unassigned">Unassigned</option>
            <option value="ongoing">Ongoing</option>
            <option value="overdue">Under review</option>
            <option value="completed">Completed</option>
            
          </select>
          <span v-if="errors.status" class="error-message">{{ errors.status }}</span>
          <p class="form-hint">Update the current status of this subtask</p>
        </div>

        <!-- Project Field (Tasks only) -->
        <div v-if="!isSubtask" class="form-group">
          <label class="form-label">Project</label>
          <select v-model="formData.projectId" class="form-input" :disabled="loadingProjects">
            <option value="">
              {{ loadingProjects ? 'Loading projects...' : 'Select a project (optional)' }}
            </option>
            <option v-for="project in availableProjects" :key="project.projectId" :value="project.projectId">
              {{ project.title }}
              <template v-if="project.ownerUid === currentUser?.uid"> (Owner)</template>
              <template v-else> (Collaborator)</template>
            </option>
          </select>
          <p class="form-hint">
            Link this task to a specific project (optional)
            <span v-if="availableProjects.length === 0 && !loadingProjects" class="text-amber-600">
              - No projects available
            </span>
          </p>
        </div>
        <!-- Status is automatically managed based on user role and assignments -->

        <!-- Owner Assignment (Managers/Directors only) -->
        <div v-if="canAssignOwner" class="form-group">
          <label class="form-label">Assign Owner</label>
          <select v-model="formData.ownerId" @change="handleOwnerChange" class="form-input">
            <option value="">Yourself</option>
            <option v-for="user in subordinateUsers" :key="user.uid" :value="user.uid">
              {{ getUserDisplayName(user) }} ({{ formatRole(user.role) }})
            </option>
          </select>
          <p class="form-hint">
            Assign this {{ isSubtask ? 'subtask' : 'task' }} to a team member in your department. Status will be managed
            automatically.
          </p>
        </div>

        <!-- Collaborators Field (Only for owners) -->
        <div v-if="canManageCollaborators" class="form-group">
          <label class="form-label">Collaborators</label>
          <!-- Department info -->
          <div class="dept-info">
            <span class="dept-badge">{{ currentUser?.department || 'Unknown Department' }}</span>
            <span class="dept-text">You can only add collaborators from your department</span>
          </div>
          <div class="collaborators-input">
            <select v-model="selectedCollaborator" @change="addCollaborator" class="form-input"
              :disabled="availableCollaborators.length === 0">
              <option value="">
                <span v-if="availableCollaborators.length === 0">No available collaborators in your department</span>
                <span v-else>Select a collaborator from your department...</span>
              </option>
              <option v-for="user in availableCollaborators" :key="user.uid" :value="user.uid">
                {{ getUserDisplayName(user) }} ({{ formatRole(user.role) }})
              </option>
            </select>
          </div>

          <!-- No collaborators message -->
          <div v-if="availableCollaborators.length === 0" class="no-collaborators-message">
            <div class="message-icon">👥</div>
            <div class="message-content">
              <div class="message-title">No Available Collaborators</div>
              <div class="message-text">There are no other users in your department ({{ currentUser?.department }}) to
                add as
                collaborators.</div>
            </div>
          </div>

          <!-- Collaborators list -->
          <div v-for="(collaboratorId, index) in displayCollaborators" :key="collaboratorId" class="collaborator-tag">
            <div class="collaborator-avatar">
              {{ getInitials(collaboratorId) }}
            </div>
            <div class="collaborator-info">
              <span class="collaborator-name">{{ getUserDisplayName(collaboratorId) }}</span>
              <span class="collaborator-role">{{ getUserRole(collaboratorId) }}</span>
            </div>
            <button type="button" @click="removeCollaborator(collaboratorId)" class="remove-collaborator">
              <X class="w-3 h-3" />
            </button>
          </div>
        </div>

        <!-- Collaborators View Only (For non-owners) -->
        <div v-else-if="displayCollaborators.length > 0" class="form-group">
          <label class="form-label">Collaborators (View Only)</label>
          <div class="collaborators-list">
            <div v-for="collaboratorId in displayCollaborators" :key="collaboratorId" class="collaborator-tag readonly">
              <div class="collaborator-avatar">
                {{ getInitials(collaboratorId) }}
              </div>
              <div class="collaborator-info">
                <span class="collaborator-name">{{ getUserDisplayName(collaboratorId) }}</span>
                <span class="collaborator-role">{{ getUserRole(collaboratorId) }}</span>
              </div>
            </div>
          </div>
          <p class="form-hint">
            Only the task owner can modify collaborators. Collaborators must be from the same department.
          </p>
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
import axios from 'axios'
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
const projects = ref([])
const loadingProjects = ref(false)
const selectedCollaborator = ref('')
const deadlineInput = ref('')
const newAttachments = ref([])
const existingAttachments = ref([])
const errors = ref({})

// Form data
const formData = ref({
  title: '',
  deadline: 0,
  status: 'unassigned', // Will be set properly in resetForm based on user role
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

// Check if current user can manage collaborators (only owners can)
const canManageCollaborators = computed(() => {
  if (!props.isEditing) {
    // During creation, creator can manage collaborators
    return true
  }
  // During editing, only owner can manage collaborators
  return props.taskData?.ownerId === currentUser.value?.uid
})

// UPDATED: Filter subordinate users by same department only
const subordinateUsers = computed(() => {
  const currentUserRole = currentUser.value?.role
  const currentUserDept = currentUser.value?.department

  if (!currentUserRole || !currentUserDept) return []

  return props.allUsers.filter(user => {
    // Must be in same department
    if (user.department !== currentUserDept) return false

    if (currentUserRole === 'director') {
      return user.role === 'manager' || user.role === 'staff'
    } else if (currentUserRole === 'manager') {
      return user.role === 'staff'
    }
    return false
  })
})

// UPDATED: Filter collaborators by same department only (regardless of role)
const availableCollaborators = computed(() => {
  const currentUserDept = currentUser.value?.department
  if (!currentUserDept) return []

  return props.allUsers.filter(user =>
    user.uid !== currentUser.value?.uid &&
    user.department === currentUserDept &&
    !formData.value.collaborators.includes(user.uid)
  )
})

// UPDATED: Display collaborators excluding the owner (for UI purposes)
const displayCollaborators = computed(() => {
  if (!props.isEditing) {
    // During creation, show all collaborators except current user
    return formData.value.collaborators.filter(id => id !== currentUser.value?.uid)
  }

  // During editing, exclude the owner from display
  const ownerId = formData.value.ownerId || currentUser.value?.uid
  return formData.value.collaborators.filter(id => id !== ownerId)
})

const availableProjects = computed(() => {
  return projects.value.filter(project =>
    project.ownerUid === currentUser.value?.uid ||
    project.collaborators?.includes(currentUser.value?.uid)
  )
})

const isFormValid = computed(() => {
  return formData.value.title.trim() &&
    formData.value.deadline > 0 &&
    !Object.keys(errors.value).length
})

// Methods
async function fetchProjects() {
  if (!currentUser.value?.uid) return

  loadingProjects.value = true
  try {
    console.log('Fetching projects for user:', currentUser.value.uid)
    const response = await axios.get(`${import.meta.env.VITE_BACKEND_API}project/${currentUser.value.uid}`)
    projects.value = response.data.projects || []
    console.log(`Loaded ${projects.value.length} projects`)
  } catch (error) {
    console.error('Error fetching projects:', error)
    if (error.response?.status === 404) {
      // No projects found is acceptable
      projects.value = []
    } else {
      toast.error('Failed to load projects')
    }
  } finally {
    loadingProjects.value = false
  }
}

// UPDATED: Handle owner change with new status rules
function handleOwnerChange() {
  const currentUserRole = currentUser.value?.role
  const assignedUser = props.allUsers.find(u => u.uid === formData.value.ownerId)
  const assignedUserRole = assignedUser?.role
  const currentStatus = formData.value.status

  // RULE 1 & 2: Staff users always have 'ongoing' status and cannot change it
  if (currentUserRole === 'staff') {
    formData.value.status = 'ongoing'
    return
  }

  // Only change status if current status is "unassigned"
  if (currentStatus !== 'unassigned') {
    // Keep current status if it's not unassigned during editing
    return
  }

  // RULE 2: For Directors/Managers during creation or when editing unassigned tasks
  if (formData.value.ownerId) {
    // Someone is assigned as owner
    if (assignedUserRole === 'staff') {
      // Assigning to staff = ongoing
      formData.value.status = 'ongoing'
    } else {
      // Director assigning to manager, or manager to manager = unassigned
      formData.value.status = 'unassigned'
    }
  } else {
    // No owner assigned = unassigned for directors/managers
    formData.value.status = 'unassigned'
  }
}


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

// UPDATED: Remove collaborator by ID instead of index
function removeCollaborator(collaboratorId) {
  const index = formData.value.collaborators.findIndex(id => id === collaboratorId)
  if (index > -1) {
    formData.value.collaborators.splice(index, 1)
  }
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

    // UPDATED: Enhanced status and ownership logic
    const currentUserRole = currentUser.value?.role

    // Only apply status logic during creation OR during editing if current status is 'unassigned'
    const shouldUpdateStatus = !props.isEditing || submitData.status === 'unassigned'

    if (!submitData.ownerId) {
      // No specific owner assigned - current user becomes owner
      submitData.ownerId = currentUser.value.uid

      // Set status based on user role (only if we should update status)
      if (shouldUpdateStatus) {
        if (currentUserRole === 'staff') {
          submitData.status = 'ongoing'
        } else {
          // Director/Manager creating unassigned task for themselves
          submitData.status = 'unassigned'
        }
      }
    } else if (shouldUpdateStatus) {
      // Owner is assigned - only update status if we should
      const assignedUser = props.allUsers.find(u => u.uid === submitData.ownerId)
      const assignedUserRole = assignedUser?.role

      if (currentUserRole === 'staff') {
        // Staff always have ongoing status
        submitData.status = 'ongoing'
      } else if (assignedUserRole === 'staff') {
        // Assigning to staff = ongoing
        submitData.status = 'ongoing'
      } else {
        // Assigning to manager/director = unassigned
        submitData.status = 'unassigned'
      }
    }

    // Always ensure owner is in collaborators (but hidden in UI)
    const ownerId = submitData.ownerId || currentUser.value.uid
    if (!submitData.collaborators.includes(ownerId)) {
      submitData.collaborators.push(ownerId)
    }

    // Also ensure creator is in collaborators
    if (!submitData.collaborators.includes(currentUser.value.uid)) {
      submitData.collaborators.push(currentUser.value.uid)
    }

    // Add a small delay for better UX (shows loading state)
    await new Promise(resolve => setTimeout(resolve, 500))

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
  // UPDATED: Set initial status based on user role
  const currentUserRole = currentUser.value?.role
  const initialStatus = currentUserRole === 'staff' ? 'ongoing' : 'unassigned'

  formData.value = {
    title: '',
    deadline: 0,
    status: initialStatus,
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
      // Creating new task/subtask - set proper initial status
      resetForm()
      // Ensure status is set correctly for new creation
      const currentUserRole = currentUser.value?.role
      if (currentUserRole === 'staff') {
        formData.value.status = 'ongoing'
      } else {
        formData.value.status = 'unassigned'
      }
    }
  }
})

watch(deadlineInput, (newVal) => {
  formData.value.deadline = dateTimeToEpoch(newVal)
})

// Initialize users and projects
onMounted(async () => {
  // Load users if not passed as prop
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

  // Load projects
  await fetchProjects()
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
  position: relative;
}

/* Loading overlay styles */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  border-radius: 1rem;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner-ring {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.loading-text {
  color: #374151;
  font-weight: 600;
  font-size: 0.875rem;
  text-align: center;
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

.form-input:disabled {
  background-color: #f9fafb;
  color: #6b7280;
  cursor: not-allowed;
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

.text-amber-600 {
  color: #d97706;
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

.dept-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background-color: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 0.5rem;
}

.dept-badge {
  background-color: #2563eb;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

.dept-text {
  font-size: 0.75rem;
  color: #0369a1;
}

.no-collaborators-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background-color: #fef3c7;
  border: 1px solid #fbbf24;
  border-radius: 0.5rem;
  margin-bottom: 0.75rem;
}

.message-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.message-content {
  flex: 1;
}

.message-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #92400e;
  margin-bottom: 0.25rem;
}

.message-text {
  font-size: 0.75rem;
  color: #b45309;
  line-height: 1.3;
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

.collaborator-tag.readonly {
  background-color: #f9fafb;
  border-color: #e5e7eb;
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
