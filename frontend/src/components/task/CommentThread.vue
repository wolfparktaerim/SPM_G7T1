<template>
  <div
    class="px-6 py-5 bg-white border border-gray-200 rounded-2xl transition-all duration-200 hover:shadow-lg hover:border-gray-300"
    :class="{ 'opacity-60 bg-gray-50': !thread.active }" @click.stop>
    <!-- Thread Header -->
    <div class="flex justify-between items-start mb-4">
      <div class="flex gap-3 flex-1">
        <div
          class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0 shadow-md shadow-blue-500/20">
          {{ getInitials(getAuthorName(thread.comments[0][0])) }}
        </div>
        <div class="flex flex-col gap-1 flex-1">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-semibold text-base text-gray-900">{{ getAuthorName(thread.comments[0][0]) }}</span>
            <span v-if="!thread.active"
              class="flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
              <CheckCircle2 class="w-3 h-3" />
              Resolved
            </span>
          </div>
          <div class="flex items-center gap-2 text-xs text-gray-600 flex-wrap">
            <div class="flex items-center gap-1">
              <Clock class="w-3 h-3" />
              <span>{{ formatTimestamp(thread.creation_date) }}</span>
            </div>
            <span v-if="thread.mention && thread.mention.length > 0" class="flex items-center gap-1 text-blue-600">
              <AtSign class="w-3 h-3" />
              {{ thread.mention.length }} {{ thread.mention.length === 1 ? 'mention' : 'mentions' }}
            </span>
          </div>
        </div>
      </div>
      <div class="flex gap-2 flex-shrink-0">
        <button v-if="thread.active" @click="toggleReplyInput"
          class="flex items-center justify-center w-9 h-9 bg-white border-2 border-gray-300 rounded-lg cursor-pointer transition-all duration-200 text-gray-600 hover:bg-gradient-to-br hover:from-blue-100 hover:to-blue-200 hover:border-blue-300 hover:text-blue-600 hover:-translate-y-0.5 hover:shadow-md"
          :class="{ '!bg-gradient-to-br !from-blue-100 !to-blue-200 !border-blue-300 !text-blue-600': showReplyInput }"
          :title="showReplyInput ? 'Cancel Reply' : 'Reply to thread'">
          <MessageCircle class="w-4 h-4" />
        </button>
        <button v-if="canResolve" @click="confirmResolveThread"
          class="flex items-center justify-center w-9 h-9 bg-white border-2 border-gray-300 rounded-lg cursor-pointer transition-all duration-200 text-gray-600 hover:bg-gradient-to-br hover:from-green-100 hover:to-green-200 hover:border-green-300 hover:text-green-600 hover:-translate-y-0.5 hover:shadow-md"
          :title="thread.active ? 'Mark as resolved' : 'Reopen thread'">
          <Check v-if="thread.active" class="w-4 h-4" />
          <RotateCcw v-else class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Initial Comment -->
    <div class="ml-[52px]">
      <div class="text-gray-700 text-base leading-relaxed whitespace-pre-wrap break-words mb-3">{{ thread.comments[0][1]
      }}</div>
      <div v-if="thread.mention && thread.mention.length > 0"
        class="flex items-start gap-2 px-3 py-2.5 bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-xl text-xs text-blue-900">
        <Users class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
        <div class="flex flex-col gap-1">
          <span class="font-semibold">Mentioned:</span>
          <div class="flex flex-wrap gap-1">
            <span v-for="(userId, idx) in thread.mention" :key="userId" class="font-medium">
              {{ getAuthorName(userId) }}{{ idx < thread.mention.length - 1 ? ', ' : '' }} </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Replies -->
    <div v-if="thread.comments.length > 1"
      class="ml-[52px] pl-5 border-l-[3px] border-gray-300 flex flex-col gap-3.5 mt-4">
      <div class="flex items-center gap-2 text-xs font-bold text-gray-600 uppercase tracking-wide mb-1">
        <CornerDownRight class="w-4 h-4" />
        <span>{{ thread.comments.length - 1 }} {{ thread.comments.length - 1 === 1 ? 'Reply' : 'Replies' }}</span>
      </div>
      <div v-for="(comment, idx) in thread.comments.slice(1)" :key="idx"
        class="px-4 py-3.5 bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200 rounded-xl transition-all duration-200 hover:bg-white hover:border-gray-300 hover:shadow-md">
        <div class="flex gap-3 items-center mb-2.5">
          <div
            class="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0 shadow-sm shadow-blue-500/20">
            {{ getInitials(getAuthorName(comment[0])) }}
          </div>
          <div class="flex flex-col gap-1">
            <span class="font-semibold text-sm text-gray-900">{{ getAuthorName(comment[0]) }}</span>
            <div class="flex items-center gap-1.5 text-xs text-gray-600">
              <Clock class="w-3 h-3" />
              <span>{{ formatTimestamp(comment[2]) }}</span>
            </div>
          </div>
        </div>
        <div class="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap break-words">{{ comment[1] }}</div>
      </div>
    </div>

    <!-- Reply Input -->
    <div v-if="showReplyInput && thread.active"
      class="ml-[52px] mt-4 px-4 py-4 bg-gradient-to-br from-blue-50 to-cyan-50 border-2 border-blue-200 rounded-xl relative">
      <div class="flex justify-between items-center mb-3.5 gap-4 flex-wrap">
        <div class="flex items-center gap-2 text-base font-semibold text-blue-900">
          <Reply class="w-4 h-4" />
          <span>Reply to thread</span>
        </div>
        <div v-if="filteredCollaboratorsForReply.length > 0" class="flex items-center gap-1.5 text-xs text-blue-700">
          <AtSign class="w-3 h-3" />
          <span>Type <kbd
              class="px-1.5 py-0.5 bg-white border border-blue-300 rounded text-xs font-mono shadow-sm">@</kbd> to
            mention</span>
        </div>
      </div>

      <!-- Mentioned Users Display for Reply -->
      <div v-if="mentionedUserIds.length > 0"
        class="flex items-center gap-2.5 px-3 py-2.5 bg-white border border-blue-300 rounded-lg mb-3 flex-wrap">
        <div class="flex items-center gap-1.5 text-xs text-blue-900 font-semibold whitespace-nowrap">
          <Users class="w-3 h-3" />
          <span>Mentioning:</span>
        </div>
        <div class="flex flex-wrap gap-1.5 flex-1">
          <button v-for="userId in mentionedUserIds" :key="userId" @click="removeMention(userId)"
            class="flex items-center gap-1.5 px-2 py-1 bg-gradient-to-r from-blue-100 to-blue-200 text-blue-900 border border-blue-300 rounded-md text-xs font-medium cursor-pointer transition-all duration-200 hover:bg-gradient-to-r hover:from-red-50 hover:to-red-100 hover:border-red-300 hover:text-red-600 hover:scale-105 active:scale-100"
            type="button">
            <span>{{ getAuthorName(userId) }}</span>
            <X class="w-3 h-3" />
          </button>
        </div>
      </div>

      <!-- Mention Dropdown for Replies - Positioned directly below textarea -->
      <div v-if="showMentionDropdown && filteredMentionList.length > 0"
        class="absolute left-4 right-4 bg-white border-2 border-blue-300 rounded-xl shadow-2xl max-h-[180px] overflow-y-auto z-20"
        :style="{ top: replyDropdownTop }">
        <div
          class="flex items-center gap-2 px-3.5 py-2.5 text-xs font-bold text-gray-700 border-b border-gray-200 bg-gradient-to-b from-gray-50 to-white uppercase tracking-wide sticky top-0 z-10">
          <AtSign class="w-3.5 h-3.5" />
          <span>Mention Collaborators</span>
        </div>
        <div v-for="user in filteredMentionList" :key="user.uid"
          class="flex items-center gap-3 px-3.5 py-3 cursor-pointer transition-all duration-150 border-b border-gray-100 last:border-b-0 hover:bg-gradient-to-r hover:from-blue-50 hover:to-blue-100 hover:translate-x-1"
          @click="selectMention(user)">
          <div
            class="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0 shadow-sm shadow-blue-500/20">
            {{ getInitials(user.displayName) }}
          </div>
          <div class="flex flex-col gap-1 flex-1 min-w-0">
            <span class="font-semibold text-sm text-gray-900 whitespace-nowrap overflow-hidden text-ellipsis">{{
              user.displayName }}</span>
            <div class="flex items-center gap-1.5 text-xs text-gray-600">
              <Building2 class="w-3 h-3" />
              <span>{{ user.department }}</span>
            </div>
          </div>
        </div>
      </div>

      <textarea v-model="replyText" ref="replyInputRef" @input="handleReplyInput" @keydown="handleKeyDown"
        placeholder="Write a reply... Use @ to mention collaborators"
        class="w-full px-3 py-3 border-2 border-blue-300 rounded-lg text-sm leading-6 resize-y min-h-[70px] max-h-[140px] transition-all duration-200 font-inherit bg-white placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:shadow-[0_0_0_3px_rgba(59,130,246,0.1)]"
        rows="2"></textarea>

      <div class="flex justify-end mt-3">
        <div class="flex gap-2.5">
          <button @click="cancelReply"
            class="flex items-center gap-2 px-4 py-2.5 bg-white text-gray-600 border border-gray-300 rounded-lg text-sm font-medium cursor-pointer transition-all duration-200 hover:bg-gray-50 hover:border-gray-400 hover:text-gray-700">
            <X class="w-4 h-4" />
            <span>Cancel</span>
          </button>
          <button @click="submitReply" :disabled="!canSubmitReply || isSubmittingReply"
            class="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 text-white border-0 rounded-lg text-sm font-semibold cursor-pointer transition-all duration-200 shadow-md shadow-blue-500/25 disabled:bg-gradient-to-r disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed disabled:shadow-none enabled:hover:from-blue-600 enabled:hover:to-blue-700 enabled:hover:-translate-y-0.5 enabled:hover:shadow-lg enabled:hover:shadow-blue-500/35 enabled:active:translate-y-0">
            <Loader2 v-if="isSubmittingReply" class="w-4 h-4 animate-spin" />
            <Send v-else class="w-4 h-4" />
            <span>{{ isSubmittingReply ? 'Posting...' : 'Post Reply' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Confirmation Modal -->
    <ConfirmationModal :show="showResolveConfirm"
      :title="thread.active ? 'Resolve Comment Thread?' : 'Reopen Comment Thread?'"
      :description="thread.active ? 'This will mark the discussion as resolved.' : 'This will reopen the discussion.'"
      :confirm-text="thread.active ? 'Resolve' : 'Reopen'" :variant="thread.active ? 'info' : 'primary'"
      :icon="thread.active ? 'check' : 'info'" :is-loading="isResolving" @confirm="resolveThread"
      @cancel="showResolveConfirm = false" />
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios'
import {
  MessageCircle,
  Check,
  RotateCcw,
  Clock,
  Users,
  CornerDownRight,
  Reply,
  AtSign,
  X,
  Send,
  Loader2,
  Building2
} from 'lucide-vue-next'
import ConfirmationModal from '../ConfirmationModal.vue'

const props = defineProps({
  thread: {
    type: Object,
    required: true
  },
  threadIndex: {
    type: Number,
    required: true
  },
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
  },
  isResolved: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['reply-added', 'thread-resolved'])

// Composables
const toast = useToast()

// Refs
const replyInputRef = ref(null)

// State
const showReplyInput = ref(false)
const replyText = ref('')
const mentionedUserIds = ref([])
const isSubmittingReply = ref(false)
const showResolveConfirm = ref(false)
const isResolving = ref(false)

// Mention dropdown state
const showMentionDropdown = ref(false)
const mentionSearchQuery = ref('')
const cursorPosition = ref(0)
const replyDropdownTop = ref('auto')

// Computed
const canResolve = computed(() => {
  // Only the thread creator can resolve
  return props.thread.comments[0][0] === props.currentUserId
})

const filteredCollaboratorsForReply = computed(() => {
  return props.collaborators.filter(user => user.uid !== props.currentUserId)
})

const filteredMentionList = computed(() => {
  if (!mentionSearchQuery.value) {
    return filteredCollaboratorsForReply.value
  }

  const query = mentionSearchQuery.value.toLowerCase()
  return filteredCollaboratorsForReply.value.filter(user => {
    const name = user.displayName?.toLowerCase() || ''
    const dept = user.department?.toLowerCase() || ''
    return name.includes(query) || dept.includes(query)
  })
})

const canSubmitReply = computed(() => {
  return replyText.value.trim().length > 0 && !isSubmittingReply.value
})

// Functions
function getAuthorName(userId) {
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

function formatTimestamp(timestamp) {
  if (!timestamp) return 'Unknown time'

  const date = new Date(timestamp * 1000)
  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)

  if (diffInSeconds < 60) return 'Just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`

  return date.toLocaleDateString('en-SG', { month: 'short', day: 'numeric', year: 'numeric' })
}

function toggleReplyInput() {
  showReplyInput.value = !showReplyInput.value

  if (showReplyInput.value) {
    nextTick(() => {
      replyInputRef.value?.focus()
    })
  } else {
    replyText.value = ''
    mentionedUserIds.value = []
    showMentionDropdown.value = false
  }
}

function cancelReply() {
  showReplyInput.value = false
  replyText.value = ''
  mentionedUserIds.value = []
  showMentionDropdown.value = false
}

function handleReplyInput(event) {
  const textarea = event.target
  const text = textarea.value
  const position = textarea.selectionStart

  cursorPosition.value = position

  // Calculate dropdown position
  if (replyInputRef.value) {
    const textareaRect = replyInputRef.value.getBoundingClientRect()
    const parentRect = replyInputRef.value.parentElement.getBoundingClientRect()
    replyDropdownTop.value = `${textareaRect.bottom - parentRect.top + 8}px`
  }

  // Check for @ mention trigger
  const textBeforeCursor = text.substring(0, position)
  const atIndex = textBeforeCursor.lastIndexOf('@')

  if (atIndex !== -1 && filteredCollaboratorsForReply.value.length > 0) {
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
  const textarea = replyInputRef.value
  const text = textarea.value
  const textBeforeCursor = text.substring(0, cursorPosition.value)
  const atIndex = textBeforeCursor.lastIndexOf('@')

  if (atIndex !== -1) {
    // Replace @query with @DisplayName
    const beforeAt = text.substring(0, atIndex)
    const afterCursor = text.substring(cursorPosition.value)

    replyText.value = `${beforeAt}@${user.displayName} ${afterCursor}`

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
    replyText.value = replyText.value.replace(mentionPattern, '')
  }

  toast.info(`Removed mention: ${getAuthorName(userId)}`)
}

async function submitReply() {
  if (!canSubmitReply.value) return

  isSubmittingReply.value = true

  try {
    const payload = {
      type: props.parentType,
      parentId: props.parentId,
      threadIndex: props.threadIndex,
      comment: replyText.value.trim(),
      userId: props.currentUserId,
      creationDate: Math.floor(Date.now() / 1000),
      mention: mentionedUserIds.value.length > 0 ? mentionedUserIds.value : []
    }

    const response = await axios.put(
      `${import.meta.env.VITE_BACKEND_API}comments`,
      payload
    )

    if (response.data.commentThread) {
      emit('reply-added', {
        thread: response.data.commentThread,
        threadIndex: props.threadIndex
      })

      // Clear inputs
      replyText.value = ''
      mentionedUserIds.value = []
      showReplyInput.value = false

      toast.success('Reply posted successfully')
    }
  } catch (error) {
    console.error('Error posting reply:', error)
    toast.error(error.response?.data?.error || 'Failed to post reply')
  } finally {
    isSubmittingReply.value = false
  }
}

function confirmResolveThread() {
  showResolveConfirm.value = true
}

async function resolveThread() {
  isResolving.value = true

  try {
    const payload = {
      type: props.parentType,
      parentId: props.parentId,
      threadIndex: props.threadIndex,
      active: !props.thread.active
    }

    const response = await axios.put(
      `${import.meta.env.VITE_BACKEND_API}comments/archive`,
      payload
    )

    if (response.data.commentThread) {
      emit('thread-resolved', {
        thread: response.data.commentThread,
        threadIndex: props.threadIndex
      })

      showResolveConfirm.value = false
      toast.success(props.thread.active ? 'Thread marked as resolved' : 'Thread reopened')
    }
  } catch (error) {
    console.error('Error resolving thread:', error)
    toast.error(error.response?.data?.error || 'Failed to update thread status')
  } finally {
    isResolving.value = false
  }
}
</script>

<style scoped>
/* Scrollbar styling for mention dropdown */
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f9fafb;
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #d1d5db, #9ca3af);
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to bottom, #9ca3af, #6b7280);
}

/* Responsive */
@media (max-width: 640px) {
  .px-6 {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .ml-\[52px\] {
    margin-left: 2.5rem;
  }

  .gap-2\.5 {
    flex-direction: column;
    width: 100%;
  }

  .gap-2\.5 button {
    width: 100%;
    justify-content: center;
  }
}
</style>
