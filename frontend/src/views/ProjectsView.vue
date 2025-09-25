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
                <!-- <p>Debug: ownerId={{ project.ownerId }} currentUser={{ currentUser.value }}</p> -->
        <!-- Actions -->
        <div class="mt-2 flex gap-2">
          <button @click="selectProject(project)" class="bg-gray-600 text-white px-2 py-1 rounded">View</button>
          <button
            v-if="project.ownerId === currentUser.value"
            @click="editProject(project)"
            class="bg-yellow-500 text-white px-2 py-1 rounded"
          >Edit</button>
          <button
            v-if="project.ownerId === currentUser.value"
            @click="handleDelete(project)"
            class="bg-red-600 text-white px-2 py-1 rounded"
          >Delete</button>
        </div>

        <!-- Add Collaborator (only for owner) -->
        <!-- <div v-if="project.ownerId === currentUser.value" class="mt-3 flex items-center gap-2"> -->
 
              <div v-if="isOwner(project)" class="mt-3 flex items-center gap-2">

      

          <select v-model="collabInputs[project.projectId]" class="border p-1 rounded flex-1">
            <option value="">Select user</option>
            <option
              v-for="user in availableUsers[project.projectId] || []"
              :key="user.uid"
              :value="user.uid"
            >
              {{ user.name }} ({{ user.email }})
            </option>
          </select>
          <button
            @click="handleAddCollaborator(project)"
            class="bg-green-600 text-white px-2 py-1 rounded"
          >
            Add Collaborator
          </button>
        </div>
      </div>
    </div>
    <p v-else>No projects found.</p>
  </div>
</template>

<script setup>
import NavigationBar from '@/components/NavigationBar.vue';
import { ref, computed, onMounted } from 'vue';
import { auth } from '@/firebase/firebaseConfig';
import { onAuthStateChanged } from 'firebase/auth';

const API_BASE = `${import.meta.env.VITE_BACKEND_API}/project`;
const isOwner = (project) => {
  return project.ownerId && currentUser.value && project.ownerId === currentUser.value;
};

const currentUser = ref(null);
const currentRole = ref("manager");

const showCreateForm = ref(false);
const projects = ref([]);
const message = ref('');
const error = ref(false);
const newProject = ref({ title: '', deadline: '', description: '' });
const editingProject = ref(null);
const searchQuery = ref('');
const filterOption = ref('');
const collabInputs = ref({});
const availableUsers = ref({});
const usersMap = ref({});

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
      usersMap.value[user.uid] = user;
    });
  } catch (err) {
    console.error("Failed to fetch users:", err);
  }
}

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
        description: newProject.value.description
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
        userid: currentUser.value,
        adduserid: [newUserId],
        projectId: project.projectId
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to add collaborator");

    message.value = data.message;
    error.value = false;

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
</script>
