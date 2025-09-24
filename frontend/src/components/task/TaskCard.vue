<template>
  <div class="task-card" :class="[
    deadlineClass,
    { 'dragging': isDragging }
  ]" draggable="true" @dragstart="handleDragStart" @dragend="handleDragEnd">
    <!-- Main Task Content -->
    <div class="task-content">
      <!-- Task Header -->
      <div class="task-header">
        <div class="task-title-section">
          <h4 class="task-title" :title="task.title">{{ task.title }}</h4>
          <div class="task-meta">
            <span v-if="task.projectId" class="project-badge">{{ projectName }}</span>
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
        <span class="deadline-text">{{ formatDeadline(task.deadline) }}</span>
        <span v-if="isOverdue" class="overdue-badge">Overdue</span>
        <span v-else-if="isDueSoon" class="due-soon-badge">Due Soon</span>
      </div>

      <!-- Owner -->
      <div class="owner-section">
        <User class="w-4 h-4" />
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

        <button @click="$emit('create-subtask', task.taskId)" class="action-btn add-btn" title="Add Subtask">
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
            :class="getSubtaskStatusClass(subtask.status)" @click="$emit('view-subtask', subtask)">
            <div class="subtask-content">
              <div class="subtask-header">
                <span class="subtask-title">{{ subtask.title }}</span>
                <div class="subtask-status">
                  <div class="status-dot" :class="getStatusDotClass(subtask.status)"></div>
                  <span class="status-text">{{ formatStatus(subtask.status) }}</span>
                </div>
              </div>

              <div class="subtask-meta">
                <div class="subtask-deadline">
                  <Calendar class="w-3 h-3" />
                  <span>{{ formatDeadline(subtask.deadline) }}</span>
                </div>
                <div class="subtask-owner">
                  <User class="w-3 h-3" />
                  <span>{{ formatOwner(subtask.ownerId) }}</span>
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
  'drag-end'
])

// Reactive state
const showSubtasks = ref(false)
const isDragging = ref(false)

// Computed properties
const canEdit = computed(() => {
  return props.task.ownerId === props.currentUserId
})

const canDelete = computed(() => {
  return props.task.ownerId === props.currentUserId
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

const deadlineClass = computed(() => {
  if (isOverdue.value) return 'overdue'
  if (isDueSoon.value) return 'due-soon'
  return ''
})
const projectName = ref('')

watch(() => props.task.projectId, async (newProjectId) => {
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
}, { immediate: true }) // triggers watcher immediately on setup

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

  // Find user in allUsers array
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
    'unassigned': 'bg-amber-400',
    'ongoing': 'bg-blue-400',
    'under_review': 'bg-purple-400',
    'completed': 'bg-green-400'
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
.task-card {
  background-color: white;
  border-radius: 0.75rem;
  border: 1px solid #e5e7eb;
  padding: 1.25rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: move;
  /* More visible cursor */
  position: relative;
  /* Prevent the card from jumping by using margin instead of transform */
  margin-bottom: 0.75rem;
}

.task-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px 0 rgba(59, 130, 246, 0.15);
  /* Use box-shadow instead of transform to prevent jumping */
  background-color: #fafbff;
  cursor: grab;
  /* Even more visible grab cursor */
}

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

.task-card.overdue {
  border-color: #fca5a5;
  background-color: rgba(254, 242, 242, 0.5);
}

.task-card.due-soon {
  border-color: #fcd34d;
  background-color: rgba(255, 251, 235, 0.5);
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

.task-title {
  font-weight: 600;
  color: #111827;
  font-size: 0.95rem;
  line-height: 1.3;
  margin-bottom: 0.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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

/* Subtasks */
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

.subtask-item {
  background-color: #f8fafc;
  border-radius: 0.5rem;
  padding: 0.875rem;
  border-left: 4px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #e2e8f0;
}

.subtask-item:hover {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
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
}

.subtask-deadline,
.subtask-owner {
  display: flex;
  align-items: center;
  gap: 0.375rem;
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
