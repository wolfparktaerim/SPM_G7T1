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

  <!-- Create Project Form (only visible if toggled) -->
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
        :key="project.id"
        class="mb-3 border rounded p-3 shadow"
      >
        <h3 class="text-lg font-semibold">{{ project.title }}</h3>
        <p>Deadline: {{ project.deadline }}</p>
        <p>Owner: {{ project.owner }}</p>
        <p v-if="project.description">Description: {{ project.description }}</p>
        <p>Collaborators: {{ project.collaborators.join(', ') }}</p>

        <!-- Actions -->
        <div class="mt-2 flex gap-2">
          <button @click="selectProject(project)" class="bg-gray-600 text-white px-2 py-1 rounded">View</button>
          <button
            v-if="project.owner === currentUser"
            @click="editProject(project)"
            class="bg-yellow-500 text-white px-2 py-1 rounded"
          >Edit</button>
          <button
            v-if="project.owner === currentUser"
            @click="handleDelete(project)"
            class="bg-red-600 text-white px-2 py-1 rounded"
          >Delete</button>
        </div>
      </div>
    </div>
    <p v-else>No projects found.</p>

    <!-- Edit Modal -->
    <div v-if="editingProject" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center">
      <div class="bg-white p-6 rounded-lg w-1/2 shadow-lg">
        <h2 class="text-xl font-bold mb-4">Edit Project</h2>
        <form @submit.prevent="handleUpdate">
          <div class="mb-2">
            <label class="block text-sm">Title *</label>
            <input v-model="editingProject.title" class="border p-1 rounded w-full" required />
          </div>
          <div class="mb-2">
            <label class="block text-sm">Deadline *</label>
            <input type="date" v-model="editingProject.deadline" class="border p-1 rounded w-full" required />
          </div>
          <div class="mb-2">
            <label class="block text-sm">Description</label>
            <textarea v-model="editingProject.description" class="border p-1 rounded w-full"></textarea>
          </div>
          <button type="submit" class="bg-blue-600 text-white px-3 py-1 rounded">Save Changes</button>
          <button type="button" @click="editingProject = null" class="ml-2 bg-gray-400 text-white px-3 py-1 rounded">Cancel</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import NavigationBar from '@/components/NavigationBar.vue';

const API_BASE = "http://localhost:8000/project"; // Kong gateway

const currentUser = "me@example.com"; // example user
const currentRole = "manager"; // example role (needed for create)

const showCreateForm = ref(false);
const projects = ref([]);
const message = ref('');
const error = ref(false);

const newProject = ref({ title: '', deadline: '', description: '' });
const editingProject = ref(null);
const searchQuery = ref('');
const filterOption = ref('');

// Load projects from backend
async function fetchProjects() {
  try {
    const res = await fetch(`${API_BASE}/${currentUser}`);
    if (!res.ok) throw new Error("Failed to fetch projects");
    const data = await res.json();
    projects.value = data.projects || [];
  } catch (err) {
    error.value = true;
    message.value = err.message;
  }
}

onMounted(fetchProjects);

// Create Project
async function handleCreate() {
  try {
    const res = await fetch(`${API_BASE}/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        userid: currentUser,
        role: currentRole,
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
  } catch (err) {
    error.value = true;
    message.value = err.message;
  }
}

// Update Project
async function handleUpdate() {
  try {
    const res = await fetch(`${API_BASE}/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        userid: currentUser,
        uid: editingProject.value.uid,
        title: editingProject.value.title,
        deadline: editingProject.value.deadline,
        description: editingProject.value.description
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to update project");

    message.value = data.message;
    error.value = false;

    // Update locally
    const idx = projects.value.findIndex(p => p.uid === editingProject.value.uid);
    if (idx !== -1) projects.value[idx] = data.project;

    editingProject.value = null;
  } catch (err) {
    error.value = true;
    message.value = err.message;
  }
}

// Delete Project (disabled in backend, but kept for UI)
async function handleDelete(project) {
  alert("Delete is disabled: Projects cannot be deleted.");
}

// Search & Filter
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
    filtered = filtered.filter(p => p.ownerUid === currentUser);
  }

  return filtered;
});

function editProject(project) {
  editingProject.value = { ...project };
}

function selectProject(project) {
  alert(`Viewing project: ${project.title}\nOwner: ${project.ownerUid}`);
}
</script>
