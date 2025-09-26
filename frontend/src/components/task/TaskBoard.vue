<template>
  <div class="task-board">
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        <span class="text-gray-600">Loading tasks...</span>
      </div>
    </div>

    <!-- Board Columns -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
      <div v-for="status in statusColumns" :key="status.key" class="board-column" :class="status.bgClass"
        @drop="handleDrop($event, status.key)" @dragover="handleDragOver" @dragenter="handleDragEnter"
        @dragleave="handleDragLeave">
        <!-- Column Header -->
        <div class="column-header" :class="status.headerClass">
          <div class="flex items-center gap-3">
            <div class="w-3 h-3 rounded-full" :class="status.dotClass"></div>
            <h3 class="font-semibold text-sm uppercase tracking-wider">{{ status.title }}</h3>
          </div>
          <div class="task-count" :class="status.countClass">
            {{ getTasksByStatus(status.key).length }}
          </div>
        </div>

        <!-- Tasks Container -->
        <div class="tasks-container">
          <div v-if="getTasksByStatus(status.key).length === 0" class="empty-state">
            <div class="empty-icon" :class="status.emptyIconClass">
              <component :is="status.emptyIcon" class="w-8 h-8" />
            </div>
            <p class="text-sm text-gray-500 text-center mt-2">No {{ status.title.toLowerCase() }} tasks</p>
          </div>

          <TaskCard v-for="task in getTasksByStatus(status.key)" :key="task.taskId" :task="task"
            :current-user-id="currentUserId" :all-users="allUsers" @view="$emit('view-task', task)"
            @edit="$emit('edit-task', task)" @delete="$emit('delete-task', task)"
            @create-subtask="$emit('create-subtask', task.taskId)" @view-subtask="$emit('view-subtask', $event)"
            @edit-subtask="$emit('edit-subtask', $event)" @delete-subtask="$emit('delete-subtask', $event)"
            @drag-start="handleDragStart" @drag-end="handleDragEnd" @subtask-expanded="handleSubtaskExpanded" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import TaskCard from './TaskCard.vue'
import {
  Clock,
  CheckCircle,
  PlayCircle,
  Eye
} from 'lucide-vue-next'

const props = defineProps({
  tasks: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  allUsers: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  'task-moved',
  'view-task',
  'edit-task',
  'delete-task',
  'create-subtask',
  'view-subtask',
  'edit-subtask',
  'delete-subtask',
  'subtask-expanded' // NEW: Forward subtask expansion event
])

const authStore = useAuthStore()
const currentUserId = computed(() => authStore.user?.uid)

// Drag and drop state
const draggedTask = ref(null)
const dragOverColumn = ref(null)

// Status columns configuration
const statusColumns = [
  {
    key: 'unassigned',
    title: 'Unassigned',
    bgClass: 'bg-amber-50/80 border-amber-200',
    headerClass: 'text-amber-800 bg-amber-100/80',
    dotClass: 'bg-amber-500',
    countClass: 'bg-amber-200 text-amber-800',
    emptyIcon: Clock,
    emptyIconClass: 'text-amber-400'
  },
  {
    key: 'ongoing',
    title: 'Ongoing',
    bgClass: 'bg-blue-50/80 border-blue-200',
    headerClass: 'text-blue-800 bg-blue-100/80',
    dotClass: 'bg-blue-500',
    countClass: 'bg-blue-200 text-blue-800',
    emptyIcon: PlayCircle,
    emptyIconClass: 'text-blue-400'
  },
  {
    key: 'under_review',
    title: 'Under Review',
    bgClass: 'bg-purple-50/80 border-purple-200',
    headerClass: 'text-purple-800 bg-purple-100/80',
    dotClass: 'bg-purple-500',
    countClass: 'bg-purple-200 text-purple-800',
    emptyIcon: Eye,
    emptyIconClass: 'text-purple-400'
  },
  {
    key: 'completed',
    title: 'Completed',
    bgClass: 'bg-green-50/80 border-green-200',
    headerClass: 'text-green-800 bg-green-100/80',
    dotClass: 'bg-green-500',
    countClass: 'bg-green-200 text-green-800',
    emptyIcon: CheckCircle,
    emptyIconClass: 'text-green-400'
  }
]

// Computed properties
function getTasksByStatus(status) {
  return props.tasks.filter(task => task.status === status)
}

// NEW: Handle subtask expansion state from TaskCard
function handleSubtaskExpanded(expanded) {
  emit('subtask-expanded', expanded)
}

// Drag and drop handlers
function handleDragStart(task) {
  draggedTask.value = task
}

function handleDragEnd() {
  draggedTask.value = null
  dragOverColumn.value = null
  // Remove drag-over class from all columns
  document.querySelectorAll('.board-column').forEach(col => {
    col.classList.remove('drag-over')
  })
}

function handleDragOver(event) {
  event.preventDefault()
}

function handleDragEnter(event) {
  event.preventDefault()
  const column = event.currentTarget

  // Remove drag-over from all columns first
  document.querySelectorAll('.board-column').forEach(col => {
    col.classList.remove('drag-over')
  })

  // Add to current column
  dragOverColumn.value = column
  column.classList.add('drag-over')
}

function handleDragLeave(event) {
  const column = event.currentTarget
  const rect = column.getBoundingClientRect()
  const x = event.clientX
  const y = event.clientY

  // Only remove drag-over class if truly leaving the column
  if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
    column.classList.remove('drag-over')
    if (dragOverColumn.value === column) {
      dragOverColumn.value = null
    }
  }
}

function handleDrop(event, newStatus) {
  event.preventDefault()
  const column = event.currentTarget
  column.classList.remove('drag-over')

  if (!draggedTask.value) return

  const task = draggedTask.value
  const oldStatus = task.status

  // Don't move if dropping on same status
  if (oldStatus === newStatus) {
    draggedTask.value = null
    return
  }

  // Emit the task move event - let parent handle validation and confirmation
  emit('task-moved', task.taskId, newStatus, oldStatus)
  draggedTask.value = null
}
</script>

<style scoped>
.task-board {
  height: calc(100vh - 200px);
  min-height: 600px;
}

.board-column {
  background-color: white;
  border-radius: 0.75rem;
  border: 2px dashed #e5e7eb;
  padding: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.board-column.drag-over {
  border-style: solid;
  border-color: #3b82f6;
  background-color: rgba(239, 246, 255, 0.7);
  transform: scale(1.02);
  box-shadow: 0 12px 32px rgba(59, 130, 246, 0.2);
}

.board-column::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent 49%, rgba(59, 130, 246, 0.05) 50%, transparent 51%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  border-radius: inherit;
}

.board-column.drag-over::before {
  opacity: 1;
}

.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  backdrop-filter: blur(4px);
  flex-shrink: 0;
}

.task-count {
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  min-width: 28px;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.task-count:hover {
  transform: scale(1.1);
}

.tasks-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  /* Remove gap since TaskCard now has margin-bottom */
  padding-right: 4px;
  /* Space for scrollbar */
  /* Custom scrollbar */
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 transparent;
}

.tasks-container::-webkit-scrollbar {
  width: 6px;
}

.tasks-container::-webkit-scrollbar-track {
  background: transparent;
}

.tasks-container::-webkit-scrollbar-thumb {
  background-color: #cbd5e0;
  border-radius: 3px;
}

.tasks-container::-webkit-scrollbar-thumb:hover {
  background-color: #a0aec0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 0;
  min-height: 200px;
}

.empty-icon {
  padding: 1rem;
  border-radius: 50%;
  background-color: #f8fafc;
  margin-bottom: 0.5rem;
}

/* Responsive adjustments */
@media (max-width: 1023px) {
  .task-board {
    height: auto;
    min-height: auto;
  }

  .board-column {
    height: auto;
    min-height: 400px;
  }

  .tasks-container {
    max-height: 400px;
  }
}

/* Enhanced drag feedback */
.board-column {
  will-change: transform, box-shadow;
}

.board-column.drag-over {
  animation: dragPulse 1.5s ease-in-out infinite;
}

@keyframes dragPulse {

  0%,
  100% {
    box-shadow: 0 12px 32px rgba(59, 130, 246, 0.2);
  }

  50% {
    box-shadow: 0 16px 40px rgba(59, 130, 246, 0.3);
  }
}
</style>
