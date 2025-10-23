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
              <!-- Priority Badge (Tasks only) -->
              <div v-if="!isSubtask && taskData?.priority" class="priority-badge" :class="getPriorityClass()">
                <span class="priority-icon">⚡</span>
                <span class="priority-value">{{ taskData.priority }}</span>
              </div>
              <!-- Recurring Badge -->
              <div v-if="!isSubtask && taskData?.scheduled" class="recurring-badge">
                🔄 {{ formatSchedule(taskData.schedule) }}
              </div>
              <!-- Enhanced ownership indicators -->
              <div v-if="isOwner" class="ownership-badge">
                👑 Owner
              </div>
              <div v-else-if="isCollaborator" class="collaborator-badge">
                🤝 Collaborator
              </div>
              <div v-else-if="isCreator" class="creator-badge">
                ✨ Creator
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
        <!-- Access Notice (for non-owners viewing task details) -->
        <div v-if="!isOwner && taskData" class="access-notice">
          <div class="access-icon">ℹ️</div>
          <div class="access-content">
            <div class="access-title">View Only Access</div>
            <div class="access-text">
              You are {{ getAccessType() }} this {{ isSubtask ? 'subtask' : 'task' }}.
              Only the owner ({{ formatOwner(taskData.ownerId) }}) can make changes.
            </div>
          </div>
        </div>

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

            <!-- Priority Display (for both tasks AND subtasks) -->
            <div v-if="taskData?.priority" class="info-item">
              <label class="info-label">
                <Zap class="w-4 h-4" />
                Priority
              </label>
              <div class="info-value">
                <div class="priority-display-inline" :class="getPriorityClass()">
                  <span class="priority-icon">⚡</span>
                  <span class="priority-value">{{ taskData.priority }}</span>
                  <span class="priority-label">{{ getPriorityLabel() }}</span>
                </div>
              </div>
            </div>

            <!-- Recurring Info (Tasks only) -->
            <div v-if="!isSubtask && taskData?.scheduled" class="info-item">
              <label class="info-label">
                <Repeat class="w-4 h-4" />
                Recurrence
              </label>
              <div class="info-value">
                <span class="recurring-display">
                  🔄 {{ formatSchedule(taskData.schedule) }}
                  <span v-if="taskData.schedule === 'custom' && taskData.custom_schedule">
                    (every {{ taskData.custom_schedule }} days)
                  </span>
                </span>
              </div>
            </div>

            <div class="info-item">
              <label class="info-label">
                <User class="w-4 h-4" />
                Owner
              </label>
              <div class="info-value">
                {{ formatOwner(taskData?.ownerId) }}
                <span v-if="taskData?.ownerId === currentUserId" class="you-tag">You</span>
              </div>
            </div>

            <div class="info-item">
              <label class="info-label">
                <UserPlus class="w-4 h-4" />
                Creator
              </label>
              <div class="info-value">
                {{ formatOwner(taskData?.creatorId) }}
                <span v-if="taskData?.creatorId === currentUserId" class="you-tag">You</span>
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

            <div v-if="taskData?.startedAt" class="info-item">
              <label class="info-label">
                <Clock class="w-4 h-4" />
                Started
              </label>
              <div class="info-value">
                {{ formatDateTime(taskData.startedAt) }}
              </div>
            </div>

            <div v-if="taskData?.completedAt" class="info-item">
              <label class="info-label">
                <Clock class="w-4 h-4" />
                Completed
              </label>
              <div class="info-value">
                {{ formatDateTime(taskData.completedAt) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Collaborators -->
        <div v-if="taskData?.collaborators?.length > 0" class="section">
          <h3 class="section-title">
            <Users class="w-5 h-5" />
            Collaborators ({{ taskData.collaborators.length }})
            <span v-if="isOwner" class="management-hint" title="You can manage collaborators in the edit modal">
              ⚙️
            </span>
          </h3>
          <div class="collaborators-list">
            <div v-for="collaboratorId in taskData.collaborators" :key="collaboratorId" class="collaborator-item">
              <div class="collaborator-avatar">
                {{ getInitials(collaboratorId) }}
              </div>
              <div class="collaborator-info">
                <span class="collaborator-name">{{ formatOwner(collaboratorId) }}</span>
                <span class="collaborator-role">{{ getUserRole(collaboratorId) }}</span>
                <span class="collaborator-dept">{{ getUserDepartment(collaboratorId) }}</span>
              </div>
              <div class="collaborator-indicators">
                <div v-if="collaboratorId === taskData.ownerId" class="owner-indicator" title="Task Owner">
                  👑
                </div>
                <div v-if="collaboratorId === taskData.creatorId" class="creator-indicator" title="Task Creator">
                  ✨
                </div>
                <div v-if="collaboratorId === currentUserId" class="you-indicator">
                  You
                </div>
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
                  <span v-if="subtask.ownerId === currentUserId" class="subtask-ownership">
                    👑 You own this
                  </span>
                  <span v-else-if="subtask.collaborators?.includes(currentUserId)" class="subtask-collaboration">
                    🤝 You collaborate
                  </span>
                  <span v-else-if="subtask.creatorId === currentUserId" class="subtask-creation">
                    ✨ You created this
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
        <div class="footer-info">
          <span v-if="isOwner" class="permission-text">
            🔓 You have full access to this {{ isSubtask ? 'subtask' : 'task' }}
            <span class="dept-context">({{ currentUserDepartment }})</span>
          </span>
          <span v-else-if="isCollaborator" class="permission-text">
            👀 You have view access as a collaborator
            <span class="dept-context">({{ currentUserDepartment }})</span>
          </span>
          <span v-else-if="isCreator" class="permission-text">
            ✨ You have view access as the creator
            <span class="dept-context">({{ currentUserDepartment }})</span>
          </span>
          <span v-else class="permission-text">
            👁️ You have view access only
            <span class="dept-context">({{ currentUserDepartment }})</span>
          </span>
        </div>
        <button @click="$emit('close')" class="footer-btn">
          Close
        </button>
      </div>
    </div>


    <!-- Comment Section -->
    <div class="section">
      <CommentSection
        :key="`comment-${isSubtask ? 'subtask' : 'task'}-${isSubtask ? taskData?.subtaskId : taskData?.taskId}`"
        :parent-id="isSubtask ? taskData.subTaskId : taskData.taskId" :parent-type="isSubtask ? 'subtask' : 'task'"
        :current-user-id="currentUserId" :all-users="allUsers" :collaborators="taskData?.collaborators || []"
        @thread-created="handleCommentThreadCreated" @thread-updated="handleCommentThreadUpdated"
        @thread-resolved="handleCommentThreadResolved" />
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
  Folder,
  Zap,
  Repeat
} from 'lucide-vue-next'

import CommentSection from './CommentSection.vue'

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

const emit = defineEmits(['close', 'edit', 'delete', 'view-subtask'])

// Composables
const authStore = useAuthStore()
const toast = useToast()

// Computed properties
const currentUserId = computed(() => authStore.user?.uid)
const currentUserDepartment = computed(() => authStore.user?.department || 'Unknown Dept')

const isOwner = computed(() => {
  return props.taskData?.ownerId === currentUserId.value
})

const isCollaborator = computed(() => {
  return props.taskData?.collaborators?.includes(currentUserId.value) || false
})

const isCreator = computed(() => {
  return props.taskData?.creatorId === currentUserId.value
})

const canEdit = computed(() => {
  return isOwner.value
})

const canDelete = computed(() => {
  return isOwner.value
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

function getAccessType() {
  if (isCollaborator.value) return 'a collaborator on'
  if (isCreator.value) return 'the creator of'
  return 'viewing'
}

// Priority methods
function getPriorityClass() {
  const priority = props.taskData?.priority || 0
  if (priority >= 8) return 'priority-critical'
  if (priority >= 6) return 'priority-high'
  if (priority >= 4) return 'priority-medium'
  return 'priority-low'
}

function getPriorityLabel() {
  const priority = props.taskData?.priority || 0
  if (priority >= 8) return 'Critical'
  if (priority >= 6) return 'High'
  if (priority >= 4) return 'Medium'
  return 'Low'
}

function formatSchedule(schedule) {
  if (!schedule) return ''
  const scheduleMap = {
    'daily': 'Daily',
    'weekly': 'Weekly',
    'monthly': 'Monthly',
    'custom': 'Custom'
  }
  return scheduleMap[schedule] || schedule
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
      const response = await axios.get(`${import.meta.env.VITE_BACKEND_API}project/${currentUserId.value}`)
      for (const project of response.data.projects) {
        if (project.projectId === newProjectId) {
          projectName.value = project.title || 'Unknown Project'
        }
      }
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
  return date.toLocaleString('en-SG', {
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
  return date.toLocaleString('en-SG', {
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

function getUserDepartment(userId) {
  if (!userId) return ''
  const user = props.allUsers.find(u => u.uid === userId)
  return user?.department || 'Unknown Dept'
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
  const type = getAttachmentType(attachment)

  if (type.includes('Image')) return `Image_${index + 1}`
  if (type.includes('PDF')) return `Document_${index + 1}.pdf`
  if (type.includes('Word')) return `Document_${index + 1}.docx`
  if (type.includes('Excel')) return `Spreadsheet_${index + 1}.xlsx`

  return `Attachment_${index + 1}`
}

function getAttachmentType(attachment) {
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
    // Remove data URL prefix if present
    const base64Data = attachment.replace(/^data:.*?;base64,/, '')

    // Decode base64 to binary
    const byteCharacters = atob(base64Data)
    const byteNumbers = new Array(byteCharacters.length)

    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i)
    }

    const byteArray = new Uint8Array(byteNumbers)

    // Detect MIME type and extension from file signature
    const { mimeType, extension } = detectFileType(byteArray, attachment)

    // Create blob with proper MIME type
    const blob = new Blob([byteArray], { type: mimeType })

    // Generate filename
    const filename = getAttachmentName(attachment, index) + '.' + extension

    // Create download link
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

function detectFileType(byteArray, base64String) {
  // Get file signature (magic numbers) from first bytes
  const header = Array.from(byteArray.slice(0, 8))
    .map(byte => byte.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase()

  // Check base64 string prefix for quicker detection
  const prefix = base64String.substring(0, 20)

  // PDF: starts with %PDF (hex: 25 50 44 46)
  if (header.startsWith('25504446') || prefix.startsWith('JVBERi0')) {
    return { mimeType: 'application/pdf', extension: 'pdf' }
  }

  // PNG: starts with PNG signature (89 50 4E 47)
  if (header.startsWith('89504E47') || prefix.startsWith('iVBORw0KGgo')) {
    return { mimeType: 'image/png', extension: 'png' }
  }

  // JPEG: starts with FF D8 FF
  if (header.startsWith('FFD8FF') || prefix.startsWith('/9j/')) {
    return { mimeType: 'image/jpeg', extension: 'jpg' }
  }

  // ZIP-based formats (DOCX, XLSX): start with PK (50 4B)
  if (header.startsWith('504B0304') || header.startsWith('504B0506') || prefix.startsWith('UEs')) {
    // Check for Office Open XML formats
    const text = String.fromCharCode(...byteArray.slice(0, 200))

    if (text.includes('word/') || text.includes('document.xml')) {
      return {
        mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        extension: 'docx'
      }
    }

    if (text.includes('xl/') || text.includes('workbook.xml')) {
      return {
        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        extension: 'xlsx'
      }
    }

    // Generic ZIP
    return { mimeType: 'application/zip', extension: 'zip' }
  }

  // Old Word doc format: D0 CF 11 E0
  if (header.startsWith('D0CF11E0')) {
    return { mimeType: 'application/msword', extension: 'doc' }
  }

  // CSV/TXT: Check if all characters are printable ASCII/UTF-8
  const sample = byteArray.slice(0, 512)
  let isPrintable = true
  let hasCommas = false

  for (let i = 0; i < sample.length; i++) {
    const byte = sample[i]
    if ((byte < 32 && byte !== 9 && byte !== 10 && byte !== 13) || byte === 127) {
      isPrintable = false
      break
    }
    if (byte === 44) hasCommas = true // comma character
  }

  if (isPrintable) {
    if (hasCommas) {
      return { mimeType: 'text/csv', extension: 'csv' }
    }
    return { mimeType: 'text/plain', extension: 'txt' }
  }

  // GIF: starts with GIF89a or GIF87a
  if (header.startsWith('474946383961') || header.startsWith('474946383761') ||
    prefix.startsWith('R0lGOD')) {
    return { mimeType: 'image/gif', extension: 'gif' }
  }

  // Default fallback
  return { mimeType: 'application/octet-stream', extension: 'bin' }
}


function viewSubtask(subtask) {
  emit('close')
  emit('view-subtask', subtask)
}
</script>

<style scoped>
/* Priority display styles */
.priority-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
}

.priority-icon {
  font-size: 0.875rem;
}

.priority-value {
  min-width: 16px;
  text-align: center;
}

.priority-critical {
  background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3);
}

.priority-high {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.priority-medium {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.priority-low {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
}

.priority-display-inline {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: 12px;
  font-weight: 600;
}

.priority-label {
  font-size: 0.75rem;
  text-transform: uppercase;
}

.recurring-badge {
  background-color: #e0e7ff;
  color: #4338ca;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.recurring-display {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 500;
}

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

.ownership-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  background-color: #fef3c7;
  color: #92400e;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.collaborator-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  background-color: #e0e7ff;
  color: #5b21b6;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.creator-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  background-color: #f0fdf4;
  color: #15803d;
  display: flex;
  align-items: center;
  gap: 0.25rem;
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

.access-notice {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.access-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.access-content {
  flex: 1;
}

.access-title {
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 4px;
}

.access-text {
  font-size: 0.875rem;
  color: #075985;
  line-height: 1.4;
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

.management-hint {
  color: #6b7280;
  font-size: 0.875rem;
  cursor: help;
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.you-tag {
  font-size: 0.75rem;
  background-color: #dbeafe;
  color: #1d4ed8;
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  font-weight: 600;
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
  position: relative;
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

.collaborator-dept {
  display: block;
  font-size: 0.75rem;
  color: #9ca3af;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.collaborator-indicators {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.owner-indicator,
.creator-indicator {
  font-size: 1rem;
}

.you-indicator {
  font-size: 0.75rem;
  background-color: #dbeafe;
  color: #1d4ed8;
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
  font-weight: 600;
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
  flex-wrap: wrap;
}

.subtask-deadline,
.subtask-owner {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.subtask-ownership,
.subtask-collaboration,
.subtask-creation {
  font-size: 0.75rem;
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.subtask-ownership {
  background-color: #fef3c7;
  color: #92400e;
}

.subtask-collaboration {
  background-color: #e0e7ff;
  color: #5b21b6;
}

.subtask-creation {
  background-color: #f0fdf4;
  color: #15803d;
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
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-info {
  flex: 1;
}

.permission-text {
  font-size: 0.875rem;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.dept-context {
  font-size: 0.75rem;
  color: #9ca3af;
  font-style: italic;
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

  .modal-footer {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .footer-info {
    text-align: center;
  }
}
</style>
