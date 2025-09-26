<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">

    <!-- Main Content -->
    <main class="relative">
      <!-- Dev Notes Section -->
      <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        <!-- Auth Buttons -->
        <div class="flex items-center space-x-4 mb-4">
          <router-link to="/auth"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-semibold rounded-xl text-blue-600 bg-blue-50 hover:bg-blue-100 hover:text-blue-700 transition-all duration-200 transform hover:scale-105">
            <User class="w-4 h-4 mr-2" />
            Sign In / Register
          </router-link>
        </div>
      </section>

      <!-- Hero Section -->
      <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div class="text-center">
          <div
            class="mx-auto h-20 w-20 flex items-center justify-center rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 mb-8 shadow-2xl">
            <Building class="h-10 w-10 text-blue-600" />
          </div>

          <h1 class="text-5xl md:text-6xl font-extrabold mb-6">
            <span class="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
              Smart Task Management System
            </span>
          </h1>

          <p class="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
            Streamline your company operations with our comprehensive management system.
            Handle projects, track tasks, and collaborate seamlessly with your team.
          </p>

          <!-- CTA Buttons -->
          <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <router-link to="/auth"
              class="inline-flex items-center px-8 py-4 border border-transparent text-lg font-semibold rounded-2xl text-white bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 shadow-2xl hover:shadow-blue-500/25 transition-all duration-300 transform hover:scale-105">
              <Rocket class="w-5 h-5 mr-3" />
              Get Started
            </router-link>

            <a href="#features"
              class="inline-flex items-center px-8 py-4 border-2 border-blue-200 text-lg font-semibold rounded-2xl text-blue-600 bg-white hover:bg-blue-50 hover:border-blue-300 shadow-lg transition-all duration-300 transform hover:scale-105">
              <Eye class="w-5 h-5 mr-3" />
              Learn More
            </a>
          </div>
        </div>
      </section>

      <!-- Features Section -->
      <section id="features" class="bg-white py-20">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="text-center mb-16">
            <h2 class="text-4xl font-bold text-gray-900 mb-4">
              Why Choose Smart Task Management System?
            </h2>
            <p class="text-xl text-gray-600 max-w-3xl mx-auto">
              Built for modern teams who value efficiency, collaboration, and results.
            </p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <!-- Feature 1 -->
            <div
              class="text-center p-8 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 hover:shadow-xl transition-shadow duration-300">
              <div
                class="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <FolderOpen class="w-8 h-8 text-white" />
              </div>
              <h3 class="text-xl font-bold text-gray-900 mb-4">Project Management</h3>
              <p class="text-gray-600">
                Organize and track your projects with intuitive dashboards and comprehensive tools.
              </p>
            </div>

            <!-- Feature 2 -->
            <div
              class="text-center p-8 rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50 hover:shadow-xl transition-shadow duration-300">
              <div
                class="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <ListChecks class="w-8 h-8 text-white" />
              </div>
              <h3 class="text-xl font-bold text-gray-900 mb-4">Task Tracking</h3>
              <p class="text-gray-600">
                Keep your team on track with detailed task management and progress monitoring.
              </p>
            </div>

            <!-- Feature 3 -->
            <div
              class="text-center p-8 rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 hover:shadow-xl transition-shadow duration-300">
              <div
                class="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Users class="w-8 h-8 text-white" />
              </div>
              <h3 class="text-xl font-bold text-gray-900 mb-4">Team Collaboration</h3>
              <p class="text-gray-600">
                Foster seamless collaboration with role-based access and communication tools.
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- About Section -->
      <section id="about" class="py-20 bg-gradient-to-br from-gray-50 to-blue-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 class="text-4xl font-bold text-gray-900 mb-6">
                Built for Modern Companies
              </h2>
              <p class="text-lg text-gray-600 mb-6">
                Smart Task Management System is designed to streamline your company's workflow
                and enhance productivity. With secure authentication, comprehensive project
                tracking, and intuitive user interfaces, we make company management simple.
              </p>
              <div class="space-y-4">
                <div class="flex items-center space-x-3">
                  <Shield class="w-6 h-6 text-green-500" />
                  <span class="text-gray-700">Secure Firebase Authentication</span>
                </div>
                <div class="flex items-center space-x-3">
                  <Zap class="w-6 h-6 text-yellow-500" />
                  <span class="text-gray-700">Real-time Data Synchronization</span>
                </div>
                <div class="flex items-center space-x-3">
                  <Target class="w-6 h-6 text-blue-500" />
                  <span class="text-gray-700">Role-based Access Control</span>
                </div>
              </div>
            </div>

            <div class="relative">
              <div class="bg-white rounded-2xl shadow-2xl p-8 border border-gray-100">
                <div class="text-center">
                  <div
                    class="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                    <TrendingUp class="w-10 h-10 text-white" />
                  </div>
                  <h3 class="text-2xl font-bold text-gray-900 mb-4">Ready to Start?</h3>
                  <p class="text-gray-600 mb-6">
                    Join our platform and experience streamlined company management today.
                  </p>
                  <router-link to="/auth"
                    class="inline-flex items-center px-6 py-3 border border-transparent text-base font-semibold rounded-xl text-white bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 shadow-lg transition-all duration-300 transform hover:scale-105">
                    <ArrowRight class="w-5 h-5 mr-2" />
                    Get Started Now
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <CustomFooter />
  </div>
</template>

<script setup>
import {
  User,
  Building,
  Code,
  Rocket,
  Eye,
  FolderOpen,
  ListChecks,
  Users,
  Shield,
  Zap,
  Target,
  TrendingUp,
  ArrowRight
} from 'lucide-vue-next'
import CustomFooter from '@/components/CustomFooter.vue';
</script>

<style scoped>
/* Custom gradient text support */
.bg-clip-text {
  -webkit-background-clip: text;
  background-clip: text;
}

/* Smooth scrolling for anchor links */
html {
  scroll-behavior: smooth;
}

/* Custom animation for hover effects */
@keyframes float {

  0%,
  100% {
    transform: translateY(0px);
  }

  50% {
    transform: translateY(-10px);
  }
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}
</style>
