<!-- frontend/src/views/DashboardView.vue -->

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
    <NavigationBar />

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-screen">
      <div class="flex flex-col items-center gap-4">
        <div class="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        <span class="text-gray-600 font-medium">Loading dashboard...</span>
      </div>
    </div>

    <!-- Main Dashboard Content -->
    <div v-else class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <!-- Welcome Section -->
      <div class="animate-fade-in">
        <h1 class="text-4xl font-bold bg-gradient-to-r">
          Welcome back, {{ getUserDisplayName() }}! 👋
        </h1>
        <p class="text-gray-600 mt-2 text-lg">
          Here's what's happening with your tasks today
        </p>
      </div>

      <!-- Statistics Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-slide-up">
        <!-- Total Tasks Card -->
        <div class="stat-card bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600">
          <div class="stat-pattern"></div>
          <div class="stat-icon bg-white/20 backdrop-blur-sm">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label">Total Tasks</p>
            <p class="stat-value">{{ statistics.totalTasks }}</p>
            <p class="stat-description">
              <span v-if="statistics.totalTasks > 0">{{ statistics.totalSubtasks }} subtasks</span>
              <span v-else>No tasks yet</span>
            </p>
          </div>
        </div>

        <!-- Ongoing Tasks Card -->
        <div class="stat-card bg-gradient-to-br from-amber-500 via-orange-500 to-amber-600">
          <div class="stat-pattern"></div>
          <div class="stat-icon bg-white/20 backdrop-blur-sm">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label">In Progress</p>
            <p class="stat-value">{{ statistics.ongoingTasks }}</p>
            <p class="stat-description">Active tasks</p>
          </div>
        </div>

        <!-- Completed Tasks Card -->
        <div class="stat-card bg-gradient-to-br from-green-500 via-emerald-500 to-green-600">
          <div class="stat-pattern"></div>
          <div class="stat-icon bg-white/20 backdrop-blur-sm">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label">Completed</p>
            <p class="stat-value">{{ statistics.completedTasks }}</p>
            <p class="stat-description">
              {{ completionRate }}% completion rate
            </p>
          </div>
        </div>

        <!-- Overdue Tasks Card -->
        <div class="stat-card bg-gradient-to-br from-red-500 via-rose-500 to-red-600">
          <div class="stat-pattern"></div>
          <div class="stat-icon bg-white/20 backdrop-blur-sm">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label">Overdue</p>
            <p class="stat-value">{{ statistics.overdueTasks }}</p>
            <p class="stat-description">
              <span v-if="statistics.overdueTasks > 0">Needs attention!</span>
              <span v-else>All on track</span>
            </p>
          </div>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Sidebar -->
        <div class="lg:col-span-1 space-y-6">
          <!-- Quick Actions -->
          <div class="card">
            <div class="card-header">
              <h2 class="card-title">
                <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Quick Actions
              </h2>
            </div>
            <div class="card-body space-y-2">
              <button @click="navigateTo('/tasks')" class="quick-action-btn group">
                <div
                  class="quick-action-icon bg-green-100 text-green-600 group-hover:bg-green-600 group-hover:text-white">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <span class="font-medium text-gray-700 group-hover:text-gray-900">View All Tasks</span>
                <svg class="w-4 h-4 text-gray-400 ml-auto transform group-hover:translate-x-1 transition-transform"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <button @click="navigateTo('/projects')" class="quick-action-btn group">
                <div
                  class="quick-action-icon bg-purple-100 text-purple-600 group-hover:bg-purple-600 group-hover:text-white">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                </div>
                <span class="font-medium text-gray-700 group-hover:text-gray-900">Browse Projects</span>
                <svg class="w-4 h-4 text-gray-400 ml-auto transform group-hover:translate-x-1 transition-transform"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <button @click="navigateTo('/profile')" class="quick-action-btn group">
                <div
                  class="quick-action-icon bg-amber-100 text-amber-600 group-hover:bg-amber-600 group-hover:text-white">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <span class="font-medium text-gray-700 group-hover:text-gray-900">View Profile</span>
                <svg class="w-4 h-4 text-gray-400 ml-auto transform group-hover:translate-x-1 transition-transform"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <!-- Add inside quick actions or suitable place -->
<button @click="openReport" class="quick-action-btn group">
  <div class="quick-action-icon bg-indigo-100 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
  </div>
  <span class="font-medium text-gray-700 group-hover:text-gray-900">Generate Project Report</span>
</button>

            </div>
          </div>

          <!-- Priority Distribution -->
          <div class="card">
            <div class="card-header">
              <h2 class="card-title">
                <svg class="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Priority Breakdown
              </h2>
            </div>
            <div class="card-body">
              <div v-if="statistics.totalTasks > 0" class="space-y-4">
                <div class="priority-bar-item">
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-sm font-semibold text-gray-700 flex items-center gap-2">
                      <span class="w-3 h-3 rounded-full bg-red-500"></span>
                      Critical (8-10)
                    </span>
                    <span class="text-sm font-bold text-gray-900">{{ statistics.criticalPriority }}</span>
                  </div>
                  <div class="priority-bar bg-red-100">
                    <div class="priority-bar-fill bg-gradient-to-r from-red-500 to-red-600"
                      :style="{ width: `${(statistics.criticalPriority / statistics.totalTasks) * 100}%` }">
                    </div>
                  </div>
                </div>
                <div class="priority-bar-item">
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-sm font-semibold text-gray-700 flex items-center gap-2">
                      <span class="w-3 h-3 rounded-full bg-orange-500"></span>
                      High (6-7)
                    </span>
                    <span class="text-sm font-bold text-gray-900">{{ statistics.highPriority }}</span>
                  </div>
                  <div class="priority-bar bg-orange-100">
                    <div class="priority-bar-fill bg-gradient-to-r from-orange-500 to-orange-600"
                      :style="{ width: `${(statistics.highPriority / statistics.totalTasks) * 100}%` }">
                    </div>
                  </div>
                </div>
                <div class="priority-bar-item">
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-sm font-semibold text-gray-700 flex items-center gap-2">
                      <span class="w-3 h-3 rounded-full bg-blue-500"></span>
                      Medium (4-5)
                    </span>
                    <span class="text-sm font-bold text-gray-900">{{ statistics.mediumPriority }}</span>
                  </div>
                  <div class="priority-bar bg-blue-100">
                    <div class="priority-bar-fill bg-gradient-to-r from-blue-500 to-blue-600"
                      :style="{ width: `${(statistics.mediumPriority / statistics.totalTasks) * 100}%` }">
                    </div>
                  </div>
                </div>
                <div class="priority-bar-item">
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-sm font-semibold text-gray-700 flex items-center gap-2">
                      <span class="w-3 h-3 rounded-full bg-gray-400"></span>
                      Low (1-3)
                    </span>
                    <span class="text-sm font-bold text-gray-900">{{ statistics.lowPriority }}</span>
                  </div>
                  <div class="priority-bar bg-gray-100">
                    <div class="priority-bar-fill bg-gradient-to-r from-gray-400 to-gray-500"
                      :style="{ width: `${(statistics.lowPriority / statistics.totalTasks) * 100}%` }">
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state-small">
                <svg class="w-12 h-12 text-gray-300 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p class="text-gray-500 text-sm text-center">No tasks to analyze</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Main Content -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Upcoming Deadlines -->
          <div class="card">
            <div class="card-header">
              <h2 class="card-title">
                <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Upcoming Deadlines
              </h2>
              <button @click="navigateTo('/tasks')" class="view-all-btn">
                View All
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            <div class="card-body">
              <div v-if="upcomingTasks.length > 0" class="space-y-3">
                <div v-for="task in upcomingTasks" :key="task.taskId || task.subTaskId" class="task-item"
                  @click="navigateToTask(task)">
                  <div class="flex items-start justify-between gap-4">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-2">
                        <h3 class="font-semibold text-gray-900 truncate">{{ task.title }}</h3>
                        <span v-if="task.priority" class="priority-badge" :class="getPriorityBadgeClass(task.priority)">
                          ⭐{{ task.priority }}
                        </span>
                      </div>
                      <div class="flex items-center gap-3 text-sm text-gray-600">
                        <span class="flex items-center gap-1">
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          {{ formatDeadline(task.deadline) }}
                        </span>
                        <span :class="getDeadlineClass(task.deadline)" class="font-semibold">
                          {{ getDeadlineStatus(task.deadline) }}
                        </span>
                      </div>
                    </div>
                    <span class="status-badge" :class="getStatusClass(task.status)">
                      {{ formatStatus(task.status) }}
                    </span>
                  </div>
                </div>
              </div>

              <div v-else class="empty-state">
                <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p class="text-gray-600 font-medium text-center mb-1">No upcoming deadlines</p>
                <p class="text-gray-400 text-sm text-center">You're all caught up!</p>
              </div>
            </div>
          </div>

          <!-- Recent Activity -->
          <div class="card">
            <div class="card-header">
              <h2 class="card-title">
                <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Recent Activity
              </h2>
              <button @click="navigateTo('/tasks')" class="view-all-btn">
                View All
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            <div class="card-body">
              <div v-if="recentTasks.length > 0" class="space-y-3">
                <div v-for="task in recentTasks" :key="task.taskId || task.subTaskId" class="activity-item"
                  @click="navigateToTask(task)">
                  <div class="flex items-center gap-3">
                    <div class="activity-icon" :class="getActivityIconClass(task.status)">
                      <svg v-if="task.status === 'completed'" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clip-rule="evenodd" />
                      </svg>
                      <svg v-else-if="task.status === 'ongoing'" class="w-4 h-4" fill="none" stroke="currentColor"
                        viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <h3 class="font-medium text-gray-900 truncate">{{ task.title }}</h3>
                        <span v-if="task.priority" class="text-xs priority-badge"
                          :class="getPriorityBadgeClass(task.priority)">
                          ⭐{{ task.priority }}
                        </span>
                      </div>
                      <p class="text-sm text-gray-500">
                        {{ getActivityDescription(task) }}
                      </p>
                    </div>
                    <span class="text-xs text-gray-400 whitespace-nowrap font-medium">
                      {{ formatRelativeTime(task.updatedAt || task.createdAt) }}
                    </span>
                  </div>
                </div>
              </div>

              <div v-else class="empty-state">
                <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p class="text-gray-600 font-medium text-center mb-1">No recent activity</p>
                <p class="text-gray-400 text-sm text-center mb-3">Start creating tasks to see activity here</p>
                <button @click="navigateTo('/tasks')" class="cta-button">
                  Create Your First Task
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Projects Overview -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">
            <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            Active Projects
          </h2>
          <button @click="navigateTo('/projects')" class="view-all-btn">
            View All
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <div class="card-body">
          <div v-if="projects.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="project in projects.slice(0, 6)" :key="project.projectId" class="project-card"
              @click="navigateTo('/projects')">
              <div class="project-card-icon">
                <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <h3 class="font-semibold text-gray-900 mb-2 truncate">{{ project.title }}</h3>
              <p v-if="project.description" class="text-sm text-gray-600 mb-3 line-clamp-2">
                {{ project.description }}
              </p>
              <div class="flex items-center justify-between text-sm mt-auto pt-3 border-t border-gray-100">
                <span class="text-gray-600 font-medium flex items-center gap-1">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  {{ getProjectTaskCount(project.projectId) }} tasks
                </span>
                <span class="text-xs text-gray-400">
                  {{ formatDate(project.creationDate) }}
                </span>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            <p class="text-gray-600 font-medium text-center mb-1">No active projects</p>
            <p class="text-gray-400 text-sm text-center mb-3">Create your first project to get started</p>
            <button @click="navigateTo('/projects')" class="cta-button">
              Create Your First Project
            </button>
          </div>
        </div>
      </div>

<!-- Project Report Modal -->
<div v-if="showReport" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
  <div class="bg-white rounded-lg shadow-lg max-w-5xl max-h-[80vh] overflow-y-auto p-6">
    <h2 class="text-3xl font-bold mb-6 border-b pb-2">Project Report</h2>

    <div id="report-content" class="space-y-8">
      <section v-for="project in projectsForReport" :key="project.projectId" class="border-b pb-4">
        <h3 class="text-2xl font-semibold text-indigo-700 mb-3">{{ project.title }}</h3>

        <div v-if="tasksByProject(project.projectId).length === 0" class="italic text-gray-400 ml-4">
          No tasks for this project.
        </div>

        <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div v-for="(tasksGroup, status) in categorizedTasksByStatus(project.projectId)" :key="status" class="bg-gray-50 rounded p-4 border">
            <h4 class="text-lg font-semibold capitalize mb-2 border-b border-gray-300 pb-1 text-gray-700">{{ status }}</h4>
            <ul>
              <li v-for="task in tasksGroup" :key="task.taskId" class="mb-1">
                <strong>{{ task.title }}</strong> — Due: {{ formatDeadline(task.deadline) }}
              </li>
            </ul>
          </div>
        </div>
      </section>
    </div>

    <div class="mt-6 flex justify-end gap-4">
      <button @click="exportPDF" class="px-5 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition">
        Export as PDF
      </button>
      <button @click="showReport = false" class="px-5 py-2 border rounded hover:bg-gray-100 transition">
        Close
      </button>
    </div>
  </div>
</div>




    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { useAuthStore } from '@/stores/auth'
import NavigationBar from '@/components/NavigationBar.vue'
import axios from 'axios'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas-pro'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const authStore = useAuthStore()

// Reactive data
const loading = ref(true)
const tasks = ref([])
const subtasks = ref([])
const projects = ref([])

const showReport = ref(false)
const tasksForReport = ref([])
const projectsForReport = ref([])  // Added for report projects grouping

// Statistics
const statistics = ref({
  totalTasks: 0,
  totalSubtasks: 0,
  ongoingTasks: 0,
  completedTasks: 0,
  overdueTasks: 0,
  dueSoonTasks: 0,
  criticalPriority: 0,
  highPriority: 0,
  mediumPriority: 0,
  lowPriority: 0
})

// Computed properties
const completionRate = computed(() => {
  if (statistics.value.totalTasks === 0) return 0
  return Math.round((statistics.value.completedTasks / statistics.value.totalTasks) * 100)
})

const upcomingTasks = computed(() => {
  const now = Date.now() / 1000
  const allTasks = [...tasks.value, ...subtasks.value]
  return allTasks
    .filter(task => task.deadline && task.deadline > now && task.status !== 'completed')
    .sort((a, b) => a.deadline - b.deadline)
    .slice(0, 5)
})

const recentTasks = computed(() => {
  const allTasks = [...tasks.value, ...subtasks.value]
  return allTasks
    .sort((a, b) => (b.updatedAt || b.createdAt) - (a.updatedAt || a.createdAt))
    .slice(0, 5)
})

// Categorized for all tasks for basic usage
const categorized = computed(() => ({
  projected: tasksForReport.value.filter(t => t.status === 'projected'),
  'in progress': tasksForReport.value.filter(t => t.status === 'ongoing'),
  'under review': tasksForReport.value.filter(t => t.status === 'under_review'),
  completed: tasksForReport.value.filter(t => t.status === 'completed')
}))

// Helper: Returns tasks for a specific project
function tasksByProject(projectId) {
  return tasksForReport.value.filter(task => task.projectId === projectId)
}

// Helper: Categorizes tasks for one project
function categorizedTasksByStatus(projectId) {
  const projectTasks = tasksByProject(projectId)
  const allCategories = {
    projected: projectTasks.filter(t => t.status === 'projected'),
    'in progress': projectTasks.filter(t => t.status === 'ongoing'),
    'under review': projectTasks.filter(t => t.status === 'under_review'),
    completed: projectTasks.filter(t => t.status === 'completed'),
  }
  return Object.fromEntries(
    Object.entries(allCategories).filter(([_, tasks]) => tasks.length > 0)
  )
}


// Methods
async function fetchData() {
  loading.value = true
  try {
    await Promise.all([
      fetchTasks(),
      fetchSubtasks(),
      fetchProjects()
    ])
    calculateStatistics()
  } catch (error) {
    console.error('Error fetching dashboard data:', error)
    toast.error('Failed to load dashboard data')
  } finally {
    loading.value = false
  }
}

async function fetchTasks() {
  try {
    const response = await axios.get(`${import.meta.env.VITE_BACKEND_API}tasks`)
    const currentUserId = authStore.user?.uid
    tasks.value = (response.data.tasks || []).filter(task =>
      task.ownerId === currentUserId ||
      task.collaborators?.includes(currentUserId) ||
      task.creatorId === currentUserId
    )
  } catch (error) {
    console.error('Error fetching tasks:', error)
    tasks.value = []
  }
}

async function fetchSubtasks() {
  try {
    const response = await axios.get(`${import.meta.env.VITE_BACKEND_API}subtasks`)
    const currentUserId = authStore.user?.uid
    subtasks.value = (response.data.subtasks || []).filter(subtask =>
      subtask.ownerId === currentUserId ||
      subtask.collaborators?.includes(currentUserId) ||
      subtask.creatorId === currentUserId
    )
  } catch (error) {
    console.error('Error fetching subtasks:', error)
    subtasks.value = []
  }
}

async function fetchProjects() {
  try {
    if (!authStore.user?.uid) return
    const response = await axios.get(`${import.meta.env.VITE_BACKEND_API}project/${authStore.user.uid}`)
    projects.value = response.data.projects || []
  } catch (error) {
    console.error('Error fetching projects:', error)
    projects.value = []
  }
}

function exportPDF() {
  const element = document.getElementById('report-content')
  html2canvas(element, { scale: 2 }).then(canvas => {
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const width = pdf.internal.pageSize.getWidth()
    const height = (canvas.height * width) / canvas.width
    pdf.addImage(imgData, 'PNG', 0, 0, width, height)
    pdf.save('Project_Report.pdf')
  })
}

function openReport() {
  tasksForReport.value = tasks.value     // existing tasks
  projectsForReport.value = projects.value  // existing projects
  showReport.value = true
}

function calculateStatistics() {
  const now = Date.now() / 1000
  const sevenDaysFromNow = now + (7 * 24 * 60 * 60)

  statistics.value = {
    totalTasks: tasks.value.length,
    totalSubtasks: subtasks.value.length,
    ongoingTasks: tasks.value.filter(t => t.status === 'ongoing').length,
    completedTasks: tasks.value.filter(t => t.status === 'completed').length,
    overdueTasks: tasks.value.filter(t => t.deadline && t.deadline < now && t.status !== 'completed').length,
    dueSoonTasks: tasks.value.filter(t => t.deadline && t.deadline > now && t.deadline < sevenDaysFromNow).length,
    criticalPriority: tasks.value.filter(t => (t.priority || 0) >= 8).length,
    highPriority: tasks.value.filter(t => (t.priority || 0) >= 6 && (t.priority || 0) < 8).length,
    mediumPriority: tasks.value.filter(t => (t.priority || 0) >= 4 && (t.priority || 0) < 6).length,
    lowPriority: tasks.value.filter(t => (t.priority || 0) < 4).length
  }
}

function getUserDisplayName() {
  return authStore.user?.displayName || authStore.user?.name || authStore.user?.email || 'User'
}

function navigateTo(path) {
  router.push(path)
}

function navigateToTask(task) {
  window.selectedTaskForView = task
  router.push('/tasks')
}

function getProjectTaskCount(projectId) {
  return tasks.value.filter(t => t.projectId === projectId).length
}

function formatDeadline(deadline) {
  if (!deadline) return 'No deadline'
  const date = new Date(deadline * 1000)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
  })
}

function formatDate(timestamp) {
  if (!timestamp) return 'Unknown'
  const date = new Date(timestamp * 1000)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatRelativeTime(timestamp) {
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
  return formatDate(timestamp)
}

function getDeadlineStatus(deadline) {
  if (!deadline) return 'No deadline'
  const now = Date.now() / 1000
  const daysUntil = Math.ceil((deadline - now) / 86400)

  if (daysUntil < 0) return 'Overdue'
  if (daysUntil === 0) return 'Due today'
  if (daysUntil === 1) return 'Due tomorrow'
  if (daysUntil <= 7) return `Due in ${daysUntil} days`
  return ''
}

function getDeadlineClass(deadline) {
  if (!deadline) return ''
  const now = Date.now() / 1000
  const daysUntil = (deadline - now) / 86400

  if (daysUntil < 0) return 'text-red-600'
  if (daysUntil <= 1) return 'text-red-500'
  if (daysUntil <= 3) return 'text-orange-500'
  if (daysUntil <= 7) return 'text-amber-500'
  return 'text-gray-500'
}

function formatStatus(status) {
  const statusMap = {
    'unassigned': 'Unassigned',
    'ongoing': 'Ongoing',
    'under_review': 'Under Review',
    'completed': 'Completed'
  }
  return statusMap[status] || status
}

function getStatusClass(status) {
  const classMap = {
    'unassigned': 'status-unassigned',
    'ongoing': 'status-ongoing',
    'under_review': 'status-review',
    'completed': 'status-completed'
  }
  return classMap[status] || 'status-default'
}

function getPriorityBadgeClass(priority) {
  const p = priority || 5
  if (p >= 8) return 'priority-critical'
  if (p >= 6) return 'priority-high'
  if (p >= 4) return 'priority-medium'
  return 'priority-low'
}

function getActivityIconClass(status) {
  const classMap = {
    'completed': 'bg-green-100 text-green-600',
    'ongoing': 'bg-blue-100 text-blue-600',
    'under_review': 'bg-purple-100 text-purple-600',
    'unassigned': 'bg-amber-100 text-amber-600'
  }
  return classMap[status] || 'bg-gray-100 text-gray-600'
}

function getActivityDescription(task) {
  const status = formatStatus(task.status)
  if (task.subTaskId) {
    return `Subtask is ${status.toLowerCase()}`
  }
  return `Task is ${status.toLowerCase()}`
}

onMounted(async () => {
  console.log('Dashboard mounted, route query:', route.query)
  await fetchData()
  await nextTick()
  
  if (route.query.newUser === 'true') {
    console.log('Showing welcome toast for new user')
    setTimeout(() => {
      toast.success('Account created successfully! Welcome to Smart Task Management System.', {
        timeout: 5000,
        closeOnClick: true,
        pauseOnFocusLoss: false,
        pauseOnHover: true,
        draggable: true,
        draggablePercent: 0.6,
        showCloseButtonOnHover: false,
        hideProgressBar: false,
        closeButton: "button",
        icon: true
      })
    }, 500)
  }
})
</script>


<style scoped>
/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fadeIn 0.6s ease-out;
}

.animate-slide-up {
  animation: slideUp 0.8s ease-out;
}

/* Card Components */
.card {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  border: 1px solid rgb(229 231 235);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  border-color: rgb(209 213 219);
}

.card-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgb(243 244 246);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(to right, rgb(249 250 251), rgb(255 255 255));
}

.card-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(17 24 39);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.card-body {
  padding: 1.5rem;
}

.view-all-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(37 99 235);
  transition: all 0.2s;
}

.view-all-btn:hover {
  color: rgb(29 78 216);
  gap: 0.5rem;
}

/* Stat Cards */
.stat-card {
  position: relative;
  overflow: hidden;
  border-radius: 1rem;
  padding: 1.75rem;
  color: white;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  transform: translateY(-0.375rem) scale(1.02);
  box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
}

.stat-pattern {
  position: absolute;
  top: 0;
  right: 0;
  width: 100%;
  height: 100%;
  background-image: radial-gradient(circle at 2px 2px, rgba(255, 255, 255, 0.15) 1px, transparent 0);
  background-size: 32px 32px;
  opacity: 0.3;
}

.stat-icon {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
  width: 4rem;
  height: 4rem;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.stat-card:hover .stat-icon {
  transform: rotate(5deg) scale(1.1);
}

.stat-content {
  position: relative;
  z-index: 10;
}

.stat-label {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 0.25rem;
  line-height: 1;
}

.stat-description {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.875rem;
  font-weight: 500;
}

/* Quick Actions */
.quick-action-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem 1rem;
  border-radius: 0.75rem;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: left;
  border: 2px solid transparent;
  background: white;
}

.quick-action-btn:hover {
  background: rgb(249 250 251);
  border-color: rgb(229 231 235);
  transform: translateX(0.25rem);
}

.quick-action-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

/* Priority Bars */
.priority-bar-item {
  transition: all 0.3s;
}

.priority-bar {
  height: 0.625rem;
  border-radius: 9999px;
  overflow: hidden;
  box-shadow: inset 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

.priority-bar-fill {
  height: 100%;
  border-radius: 9999px;
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px 0 rgb(0 0 0 / 0.1);
}

/* Task Items */
.task-item {
  padding: 1.25rem;
  border: 2px solid rgb(243 244 246);
  border-radius: 0.75rem;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  background: white;
}

.task-item:hover {
  background: rgb(249 250 251);
  border-color: rgb(191 219 254);
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  transform: translateX(0.25rem);
}

/* Activity Items */
.activity-item {
  padding: 1rem;
  border: 2px solid rgb(243 244 246);
  border-radius: 0.75rem;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  background: white;
}

.activity-item:hover {
  background: rgb(249 250 251);
  border-color: rgb(191 219 254);
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
}

.activity-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.activity-item:hover .activity-icon {
  transform: scale(1.1);
}

/* Status Badges */
.status-badge {
  padding: 0.375rem 0.875rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-unassigned {
  background: linear-gradient(135deg, rgb(254 243 199) 0%, rgb(253 230 138) 100%);
  color: rgb(146 64 14);
}

.status-ongoing {
  background: linear-gradient(135deg, rgb(219 234 254) 0%, rgb(191 219 254) 100%);
  color: rgb(30 64 175);
}

.status-review {
  background: linear-gradient(135deg, rgb(243 232 255) 0%, rgb(233 213 255) 100%);
  color: rgb(88 28 135);
}

.status-completed {
  background: linear-gradient(135deg, rgb(220 252 231) 0%, rgb(187 247 208) 100%);
  color: rgb(22 101 52);
}

/* Priority Badges */
.priority-badge {
  padding: 0.25rem 0.625rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 800;
  white-space: nowrap;
}

.priority-critical {
  background: linear-gradient(135deg, rgb(254 226 226) 0%, rgb(252 165 165) 100%);
  color: rgb(153 27 27);
}

.priority-high {
  background: linear-gradient(135deg, rgb(255 237 213) 0%, rgb(253 186 116) 100%);
  color: rgb(154 52 18);
}

.priority-medium {
  background: linear-gradient(135deg, rgb(219 234 254) 0%, rgb(191 219 254) 100%);
  color: rgb(30 64 175);
}

.priority-low {
  background: linear-gradient(135deg, rgb(243 244 246) 0%, rgb(229 231 235) 100%);
  color: rgb(55 65 81);
}

/* Project Cards */
.project-card {
  padding: 1.25rem;
  border: 2px solid rgb(243 244 246);
  border-radius: 0.75rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  background: white;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.project-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, rgb(168 85 247), rgb(147 51 234));
  transform: scaleX(0);
  transition: transform 0.3s;
}

.project-card:hover::before {
  transform: scaleX(1);
}

.project-card:hover {
  border-color: rgb(216 180 254);
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  transform: translateY(-0.25rem);
}

.project-card-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  background: linear-gradient(135deg, rgb(243 232 255), rgb(233 213 255));
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.75rem;
  transition: all 0.3s;
}

.project-card:hover .project-card-icon {
  transform: rotate(5deg) scale(1.1);
  background: linear-gradient(135deg, rgb(233 213 255), rgb(216 180 254));
}

/* Empty States */
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
}

.empty-state-small {
  text-align: center;
  padding: 2rem 1rem;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, rgb(59 130 246), rgb(37 99 235));
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  border-radius: 0.5rem;
  transition: all 0.3s;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
}

.cta-button:hover {
  background: linear-gradient(135deg, rgb(37 99 235), rgb(29 78 216));
  transform: translateY(-0.125rem);
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}

/* Utility Classes */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
