<template>
   <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <NavigationBar />
      <!-- Page Header -->
      <div class="bg-white/70 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-10">
         <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
               <div>
                  <h1 class="text-3xl font-bold text-gray-900 tracking-tight">Schedule</h1>
                  <p class="text-gray-600 mt-1">{{ viewingUserId === currentUser ? 'View and manage your schedule' : `Viewing ${getUserDisplayName(viewingUserId)}'s schedule` }}</p>
               </div>
            </div>
         </div>
      </div>
      <!-- Main Content -->
      <!-- Main Content with Sidebar -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
         <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <!-- Sidebar Filters -->
            <div class="lg:col-span-1">
               <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 space-y-6 sticky top-24">
                  <div>
                     <h3 class="text-lg font-bold text-gray-900 mb-4">Filter Schedule</h3>
                     <!-- Viewing User Info -->
                     <div class="mb-4 p-3 bg-blue-50 rounded-lg">
                        <p class="text-xs text-gray-600 mb-1">Currently viewing:</p>
                        <p class="text-sm font-semibold text-gray-900">
                           {{ viewingUserId === currentUser ? 'Your Schedule' : getUserDisplayName(viewingUserId) }}
                        </p>
                     </div>
                     <!-- Show role context for directors -->
                     <div v-if="currentRole?.toLowerCase() === 'director'" class="pt-2 border-t border-blue-200">
                        <p class="text-xs text-gray-600 mb-1">Department:</p>
                        <p class="text-xs font-semibold text-blue-700">
                           {{ currentUserDepartment || 'N/A' }}
                        </p>
                     </div>
                     <!-- Project Dropdown -->
                     <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                        Select Project
                        </label>
                        <select 
                           v-model="selectedProjectId"
                           @change="onProjectSelect($event.target.value)"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                           >
                           <option :value="null">All Projects</option>
                           <option 
                              v-for="project in userProjects" 
                              :key="project.projectId" 
                              :value="project.projectId"
                              >
                              {{ project.title }}
                           </option>
                        </select>
                     </div>
                     <!-- Collaborator Dropdown (only shown when project is selected) -->
                     <div v-if="selectedProject && projectCollaborators.length > 0" class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                        View Team Member's Schedule
                        </label>
                        <select 
                           v-model="selectedCollaborator"
                           @change="onCollaboratorSelect($event.target.value)"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                           >
                           <option :value="null">Select a team member</option>
                           <option 
                              v-for="collaborator in projectCollaborators" 
                              :key="collaborator.uid" 
                              :value="collaborator.uid"
                              >
                              {{ collaborator.name }}
                              {{ collaborator.isCurrentUser ? ' (You)' : '' }}
                              {{ collaborator.isOwner ? ' 👑' : '' }}
                           </option>
                        </select>
                        <p class="text-xs text-gray-500 mt-1">
                           {{ projectCollaborators.length }} team member{{ projectCollaborators.length !== 1 ? 's' : '' }} in this project
                        </p>
                     </div>
                     <!-- Reset Button -->
                     <button 
                        v-if="selectedProject || selectedCollaborator"
                        @click="resetFilters"
                        class="w-full px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-all"
                        >
                     Reset Filters
                     </button>
                  </div>
               </div>
            </div>
            <!-- Calendar Container -->
            <div class="lg:col-span-3">
               <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
                  <FullCalendar :options="calendarOptions" />
               </div>
            </div>
         </div>
      </div>
      <!-- Task Detail Modal -->
      <transition name="fade">
         <div v-if="showTaskDetailModal" class="fixed inset-0 z-50 overflow-y-auto" @click.self="closeTaskDetailModal">
            <div class="flex items-center justify-center min-h-screen px-4 py-6">
               <!-- Modal panel -->
               <transition name="scale">
                  <div 
                     v-if="showTaskDetailModal"
                     class="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl transform transition-all"
                     @click.stop
                     >
                     <!-- Header -->
                     <div class="px-6 py-4 border-b border-gray-200">
                        <div class="flex items-start justify-between">
                           <div class="flex-1 pr-4">
                              <h3 class="text-xl font-bold text-gray-900 mb-3">
                                 {{ selectedTaskDetail?.title || 'Task Details' }}
                              </h3>
                              <div class="flex items-center gap-2 flex-wrap">
                                 <!-- Status Badge -->
                                 <span 
                                    v-if="selectedTaskDetail?.status"
                                    :class="getStatusBadgeClass(selectedTaskDetail.status)" 
                                    class="px-3 py-1 rounded-full text-xs font-semibold"
                                    >
                                 <span class="mr-1">●</span>{{ formatStatus(selectedTaskDetail.status) }}
                                 </span>
                                 <!-- Owner Badge -->
                                 <span v-if="isTaskOwner(selectedTaskDetail)" class="px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700">
                                    <Crown class="w-3 h-3 inline-block mr-1" />
                                    Owner
                                 </span>
                                 <!-- Due Soon Badge -->
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
                              <!-- Edit Button (only if owner) -->
                              <button 
                                 v-if="isTaskOwner(selectedTaskDetail)"
                                 @click="handleEditTask(selectedTaskDetail)"
                                 class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                                 title="Edit Task"
                                 >
                                 <Edit3 class="w-5 h-5" />
                              </button>
                              <!-- Close Button -->
                              <button 
                                 @click="closeTaskDetailModal"
                                 class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all"
                                 >
                                 <X class="w-5 h-5" />
                              </button>
                           </div>
                        </div>
                     </div>
                     <!-- Body -->
                     <div class="px-6 py-6 space-y-6 max-h-[60vh] overflow-y-auto">
                        <!-- Basic Information -->
                        <div>
                           <h4 class="text-sm font-semibold text-gray-900 mb-4">Basic Information</h4>
                           <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <!-- Deadline -->
                              <div>
                                 <div class="flex items-center gap-2 text-sm text-gray-600 mb-1">
                                    <Calendar class="w-4 h-4" />
                                    <span class="font-medium">Deadline</span>
                                 </div>
                                 <p class="text-sm text-gray-900 ml-6">
                                    {{ formatDateDisplay(selectedTaskDetail?.deadline) }}
                                 </p>
                              </div>
                              <!-- Owner -->
                              <div>
                                 <div class="flex items-center gap-2 text-sm text-gray-600 mb-1">
                                    <User class="w-4 h-4" />
                                    <span class="font-medium">Owner</span>
                                 </div>
                                 <div class="flex items-center gap-2 ml-6">
                                    <p class="text-sm text-gray-900">
                                       {{ getUserDisplayName(selectedTaskDetail?.ownerId) }}
                                    </p>
                                    <span v-if="selectedTaskDetail?.ownerId === currentUser" class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                                    You
                                    </span>
                                 </div>
                              </div>
                           </div>
                        </div>
                        <!-- Collaborators -->
                        <div v-if="selectedTaskDetail?.collaborators && selectedTaskDetail.collaborators.length > 0">
                           <h4 class="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                              <Users class="w-4 h-4" />
                              Collaborators ({{ selectedTaskDetail.collaborators.length }})
                           </h4>
                           <div class="space-y-2">
                              <div 
                                 v-for="collaboratorId in selectedTaskDetail.collaborators" 
                                 :key="collaboratorId"
                                 class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                                 >
                                 <div class="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-semibold text-sm">
                                    {{ getUserDisplayName(collaboratorId).charAt(0).toUpperCase() }}
                                 </div>
                                 <div class="flex-1">
                                    <p class="text-sm font-medium text-gray-900">
                                       {{ getUserDisplayName(collaboratorId) }}
                                    </p>
                                    <p class="text-xs text-gray-600">
                                       {{ usersMap[collaboratorId]?.role || 'Collaborator' }}
                                    </p>
                                 </div>
                                 <span v-if="collaboratorId === currentUser" class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                                 You
                                 </span>
                              </div>
                           </div>
                        </div>
                        <!-- Notes -->
                        <div v-if="selectedTaskDetail?.notes">
                           <h4 class="text-sm font-semibold text-gray-900 mb-2">Notes</h4>
                           <p class="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-3 rounded-lg">{{ selectedTaskDetail.notes }}</p>
                        </div>
                     </div>
                     <!-- Footer -->
                     <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end rounded-b-2xl">
                        <button 
                           @click="closeTaskDetailModal"
                           class="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-all"
                           >
                        Close
                        </button>
                     </div>
                  </div>
               </transition>
            </div>
         </div>
      </transition>
      <!-- Toast Notification -->
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
   import { X, Edit3, Trash2, Calendar, User, Crown, Users } from 'lucide-vue-next';
   import { usersService } from '@/services/users';
   
   // FullCalendar imports
   import FullCalendar from '@fullcalendar/vue3';
   import dayGridPlugin from '@fullcalendar/daygrid';
   import interactionPlugin from '@fullcalendar/interaction';
   
   // --- Composables ---
   const router = useRouter();
   
   // --- API Base URL ---
   const KONG_BASE = import.meta.env.VITE_BACKEND_API || 'http://localhost:8000/';
   const API_BASE = `${KONG_BASE}tasks`;
   const PROJECT_API_BASE = `${import.meta.env.VITE_BACKEND_API}project`;
   
   // --- Reactive state ---
   const currentUser = ref(null);
   const currentRole = ref('');
   const currentUserDepartment = ref('');
   const loading = ref(true);
   const allTasks = ref([]);
   const filteredTasks = ref([]);
   
   // Add modal state
   const showTaskDetailModal = ref(false);
   const selectedTaskDetail = ref(null);
   const allUsers = ref([]);
   const usersMap = ref({});
   
   // --- Sidebar state ---
   const userProjects = ref([]);
   const selectedProject = ref(null);
   const projectCollaborators = ref([]);
   const selectedCollaborator = ref(null);
   const viewingUserId = ref(null); // The user whose schedule is being viewed
   const selectedProjectId = ref(null);
   
   // --- Show notification ---
   const showNotification = ref(false);
   const notificationMessage = ref('');
   
   // --- Computed: Transform filtered tasks into calendar events ---
   const calendarEvents = computed(() => {
   return filteredTasks.value.map(task => {
      // Safety check and convert to Date object
      let deadlineDate;
      
      if (!task.deadline) {
         console.warn('Task missing deadline:', task);
         return null;
      }
      
      // Check if deadline is already a Date object
      if (task.deadline instanceof Date) {
         deadlineDate = task.deadline;
      } 
      // Check if it's a Unix timestamp (number)
      else if (typeof task.deadline === 'number') {
         deadlineDate = new Date(task.deadline * 1000);
      }
      // Check if it's a string
      else if (typeof task.deadline === 'string') {
         deadlineDate = new Date(task.deadline);
      }
      else {
         console.warn('Invalid deadline format:', task.deadline);
         return null;
      }
      
      // Determine start date (today or task creation date)
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      let startDate;
      if (task.createdAt) {
         // Use task creation date as start if available
         const taskCreatedDate = new Date(task.createdAt * 1000);
         startDate = taskCreatedDate < today ? taskCreatedDate : today;
      } else {
         // Default to today if no creation date
         startDate = today;
      }
      
      // Format dates as YYYY-MM-DD
      const formatDate = (date) => {
         const year = date.getFullYear();
         const month = String(date.getMonth() + 1).padStart(2, '0');
         const day = String(date.getDate()).padStart(2, '0');
         return `${year}-${month}-${day}`;
      };
      
      const startString = formatDate(startDate);
      const endString = formatDate(new Date(deadlineDate.getTime() + 86400000)); // +1 day for inclusive end
      
      // Your existing status and color logic
      const statusLower = task.status?.toLowerCase() || 'unassigned';
      let backgroundColor, borderColor;
      
      if (statusLower === 'completed') {
         backgroundColor = '#9ca3af';
         borderColor = '#6b7280';
      } else if (statusLower === 'ongoing') {
         backgroundColor = '#3b82f6';
         borderColor = '#2563eb';
      } else if (statusLower === 'under review') {
         backgroundColor = '#f59e0b';
         borderColor = '#d97706';
      } else if(statusLower === 'unassigned'){
         backgroundColor = '#8b5cf6'; // Violet-500
         borderColor = '#7c3aed'; // Violet-600
      } else {
         backgroundColor = '#ef4444';
         borderColor = '#dc2626';
      }
      
      // Check if current user can view this task
      const isViewable = canViewTaskDetails(task);
      
      // Calculate days until deadline
      deadlineDate.setHours(0, 0, 0, 0);
      const daysUntilDeadline = Math.ceil((deadlineDate - today) / (1000 * 60 * 60 * 24));
      
      return {
         id: task.taskId,
         title: task.title,
         start: startString, // ✅ Start date
         end: endString, // ✅ End date (deadline + 1 day for inclusive)
         allDay: true,
         backgroundColor: backgroundColor,
         borderColor: borderColor,
         classNames: isViewable ? 'cursor-pointer' : 'cursor-not-allowed opacity-60',
         extendedProps: {
         status: task.status,
         notes: task.notes,
         projectId: task.projectId,
         ownerId: task.ownerId,
         daysUntilDeadline: daysUntilDeadline,
         isViewable: isViewable
         }
      };
   }).filter(event => event !== null);
   });


   
   // --- Calendar Configuration ---
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
     selectMirror: true,
     dayMaxEvents: true,
     weekends: true,
     events: calendarEvents, // Use computed events
      // Event click handler
      eventClick: function(info) {
      const taskId = info.event.id;
      const task = filteredTasks.value.find(t => t.taskId === taskId);
      
      if (!task) return;
      
      // Check if current user has permission to view
      if (!canViewTaskDetails(task)) {
         showToast('🔒 You do not have permission to view this task');
         return;
      }
      
      // If permission granted, open modal
      openTaskDetailModal(task);
      },
     // Date select handler
     select: function(info) {
       console.log('Date selected:', info.startStr, 'to', info.endStr);
       // You'll add create task functionality later
     }
   });
   
   function showToast(message) {
      notificationMessage.value = message;
      showNotification.value = true;
      
      // Auto-hide after 3 seconds
      setTimeout(() => {
         showNotification.value = false;
      }, 3000);
   }
   
   // --- Fetch all tasks from backend ---
   async function fetchAllTasks() {
     try {
       const response = await fetch(`${API_BASE}`);
       if (!response.ok) {
         throw new Error('Failed to fetch tasks');
       }
       const data = await response.json();
       allTasks.value = data.tasks || [];
       console.log('All tasks fetched:', allTasks.value.length);
     } catch (error) {
       console.error('Error fetching tasks:', error);
       allTasks.value = [];
     }
   }
   
   // --- Filter tasks where current user is a collaborator ---
   function filterTasksByUser(userId) {
     filteredTasks.value = allTasks.value.filter(task => {
       // Check if user is in collaborators array
       const collaborators = task.collaborators || [];
       return collaborators.includes(userId);
     });
     
     console.log(`Filtered tasks for user ${userId}:`, filteredTasks.value.length);
   }
   
   // --- Fetch all users for display ---
   async function fetchAllUsers() {
     try {
       const users = await usersService.getAllUsers();
       allUsers.value = users;
       
       // Create a map for quick lookup
       const map = {};
       users.forEach(user => {
         map[user.uid] = user;
       });
       usersMap.value = map;
       
       console.log('Loaded users:', allUsers.value.length);
     } catch (error) {
       console.error('Error fetching users:', error);
     }
   }
   
   // --- Open task detail modal ---
   function openTaskDetailModal(task) {
     selectedTaskDetail.value = task;
     showTaskDetailModal.value = true;
   }
   
   // --- Close task detail modal ---
   function closeTaskDetailModal() {
     showTaskDetailModal.value = false;
     selectedTaskDetail.value = null;
   }
   
   // --- Get user display name ---
   function getUserDisplayName(userId) {
     if (!userId) return 'Unassigned';
     if (userId === currentUser.value) return 'You';
     const user = usersMap.value[userId];
     return user ? (user.name || user.displayName || user.email) : 'Unknown User';
   }
   
   // --- Format date for display ---
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
   
   // --- Format status ---
   function formatStatus(status) {
     const statusMap = {
       'ongoing': 'Ongoing',
       'completed': 'Completed',
       'under review': 'Under Review',
       'unassigned': 'Unassigned'
     };
     return statusMap[status?.toLowerCase()] || status;
   }
   
   // --- Get status badge class ---
   function getStatusBadgeClass(status) {
     const statusLower = (status || '').toLowerCase();
     if (statusLower === 'completed') return 'bg-green-100 text-green-700';
     if (statusLower === 'ongoing') return 'bg-blue-100 text-blue-700';
     if (statusLower === 'under review') return 'bg-yellow-100 text-yellow-700';
     if (statusLower === 'unassigned') return 'bg-gray-100 text-gray-700';
     return 'bg-gray-100 text-gray-700';
   }
   
   // --- Check if current user is task owner ---
   function isTaskOwner(task) {
     return task.ownerId === currentUser.value;
   }
   
   // --- Handle edit task ---
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

    // --- Get due soon badge ---
    function getDueSoonBadge(task) {
    // Don't show due soon badge for completed tasks
    if (task?.status?.toLowerCase() === 'completed') {
        return null; 
    }
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const deadlineDate = new Date(task.deadline * 1000);
    deadlineDate.setHours(0, 0, 0, 0);
    const daysUntilDeadline = Math.ceil((deadlineDate - today) / (1000 * 60 * 60 * 24));
    
    if (daysUntilDeadline < 0) return { text: 'Overdue', class: 'bg-red-100 text-red-700' };
    if (daysUntilDeadline === 0) return { text: 'Due Today', class: 'bg-orange-100 text-orange-700' };
    if (daysUntilDeadline <= 3) return { text: `Due in ${daysUntilDeadline} days`, class: 'bg-orange-100 text-orange-700' };
    return null;
    }
   
   // --- Fetch user's projects (role-aware) ---
   async function fetchUserProjects() {
   if (!currentUser.value) return;
   
   try {
      let response;
      
      // Check if user is a director
      if (currentRole.value?.toLowerCase() === 'director') {
         // Directors see all projects in their department
         response = await fetch(`${PROJECT_API_BASE}/department/${currentUserDepartment.value}`);
      } else {
         // Non-directors see only projects they're involved in
         response = await fetch(`${PROJECT_API_BASE}/${currentUser.value}`);
      }
      
      if (!response.ok) {
         throw new Error('Failed to fetch projects');
      }
      
      const data = await response.json();
      userProjects.value = data.projects || [];
      
      console.log(`Projects loaded for ${currentRole.value}:`, userProjects.value.length);
   } catch (error) {
      console.error('Error fetching user projects:', error);
      userProjects.value = [];
   }
   }
   
   // --- Handle project selection ---
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
   
   // Get all unique collaborators (owner + collaborators)
   const collaboratorIds = new Set();
   
   // Add project owner
   if (project.ownerId) {
      collaboratorIds.add(project.ownerId);
   }
   
   // Add all collaborators
   if (project.collaborators && Array.isArray(project.collaborators)) {
      project.collaborators.forEach(id => collaboratorIds.add(id));
   }
   
   // Convert to array and map to user objects
   projectCollaborators.value = Array.from(collaboratorIds)
      .map(userId => {
         const user = usersMap.value[userId];
         return {
         uid: userId,
         name: user ? (user.name || user.displayName || user.email) : 'Unknown User',
         isCurrentUser: userId === currentUser.value,
         isOwner: userId === project.ownerId
         };
      })
      .sort((a, b) => {
         // Sort: current user first, then owner, then alphabetically
         if (a.isCurrentUser) return -1;
         if (b.isCurrentUser) return 1;
         if (a.isOwner) return -1;
         if (b.isOwner) return 1;
         return a.name.localeCompare(b.name);
      });
   
   console.log('Project collaborators:', projectCollaborators.value);
   
   // Reset collaborator selection
   selectedCollaborator.value = null;
   }
   
   // --- Handle collaborator selection ---
   function onCollaboratorSelect(userId) {
   if (!userId) {
      selectedCollaborator.value = null;
      viewingUserId.value = currentUser.value;
      filterTasksByUser(currentUser.value);
      return;
   }
   
   selectedCollaborator.value = userId;
   viewingUserId.value = userId;
   
   // Filter tasks for the selected user
   filterTasksByUser(userId);
   
   console.log('Now viewing schedule for:', getUserDisplayName(userId));
   }
   
   // --- Check if current user can view task details ---
   function canViewTaskDetails(task) {
   if (!task) return false;
   
   // Directors can view all tasks
   if (currentRole.value?.toLowerCase() === 'director') {
      return true;
   }
   
   // Non-directors: check if they're a collaborator
   if (!task.collaborators) return false;
   return task.collaborators.includes(currentUser.value);
   }

   
   // --- Reset filters ---
   function resetFilters() {
   selectedProject.value = null;
   selectedProjectId.value = null;
   projectCollaborators.value = [];
   selectedCollaborator.value = null;
   viewingUserId.value = currentUser.value;
   filterTasksByUser(currentUser.value);
   }
   
   // --- Initialization ---
   onMounted(() => {
     onAuthStateChanged(auth, async (user) => {
       if (user) {
         currentUser.value = user.uid;
         viewingUserId.value = user.uid;
   
         try {
           // Fetch user info
           const userInfo = await usersService.getUserById(user.uid);
           currentRole.value = userInfo.role;
           currentUserDepartment.value = userInfo.department || "";
   
           // Fetch all tasks
           await fetchAllTasks();
           await fetchAllUsers();
           await fetchUserProjects();
   
           // Filter tasks for current user
           filterTasksByUser(currentUser.value);
           
           // Fetch other data if needed
           fetchAllUsers();
           
         } catch (err) {
           console.error("Failed to fetch user info or tasks:", err);
         } finally {
           loading.value = false;
         }
   
       } else {
         router.push('/authentication');
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
