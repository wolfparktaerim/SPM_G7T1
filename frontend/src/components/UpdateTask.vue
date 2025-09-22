<template>
  <div class="max-w-xl mx-auto p-6 bg-white rounded-lg shadow-md">
    <h3 class="text-2xl font-semibold mb-6 text-gray-800">Update Task</h3>
    
    <div class="mb-6 flex gap-2">
      <input v-model="loadUid" placeholder="Enter Task ID to load" class="flex-grow px-4 py-2 border rounded-md focus:ring-indigo-500 focus:outline-none" />
      <button @click="loadTask" class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition">Load Task</button>
    </div>
    
    <form v-if="taskLoaded" @submit.prevent="submitUpdate" class="space-y-5">
      <div>
        <label class="block mb-1 font-medium text-gray-700">User ID (auto from cookie):</label>
        <input v-model="userid" readonly class="w-full px-4 py-2 border rounded-md bg-gray-100 cursor-not-allowed" type="text" />
      </div>

      <div>
        <label class="block mb-1 font-medium text-gray-700">Role:</label>
        <select v-model="role" disabled class="w-full px-4 py-2 border rounded-md bg-gray-100 cursor-not-allowed">
          <option disabled value="">Select role</option>
          <option>user</option>
          <option>manager</option>
          <option>director</option>
        </select>
      </div>

      <div>
        <label class="block mb-1 font-medium text-gray-700">Task ID (uid):</label>
        <input v-model="uid" readonly class="w-full px-4 py-2 border rounded-md bg-gray-100 cursor-not-allowed" type="text" />
      </div>

      <div>
         <label class="block mb-1 font-medium text-gray-700">Title:</label>
         <input v-model="title" class="w-full px-4 py-2 border rounded-md focus:ring-indigo-500 focus:outline-none" type="text" />
      </div>

      <div>
        <label class="block mb-1 font-medium text-gray-700">Deadline:</label>
        <input type="date" v-model="deadline" class="w-full px-4 py-2 border rounded-md focus:ring-indigo-500 focus:outline-none" />
      </div>

      <div>
        <label class="block mb-1 font-medium text-gray-700">Status:</label>
        <select v-model="status" class="w-full px-4 py-2 border rounded-md focus:ring-indigo-500 focus:outline-none bg-white" required>
          <option value="Unassigned">Unassigned</option>
          <option value="Ongoing">Ongoing</option>
          <option value="Under Review">Under Review</option>
          <option value="Completed">Completed</option>
        </select>
      </div>

      <div>
        <label class="block mb-1 font-medium text-gray-700">Notes:</label>
        <textarea v-model="notes" rows="3" class="w-full px-4 py-2 border rounded-md focus:ring-indigo-500 focus:outline-none resize-none"></textarea>
      </div>

      <div>
        <label class="block mb-1 font-medium text-gray-700">Attachments (comma-separated URLs):</label>
        <input v-model="attachments" class="w-full px-4 py-2 border rounded-md focus:ring-indigo-500 focus:outline-none" type="text" placeholder="URL1, URL2" />
      </div>

      <div>
        <label class="block mb-1 font-medium text-gray-700">Owner UID:</label>
        <input v-model="ownerUid" 
               :readonly="ownerUidReadonly" 
               :class="ownerUidReadonly ? 'bg-gray-100 cursor-not-allowed' : 'bg-white cursor-auto'" 
               class="w-full px-4 py-2 border rounded-md focus:ring-indigo-500 focus:outline-none" 
               type="text" />
      </div>

      <div>
        <label class="block mb-1 font-medium text-gray-700">Collaborators (comma-separated UIDs):</label>
        <input v-model="collaborators" class="w-full px-4 py-2 border rounded-md focus:ring-indigo-500 focus:outline-none" type="text" placeholder="User1, User2" />
      </div>

      <div>
        <label class="block mb-1 font-medium text-gray-700">Project:</label>
        <input v-model="project" class="w-full px-4 py-2 border rounded-md focus:ring-indigo-500 focus:outline-none" type="text" />
      </div>

      <button type="submit" class="w-full py-3 bg-indigo-600 text-white font-bold rounded-md hover:bg-indigo-700 transition">
        Update Task
      </button>
    </form>

    <div v-if="message" :class="error ? 'text-red-600 mt-4 font-semibold' : 'text-green-600 mt-4 font-semibold'">
      {{ message }}
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { useAuthStore } from '@/stores/auth.js'
import { watch } from 'vue'

export default {
  data() {
    return {
      loadUid: '',
      userid: '',
      role: '',
      uid: '',
      title: '',
      deadline: '',
      status: '',
      notes: '',
      attachments: '',
      ownerUid: '',
      collaborators: '',
      project: '',
      message: '',
      error: false,
      taskLoaded: false,
    };
  },
  computed: {
    ownerUidReadonly() {
      // Owner UID is readonly if status is not 'Unassigned' OR user role is 'staff'
      return this.status.toLowerCase() !== 'unassigned' || this.role.toLowerCase() === 'staff';
    }
  },
  setup() {
    const authStore = useAuthStore()

    watch(
      () => authStore.user,
      (newUser) => {
        console.log('User data from auth store:', newUser)
      },
      { immediate: true }
    )

    return { authStore }
  },
  mounted() {
    if(this.authStore.user){
      this.userid = this.authStore.user.uid
      this.role = this.authStore.user.role || ''
      console.log('User ID:', this.userid, 'Role:', this.role)
    }
  },
  methods: {
    async loadTask() {
      this.message = ''
      this.error = false
      if (!this.loadUid) {
        this.message = 'Please enter a Task ID to load.'
        this.error = true
        return
      }
      try {
        const response = await axios.get(`http://localhost:8000/task/${this.loadUid}`)
        console.log('Load Task response:', response)
        if (response.status !== 200) throw new Error(response.data.error || 'Failed to fetch task')
        
        const task = response.data.task
        if(!task) throw new Error('No task data found')

        this.uid = task.uid
        this.title = task.title || ''
        this.deadline = task.deadline ? task.deadline.split('T')[0] : '' // format date to yyyy-mm-dd for input
        this.status = task.status || ''
        this.notes = task.notes || ''
        this.attachments = Array.isArray(task.attachments) ? task.attachments.join(', ') : ''
        this.ownerUid = task.ownerUid || ''
        this.collaborators = Array.isArray(task.collaborators) ? task.collaborators.join(', ') : ''
        this.project = task.project || ''
        this.taskLoaded = true
        this.message = 'Task loaded successfully. You can now update the fields.'
        this.error = false
      } catch (err) {
        this.message = 'Error loading task: ' + err.message
        this.error = true
        this.taskLoaded = false
      }
    },
    async submitUpdate() {
      this.message = ''
      this.error = false

      if (!this.userid || !this.role) {
        this.message = 'User ID or Role missing from store. Please login or select.'
        this.error = true
        return
      }
      const updateData = {
        userid: this.userid,
        role: this.role,
        uid: this.uid,
      }
      if (this.title) updateData.title = this.title
      if (this.deadline) updateData.deadline = this.deadline
      if (this.status) updateData.status = this.status
      if (this.notes) updateData.notes = this.notes
      if (this.attachments) updateData.attachments = this.attachments.split(',').map(a => a.trim())
      // Only include ownerUid if allowed to edit
      if (!this.ownerUidReadonly && this.ownerUid) updateData.ownerUid = this.ownerUid
      if (this.collaborators) updateData.collaborators = this.collaborators.split(',').map(c => c.trim())
      if (this.project) updateData.project = this.project

      try {
        const response = await axios.post('http://localhost:8000/task/update', updateData)
        console.log('Update Task response:', response)
        if (response.status === 200) {
          this.message = response.data.message || 'Task updated successfully'
          this.error = false
        } else {
          this.message = response.data.error || 'Failed to update task'
          this.error = true
        }
      } catch (err) {
        this.message = 'Error: ' + (err.response?.data?.error || err.message)
        this.error = true
      }
    },
  },
}
</script>
