<template>
  <div v-if="show" class="modal-overlay" @click="handleBackdropClick">
    <div class="modal" @click.stop>
      <!-- Modal Header -->
      <div class="modal-header">
        <div class="header-content">
          <div class="title-section">
            <h2 class="modal-title">{{ taskData?.title || 'Task Details' }}</h2>
            <div class="task-meta">
              <div class="status-badge" :class="getStatusClass(taskData?.status)">
                <div class="status-dot"></div>
                {{ formatStatus(taskData?.status) }}
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="header-actions">
            <button v-if="canEdit" @click="$emit('edit')" class="action-btn edit-btn" title="Edit">
              <Edit3 class="w-5 h-5" />
              <span class="btn-text">Edit</span>
            </button>

            <button v-if="canDelete" @click="$emit('delete')" class="action-btn delete-btn" title="Delete">
              <Trash2 class="w-5 h-5" />
              <span class="btn-text">Delete</span>
            </button>

            <button @click="$emit('close')" class="action-btn close-btn">
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <!-- Modal Content -->
      <div class="modal-content">
        <!-- Basic Information -->
        <div class="section">
          <h3 class="section-title">Basic Information</h3>
          <div class="info-grid">
            <div class="info-item">
              <label class="info-label">
                <Calendar class="w-4 h-4" />
                Deadline
              </label>
              <div class="info-value" :class="getDeadlineClass()">
                {{ formatDeadline(taskData?.deadline) }}
                <span v-if="isOverdue" class="overdue-indicator">Overdue</span>
                <span v-else-if="isDueSoon" class="due-soon-indicator">Due Soon</span>
              </div>
            </div>

            <div class="info-item">
              <label class="info-label">
                <User class="w-4 h-4" />
                Owner
              </label>
              <div class="info-value">
                {{ formatOwner(taskData?.ownerId) }}
              </div>
            </div>

            <div class="info-item">
              <label class="info-label">
                <UserPlus class="w-4 h-4" />
                Creator
              </label>
              <div class="info-value">
                {{ formatOwner(taskData?.creatorId) }}
              </div>
            </div>

            <div v-if="!isSubtask && taskData?.projectId" class="info-item">
              <label class="info-label">
                <Folder class="w-4 h-4" />
                Project
              </label>
              <div class="info-value">
                {{ projectName }}
              </div>
            </div>

            <div class="info-item">
              <label class="info-label">
                <Clock class="w-4 h-4" />
                Created
              </label>
              <div class="info-value">
                {{ formatDateTime(taskData?.createdAt) }}
              </div>
            </div>

            <div v-if="taskData?.updatedAt && taskData.updatedAt !== taskData.createdAt" class="info-item">
              <label class="info-label">
                <Clock class="w-4 h-4" />
                Last Updated
              </label>
              <div class="info-value">
                {{ formatDateTime(taskData?.updatedAt) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Collaborators -->
        <div v-if="taskData?.collaborators?.length > 0" class="section">
          <h3 class="section-title">
            <Users class="w-5 h-5" />
            Collaborators ({{ taskData.collaborators.length }})
          </h3>
          <div class="collaborators-list">
            <div v-for="collaboratorId in taskData.collaborators" :key="collaboratorId" class="collaborator-item">
              <div class="collaborator-avatar">
                {{ getInitials(collaboratorId) }}
              </div>
              <div class="collaborator-info">
                <span class="collaborator-name">{{ formatOwner(collaboratorId) }}</span>
                <span class="collaborator-role">{{ getUserRole(collaboratorId) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="taskData?.notes" class="section">
          <h3 class="section-title">
            <FileText class="w-5 h-5" />
            Notes
          </h3>
          <div class="notes-content">
            {{ taskData.notes }}
          </div>
        </div>

        <!-- Attachments -->
        <div v-if="taskData?.attachments?.length > 0" class="section">
          <h3 class="section-title">
            <Paperclip class="w-5 h-5" />
            Attachments ({{ taskData.attachments.length }})
          </h3>
          <div class="attachments-list">
            <div v-for="(attachment, index) in taskData.attachments" :key="index" class="attachment-item">
              <div class="attachment-info">
                <div class="attachment-icon">
                  <Download class="w-5 h-5" />
                </div>
                <div class="attachment-details">
                  <span class="attachment-name">{{ getAttachmentName(attachment, index) }}</span>
                  <span class="attachment-type">{{ getAttachmentType(attachment) }}</span>
                </div>
              </div>
              <button @click="downloadAttachment(attachment, index)" class="download-btn" title="Download attachment">
                <Download class="w-4 h-4" />
                Download
              </button>
            </div>
          </div>
        </div>

        <!-- Subtasks (for tasks only) -->
        <div v-if="!isSubtask && taskData?.subtasks?.length > 0" class="section">
          <h3 class="section-title">
            <List class="w-5 h-5" />
            Subtasks ({{ taskData.subtasks.length }})
          </h3>
          <div class="subtasks-list">
            <div v-for="subtask in taskData.subtasks" :key="subtask.subTaskId" class="subtask-item"
              @click="viewSubtask(subtask)">
              <div class="subtask-content">
                <div class="subtask-header">
                  <span class="subtask-title">{{ subtask.title }}</span>
                  <div class="subtask-status" :class="getStatusClass(subtask.status)">
                    <div class="status-dot"></div>
                    {{ formatStatus(subtask.status) }}
                  </div>
                </div>
                <div class="subtask-meta">
                  <span class="subtask-deadline">
                    <Calendar class="w-3 h-3" />
                    {{ formatDeadline(subtask.deadline) }}
                  </span>
                  <span class="subtask-owner">
                    <User class="w-3 h-3" />
                    {{ formatOwner(subtask.ownerId) }}
                  </span>
                </div>
              </div>
              <ChevronRight class="w-5 h-5 text-gray-400" />
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!taskData" class="empty-state">
          <div class="empty-icon">
            <AlertCircle class="w-12 h-12 text-gray-400" />
          </div>
          <p class="empty-text">No task data available</p>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="modal-footer">
        <button @click="$emit('close')" class="footer-btn">
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'
import { computed, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'vue-toastification'
import {
  X,
  Edit3,
  Trash2,
  Calendar,
  User,
  UserPlus,
  Users,
  Clock,
  FileText,
  Paperclip,
  Download,
  List,
  ChevronRight,
  AlertCircle,
  Folder
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
  isSubtask: {
    type: Boolean,
    default: false
  },
  allUsers: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'edit', 'delete'])

// Composables
const authStore = useAuthStore()
const toast = useToast()

// Computed properties
const currentUserId = computed(() => authStore.user?.uid)

const canEdit = computed(() => {
  return props.taskData?.ownerId === currentUserId.value
})

const canDelete = computed(() => {
  return props.taskData?.ownerId === currentUserId.value
})

const isOverdue = computed(() => {
  if (!props.taskData?.deadline) return false
  return props.taskData.deadline * 1000 < Date.now()
})

const isDueSoon = computed(() => {
  if (!props.taskData?.deadline || isOverdue.value) return false
  const daysUntilDue = (props.taskData.deadline * 1000 - Date.now()) / (1000 * 60 * 60 * 24)
  return daysUntilDue <= 7
})

// Methods
function handleBackdropClick() {
  emit('close')
}

function formatStatus(status) {
  const statusMap = {
    'unassigned': 'Unassigned',
    'ongoing': 'Ongoing',
    'under_review': 'Under Review',
    'completed': 'Completed'
  }
  return statusMap[status] || status
}
const projectName = ref('')

watch(() => props.taskData?.projectId, async (newProjectId) => {
  if (newProjectId) {
    try {
      const response = await axios.get(`${import.meta.env.VITE_BACKEND_API}project/indiv/${newProjectId}`)
      projectName.value = response.data.project?.title || 'Unknown Project'
    } catch (error) {
      console.error('Error fetching project name:', error)
      projectName.value = 'Unknown Project'
    }
  } else {
    projectName.value = ''
  }
})
function getStatusClass(status) {
  const classMap = {
    'unassigned': 'status-unassigned',
    'ongoing': 'status-ongoing',
    'under_review': 'status-review',
    'completed': 'status-completed'
  }
  return classMap[status] || 'status-default'
}

function formatDeadline(deadline) {
  if (!deadline) return 'No deadline set'
  const date = new Date(deadline * 1000)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatDateTime(timestamp) {
  if (!timestamp) return 'Unknown'
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatOwner(ownerId) {
  if (!ownerId) return 'Unassigned'
  if (ownerId === currentUserId.value) return 'You'

  const user = props.allUsers.find(u => u.uid === ownerId)
  if (user) {
    return user.name || user.displayName || user.email || 'Unknown User'
  }

  return 'Unknown User'
}

function getUserRole(userId) {
  if (!userId) return ''
  const user = props.allUsers.find(u => u.uid === userId)
  return user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : ''
}

function getInitials(userId) {
  if (!userId) return '?'
  if (userId === currentUserId.value) return 'Y'

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

function getDeadlineClass() {
  if (isOverdue.value) return 'deadline-overdue'
  if (isDueSoon.value) return 'deadline-soon'
  return ''
}

function getAttachmentName(attachment, index) {
  // Try to extract filename if it's a data URL with filename
  const type = getAttachmentType(attachment)

  // Generate a meaningful name based on type
  if (type.includes('Image')) return `Image_${index + 1}`
  if (type.includes('PDF')) return `Document_${index + 1}.pdf`
  if (type.includes('Word')) return `Document_${index + 1}.docx`
  if (type.includes('Excel')) return `Spreadsheet_${index + 1}.xlsx`

  return `Attachment_${index + 1}`
}

function getAttachmentType(attachment) {
  // Try to detect file type from base64 data
  if (!attachment) return 'Unknown'

  const header = attachment.slice(0, 10).toLowerCase()
  if (header.includes('ivbor')) return 'PNG Image'
  if (header.includes('/9j/')) return 'JPEG Image'
  if (header.includes('jvber')) return 'PDF Document'
  if (header.includes('uesdb')) return 'Word Document'
  if (header.includes('pk')) return 'Excel Spreadsheet'

  return 'File'
}

function downloadAttachment(attachment, index) {
  try {
    // Create download link
    const byteCharacters = atob(attachment)
    const byteNumbers = new Array(byteCharacters.length)

    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i)
    }

    const byteArray = new Uint8Array(byteNumbers)
    const blob = new Blob([byteArray])

    // Determine filename and type
    const type = getAttachmentType(attachment)
    let extension = 'bin'

    if (type.includes('PNG')) extension = 'png'
    else if (type.includes('JPEG')) extension = 'jpg'
    else if (type.includes('PDF')) extension = 'pdf'
    else if (type.includes('Word')) extension = 'docx'
    else if (type.includes('Excel')) extension = 'xlsx'

    const filename = getAttachmentName(attachment, index) + (extension !== 'bin' ? '' : `.${extension}`)

    // Create and trigger download
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    toast.success(`Downloaded ${filename}`)

  } catch (error) {
    console.error('Error downloading attachment:', error)
    toast.error('Failed to download attachment')
  }
}

function viewSubtask(subtask) {
  // This could emit an event to open the subtask in detail view
  // For now, just show a toast
  toast.info(`Opening subtask: ${subtask.title}`)
}
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
  max-width: 56rem;
  max-height: 90vh;
  overflow: hidden;
}

.modal-header {
  border-bottom: 1px solid #e5e7eb;
  padding: 1.5rem;
}

.header-content {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.title-section {
  flex: 1;
  min-width: 0;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.5rem;
  word-break: break-words;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.875rem;
  border-radius: 16px;
  font-size: 0.875rem;
  font-weight: 600;
}

.status-badge .status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
}

.status-unassigned {
  background-color: #fef3c7;
  color: #92400e;
}

.status-unassigned .status-dot {
  background-color: #f59e0b;
}

.status-ongoing {
  background-color: #dbeafe;
  color: #1e40af;
}

.status-ongoing .status-dot {
  background-color: #3b82f6;
}

.status-review {
  background-color: #ede9fe;
  color: #6b21a8;
}

.status-review .status-dot {
  background-color: #8b5cf6;
}

.status-completed {
  background-color: #d1fae5;
  color: #065f46;
}

.status-completed .status-dot {
  background-color: #10b981;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.15s ease;
}

.edit-btn {
  background-color: #dbeafe;
  color: #1d4ed8;
}

.edit-btn:hover {
  background-color: #bfdbfe;
}

.delete-btn {
  background-color: #fee2e2;
  color: #b91c1c;
}

.delete-btn:hover {
  background-color: #fecaca;
}

.close-btn {
  background-color: #f3f4f6;
  color: #374151;
}

.close-btn:hover {
  background-color: #e5e7eb;
}

.btn-text {
  display: none;
}

@media (min-width: 640px) {
  .btn-text {
    display: inline;
  }
}

.modal-content {
  padding: 1.5rem;
  overflow-y: auto;
  max-height: calc(90vh - 160px);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section {
  background-color: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #4b5563;
}

.info-value {
  color: #111827;
  font-weight: 500;
}

.deadline-overdue {
  color: #dc2626;
}

.deadline-soon {
  color: #d97706;
}

.overdue-indicator {
  margin-left: 0.5rem;
  font-size: 0.75rem;
  background-color: #fee2e2;
  color: #b91c1c;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-weight: 600;
}

.due-soon-indicator {
  margin-left: 0.5rem;
  font-size: 0.75rem;
  background-color: #fef3c7;
  color: #d97706;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-weight: 600;
}

.collaborators-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
}

@media (min-width: 640px) {
  .collaborators-list {
    grid-template-columns: 1fr 1fr;
  }
}

.collaborator-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem;
  background-color: white;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.collaborator-avatar {
  width: 2.75rem;
  height: 2.75rem;
  background-color: #dbeafe;
  color: #1d4ed8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.875rem;
}

.collaborator-info {
  flex: 1;
  min-width: 0;
}

.collaborator-name {
  display: block;
  font-weight: 600;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.collaborator-role {
  display: block;
  font-size: 0.875rem;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notes-content {
  background-color: white;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  color: #374151;
  white-space: pre-wrap;
  line-height: 1.6;
}

.attachments-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.attachment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background-color: white;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  transition: all 0.15s ease;
}

.attachment-item:hover {
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.attachment-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.attachment-icon {
  width: 2.75rem;
  height: 2.75rem;
  background-color: #f3f4f6;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4b5563;
}

.attachment-details {
  display: flex;
  flex-direction: column;
}

.attachment-name {
  font-weight: 600;
  color: #111827;
}

.attachment-type {
  font-size: 0.875rem;
  color: #6b7280;
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #dbeafe;
  color: #1d4ed8;
  border-radius: 0.5rem;
  transition: all 0.15s ease;
  font-weight: 500;
}

.download-btn:hover {
  background-color: #bfdbfe;
}

.subtasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.subtask-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background-color: white;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.15s ease;
}

.subtask-item:hover {
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  background-color: #fafbff;
}

.subtask-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.subtask-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.subtask-title {
  font-weight: 600;
  color: #111827;
}

.subtask-status {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.subtask-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.subtask-deadline,
.subtask-owner {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 0;
}

.empty-icon {
  margin-bottom: 1rem;
}

.empty-text {
  color: #6b7280;
  font-size: 1.125rem;
}

.modal-footer {
  border-top: 1px solid #e5e7eb;
  padding: 1.5rem;
}

.footer-btn {
  padding: 0.75rem 1.5rem;
  background-color: #f3f4f6;
  color: #374151;
  border-radius: 0.5rem;
  transition: all 0.15s ease;
  font-weight: 500;
}

.footer-btn:hover {
  background-color: #e5e7eb;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .modal {
    margin: 0 0.5rem;
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }

  .action-btn .btn-text {
    display: inline;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
