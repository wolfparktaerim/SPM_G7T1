// Routing rules & logics
// Once you created a view page, you must register the page here so that the app can route to it with the right url endpoint eg: /profile

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'

// import views
import HomeView from '../views/HomeView.vue'
import NotFoundView from '../views/NotFoundView.vue'
import UnauthorizedView from '@/views/UnauthorizedView.vue'
import DashboardView from '@/views/DashboardView.vue'
import ProjectsView from '@/views/ProjectsView.vue'
import TasksView from '@/views/TasksView.vue'
import ProfileView from '@/views/ProfileView.vue'
import SettingsView from '@/views/SettingsView.vue'
import AuthenticationView from '@/views/AuthView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: false },
    },
    {
      path: '/auth',
      name: 'authentication',
      component: AuthenticationView,
      meta: { requiresAuth: false },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true },
    },
    {
      path: '/projects',
      name: 'projects',
      component: ProjectsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: TasksView,
      meta: { requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { requiresAuth: true },
    },

    {
      path: '/:catchAll(.*)',
      component: NotFoundView,
      meta: { requiresAuth: false },
    },
    {
      path: '/unauthorized',
      name: 'unauthorized',
      component: UnauthorizedView,
      meta: { requiresAuth: false },
    },
  ],
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Set router instance in auth store for navigation
  authStore.setRouter(router)

  // Wait for auth initialization if not already done
  if (!authStore.initialized) {
    await authStore.initializeAuth()
  }

  // Check if route requires authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/auth')
    return
  }

  // Redirect user to dashboard if they try to go /auth or home page
  if ((to.name == 'authentication' || to.name == 'home') && authStore.isAuthenticated) {
    // Preserve query parameters when redirecting to dashboard
    next({ path: '/dashboard', query: to.query })
    return
  }
  next()
})

export default router
