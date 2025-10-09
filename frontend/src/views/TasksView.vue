<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
    <NavigationBar />
    <!-- Header Section -->
    <div class="bg-white/70 backdrop-blur-sm border-b border-gray-200/50 top-0">
      <div class="max-w-full px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">Task Board</h1>
            <p class="text-sm text-gray-600 mt-1">Manage and track your tasks and subtasks</p>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <!-- Auto Refresh Indicator -->
            <div v-if="!autoRefreshPaused"
              class="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 rounded-lg text-xs font-medium">
              <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              Auto-refresh {{ autoRefreshCountdown }}s
            </div>
            <div v-else
              class="flex items-center gap-2 px-3 py-1.5 bg-amber-50 text-amber-700 rounded-lg text-xs font-medium">
              <div class="w-2 h-2 bg-amber-500 rounded-full"></div>
              Auto-refresh paused
            </div>

            <!-- Refresh Button -->
            <button @click="manualRefresh" :disabled="loading"
              class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-all shadow-sm">
              <RefreshCw :class="['w-4 h-4', { 'animate-spin': loading }]" />
              <span class="hidden sm:inline">Refresh</span>
            </button>

            <!-- Filter Button -->
            <button @click="toggleFilters"
              class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-all shadow-sm"
              :class="{ 'bg-blue-50 border-blue-300 text-blue-700': hasActiveFilters }">
              <Filter class="w-4 h-4" />
              <span class="hidden sm:inline">Filter</span>
              <span v-if="hasActiveFilters" class="w-2 h-2 bg-blue-500 rounded-full"></span>
            </button>

            <!-- Create Task Button -->
            <button @click="openCreateTaskModal"
              class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl">
              <Plus class="w-4 h-4" />
              <span class="hidden sm:inline">Create Task</span>
            </button>
          </div>
        </div>

        <!-- Filter Section -->
        <transition name="slide-down">
          <div v-if="showFilters" class="mt-4 p-4 bg-gray-50 rounded-lg border relative">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Search</label>
                <input v-model="filters.search" type="text" placeholder="Search by title, owner..."
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Project</label>
                <select v-model="filters.project" :disabled="loadingProjects"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                  <option value="">All Projects</option>
                  <option value="no-project">📁 No Project</option>
                  <option v-for="project in projects" :key="project.projectId" :value="project.projectId">
                    {{ project.title }}
                  </option>
                </select>
                <div v-if="loadingProjects" class="text-xs text-gray-500 mt-1">Loading projects...</div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
                <select v-model="filters.sortBy"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">

                  <option value="createdAt">Creation Date</option>
                  <option value="priority">Priority (High to Low)</option>
                  <option value="deadline">Deadline</option>
                  <option value="title">Title</option>
                </select>
              </div>
            </div>

            <div class="flex justify-end gap-2 mt-4">
              <button @click="clearFilters" class="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800">
                Clear All
              </button>
              <button @click="closeFilters" class="px-3 py-1.5 text-sm bg-gray-200 hover:bg-gray-300 rounded">
                Close
              </button>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- Task Board -->
    <div class="max-w-full px-4 sm:px-6 lg:px-8 py-6">
      <TaskBoard :tasks="filteredTasks" :loading="loading" :all-users="allUsers" @task-moved="handleTaskMoved"
        @view-task="handleViewTask" @edit-task="handleEditTask" @delete-task="handleDeleteTask"
        @create-subtask="handleCreateSubtask" @view-subtask="handleViewSubtask" @edit-subtask="handleEditSubtask"
        @delete-subtask="handleDeleteSubtask" @subtask-expanded="handleSubtaskExpanded" />
    </div>

    <!-- Modals -->
    <TaskCreateEditModal :show="showCreateEditModal" :task-data="selectedTask" :is-editing="isEditing"
      :is-subtask="isSubtask" :parent-task-id="parentTaskId" :parent-task="parentTask" :all-users="allUsers"
      @close="closeCreateEditModal" @save="handleSaveTask" />

    <TaskDetailModal :show="showDetailModal" :task-data="selectedTask" :is-subtask="isSubtask" :all-users="allUsers"
      @close="closeDetailModal" @edit="handleEditFromDetail" @delete="handleDeleteFromDetail"
      @view-subtask="handleViewSubtask" />

    <!-- Confirmation Modal -->
    <ConfirmationModal :show="showConfirmModal" :title="confirmModal.title" :description="confirmModal.description"
      :warning-text="confirmModal.warningText" :confirm-text="confirmModal.confirmText" :variant="confirmModal.variant"
      :loading="confirmModal.loading" @confirm="confirmModal.onConfirm" @cancel="closeConfirmModal" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useToast } from 'vue-toastification'
import { useAuthStore } from '@/stores/auth'
import { usersService } from '@/services/users'
import axios from 'axios'
import NavigationBar from '@/components/NavigationBar.vue'
import TaskBoard from '@/components/task/TaskBoard.vue'
import TaskCreateEditModal from '@/components/task/TaskCreateEditModal.vue'
import TaskDetailModal from '@/components/task/TaskDetailModal.vue'
import ConfirmationModal from '@/components/ConfirmationModal.vue'
import { RefreshCw, Filter, Plus } from 'lucide-vue-next'

// Composables
const toast = useToast()
const authStore = useAuthStore()

// Reactive data
const loading = ref(false)
const tasks = ref([])
const subtasks = ref([])
const allUsers = ref([])

// Filter state
const showFilters = ref(false)
const filters = ref({
  search: '',
  project: '',
  sortBy: 'createdAt' // Default sort by creation date
})

// Modal state
const showCreateEditModal = ref(false)
const showDetailModal = ref(false)
const showConfirmModal = ref(false)
const selectedTask = ref(null)
const isEditing = ref(false)
const isSubtask = ref(false)
const parentTaskId = ref(null)
const parentTask = ref(null)

// Auto refresh state
const autoRefreshInterval = ref(null)
const autoRefreshCountdown = ref(30)
const autoRefreshCountdownInterval = ref(null)
const autoRefreshPaused = ref(false)
const lastRefreshTime = ref(Date.now())
const isManualRefresh = ref(false)
const subtasksExpanded = ref(false) // NEW: Track subtask expansion state

//project loading
const projects = ref([])
const loadingProjects = ref(false)

// Confirmation modal state
const confirmModal = ref({
  title: '',
  description: '',
  warningText: '',
  confirmText: 'Confirm',
  variant: 'danger',
  loading: false,
  onConfirm: () => { }
})

// Computed properties
const hasActiveFilters = computed(() => {
  return filters.value.search || filters.value.project
})

const anyModalOpen = computed(() => {
  return showCreateEditModal.value || showDetailModal.value || showConfirmModal.value || showFilters.value || subtasksExpanded.value // NEW: Include subtask expansion
})

const filteredTasks = computed(() => {
  let filtered = [...tasks.value]

  // Search filter
  if (filters.value.search) {
    const searchTerm = filters.value.search.toLowerCase()
    filtered = filtered.filter(task =>
      task.title?.toLowerCase().includes(searchTerm) ||
      getUserDisplayName(task.ownerId)?.toLowerCase().includes(searchTerm) ||
      task.projectId?.toLowerCase().includes(searchTerm)
    )
  }

  // Project filter
  if (filters.value.project) {
    if (filters.value.project === 'no-project') {
      filtered = filtered.filter(task => !task.projectId || task.projectId.trim() === '')
    } else {
      filtered = filtered.filter(task => task.projectId === filters.value.project)
    }
  }

  // Sort
  const sortBy = filters.value.sortBy
  filtered.sort((a, b) => {
    if (sortBy === 'priority') {
      // Sort by priority (highest first), then by creation date for ties
      const priorityDiff = (b.priority || 5) - (a.priority || 5)
      if (priorityDiff !== 0) return priorityDiff
      return b.createdAt - a.createdAt
    } else if (sortBy === 'deadline') {
      // Sort by deadline (earliest first)
      return (a.deadline || Infinity) - (b.deadline || Infinity)
    } else if (sortBy === 'title') {
      // Sort alphabetically by title
      return (a.title || '').localeCompare(b.title || '')
    } else {
      // Default: sort by creation date (newest first)
      return b.createdAt - a.createdAt
    }
  })

  return filtered
})


// API functions
async function fetchTasks() {
  try {
    console.log('Fetching tasks from:', `${import.meta.env.VITE_BACKEND_API}tasks`)
    const response = await axios.get(`${import.meta.env.VITE_BACKEND_API}tasks`)
    const data = response.data

    const currentUserId = authStore.user?.uid
    const currentUserRole = authStore.user?.role

    // Get all tasks first
    let allTasks = data.tasks || []

    // STAFF: Can only view tasks they own or collaborate in
    if (currentUserRole === 'staff') {
      tasks.value = allTasks.filter(task => {
        return task.ownerId === currentUserId ||
          task.collaborators?.includes(currentUserId) ||
          task.creatorId === currentUserId
      })
      console.log(`[STAFF] Loaded ${tasks.value.length} tasks for user ${currentUserId}`)
      return
    }

    // MANAGER/DIRECTOR: Can view tasks they own/collaborate in + tasks from their projects
    if (currentUserRole === 'manager' || currentUserRole === 'director') {
      // Get user's project IDs (projects they own or collaborate in)
      const userProjectIds = new Set()

      if (projects.value && projects.value.length > 0) {
        projects.value.forEach(project => {
          if (project.ownerId === currentUserId ||
            project.collaborators?.includes(currentUserId)) {
            userProjectIds.add(project.projectId)
          }
        })
      }

      console.log(`[${currentUserRole.toUpperCase()}] User's project IDs:`, Array.from(userProjectIds))

      tasks.value = allTasks.filter(task => {
        // Include if user is directly involved
        const isDirectlyInvolved = task.ownerId === currentUserId ||
          task.collaborators?.includes(currentUserId) ||
          task.creatorId === currentUserId

        // Include if task belongs to user's project
        const isInUserProject = task.projectId && userProjectIds.has(task.projectId)

        return isDirectlyInvolved || isInUserProject
      })

      console.log(`[${currentUserRole.toUpperCase()}] Loaded ${tasks.value.length} tasks for user ${currentUserId}`)
      return
    }

    // Fallback: if role is not recognized, show only directly involved tasks
    tasks.value = allTasks.filter(task => {
      return task.ownerId === currentUserId ||
        task.collaborators?.includes(currentUserId) ||
        task.creatorId === currentUserId
    })

    console.log(`[FALLBACK] Loaded ${tasks.value.length} tasks for user ${currentUserId}`)

  } catch (error) {
    console.error('Error fetching tasks:', error.response?.status, error.response?.data)
    if (error.response?.status === 404) {
      if (isManualRefresh.value) {
        toast.error('Tasks API not found. Please check if the backend services are running.')
      }
    } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      if (isManualRefresh.value) {
        toast.error('Cannot connect to backend. Please ensure services are running.')
      }
    } else {
      if (isManualRefresh.value) {
        toast.error('Failed to load tasks')
      }
    }
    throw error
  }
}



function openCreateTaskModal() {
  selectedTask.value = null
  isEditing.value = false
  isSubtask.value = false
  parentTaskId.value = null
  showCreateEditModal.value = true

  // If we have a selected project from navigation, pre-fill it
  if (window.selectedProjectForFilter) {
    // You'll need to modify TaskCreateEditModal to accept initial project selection
    // Pass the project ID as a prop or emit an event to set the initial project
  }
}
// Also update fetchSubtasks with the same logic
async function fetchSubtasks() {
  try {
    console.log('Fetching subtasks from:', `${import.meta.env.VITE_BACKEND_API}subtasks`)
    const response = await axios.get(`${import.meta.env.VITE_BACKEND_API}subtasks`)
    const data = response.data

    const currentUserId = authStore.user?.uid
    const currentUserRole = authStore.user?.role

    // Get all subtasks first
    let allSubtasks = data.subtasks || []

    // STAFF: Can only view subtasks they own or collaborate in
    if (currentUserRole === 'staff') {
      subtasks.value = allSubtasks.filter(subtask => {
        return subtask.ownerId === currentUserId ||
          subtask.collaborators?.includes(currentUserId) ||
          subtask.creatorId === currentUserId
      })
      console.log(`[STAFF] Loaded ${subtasks.value.length} subtasks for user ${currentUserId}`)
      return
    }

    // MANAGER/DIRECTOR: Can view subtasks they own/collaborate in + subtasks from their project tasks
    if (currentUserRole === 'manager' || currentUserRole === 'director') {
      // Get user's project IDs (projects they own or collaborate in)
      const userProjectIds = new Set()

      if (projects.value && projects.value.length > 0) {
        projects.value.forEach(project => {
          if (project.ownerId === currentUserId ||
            project.collaborators?.includes(currentUserId)) {
            userProjectIds.add(project.projectId)
          }
        })
      }

      // Get task IDs that belong to user's projects
      const projectTaskIds = new Set()
      if (tasks.value && tasks.value.length > 0) {
        tasks.value.forEach(task => {
          if (task.projectId && userProjectIds.has(task.projectId)) {
            projectTaskIds.add(task.taskId)
          }
        })
      }

      console.log(`[${currentUserRole.toUpperCase()}] Project task IDs:`, Array.from(projectTaskIds))

      subtasks.value = allSubtasks.filter(subtask => {
        // Include if user is directly involved
        const isDirectlyInvolved = subtask.ownerId === currentUserId ||
          subtask.collaborators?.includes(currentUserId) ||
          subtask.creatorId === currentUserId

        // Include if subtask belongs to a task in user's project
        const isInProjectTask = subtask.taskId && projectTaskIds.has(subtask.taskId)

        return isDirectlyInvolved || isInProjectTask
      })

      console.log(`[${currentUserRole.toUpperCase()}] Loaded ${subtasks.value.length} subtasks for user ${currentUserId}`)
      return
    }

    // Fallback: if role is not recognized, show only directly involved subtasks
    subtasks.value = allSubtasks.filter(subtask => {
      return subtask.ownerId === currentUserId ||
        subtask.collaborators?.includes(currentUserId) ||
        subtask.creatorId === currentUserId
    })

    console.log(`[FALLBACK] Loaded ${subtasks.value.length} subtasks for user ${currentUserId}`)

  } catch (error) {
    console.error('Error fetching subtasks:', error.response?.status, error.response?.data)
    if (error.response?.status === 404) {
      if (isManualRefresh.value) {
        toast.error('Subtasks API not found. Please check if the backend services are running.')
      }
    } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      if (isManualRefresh.value) {
        toast.error('Cannot connect to backend. Please ensure services are running.')
      }
    } else {
      if (isManualRefresh.value) {
        toast.error('Failed to load subtasks')
      }
    }
    throw error
  }
}

// Associate subtasks with tasks after both are loaded
function associateSubtasksWithTasks() {
  tasks.value.forEach(task => {
    task.subtasks = subtasks.value.filter(subtask => subtask.taskId === task.taskId)
  })
  console.log('Associated subtasks with tasks')
}

async function fetchUsers() {
  try {
    const users = await usersService.getAllUsers()
    allUsers.value = users
    console.log(`Loaded ${allUsers.value.length} users`)
  } catch (error) {
    console.error('Error fetching users:', error)
  }
}

async function refreshTasks() {
  loading.value = true
  try {
    await fetchTasks()
    await fetchSubtasks()
    associateSubtasksWithTasks()
    lastRefreshTime.value = Date.now()

    // Only show success message on manual refresh
    if (isManualRefresh.value) {
      toast.success('Tasks refreshed successfully')
      isManualRefresh.value = false
    }
  } catch (error) {
    console.log(error)
    if (isManualRefresh.value) {
      toast.error('Failed to refresh tasks')
      isManualRefresh.value = false
    }
  } finally {
    loading.value = false
  }
}

async function manualRefresh() {
  isManualRefresh.value = true
  await refreshTasks()
}

// NEW: Handle subtask expansion state
function handleSubtaskExpanded(expanded) {
  subtasksExpanded.value = expanded
}


function closeCreateEditModal() {
  showCreateEditModal.value = false
  selectedTask.value = null
  isEditing.value = false
  isSubtask.value = false
  parentTaskId.value = null
  parentTask.value = null // NEW: Clear parent task reference
}

function closeDetailModal() {
  showDetailModal.value = false
  selectedTask.value = null
  isSubtask.value = false
}

function closeConfirmModal() {
  showConfirmModal.value = false
  confirmModal.value = {
    title: '',
    description: '',
    warningText: '',
    confirmText: 'Confirm',
    variant: 'danger',
    loading: false,
    onConfirm: () => { }
  }
}

function toggleFilters() {
  showFilters.value = !showFilters.value
}

function closeFilters() {
  showFilters.value = false
}

// Task handlers
function handleViewTask(task) {
  selectedTask.value = task
  isSubtask.value = false
  showDetailModal.value = true
}

function handleEditTask(task) {
  selectedTask.value = task
  isEditing.value = true
  isSubtask.value = false
  showCreateEditModal.value = true
}

function handleDeleteTask(task) {
  confirmModal.value = {
    title: 'Delete Task',
    description: `Are you sure you want to delete "${task.title}"?`,
    warningText: task.subtasks?.length > 0 ?
      `This will also delete ${task.subtasks.length} subtask(s). This action cannot be undone.` :
      'This action cannot be undone.',
    confirmText: 'Delete Task',
    variant: 'danger',
    loading: false,
    onConfirm: () => confirmDeleteTask(task)
  }
  showConfirmModal.value = true
}

function handleCreateSubtask(taskId) {
  // Find the parent task
  const task = tasks.value.find(t => t.taskId === taskId)

  selectedTask.value = null
  isEditing.value = false
  isSubtask.value = true
  parentTaskId.value = taskId
  parentTask.value = task // NEW: Store parent task reference
  showCreateEditModal.value = true
}

function handleViewSubtask(subtask) {
  selectedTask.value = subtask
  isSubtask.value = true
  showDetailModal.value = true
}

function handleEditSubtask(subtask) {
  selectedTask.value = subtask
  isEditing.value = true
  isSubtask.value = true
  showCreateEditModal.value = true
}

function handleDeleteSubtask(subtask) {
  confirmModal.value = {
    title: 'Delete Subtask',
    description: `Are you sure you want to delete "${subtask.title}"?`,
    warningText: 'This action cannot be undone.',
    confirmText: 'Delete Subtask',
    variant: 'danger',
    loading: false,
    onConfirm: () => confirmDeleteSubtask(subtask)
  }
  showConfirmModal.value = true
}

function handleEditFromDetail() {
  showDetailModal.value = false
  isEditing.value = true
  showCreateEditModal.value = true
}

function handleDeleteFromDetail() {
  showDetailModal.value = false
  if (isSubtask.value) {
    handleDeleteSubtask(selectedTask.value)
  } else {
    handleDeleteTask(selectedTask.value)
  }
}

// Task operations
async function handleSaveTask(taskData) {
  try {
    console.log('Saving task:', taskData)
    const endpoint = isSubtask.value ? 'subtasks' : 'tasks'
    let response

    if (isEditing.value) {
      // Update existing task/subtask
      const id = isSubtask.value ? selectedTask.value.subTaskId : selectedTask.value.taskId
      console.log(`Updating ${endpoint}/${id}`)
      response = await axios.put(`${import.meta.env.VITE_BACKEND_API}${endpoint}/${id}`, taskData)
    } else {
      // Create new task/subtask
      if (isSubtask.value) {
        taskData.taskId = parentTaskId.value
      }
      taskData.creatorId = authStore.user?.uid

      console.log(`Creating new ${endpoint}`)
      response = await axios.post(`${import.meta.env.VITE_BACKEND_API}${endpoint}`, taskData)
    }

    console.log('Save response:', response.data)
    toast.success(`${isSubtask.value ? 'Subtask' : 'Task'} ${isEditing.value ? 'updated' : 'created'} successfully`)
    closeCreateEditModal()

    // Refresh data after successful save
    isManualRefresh.value = false // Don't show success message for this refresh
    await refreshTasks()

  } catch (error) {
    console.error('Error saving task:', error.response?.status, error.response?.data)
    const errorMessage = error.response?.data?.error || error.message

    if (error.response?.status === 404) {
      toast.error(`${isSubtask.value ? 'Subtask' : 'Task'} API not found. Please check if backend services are running.`)
    } else if (error.response?.status === 400) {
      toast.error(`Invalid data: ${errorMessage}`)
    } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      toast.error('Cannot connect to backend. Please ensure services are running.')
    } else {
      toast.error(`Failed to ${isEditing.value ? 'update' : 'create'} ${isSubtask.value ? 'subtask' : 'task'}: ${errorMessage}`)
    }
  }
}

async function confirmDeleteTask(task) {
  confirmModal.value.loading = true
  try {
    console.log('Deleting task:', task.taskId)
    await axios.delete(`${import.meta.env.VITE_BACKEND_API}tasks/${task.taskId}`)

    toast.success('Task deleted successfully')
    closeConfirmModal()

    // Refresh data after successful delete
    isManualRefresh.value = false // Don't show success message for this refresh
    await refreshTasks()

  } catch (error) {
    console.error('Error deleting task:', error.response?.status, error.response?.data)
    const errorMessage = error.response?.data?.error || error.message

    if (error.response?.status === 404) {
      toast.error('Task not found or already deleted')
    } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      toast.error('Cannot connect to backend. Please ensure services are running.')
    } else {
      toast.error(`Failed to delete task: ${errorMessage}`)
    }
  } finally {
    confirmModal.value.loading = false
  }
}

async function confirmDeleteSubtask(subtask) {
  confirmModal.value.loading = true
  try {
    console.log('Deleting subtask:', subtask.subTaskId)
    await axios.delete(`${import.meta.env.VITE_BACKEND_API}subtasks/${subtask.subTaskId}`)

    toast.success('Subtask deleted successfully')
    closeConfirmModal()

    // Refresh data after successful delete
    isManualRefresh.value = false // Don't show success message for this refresh
    await refreshTasks()

  } catch (error) {
    console.error('Error deleting subtask:', error.response?.status, error.response?.data)
    const errorMessage = error.response?.data?.error || error.message

    if (error.response?.status === 404) {
      toast.error('Subtask not found or already deleted')
    } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      toast.error('Cannot connect to backend. Please ensure services are running.')
    } else {
      toast.error(`Failed to delete subtask: ${errorMessage}`)
    }
  } finally {
    confirmModal.value.loading = false
  }
}

async function handleTaskMoved(taskId, newStatus, oldStatus) {
  const task = tasks.value.find(t => t.taskId === taskId)
  if (!task) return

  // Check for backward movement (except to unassigned)
  const statusOrder = ['unassigned', 'ongoing', 'under_review', 'completed']
  const oldIndex = statusOrder.indexOf(oldStatus)
  const newIndex = statusOrder.indexOf(newStatus)

  // Check that subtask status are completed before task can be completed
  if (task.subtasks?.length > 0 && newStatus === 'completed') {
    const incompleteSubtasks = task.subtasks.filter(st => st.status !== 'completed')
    if (incompleteSubtasks.length > 0) {
      toast.error(`Cannot complete task. ${incompleteSubtasks.length} subtask(s) are not completed.`)
      return
    }
  }

  // Show confirmation modal
  confirmModal.value = {
    title: 'Move Task',
    description: `Move "${task.title}" from ${formatStatus(oldStatus)} to ${formatStatus(newStatus)}?`,
    warningText: newStatus === 'completed' ? 'This will mark the task as completed.' :
      newIndex < oldIndex ? 'This will move the task backward in the workflow.' : '',
    confirmText: 'Move Task',
    variant: newIndex < oldIndex ? 'warning' : 'info',
    loading: false,
    onConfirm: () => confirmMoveTask(taskId, newStatus)
  }
  showConfirmModal.value = true
}

async function confirmMoveTask(taskId, newStatus) {
  confirmModal.value.loading = true
  try {
    console.log(`Moving task ${taskId} to status: ${newStatus}`)
    await axios.put(`${import.meta.env.VITE_BACKEND_API}tasks/${taskId}`, {
      status: newStatus
    })

    toast.success('Task moved successfully')
    closeConfirmModal()

    // Refresh data after successful move
    isManualRefresh.value = false // Don't show success message for this refresh
    await refreshTasks()

  } catch (error) {
    console.error('Error moving task:', error.response?.status, error.response?.data)
    const errorMessage = error.response?.data?.error || error.message

    if (error.response?.status === 404) {
      toast.error('Task not found')
    } else if (error.response?.status === 400) {
      toast.error(`Invalid status change: ${errorMessage}`)
    } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      toast.error('Cannot connect to backend. Please ensure services are running.')
    } else {
      toast.error(`Failed to move task: ${errorMessage}`)
    }
  } finally {
    confirmModal.value.loading = false
  }
}

// Utility functions
function formatStatus(status) {
  const statusMap = {
    'unassigned': 'Unassigned',
    'ongoing': 'Ongoing',
    'under_review': 'Under Review',
    'completed': 'Completed'
  }
  return statusMap[status] || status
}

function getUserDisplayName(userId) {
  if (!userId) return 'Unassigned'
  if (userId === authStore.user?.uid) return 'You'
  const user = allUsers.value.find(u => u.uid === userId)
  return user ? (user.name || user.displayName || user.email) : 'Unknown User'
}

function clearFilters() {
  filters.value = {
    search: '',
    project: '',
    sortBy: 'createdAt'
  }
}

// Auto refresh functionality
function startAutoRefresh() {
  autoRefreshInterval.value = setInterval(() => {
    if (!autoRefreshPaused.value) {
      isManualRefresh.value = false // Silent refresh
      refreshTasks()
    }
  }, 30000) // 30 seconds

  autoRefreshCountdownInterval.value = setInterval(() => {
    if (!autoRefreshPaused.value) {
      autoRefreshCountdown.value--
      if (autoRefreshCountdown.value <= 0) {
        autoRefreshCountdown.value = 30
      }
    }
  }, 1000)
}

function stopAutoRefresh() {
  if (autoRefreshInterval.value) {
    clearInterval(autoRefreshInterval.value)
    autoRefreshInterval.value = null
  }
  if (autoRefreshCountdownInterval.value) {
    clearInterval(autoRefreshCountdownInterval.value)
    autoRefreshCountdownInterval.value = null
  }
}

async function fetchProjects() {
  if (!authStore.user?.uid) {
    console.log('⚠️ No user ID available for fetchProjects')
    return
  }

  loadingProjects.value = true
  try {
    console.log('Fetching projects for user:', authStore.user.uid)
    const response = await axios.get(`${import.meta.env.VITE_BACKEND_API}project/${authStore.user.uid}`)

    console.log('📡 Full API response:', response)
    console.log('📊 Response data:', response.data)
    console.log('📋 Projects array:', response.data.projects)

    projects.value = response.data.projects || []

    // Cache projects globally for TaskCard to use
    if (!window.cachedProjects) {
      window.cachedProjects = {}
    }

    projects.value.forEach(project => {
      window.cachedProjects[project.projectId] = {
        title: project.title,
        ownerId: project.ownerId,
        collaborators: project.collaborators
      }
    })

    console.log(`✅ Loaded ${projects.value.length} projects:`, projects.value)
  } catch (error) {
    console.error('⚠️ Error fetching projects:', error)
    if (error.response?.status === 404) {
      projects.value = []
    } else {
      toast.error('Failed to load projects')
    }
  } finally {
    loadingProjects.value = false
  }
}

function handleProjectFilterFromNavigation() {
  // Check if we came from project page with a filter
  if (window.selectedProjectForFilter) {
    const projectFilter = window.selectedProjectForFilter

    // Set the project filter
    filters.value.project = projectFilter.projectId

    // Open create task modal if requested
    if (window.createTaskForProject) {
      setTimeout(() => {
        openCreateTaskModal()
        window.createTaskForProject = null // Clear flag
      }, 500)
    }

    // Open task detail modal if specific task was selected
    if (window.selectedTaskForView) {
      const task = window.selectedTaskForView
      setTimeout(() => {
        handleViewTask(task)
        window.selectedTaskForView = null // Clear flag
      }, 500)
    }

    // Clear the global variable
    window.selectedProjectForFilter = null

    // Show success message
    toast.info(`Filtered tasks for project: ${projectFilter.projectTitle}`)
  }
}

// Watch for modals opening/closing to pause auto-refresh
watch(anyModalOpen, (isOpen) => {
  autoRefreshPaused.value = isOpen
  if (!isOpen) {
    autoRefreshCountdown.value = 30
  }
})

// Lifecycle
onMounted(async () => {
  console.log('🚀 TasksView mounted, starting initialization...')

  loading.value = true
  try {
    console.log('📊 Loading initial data...')

    // Load in the correct order:
    // 1. Users first (needed for display names)
    await fetchUsers()

    // 2. Projects second (needed for filtering tasks/subtasks)
    await fetchProjects()

    // 3. Tasks third (needed before subtasks for project-based filtering)
    await fetchTasks()

    // 4. Subtasks last (can now check against tasks for project filtering)
    await fetchSubtasks()

    // 5. Associate subtasks with tasks
    associateSubtasksWithTasks()

    // Check for project filter from navigation
    handleProjectFilterFromNavigation()

    startAutoRefresh()
    console.log('✅ Initial data loaded successfully')

    // Show initial load success only
    toast.success('Task board loaded successfully')
  } catch (error) {
    console.error('⚠️ Failed to load initial data:', error)
    toast.error('Failed to load initial data')
  } finally {
    loading.value = false
  }
})


onUnmounted(() => {
  stopAutoRefresh()
  // Clean up global variables
  if (window.selectedProjectForFilter) {
    window.selectedProjectForFilter = null
  }
  if (window.selectedTaskForView) {
    window.selectedTaskForView = null
  }
  if (window.createTaskForProject) {
    window.createTaskForProject = null
  }
})
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
