<!-- frontend/src/views/ProfileView.vue -->
<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
    <NavigationBar />

    <!-- Header Section -->
    <div class="bg-white/70 backdrop-blur-sm border-b border-gray-200/50">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex items-center gap-4">
          <div
            class="w-16 h-16 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold shadow-lg">
            {{ userInitials }}
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ authStore.user?.displayName || 'Your Profile' }}</h1>
            <p class="text-sm text-gray-600 mt-1">Manage your account information and preferences</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-20">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
          <span class="text-gray-600">Loading profile...</span>
        </div>
      </div>

      <!-- Profile Content -->
      <div v-else class="space-y-6">
        <!-- Personal Information Card -->
        <div class="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
          <div class="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <User class="w-6 h-6 text-blue-600" />
                <h2 class="text-xl font-bold text-gray-900">Personal Information</h2>
              </div>
              <button v-if="!editingPersonal" @click="startEditingPersonal" class="btn btn-outline">
                <Edit3 class="w-4 h-4" />
                <span>Edit</span>
              </button>
            </div>
          </div>

          <div class="p-6">
            <!-- View Mode -->
            <div v-if="!editingPersonal" class="space-y-4">
              <div class="info-row">
                <span class="info-label">Display Name</span>
                <span class="info-value">{{ profileData.displayName || 'Not set' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Full Name</span>
                <span class="info-value">{{ profileData.name || 'Not set' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Email</span>
                <span class="info-value">{{ profileData.email }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Job Title</span>
                <span class="info-value">{{ profileData.title || 'Not set' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Department</span>
                <span class="info-value">{{ profileData.department || 'Not set' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Role</span>
                <span class="role-badge" :class="getRoleBadgeClass(profileData.role)">
                  {{ formatRole(profileData.role) }}
                </span>
              </div>
            </div>

            <!-- Edit Mode -->
            <form v-else @submit.prevent="savePersonalInfo" class="space-y-4">
              <div class="form-group">
                <label class="form-label">Display Name</label>
                <input v-model="editForm.displayName" type="text" class="form-input"
                  placeholder="How you want to be shown" maxlength="50" />
                <p class="form-hint">This name will be displayed throughout the application</p>
              </div>

              <div class="form-group">
                <label class="form-label">Full Name</label>
                <input v-model="editForm.name" type="text" class="form-input" placeholder="Your full name"
                  maxlength="100" />
              </div>

              <div class="form-group">
                <label class="form-label">Email</label>
                <input :value="profileData.email" type="email" class="form-input" disabled />
                <p class="form-hint">Email cannot be changed from this page</p>
              </div>

              <div class="form-group">
                <label class="form-label">Job Title</label>
                <input v-model="editForm.title" type="text" class="form-input" placeholder="e.g., Senior Developer"
                  maxlength="100" />
              </div>

              <div class="form-group">
                <label class="form-label">Department</label>
                <select v-model="editForm.department" class="form-input">
                  <option value="">Select a department...</option>
                  <option v-for="dept in DEPARTMENTS_LIST" :key="dept" :value="dept">
                    {{ dept }}
                  </option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">Role</label>
                <select v-model="editForm.role" class="form-input">
                  <option v-for="role in USER_ROLES_LIST" :key="role" :value="role">
                    {{ formatRole(role) }}
                  </option>
                </select>
              </div>

              <div class="flex gap-3 pt-4">
                <button type="submit" :disabled="savingPersonal" class="btn btn-primary flex-1">
                  <Loader2 v-if="savingPersonal" class="w-4 h-4 animate-spin" />
                  <Save v-else class="w-4 h-4" />
                  <span>{{ savingPersonal ? 'Saving...' : 'Save Changes' }}</span>
                </button>
                <button type="button" @click="cancelEditingPersonal" :disabled="savingPersonal"
                  class="btn btn-secondary">
                  <X class="w-4 h-4" />
                  <span>Cancel</span>
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- Account Details Card -->
        <div class="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
          <div class="p-6 border-b border-gray-200 bg-gradient-to-r from-green-50 to-blue-50">
            <div class="flex items-center gap-3">
              <Shield class="w-6 h-6 text-green-600" />
              <h2 class="text-xl font-bold text-gray-900">Account Details</h2>
            </div>
          </div>

          <div class="p-6 space-y-4">
            <div class="info-row">
              <span class="info-label">User ID</span>
              <span class="info-value font-mono text-sm">{{ profileData.uid }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Account Created</span>
              <span class="info-value">{{ formatDate(profileData.createdAt) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Last Login</span>
              <span class="info-value">{{ formatDate(profileData.lastLoginAt) }}</span>
            </div>
            <div v-if="profileData.updatedAt" class="info-row">
              <span class="info-label">Last Updated</span>
              <span class="info-value">{{ formatDate(profileData.updatedAt) }}</span>
            </div>
          </div>
        </div>

        <!-- Security Card -->
        <div class="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
          <div class="p-6 border-b border-gray-200 bg-gradient-to-r from-amber-50 to-orange-50">
            <div class="flex items-center gap-3">
              <Lock class="w-6 h-6 text-amber-600" />
              <h2 class="text-xl font-bold text-gray-900">Security</h2>
            </div>
          </div>

          <div class="p-6 space-y-4">
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div class="flex items-center gap-3">
                <Key class="w-5 h-5 text-gray-600" />
                <div>
                  <p class="font-semibold text-gray-900">Password</p>
                  <p class="text-sm text-gray-600">Change your password to keep your account secure</p>
                </div>
              </div>
              <button @click="openPasswordModal" class="btn btn-outline">
                <Key class="w-4 h-4" />
                <span>Change Password</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Account Actions Card -->
        <div class="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
          <div class="p-6 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-slate-50">
            <div class="flex items-center gap-3">
              <LogOut class="w-6 h-6 text-gray-600" />
              <h2 class="text-xl font-bold text-gray-900">Account Actions</h2>
            </div>
          </div>

          <div class="p-6">
            <div class="flex items-start justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div class="flex items-start gap-3 flex-1">
                <LogOut class="w-5 h-5 text-gray-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p class="font-semibold text-gray-900">Sign Out</p>
                  <p class="text-sm text-gray-600">Sign out of your account on this device</p>
                </div>
              </div>
              <button @click="handleSignOut" class="btn btn-secondary">
                <LogOut class="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Change Password Modal -->
    <teleport to="body">
      <transition name="modal">
        <div v-if="showPasswordModal" class="modal-overlay" @click="closePasswordModal">
          <div class="modal-container" @click.stop>
            <div class="modal-header">
              <div class="flex items-center gap-3">
                <Key class="w-6 h-6 text-blue-600" />
                <h3 class="modal-title">Change Password</h3>
              </div>
              <button @click="closePasswordModal" class="modal-close-btn">
                <X class="w-5 h-5" />
              </button>
            </div>

            <form @submit.prevent="changePassword" class="modal-body">
              <div class="space-y-4">
                <div class="form-group">
                  <label class="form-label required">Current Password</label>
                  <div class="relative">
                    <input v-model="passwordForm.currentPassword" :type="showCurrentPassword ? 'text' : 'password'"
                      required class="form-input w-full pr-10" placeholder="Enter your current password" />
                    <button type="button" @click="showCurrentPassword = !showCurrentPassword"
                      class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600">
                      <EyeOff v-if="showCurrentPassword" class="w-5 h-5" />
                      <Eye v-else class="w-5 h-5" />
                    </button>
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label required">New Password</label>
                  <div class="relative">
                    <input v-model="passwordForm.newPassword" :type="showNewPassword ? 'text' : 'password'" required
                      class="form-input w-full pr-10" placeholder="Enter new password" minlength="8" />
                    <button type="button" @click="showNewPassword = !showNewPassword"
                      class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600">
                      <EyeOff v-if="showNewPassword" class="w-5 h-5" />
                      <Eye v-else class="w-5 h-5" />
                    </button>
                  </div>

                  <!-- Password length error -->
                  <div v-if="passwordForm.newPassword && passwordForm.newPassword.length < 8"
                    class="mt-2 flex items-center text-red-600">
                    <AlertCircle class="w-4 h-4 mr-1" />
                    <span class="text-xs font-medium">Password must be at least 8 characters long</span>
                  </div>

                  <!-- Password strength indicator -->
                  <div v-if="passwordForm.newPassword && passwordForm.newPassword.length >= 8" class="mt-3">
                    <div class="flex gap-1">
                      <div v-for="i in 4" :key="i" :class="[
                        'h-2 flex-1 rounded-full transition-all duration-300',
                        newPasswordStrength >= i ? getStrengthColor(newPasswordStrength) : 'bg-gray-200'
                      ]"></div>
                    </div>
                    <p class="mt-2 text-xs font-medium" :class="getStrengthTextColor(newPasswordStrength)">
                      {{ getStrengthText(newPasswordStrength) }}
                    </p>
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label required">Confirm New Password</label>
                  <div class="relative">
                    <input v-model="passwordForm.confirmPassword" :type="showConfirmNewPassword ? 'text' : 'password'"
                      required class="form-input w-full pr-10" placeholder="Confirm new password" />
                    <button type="button" @click="showConfirmNewPassword = !showConfirmNewPassword"
                      class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600">
                      <EyeOff v-if="showConfirmNewPassword" class="w-5 h-5" />
                      <Eye v-else class="w-5 h-5" />
                    </button>
                  </div>

                  <!-- Password match indicator -->
                  <div v-if="passwordForm.confirmPassword && passwordForm.confirmPassword !== passwordForm.newPassword"
                    class="mt-2 flex items-center text-red-600">
                    <X class="w-4 h-4 mr-1" />
                    <span class="text-xs font-medium">Passwords do not match</span>
                  </div>
                  <div
                    v-if="passwordForm.confirmPassword && passwordForm.confirmPassword === passwordForm.newPassword && passwordForm.newPassword"
                    class="mt-2 flex items-center text-green-600">
                    <Check class="w-4 h-4 mr-1" />
                    <span class="text-xs font-medium">Passwords match</span>
                  </div>
                </div>
              </div>

              <div class="modal-actions">
                <button type="button" @click="closePasswordModal" :disabled="changingPassword"
                  class="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" :disabled="changingPassword || !isPasswordFormValid" class="btn btn-primary">
                  <Loader2 v-if="changingPassword" class="w-4 h-4 animate-spin" />
                  <Key v-else class="w-4 h-4" />
                  <span>{{ changingPassword ? 'Changing...' : 'Change Password' }}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </transition>
    </teleport>

    <!-- Confirmation Modals -->
    <ConfirmationModal :show="showSignOutModal" title="Sign Out" description="Are you sure you want to sign out?"
      confirm-text="Sign Out" cancel-text="Cancel" variant="danger" icon="logout" @confirm="confirmSignOut"
      @cancel="showSignOutModal = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usersService } from '@/services/users'
import { DEPARTMENTS, USER_ROLES } from '@/models/user'
import { useToast } from 'vue-toastification'
import NavigationBar from '@/components/NavigationBar.vue'
import ConfirmationModal from '@/components/ConfirmationModal.vue'
import {
  User,
  Edit3,
  Save,
  X,
  Shield,
  Lock,
  Key,
  LogOut,
  Loader2,
  Eye,
  EyeOff,
  AlertCircle,
  Check
} from 'lucide-vue-next'
import { updatePassword, reauthenticateWithCredential, EmailAuthProvider } from 'firebase/auth'
import { auth } from '@/firebase/firebaseConfig'

// Composables
const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

// Constants
const DEPARTMENTS_LIST = Object.values(DEPARTMENTS)
const USER_ROLES_LIST = Object.values(USER_ROLES)

// Reactive state
const loading = ref(true)
const editingPersonal = ref(false)
const savingPersonal = ref(false)
const showPasswordModal = ref(false)
const changingPassword = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmNewPassword = ref(false)
const showSignOutModal = ref(false)

const profileData = ref({
  uid: '',
  email: '',
  name: '',
  displayName: '',
  title: '',
  department: '',
  role: '',
  photoURL: '',
  createdAt: 0,
  lastLoginAt: 0,
  updatedAt: 0
})

const editForm = ref({
  displayName: '',
  name: '',
  title: '',
  department: '',
  role: ''
})

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// Computed properties
const userInitials = computed(() => {
  const name = profileData.value.displayName || profileData.value.name || profileData.value.email
  if (!name) return '?'

  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
})

const isPasswordFormValid = computed(() => {
  return passwordForm.value.currentPassword &&
    passwordForm.value.newPassword &&
    passwordForm.value.confirmPassword &&
    passwordForm.value.newPassword === passwordForm.value.confirmPassword &&
    passwordForm.value.newPassword.length >= 8
})

// Password strength calculation
const newPasswordStrength = computed(() => {
  const pwd = passwordForm.value.newPassword
  if (!pwd) return 0

  // If password is less than 8 characters, it's always weak (strength 1)
  if (pwd.length < 8) return 1

  let strength = 0
  if (pwd.length >= 8) strength++
  if (/[A-Z]/.test(pwd)) strength++
  if (/[a-z]/.test(pwd)) strength++
  if (/\d/.test(pwd)) strength++
  if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) strength++

  return Math.min(strength, 4)
})

// Methods
function getStrengthColor(strength) {
  if (strength <= 1) return 'bg-red-400'
  if (strength <= 2) return 'bg-yellow-400'
  if (strength <= 3) return 'bg-blue-400'
  return 'bg-green-400'
}

function getStrengthTextColor(strength) {
  if (strength <= 1) return 'text-red-600'
  if (strength <= 2) return 'text-yellow-600'
  if (strength <= 3) return 'text-blue-600'
  return 'text-green-600'
}

function getStrengthText(strength) {
  if (strength <= 1) return 'Weak password'
  if (strength <= 2) return 'Fair password'
  if (strength <= 3) return 'Good password'
  return 'Strong password'
}

function formatRole(role) {
  if (!role) return 'Unknown'
  return role.charAt(0).toUpperCase() + role.slice(1)
}

function getRoleBadgeClass(role) {
  const classes = {
    'director': 'role-badge-director',
    'manager': 'role-badge-manager',
    'staff': 'role-badge-staff'
  }
  return classes[role?.toLowerCase()] || 'role-badge-default'
}

function formatDate(timestamp) {
  if (!timestamp) return 'Unknown'
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function loadProfile() {
  loading.value = true
  try {
    const currentUser = authStore.user
    if (!currentUser) {
      toast.error('No user logged in')
      router.push('/authentication')
      return
    }

    profileData.value = {
      uid: currentUser.uid,
      email: currentUser.email,
      name: currentUser.name || '',
      displayName: currentUser.displayName || '',
      title: currentUser.title || '',
      department: currentUser.department || '',
      role: currentUser.role || '',
      photoURL: currentUser.photoURL || '',
      createdAt: currentUser.createdAt || 0,
      lastLoginAt: currentUser.lastLoginAt || 0,
      updatedAt: currentUser.updatedAt || 0
    }
  } catch (error) {
    console.error('Error loading profile:', error)
    toast.error('Failed to load profile')
  } finally {
    loading.value = false
  }
}

function startEditingPersonal() {
  editForm.value = {
    displayName: profileData.value.displayName,
    name: profileData.value.name,
    title: profileData.value.title,
    department: profileData.value.department,
    role: profileData.value.role
  }
  editingPersonal.value = true
}

function cancelEditingPersonal() {
  editingPersonal.value = false
  editForm.value = {
    displayName: '',
    name: '',
    title: '',
    department: '',
    role: ''
  }
}

async function savePersonalInfo() {
  savingPersonal.value = true
  try {
    const updates = {
      displayName: editForm.value.displayName.trim(),
      name: editForm.value.name.trim(),
      title: editForm.value.title.trim(),
      department: editForm.value.department.trim(),
      role: editForm.value.role
    }

    await usersService.updateUserFields(profileData.value.uid, updates)

    // Update local state
    profileData.value = {
      ...profileData.value,
      ...updates,
      updatedAt: Date.now()
    }

    // Update auth store
    authStore.user = {
      ...authStore.user,
      ...updates
    }

    toast.success('Profile updated successfully')
    editingPersonal.value = false
  } catch (error) {
    console.error('Error updating profile:', error)
    toast.error('Failed to update profile')
  } finally {
    savingPersonal.value = false
  }
}

function openPasswordModal() {
  passwordForm.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  showCurrentPassword.value = false
  showNewPassword.value = false
  showConfirmNewPassword.value = false
  showPasswordModal.value = true
}

function closePasswordModal() {
  showPasswordModal.value = false
  showCurrentPassword.value = false
  showNewPassword.value = false
  showConfirmNewPassword.value = false
  passwordForm.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}

async function changePassword() {
  if (!isPasswordFormValid.value) {
    toast.error('Please check your password entries')
    return
  }

  changingPassword.value = true
  try {
    const user = auth.currentUser
    if (!user || !user.email) {
      throw new Error('No authenticated user found')
    }

    // Re-authenticate user
    const credential = EmailAuthProvider.credential(
      user.email,
      passwordForm.value.currentPassword
    )
    await reauthenticateWithCredential(user, credential)

    // Update password
    await updatePassword(user, passwordForm.value.newPassword)

    toast.success('Password changed successfully')
    closePasswordModal()
  } catch (error) {
    console.error('Error changing password:', error)

    if (error.code === 'auth/wrong-password') {
      toast.error('Current password is incorrect')
    } else if (error.code === 'auth/weak-password') {
      toast.error('New password is too weak')
    } else {
      toast.error('Failed to change password')
    }
  } finally {
    changingPassword.value = false
  }
}

function handleSignOut() {
  showSignOutModal.value = true
}

async function confirmSignOut() {
  try {
    await authStore.signOutUser()
    toast.success('Signed out successfully')
    router.push('/authentication')
  } catch (error) {
    console.error('Error signing out:', error)
    toast.error('Failed to sign out')
  }
}

// Lifecycle
onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
  border: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-outline {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-outline:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #9ca3af;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

/* Info Rows */
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-weight: 500;
  color: #6b7280;
  font-size: 0.875rem;
}

.info-value {
  color: #111827;
  font-weight: 500;
}

/* Role Badges */
.role-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.role-badge-director {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: #78350f;
}

.role-badge-manager {
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  color: #1e3a8a;
}

.role-badge-staff {
  background: linear-gradient(135deg, #34d399, #10b981);
  color: #064e3b;
}

.role-badge-default {
  background: #e5e7eb;
  color: #374151;
}

/* Form Elements */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.form-label.required::after {
  content: ' *';
  color: #ef4444;
}

.form-input {
  padding: 0.75rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  transition: all 0.2s ease;
}

/* Add padding for inputs with icons inside */
.form-input.pr-10 {
  padding-right: 2.5rem;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input:disabled {
  background: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
}

.form-hint {
  font-size: 0.75rem;
  color: #6b7280;
}

/* Password visibility toggle button */
.form-group button[type="button"] {
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s ease;
}

/* Strength indicator spacing */
.gap-1>*+* {
  margin-left: 0.25rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 1rem;
  max-width: 28rem;
  width: 100%;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.modal-close-btn {
  padding: 0.5rem;
  color: #9ca3af;
  border-radius: 0.5rem;
  transition: all 0.15s ease;
  background: none;
  border: none;
  cursor: pointer;
}

.modal-close-btn:hover {
  color: #4b5563;
  background: #f3f4f6;
}

.modal-body {
  padding: 1.5rem;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #f3f4f6;
}

.modal-actions .btn {
  flex: 1;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95) translateY(20px);
}

/* Responsive */
@media (max-width: 640px) {
  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
