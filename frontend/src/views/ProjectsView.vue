<template>
   <NavigationBar />
   <div class="p-6">
      <h1 class="text-2xl font-bold mb-4">Projects</h1>
      <!-- Create Project Section -->
      <div class="mb-6 border rounded-lg p-4 shadow">
         <div class="flex justify-between items-center">
            <h2 class="font-semibold">Projects</h2>
            <button 
               @click="showCreateForm = !showCreateForm"
               class="bg-green-600 text-white px-3 py-1 rounded"
               >
            {{ showCreateForm ? 'Cancel' : 'New Project' }}
            </button>
         </div>
         <!-- Create Project Form -->
         <form v-if="showCreateForm" @submit.prevent="handleCreate" class="mt-4">
            <div class="mb-2">
               <label class="block text-sm">Title *</label>
               <input v-model="newProject.title" class="border p-1 rounded w-full" required />
            </div>
            <div class="mb-2">
               <label class="block text-sm">Deadline *</label>
               <input type="date" v-model="newProject.deadline" class="border p-1 rounded w-full" required />
            </div>
            <div class="mb-2">
               <label class="block text-sm">Description (optional)</label>
               <textarea v-model="newProject.description" class="border p-1 rounded w-full"></textarea>
            </div>
            <div class="mb-2">
               <label class="block text-sm">Add Collaborators (optional)</label>
               <div class="flex gap-2">
                  <select v-model="selectedCollaborator" class="border p-1 rounded flex-1">
                     <option value="">Select user</option>
                     <option v-for="user in allUsers" :key="user.uid" :value="user.uid">
                        {{ user.name }} ({{ user.email }})
                     </option>
                  </select>
                  <button type="button" @click="addCollaborator" class="bg-green-600 text-white px-2 py-1 rounded">
                  Add Collaborator
                  </button>
               </div>
               <div v-if="collaborators && collaborators.length">
                  <p>Collaborators added:</p>
                  <ul>
                     <li v-for="uid in collaborators" :key="uid">{{ usersMap[uid]?.name || uid }}</li>
                  </ul>
               </div>
            </div>
            <button type="submit" class="bg-blue-600 text-white px-3 py-1 rounded">Create Project</button>
         </form>
         <p v-if="message" class="mt-2 text-sm" :class="error ? 'text-red-600' : 'text-green-600'">
            {{ message }}
         </p>
      </div>
      <!-- Search & Filter -->
      <div class="flex gap-4 mb-4">
         <input v-model="searchQuery" placeholder="Search by title" class="border p-1 rounded flex-1" />
         <select v-model="filterOption" class="border p-1 rounded">
            <option value="">All</option>
            <option value="deadline">Sort by Deadline</option>
            <option value="owner">Filter by Owner</option>
            <option value="createdAt">Sort by Creation Date</option>
         </select>
      </div>
      <!-- Project List -->
      <div v-if="projectsToShow.length">
         <div
            v-for="project in projectsToShow"
            :key="project.projectId"
            class="mb-3 border rounded p-3 shadow"
            >
            <h3 class="text-lg font-semibold">{{ project.title }}</h3>
            <p>Deadline: {{ project.deadline }}</p>
            <p v-if="project.description">Description: {{ project.description }}</p>
            <p>Owner: {{ usersMap[project.ownerId]?.name || project.ownerId }}</p>
            <p>
               Collaborators: 
               {{ project.collaborators.map(uid => usersMap[uid]?.name || uid).join(', ') }}
            </p>
            <button 
               v-if="isOwner" 
               @click="openEditModal(project)"
               class="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
            Edit
            </button>
            <button 
  @click="openViewModal(project)"
  class="bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 ml-2"
>
  View
</button>

         </div>
      </div>
      <!-- Edit Modal -->
      <div v-if="editingProject" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
         <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <!-- Modal Header -->
            <div class="px-6 py-4 border-b border-gray-200">
               <h2 class="text-xl font-semibold text-gray-800">Edit Project</h2>
            </div>
            <!-- Modal Body -->
            <div class="px-6 py-4 space-y-4">
               <!-- Title Field -->
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
                  <input 
                     v-model="editingProject.title" 
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     />
               </div>
               <!-- Deadline Field -->
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Deadline</label>
                  <input 
                     type="date" 
                     v-model="editingProject.deadline" 
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     />
               </div>
               <!-- Description Field -->
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea 
                     v-model="editingProject.description" 
                     rows="3"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     ></textarea>
               </div>
               <!-- Assign Owner Section (only show if user can assign) -->
               <div v-if="assignableUsers.length > 0">
                  <label class="block text-sm font-medium text-gray-700 mb-2">Assign Owner</label>
                  <select 
                     v-model="editingProject.ownerId"
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                     >
                     <option :value="editingProject.ownerId">Keep Current Owner ({{ usersMap[editingProject.ownerId]?.name }})</option>
                     <option 
                        v-for="user in assignableUsers" 
                        :key="user.uid" 
                        :value="user.uid"
                        >
                        {{ user.name }} ({{ user.email }}) - {{ user.role }}
                     </option>
                  </select>
                  <p class="text-xs text-gray-500 mt-1">
                     You can only assign ownership to users of lower rank in your department.
                  </p>
               </div>
               <!-- Add Collaborators Section -->
               <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Add Collaborators</label>
                  <div class="flex gap-2">
                     <select 
                        v-model="selectedCollaborator"
                        class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                        <option value="">Select user</option>
                        <option
                           v-for="user in availableUsers[editingProject.projectId] || []"
                           :key="user.uid"
                           :value="user.uid"
                           >
                           {{ user.name }} ({{ user.email }})
                        </option>
                     </select>
                     <button 
                        @click="addCollaborator"
                        class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                        >
                     Add
                     </button>
                  </div>
               </div>
               <!-- Current Collaborators -->
               <div v-if="editingProject.collaborators && editingProject.collaborators.length">
                  <label class="block text-sm font-medium text-gray-700 mb-2">Current Collaborators</label>
                  <div class="bg-gray-50 rounded-md p-3">
                     <div class="flex flex-wrap gap-2">
                        <span 
                           v-for="uid in editingProject.collaborators" 
                           :key="uid"
                           class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                           >
                        {{ usersMap[uid]?.name || uid }}
                        </span>
                     </div>
                  </div>
               </div>
            </div>
            <!-- Modal Footer -->
            <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
               <button 
                  @click="closeEditModal"
                  class="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
               Cancel
               </button>
               <button 
                  @click="saveProject"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
               Save Changes
               </button>
            </div>
         </div>
      </div>
      <!-- View Modal -->
<div v-if="viewingProject" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
  <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[90vh] overflow-y-auto">
    
    <!-- Modal Header -->
    <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
      <h2 class="text-xl font-semibold text-gray-800">Project Details</h2>
      <button 
        @click="closeViewModal"
        class="text-gray-500 hover:text-gray-700 focus:outline-none"
      >✕</button>
    </div>

    <!-- Modal Body -->
    <div class="px-6 py-4 space-y-4">
      <div>
        <p><strong>Title:</strong> {{ viewingProject.title }}</p>
        <p><strong>Description:</strong> {{ viewingProject.description || 'No description provided' }}</p>
        <p><strong>Deadline:</strong> {{ viewingProject.deadline }}</p>
        <p><strong>Owner:</strong> {{ usersMap[viewingProject.ownerId]?.name || viewingProject.ownerId }}</p>
      </div>

      <div>
        <p class="font-semibold">Collaborators:</p>
        <ul class="list-disc list-inside">
          <li 
            v-for="uid in viewingProject.collaborators" 
            :key="uid"
          >
            {{ usersMap[uid]?.name || uid }}
          </li>
        </ul>
      </div>

      <div>
        <p class="font-semibold">Tasks:</p>
        <div v-if="tasks.length">
          <ul class="list-disc list-inside">
            <li v-for="task in tasks" :key="task.id">
              <strong>{{ task.title }}</strong> - {{ task.status }}
              <p class="text-sm text-gray-500">{{ task.description }}</p>
            </li>
          </ul>
        </div>
        <p v-else>No tasks found for this project.</p>
      </div>
    </div>

    <!-- Modal Footer -->
    <div class="px-6 py-4 border-t border-gray-200 text-right">
      <button 
        @click="closeViewModal"
        class="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
      >
        Close
      </button>
    </div>
  </div>
</div>

   </div>
</template>
<script setup>
   import NavigationBar from '@/components/NavigationBar.vue';
   import { ref, computed, onMounted, reactive, watch } from 'vue';
   import { auth } from '@/firebase/firebaseConfig';
   import { onAuthStateChanged } from 'firebase/auth';
   import { usersService } from '@/services/users.js'; 
   
   const API_BASE = `${import.meta.env.VITE_BACKEND_API}/project`;
   const isOwner = (project) => {
     return project.ownerId && currentUser.value && project.ownerId === currentUser.value;
   };
   
   const currentUser = ref(null);
   const currentRole = ref("manager");
   const usersMap = reactive({});   // mapping from uid -> user info
   const availableUsers = ref([]);
   
   const showCreateForm = ref(false);
   const projects = ref([]);
   const message = ref('');
   const error = ref(false);
   const newProject = ref({ title: '', deadline: '', description: '', collaborators: [] });
   const editingProject = ref(null);
   const searchQuery = ref('');
   const filterOption = ref('');
   const collabInputs = ref({});
   const collaborators = ref([])
   const allUsers = ref([]);
   const selectedCollaborator = ref('');
   const assignableUsers = ref([]); // Users who can be assigned ownership
   const newlyAddedCollaborators = ref([]);
   
   
   
   // Firebase Auth + fetch projects after login
   onMounted(() => {
     onAuthStateChanged(auth, (user) => {
       if (user) {
         currentUser.value = user.uid; // ✅ use uid from Firebase
         fetchProjects();
         fetchAllUsers();
       } else {
         alert("Please login to access projects");
       }
     });
   });
   
   async function fetchAllUsers() {
     try {
       const res = await fetch(`${API_BASE}/all-users`);
       const data = await res.json();
       data.users.forEach(user => {
         usersMap[user.uid] = user;
       });
     } catch (err) {
       console.error("Failed to fetch users:", err);
     }
   }
   
   // Get All Users from Firebase
   async function getAllUsersFromFireBase() {
     try {
       const users = await usersService.getAllUsers();
       console.log('Fetched users:', users);
       return users;
     } catch (error) {
       console.error('Failed to fetch all users:', error);
       return [];
     }
   }
   
   getAllUsersFromFireBase().then(users => {
     allUsers.value = users;
   });
   
   async function fetchProjects() {
     if (!currentUser.value) return;
     try {
       const res = await fetch(`${API_BASE}/${currentUser.value}`);
       if (!res.ok) throw new Error("Failed to fetch projects");
       const data = await res.json();
       projects.value = data.projects || [];
       projects.value.forEach(project => fetchAvailableUsers(project));
     } catch (err) {
       error.value = true;
       message.value = err.message;
     }
   }
//placeholder for fetching tasks start

const viewingProject = ref(null);
const tasks = ref([]);

// Placeholder: Simulate fetching tasks from API
async function fetchProjectTasks(projectId) {
  try {
    // Replace with actual API call later
    // const res = await fetch(`${API_BASE}/${projectId}/tasks`);
    // const data = await res.json();
    // tasks.value = data.tasks || [];

    // Dummy data for now
    tasks.value = [
      { id: 1, title: 'Design Wireframe', description: 'Create initial design layout', status: 'In Progress' },
      { id: 2, title: 'Setup Database', description: 'Initialize Firestore collections', status: 'Completed' },
      { id: 3, title: 'API Integration', description: 'Connect frontend to backend', status: 'Pending' }
    ];
  } catch (err) {
    console.error("Failed to fetch tasks:", err);
    tasks.value = [];
  }
}

// Open modal
function openViewModal(project) {
  viewingProject.value = project;
  fetchProjectTasks(project.projectId);
}

// Close modal
function closeViewModal() {
  viewingProject.value = null;
  tasks.value = [];
}
   //placeholder for fetching tasks end

   function fetchAssignableUsers(currentUserId) {
   try {
    const currentUserRole = usersMap[currentUserId]?.role;
    
    // Filter users from existing allUsers array based on role hierarchy
    const filtered = allUsers.value.filter(user => {
      if (user.uid === currentUserId) return false; // Can't assign to self
      
      const userRole = user.role;
      
      // Role hierarchy: director > manager > staff
      if (currentUserRole === 'director') {
        return userRole === 'manager'; // Director can assign to manager only
      } else if (currentUserRole === 'manager') {
        return userRole === 'staff'; // Manager can assign to staff only
      }
      
      return false; // Staff cannot assign ownership
    });
    
    assignableUsers.value = filtered;
   } catch (error) {
    console.error('Failed to filter assignable users:', error);
    assignableUsers.value = [];
   }
   }
   
   
   async function fetchAvailableUsers(project) {
     try {
       const res = await fetch(`${API_BASE}/users/available-for-collaboration/${project.projectId}`);
       const data = await res.json();
       if (!res.ok) throw new Error(data.error || "Failed to fetch users");
       availableUsers.value[project.projectId] = data.availableUsers || [];
     } catch (err) {
       console.error(err.message);
       availableUsers.value[project.projectId] = [];
     }
   }
   
   async function handleCreate() {
     if (!currentUser.value) return;
     try {
       const res = await fetch(`${API_BASE}/create`, {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({
           userid: currentUser.value,
           role: currentRole.value,
           title: newProject.value.title,
           deadline: newProject.value.deadline,
           description: newProject.value.description,
           collaborators: collaborators.value || []
         })
       });
       const data = await res.json();
       if (!res.ok) throw new Error(data.error || "Failed to create project");
   
       message.value = data.message;
       error.value = false;
       projects.value.push(data.project);
       newProject.value = { title: '', deadline: '', description: '' };
       showCreateForm.value = false;
   
       fetchAvailableUsers(data.project);
     } catch (err) {
       error.value = true;
       message.value = err.message;
     }
   }
   
    function addCollaborator() {
      if (selectedCollaborator.value && !editingProject.value.collaborators.includes(selectedCollaborator.value)) {
        // Add to the editingProject for display
        editingProject.value.collaborators.push(selectedCollaborator.value);
        
        // Track this as a newly added collaborator
        newlyAddedCollaborators.value.push(selectedCollaborator.value);
        
        selectedCollaborator.value = '';
        fetchAvailableUsers(editingProject.value);
      }
    }
   
   async function handleUpdate() {
     if (!currentUser.value) return;
     try {
       const res = await fetch(`${API_BASE}/update`, {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({
           userid: currentUser.value,
           projectId: editingProject.value.projectId,
           title: editingProject.value.title,
           deadline: editingProject.value.deadline,
           description: editingProject.value.description
         })
       });
       const data = await res.json();
       if (!res.ok) throw new Error(data.error || "Failed to update project");
   
       message.value = data.message;
       error.value = false;
   
       const idx = projects.value.findIndex(p => p.projectId === editingProject.value.projectId);
       if (idx !== -1) projects.value[idx] = data.project;
       editingProject.value = null;
     } catch (err) {
       error.value = true;
       message.value = err.message;
     }
   }
   
   async function handleAddCollaborator(project) {
     const newUserId = collabInputs.value[project.projectId];
     if (!newUserId) return alert("Select a user");
     if (!currentUser.value) return;
   
     try {
       const res = await fetch(`${API_BASE}/add-collaborator`, {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({
           userid: currentUser.value,        // owner UID
           adduserid: [newUserId],           // array of UIDs
           uid: project.projectId             // project ID
         })
       });
       const data = await res.json();
       if (!res.ok) throw new Error(data.error || "Failed to add collaborator");
   
       message.value = data.message;
       error.value = false;
   
       // update local projects list
       const idx = projects.value.findIndex(p => p.projectId === project.projectId);
       if (idx !== -1) projects.value[idx] = data.project;
   
       collabInputs.value[project.projectId] = '';
       fetchAvailableUsers(project);
     } catch (err) {
       error.value = true;
       message.value = err.message;
     }
   }
   
   
   async function handleDelete(project) {
     alert("Delete is disabled: Projects cannot be deleted.");
   }
   
   const projectsToShow = computed(() => {
     let filtered = projects.value;
   
     if (searchQuery.value) {
       filtered = filtered.filter(p =>
         p.title.toLowerCase().includes(searchQuery.value.toLowerCase())
       );
     }
   
     if (filterOption.value === "deadline") {
       filtered = [...filtered].sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
     } else if (filterOption.value === "createdAt") {
       filtered = [...filtered].sort((a, b) => new Date(a.creationDate) - new Date(b.creationDate));
     } else if (filterOption.value === "owner") {
       filtered = filtered.filter(p => p.ownerId === currentUser.value);
     }
   
     return filtered;
   });
   
   function editProject(project) {
     editingProject.value = { ...project };
   }
   
   function selectProject(project) {
     alert(`Viewing project: ${project.title}\nOwner: ${project.ownerId}`);
   }
   
   function openEditModal(project) {
   editingProject.value = JSON.parse(JSON.stringify(project)); // deep copy
   newlyAddedCollaborators.value = []; // Reset newly added collaborators
   fetchAvailableUsers(editingProject.value);
   
   // Make sure allUsers is populated before filtering
   if (allUsers.value.length === 0) {
    fetchAllUsers().then(() => {
      fetchAssignableUsers(currentUser.value);
    });
   } else {
    fetchAssignableUsers(currentUser.value);
   }
   }
   
   function closeEditModal() {
     editingProject.value = null;
     selectedCollaborator.value = '';
     availableUsers.value = [];
   }
   
  async function saveProject() {
    if (!currentUser.value) return;
    
    try {
      const currentUserRole = usersMap[currentUser.value]?.role;
      
      const res = await fetch(`${API_BASE}/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userid: currentUser.value,
          role: currentUserRole,
          projectId: editingProject.value.projectId,
          title: editingProject.value.title,
          deadline: editingProject.value.deadline,
          description: editingProject.value.description,
          collaborators: newlyAddedCollaborators.value, // Send only newly added collaborators
          ownerId: editingProject.value.ownerId,
        }),
      });

      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || "Failed to update project");
      }

      message.value = "Project updated successfully!";
      error.value = false;
      closeEditModal();
      await fetchProjects();
      
    } catch (err) {
      error.value = true;
      message.value = err.message;
      console.error("Failed to save project:", err);
    }
  }
   
   async function loadProjects() {
     // Fetch projects and users map, omitted details here
   }
</script>
