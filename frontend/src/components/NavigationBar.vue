<!-- src/components/NavigationBar.vue -->
<!--
  You need to import this component file in every view page:

  <template>
    <NavigationBar />
  </template>
  <script setup>
  import NavigationBar from '@/components/NavigationBar.vue';
  </script>

-->
<template>
  <!-- Enhanced Navigation Header -->
  <nav class="bg-white/95 backdrop-blur-xl shadow-xl border-b border-white/30 sticky top-0 z-50">
    <div class="w-full px-6 sm:px-8 lg:px-12">
      <div class="flex justify-between h-16">
        <!-- Logo and Navigation -->
        <div class="flex">
          <!-- Enhanced Logo -->
          <div class="flex-shrink-0 flex items-center group">
            <router-link to="/dashboard"
              class="flex items-center space-x-3 text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-clip-text text-transparent hover:from-blue-700 hover:via-purple-700 hover:to-blue-700 transition-all duration-500 bg-size-200 hover:bg-pos-100 transform hover:scale-105">
              <CheckSquare class="w-8 h-8 text-blue-500 group-hover:text-blue-600 transition-colors duration-300" />
              <span>STMS</span>
            </router-link>
          </div>

          <!-- Enhanced Navigation Links -->
          <div class="hidden sm:ml-10 sm:flex sm:items-center sm:space-x-2">
            <router-link v-for="item in navigationItems" :key="item.name" :to="item.route"
              class="relative px-4 py-2 text-gray-600 hover:text-gray-900 font-semibold text-sm transition-all duration-300 group rounded-xl"
              :class="getNavLinkClass(item.route)">

              <!-- Background highlight for active/hover -->
              <div class="absolute inset-0 rounded-xl transition-all duration-300"
                :class="getNavBackgroundClass(item.route)"></div>

              <!-- Icon for each nav item -->
              <div class="relative flex items-center space-x-2">
                <component :is="getNavIcon(item.name)" class="w-4 h-4 transition-all duration-300"
                  :class="getNavIconClass(item.route)" :stroke-width="2" />
                <span class="relative z-10">{{ item.label }}</span>
              </div>

              <!-- Hover glow effect -->
              <div
                class="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-20 transition-opacity duration-300 bg-gradient-to-r from-blue-400 to-purple-400 blur-sm">
              </div>
            </router-link>
          </div>
        </div>

        <!-- User Menu and Mobile Button -->
        <div class="flex items-center space-x-4 z-50">
          <!-- Notification Bell - Hidden on mobile -->
          <div class="relative hidden sm:block" v-if="authStore.isAuthenticated">
            <button @click="toggleNotificationCard"
              class="relative p-2 rounded-xl hover:bg-gray-50 transition-all duration-300 group">
              <Bell
                class="w-6 h-6 text-gray-600 group-hover:text-blue-600 transition-colors duration-300"
                :stroke-width="2"
              />
              <!-- Unread count badge -->
              <span
                v-if="unreadNotificationCount > 0"
                class="absolute -top-1 -right-1 flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full ring-2 ring-white"
              >
                {{ unreadNotificationCount > 9 ? '9+' : unreadNotificationCount }}
              </span>
            </button>

            <!-- Notification Card -->
            <NotificationCard
              :show="showNotificationCard"
              @update:show="showNotificationCard = $event"
              @unreadCountChange="handleUnreadCountChange"
            />
          </div>

          <!-- Enhanced User Menu - Hidden on mobile -->
          <div class="relative hidden sm:block" v-if="authStore.isAuthenticated">
            <button @click="toggleUserMenu"
              class="flex items-center space-x-3 p-2 rounded-xl hover:bg-gray-50 transition-all duration-300 group">
              <div class="relative">
                <div
                  class="w-10 h-10 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white text-sm font-semibold ring-2 ring-gray-200 group-hover:ring-blue-300 transition-all duration-300">
                  <User class="w-5 h-5" />
                </div>
                <!-- Online status indicator -->
                <div
                  class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 border-2 border-white rounded-full animate-pulse">
                </div>
              </div>
              <div class="hidden md:block text-left">
                <div
                  class="text-sm font-semibold text-gray-900 group-hover:text-blue-600 transition-colors duration-300">
                  {{ getUserDisplayName() }}
                </div>
                <div class="text-xs text-gray-500">{{ getUserEmail() }}</div>
              </div>
              <ChevronDown class="w-4 h-4 text-gray-400 transition-all duration-300 group-hover:text-blue-500"
                :class="{ 'rotate-180': showUserMenu }" :stroke-width="2" />
            </button>

            <!-- Enhanced User Menu Dropdown -->
            <transition enter-active-class="transition ease-out duration-200"
              enter-from-class="transform opacity-0 scale-95 translate-y-2"
              enter-to-class="transform opacity-100 scale-100 translate-y-0"
              leave-active-class="transition ease-in duration-150"
              leave-from-class="transform opacity-100 scale-100 translate-y-0"
              leave-to-class="transform opacity-0 scale-95 translate-y-2">
              <div v-if="showUserMenu"
                class="absolute right-0 mt-3 w-80 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/50 overflow-hidden z-50 origin-top-right">

                <!-- User Info Header -->
                <div class="p-6 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-600">
                  <div class="flex items-center space-x-4">
                    <div class="relative">
                      <div
                        class="w-14 h-14 rounded-xl bg-gradient-to-r from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold text-lg ring-3 ring-white/30">
                        <User class="w-7 h-7" />
                      </div>
                      <div class="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 border-2 border-white rounded-full">
                      </div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-lg font-bold text-white truncate">
                        {{ getUserDisplayName() }}
                      </p>
                      <p class="text-sm text-blue-100 truncate">{{ getUserEmail() }}</p>
                    </div>
                  </div>
                </div>

                <!-- Menu Items -->
                <div class="py-3">
                  <router-link to="/profile" @click="showUserMenu = false"
                    class="group flex items-center px-6 py-4 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 hover:text-gray-900 transition-all duration-300">
                    <div
                      class="mr-4 w-10 h-10 rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 flex items-center justify-center group-hover:from-blue-600 group-hover:to-blue-700 group-hover:scale-110 transition-all duration-300">
                      <UserCircle class="w-5 h-5 text-white" :stroke-width="2" />
                    </div>
                    <div class="flex-1">
                      <p class="font-semibold">Profile</p>
                      <p class="text-xs text-gray-500">Manage your profile settings</p>
                    </div>
                    <ChevronRight class="w-4 h-4 text-gray-400 group-hover:text-blue-500 transition-colors duration-300"
                      :stroke-width="2" />
                  </router-link>

                  <router-link to="/settings" @click="showUserMenu = false"
                    class="group flex items-center px-6 py-4 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 hover:text-gray-900 transition-all duration-300">
                    <div
                      class="mr-4 w-10 h-10 rounded-xl bg-gradient-to-r from-purple-500 to-purple-600 flex items-center justify-center group-hover:from-purple-600 group-hover:to-purple-700 group-hover:scale-110 transition-all duration-300">
                      <Settings class="w-5 h-5 text-white" :stroke-width="2" />
                    </div>
                    <div class="flex-1">
                      <p class="font-semibold">Settings</p>
                      <p class="text-xs text-gray-500">Configure your preferences</p>
                    </div>
                    <ChevronRight class="w-4 h-4 text-gray-400 group-hover:text-blue-500 transition-colors duration-300"
                      :stroke-width="2" />
                  </router-link>

                  <hr class="my-3 border-gray-200">

                  <button @click="showLogoutModal"
                    class="group flex items-center w-full px-6 py-4 text-red-600 hover:text-red-700 hover:bg-red-50 transition-all duration-300">
                    <div
                      class="mr-4 w-10 h-10 rounded-xl bg-gradient-to-r from-red-500 to-red-600 flex items-center justify-center group-hover:from-red-600 group-hover:to-red-700 group-hover:scale-110 transition-all duration-300">
                      <LogOut class="w-5 h-5 text-white" :stroke-width="2" />
                    </div>
                    <div class="flex-1 text-left">
                      <p class="font-semibold">Logout</p>
                      <p class="text-xs text-gray-500">Sign out of your account</p>
                    </div>
                  </button>
                </div>
              </div>
            </transition>
          </div>

          <!-- Enhanced Mobile Menu Button -->
          <button @click="showMobileMenu = !showMobileMenu"
            class="sm:hidden relative p-2 rounded-xl text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-all duration-300 group">
            <div class="w-6 h-6 flex flex-col justify-center items-center">
              <span class="absolute w-5 h-0.5 bg-current transform transition-all duration-300 ease-in-out"
                :class="showMobileMenu ? 'rotate-45' : '-translate-y-1.5'"></span>
              <span class="w-5 h-0.5 bg-current transition-all duration-300 ease-in-out"
                :class="showMobileMenu ? 'opacity-0' : ''"></span>
              <span class="absolute w-5 h-0.5 bg-current transform transition-all duration-300 ease-in-out"
                :class="showMobileMenu ? '-rotate-45' : 'translate-y-1.5'"></span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Enhanced Mobile Navigation Menu -->
    <transition enter-active-class="transition ease-out duration-300"
      enter-from-class="transform opacity-0 scale-95 -translate-y-4"
      enter-to-class="transform opacity-100 scale-100 translate-y-0"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="transform opacity-100 scale-100 translate-y-0"
      leave-to-class="transform opacity-0 scale-95 -translate-y-4">
      <div v-if="showMobileMenu" class="sm:hidden bg-white/95 backdrop-blur-xl border-t border-gray-100 shadow-2xl">
        <!-- Navigation Links -->
        <div class="pt-4 pb-3 space-y-2 px-4">
          <router-link v-for="item in navigationItems" :key="item.name" :to="item.route" @click="showMobileMenu = false"
            class="group flex items-center px-4 py-3 rounded-xl text-base font-semibold transition-all duration-300"
            :class="getMobileNavClass(item.route)">

            <!-- Icon -->
            <div class="mr-4 p-2 rounded-lg transition-all duration-300" :class="getMobileNavIconBg(item.route)">
              <component :is="getNavIcon(item.name)" class="w-5 h-5 transition-colors duration-300"
                :class="getMobileNavIconColor(item.route)" :stroke-width="2" />
            </div>

            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span>{{ item.label }}</span>
                <!-- Active indicator -->
                <div v-if="isActiveRoute(item.route)"
                  class="w-2 h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse">
                </div>
              </div>
            </div>
          </router-link>
        </div>

        <!-- User Section (only show if authenticated) -->
        <div v-if="authStore.isAuthenticated"
          class="pt-4 pb-3 border-t border-gray-200 bg-gradient-to-r from-gray-50 to-blue-50/30">
          <!-- User Info -->
          <div class="flex items-center px-6 mb-4">
            <div class="relative">
              <div
                class="w-12 h-12 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold ring-2 ring-gray-200">
                <User class="w-6 h-6" />
              </div>
              <div class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 border-2 border-white rounded-full">
              </div>
            </div>
            <div class="ml-3 flex-1">
              <div class="text-base font-semibold text-gray-900">{{ getUserDisplayName() }}</div>
              <div class="text-sm text-gray-500">{{ getUserEmail() }}</div>
            </div>
          </div>

          <!-- User Menu Links -->
          <div class="space-y-1 px-4">
            <router-link to="/profile" @click="showMobileMenu = false"
              class="group flex items-center px-4 py-3 rounded-xl text-gray-700 hover:bg-white hover:text-gray-900 transition-all duration-300">
              <div
                class="mr-3 w-8 h-8 rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <UserCircle class="w-4 h-4 text-white" :stroke-width="2" />
              </div>
              Profile
            </router-link>

            <router-link to="/settings" @click="showMobileMenu = false"
              class="group flex items-center px-4 py-3 rounded-xl text-gray-700 hover:bg-white hover:text-gray-900 transition-all duration-300">
              <div
                class="mr-3 w-8 h-8 rounded-lg bg-gradient-to-r from-purple-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Settings class="w-4 h-4 text-white" :stroke-width="2" />
              </div>
              Settings
            </router-link>

            <hr class="my-3 border-gray-200">

            <button @click="showLogoutModal"
              class="group flex items-center w-full px-4 py-3 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-xl transition-all duration-300">
              <div
                class="mr-3 w-8 h-8 rounded-lg bg-gradient-to-r from-red-500 to-red-600 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <LogOut class="w-4 h-4 text-white" :stroke-width="2" />
              </div>
              Logout
            </button>
          </div>
        </div>
      </div>
    </transition>
  </nav>

  <!-- Logout Confirmation Modal -->
  <ConfirmationModal :show="showLogoutConfirmation" title="Sign Out"
    description="Are you sure you want to sign out of your account?"
    warning-text="You will need to log in again to access your account" confirm-text="Sign Out"
    cancel-text="Stay Signed In" loading-text="Signing out..." :loading="isLoggingOut" variant="danger" icon="logout"
    @confirm="handleLogout" @cancel="showLogoutConfirmation = false" @update:show="showLogoutConfirmation = $event" />
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  CheckSquare, User, Settings, LogOut, ChevronDown, ChevronRight,
  Home, FolderOpen, ListChecks, UserCircle, Calendar, Bell
} from 'lucide-vue-next'
import ConfirmationModal from '@/components/ConfirmationModal.vue'
import NotificationCard from '@/components/NotificationCard.vue'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'vue-toastification'
import { notificationService } from '@/services/notificationService'
import { useNotificationEvents } from '@/composables/useNotificationEvents'

// Auth store
const authStore = useAuthStore()

// Router composables
const route = useRoute()
const router = useRouter()

// Toast composable
const toast = useToast()

// Notification events composable
const { onNotificationUpdate } = useNotificationEvents()

// State
const showUserMenu = ref(false)
const showNotificationCard = ref(false)
const showMobileMenu = ref(false)
const showLogoutConfirmation = ref(false)
const isLoggingOut = ref(false)
const unreadNotificationCount = ref(0)
let unreadCountInterval = null

// Navigation items with routes
const navigationItems = [
  { name: 'Dashboard', label: 'Dashboard', route: '/dashboard' },
  { name: 'Projects', label: 'Projects', route: '/projects' },
  { name: 'Tasks', label: 'Tasks', route: '/tasks' },
  { name: 'Schedule', label: 'Schedule', route: '/schedule' },
]

// Get navigation icon component
const getNavIcon = (itemName) => {
  const iconMap = {
    'Dashboard': Home,
    'Projects': FolderOpen,
    'Tasks': ListChecks,
    'Schedule': Calendar,
  }
  return iconMap[itemName] || Home
}

// User display name method - now using auth store
const getUserDisplayName = () => {
  if (!authStore.user) return 'User'

  // Try displayName first, then extract from email, or fallback to 'User'
  return authStore.user.displayName ||
    authStore.user.name ||
    'User'
}

// Get user email for display - now using auth store
const getUserEmail = () => {
  return authStore.user?.email || ''
}

// Navigation styling methods using Vue Router
const isActiveRoute = (routePath) => {
  return route.path === routePath
}

const getNavLinkClass = (routePath) => {
  return isActiveRoute(routePath)
    ? 'text-white font-bold'
    : 'hover:text-gray-900'
}

const getNavBackgroundClass = (routePath) => {
  return isActiveRoute(routePath)
    ? 'bg-gradient-to-r from-blue-500 via-purple-500 to-blue-600 shadow-lg'
    : 'group-hover:bg-gradient-to-r group-hover:from-blue-50 group-hover:to-purple-50'
}

const getNavIconClass = (routePath) => {
  return isActiveRoute(routePath)
    ? 'text-white drop-shadow-sm'
    : 'text-gray-500 group-hover:text-blue-600'
}

// Mobile navigation styling
const getMobileNavClass = (routePath) => {
  return isActiveRoute(routePath)
    ? 'text-white bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg'
    : 'text-gray-600 hover:text-gray-900 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50'
}

const getMobileNavIconBg = (routePath) => {
  return isActiveRoute(routePath)
    ? 'bg-white/20'
    : 'bg-gray-100 group-hover:bg-white'
}

const getMobileNavIconColor = (routePath) => {
  return isActiveRoute(routePath)
    ? 'text-white'
    : 'text-gray-500 group-hover:text-blue-600'
}

// Show logout confirmation modal
const showLogoutModal = () => {
  showUserMenu.value = false
  showMobileMenu.value = false
  showLogoutConfirmation.value = true
}

// Logout method with proper auth store integration
const handleLogout = async () => {
  isLoggingOut.value = true
  try {
    // Sign out from auth store
    await authStore.signOutUser()

    // Show success toast message
    toast.success('Signed out successfully!')

    // Close the modal
    showLogoutConfirmation.value = false

    // Redirect to login page immediately
    router.push('/')
  } catch (error) {
    console.error('Logout failed:', error)
    toast.error('Failed to sign out. Please try again.')
  } finally {
    isLoggingOut.value = false
  }
}

// Toggle notification card and close user menu
const toggleNotificationCard = () => {
  showNotificationCard.value = !showNotificationCard.value
  if (showNotificationCard.value) {
    showUserMenu.value = false
  }
}

// Toggle user menu and close notification card
const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
  if (showUserMenu.value) {
    showNotificationCard.value = false
  }
}

// Fetch unread notification count
const fetchUnreadCount = async () => {
  if (!authStore.user?.uid) {
    unreadNotificationCount.value = 0
    return
  }

  try {
    const { count } = await notificationService.getUnreadNotifications(authStore.user.uid)
    unreadNotificationCount.value = count
  } catch (error) {
    console.error('Failed to fetch unread count:', error)
    // Don't update count on error to avoid flickering
  }
}

// Start auto-refresh for unread count
const startUnreadCountRefresh = () => {
  // Fetch immediately on start
  fetchUnreadCount()

  // Refresh every 15 minutes to sync with backend scheduler
  unreadCountInterval = setInterval(() => {
    fetchUnreadCount()
  }, 900000)
}

// Stop auto-refresh
const stopUnreadCountRefresh = () => {
  if (unreadCountInterval) {
    clearInterval(unreadCountInterval)
    unreadCountInterval = null
  }
}

// Handle unread count change from notification card
const handleUnreadCountChange = (count) => {
  unreadNotificationCount.value = count
}

// Close menus on escape key
const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    showUserMenu.value = false
    showNotificationCard.value = false
    showMobileMenu.value = false
  }
}

// Click outside to close menus
const handleClickOutside = (event) => {
  const target = event.target
  if (!target.closest('.relative')) {
    showUserMenu.value = false
    showNotificationCard.value = false
    showMobileMenu.value = false
  }
}

// Watch for notification update events
watch(onNotificationUpdate(), () => {
  // Refresh the notification count when an event is triggered
  fetchUnreadCount()
})

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('click', handleClickOutside)

  // Start auto-refresh for unread count if user is authenticated
  if (authStore.isAuthenticated) {
    startUnreadCountRefresh()
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('click', handleClickOutside)

  // Stop auto-refresh on component unmount
  stopUnreadCountRefresh()
})
</script>

<style scoped>
/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .animate-scale-in,
.modal-leave-to .animate-scale-in {
  transform: scale(0.9);
}

/* Enhanced hover effects */
.group:hover .w-10.h-10,
.group:hover .w-14.h-14 {
  transform: scale(1.05);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

/* Smooth transitions for all interactive elements */
* {
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Enhanced focus states for accessibility */
button:focus-visible,
a:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
  border-radius: 0.75rem;
}

/* Enhanced mobile responsiveness */
@media (max-width: 640px) {
  nav {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }
}

/* Enhanced scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #3b82f6, #8b5cf6);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to bottom, #2563eb, #7c3aed);
}

/* Button hover effects */
button:hover:not(:disabled) {
  transform: translateY(-1px);
}

button:active:not(:disabled) {
  transform: translateY(0);
}

/* Navigation glow effects */
.group:hover .blur-sm {
  filter: blur(4px);
}

/* Enhanced card effects */
.backdrop-blur-xl {
  backdrop-filter: blur(24px);
}

/* Status indicator animations */
@keyframes status-pulse {

  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

.animate-pulse {
  animation: status-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Enhanced navbar styling */
nav {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
}

/* Logo animation effects */
.bg-size-200 {
  background-size: 200% auto;
}

.hover\:bg-pos-100:hover {
  background-position: 100% center;
}

/* Enhanced navigation link effects */
.group:hover .absolute.inset-0 {
  backdrop-filter: blur(8px);
}
</style>
