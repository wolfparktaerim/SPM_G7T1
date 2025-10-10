// src/composables/useProjects.js
import { ref, computed } from 'vue';

const projects = ref([]);

export function useProjects(currentUser = "me@example.com") {
  const message = ref('');
  const error = ref(false);

  function createProject({ title, deadline, description }) {
    if (!title || !deadline) {
      message.value = "Title and deadline are required.";
      error.value = true;
      return false;
    }

    const project = {
      id: Date.now(), // backend will replace later
      title,
      deadline,
      description: description || '',
      owner: currentUser,
      collaborators: [currentUser],
      createdAt: new Date().toISOString(),
      tasks: []
    };

    projects.value.push(project);
    message.value = "Project created successfully!";
    error.value = false;
    return true;
  }

  function updateProject(updated) {
    if (!updated.title || !updated.deadline) {
      message.value = "Title and deadline are required.";
      error.value = true;
      return false;
    }
    const idx = projects.value.findIndex(p => p.id === updated.id);
    if (idx !== -1) {
      projects.value[idx] = { ...updated };
      message.value = "Project updated successfully!";
      error.value = false;
      return true;
    }
    return false;
  }

  function deleteProject(project) {
    if (project.tasks.length > 0) {
      message.value = "Cannot delete project with tasks or subtasks.";
      error.value = true;
      return false;
    }
    projects.value = projects.value.filter(p => p.id !== project.id);
    message.value = "Project deleted successfully!";
    error.value = false;
    return true;
  }

  function getProjectById(id) {
    return projects.value.find(p => p.id === id);
  }

  const filteredProjects = (searchQuery, filterOption) => computed(() => {
    let result = [...projects.value];

    if (searchQuery.value) {
      result = result.filter(p =>
        p.title.toLowerCase().includes(searchQuery.value.toLowerCase())
      );
    }

    if (filterOption.value === 'deadline') {
      result.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
    } else if (filterOption.value === 'owner') {
      result = result.filter(p => p.owner === currentUser);
    } else if (filterOption.value === 'createdAt') {
      result.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
    }

    return result;
  });

  return {
    projects,
    message,
    error,
    createProject,
    updateProject,
    deleteProject,
    getProjectById,
    filteredProjects
  };
}
