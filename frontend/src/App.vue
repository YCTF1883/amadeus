<script setup>
import { computed, onMounted, ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import CharacterStage from './components/CharacterStage.vue'
import ConversationDock from './components/ConversationDock.vue'
import KnowledgeWorkspace from './components/KnowledgeWorkspace.vue'
import MatrixBackdrop from './components/MatrixBackdrop.vue'
import SystemInspector from './components/SystemInspector.vue'
import { useAmadeusTelemetry } from './composables/useAmadeusTelemetry.js'
import { useAudioPlayback } from './composables/useAudioPlayback.js'
import { useCharacterController } from './composables/useCharacterController.js'
import { useChat } from './composables/useChat.js'
import { useKnowledge } from './composables/useKnowledge.js'
import { useVoice } from './composables/useVoice.js'
import { useVoiceInput } from './composables/useVoiceInput.js'

const {
  messages,
  isLoading,
  runningToolCount,
  chatError,
  worldlineEnabled,
  worldlineMode,
  sendMessage,
  clearHistory,
} = useChat()

const { isListening, startRecording, stopRecording } = useVoiceInput()
const {
  files,
  isUploading,
  isRagLoading,
  ragQuestion,
  ragAnswer,
  ragSources,
  knowledgeError,
  knowledgeMessage,
  loadFiles,
  uploadFile,
  deleteFile,
  askRag,
} = useKnowledge()

const playback = useAudioPlayback()
const voice = useVoice(playback)
const telemetry = useAmadeusTelemetry({ messages, files })
const characterError = ref('')

const hasError = computed(() => Boolean(
  chatError.value || knowledgeError.value || playback.audioError.value || characterError.value,
))

const character = useCharacterController({
  hasError,
  isSpeaking: playback.isSpeaking,
  isListening,
  runningToolCount,
  isLoading,
  audioLevel: playback.audioLevel,
})

const inspectorStats = computed(() => ({
  messageCount: telemetry.messageCount.value,
  toolCount: telemetry.toolCount.value,
  activeToolCount: runningToolCount.value,
  fileCount: telemetry.fileCount.value,
  chunkCount: telemetry.chunkCount.value,
  sysTime: telemetry.sysTime.value,
  renderer: 'STATIC',
}))

const conversationError = computed(() => chatError.value || playback.audioError.value || characterError.value)
const connectionLabel = computed(() => hasError.value ? 'DEGRADED' : 'ONLINE')

function onTextToken(token) {
  if (token.trim().startsWith('{"type"')) return
  const lastMessage = messages.value.at(-1)
  if (lastMessage?.role === 'assistant') lastMessage.content += token
}

function onAudioData(base64) {
  playback.playBase64Wav(base64).catch(() => {})
}

function onStreamEnd() {
  isLoading.value = false
}

function onSTT(text) {
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: text,
    timestamp: new Date(),
  })
  messages.value.push({
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    toolCalls: [],
    timestamp: new Date(),
  })
  isLoading.value = true
}

async function toggleMic() {
  characterError.value = ''
  if (isListening.value) {
    stopRecording()
    return
  }
  try {
    await startRecording(onTextToken, onAudioData, onStreamEnd, onSTT)
  } catch (error) {
    characterError.value = `麦克风不可用：${error.message}`
  }
}

function handleNewConversation() {
  playback.stop()
  playback.audioError.value = ''
  characterError.value = ''
  clearHistory()
}

function confirmDeleteFile(file) {
  if (!file) return
  if (window.confirm(`确定从知识库删除「${file.filename}」吗？`)) {
    deleteFile(file.file_id)
  }
}

function handleCharacterReady() {
  characterError.value = ''
}

function handleCharacterError() {
  characterError.value = '角色图像加载失败，可点击重试'
}

onMounted(loadFiles)
</script>

<template>
  <div class="amadeus-app">
    <MatrixBackdrop />
    <div class="crt-overlay" aria-hidden="true"></div>

    <AppHeader
      class="workbench-header"
      :world-line="telemetry.worldLine.value"
      :is-listening="isListening"
      :connection-label="connectionLabel"
      @new-conversation="handleNewConversation"
      @toggle-mic="toggleMic"
    />

    <main class="workbench-grid">
      <KnowledgeWorkspace
        class="workbench-knowledge"
        :files="files"
        :is-uploading="isUploading"
        :is-rag-loading="isRagLoading"
        :rag-question="ragQuestion"
        :rag-answer="ragAnswer"
        :rag-sources="ragSources"
        :error="knowledgeError"
        :message="knowledgeMessage"
        @refresh="loadFiles"
        @upload="uploadFile"
        @delete="confirmDeleteFile"
        @ask="askRag()"
        @update:rag-question="value => { ragQuestion = value }"
      />

      <CharacterStage
        class="workbench-character"
        renderer="static"
        model-id="makise-kurisu"
        image-src="/kurisu.png"
        :state="character.characterState.value"
        :audio-level="character.audioLevel.value"
        @ready="handleCharacterReady"
        @error="handleCharacterError"
      />

      <SystemInspector
        class="workbench-inspector"
        :stats="inspectorStats"
        :character-state="character.characterState.value"
        :is-speaking="playback.isSpeaking.value"
        :audio-level="character.audioLevel.value"
      />

      <ConversationDock
        class="workbench-conversation"
        :messages="messages"
        :is-loading="isLoading"
        :is-speaking="playback.isSpeaking.value"
        :is-listening="isListening"
        :worldline-enabled="worldlineEnabled"
        :worldline-mode="worldlineMode"
        :error="conversationError"
        @send="sendMessage"
        @quick-send="sendMessage"
        @speak="voice.speak"
        @toggle-mic="toggleMic"
        @update:worldline-enabled="value => { worldlineEnabled = value }"
        @update:worldline-mode="value => { worldlineMode = value }"
      />
    </main>
  </div>
</template>
