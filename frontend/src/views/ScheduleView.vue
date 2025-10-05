<template>
   <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <NavigationBar />
      <!-- Page Header -->
      <div class="bg-white/70 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-10">
         <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
               <div>
                  <h1 class="text-3xl font-bold text-gray-900 tracking-tight">Schedule</h1>
                  <p class="text-gray-600 mt-1">View and manage your schedule</p>
               </div>
            </div>
         </div>
      </div>
      <!-- Main Content -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
         <!-- Calendar Container -->
         <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
            <FullCalendar :options="calendarOptions" />
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
   
   // --- Computed: Transform filtered tasks into calendar events ---
   const calendarEvents = computed(() => {
     return filteredTasks.value.map(task => {
       // Convert epoch timestamp to ISO date string
       const taskDate = new Date(task.deadline * 1000).toISOString().split('T')[0];
       
       // Calculate days until deadline
       const today = new Date();
       today.setHours(0, 0, 0, 0); // Reset time to start of day
       const deadlineDate = new Date(task.deadline * 1000);
       deadlineDate.setHours(0, 0, 0, 0); // Reset time to start of day
       const daysUntilDeadline = Math.ceil((deadlineDate - today) / (1000 * 60 * 60 * 24));
       
       // Determine color based on priority logic
       let backgroundColor = '#3b82f6'; // Default blue (ongoing)
       let borderColor = '#2563eb';
       
       const statusLower = (task.status || '').toLowerCase();
       
       // Priority 1: Completed tasks (grey)
       if (statusLower === 'completed') {
         backgroundColor = '#9ca3af'; // grey
         borderColor = '#6b7280';
       }
       // Priority 2: Overdue tasks (red) - not completed and past deadline
       else if (daysUntilDeadline < 0 && statusLower !== 'completed') {
         backgroundColor = '#ef4444'; // red
         borderColor = '#dc2626';
       }
       // Priority 3: Due soon (orange) - within 3 days
       else if (daysUntilDeadline >= 0 && daysUntilDeadline <= 3) {
         backgroundColor = '#f59e0b'; // orange
         borderColor = '#d97706';
       }
       // Default: Ongoing (blue)
       // else - already set to blue by default
       
       return {
         id: task.taskId,
         title: task.title,
         start: taskDate,
         backgroundColor: backgroundColor,
         borderColor: borderColor,
         extendedProps: {
           status: task.status,
           notes: task.notes,
           projectId: task.projectId,
           ownerId: task.ownerId,
           daysUntilDeadline: daysUntilDeadline // Store for debugging/tooltips
         }
       };
     });
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
     if (task) {
       openTaskDetailModal(task);
     }
   },
     // Date select handler
     select: function(info) {
       console.log('Date selected:', info.startStr, 'to', info.endStr);
       // You'll add create task functionality later
     }
   });
   
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
     // TODO: Add edit task logic (navigate to tasks page or open edit modal)
     console.log('Edit task:', task.taskId);
   }
   
    // --- Get due soon badge ---
    function getDueSoonBadge(task) {
    // Don't show due soon badge for completed tasks
    if (task?.status?.toLowerCase() === 'completed') {
        return null; // ✅ Completed tasks don't get overdue/due soon badges
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
   
   // --- Initialization ---
   onMounted(() => {
     onAuthStateChanged(auth, async (user) => {
       if (user) {
         currentUser.value = user.uid;
   
         try {
           // Fetch user info
           const userInfo = await usersService.getUserById(user.uid);
           currentRole.value = userInfo.role;
           currentUserDepartment.value = userInfo.department || "";
   
           // Fetch all tasks
           await fetchAllTasks();
           await fetchAllUsers();
   
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
