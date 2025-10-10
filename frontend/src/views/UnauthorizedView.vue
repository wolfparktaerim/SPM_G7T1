<template>
  <div
    class="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 text-white px-4">
    <div class="text-center space-y-6 max-w-2xl">
      <h1 class="text-[12rem] md:text-[16rem] font-black text-yellow-500 leading-none animate-pulse">403</h1>
      <div class="space-y-3">
        <p class="text-3xl md:text-4xl font-bold tracking-tight">Access Denied</p>
        <p class="text-lg md:text-xl text-gray-300 max-w-md mx-auto leading-relaxed">
          You don't have permission to access this page or resource.
        </p>
      </div>
      <button @click="goBack"
        class="cursor-pointer inline-flex items-center gap-2 mt-8 px-8 py-4 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 focus:ring-4 focus:ring-red-500/50 transition-all duration-300 text-white font-semibold text-lg rounded-xl shadow-xl hover:shadow-2xl hover:scale-105 transform">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Go Back
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: "UnauthorizedView",
  methods: {
    goBack() {
      // Check if there's a previous page in history
      if (window.history.length > 1) {
        this.$router.go(-1)
      } else {
        // If no history, go to home page as fallback
        this.$router.push('/')
      }
    }
  }
};
</script>
