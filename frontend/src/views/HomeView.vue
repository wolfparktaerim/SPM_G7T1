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
        <div class="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-6 mb-12 shadow-lg">
          <div class="flex items-start space-x-4">
            <div class="flex-shrink-0">
              <div class="w-10 h-10 bg-yellow-400 rounded-xl flex items-center justify-center">
                <Code class="w-5 h-5 text-yellow-800" />
              </div>
            </div>
            <div class="flex-1 min-w-0">
              <h2 class="text-xl font-bold text-yellow-800 mb-4">
                🚀 Developer Notes - Frontend Updates (by TaiLin 🐺)
              </h2>
              <div class="text-yellow-700 text-sm space-y-4 leading-relaxed">
                <p class="font-medium">
                  So just a few updates on the frontend (well i think i finished my 6 hrs coding this week alr... but
                  idm do up to 10hrs ofc) and it's pushed to github <span class="font-bold text-lg">develop</span>
                  branch:
                </p>

                <ol class="list-decimal list-inside space-y-2 ml-4">
                  <li>I made many empty view pages (for whoever responsible to fill in themselves) and integrated with
                    the navigation bar (you need to log in the system first, the home page which is for guest is not
                    integrated with navigation bar)</li>

                  <li>A standard simple homepage allow you to login and register</li>

                  <li>Auth routing: if you are logged in, the system will save your credentials and you are free to
                    navigate to any page given ('Tasks', 'Projects' ... ) else you will be stopped and the system will
                    bring you to the authenticate page (for you to login / register)</li>

                  <li>There is a not-found page redirection happens when you key in some random url like /asdjaghfyag ,
                    and there is a button for you to go back</li>

                  <li>There is an unauthorized page currently not really useful but just included for future (in case
                    they want stricter hierarchy). You can access it by key in /unauthorized</li>

                  <li>
                    <span class="text-red-700 font-bold text-md">Login & Registration functions</span> are used in the
                    same
                    page called <span class="font-bold">AuthView.vue</span>, the firebase functions are
                    implemented correctly but there is one user story acceptance criteria missing which is
                    <strong>"Users can only choose the roles and departments available in the system."</strong> becuz
                    there are too many titles in the org chart and im lazy, i assume the responsible person for this
                    feature is <span class="bg-yellow-200 px-2 py-1 rounded font-mono text-md font-bold">@Tengku
                      Shamel</span> so i
                    will leave it
                    to you, the relevant files you may need to change are:
                    <ul class="list-disc list-inside mt-2 ml-4 space-y-1">
                      <li><code class="bg-yellow-200 px-1 py-0.5 rounded text-xs">frontend/src/models/users.js</code>
                        (it defines a user's attributes)</li>
                      <li><code class="bg-yellow-200 px-1 py-0.5 rounded text-xs">frontend/src/services/users.js</code>
                        (it defines CRUD functions related to user entity)</li>
                      <li><code class="bg-yellow-200 px-1 py-0.5 rounded text-xs">frontend/src/stores/auth.js</code>
                        (for authentication) (optional becuz it should be very well implemented alr, but this is where
                        you should visit if there are authentication issues)</li>
                      <li><code class="bg-yellow-200 px-1 py-0.5 rounded text-xs">frontend/src/views/AuthView.vue</code>
                        (the main auth view page, you can update UI UX and password strength threshold..)</li>
                    </ul>
                    <p class="mt-2">improve redirection (smoother) improve pop up message (use toast-notification)</p>
                    <p class="mt-1">in future you will have to change it anyway, you need to include another attribute
                      called "notifications" in the user attribute integrated with notification system (not doing
                      anytime soon)
                    </p>
                  </li>

                  <li>
                    I have created 3 accts yall can try:
                    <ul class="list-disc list-inside mt-1 ml-4">
                      <li><code class="bg-blue-100 px-2 py-1 rounded text-xs">testmgr@g7t1.com</code></li>
                      <li><code class="bg-blue-100 px-2 py-1 rounded text-xs">teststaff@g7t1.com</code></li>
                      <li><code class="bg-blue-100 px-2 py-1 rounded text-xs">testdir@g7t1.com</code></li>
                    </ul>
                    <p class="mt-1">password is all the same: <code
                        class="bg-red-100 px-2 py-1 rounded text-xs font-bold">@Aa123456</code></p>
                  </li>

                  <li><strong class="text-red-600">RMB TO PUT MY .ENV FILE THAT I PINNED INSIDE FRONTEND FOLDER
                      OTHERWISE FIREBASE WONT WORK AND ALSO RESTART YOUR SERVER AFTER THAT</strong></li>

                  <li>Let me know if there's any bug you found - you can create a hotfix branch to fix it yourself if
                    needs be. The test cases not well tested yet, and bugs are unavoidable (fixing them is the most
                    painful
                    part...)</li>

                  <li>I think I have done quite enough foundation for you guys to work and explore in so... <strong
                      class="text-green-600">HAVE FUNNNNN CODINNNG</strong></li>
                </ol>
              </div>
            </div>
          </div>
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
              G7T1 Management
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
              Why Choose G7T1?
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
                G7T1 Management System is designed to streamline your company's workflow
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
