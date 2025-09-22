<template>
  <NavigationBar />
  <div>
    This is the task view
  </div>
    <div>
    This is the projects view
    <UpdateTask />
  </div>
</template>

<script setup>
import NavigationBar from '@/components/NavigationBar.vue';
import UpdateTask from '@/components/UpdateTask.vue';
</script>

<style scoped></style>
