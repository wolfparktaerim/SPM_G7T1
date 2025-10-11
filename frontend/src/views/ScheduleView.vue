<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
    <NavigationBar />

    <!-- 🧭 Page Header -->
    <div class="bg-white/70 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 tracking-tight">Schedule</h1>
            <p class="text-gray-600 mt-1">
              {{ viewingUserId === currentUser
                ? 'View and manage your schedule'
                : `Viewing ${getUserDisplayName(viewingUserId)}'s schedule` }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 🧭 Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <!-- 🧭 Sidebar Filters -->
        <div class="lg:col-span-1">
          <div
            class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 space-y-6 sticky top-24"
          >
            <h3 class="text-lg font-bold text-gray-900 mb-4">Filter Schedule</h3>

            <!-- 👤 Viewing User -->
            <div class="mb-4 p-3 bg-blue-50 rounded-lg">
              <p class="text-xs text-gray-600 mb-1">Currently viewing:</p>
              <p class="text-sm font-semibold text-gray-900">
                {{ viewingUserId === currentUser ? 'Your Schedule' : getUserDisplayName(viewingUserId) }}
              </p>
            </div>

            <!-- 🏢 Department (Directors only) -->
            <div v-if="isDirector" class="pt-2 border-t border-blue-200">
              <p class="text-sm font-medium text-gray-600 mb-1">Department:</p>
              <p class="text-sm font-semibold text-blue-700">
                {{ currentUserDepartment || 'N/A' }}
              </p>
            </div>

            <!-- 📁 Project Filter -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Select Project</label>
              <select
                v-model="selectedProjectId"
                @change="onProjectSelect($event.target.value)"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option :value="null">Select Project</option>
                <option v-for="p in userProjects" :key="p.projectId" :value="p.projectId">
                  {{ p.title }}
                </option>
              </select>
            </div>

            <!-- 👥 Collaborator Filter -->
            <div v-if="selectedProject && projectCollaborators.length" class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">View Team Member</label>
              <select
                v-model="selectedCollaborator"
                @change="onCollaboratorSelect($event.target.value)"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option :value="null">Select a team member</option>
                <option
                  v-for="c in projectCollaborators"
                  :key="c.uid"
                  :value="c.uid"
                >
                  {{ c.name }} {{ c.isCurrentUser ? '(You)' : '' }} {{ c.isOwner ? '👑' : '' }}
                </option>
              </select>
              <p class="text-xs text-gray-500 mt-1">
                {{ projectCollaborators.length }} member{{ projectCollaborators.length !== 1 ? 's' : '' }}
              </p>
            </div>

            <!-- 🔄 Reset -->
            <button
              v-if="selectedProject || selectedCollaborator"
              @click="resetFilters"
              class="w-full px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-all"
            >
              Reset Filters
            </button>
          </div>
        </div>

        <!-- 📅 Calendar -->
        <div class="lg:col-span-3">
          <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
            <FullCalendar :options="calendarOptions" />

            <!-- 🧭 Legend -->
            <div class="flex flex-wrap gap-3 mt-4 text-sm">
              <div v-for="(color, label) in statusColors" :key="label" class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full" :style="{ backgroundColor: color }"></span>
                <span class="capitalize">{{ label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 🧭 Task Detail Modal -->
    <transition name="fade">
      <div
        v-if="showTaskDetailModal"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="closeTaskDetailModal"
      >
        <div class="flex items-center justify-center min-h-screen px-4 py-6">
          <transition name="scale">
            <div
              v-if="showTaskDetailModal"
              class="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl transform transition-all"
              @click.stop
            >
              <!-- Header -->
              <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-start">
                <div>
                  <h3 class="text-xl font-bold text-gray-900 mb-3">
                    {{ selectedTaskDetail?.title || 'Task Details' }}
                  </h3>
                  <div class="flex items-center gap-2 flex-wrap">
                    <span
                      v-if="selectedTaskDetail?.status"
                      :class="getStatusBadgeClass(selectedTaskDetail.status)" 
                      class="px-3 py-1 rounded-full text-xs font-semibold"
                      >
                      ● {{ selectedTaskDetail.status}}
                    </span>
                    <span
                      v-if="isTaskOwner(selectedTaskDetail)"
                      class="px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700"
                    >
                      <Crown class="w-3 h-3 inline-block mr-1" /> Owner
                    </span>
                    <span
                      v-if="getDueSoonBadge(selectedTaskDetail)"
                      :class="getDueSoonBadge(selectedTaskDetail).class"
                      class="px-3 py-1 rounded-full text-xs font-semibold"
                    >
                      {{ getDueSoonBadge(selectedTaskDetail).text }}
                    </span>
                  </div>
                </div>

                <div class="flex items-center gap-2">
                  <button
                    v-if="isTaskOwner(selectedTaskDetail)"
                    @click="handleEditTask(selectedTaskDetail)"
                    class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                    title="Edit Task"
                  >
                    <Edit3 class="w-5 h-5" />
                  </button>
                  <button
                    @click="closeTaskDetailModal"
                    class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    <X class="w-5 h-5" />
                  </button>
                </div>
              </div>

              <!-- Body -->
              <div class="px-6 py-6 space-y-6 max-h-[60vh] overflow-y-auto">
                <!-- 📋 Basic Info -->
                <div>
                  <h4 class="text-sm font-semibold text-gray-900 mb-4">Basic Information</h4>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div class="flex items-center gap-2 text-sm text-gray-600 mb-1">
                        <Calendar class="w-4 h-4" />
                        <span class="font-medium">Deadline</span>
                      </div>
                      <p class="text-sm text-gray-900 ml-6">
                        {{ formatDateDisplay(selectedTaskDetail?.deadline) }}
                      </p>
                    </div>
                    <div>
                      <div class="flex items-center gap-2 text-sm text-gray-600 mb-1">
                        <User class="w-4 h-4" />
                        <span class="font-medium">Owner</span>
                      </div>
                      <div class="flex items-center gap-2 ml-6">
                        <p class="text-sm text-gray-900">
                          {{ getUserDisplayName(selectedTaskDetail?.ownerId) }}
                        </p>
                        <span
                          v-if="selectedTaskDetail?.ownerId === currentUser"
                          class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium"
                          >You</span
                        >
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 👥 Collaborators -->
                <div v-if="selectedTaskDetail?.collaborators?.length">
                  <h4 class="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <Users class="w-4 h-4" />
                    Collaborators ({{ selectedTaskDetail.collaborators.length }})
                  </h4>
                  <div class="space-y-2">
                    <div
                      v-for="id in selectedTaskDetail.collaborators"
                      :key="id"
                      class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                    >
                      <div
                        class="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-semibold text-sm"
                      >
                        {{ getUserDisplayName(id).charAt(0).toUpperCase() }}
                      </div>
                      <div class="flex-1">
                        <p class="text-sm font-medium text-gray-900">{{ getUserDisplayName(id) }}</p>
                        <p class="text-xs text-gray-600">{{ usersMap[id]?.role || 'Collaborator' }}</p>
                      </div>
                      <span
                        v-if="id === currentUser"
                        class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium"
                        >You</span
                      >
                    </div>
                  </div>
                </div>

                <!-- 📝 Notes -->
                <div v-if="selectedTaskDetail?.notes">
                  <h4 class="text-sm font-semibold text-gray-900 mb-2">Notes</h4>
                  <p class="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-3 rounded-lg">
                    {{ selectedTaskDetail.notes }}
                  </p>
                </div>

                <!-- ✅ NEW: Subtasks Section -->
                <div v-if="selectedTaskDetail?.subtasks && selectedTaskDetail.subtasks.length > 0">
                  <h4 class="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <ListChecks class="w-4 h-4" />
                    Subtasks ({{ selectedTaskDetail.subtasks.length }})
                  </h4>
                  <div class="space-y-2">
                    <div
                      v-for="subtask in selectedTaskDetail.subtasks"
                      :key="subtask.subTaskId"
                      class="group bg-gray-50 hover:bg-white border border-gray-200 hover:border-blue-300 rounded-lg p-3 transition-all"
                    >
                      <div class="flex items-start justify-between gap-3">
                        <!-- Subtask Info -->
                        <div class="flex-1 min-w-0">
                          <div class="flex items-center gap-2 mb-2">
                            <h5 class="text-sm font-medium text-gray-900 truncate">{{ subtask.title }}</h5>
                            
                            <!-- Status Badge -->
                            <span 
                              :class="getStatusBadgeClass(subtask.status)" 
                              class="text-xs px-2 py-0.5 rounded-full whitespace-nowrap"
                            >
                              ● {{ subtask.status }}
                            </span>
                          </div>
                          
                          <!-- Subtask Meta Info -->
                          <div class="flex flex-wrap items-center gap-3 text-xs text-gray-600">
                            <!-- Owner -->
                            <div class="flex items-center gap-1">
                              <User class="w-3 h-3" />
                              <span>{{ getUserDisplayName(subtask.ownerId) }}</span>
                              <span 
                                v-if="subtask.ownerId === currentUser" 
                                class="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium"
                              >
                                You
                              </span>
                            </div>
                            
                            <!-- Deadline -->
                            <div class="flex items-center gap-1">
                              <Calendar class="w-3 h-3" />
                              <span>{{ formatDateDisplay(subtask.deadline) }}</span>
                            </div>
                            
                            <!-- Due Soon Badge -->
                            <span 
                              v-if="getDueSoonBadge(subtask)" 
                              :class="getDueSoonBadge(subtask).class"
                              class="px-2 py-0.5 rounded-full text-xs font-semibold"
                            >
                              {{ getDueSoonBadge(subtask).text }}
                            </span>
                          </div>
                        </div>

                        <!-- Owner Badge for Subtask -->
                        <div v-if="isTaskOwner(subtask)" class="flex-shrink-0">
                          <span class="px-2 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700">
                            <Crown class="w-3 h-3 inline-block" /> Owner
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Footer -->
              <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end rounded-b-2xl">
                <button
                  @click="closeTaskDetailModal"
                  class="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </transition>

    <!-- 🔔 Toast -->
    <transition name="fade">
      <div
        v-if="showNotification"
        class="fixed bottom-8 right-8 z-50 bg-gray-900 text-white px-6 py-4 rounded-lg shadow-xl flex items-center gap-3"
      >
        <span>{{ notificationMessage }}</span>
        <button @click="showNotification = false" class="text-gray-400 hover:text-white">
          <X class="w-4 h-4" />
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { auth } from '@/firebase/firebaseConfig';
import { onAuthStateChanged } from 'firebase/auth';
import NavigationBar from '@/components/NavigationBar.vue';
import { usersService } from '@/services/users';
import { X, Edit3, Trash2, Calendar, User, Crown, Users, ListChecks } from 'lucide-vue-next';

// --- FullCalendar imports ---
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';

// --- Setup ---
const router = useRouter();
const KONG_BASE = import.meta.env.VITE_BACKEND_API || 'http://localhost:8000/';
const API_BASE = `${KONG_BASE}tasks`;
const PROJECT_API_BASE = `${import.meta.env.VITE_BACKEND_API}project`;
const SUBTASKAPI = `${KONG_BASE}subtasks`

// --- State ---
const currentUser = ref(null);
const currentRole = ref('');
const currentUserDepartment = ref('');
const loading = ref(true);

const allTasks = ref([]);
const filteredTasks = ref([]);
const allUsers = ref([]);
const usersMap = ref({});

const showTaskDetailModal = ref(false);
const selectedTaskDetail = ref(null);

const userProjects = ref([]);
const selectedProject = ref(null);
const selectedProjectId = ref(null);
const projectCollaborators = ref([]);
const selectedCollaborator = ref(null);
const viewingUserId = ref(null);

const showNotification = ref(false);
const notificationMessage = ref('');

// --- Status Colors (Unified) ---
const statusColors = {
  unassigned:    '#d1d5db', // gray
  ongoing:       '#1945e6', // blue
  'under_review':'#f59e0b', // orange
  completed:     '#3BB143', // green
  overdue:       '#ff0009'  // red
};

// --- Computed: Calendar Events ---
const calendarEvents = computed(() => {
  return filteredTasks.value.map(task => {
    if (!task.deadline) return null;

    // Convert deadline to Date
    const deadlineDate = typeof task.deadline === 'number'
      ? new Date(task.deadline * 1000)
      : new Date(task.deadline);

    // Determine start date (today or creation date)
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const startDate = task.createdAt
      ? new Date(task.createdAt * 1000)
      : today;

    // Format YYYY-MM-DD
    const formatDate = (d) =>
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

    const startStr = formatDate(startDate);
    const endStr = formatDate(new Date(deadlineDate.getTime() + 86400000));

    const deadlineOnly = new Date(deadlineDate);
    deadlineOnly.setHours(0, 0, 0, 0);
    const isOverdue = deadlineOnly < today && task.status?.toLowerCase() !== 'completed';

    const status = isOverdue ? 'overdue' : (task.status || 'unassigned').toLowerCase();
    const color = statusColors[status] || statusColors.unassigned;
    const isViewable = canViewTaskDetails(task);

    // Days until deadline
    const daysUntilDeadline = Math.ceil((deadlineDate - today) / (1000 * 60 * 60 * 24));

    return {
      id: task.taskId,
      title: task.title,
      start: startStr,
      end: endStr,
      allDay: true,
      backgroundColor: color,
      borderColor: color,
      classNames: isViewable ? 'cursor-pointer' : 'cursor-not-allowed opacity-60',
      extendedProps: { ...task, daysUntilDeadline, isViewable }
    };
  }).filter(Boolean);
});

const isDirector = computed(() => {
  return currentRole.value?.toLowerCase() === 'director';
});

// --- Calendar Config ---
const calendarOptions = ref({
  plugins: [dayGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,dayGridWeek,dayGridDay'
  },
  editable: true,
  selectable: true,
  dayMaxEvents: true,
  weekends: true,
  events: calendarEvents,

  eventContent(info) {
    return {
      html: `
        <div style="
          display: flex; align-items: center; gap: 4px;
          font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        ">
          <span>${info.event.title}</span>
        </div>
      `
    };
  },

  dayCellDidMount(info) {
    const cellDate = info.date.toISOString().split('T')[0];
    const dayEvents = calendarEvents.value?.filter(e => e.start.startsWith(cellDate)) || [];
    if (!dayEvents.length) return;

    const priority = ['overdue', 'ongoing', 'under review', 'completed', 'unassigned'];
    const matchedStatus = priority.find(s =>
      dayEvents.some(e => e.extendedProps.status?.toLowerCase() === s)
    );
    const color = statusColors[matchedStatus];
    if (color) {
      info.el.style.borderRadius = '8px';
      info.el.style.transition = 'background-color 0.3s ease';
      info.el.style.background = `linear-gradient(${color}55, ${color}55)`;
      info.el.style.boxShadow = `inset 0 0 0 2px ${color}`;
    }
  },

  eventClick(info) {
    const task = filteredTasks.value.find(t => t.taskId === info.event.id);
    if (!task) return;
    if (!canViewTaskDetails(task)) return showToast('🔒 You do not have permission to view this task');
    openTaskDetailModal(task);
  }
});

// --- Utility Functions ---
function showToast(msg) {
  notificationMessage.value = msg;
  showNotification.value = true;
  setTimeout(() => (showNotification.value = false), 3000);
}

async function openTaskDetailModal(task) {
  // Load subtasks for the task
  const subtasks = await fetchTaskSubtasks(task.taskId)
  selectedTaskDetail.value = {
    ...task,
    subtasks
  }
  showTaskDetailModal.value = true
}

function closeTaskDetailModal() {
  selectedTaskDetail.value = null;
  showTaskDetailModal.value = false;
}

function canViewTaskDetails(task) {
  if (!task) return false;
  if (currentRole.value?.toLowerCase() === 'director') return true;
  return task.collaborators?.includes(currentUser.value);
}

function filterTasksByUser(userId) {
  filteredTasks.value = allTasks.value.filter(t => t.collaborators?.includes(userId));
}

function getUserDisplayName(userId) {
  if (!userId) return 'Unassigned';
  if (userId === currentUser.value) return 'You';
  const user = usersMap.value[userId];
  return user ? (user.name || user.displayName || user.email) : 'Unknown User';
}

function getDueSoonBadge(task) {
  if (task?.status?.toLowerCase() === 'completed') return null;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const deadline = new Date(task.deadline * 1000); deadline.setHours(0, 0, 0, 0);
  const diff = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
  if (diff < 0) return { text: 'Overdue', class: 'bg-red-100 text-red-700' };
  if (diff === 0) return { text: 'Due Today', class: 'bg-orange-100 text-orange-700' };
  if (diff <= 3) return { text: `Due in ${diff} days`, class: 'bg-orange-100 text-orange-700' };
  return null;
}

function isTaskOwner(task) {
  return task.ownerId === currentUser.value;
}

function formatDateDisplay(epochTimestamp) {
  if (!epochTimestamp) return 'No deadline';
  const date = new Date(epochTimestamp * 1000);
  return date.toLocaleDateString('en-US', { 
    month: 'long', 
    day: 'numeric', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function resetFilters() {
selectedProject.value = null;
selectedProjectId.value = null;
projectCollaborators.value = [];
selectedCollaborator.value = null;
viewingUserId.value = currentUser.value;
filterTasksByUser(currentUser.value);
}

function getStatusBadgeClass(status) {
  const statusLower = (status || '').toLowerCase();
  if (statusLower === 'completed') return 'bg-green-100 text-green-700';
  if (statusLower === 'ongoing') return 'bg-blue-100 text-blue-700';
  if (statusLower === 'under_review') return 'bg-yellow-100 text-yellow-700';
  if (statusLower === 'unassigned') return 'bg-gray-100 text-gray-700';
  return 'bg-gray-100 text-gray-700';
}

function handleEditTask(task) {
  closeTaskDetailModal();
  // Navigate to Tasks page with taskId as query parameter
  router.push({ 
      name: 'tasks', 
      query: { 
        taskId: task.taskId,
        action: 'edit' // Optional: indicates intent to edit
      }
  });
}


// --- Fetching ---
async function fetchAllTasks() {
  try {
    const res = await fetch(API_BASE);
    if (!res.ok) throw new Error('Failed to fetch tasks');
    const data = await res.json();
    allTasks.value = data.tasks || [];
  } catch (err) {
    console.error('Error fetching tasks:', err);
    allTasks.value = [];
  }
}

async function fetchAllUsers() {
  try {
    const users = await usersService.getAllUsers();
    allUsers.value = users;
    usersMap.value = Object.fromEntries(users.map(u => [u.uid, u]));
  } catch (err) {
    console.error('Error fetching users:', err);
  }
}

async function fetchUserProjects() {
  if (!currentUser.value) return;
  try {
    const url = currentRole.value?.toLowerCase() === 'director'
      ? `${PROJECT_API_BASE}/department/${currentUserDepartment.value}`
      : `${PROJECT_API_BASE}/${currentUser.value}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch projects');
    const data = await res.json();
    userProjects.value = data.projects || [];
  } catch (err) {
    console.error('Error fetching user projects:', err);
    userProjects.value = [];
  }
}

async function fetchTaskSubtasks(taskId) {
  try {
    const res = await fetch(`${SUBTASKAPI}/task/${taskId}`)
    if (!res.ok) throw new Error('Failed to fetch subtasks')
    const data = await res.json()
    return data.subtasks || []
  } catch (err) {
    console.error('Error fetching subtasks:', err)
    return []
  }
}

// --- Handlers ---
async function onProjectSelect(projectId) {
  if (!projectId) {
    selectedProject.value = null;
    projectCollaborators.value = [];
    selectedCollaborator.value = null;
    viewingUserId.value = currentUser.value;
    filterTasksByUser(currentUser.value);
    return;
  }

  const project = userProjects.value.find(p => p.projectId === projectId);
  selectedProject.value = project;
  selectedProjectId.value = projectId;

  const ids = new Set([project.ownerId, ...(project.collaborators || [])]);
  projectCollaborators.value = Array.from(ids)
    .map(uid => {
      const u = usersMap.value[uid];
      return {
        uid,
        name: u ? (u.name || u.displayName || u.email) : 'Unknown User',
        isCurrentUser: uid === currentUser.value,
        isOwner: uid === project.ownerId
      };
    })
    .sort((a, b) => a.isCurrentUser ? -1 : b.isCurrentUser ? 1 :
                   a.isOwner ? -1 : b.isOwner ? 1 :
                   a.name.localeCompare(b.name));
}

function onCollaboratorSelect(uid) {
  selectedCollaborator.value = uid;
  viewingUserId.value = uid || currentUser.value;
  filterTasksByUser(viewingUserId.value);
}

// --- Lifecycle ---
onMounted(() => {
  onAuthStateChanged(auth, async user => {
    if (!user) return router.push('/authentication');
    currentUser.value = viewingUserId.value = user.uid;

    try {
      const info = await usersService.getUserById(user.uid);
      currentRole.value = info.role;
      currentUserDepartment.value = info.department || '';
      await Promise.all([fetchAllUsers(), fetchAllTasks(), fetchUserProjects()]);
      filterTasksByUser(user.uid);
    } catch (err) {
      console.error('Failed to load user info or tasks:', err);
    } finally {
      loading.value = false;
    }
  });
});
</script>

<style scoped>
   /* FullCalendar custom styling */
   :deep(.fc) {
   /* Override FullCalendar default styles to match your design */
   font-family: inherit;
   }
   :deep(.fc .fc-button) {
   background-color: #3b82f6;
   border-color: #3b82f6;
   text-transform: capitalize;
   font-weight: 600;
   padding: 0.5rem 1rem;
   border-radius: 0.5rem;
   transition: all 0.2s;
   }
   :deep(.fc .fc-button:hover) {
   background-color: #2563eb;
   border-color: #2563eb;
   }
   :deep(.fc .fc-button-active) {
   background-color: #1e40af !important;
   border-color: #1e40af !important;
   }
   :deep(.fc-theme-standard .fc-scrollgrid) {
   border-color: #e5e7eb;
   }
   :deep(.fc-theme-standard td, .fc-theme-standard th) {
   border-color: #e5e7eb;
   }
   :deep(.fc .fc-daygrid-day-number) {
   color: #374151;
   font-weight: 600;
   }
   :deep(.fc .fc-col-header-cell-cushion) {
   color: #6b7280;
   font-weight: 700;
   text-transform: uppercase;
   font-size: 0.75rem;
   padding: 0.75rem 0;
   }
   :deep(.fc .fc-event) {
   border-radius: 0.375rem;
   padding: 0.25rem 0.5rem;
   font-weight: 500;
   font-size: 0.875rem;
   cursor: pointer;
   transition: transform 0.2s;
   }
   :deep(.fc .fc-event:hover) {
   transform: scale(1.02);
   }
   :deep(.fc-daygrid-day.fc-day-today) {
   background-color: rgba(59, 130, 246, 0.05) !important;
   }
   /* Modal transitions */
   .fade-enter-active, .fade-leave-active {
   transition: opacity 0.3s ease;
   }
   .fade-enter-from, .fade-leave-to {
   opacity: 0;
   }
   .scale-enter-active, .scale-leave-active {
   transition: all 0.3s ease;
   }
   .scale-enter-from, .scale-leave-to {
   opacity: 0;
   transform: scale(0.9);
   }
</style>
