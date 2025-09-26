<!-- src/tests/TestTaskBackend.vue -->
<template>
  <div class="test-container">
    <!-- Header -->
    <div class="header">
      <h1>🎯 Task & SubTask Manager</h1>
      <p class="subtitle">Comprehensive CRUD Testing Interface</p>

      <div v-if="authStore.isAuthenticated" class="user-info">
        <div class="user-avatar">👤</div>
        <div class="user-details">
          <div class="user-name">{{ authStore.user.displayName || authStore.user.email }}</div>
          <div class="user-role">{{ authStore.user.role || 'Team Member' }}</div>
        </div>
      </div>

      <div v-else class="auth-warning">
        <span class="warning-icon">⚠️</span>
        Please log in to test the APIs
      </div>
    </div>

    <!-- Login Prompt -->
    <div v-if="!authStore.isAuthenticated" class="login-prompt">
      <div class="login-content">
        <h2>🔐 Authentication Required</h2>
        <p>You need to be logged in to test the Task and SubTask APIs.</p>
        <button @click="$router.push('/authentication')" class="btn btn-primary btn-large">
          🚀 Go to Login
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else class="main-content">
      <!-- Success/Error Notifications -->
      <div v-if="notification.show" :class="['notification', notification.type]">
        <span class="notification-icon">
          {{ notification.type === 'success' ? '✅' : '❌' }}
        </span>
        <span class="notification-message">{{ notification.message }}</span>
        <button @click="hideNotification" class="notification-close">×</button>
      </div>

      <!-- Tab Navigation -->
      <div class="tabs">
        <button :class="['tab-btn', { active: activeTab === 'tasks' }]" @click="switchTab('tasks')">
          <span class="tab-icon">📋</span>
          <span>Tasks</span>
          <span v-if="tasks.length > 0" class="tab-count">{{ tasks.length }}</span>
        </button>
        <button :class="['tab-btn', { active: activeTab === 'subtasks' }]" @click="switchTab('subtasks')">
          <span class="tab-icon">📝</span>
          <span>SubTasks</span>
          <span v-if="subtasks.length > 0" class="tab-count">{{ subtasks.length }}</span>
        </button>
      </div>

      <!-- Tasks Tab -->
      <div v-if="activeTab === 'tasks'" class="tab-content">
        <!-- Create Task Form -->
        <div class="create-section">
          <div class="section-header">
            <h2>
              <span class="section-icon">➕</span>
              Create New Task
            </h2>
            <button v-if="Object.values(newTask).some(val => val)" @click="clearTaskForm"
              class="btn btn-outline btn-small">
              🗑️ Clear Form
            </button>
          </div>

          <form @submit.prevent="createTask" class="create-form">
            <!-- Row 1: Title and Project -->
            <div class="form-row">
              <div class="form-group flex-2">
                <label for="task-title" class="form-label required">Task Title</label>
                <input id="task-title" v-model="newTask.title" placeholder="e.g., Implement user authentication system"
                  required class="form-input" maxlength="100" />
                <div class="char-count">{{ newTask.title.length }}/100</div>
              </div>
              <div class="form-group flex-1">
                <label for="task-project" class="form-label">Project ID</label>
                <input id="task-project" v-model="newTask.projectId" placeholder="project-alpha-2024"
                  class="form-input" />
              </div>
            </div>

            <!-- Row 2: Deadline and Status -->
            <div class="form-row">
              <div class="form-group flex-1">
                <label for="task-deadline" class="form-label required">Deadline</label>
                <div class="datetime-group">
                  <input id="task-deadline" v-model="newTask.deadlineDate" type="datetime-local" required
                    class="form-input" :min="minDateTime" />
                  <div class="quick-dates">
                    <button type="button" @click="setQuickDate('task', 1)" class="quick-btn">Tomorrow</button>
                    <button type="button" @click="setQuickDate('task', 7)" class="quick-btn">Next Week</button>
                    <button type="button" @click="setQuickDate('task', 30)" class="quick-btn">Next Month</button>
                  </div>
                </div>
              </div>
              <div class="form-group flex-1">
                <label for="task-status" class="form-label">Status</label>
                <select id="task-status" v-model="newTask.status" class="form-input">
                  <option value="unassigned">📋 Unassigned</option>
                  <option value="ongoing">🔄 Ongoing</option>
                  <option value="under_review">👀 Under Review</option>
                  <option value="completed">✅ Completed</option>
                </select>
              </div>
            </div>

            <!-- Row 3: Notes -->
            <div class="form-row">
              <div class="form-group full-width">
                <label for="task-notes" class="form-label">Notes</label>
                <textarea id="task-notes" v-model="newTask.notes"
                  placeholder="Add any additional details, requirements, or context..." class="form-textarea" rows="3"
                  maxlength="500"></textarea>
                <div class="char-count">{{ newTask.notes.length }}/500</div>
              </div>
            </div>

            <!-- Row 4: Attachments -->
            <div class="form-row">
              <div class="form-group full-width">
                <label for="task-attachments" class="form-label">Attachments</label>
                <div class="file-upload-area">
                  <input id="task-attachments" type="file" multiple @change="handleTaskFileUpload"
                    accept="image/*,application/pdf,.doc,.docx,.txt,.csv,.xlsx" class="file-input"
                    ref="taskFileInput" />
                  <div class="file-upload-content" @click="$refs.taskFileInput.click()">
                    <div class="upload-icon">📎</div>
                    <div class="upload-text">
                      <span class="upload-title">Click to upload attachments</span>
                      <span class="upload-subtitle">PNG, JPG, PDF, DOC, TXT (max 2MB each)</span>
                    </div>
                  </div>
                </div>

                <!-- File List -->
                <div v-if="taskAttachments.length > 0" class="file-list">
                  <div v-for="(file, index) in taskAttachments" :key="index" class="file-item">
                    <div class="file-info">
                      <span class="file-icon">{{ getFileIcon(file.type) }}</span>
                      <div class="file-details">
                        <span class="file-name">{{ file.name }}</span>
                        <span class="file-size">{{ formatFileSize(file.size) }}</span>
                      </div>
                    </div>
                    <button type="button" @click="removeTaskAttachment(index)" class="file-remove">
                      ×
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Row 5: Team -->
            <div class="form-row">
              <div class="form-group flex-1">
                <label for="task-collaborators" class="form-label">Collaborators</label>
                <input id="task-collaborators" v-model="collaboratorsInput" placeholder="user1, user2, user3"
                  class="form-input" />
                <div class="form-hint">Comma-separated user IDs</div>
              </div>
              <div class="form-group flex-1">
                <label for="task-owner" class="form-label">Task Owner</label>
                <input id="task-owner" v-model="newTask.ownerId" :placeholder="authStore.user.uid" class="form-input" />
                <div class="form-hint">Defaults to you</div>
              </div>
            </div>

            <!-- Submit Button -->
            <div class="form-actions">
              <button type="submit" :disabled="loading || !newTask.title.trim()" class="btn btn-primary btn-large">
                <span v-if="loading" class="spinner"></span>
                {{ loading ? 'Creating Task...' : '🚀 Create Task' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Tasks List -->
        <div class="list-section">
          <div class="section-header">
            <h2>
              <span class="section-icon">📋</span>
              All Tasks
              <span v-if="tasks.length > 0" class="count-badge">{{ tasks.length }}</span>
            </h2>
            <div class="header-actions">
              <button @click="getAllTasks" :disabled="loading" class="btn btn-outline">
                <span v-if="loading" class="spinner-small"></span>
                🔄 Refresh
              </button>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="tasks.length === 0" class="empty-state">
            <div class="empty-icon">📝</div>
            <h3>No tasks yet</h3>
            <p>Create your first task using the form above!</p>
          </div>

          <!-- Tasks Grid -->
          <div v-else class="items-grid">
            <div v-for="task in tasks" :key="task.taskId" class="task-card">
              <div class="card-header">
                <h3 class="card-title">{{ task.title }}</h3>
                <span :class="['status-badge', task.status]">
                  {{ getStatusIcon(task.status) }} {{ formatStatus(task.status) }}
                </span>
              </div>

              <div class="card-content">
                <div class="card-meta">
                  <div class="meta-item">
                    <span class="meta-label">📅 Deadline:</span>
                    <span :class="['meta-value', { 'overdue': isOverdue(task.deadline) }]">
                      {{ formatDateTime(task.deadline) }}
                    </span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">👤 Owner:</span>
                    <span class="meta-value">{{ task.ownerId === authStore.user.uid ? 'You' : task.ownerId }}</span>
                  </div>
                  <div v-if="task.projectId" class="meta-item">
                    <span class="meta-label">🏗️ Project:</span>
                    <span class="meta-value">{{ task.projectId }}</span>
                  </div>
                  <div v-if="task.collaborators?.length" class="meta-item">
                    <span class="meta-label">👥 Team:</span>
                    <span class="meta-value">{{ task.collaborators.length }} members</span>
                  </div>
                  <div v-if="task.attachments?.length" class="meta-item">
                    <span class="meta-label">📎 Files:</span>
                    <span class="meta-value">{{ task.attachments.length }} attachment{{ task.attachments.length > 1 ?
                      's' : '' }}</span>
                  </div>
                </div>

                <div v-if="task.notes" class="card-notes">
                  <p>{{ task.notes }}</p>
                </div>

                <div class="card-timestamps">
                  <small>Created {{ formatRelativeTime(task.createdAt) }}</small>
                  <small v-if="task.updatedAt !== task.createdAt">
                    • Updated {{ formatRelativeTime(task.updatedAt) }}
                  </small>
                </div>
              </div>

              <div class="card-actions">
                <button @click="editTask(task)" class="btn btn-small btn-outline">
                  ✏️ Edit
                </button>
                <button @click="getTaskSubtasks(task.taskId)" class="btn btn-small btn-info">
                  📝 SubTasks
                </button>
                <button @click="deleteTask(task.taskId)" class="btn btn-small btn-danger">
                  🗑️ Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- SubTasks Tab -->
      <div v-if="activeTab === 'subtasks'" class="tab-content">
        <!-- Create SubTask Form -->
        <div class="create-section">
          <div class="section-header">
            <h2>
              <span class="section-icon">➕</span>
              Create New SubTask
            </h2>
            <button v-if="Object.values(newSubtask).some(val => val)" @click="clearSubtaskForm"
              class="btn btn-outline btn-small">
              🗑️ Clear Form
            </button>
          </div>

          <form @submit.prevent="createSubtask" class="create-form">
            <!-- Row 1: Title and Parent Task -->
            <div class="form-row">
              <div class="form-group flex-2">
                <label for="subtask-title" class="form-label required">SubTask Title</label>
                <input id="subtask-title" v-model="newSubtask.title" placeholder="e.g., Design login form UI components"
                  required class="form-input" maxlength="100" />
                <div class="char-count">{{ newSubtask.title.length }}/100</div>
              </div>
              <div class="form-group flex-1">
                <label for="subtask-parent" class="form-label required">Parent Task</label>
                <select id="subtask-parent" v-model="newSubtask.taskId" required class="form-input">
                  <option value="">Select a parent task...</option>
                  <option v-for="task in tasks" :key="task.taskId" :value="task.taskId">
                    {{ task.title }}
                  </option>
                </select>
                <div v-if="tasks.length === 0" class="form-hint warning">
                  ⚠️ Create a task first!
                </div>
              </div>
            </div>

            <!-- Row 2: Deadline and Status -->
            <div class="form-row">
              <div class="form-group flex-1">
                <label for="subtask-deadline" class="form-label required">Deadline</label>
                <div class="datetime-group">
                  <input id="subtask-deadline" v-model="newSubtask.deadlineDate" type="datetime-local" required
                    class="form-input" :min="minDateTime" />
                  <div class="quick-dates">
                    <button type="button" @click="setQuickDate('subtask', 1)" class="quick-btn">Tomorrow</button>
                    <button type="button" @click="setQuickDate('subtask', 7)" class="quick-btn">Next Week</button>
                  </div>
                </div>
              </div>
              <div class="form-group flex-1">
                <label for="subtask-status" class="form-label">Status</label>
                <select id="subtask-status" v-model="newSubtask.status" class="form-input">
                  <option value="unassigned">📋 Unassigned</option>
                  <option value="ongoing">🔄 Ongoing</option>
                  <option value="under_review">👀 Under Review</option>
                  <option value="completed">✅ Completed</option>
                </select>
              </div>
            </div>

            <!-- Row 3: Notes -->
            <div class="form-row">
              <div class="form-group full-width">
                <label for="subtask-notes" class="form-label">Notes</label>
                <textarea id="subtask-notes" v-model="newSubtask.notes"
                  placeholder="Add implementation details, requirements, or context..." class="form-textarea" rows="3"
                  maxlength="500"></textarea>
                <div class="char-count">{{ newSubtask.notes.length }}/500</div>
              </div>
            </div>

            <!-- Row 4: Attachments -->
            <div class="form-row">
              <div class="form-group full-width">
                <label for="subtask-attachments" class="form-label">Attachments</label>
                <div class="file-upload-area">
                  <input id="subtask-attachments" type="file" multiple @change="handleSubtaskFileUpload"
                    accept="image/*,application/pdf,.doc,.docx,.txt,.csv,.xlsx" class="file-input"
                    ref="subtaskFileInput" />
                  <div class="file-upload-content" @click="$refs.subtaskFileInput.click()">
                    <div class="upload-icon">📎</div>
                    <div class="upload-text">
                      <span class="upload-title">Click to upload attachments</span>
                      <span class="upload-subtitle">PNG, JPG, PDF, DOC, TXT (max 2MB each)</span>
                    </div>
                  </div>
                </div>

                <!-- File List -->
                <div v-if="subtaskAttachments.length > 0" class="file-list">
                  <div v-for="(file, index) in subtaskAttachments" :key="index" class="file-item">
                    <div class="file-info">
                      <span class="file-icon">{{ getFileIcon(file.type) }}</span>
                      <div class="file-details">
                        <span class="file-name">{{ file.name }}</span>
                        <span class="file-size">{{ formatFileSize(file.size) }}</span>
                      </div>
                    </div>
                    <button type="button" @click="removeSubtaskAttachment(index)" class="file-remove">
                      ×
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Row 5: Team -->
            <div class="form-row">
              <div class="form-group flex-1">
                <label for="subtask-collaborators" class="form-label">Collaborators</label>
                <input id="subtask-collaborators" v-model="subtaskCollaboratorsInput" placeholder="user1, user2, user3"
                  class="form-input" />
                <div class="form-hint">Comma-separated user IDs</div>
              </div>
              <div class="form-group flex-1">
                <label for="subtask-owner" class="form-label">SubTask Owner</label>
                <input id="subtask-owner" v-model="newSubtask.ownerId" :placeholder="authStore.user.uid"
                  class="form-input" />
                <div class="form-hint">Defaults to you</div>
              </div>
            </div>

            <!-- Submit Button -->
            <div class="form-actions">
              <button type="submit" :disabled="loading || !newSubtask.title.trim() || !newSubtask.taskId"
                class="btn btn-primary btn-large">
                <span v-if="loading" class="spinner"></span>
                {{ loading ? 'Creating SubTask...' : '🚀 Create SubTask' }}
              </button>
            </div>
          </form>
        </div>

        <!-- SubTasks List -->
        <div class="list-section">
          <div class="section-header">
            <h2>
              <span class="section-icon">📝</span>
              All SubTasks
              <span v-if="subtasks.length > 0" class="count-badge">{{ subtasks.length }}</span>
            </h2>
            <div class="header-actions">
              <button @click="getAllSubtasks" :disabled="loading" class="btn btn-outline">
                <span v-if="loading" class="spinner-small"></span>
                🔄 Refresh
              </button>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="subtasks.length === 0" class="empty-state">
            <div class="empty-icon">📝</div>
            <h3>No subtasks yet</h3>
            <p>Break down your tasks into manageable subtasks!</p>
          </div>

          <!-- SubTasks Grid -->
          <div v-else class="items-grid">
            <div v-for="subtask in subtasks" :key="subtask.subTaskId" class="subtask-card">
              <div class="card-header">
                <h3 class="card-title">{{ subtask.title }}</h3>
                <span :class="['status-badge', subtask.status]">
                  {{ getStatusIcon(subtask.status) }} {{ formatStatus(subtask.status) }}
                </span>
              </div>

              <div class="card-content">
                <div class="parent-task">
                  <span class="parent-label">🔗 Parent Task:</span>
                  <span class="parent-value">{{ getParentTaskTitle(subtask.taskId) }}</span>
                </div>

                <div class="card-meta">
                  <div class="meta-item">
                    <span class="meta-label">📅 Deadline:</span>
                    <span :class="['meta-value', { 'overdue': isOverdue(subtask.deadline) }]">
                      {{ formatDateTime(subtask.deadline) }}
                    </span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">👤 Owner:</span>
                    <span class="meta-value">{{ subtask.ownerId === authStore.user.uid ? 'You' : subtask.ownerId
                      }}</span>
                  </div>
                  <div v-if="subtask.collaborators?.length" class="meta-item">
                    <span class="meta-label">👥 Team:</span>
                    <span class="meta-value">{{ subtask.collaborators.length }} members</span>
                  </div>
                  <div v-if="subtask.attachments?.length" class="meta-item">
                    <span class="meta-label">📎 Files:</span>
                    <span class="meta-value">{{ subtask.attachments.length }} attachment{{ subtask.attachments.length >
                      1 ? 's' : '' }}</span>
                  </div>
                </div>

                <div v-if="subtask.notes" class="card-notes">
                  <p>{{ subtask.notes }}</p>
                </div>

                <div class="card-timestamps">
                  <small>Created {{ formatRelativeTime(subtask.createdAt) }}</small>
                  <small v-if="subtask.updatedAt !== subtask.createdAt">
                    • Updated {{ formatRelativeTime(subtask.updatedAt) }}
                  </small>
                </div>
              </div>

              <div class="card-actions">
                <button @click="editSubtask(subtask)" class="btn btn-small btn-outline">
                  ✏️ Edit
                </button>
                <button @click="deleteSubtask(subtask.subTaskId)" class="btn btn-small btn-danger">
                  🗑️ Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Edit Modal -->
      <TaskEdit :show="editModal.show && editModal.type === 'task'" :taskData="editModal.data" @close="closeEditModal"
        @save="saveEdit" />


      <!-- API Response Logger -->
      <div v-if="lastResponse" class="response-logger">
        <div class="logger-header">
          <h3>🔍 API Response Log</h3>
          <button @click="clearResponse" class="btn btn-small btn-outline">Clear</button>
        </div>
        <div class="response-container">
          <div class="response-meta">
            <span :class="['method-badge', lastResponse.method]">{{ lastResponse.method }}</span>
            <span class="url-text">{{ lastResponse.url }}</span>
            <span :class="['status-badge', lastResponse.success ? 'success' : 'error']">
              {{ lastResponse.status }}
            </span>
            <span class="timestamp">{{ lastResponse.timestamp }}</span>
          </div>
          <pre class="response-body">{{ JSON.stringify(lastResponse.data, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import TaskEdit from "@/components/task/ChangeTaskDetails.vue";
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'



// Environment variables - Fix the API endpoints
const taskAPI = import.meta.env.VITE_BACKEND_API
const subtaskAPI = import.meta.env.VITE_BACKEND_API

// Stores
const authStore = useAuthStore()

// Reactive data
const activeTab = ref('tasks')
const loading = ref(false)
const tasks = ref([])
const subtasks = ref([])
const lastResponse = ref(null)

// Notification system
const notification = ref({
  show: false,
  type: 'success', // 'success' | 'error'
  message: ''
})

// Computed properties
const minDateTime = computed(() => {
  const now = new Date()
  return now.toISOString().slice(0, 16)
})

// Task form data with date handling
const newTask = ref({
  title: '',
  deadlineDate: '',
  status: 'ongoing',
  notes: '',
  projectId: '',
  ownerId: ''
})

// Subtask form data with date handling
const newSubtask = ref({
  title: '',
  taskId: '',
  deadlineDate: '',
  status: 'ongoing',
  notes: '',
  ownerId: ''
})

// Collaborators inputs
const collaboratorsInput = ref('')
const subtaskCollaboratorsInput = ref('')

// File attachments
const taskAttachments = ref([])
const subtaskAttachments = ref([])
const editAttachments = ref([])

// File upload refs
const taskFileInput = ref(null)
const subtaskFileInput = ref(null)
const editFileInput = ref(null)

// Edit modal with date handling
const editModal = ref({
  show: false,
  type: '', // 'task' | 'subtask'
  data: {},
  id: '',
  deadlineDate: ''
})

// Utility Functions
const formatDateTime = (timestamp) => {
  if (!timestamp) return 'Not set'
  const date = new Date(timestamp * 1000)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const formatRelativeTime = (timestamp) => {
  if (!timestamp) return 'Unknown'
  const now = Date.now()
  const time = timestamp * 1000
  const diff = now - time

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return formatDateTime(timestamp)
}

const formatStatus = (status) => {
  const statusMap = {
    'ongoing': 'Ongoing',
    'unassigned': 'Unassigned',
    'under_review': 'Under Review',
    'completed': 'Completed'
  }
  return statusMap[status] || status
}

const getStatusIcon = (status) => {
  const iconMap = {
    'ongoing': '🔄',
    'unassigned': '📋',
    'under_review': '👀',
    'completed': '✅'
  }
  return iconMap[status] || '❓'
}

const isOverdue = (deadline) => {
  return deadline && (Date.now() / 1000) > deadline
}

const getParentTaskTitle = (taskId) => {
  const task = tasks.value.find(t => t.taskId === taskId)
  return task ? task.title : 'Unknown Task'
}

const dateTimeToEpoch = (dateTimeLocal) => {
  return dateTimeLocal ? Math.floor(new Date(dateTimeLocal).getTime() / 1000) : null
}

const epochToDateTime = (epoch) => {
  if (!epoch) return ''
  return new Date(epoch * 1000).toISOString().slice(0, 16)
}

const setQuickDate = (type, days) => {
  const date = new Date()
  date.setDate(date.getDate() + days)
  const dateTimeLocal = date.toISOString().slice(0, 16)

  if (type === 'task') {
    newTask.value.deadlineDate = dateTimeLocal
  } else {
    newSubtask.value.deadlineDate = dateTimeLocal
  }
}

const parseCollaborators = (input) => {
  return input ? input.split(',').map(id => id.trim()).filter(id => id) : []
}

const showNotification = (type, message) => {
  notification.value = { show: true, type, message }
  setTimeout(() => {
    notification.value.show = false
  }, 5000)
}

const hideNotification = () => {
  notification.value.show = false
}

const clearResponse = () => {
  lastResponse.value = null
}

const clearTaskForm = () => {
  newTask.value = {
    title: '',
    deadlineDate: '',
    status: 'ongoing',
    notes: '',
    projectId: '',
    ownerId: ''
  }
  collaboratorsInput.value = ''
  taskAttachments.value = []
}

const clearSubtaskForm = () => {
  newSubtask.value = {
    title: '',
    taskId: '',
    deadlineDate: '',
    status: 'ongoing',
    notes: '',
    ownerId: ''
  }
  subtaskCollaboratorsInput.value = ''
  subtaskAttachments.value = []
}

// File handling utilities
const MAX_FILE_SIZE = 2 * 1024 * 1024 // 2MB in bytes

const getFileIcon = (fileType) => {
  if (fileType.startsWith('image/')) return '🖼️'
  if (fileType.includes('pdf')) return '📄'
  if (fileType.includes('word') || fileType.includes('doc')) return '📝'
  if (fileType.includes('excel') || fileType.includes('sheet')) return '📊'
  if (fileType.includes('text')) return '📄'
  return '📎'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const validateFile = (file) => {
  if (file.size > MAX_FILE_SIZE) {
    showNotification('error', `File "${file.name}" is too large. Maximum size is 2MB.`)
    return false
  }
  return true
}

const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => {
      // Remove the data:mime;base64, prefix
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = error => reject(error)
  })
}

const handleTaskFileUpload = async (event) => {
  const files = Array.from(event.target.files)

  for (const file of files) {
    if (!validateFile(file)) continue

    try {
      const base64 = await fileToBase64(file)
      taskAttachments.value.push({
        name: file.name,
        type: file.type,
        size: file.size,
        base64: base64
      })
    } catch (error) {
      showNotification('error', `Failed to process file "${file.name}"`)
    }
  }

  // Clear the input so the same file can be selected again
  event.target.value = ''
}

const handleSubtaskFileUpload = async (event) => {
  const files = Array.from(event.target.files)

  for (const file of files) {
    if (!validateFile(file)) continue

    try {
      const base64 = await fileToBase64(file)
      subtaskAttachments.value.push({
        name: file.name,
        type: file.type,
        size: file.size,
        base64: base64
      })
    } catch (error) {
      showNotification('error', `Failed to process file "${file.name}"`)
    }
  }

  // Clear the input so the same file can be selected again
  event.target.value = ''
}

const removeTaskAttachment = (index) => {
  taskAttachments.value.splice(index, 1)
}

const removeSubtaskAttachment = (index) => {
  subtaskAttachments.value.splice(index, 1)
}

const handleEditFileUpload = async (event) => {
  const files = Array.from(event.target.files)

  for (const file of files) {
    if (!validateFile(file)) continue

    try {
      const base64 = await fileToBase64(file)
      editAttachments.value.push({
        name: file.name,
        type: file.type,
        size: file.size,
        base64: base64
      })
    } catch (error) {
      showNotification('error', `Failed to process file "${file.name}"`)
    }
  }

  // Clear the input so the same file can be selected again
  event.target.value = ''
}

const removeEditAttachment = (index) => {
  editAttachments.value.splice(index, 1)
}

const logResponse = (method, url, success, status, data) => {
  lastResponse.value = {
    method,
    url,
    success,
    status,
    data,
    timestamp: new Date().toLocaleString()
  }
}

// API Functions
const makeRequest = async (url, options = {}) => {
  try {
    loading.value = true
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    })

    const data = await response.json()
    const success = response.ok

    logResponse(options.method || 'GET', url, success, response.status, data)

    if (!success) {
      showNotification('error', data.error || 'Request failed')
      throw new Error(data.error || 'Request failed')
    }

    return data
  } catch (error) {
    logResponse(options.method || 'GET', url, false, 'ERROR', { error: error.message })
    showNotification('error', error.message)
    throw error
  } finally {
    loading.value = false
  }
}

// Task CRUD Operations
const createTask = async () => {
  const taskData = {
    title: newTask.value.title,
    creatorId: authStore.user.uid,
    deadline: dateTimeToEpoch(newTask.value.deadlineDate),
    status: newTask.value.status,
    notes: newTask.value.notes,
    projectId: newTask.value.projectId,
    ownerId: newTask.value.ownerId || authStore.user.uid,
    collaborators: parseCollaborators(collaboratorsInput.value),
    attachments: taskAttachments.value.map(file => file.base64)
  }

  const response = await makeRequest(`${taskAPI}tasks`, {
    method: 'POST',
    body: JSON.stringify(taskData)
  })

  showNotification('success', 'Task created successfully!')
  clearTaskForm()
  await getAllTasks()
}

const getAllTasks = async () => {
  const response = await makeRequest(`${taskAPI}tasks`)
  tasks.value = response.tasks || []
}

const deleteTask = async (taskId) => {
  if (!confirm('⚠️ Are you sure you want to delete this task? This action cannot be undone.')) return

  await makeRequest(`${taskAPI}tasks/${taskId}`, {
    method: 'DELETE'
  })

  showNotification('success', 'Task deleted successfully!')
  await getAllTasks()
}

const editTask = (task) => {
  editModal.value = {
    show: true,
    type: 'task',
    id: task.taskId,
    data: { ...task },
    deadlineDate: epochToDateTime(task.deadline)
  }
  // Note: We don't populate existing attachments since they're base64 strings
  // and we can't reconstruct file objects from them
  editAttachments.value = []
}

// Subtask CRUD Operations
const createSubtask = async () => {
  const subtaskData = {
    title: newSubtask.value.title,
    taskId: newSubtask.value.taskId,
    creatorId: authStore.user.uid,
    deadline: dateTimeToEpoch(newSubtask.value.deadlineDate),
    status: newSubtask.value.status,
    notes: newSubtask.value.notes,
    ownerId: newSubtask.value.ownerId || authStore.user.uid,
    collaborators: parseCollaborators(subtaskCollaboratorsInput.value),
    attachments: subtaskAttachments.value.map(file => file.base64)
  }

  const response = await makeRequest(`${subtaskAPI}subtasks`, {
    method: 'POST',
    body: JSON.stringify(subtaskData)
  })

  showNotification('success', 'SubTask created successfully!')
  clearSubtaskForm()
  await getAllSubtasks()
}

const getAllSubtasks = async () => {
  const response = await makeRequest(`${subtaskAPI}subtasks`)
  subtasks.value = response.subtasks || []
}

const deleteSubtask = async (subtaskId) => {
  if (!confirm('⚠️ Are you sure you want to delete this subtask? This action cannot be undone.')) return

  await makeRequest(`${subtaskAPI}subtasks/${subtaskId}`, {
    method: 'DELETE'
  })

  showNotification('success', 'SubTask deleted successfully!')
  await getAllSubtasks()
}

const editSubtask = (subtask) => {
  editModal.value = {
    show: true,
    type: 'subtask',
    id: subtask.subTaskId,
    data: { ...subtask },
    deadlineDate: epochToDateTime(subtask.deadline)
  }
  // Note: We don't populate existing attachments since they're base64 strings
  // and we can't reconstruct file objects from them
  editAttachments.value = []
}

const getTaskSubtasks = async (taskId) => {
  const response = await makeRequest(`${subtaskAPI}subtasks/task/${taskId}`)
  subtasks.value = response.subtasks || []
  activeTab.value = 'subtasks'
  showNotification('success', `Found ${response.subtasks.length} subtasks for this task`)
}

// Edit modal functions
async function saveEdit(updatedTask) {
  try {
    // Determine if it's a task or subtask update
    const isTask = editModal.value.type === 'task';
    const apiUrl = isTask
      ? `${taskAPI}tasks/${editModal.value.id}`
      : `${subtaskAPI}subtasks/${editModal.value.id}`;

    // Use the data as-is since the component already converted datetime to epoch
    const updateData = {
      ...updatedTask
      // ✅ No need to convert deadline - component already did this
    };

    // Make the API call
    await makeRequest(apiUrl, {
      method: 'PUT',
      body: JSON.stringify(updateData)
    });

    // Show success message
    showNotification('success', `${isTask ? 'Task' : 'SubTask'} updated successfully!`);

    // Refresh data and close modal
    if (isTask) {
      await getAllTasks();
    } else {
      await getAllSubtasks();
    }

    closeEditModal();
  } catch (error) {
    console.error('Error updating:', error);
    showNotification('error', 'Failed to update. Please try again.');
  }
}


function closeEditModal() {
  editModal.value.show = false;
}




// Tab switching
const switchTab = async (tab) => {
  activeTab.value = tab
  if (tab === 'tasks' && tasks.value.length === 0) {
    await getAllTasks()
  } else if (tab === 'subtasks' && subtasks.value.length === 0) {
    await getAllSubtasks()
  }
}

// Initialize
onMounted(async () => {
  if (authStore.isAuthenticated) {
    await getAllTasks()
    // Set default deadline to tomorrow
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    tomorrow.setHours(9, 0, 0, 0) // 9 AM tomorrow
    newTask.value.deadlineDate = tomorrow.toISOString().slice(0, 16)
    newSubtask.value.deadlineDate = tomorrow.toISOString().slice(0, 16)
  }
})
</script>

<style scoped>
/* Base Styles */
.test-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

/* Header */
.header {
  text-align: center;
  margin-bottom: 32px;
  padding: 32px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.header h1 {
  font-size: 2.5rem;
  font-weight: 800;
  color: #1a202c;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
  margin: 0 0 24px 0;
}

.user-info {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 12px 20px;
  border-radius: 50px;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

.user-avatar {
  font-size: 1.5rem;
}

.user-name {
  font-weight: 600;
  font-size: 0.95rem;
}

.user-role {
  font-size: 0.8rem;
  opacity: 0.9;
}

.auth-warning {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #fff3cd;
  color: #856404;
  padding: 12px 20px;
  border-radius: 8px;
  border: 1px solid #ffeaa7;
}

/* Login Prompt */
.login-prompt {
  text-align: center;
  padding: 60px 40px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.login-content h2 {
  color: #1a202c;
  margin-bottom: 16px;
}

.login-content p {
  color: #666;
  margin-bottom: 24px;
  font-size: 1.1rem;
}

/* Main Content */
.main-content {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* Notifications */
.notification {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  margin: 0 24px 24px 24px;
  border-radius: 8px;
  font-weight: 500;
  animation: slideDown 0.3s ease-out;
}

.notification.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.notification.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.notification-close {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
}

.notification-close:hover {
  opacity: 1;
}

/* Tabs */
.tabs {
  display: flex;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  color: #64748b;
  border-bottom: 3px solid transparent;
  transition: all 0.2s ease;
  position: relative;
}

.tab-btn:hover {
  background: #e2e8f0;
  color: #334155;
}

.tab-btn.active {
  color: #667eea;
  border-bottom-color: #667eea;
  background: white;
}

.tab-icon {
  font-size: 1.1rem;
}

.tab-count {
  background: #667eea;
  color: white;
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

/* Sections */
.create-section,
.list-section {
  padding: 32px;
}

.create-section {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
}

.section-icon {
  font-size: 1.3rem;
}

.count-badge {
  background: #667eea;
  color: white;
  font-size: 0.8rem;
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* Forms */
.create-form,
.modal-form {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group.flex-1 {
  flex: 1;
}

.form-group.flex-2 {
  flex: 2;
}

.form-group.full-width {
  width: 100%;
}

.form-label {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.form-label.required::after {
  content: ' *';
  color: #ef4444;
}

.form-input,
.form-textarea {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s ease;
  background: white;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.char-count {
  font-size: 0.75rem;
  color: #9ca3af;
  text-align: right;
}

.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
}

.form-hint.warning {
  color: #d97706;
  font-weight: 500;
}

.datetime-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-dates {
  display: flex;
  gap: 6px;
}

.quick-btn {
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s ease;
}

.quick-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.form-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-small {
  padding: 6px 12px;
  font-size: 0.75rem;
}

.btn-large {
  padding: 14px 24px;
  font-size: 1rem;
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

.btn-outline {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-outline:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #9ca3af;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-info {
  background: #06b6d4;
  color: white;
}

.btn-info:hover:not(:disabled) {
  background: #0891b2;
}

/* Loading Spinners */
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-small {
  width: 12px;
  height: 12px;
  border: 1px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Empty States */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
}

.empty-state p {
  margin: 0;
  font-size: 0.875rem;
}

/* Cards Grid */
.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 20px;
}

.task-card,
.subtask-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.task-card:hover,
.subtask-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: #d1d5db;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 20px 20px 16px 20px;
  border-bottom: 1px solid #f3f4f6;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  line-height: 1.4;
  flex: 1;
}

.status-badge {
  padding: 6px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.status-badge.ongoing {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.unassigned {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.under_review {
  background: #e0e7ff;
  color: #5b21b6;
}

.status-badge.completed {
  background: #d1fae5;
  color: #065f46;
}

.card-content {
  padding: 0 20px 16px 20px;
}

.parent-task {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 8px 12px;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 0.8rem;
}

.parent-label {
  font-weight: 500;
  color: #6b7280;
}

.parent-value {
  color: #374151;
}

.card-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
}

.meta-label {
  font-weight: 500;
  color: #6b7280;
  min-width: 80px;
}

.meta-value {
  color: #374151;
}

.meta-value.overdue {
  color: #dc2626;
  font-weight: 600;
}

.card-notes {
  margin-bottom: 16px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.card-notes p {
  margin: 0;
  font-size: 0.875rem;
  color: #374151;
  line-height: 1.5;
}

.card-timestamps {
  display: flex;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
  font-size: 0.75rem;
  color: #9ca3af;
}

.card-actions {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  background: #f9fafb;
  border-top: 1px solid #f3f4f6;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
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
  animation: modalSlideIn 0.3s ease-out;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 24px 0 24px;
  margin-bottom: 20px;
}

.modal-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #9ca3af;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #6b7280;
}

.modal-form {
  padding: 0 24px 24px 24px;
  background: transparent;
  box-shadow: none;
}

.modal-form .form-group {
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f3f4f6;
}

/* Response Logger */
.response-logger {
  margin: 32px;
  background: #1f2937;
  border-radius: 12px;
  overflow: hidden;
}

.logger-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #374151;
  border-bottom: 1px solid #4b5563;
}

.logger-header h3 {
  color: white;
  margin: 0;
  font-size: 1rem;
}

.response-container {
  background: #1f2937;
}

.response-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: #374151;
  border-bottom: 1px solid #4b5563;
  flex-wrap: wrap;
}

.method-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
}

.method-badge.GET {
  background: #10b981;
}

.method-badge.POST {
  background: #3b82f6;
}

.method-badge.PUT {
  background: #f59e0b;
}

.method-badge.DELETE {
  background: #ef4444;
}

.url-text {
  font-family: 'Fira Code', monospace;
  font-size: 0.75rem;
  color: #d1d5db;
  flex: 1;
  word-break: break-all;
}

.status-badge.success {
  background: #10b981;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.error {
  background: #ef4444;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.timestamp {
  font-size: 0.75rem;
  color: #9ca3af;
}

.response-body {
  margin: 0;
  padding: 20px;
  background: #111827;
  color: #f3f4f6;
  font-family: 'Fira Code', monospace;
  font-size: 0.75rem;
  line-height: 1.6;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

/* Animations */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }

  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* File Upload Styles */
.file-upload-area {
  position: relative;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  transition: all 0.2s ease;
  overflow: hidden;
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

.file-upload-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
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
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.file-remove:hover {
  background: #dc2626;
  transform: scale(1.1);
}

/* Responsive Design */
@media (max-width: 768px) {
  .test-container {
    padding: 16px;
  }

  .header {
    padding: 20px;
  }

  .header h1 {
    font-size: 2rem;
  }

  .create-section,
  .list-section {
    padding: 20px;
  }

  .form-row {
    flex-direction: column;
    gap: 16px;
  }

  .form-group.flex-1,
  .form-group.flex-2 {
    flex: none;
  }

  .items-grid {
    grid-template-columns: 1fr;
  }

  .card-actions {
    flex-wrap: wrap;
  }

  .modal {
    width: 95%;
    margin: 20px;
  }

  .response-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
  }

  .tabs {
    flex-direction: column;
  }

  .tab-btn {
    justify-content: center;
  }

  .file-upload-content {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }

  .file-info {
    gap: 8px;
  }

  .file-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .file-remove {
    align-self: flex-end;
  }
}
</style>
