import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './assets/main.css'

import Toast from 'vue-toastification'
// Import the CSS or use your own!
import 'vue-toastification/dist/index.css'

import App from './App.vue'
import router from './router'
import { scheduleAutoCleanup } from './utils/passwordResetCleanup'

const app = createApp(App)

// options for toast
// how to use toast notification: https://github.com/Maronato/vue-toastification
const options = {
  // You can set your default options here
}

app.use(Toast, options)

app.use(createPinia())
app.use(router)

app.mount('#app')

// Schedule automatic cleanup of expired password reset requests every hour
scheduleAutoCleanup(60)
