<!-- src/views/AuthenticationView.vue -->

<template>
  <div
    class="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <!-- Header -->
      <div class="text-center">
        <div
          class="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 mb-6 shadow-lg">
          <Building class="h-8 w-8 text-blue-600" />
        </div>
        <h2 class="text-3xl font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
          G7T1 Management
        </h2>
        <p class="mt-2 text-sm text-gray-600">
          Company Management System
        </p>
      </div>

      <!-- Auth Card -->
      <div class="bg-white rounded-2xl shadow-xl border border-blue-100 p-8 space-y-6">
        <!-- Mode Toggle -->
        <div class="flex bg-blue-50 rounded-xl p-1.5 border border-blue-100">
          <button @click="setMode('signin')" :class="[
            'flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 transform',
            mode === 'signin'
              ? 'bg-white text-blue-600 shadow-md scale-105 border border-blue-200'
              : 'text-blue-500 hover:text-blue-600 hover:bg-blue-100'
          ]">
            Sign In
          </button>
          <button @click="setMode('signup')" :class="[
            'flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 transform',
            mode === 'signup'
              ? 'bg-white text-blue-600 shadow-md scale-105 border border-blue-200'
              : 'text-blue-500 hover:text-blue-600 hover:bg-blue-100'
          ]">
            Register
          </button>
        </div>

        <!-- Error Alert -->
        <transition name="slide-down">
          <div v-if="authStore.error" class="bg-red-50 border-2 border-red-200 rounded-xl p-4 shadow-sm">
            <div class="flex items-center">
              <AlertCircle class="h-5 w-5 text-red-500 mr-3" />
              <span class="text-red-800 text-sm font-medium">{{ displayError }}</span>
            </div>
          </div>
        </transition>

        <!-- Success Alert -->
        <transition name="slide-down">
          <div v-if="authStore.success" class="bg-green-50 border-2 border-green-200 rounded-xl p-4 shadow-sm">
            <div class="flex items-center">
              <Check class="h-5 w-5 text-green-500 mr-3" />
              <span class="text-green-800 text-sm font-medium">{{ authStore.success }}</span>
            </div>
          </div>
        </transition>

        <!-- Sign In Form -->
        <form v-if="mode === 'signin'" @submit.prevent="handleSignIn" class="space-y-5">
          <div>
            <label for="signin-email" class="block text-sm font-semibold text-gray-700 mb-2">
              Email Address
            </label>
            <div class="relative">
              <Mail class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-blue-400" />
              <input id="signin-email" v-model="email" type="email" autocomplete="email" required
                :disabled="authStore.loading"
                class="w-full pl-10 pr-4 py-3 border-2 border-blue-200 rounded-xl shadow-sm placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-blue-50 disabled:cursor-not-allowed transition-all duration-200"
                placeholder="Enter your company email" />
            </div>
          </div>

          <div>
            <label for="signin-password" class="block text-sm font-semibold text-gray-700 mb-2">
              Password
            </label>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-blue-400" />
              <input id="signin-password" v-model="password" :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password" required :disabled="authStore.loading"
                class="w-full pl-10 pr-12 py-3 border-2 border-blue-200 rounded-xl shadow-sm placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-blue-50 disabled:cursor-not-allowed transition-all duration-200"
                placeholder="Enter your password" />
              <button type="button" @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-blue-400 hover:text-blue-600 transition-colors">
                <EyeOff v-if="showPassword" class="h-5 w-5" />
                <Eye v-else class="h-5 w-5" />
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <input id="remember-me" v-model="rememberMe" type="checkbox"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-blue-300 rounded" />
              <label for="remember-me" class="ml-2 block text-sm text-gray-700 font-medium">
                Remember me
              </label>
            </div>
            <button type="button" @click="openForgotPasswordModal"
              class="text-sm text-blue-600 hover:text-blue-500 font-semibold hover:underline transition-colors">
              Forgot password?
            </button>
          </div>

          <button type="submit" :disabled="authStore.loading || !isSignInFormValid"
            class="w-full flex justify-center items-center py-3.5 px-4 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105">
            <Loader2 v-if="authStore.loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" />
            {{ authStore.loading ? 'Signing in...' : 'Sign In' }}
          </button>
        </form>

        <!-- Sign Up Form -->
        <form v-if="mode === 'signup'" @submit.prevent="handleSignUp" class="space-y-5">
          <!-- User Information Fields -->
          <div class="grid grid-cols-1 gap-5">
            <div>
              <label for="signup-name" class="block text-sm font-semibold text-gray-700 mb-2">
                Full Name
              </label>
              <div class="relative">
                <User class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-blue-400" />
                <input id="signup-name" v-model="name" type="text" autocomplete="name" required
                  :disabled="authStore.loading"
                  class="w-full pl-10 pr-4 py-3 border-2 border-blue-200 rounded-xl shadow-sm placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-blue-50 disabled:cursor-not-allowed transition-all duration-200"
                  placeholder="Enter your full name" />
              </div>
            </div>

            <div>
              <label for="signup-email" class="block text-sm font-semibold text-gray-700 mb-2">
                Email Address
              </label>
              <div class="relative">
                <Mail class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-blue-400" />
                <input id="signup-email" v-model="email" type="email" autocomplete="email" required
                  :disabled="authStore.loading"
                  class="w-full pl-10 pr-4 py-3 border-2 border-blue-200 rounded-xl shadow-sm placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-blue-50 disabled:cursor-not-allowed transition-all duration-200"
                  placeholder="Enter your company email" />
              </div>
            </div>

            <div>
              <label for="signup-department" class="block text-sm font-semibold text-gray-700 mb-2">
                Department
              </label>
              <div class="relative">
                <Building2 class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-blue-400" />
                <select id="signup-department" v-model="department" required :disabled="authStore.loading"
                  class="w-full pl-10 pr-4 py-3 border-2 border-blue-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-blue-50 disabled:cursor-not-allowed transition-all duration-200">
                  <option value="">Select your department</option>
                  <option v-for="dept in Object.values(departmentOptions)" :key="dept" :value="dept">{{ dept }}</option>
                </select>
              </div>
            </div>

            <div>
              <label for="signup-role" class="block text-sm font-semibold text-gray-700 mb-2">
                Role Level
              </label>
              <div class="relative">
                <Crown class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-blue-400" />
                <select id="signup-role" v-model="role" required :disabled="authStore.loading"
                  class="w-full pl-10 pr-4 py-3 border-2 border-blue-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-blue-50 disabled:cursor-not-allowed transition-all duration-200">
                  <option value="">Select your role level</option>
                  <option value="staff">Staff</option>
                  <option value="manager">Manager</option>
                  <option value="director">Director</option>
                </select>
              </div>
            </div>
          </div>

          <div>
            <label for="signup-password" class="block text-sm font-semibold text-gray-700 mb-2">
              Password
            </label>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-blue-400" />
              <input id="signup-password" v-model="password" :type="showPassword ? 'text' : 'password'"
                autocomplete="new-password" required :disabled="authStore.loading"
                class="w-full pl-10 pr-12 py-3 border-2 border-blue-200 rounded-xl shadow-sm placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-blue-50 disabled:cursor-not-allowed transition-all duration-200"
                placeholder="Create a strong password" />
              <button type="button" @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-blue-400 hover:text-blue-600 transition-colors">
                <EyeOff v-if="showPassword" class="h-5 w-5" />
                <Eye v-else class="h-5 w-5" />
              </button>
            </div>
            <!-- Password length error -->
            <div v-if="password && password.length <= 7" class="mt-2 flex items-center text-red-600">
              <AlertCircle class="h-4 w-4 mr-1" />
              <span class="text-xs font-medium">Password must be at least 8 characters long</span>
            </div>
            <!-- Password strength indicator -->
            <div v-if="password" class="mt-3">
              <div class="flex space-x-1">
                <div v-for="i in 4" :key="i" :class="[
                  'h-2 flex-1 rounded-full transition-all duration-300',
                  passwordStrength >= i ? getStrengthColor(passwordStrength) : 'bg-blue-100'
                ]">
                </div>
              </div>
              <p class="mt-2 text-xs font-medium" :class="getStrengthTextColor(passwordStrength)">
                {{ getStrengthText(passwordStrength) }}
              </p>
            </div>
          </div>

          <div>
            <label for="confirm-password" class="block text-sm font-semibold text-gray-700 mb-2">
              Confirm Password
            </label>
            <div class="relative">
              <Shield class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-blue-400" />
              <input id="confirm-password" v-model="confirmPassword" :type="showConfirmPassword ? 'text' : 'password'"
                autocomplete="new-password" required :disabled="authStore.loading"
                class="w-full pl-10 pr-12 py-3 border-2 border-blue-200 rounded-xl shadow-sm placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-blue-50 disabled:cursor-not-allowed transition-all duration-200"
                placeholder="Confirm your password" />
              <button type="button" @click="showConfirmPassword = !showConfirmPassword"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-blue-400 hover:text-blue-600 transition-colors">
                <EyeOff v-if="showConfirmPassword" class="h-5 w-5" />
                <Eye v-else class="h-5 w-5" />
              </button>
            </div>
            <!-- Password match indicator -->
            <div v-if="confirmPassword && confirmPassword !== password" class="mt-2 flex items-center text-red-600">
              <X class="h-4 w-4 mr-1" />
              <span class="text-xs font-medium">Passwords do not match</span>
            </div>
            <div v-if="confirmPassword && confirmPassword === password && password"
              class="mt-2 flex items-center text-green-600">
              <Check class="h-4 w-4 mr-1" />
              <span class="text-xs font-medium">Passwords match</span>
            </div>
          </div>

          <button type="submit" :disabled="authStore.loading || !isSignUpFormValid"
            class="w-full flex justify-center items-center py-3.5 px-4 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105">
            <Loader2 v-if="authStore.loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" />
            {{ authStore.loading ? 'Creating Account...' : 'Create Account' }}
          </button>
        </form>
      </div>
    </div>

    <!-- Footer -->
    <footer class="mt-12 text-center text-gray-500 text-sm">
      <div class="max-w-md mx-auto space-y-2">
        <p>© {{ currentYear }} G7T1 Management System. All rights reserved.</p>
        <div class="flex justify-center space-x-4 text-xs">
          <a href="mailto:support@g7t1.com" class="hover:text-blue-600 transition-colors">
            Support
          </a>
        </div>
      </div>
    </footer>

    <!-- Forgot Password Modal -->
    <div v-if="showForgotPassword"
      class="fixed inset-0 bg-black/70 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
      <div class="relative bg-white rounded-2xl shadow-2xl max-w-md w-full">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-xl font-bold text-gray-900">Reset Password</h3>
            <button @click="closeForgotPasswordModal"
              class="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100">
              <X class="h-6 w-6" />
            </button>
          </div>

          <div class="space-y-4">
            <p class="text-sm text-gray-600">
              Enter your email address and we'll send you a link to reset your password.
            </p>

            <!-- Success message for forgot password -->
            <div v-if="forgotPasswordSuccess" class="bg-green-50 border-2 border-green-200 rounded-xl p-4">
              <div class="flex items-start">
                <Check class="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                <div class="text-green-800 text-sm">
                  <p class="font-medium mb-1">Email Sent!</p>
                  <p>We've sent a password reset link to <strong>{{ forgotPasswordEmail }}</strong>. Please check your
                    inbox and spam folder.</p>
                </div>
              </div>
            </div>

            <!-- Error message for forgot password -->
            <div v-if="forgotPasswordError" class="bg-red-50 border-2 border-red-200 rounded-xl p-4">
              <div class="flex items-center">
                <AlertCircle class="h-5 w-5 text-red-500 mr-3" />
                <span class="text-red-800 text-sm font-medium">{{ forgotPasswordError }}</span>
              </div>
            </div>

            <form v-if="!forgotPasswordSuccess" @submit.prevent="handleForgotPassword" class="space-y-4">
              <div>
                <label for="forgot-email" class="block text-sm font-semibold text-gray-700 mb-2">
                  Email Address
                </label>
                <div class="relative">
                  <Mail class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-blue-400" />
                  <input id="forgot-email" v-model="forgotPasswordEmail" type="email" autocomplete="email" required
                    :disabled="forgotPasswordLoading"
                    class="w-full pl-10 pr-4 py-3 border-2 border-blue-200 rounded-xl shadow-sm placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-blue-50 disabled:cursor-not-allowed transition-all duration-200"
                    placeholder="Enter your email address" />
                </div>
              </div>

              <div class="flex space-x-3 pt-2">
                <button type="button" @click="closeForgotPasswordModal" :disabled="forgotPasswordLoading"
                  class="flex-1 px-4 py-2 text-gray-600 hover:text-gray-800 font-medium transition-colors disabled:opacity-50">
                  Cancel
                </button>
                <button type="submit" :disabled="forgotPasswordLoading || !forgotPasswordEmail"
                  class="flex-1 flex justify-center items-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200">
                  <Loader2 v-if="forgotPasswordLoading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" />
                  {{ forgotPasswordLoading ? 'Sending...' : 'Send Reset Link' }}
                </button>
              </div>
            </form>

            <div v-if="forgotPasswordSuccess" class="pt-2">
              <button @click="closeForgotPasswordModal"
                class="w-full py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.js'
import { usersService } from '@/services/users.js'
import { DEPARTMENTS } from '@/models/user.js'
import {
  Building,
  Building2,
  Briefcase,
  Crown,
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  AlertCircle,
  Shield,
  Check,
  X
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

// Form state
const mode = ref('signin')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const name = ref('')
const department = ref('')
const role = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const showForgotPassword = ref(false)

// Forgot password state
const forgotPasswordEmail = ref('')
const forgotPasswordLoading = ref(false)
const forgotPasswordSuccess = ref(false)
const forgotPasswordError = ref('')

// Current year for footer
const currentYear = new Date().getFullYear()

// Make DEPARTMENTS available in template
const departmentOptions = DEPARTMENTS

// Generic error message for security
const displayError = computed(() => {
  if (mode.value === 'signin' && authStore.error) {
    // For signin, show generic error for security
    if (authStore.error.includes('user-not-found') ||
      authStore.error.includes('wrong-password') ||
      authStore.error.includes('invalid-credential')) {
      return 'Invalid username or password'
    }
  }
  return authStore.error
})

// Password strength calculation
const passwordStrength = computed(() => {
  const pwd = password.value
  if (!pwd) return 0

  let strength = 0
  if (pwd.length >= 8) strength++
  if (/[A-Z]/.test(pwd)) strength++
  if (/[a-z]/.test(pwd)) strength++
  if (/\d/.test(pwd)) strength++
  if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) strength++

  return Math.min(strength, 4)
})

// Form validation
const isSignInFormValid = computed(() => {
  return email.value && password.value && !authStore.loading
})

const isSignUpFormValid = computed(() => {
  return email.value &&
    password.value &&
    confirmPassword.value &&
    name.value &&
    department.value &&
    role.value &&
    password.value === confirmPassword.value &&
    passwordStrength.value >= 2 &&
    !authStore.loading
})

// Clear errors when switching modes
watch(mode, () => {
  authStore.clearMessages()
  clearForgotPasswordState()
})

// Clear forgot password messages when closing modal
watch(showForgotPassword, (newValue) => {
  if (!newValue) {
    setTimeout(() => {
      clearForgotPasswordState()
    }, 300) // Wait for modal close animation
  }
})

// Methods
const setMode = (newMode) => {
  mode.value = newMode
  // Clear form when switching modes
  email.value = ''
  password.value = ''
  confirmPassword.value = ''
  name.value = ''
  department.value = ''
  role.value = ''
  showPassword.value = false
  showConfirmPassword.value = false
  authStore.clearMessages()
}

const getStrengthColor = (strength) => {
  if (strength <= 1) return 'bg-red-400'
  if (strength <= 2) return 'bg-yellow-400'
  if (strength <= 3) return 'bg-blue-400'
  return 'bg-green-400'
}

const getStrengthTextColor = (strength) => {
  if (strength <= 1) return 'text-red-600'
  if (strength <= 2) return 'text-yellow-600'
  if (strength <= 3) return 'text-blue-600'
  return 'text-green-600'
}

const getStrengthText = (strength) => {
  if (strength <= 1) return 'Weak password'
  if (strength <= 2) return 'Fair password'
  if (strength <= 3) return 'Good password'
  return 'Strong password'
}

const clearForgotPasswordState = () => {
  forgotPasswordEmail.value = ''
  forgotPasswordLoading.value = false
  forgotPasswordSuccess.value = false
  forgotPasswordError.value = ''
}

const openForgotPasswordModal = () => {
  // Pre-fill email if user has entered it in sign-in form
  if (email.value) {
    forgotPasswordEmail.value = email.value
  }
  showForgotPassword.value = true
  authStore.clearMessages()
}

const closeForgotPasswordModal = () => {
  showForgotPassword.value = false
  authStore.clearMessages()
}

const handleForgotPassword = async () => {
  if (!forgotPasswordEmail.value) return

  try {
    forgotPasswordError.value = ''
    forgotPasswordLoading.value = true

    await authStore.sendPasswordReset(forgotPasswordEmail.value)
    forgotPasswordSuccess.value = true
  } catch (error) {
    console.log(error)
    forgotPasswordError.value = authStore.error || 'Failed to send password reset email'
  } finally {
    forgotPasswordLoading.value = false
  }
}

const handleSignIn = async () => {
  if (!isSignInFormValid.value) return

  try {
    await authStore.signInWithEmail(email.value, password.value)
    // Redirect to dashboard after short delay
    setTimeout(() => {
      router.push('/dashboard')
    }, 1500)
  } catch (error) {
    console.log(error)
    // Error is handled by the store and displayed generically for security
  }
}

const handleSignUp = async () => {
  if (!isSignUpFormValid.value) return

  try {
    // Create Firebase auth user
    const userCredential = await authStore.signUpWithEmail(email.value, password.value)

    // Use the Firebase user directly from the credential instead of authStore.user
    // This avoids timing issues with onAuthStateChanged
    const firebaseUser = userCredential?.user || authStore.user

    if (firebaseUser) {
      // Create user profile in database
      const userData = {
        uid: firebaseUser.uid,
        email: firebaseUser.email,
        name: name.value,
        department: department.value,
        role: role.value,
        displayName: name.value,
        photoURL: firebaseUser.photoURL || '',
        createdAt: Date.now(),
        lastLoginAt: Date.now()
      }

      // Save user profile to database
      await usersService.createUser(userData)

      // Redirect to dashboard with success indication
      console.log('Redirecting to dashboard with newUser=true')
      router.push({ path: '/dashboard', query: { newUser: 'true' } })
    }
  } catch (error) {
    console.error('Registration error:', error)
    // Error is handled by the store
  }
}
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

/* Custom gradient text support */
.bg-clip-text {
  -webkit-background-clip: text;
  background-clip: text;
}
</style>
