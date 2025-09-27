<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
    <NavigationBar />

    <!-- Page Header -->
    <div class="bg-white/70 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 tracking-tight">Projects</h1>
            <p class="text-gray-600 mt-1">Manage and collaborate on your projects</p>
          </div>

          <button @click="showCreateForm = !showCreateForm"
            class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-300 transform hover:scale-105">
            <Plus class="w-5 h-5" />
            {{ showCreateForm ? 'Cancel' : 'New Project' }}
          </button>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Create Project Form -->
      <transition name="slide-down">
        <div v-if="showCreateForm" class="mb-8">
          <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-8">
            <div class="flex items-center gap-3 mb-6">
              <div
                class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <FolderPlus class="w-6 h-6 text-white" />
              </div>
              <h2 class="text-2xl font-bold text-gray-900">Create New Project</h2>
            </div>

            <form @submit.prevent="handleCreate" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <label class="block text-sm font-semibold text-gray-700">Project Title *</label>
                  <input v-model="newProject.title"
                    class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                    placeholder="Enter project title..." required />
                </div>

                <div class="space-y-2">
                  <label class="block text-sm font-semibold text-gray-700">Deadline *</label>
                  <input type="date" v-model="newProject.deadline"
                    class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                    required />
                </div>
              </div>

              <div class="space-y-2">
                <label class="block text-sm font-semibold text-gray-700">Description</label>
                <textarea v-model="newProject.description" rows="3"
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                  placeholder="Describe your project..." />
              </div>

              <div class="space-y-4">
                <label class="block text-sm font-semibold text-gray-700">Add Collaborators</label>
                <div class="flex gap-3">
                  <select v-model="selectedCollaborator"
                    class="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200">
                    <option value="">Select a collaborator...</option>
                    <option v-for="user in allUsers" :key="user.uid" :value="user.uid">
                      {{ user.name }} ({{ user.email }})
                    </option>
                  </select>
                  <button type="button" @click="addCollaborator"
                    class="px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-xl font-semibold hover:from-green-700 hover:to-green-800 transition-all duration-200 transform hover:scale-105">
                    <UserPlus class="w-5 h-5" />
                  </button>
                </div>

                <div v-if="collaborators && collaborators.length" class="bg-gray-50 rounded-xl p-4">
                  <p class="text-sm font-medium text-gray-700 mb-3">Selected Collaborators:</p>
                  <div class="flex flex-wrap gap-2">
                    <span v-for="uid in collaborators" :key="uid"
                      class="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                      {{ usersMap[uid]?.name || uid }}
                      <button @click="removeCollaborator(uid)" class="text-blue-600 hover:text-blue-800">
                        <X class="w-4 h-4" />
                      </button>
                    </span>
                  </div>
                </div>
              </div>

              <div class="flex justify-end gap-3 pt-6 border-t border-gray-200">
                <button type="button" @click="showCreateForm = false"
                  class="px-6 py-3 text-gray-700 bg-gray-100 rounded-xl font-semibold hover:bg-gray-200 transition-all duration-200">
                  Cancel
                </button>
                <button type="submit"
                  class="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-300 transform hover:scale-105">
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      </transition>

      <!-- Search & Filter -->
      <div class="mb-8">
        <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/50 p-6">
          <div class="flex flex-col sm:flex-row gap-4">
            <div class="relative flex-1">
              <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input v-model="searchQuery" placeholder="Search projects by title..."
                class="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200" />
            </div>
            <select v-model="filterOption"
              class="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 min-w-48">
              <option value="">All Projects</option>
              <option value="deadline">Sort by Deadline</option>
              <option value="owner">My Projects Only</option>
              <option value="createdAt">Sort by Creation Date</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Projects List -->
      <div class="space-y-6">
        <div v-if="loading" class="flex justify-center items-center py-12">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
            <span class="text-gray-600 font-medium">Loading projects...</span>
          </div>
        </div>

        <div v-else-if="projectsToShow.length" class="space-y-6">
          <div v-for="project in projectsToShow" :key="project.projectId"
            class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/50 overflow-hidden hover:shadow-xl transition-all duration-300">
            <!-- Project Header -->
            <div class="p-6 pb-4 border-b border-gray-100">
              <div class="flex items-start justify-between">
                <div class="flex items-start gap-4 flex-1">
                  <div
                    class="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                    <Folder class="w-7 h-7 text-white" />
                  </div>

                  <div class="flex-1 min-w-0">
                    <div class="flex items-start justify-between">
                      <div>
                        <h3 class="text-xl font-bold text-gray-900 mb-2">{{ project.title }}</h3>
                        <div class="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                          <div class="flex items-center gap-1">
                            <Calendar class="w-4 h-4" />
                            <span>Due: {{ formatDate(project.deadline) }}</span>
                            <span v-if="isOverdue(project.deadline)"
                              class="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-semibold ml-2">
                              Overdue
                            </span>
                            <span v-else-if="isDueSoon(project.deadline)"
                              class="px-2 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-semibold ml-2">
                              Due Soon
                            </span>
                          </div>
                          <div class="flex items-center gap-1">
                            <User class="w-4 h-4" />
                            <span>{{ usersMap[project.ownerId]?.name || project.ownerId }}</span>
                          </div>
                          <div class="flex items-center gap-1">
                            <Users class="w-4 h-4" />
                            <span>{{ project.collaborators.length }} collaborators</span>
                          </div>
                        </div>
                      </div>

                      <div class="flex items-center gap-2 flex-shrink-0">
                        <button v-if="isOwner(project)" @click="openEditModal(project)"
                          class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all duration-200"
                          title="Edit Project">
                          <Edit3 class="w-5 h-5" />
                        </button>
                        <button @click="openViewModal(project)"
                          class="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-all duration-200"
                          title="View Details">
                          <Eye class="w-5 h-5" />
                        </button>
                      </div>
                    </div>

                    <div v-if="project.description" class="mt-3 text-gray-600 text-sm">
                      {{ project.description }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Project Tasks Section -->
            <div class="p-6">
              <div class="flex items-center justify-between mb-4">
                <h4 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <CheckSquare class="w-5 h-5 text-blue-600" />
                  Tasks
                  <span class="text-sm font-normal text-gray-500">
                    ({{ getProjectTasks(project.projectId).length }})
                  </span>
                </h4>

                <button @click="viewAllProjectTasks(project)"
                  class="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 transition-all duration-200 text-sm">
                  View All Tasks
                </button>
              </div>

              <!-- Task List -->
              <div v-if="loadingTasks[project.projectId]" class="flex items-center justify-center py-8">
                <div class="flex items-center gap-2">
                  <div class="w-5 h-5 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                  <span class="text-gray-600 text-sm">Loading tasks...</span>
                </div>
              </div>

              <div v-else-if="getProjectTasks(project.projectId).length" class="space-y-3">
                <div v-for="task in getProjectTasks(project.projectId).slice(0, 3)" :key="task.taskId"
                  class="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-all duration-200 cursor-pointer border border-gray-200"
                  @click="viewSingleTask(task, project)">
                  <div class="flex items-center justify-between">
                    <div class="flex-1">
                      <div class="flex items-center gap-3 mb-2">
                        <h5 class="font-semibold text-gray-900 text-sm">{{ task.title }}</h5>
                        <span class="px-2 py-1 rounded-full text-xs font-semibold"
                          :class="getStatusBadgeClass(task.status)">
                          {{ formatTaskStatus(task.status) }}
                        </span>
                      </div>

                      <div class="flex items-center gap-4 text-xs text-gray-600">
                        <div class="flex items-center gap-1">
                          <Calendar class="w-3 h-3" />
                          <span>{{ formatDate(task.deadline) }}</span>
                        </div>
                        <div class="flex items-center gap-1">
                          <User class="w-3 h-3" />
                          <span>{{ getOwnerName(task.ownerId) }}</span>
                        </div>
                        <div v-if="task.subtasks && task.subtasks.length" class="flex items-center gap-1">
                          <CheckSquare class="w-3 h-3" />
                          <span>{{ task.subtasks.length }} subtasks</span>
                        </div>
                      </div>
                    </div>

                    <ChevronRight class="w-4 h-4 text-gray-400" />
                  </div>
                </div>

                <div v-if="getProjectTasks(project.projectId).length > 3" class="text-center pt-2">
                  <button @click="viewAllProjectTasks(project)"
                    class="text-blue-600 hover:text-blue-700 font-medium text-sm">
                    View {{ getProjectTasks(project.projectId).length - 3 }} more tasks →
                  </button>
                </div>
              </div>

              <div v-else class="text-center py-8">
                <CheckSquare class="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p class="text-gray-600 text-sm">No tasks yet</p>
                <button @click="createTaskForProject(project)"
                  class="mt-2 text-blue-600 hover:text-blue-700 font-medium text-sm">
                  Create first task →
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-12">
          <div class="w-24 h-24 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Folder class="w-12 h-12 text-gray-400" />
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">No projects found</h3>
          <p class="text-gray-600 mb-6">Get started by creating your first project</p>
          <button @click="showCreateForm = true"
            class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-300 transform hover:scale-105">
            <Plus class="w-5 h-5" />
            Create Project
          </button>
        </div>
      </div>

      <!-- Messages -->
      <transition name="fade">
        <div v-if="message" class="fixed bottom-6 right-6 z-50">
          <div class="px-6 py-4 rounded-xl shadow-lg border backdrop-blur-sm"
            :class="error ? 'bg-red-50/90 text-red-700 border-red-200' : 'bg-green-50/90 text-green-700 border-green-200'">
            <div class="flex items-center gap-3">
              <component :is="error ? AlertCircle : CheckCircle" class="w-5 h-5" />
              <span class="font-medium">{{ message }}</span>
              <button @click="message = ''" class="text-current hover:opacity-75">
                <X class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- Edit Modal -->
    <transition name="modal">
      <div v-if="editingProject"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-50 p-4">
        <div
          class="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto border border-white/50">
          <!-- Modal Header -->
          <div class="px-8 py-6 border-b border-gray-200/50 flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900">Edit Project</h2>
            <button @click="closeEditModal"
              class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all duration-200">
              <X class="w-6 h-6" />
            </button>
          </div>

          <!-- Modal Body -->
          <div class="px-8 py-6 space-y-6">
            <!-- Basic Fields -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <label class="block text-sm font-semibold text-gray-700">Title</label>
                <input v-model="editingProject.title"
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200" />
              </div>

              <div class="space-y-2">
                <label class="block text-sm font-semibold text-gray-700">Deadline</label>
                <input type="date" v-model="editingProject.deadline"
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200" />
              </div>
            </div>

            <div class="space-y-2">
              <label class="block text-sm font-semibold text-gray-700">Description</label>
              <textarea v-model="editingProject.description" rows="3"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200" />
            </div>

            <!-- Owner Assignment -->
            <div v-if="assignableUsers.length > 0" class="space-y-2">
              <label class="block text-sm font-semibold text-gray-700">Assign Owner</label>
              <select v-model="editingProject.ownerId"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200">
                <option :value="editingProject.ownerId">
                  Keep Current Owner ({{ usersMap[editingProject.ownerId]?.name }})
                </option>
                <option v-for="user in assignableUsers" :key="user.uid" :value="user.uid">
                  {{ user.name }} ({{ user.email }}) - {{ user.role }}
                </option>
              </select>
              <p class="text-sm text-gray-500">You can only assign ownership to users of lower rank in your department.
              </p>
            </div>

            <!-- Add Collaborators -->
            <div class="space-y-4">
              <label class="block text-sm font-semibold text-gray-700">Add Collaborators</label>
              <div class="flex gap-3">
                <select v-model="selectedCollaborator"
                  class="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200">
                  <option value="">Select user...</option>
                  <option v-for="user in availableUsers[editingProject.projectId] || []" :key="user.uid"
                    :value="user.uid">
                    {{ user.name }} ({{ user.email }})
                  </option>
                </select>
                <button @click="addCollaborator"
                  class="px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-xl font-semibold hover:from-green-700 hover:to-green-800 transition-all duration-200 transform hover:scale-105">
                  <UserPlus class="w-5 h-5" />
                </button>
              </div>

              <!-- Current Collaborators -->
              <div v-if="editingProject.collaborators && editingProject.collaborators.length"
                class="bg-gray-50 rounded-xl p-4">
                <label class="block text-sm font-semibold text-gray-700 mb-3">Current Collaborators</label>
                <div class="flex flex-wrap gap-2">
                  <span v-for="uid in editingProject.collaborators" :key="uid"
                    class="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                    {{ usersMap[uid]?.name || uid }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="px-8 py-6 border-t border-gray-200/50 flex justify-end gap-3">
            <button @click="closeEditModal"
              class="px-6 py-3 text-gray-700 bg-gray-100 rounded-xl font-semibold hover:bg-gray-200 transition-all duration-200">
              Cancel
            </button>
            <button @click="saveProject"
              class="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-300 transform hover:scale-105">
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- View Modal -->
    <transition name="modal">
      <div v-if="viewingProject"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-50 p-4">
        <div
          class="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-white/50">
          <!-- Modal Header -->
          <div class="px-8 py-6 border-b border-gray-200/50">
            <div class="flex items-start justify-between">
              <div>
                <h2 class="text-2xl font-bold text-gray-900">{{ viewingProject.title }}</h2>
                <div class="flex items-center gap-4 mt-2 text-sm text-gray-600">
                  <div class="flex items-center gap-1">
                    <Calendar class="w-4 h-4" />
                    <span>Due: {{ formatDate(viewingProject.deadline) }}</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <User class="w-4 h-4" />
                    <span>Owner: {{ usersMap[viewingProject.ownerId]?.name || viewingProject.ownerId }}</span>
                  </div>
                </div>
              </div>
              <button @click="closeViewModal"
                class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all duration-200">
                <X class="w-6 h-6" />
              </button>
            </div>
          </div>

          <!-- Modal Body -->
          <div class="px-8 py-6 space-y-8">
            <!-- Project Description -->
            <div v-if="viewingProject.description" class="bg-gray-50 rounded-xl p-6">
              <h3 class="font-semibold text-gray-900 mb-3">Description</h3>
              <p class="text-gray-700 leading-relaxed">{{ viewingProject.description }}</p>
            </div>

            <!-- Collaborators Section -->
            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6">
              <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Users class="w-5 h-5 text-blue-600" />
                Collaborators ({{ viewingProject.collaborators.length }})
              </h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div v-for="uid in viewingProject.collaborators" :key="uid"
                  class="flex items-center gap-3 bg-white/80 rounded-lg p-3 backdrop-blur-sm">
                  <div
                    class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-semibold text-sm">
                    {{ getInitials(uid) }}
                  </div>
                  <div>
                    <div class="font-medium text-gray-900 text-sm">
                      {{ usersMap[uid]?.name || uid }}
                    </div>
                    <div class="text-xs text-gray-500">
                      {{ usersMap[uid]?.email }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tasks Section -->
            <div class="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-semibold text-gray-900 flex items-center gap-2">
                  <CheckSquare class="w-5 h-5 text-green-600" />
                  Tasks ({{ getProjectTasks(viewingProject.projectId).length }})
                </h3>
                <button @click="viewAllProjectTasks(viewingProject)"
                  class="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 transition-all duration-200 text-sm">
                  View All Tasks
                </button>
              </div>

              <div v-if="loadingTasks[viewingProject.projectId]" class="flex items-center justify-center py-8">
                <div class="flex items-center gap-3">
                  <div class="w-6 h-6 border-3 border-green-200 border-t-green-600 rounded-full animate-spin"></div>
                  <span class="text-gray-600">Loading tasks...</span>
                </div>
              </div>

              <div v-else-if="getProjectTasks(viewingProject.projectId).length" class="space-y-3">
                <div v-for="task in getProjectTasks(viewingProject.projectId).slice(0, 5)" :key="task.taskId"
                  class="bg-white/80 rounded-lg p-4 border border-white/50 backdrop-blur-sm cursor-pointer hover:bg-white/90 transition-all duration-200"
                  @click="viewSingleTask(task, viewingProject)">
                  <div class="flex items-center justify-between mb-2">
                    <h4 class="font-semibold text-gray-900 text-sm">{{ task.title }}</h4>
                    <div class="flex items-center gap-2">
                      <span class="px-2 py-1 rounded-full text-xs font-semibold"
                        :class="getStatusBadgeClass(task.status)">
                        {{ formatTaskStatus(task.status) }}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center gap-4 text-xs text-gray-600">
                    <div class="flex items-center gap-1">
                      <Calendar class="w-3 h-3" />
                      <span>{{ formatDate(task.deadline) }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <User class="w-3 h-3" />
                      <span>{{ getOwnerName(task.ownerId) }}</span>
                    </div>
                    <div v-if="task.subtasks && task.subtasks.length" class="flex items-center gap-1">
                      <CheckSquare class="w-3 h-3" />
                      <span>{{ task.subtasks.length }} subtasks</span>
                    </div>
                  </div>
                </div>

                <div v-if="getProjectTasks(viewingProject.projectId).length > 5" class="text-center pt-2">
                  <button @click="viewAllProjectTasks(viewingProject)"
                    class="text-blue-600 hover:text-blue-700 font-medium text-sm">
                    View {{ getProjectTasks(viewingProject.projectId).length - 5 }} more tasks →
                  </button>
                </div>
              </div>

              <div v-else class="text-center py-8">
                <CheckSquare class="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p class="text-gray-600">No tasks found for this project</p>
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="px-8 py-6 border-t border-gray-200/50 flex justify-end">
            <button @click="closeViewModal"
              class="px-6 py-3 text-gray-700 bg-gray-100 rounded-xl font-semibold hover:bg-gray-200 transition-all duration-200">
              Close
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue';
import { useRouter } from 'vue-router';
import { auth } from '@/firebase/firebaseConfig';
import { onAuthStateChanged } from 'firebase/auth';
import { usersService } from '@/services/users.js';
import NavigationBar from '@/components/NavigationBar.vue';
import {
  Plus,
  FolderPlus,
  Folder,
  Search,
  Calendar,
  Users,
  User,
  Eye,
  Edit3,
  X,
  UserPlus,
  CheckCircle,
  AlertCircle,
  CheckSquare,
  ChevronRight
} from 'lucide-vue-next';

// Composables
const router = useRouter();

// API endpoints
const API_BASE = `${import.meta.env.VITE_BACKEND_API}project`;
const TASK_API_BASE = `${import.meta.env.VITE_BACKEND_API}tasks`;

// Reactive state
const currentUser = ref(null);
const currentRole = ref("manager");
const usersMap = reactive({});
const availableUsers = ref({});
const loading = ref(false);
const loadingTasks = reactive({});

// Form state
const showCreateForm = ref(false);
const projects = ref([]);
const projectTasks = reactive({});  // Store tasks by project ID
const message = ref('');
const error = ref(false);
const newProject = ref({ title: '', deadline: '', description: '', collaborators: [] });
const editingProject = ref(null);
const viewingProject = ref(null);
const searchQuery = ref('');
const filterOption = ref('');
const collaborators = ref([]);
const allUsers = ref([]);
const selectedCollaborator = ref('');
const assignableUsers = ref([]);
const newlyAddedCollaborators = ref([]);

// Helper functions
const isOwner = (project) => {
  return project.ownerId && currentUser.value && project.ownerId === currentUser.value;
};

// Initialize
onMounted(() => {
  onAuthStateChanged(auth, (user) => {
    if (user) {
      currentUser.value = user.uid;
      fetchProjects();
      fetchAllUsers();
    } else {
      router.push('/authentication');
    }
  });
});

// Fetch data functions
async function fetchAllUsers() {
  try {
    const users = await usersService.getAllUsers();
    allUsers.value = users;
    users.forEach(user => {
      usersMap[user.uid] = user;
    });
  } catch (err) {
    console.error("Failed to fetch users:", err);
  }
}

async function fetchProjects() {
  if (!currentUser.value) return;
  loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/${currentUser.value}`);
    if (!res.ok) throw new Error("Failed to fetch projects");
    const data = await res.json();
    projects.value = data.projects || [];

    // Fetch tasks for each project
    for (const project of projects.value) {
      await fetchProjectTasks(project.projectId);
      fetchAvailableUsers(project);
    }
  } catch (err) {
    error.value = true;
    message.value = err.message;
    setTimeout(() => {
      message.value = '';
      error.value = false;
    }, 5000);
  } finally {
    loading.value = false;
  }
}

async function fetchProjectTasks(projectId) {
  loadingTasks[projectId] = true;
  try {
    // Fetch tasks by project ID from the actual task service API
    const res = await fetch(`${TASK_API_BASE}/project/${projectId}`);
    if (!res.ok) {
      throw new Error("Failed to fetch tasks");
    }
    const data = await res.json();
    projectTasks[projectId] = data.tasks || [];
  } catch (err) {
    console.error("Failed to fetch tasks for project", projectId, ":", err);
    projectTasks[projectId] = [];
  } finally {
    loadingTasks[projectId] = false;
  }
}

function getProjectTasks(projectId) {
  return projectTasks[projectId] || [];
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

// Project operations
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

    message.value = "Project created successfully!";
    error.value = false;
    projects.value.push(data.project);

    // Initialize tasks for new project
    projectTasks[data.project.projectId] = [];

    newProject.value = { title: '', deadline: '', description: '' };
    collaborators.value = [];
    showCreateForm.value = false;
    fetchAvailableUsers(data.project);

    setTimeout(() => {
      message.value = '';
    }, 5000);
  } catch (err) {
    error.value = true;
    message.value = err.message;
    setTimeout(() => {
      message.value = '';
      error.value = false;
    }, 5000);
  }
}

// Modal functions
function openEditModal(project) {
  editingProject.value = JSON.parse(JSON.stringify(project));
  newlyAddedCollaborators.value = [];
  fetchAvailableUsers(editingProject.value);

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
  newlyAddedCollaborators.value = [];
}

function openViewModal(project) {
  viewingProject.value = project;
  // Tasks are already loaded, no need to fetch again
}

function closeViewModal() {
  viewingProject.value = null;
}

// Collaborator management
function addCollaborator() {
  if (selectedCollaborator.value) {
    if (editingProject.value) {
      // Editing mode
      if (!editingProject.value.collaborators.includes(selectedCollaborator.value)) {
        editingProject.value.collaborators.push(selectedCollaborator.value);
        newlyAddedCollaborators.value.push(selectedCollaborator.value);
        selectedCollaborator.value = '';
        fetchAvailableUsers(editingProject.value);
      }
    } else {
      // Create mode
      if (!collaborators.value.includes(selectedCollaborator.value)) {
        collaborators.value.push(selectedCollaborator.value);
        selectedCollaborator.value = '';
      }
    }
  }
}

function removeCollaborator(uid) {
  const index = collaborators.value.indexOf(uid);
  if (index > -1) {
    collaborators.value.splice(index, 1);
  }
}

function fetchAssignableUsers(currentUserId) {
  try {
    const currentUserRole = usersMap[currentUserId]?.role;

    const filtered = allUsers.value.filter(user => {
      if (user.uid === currentUserId) return false;

      const userRole = user.role;

      if (currentUserRole === 'director') {
        return userRole === 'manager';
      } else if (currentUserRole === 'manager') {
        return userRole === 'staff';
      }

      return false;
    });

    assignableUsers.value = filtered;
  } catch (error) {
    console.error('Failed to filter assignable users:', error);
    assignableUsers.value = [];
  }
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
        collaborators: newlyAddedCollaborators.value,
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

    setTimeout(() => {
      message.value = '';
    }, 5000);

  } catch (err) {
    error.value = true;
    message.value = err.message;
    setTimeout(() => {
      message.value = '';
      error.value = false;
    }, 5000);
  }
}

// Navigation functions
function viewAllProjectTasks(project) {
  // Store project data globally so TasksView can access it
  window.selectedProjectForFilter = {
    projectId: project.projectId,
    projectTitle: project.title
  };

  router.push({ name: 'tasks' });
}

function viewSingleTask(task, project) {
  // Store both project and task data
  window.selectedProjectForFilter = {
    projectId: project.projectId,
    projectTitle: project.title
  };
  window.selectedTaskForView = task;

  router.push({ name: 'tasks' });
}

function createTaskForProject(project) {
  // Store project data and trigger task creation
  window.selectedProjectForFilter = {
    projectId: project.projectId,
    projectTitle: project.title
  };
  window.createTaskForProject = true;

  router.push({ name: 'tasks' });
}

// Utility functions
function formatDate(dateString) {
  if (!dateString) return 'No deadline';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

function isOverdue(deadline) {
  if (!deadline) return false;
  return new Date(deadline) < new Date();
}

function isDueSoon(deadline) {
  if (!deadline || isOverdue(deadline)) return false;
  const daysUntilDue = (new Date(deadline) - new Date()) / (1000 * 60 * 60 * 24);
  return daysUntilDue <= 7;
}

function getInitials(uid) {
  if (!uid) return '?';
  if (uid === currentUser.value) return 'Y';

  const user = usersMap[uid];
  if (user) {
    const name = user.name || user.displayName || user.email;
    if (name) {
      const parts = name.split(' ');
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
      }
      return name.slice(0, 2).toUpperCase();
    }
  }

  return uid.slice(0, 2).toUpperCase();
}

function getOwnerName(ownerId) {
  if (!ownerId) return 'Unassigned';
  if (ownerId === currentUser.value) return 'You';
  return usersMap[ownerId]?.name || 'Unknown';
}

function formatTaskStatus(status) {
  const statusMap = {
    'unassigned': 'Unassigned',
    'ongoing': 'Ongoing',
    'under_review': 'Under Review',
    'completed': 'Completed'
  };
  return statusMap[status] || status;
}

function getStatusBadgeClass(status) {
  const classMap = {
    'unassigned': 'bg-amber-100 text-amber-800',
    'ongoing': 'bg-blue-100 text-blue-800',
    'under_review': 'bg-purple-100 text-purple-800',
    'completed': 'bg-green-100 text-green-800'
  };
  return classMap[status] || 'bg-gray-100 text-gray-800';
}

// Computed properties
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
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Transitions */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
</style>
