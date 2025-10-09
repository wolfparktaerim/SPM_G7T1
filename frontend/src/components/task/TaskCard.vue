<template>
  <div class="task-card" :class="getCardColorClass()" draggable="true" @dragstart="handleDragStart"
    @dragend="handleDragEnd">
    <!-- Main Task Content -->
    <div class="task-content">
      <!-- Task Header -->
      <div class="task-header">
        <div class="task-title-section">
          <div class="title-row">
            <h4 class="task-title" :title="task.title">{{ task.title }}</h4>
            <!-- Priority Badge -->
            <div class="priority-badge" :class="getPriorityClass(task.priority)"
              :title="`Priority: ${task.priority || 5}`">
              <span class="priority-icon">⭐</span>
              <span class="priority-value">{{ task.priority || 5 }}</span>
            </div>
          </div>
          <div class="task-meta">
            <span class="project-badge">{{ projectDisplayName }}</span>
            <!-- Ownership indicator - Clear and prominent -->
            <span v-if="isOwnedByYou" class="ownership-indicator-you" title="You are the owner">
              👑 You Own This
            </span>
            <span v-else-if="isCollaboratedByYou" class="ownership-indicator-collab" title="You are a collaborator">
              🤝 Collaborating
            </span>
            <span v-else class="ownership-indicator-other" title="Owned by another user">
              👤 Others' Task
            </span>
            <!-- Recurring indicator -->
            <span v-if="task.scheduled" class="recurring-indicator"
              :title="`Recurring: ${formatSchedule(task.schedule, task.custom_schedule)}`">
              🔁 {{ formatSchedule(task.schedule, task.custom_schedule) }}
            </span>
          </div>
        </div>

        <!-- Expand Subtasks Button -->
        <button v-if="task.subtasks?.length > 0" @click="toggleSubtasks" class="expand-button"
          :class="{ 'expanded': showSubtasks }">
          <ChevronDown class="w-4 h-4 transition-transform duration-200" />
          <span class="subtask-count">{{ task.subtasks.length }}</span>
        </button>
      </div>

      <!-- Deadline -->
      <div class="deadline-section">
        <Calendar class="w-4 h-4" />
        <span class="deadline-text">Deadline:</span>
        <span class="deadline-text">{{ formatDeadline(task.deadline) }}</span>
        <span v-if="task.status === 'completed'" class="status-badge-completed">✓ Completed</span>
        <span v-else-if="isOverdue" class="status-badge-overdue">⚠ Overdue</span>
        <span v-else-if="isDueSoon" class="status-badge-due-soon">⏰ Due Soon</span>
      </div>

      <!-- Owner -->
      <div class="owner-section">
        <User class="w-4 h-4" />
        <span class="owner-text">Owned by: </span>
        <span class="owner-text">{{ formatOwner(task.ownerId) }}</span>
      </div>

      <!-- Collaborators (if any) -->
      <div v-if="task.collaborators?.length > 0" class="collaborators-section">
        <Users class="w-4 h-4" />
        <span class="collaborators-text">
          +{{ task.collaborators.length }} collaborator{{ task.collaborators.length > 1 ? 's' : '' }}
        </span>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button @click="$emit('view', task)" class="action-btn view-btn" title="View Details">
          <Eye class="w-4 h-4" />
        </button>

        <button v-if="canEdit" @click="$emit('edit', task)" class="action-btn edit-btn" title="Edit Task">
          <Edit3 class="w-4 h-4" />
        </button>

        <button v-if="canEdit" @click="$emit('create-subtask', task.taskId)" class="action-btn add-btn"
          title="Add Subtask">
          <Plus class="w-4 h-4" />
        </button>

        <button v-if="canDelete" @click="$emit('delete', task)" class="action-btn delete-btn" title="Delete Task">
          <Trash2 class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Subtasks Expansion -->
    <transition name="subtasks">
      <div v-if="showSubtasks && task.subtasks?.length > 0" class="subtasks-container">
        <div class="subtasks-header">
          <h5 class="subtasks-title">Subtasks ({{ task.subtasks.length }})</h5>
        </div>

        <div class="subtasks-list">
          <div v-for="subtask in task.subtasks" :key="subtask.subTaskId" class="subtask-item"
            :class="getSubtaskColorClass(subtask)" @click="$emit('view-subtask', subtask)">
            <div class="subtask-content">
              <div class="subtask-header">
                <div class="subtask-title-row">
                  <span class="subtask-title">{{ subtask.title }}</span>
                  <!-- Subtask Priority Badge -->
                  <div class="subtask-priority-badge" :class="getPriorityClass(subtask.priority)"
                    :title="`Priority: ${subtask.priority || 5}`">
                    ⭐{{ subtask.priority || 5 }}
                  </div>
                </div>
                <div class="subtask-status" :class="getStatusDotClass(subtask.status)">
                  <div class="status-dot"></div>
                  <span class="status-text">{{ formatStatus(subtask.status) }}</span>
                </div>
              </div>

              <div class="subtask-meta">
                <div class="subtask-deadline">
                  <Calendar class="w-3 h-3" />
                  <span>{{ formatDeadline(subtask.deadline) }}</span>
                  <span v-if="subtask.status === 'completed'" class="subtask-status-badge-completed">✓</span>
                  <span v-else-if="isSubtaskOverdue(subtask)" class="subtask-status-badge-overdue">⚠</span>
                  <span v-else-if="isSubtaskDueSoon(subtask)" class="subtask-status-badge-due-soon">⏰</span>
                </div>
                <div class="subtask-owner">
                  <User class="w-3 h-3" />
                  <span>{{ formatOwner(subtask.ownerId) }}</span>
                </div>
                <!-- Subtask ownership indicators -->
                <div v-if="subtask.ownerId === currentUserId" class="subtask-ownership-badge-you">
                  👑 You
                </div>
                <div v-else-if="subtask.collaborators?.includes(currentUserId)" class="subtask-ownership-badge-collab">
                  🤝 Collab
                </div>
                <!-- Subtask recurring indicator -->
                <div v-if="subtask.scheduled" class="subtask-recurring-badge"
                  :title="`Recurring: ${formatSchedule(subtask.schedule, subtask.custom_schedule)}`">
                  🔁 {{ formatSchedule(subtask.schedule, subtask.custom_schedule) }}
                </div>
              </div>
            </div>

            <!-- Subtask Actions -->
            <div class="subtask-actions">
              <button v-if="canEditSubtask(subtask)" @click.stop="$emit('edit-subtask', subtask)"
                class="subtask-action-btn" title="Edit Subtask">
                <Edit3 class="w-3 h-3" />
              </button>

              <button v-if="canDeleteSubtask(subtask)" @click.stop="$emit('delete-subtask', subtask)"
                class="subtask-action-btn delete" title="Delete Subtask">
                <Trash2 class="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import axios from 'axios'
import { ref, computed, watch } from 'vue'
import { useToast } from 'vue-toastification'
import {
  Calendar,
  User,
  Users,
  Eye,
  Edit3,
  Plus,
  Trash2,
  ChevronDown
} from 'lucide-vue-next'

const props = defineProps({
  task: {
    type: Object,
    required: true
  },
  currentUserId: {
    type: String,
    required: true
  },
  allUsers: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  'view',
  'edit',
  'delete',
  'create-subtask',
  'view-subtask',
  'edit-subtask',
  'delete-subtask',
  'drag-start',
  'drag-end',
  'subtask-expanded'
])

// Composables
const toast = useToast()

// Reactive state
const showSubtasks = ref(false)
const isDragging = ref(false)

// Enhanced computed properties for ownership and collaboration
const isOwnedByYou = computed(() => {
  return props.task.ownerId === props.currentUserId
})

const isCollaboratedByYou = computed(() => {
  return props.task.collaborators?.includes(props.currentUserId) || false
})

const isCompleted = computed(() => {
  return props.task.status?.toLowerCase() === 'completed'
})

const isOverdue = computed(() => {
  if (!props.task.deadline) return false
  return props.task.deadline * 1000 < Date.now()
})

const isDueSoon = computed(() => {
  if (!props.task.deadline || isOverdue.value) return false
  const daysUntilDue = (props.task.deadline * 1000 - Date.now()) / (1000 * 60 * 60 * 24)
  return daysUntilDue <= 7
})

// NEW: Priority-based card color class
const getCardColorClass = () => {
  // Priority 1: Completed (Green)
  if (isCompleted.value) {
    return 'card-completed'
  }

  // Priority 2: Overdue (Red)
  if (isOverdue.value) {
    return 'card-overdue'
  }

  // Priority 3: Due Soon (Orange)
  if (isDueSoon.value) {
    return 'card-due-soon'
  }

  // Priority 4: Ownership indicators (only when no status colors apply)
  if (isOwnedByYou.value) {
    return 'card-owned-by-you'
  }

  if (isCollaboratedByYou.value) {
    return 'card-collaborated-by-you'
  }

  // Default: Others' task
  return 'card-default'
}

// NEW: Subtask color class with same priority logic
const getSubtaskColorClass = (subtask) => {
  const classes = []

  // Add status border class
  classes.push(getSubtaskStatusClass(subtask.status))

  // Priority 1: Completed
  if (subtask.status?.toLowerCase() === 'completed') {
    classes.push('subtask-completed')
    return classes.join(' ')
  }

  // Priority 2: Overdue
  const subtaskOverdue = subtask.deadline && subtask.deadline * 1000 < Date.now()
  if (subtaskOverdue) {
    classes.push('subtask-overdue')
    return classes.join(' ')
  }

  // Priority 3: Due Soon
  const daysUntilDue = subtask.deadline ? (subtask.deadline * 1000 - Date.now()) / (1000 * 60 * 60 * 24) : Infinity
  if (daysUntilDue <= 7 && daysUntilDue > 0) {
    classes.push('subtask-due-soon')
    return classes.join(' ')
  }

  // Priority 4: Ownership
  if (subtask.ownerId === props.currentUserId) {
    classes.push('subtask-owned')
  } else if (subtask.collaborators?.includes(props.currentUserId)) {
    classes.push('subtask-collaborated')
  }

  return classes.join(' ')
}

// Existing computed properties
const canEdit = computed(() => {
  return props.task.ownerId === props.currentUserId
})

const canDelete = computed(() => {
  return props.task.ownerId === props.currentUserId
})

  // Default: White background with ownership border
  if (isOwnedByYou.value) {
    return 'task-owned-by-you'
  } else if (isCollaboratedByYou.value) {
    return 'task-collaborated'
  }

  return 'task-default'
}

// NEW: Get subtask card class with same priority logic
function getSubtaskCardClass(subtask) {
  const classes = [getSubtaskStatusClass(subtask.status)]

  // Priority 1: Completed
  if (subtask.status === 'completed') {
    classes.push('subtask-completed')
  }
  // Priority 2: Overdue
  else if (isSubtaskOverdue(subtask)) {
    classes.push('subtask-overdue')
  }
  // Priority 3: Due soon
  else if (isSubtaskDueSoon(subtask)) {
    classes.push('subtask-due-soon')
  }
  // Default: White with ownership indicator
  else {
    if (subtask.ownerId === props.currentUserId) {
      classes.push('subtask-owned-by-you')
    } else if (subtask.collaborators?.includes(props.currentUserId)) {
      classes.push('subtask-collaborated')
    }
  }

const projectDisplayName = computed(() => {
  if (!props.task.projectId) {
    return 'No Project'
  }
  return projectName.value || 'Loading...'
})

watch(() => props.task.projectId, async (newProjectId) => {
  if (newProjectId) {
    try {
      if (window.cachedProjects && window.cachedProjects[newProjectId]) {
        projectName.value = window.cachedProjects[newProjectId].title
        return
      }

      const response = await axios.get(`${import.meta.env.VITE_BACKEND_API}project/indiv/${newProjectId}`)
      projectName.value = response.data.project?.title || 'Unknown Project'

      if (!window.cachedProjects) {
        window.cachedProjects = {}
      }
      window.cachedProjects[newProjectId] = { title: projectName.value }

    } catch (error) {
      console.error('Error fetching project name:', error)
      projectName.value = 'Unknown Project'
    }
  } else {
    projectName.value = ''
  }
}, { immediate: true })

watch(showSubtasks, (expanded) => {
  emit('subtask-expanded', expanded)
})

// Methods
function toggleSubtasks() {
  showSubtasks.value = !showSubtasks.value
}

function canEditSubtask(subtask) {
  return subtask.ownerId === props.currentUserId
}

function canDeleteSubtask(subtask) {
  return subtask.ownerId === props.currentUserId
}

function getPriorityClass(priority) {
  const p = priority || 5
  if (p >= 8) return 'priority-critical'
  if (p >= 6) return 'priority-high'
  if (p >= 4) return 'priority-medium'
  return 'priority-low'
}

function formatSchedule(schedule, customSchedule) {
  if (!schedule) return ''
  if (schedule === 'custom' && customSchedule) {
    return `Every ${customSchedule} days`
  }
  return schedule.charAt(0).toUpperCase() + schedule.slice(1)
}

function isSubtaskOverdue(subtask) {
  if (!subtask.deadline) return false
  return subtask.deadline * 1000 < Date.now()
}

function isSubtaskDueSoon(subtask) {
  if (!subtask.deadline || isSubtaskOverdue(subtask)) return false
  const daysUntilDue = (subtask.deadline * 1000 - Date.now()) / (1000 * 60 * 60 * 24)
  return daysUntilDue <= 7
}

function formatDeadline(deadline) {
  if (!deadline) return 'No deadline'
  const date = new Date(deadline * 1000)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
  })
}

function formatOwner(ownerId) {
  if (!ownerId) return 'Unassigned'
  if (ownerId === props.currentUserId) return 'You'

  const user = props.allUsers.find(u => u.uid === ownerId)
  if (user) {
    const displayName = user.name || user.displayName || user.email
    return displayName.length > 20 ? displayName.slice(0, 20) + '...' : displayName
  }

  return 'Unknown User'
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

function getStatusDotClass(status) {
  const classMap = {
    'unassigned': 'status-unassigned',
    'ongoing': 'status-ongoing',
    'under_review': 'status-under-review',
    'completed': 'status-completed'
  }
  return classMap[status] || 'bg-gray-400'
}

function getSubtaskStatusClass(status) {
  const classMap = {
    'unassigned': 'border-l-amber-400',
    'ongoing': 'border-l-blue-400',
    'under_review': 'border-l-purple-400',
    'completed': 'border-l-green-400'
  }
  return classMap[status] || 'border-l-gray-400'
}

function handleDragStart(event) {
  if (!isOwnedByYou.value) {
    event.preventDefault()
    toast.error('You can only move tasks that you own')
    return false
  }

  isDragging.value = true
  emit('drag-start', props.task)
  event.dataTransfer.effectAllowed = 'move'
}

function handleDragEnd() {
  isDragging.value = false
  emit('drag-end')
}
</script>

<style scoped>
/* Base task card - WHITE background */
.task-card {
  background-color: white;
  border-radius: 0.75rem;
  border: 2px solid #e5e7eb;
  padding: 1.25rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: move;
  position: relative;
  margin-bottom: 0.75rem;
}

/* ========================================
   PRIORITY-BASED CARD COLORING SYSTEM
   ======================================== */

/* Priority 1: Completed (Green) - Highest Priority */
.task-card.card-completed {
  background-color: #d1fae5;
  border: 2px solid #10b981;
}

.task-card.card-completed:hover {
  background-color: #a7f3d0;
  border-color: #059669;
  box-shadow: 0 4px 12px 0 rgba(16, 185, 129, 0.2);
}

/* Priority 2: Overdue (Red) - Second Priority */
.task-card.card-overdue {
  background-color: #fee2e2;
  border: 2px solid #dc2626;
}

.task-card.card-overdue:hover {
  background-color: #fecaca;
  border-color: #b91c1c;
  box-shadow: 0 4px 12px 0 rgba(220, 38, 38, 0.2);
}

/* Priority 3: Due Soon (Orange) - Third Priority */
.task-card.card-due-soon {
  background-color: #fef3c7;
  border: 2px solid #f59e0b;
}

.task-card.card-due-soon:hover {
  background-color: #fde68a;
  border-color: #d97706;
  box-shadow: 0 4px 12px 0 rgba(245, 158, 11, 0.2);
}

/* Priority 4a: You Own This (Blue Left Border) - Fourth Priority */
.task-card.card-owned-by-you {
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-left: 5px solid #3b82f6;
}

.task-card.card-owned-by-you:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
  border-left-color: #2563eb;
  box-shadow: 0 4px 12px 0 rgba(59, 130, 246, 0.15);
}

/* Priority 4b: Collaborating (Gray Left Border) */
.task-card.card-collaborated-by-you {
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-left: 3px solid #9ca3af;
}

.task-card.card-collaborated-by-you:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
  border-left-color: #6b7280;
  box-shadow: 0 4px 12px 0 rgba(156, 163, 175, 0.15);
}

/* Priority 4c: Default (Others' Task) - Lowest Priority */
.task-card.card-default {
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
}

.task-card.card-default:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px 0 rgba(156, 163, 175, 0.1);
}

/* Dragging state */
.task-card:active {
  cursor: grabbing;
}

.task-card.dragging {
  opacity: 0.6;
  transform: rotate(2deg);
  cursor: grabbing;
  z-index: 1000;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

/* ========================================
   SUBTASK PRIORITY-BASED COLORING
   ======================================== */

.subtask-item {
  background-color: #f8fafc;
  border-radius: 0.5rem;
  padding: 0.875rem;
  border-left: 4px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #e2e8f0;
}

/* Priority 1: Completed Subtask (Green) */
.subtask-item.subtask-completed {
  background-color: #d1fae5;
  border: 1px solid #10b981;
  border-left: 4px solid #10b981;
}

.subtask-item.subtask-completed:hover {
  background-color: #a7f3d0;
  border-color: #059669;
}

/* Priority 2: Overdue Subtask (Red) */
.subtask-item.subtask-overdue {
  background-color: #fee2e2;
  border: 1px solid #dc2626;
  border-left: 4px solid #dc2626;
}

.subtask-item.subtask-overdue:hover {
  background-color: #fecaca;
  border-color: #b91c1c;
}

.subtask-item.subtask-overdue .subtask-title {
  color: #7f1d1d;
  font-weight: 600;
}

/* Priority 3: Due Soon Subtask (Orange) */
.subtask-item.subtask-due-soon {
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  border-left: 4px solid #f59e0b;
}

.subtask-item.subtask-due-soon:hover {
  background-color: #fde68a;
  border-color: #d97706;
}

/* Priority 4a: You Own This Subtask (Blue Left Border) */
.subtask-item.subtask-owned {
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #3b82f6;
}

.subtask-item.subtask-owned:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
  border-left-color: #2563eb;
}

/* Priority 4b: Collaborating Subtask (Gray Left Border) */
.subtask-item.subtask-collaborated {
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #9ca3af;
}

.subtask-item.subtask-collaborated:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

/* Default subtask hover */
.subtask-item:hover {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
}

/* ========================================
   REST OF THE STYLES (UNCHANGED)
   ======================================== */

.task-card:hover {
  cursor: grab;
}

.task-content {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.task-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.task-title-section {
  flex: 1;
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.task-title {
  font-weight: 600;
  color: #111827;
  font-size: 0.95rem;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.priority-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
  border: 2px solid;
}

.priority-icon {
  font-size: 0.875rem;
}

.priority-value {
  font-size: 0.75rem;
}

.priority-critical {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
  border-color: #dc2626;
}

.priority-high {
  background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%);
  color: #9a3412;
  border-color: #f97316;
}

.priority-medium {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  border-color: #f59e0b;
}

.priority-low {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1e40af;
  border-color: #3b82f6;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.project-badge {
  background-color: #e0f2fe;
  color: #0369a1;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.ownership-indicator {
  background-color: #fef3c7;
  color: #92400e;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 500;
  border: 1px solid #fbbf24;
}

.collaborator-indicator {
  background-color: #ede9fe;
  color: #6b21a8;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-weight: 600;
  border: 1px solid #dc2626;
}

.recurring-indicator {
  background-color: #e0e7ff;
  color: #4338ca;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.65rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.expand-button {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem;
  color: #6b7280;
  border-radius: 0.375rem;
  transition: all 0.2s ease;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
}

.expand-button:hover {
  color: #374151;
  background-color: #f1f5f9;
  border-color: #cbd5e1;
}

.expand-button.expanded {
  color: #2563eb;
  background-color: #eff6ff;
  border-color: #bfdbfe;
}

.expand-button.expanded .w-4 {
  transform: rotate(180deg);
}

.subtask-count {
  font-size: 0.75rem;
  font-weight: 600;
  min-width: 16px;
  text-align: center;
}

.deadline-section,
.owner-section,
.collaborators-section {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 0.875rem;
  color: #4b5563;
}

.deadline-text,
.owner-text,
.collaborators-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.overdue-badge {
  font-size: 0.75rem;
  background-color: #fee2e2;
  color: #b91c1c;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-weight: 600;
}

.due-soon-badge {
  font-size: 0.75rem;
  background-color: #fef3c7;
  color: #d97706;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f1f5f9;
}

.action-btn {
  padding: 0.5rem;
  color: #64748b;
  border-radius: 0.375rem;
  transition: all 0.2s ease;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
}

.action-btn:hover {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
}

.action-btn.view-btn:hover {
  color: #2563eb;
  background-color: #eff6ff;
  border-color: #bfdbfe;
}

.action-btn.edit-btn:hover {
  color: #16a34a;
  background-color: #f0fdf4;
  border-color: #bbf7d0;
}

.action-btn.add-btn:hover {
  color: #9333ea;
  background-color: #faf5ff;
  border-color: #e9d5ff;
}

.action-btn.delete-btn:hover {
  color: #dc2626;
  background-color: #fef2f2;
  border-color: #fecaca;
}

.subtasks-container {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f1f5f9;
}

.subtasks-header {
  margin-bottom: 0.75rem;
}

.subtasks-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.subtasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.subtask-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.subtask-priority-badge {
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  font-size: 0.65rem;
  font-weight: 700;
  flex-shrink: 0;
  border: 1.5px solid;
}

.subtask-recurring-badge {
  font-size: 0.65rem;
  background-color: #e0e7ff;
  color: #4338ca;
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  font-weight: 600;
}

.subtask-content {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.subtask-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.subtask-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
  flex: 1;
  line-height: 1.3;
}

.subtask-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex-shrink: 0;
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
}

.status-unassigned .status-dot {
  background-color: #f59e0b;
}

.status-ongoing .status-dot {
  background-color: #3b82f6;
}

.status-under-review .status-dot {
  background-color: #8b5cf6;
}

.status-completed .status-dot {
  background-color: #10b981;
}

.status-text {
  font-size: 0.75rem;
  color: #4b5563;
  font-weight: 500;
}

.subtask-meta {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  font-size: 0.75rem;
  color: #6b7280;
  flex-wrap: wrap;
}

.subtask-deadline,
.subtask-owner {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.subtask-overdue-badge {
  font-size: 0.65rem;
  background-color: #fee2e2;
  color: #b91c1c;
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  font-weight: 600;
  margin-left: 0.375rem;
}

.subtask-due-soon-badge {
  font-size: 0.65rem;
  background-color: #fef3c7;
  color: #d97706;
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  font-weight: 600;
  margin-left: 0.375rem;
}

.subtask-ownership-badge,
.subtask-collaboration-badge {
  font-size: 0.65rem;
  padding: 0.125rem 0.375rem;
  border-radius: 8px;
  font-weight: 700;
  background-color: #dbeafe;
  color: #1e40af;
  border: 1px solid #3b82f6;
}

.subtask-ownership-badge {
  background-color: #fef3c7;
  color: #92400e;
}

.subtask-collaboration-badge {
  background-color: #ede9fe;
  color: #6b21a8;
}

.subtask-actions {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin-top: 0.625rem;
  padding-top: 0.625rem;
  border-top: 1px solid #e5e7eb;
}

.subtask-action-btn {
  padding: 0.375rem;
  color: #64748b;
  border-radius: 0.25rem;
  transition: all 0.2s ease;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
}

.subtask-action-btn:hover {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
}

.subtask-action-btn.delete:hover {
  color: #dc2626;
  background-color: #fef2f2;
  border-color: #fecaca;
}

/* Animations */
.subtasks-enter-active,
.subtasks-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.subtasks-enter-from,
.subtasks-leave-to {
  opacity: 0;
  transform: translateY(-10px);
  max-height: 0;
}

.subtasks-enter-to,
.subtasks-leave-from {
  opacity: 1;
  transform: translateY(0);
  max-height: 500px;
}

/* Responsive */
@media (max-width: 640px) {
  .task-card {
    padding: 1rem;
  }

  .task-title {
    font-size: 0.875rem;
  }

  .deadline-section,
  .owner-section,
  .collaborators-section {
    font-size: 0.8125rem;
  }

  .action-buttons {
    flex-wrap: wrap;
  }

  .action-btn {
    padding: 0.375rem;
  }
}

/* Enhanced cursor visibility */
.task-card * {
  cursor: inherit;
}

.action-btn,
.expand-button,
.subtask-item,
.subtask-action-btn {
  cursor: pointer !important;
}
</style>
