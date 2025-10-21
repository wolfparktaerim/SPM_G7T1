<template>
  <div
    class="flex flex-col h-full max-h-[75vh] min-h-[400px] bg-gradient-to-b from-white to-gray-50 rounded-2xl overflow-hidden"
    @click.stop>
    <!-- Section Header -->
    <div class="flex justify-between items-center px-6 py-5 border-b-2 border-gray-200 bg-white flex-shrink-0">
      <div class="flex items-center gap-3">
        <MessageSquare class="w-5 h-5 text-blue-600" />
        <h3 class="text-xl font-bold text-gray-900 m-0">Comments & Discussion</h3>
      </div>
      <div v-if="activeThreads.length > 0"
        class="flex items-center px-3 py-1.5 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-full text-xs font-semibold shadow-md shadow-blue-500/20">
        {{ activeThreads.length }} {{ activeThreads.length === 1 ? 'thread' : 'threads' }}
      </div>
    </div>

    <!-- New Comment Input  -->
    <div class="border-b-2 border-gray-200 px-6 py-5 bg-white flex-shrink-0 relative">
      <div class="flex justify-between items-center mb-4">
        <h4 class="flex items-center gap-2 text-base font-semibold text-gray-700 m-0">
          <PlusCircle class="w-4 h-4" />
          Add Comment
        </h4>
        <div v-if="availableCollaborators.length > 0" class="flex items-center gap-1.5 text-xs text-gray-600">
          <AtSign class="w-3 h-3" />
          <span>Type <kbd
              class="px-1.5 py-0.5 bg-gradient-to-b from-gray-50 to-gray-100 border border-gray-300 rounded text-xs font-mono shadow-sm">@</kbd>
            to mention</span>
        </div>
      </div>

      <!-- Mentioned Users Display -->
      <div v-if="mentionedUserIds.length > 0"
        class="flex items-center gap-3 px-3.5 py-3 bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-xl mb-4 flex-wrap">
        <div class="flex items-center gap-1.5 text-xs text-blue-900 font-semibold whitespace-nowrap">
          <Users class="w-3.5 h-3.5" />
          <span>Mentioning:</span>
        </div>
        <div class="flex flex-wrap gap-2 flex-1">
          <button v-for="userId in mentionedUserIds" :key="userId" @click="removeMention(userId)"
            class="flex items-center gap-1.5 px-2.5 py-1.5 bg-white text-blue-900 border border-blue-300 rounded-lg text-xs font-medium cursor-pointer transition-all duration-200 shadow-sm hover:bg-red-50 hover:border-red-300 hover:text-red-600 hover:-translate-y-0.5 hover:shadow-md active:translate-y-0"
            type="button">
            <span>{{ getUserDisplayName(userId) }}</span>
            <X class="w-3 h-3" />
          </button>
        </div>
      </div>

      <!-- Comment Textarea -->
      <div class="flex flex-col gap-4">
        <textarea v-model="newComment" ref="commentInputRef" @input="handleInput" @keydown="handleKeyDown"
          placeholder="Write a comment... Use @ to mention collaborators"
          class="w-full px-4 py-3.5 border-2 border-gray-300 rounded-xl text-base leading-6 resize-y min-h-[90px] max-h-[180px] transition-all duration-200 font-inherit bg-white placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:shadow-[0_0_0_3px_rgba(59,130,246,0.1)] focus:bg-blue-50/30"
          rows="3"></textarea>

        <!-- Mention Dropdown - Positioned directly below textarea -->
        <div v-if="showMentionDropdown && filteredMentionList.length > 0"
          class="absolute left-6 right-6 bg-white border border-gray-200 rounded-xl shadow-2xl max-h-[240px] overflow-y-auto z-20"
          :style="{ top: mentionDropdownTop }">
          <div
            class="flex items-center gap-2 px-4 py-3 text-xs font-bold text-gray-700 border-b border-gray-200 bg-gradient-to-b from-gray-50 to-white uppercase tracking-wide sticky top-0 z-10">
            <AtSign class="w-4 h-4" />
            <span>Mention Collaborators</span>
          </div>
          <div v-for="user in filteredMentionList" :key="user.uid"
            class="flex items-center gap-3.5 px-4 py-3.5 cursor-pointer transition-all duration-150 border-b border-gray-100 last:border-b-0 hover:bg-gradient-to-r hover:from-blue-50 hover:to-blue-100 hover:translate-x-1"
            @click="selectMention(user)">
            <div
              class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0 shadow-md shadow-blue-500/20">
              {{ getInitials(user.displayName) }}
            </div>
            <div class="flex flex-col gap-1 flex-1 min-w-0">
              <span class="font-semibold text-base text-gray-900 whitespace-nowrap overflow-hidden text-ellipsis">{{
                user.displayName }}</span>
              <div class="flex items-center gap-1.5 text-xs text-gray-600">
                <Building2 class="w-3 h-3" />
                <span>{{ user.department }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex justify-end items-center">
          <button @click="submitComment" :disabled="!canSubmitComment || isSubmitting"
            class="flex items-center gap-2.5 px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white border-0 rounded-xl font-semibold text-base cursor-pointer transition-all duration-200 shadow-lg shadow-blue-500/20 disabled:bg-gradient-to-r disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed disabled:shadow-none enabled:hover:from-blue-600 enabled:hover:to-blue-700 enabled:hover:-translate-y-0.5 enabled:hover:shadow-xl enabled:hover:shadow-blue-500/30 enabled:active:translate-y-0">
            <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" />
            <Send v-else class="w-4 h-4" />
            <span>{{ isSubmitting ? 'Posting...' : 'Post Comment' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Tab Navigation (NEW) -->
    <div class="flex border-b-2 border-gray-200 bg-white px-6 flex-shrink-0">
      <button @click="activeTab = 'active'" :class="[
        'px-4 py-3 font-semibold text-sm transition-all duration-200 border-b-2 -mb-[2px]',
        activeTab === 'active'
          ? 'text-blue-600 border-blue-600'
          : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
      ]">
        <div class="flex items-center gap-2">
          <MessageCircle class="w-4 h-4" />
          <span>Active</span>
          <span class="px-2 py-0.5 bg-blue-100 text-blue-600 rounded-full text-xs font-bold">
            {{ activeThreads.length }}
          </span>
        </div>
      </button>
      <button @click="activeTab = 'resolved'" :class="[
        'px-4 py-3 font-semibold text-sm transition-all duration-200 border-b-2 -mb-[2px]',
        activeTab === 'resolved'
          ? 'text-green-600 border-green-600'
          : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
      ]">
        <div class="flex items-center gap-2">
          <CheckCircle class="w-4 h-4" />
          <span>Resolved</span>
          <span class="px-2 py-0.5 bg-green-100 text-green-600 rounded-full text-xs font-bold">
            {{ resolvedThreads.length }}
          </span>
        </div>
      </button>
    </div>

    <!-- Scrollable Comments Container -->
    <div class="flex-1 overflow-y-auto px-6 py-6 max-h-[calc(75vh-300px)] min-h-[200px]" ref="commentsContainerRef">
      <!-- Loading State -->
      <div v-if="isLoading" class="flex flex-col items-center justify-center px-8 py-16 h-full">
        <div class="relative mb-6">
          <div class="w-16 h-16 border-4 border-gray-200 rounded-full"></div>
          <div
            class="absolute top-0 left-0 w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin">
          </div>
        </div>
        <p class="text-lg font-semibold text-gray-700 mb-2">Loading comments...</p>
        <p class="text-sm text-gray-500">Please wait while we fetch the discussion</p>
      </div>

      <!-- Active Tab Content (NEW) -->
      <div v-else-if="activeTab === 'active'">
        <div v-if="activeThreads.length > 0" class="flex flex-col gap-4">
          <CommentThread v-for="(thread, index) in activeThreads" :key="index" :thread="thread" :thread-index="index"
            :parent-id="parentId" :parent-type="parentType" :current-user-id="currentUserId" :all-users="allUsers"
            :collaborators="collaboratorUsers" @reply-added="handleReplyAdded"
            @thread-resolved="handleThreadResolved" />
        </div>
        <div v-else class="flex flex-col items-center justify-center px-8 py-16 text-center h-full">
          <div class="mb-6 p-6 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full">
            <MessageCircle class="w-16 h-16 text-gray-300" />
          </div>
          <p class="text-xl font-semibold text-gray-700 mb-2">No active comments</p>
          <p class="text-base text-gray-600 max-w-xs">Start a conversation to collaborate with your team</p>
        </div>
      </div>

      <!-- Resolved Tab Content (NEW) -->
      <div v-else-if="activeTab === 'resolved'">
        <div v-if="resolvedThreads.length > 0" class="flex flex-col gap-4">
          <CommentThread v-for="(thread, index) in resolvedThreads" :key="index" :thread="thread"
            :thread-index="getOriginalThreadIndex(thread)" :parent-id="parentId" :parent-type="parentType"
            :current-user-id="currentUserId" :all-users="allUsers" :collaborators="collaboratorUsers"
            :is-resolved="true" @reply-added="handleReplyAdded" @thread-resolved="handleThreadResolved" />
        </div>
        <div v-else class="flex flex-col items-center justify-center px-8 py-16 text-center h-full">
          <div class="mb-6 p-6 bg-gradient-to-br from-green-100 to-green-200 rounded-full">
            <CheckCircle class="w-16 h-16 text-green-300" />
          </div>
          <p class="text-xl font-semibold text-gray-700 mb-2">No resolved comments</p>
          <p class="text-base text-gray-600 max-w-xs">Resolved conversations will appear here</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios'
import {
  Send,
  Loader2,
  MessageSquare,
  MessageCircle,
  PlusCircle,
  AtSign,
  Users,
  X,
  Building2,
  CheckCircle
} from 'lucide-vue-next'
import CommentThread from './CommentThread.vue'

const props = defineProps({
  parentId: {
    type: String,
    required: true
  },
  parentType: {
    type: String,
    required: true,
    validator: (value) => ['task', 'subtask'].includes(value)
  },
  currentUserId: {
    type: String,
    required: true
  },
  allUsers: {
    type: Array,
    default: () => []
  },
  collaborators: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['thread-created', 'thread-updated', 'thread-resolved'])
const activeTab = ref('active') // 'active' or 'resolved'
// Composables
const toast = useToast()

// Refs
const commentInputRef = ref(null)
const commentsContainerRef = ref(null)

// State
const commentThreads = ref([])
const newComment = ref('')
const mentionedUserIds = ref([])
const isSubmitting = ref(false)
const isLoading = ref(false)

// Mention dropdown state
const showMentionDropdown = ref(false)
const mentionSearchQuery = ref('')
const cursorPosition = ref(0)
const mentionDropdownTop = ref('auto')

// Computed
const activeThreads = computed(() => {
  return commentThreads.value.filter(thread => thread.active !== false)
})

const resolvedThreads = computed(() => {
  return commentThreads.value.filter(thread => thread.active === false)
})

// Get full user objects for collaborators (excluding current user)
const collaboratorUsers = computed(() => {
  return props.allUsers.filter(user =>
    props.collaborators.includes(user.uid)
  )
})

// Filter out current user from collaborators list for mentioning
const availableCollaborators = computed(() => {
  return collaboratorUsers.value.filter(user => user.uid !== props.currentUserId)
})

// Filter mention list based on search query
const filteredMentionList = computed(() => {
  if (!mentionSearchQuery.value) {
    return availableCollaborators.value
  }

  const query = mentionSearchQuery.value.toLowerCase()
  return availableCollaborators.value.filter(user => {
    const name = user.displayName?.toLowerCase() || ''
    const dept = user.department?.toLowerCase() || ''
    return name.includes(query) || dept.includes(query)
  })
})

const canSubmitComment = computed(() => {
  return newComment.value.trim().length > 0 && !isSubmitting.value
})

// Functions
async function fetchComments() {
  if (!props.parentId) return

  isLoading.value = true

  try {
    const response = await axios.get(
      `${import.meta.env.VITE_BACKEND_API}comments/${props.parentId}`,
      {
        params: {
          type: props.parentType
        }
      }
    )

    if (response.data.commentThreads) {
      commentThreads.value = response.data.commentThreads
    }
  } catch (error) {
    console.error('Error fetching comments:', error)
    toast.error('Failed to load comments')
  } finally {
    isLoading.value = false
  }
}

function handleInput(event) {
  const textarea = event.target
  const text = textarea.value
  const position = textarea.selectionStart

  cursorPosition.value = position

  // Calculate dropdown position
  if (commentInputRef.value) {
    const textareaRect = commentInputRef.value.getBoundingClientRect()
    mentionDropdownTop.value = `${textareaRect.bottom - textareaRect.top + 80}px`
  }

  // Check for @ mention trigger
  const textBeforeCursor = text.substring(0, position)
  const atIndex = textBeforeCursor.lastIndexOf('@')

  if (atIndex !== -1 && availableCollaborators.value.length > 0) {
    const textAfterAt = textBeforeCursor.substring(atIndex + 1)

    // Check if there's a space after @ (which would close the mention)
    if (!textAfterAt.includes(' ')) {
      mentionSearchQuery.value = textAfterAt
      showMentionDropdown.value = true
      return
    }
  }

  showMentionDropdown.value = false
  mentionSearchQuery.value = ''
}

function handleKeyDown(event) {
  // Close dropdown on Escape
  if (event.key === 'Escape' && showMentionDropdown.value) {
    showMentionDropdown.value = false
    mentionSearchQuery.value = ''
  }
}

function selectMention(user) {
  const textarea = commentInputRef.value
  const text = textarea.value
  const textBeforeCursor = text.substring(0, cursorPosition.value)
  const atIndex = textBeforeCursor.lastIndexOf('@')

  if (atIndex !== -1) {
    // Replace @query with @DisplayName
    const beforeAt = text.substring(0, atIndex)
    const afterCursor = text.substring(cursorPosition.value)

    newComment.value = `${beforeAt}@${user.displayName} ${afterCursor}`

    // Add to mentioned users if not already there
    if (!mentionedUserIds.value.includes(user.uid)) {
      mentionedUserIds.value.push(user.uid)
    }

    // Close dropdown
    showMentionDropdown.value = false
    mentionSearchQuery.value = ''

    // Focus back on textarea
    nextTick(() => {
      textarea.focus()
      const newPosition = atIndex + user.displayName.length + 2 // +2 for @ and space
      textarea.setSelectionRange(newPosition, newPosition)
    })
  }
}

function removeMention(userId) {
  // Remove user from mentioned list
  mentionedUserIds.value = mentionedUserIds.value.filter(id => id !== userId)

  // Remove @mention from text
  const user = props.allUsers.find(u => u.uid === userId)
  if (user) {
    const mentionPattern = new RegExp(`@${user.displayName}\\s?`, 'g')
    newComment.value = newComment.value.replace(mentionPattern, '')
  }

  toast.info(`Removed mention: ${getUserDisplayName(userId)}`)
}

function getOriginalThreadIndex(thread) {
  // Find the original index in the full commentThreads array
  return commentThreads.value.findIndex(t => t === thread)
}

async function submitComment() {
  if (!canSubmitComment.value) return

  isSubmitting.value = true

  try {
    const payload = {
      comment: newComment.value.trim(),
      userId: props.currentUserId,
      creationDate: Math.floor(Date.now() / 1000),
      mention: mentionedUserIds.value,
      type: props.parentType,
      parentId: props.parentId
    }

    const response = await axios.post(
      `${import.meta.env.VITE_BACKEND_API}comments`,
      payload
    )

    if (response.data.commentThread) {
      commentThreads.value.push(response.data.commentThread)
      emit('thread-created', response.data.commentThread)

      // Clear inputs
      newComment.value = ''
      mentionedUserIds.value = []

      toast.success('Comment posted successfully')

      // Scroll to bottom
      nextTick(() => {
        if (commentsContainerRef.value) {
          commentsContainerRef.value.scrollTop = commentsContainerRef.value.scrollHeight
        }
      })
    }
  } catch (error) {
    console.error('Error posting comment:', error)
    toast.error(error.response?.data?.error || 'Failed to post comment')
  } finally {
    isSubmitting.value = false
  }
}

function handleReplyAdded(data) {
  // Update the thread in our local state
  if (data.threadIndex >= 0 && data.threadIndex < commentThreads.value.length) {
    commentThreads.value[data.threadIndex] = data.thread
    emit('thread-updated', data)
  }
}

function handleThreadResolved(data) {
  // Update the thread's active status
  if (data.threadIndex >= 0 && data.threadIndex < commentThreads.value.length) {
    commentThreads.value[data.threadIndex] = data.thread
    emit('thread-resolved', data)
  }
}

function getUserDisplayName(userId) {
  const user = props.allUsers.find(u => u.uid === userId)
  return user?.displayName || 'Unknown User'
}

function getInitials(name) {
  if (!name) return '?'
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2)
}

watch(
  () => [props.parentId, props.parentType],
  () => {
    // Clear state
    commentThreads.value = []
    newComment.value = ''
    mentionedUserIds.value = []
    showMentionDropdown.value = false
    activeTab.value = 'active'

    // Fetch if valid
    if (props.parentId && props.parentType) {
      fetchComments()
    }
  },
  { immediate: true }
)

// Clean up on unmount
onUnmounted(() => {
  commentThreads.value = []
  newComment.value = ''
  mentionedUserIds.value = []
})

// Lifecycle
onMounted(() => {
  fetchComments()
})
</script>

<style scoped>
/* Scrollbar styling */
.overflow-y-auto::-webkit-scrollbar {
  width: 10px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f9fafb;
  border-radius: 5px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #d1d5db, #9ca3af);
  border-radius: 5px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to bottom, #9ca3af, #6b7280);
}

@media (max-width: 640px) {
  .flex-col.gap-3 {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
