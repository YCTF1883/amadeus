<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { useChat } from './composables/useChat.js'
import { useVoice } from './composables/useVoice.js'
import { useVoiceInput } from './composables/useVoiceInput.js'

const { messages, isLoading, threadId, sendMessage, clearHistory } = useChat()
const { isListening, recognizedText, startRecording, stopRecording } = useVoiceInput()
const voiceReply = ref('')
const voiceQueue = ref([])

function onTextToken(token) {
  // 跳过 meta JSON token
  if (token.trim().startsWith('{"type"')) return
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg && lastMsg.role === 'assistant') {
    lastMsg.content += token
  }
}
function onAudioData(b64) {
  const blob = new Blob(
    [Uint8Array.from(atob(b64), c => c.charCodeAt(0))],
    { type: 'audio/wav' }
  )
  const url = URL.createObjectURL(blob)
  const audio = new Audio(url)
  audio.onended = () => URL.revokeObjectURL(url)
  audio.play()
}

function onStreamEnd() {
  isLoading.value = false
}

function onSTT(text) {
  // STT 识别结果回来后，把用户消息 + 空助理气泡推入聊天
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: text,
    timestamp: new Date()
  })
  messages.value.push({
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    timestamp: new Date()
  })
  isLoading.value = true
}

async function toggleMic() {
  if (isListening.value) {
    stopRecording()
    voiceReply.value = ''
  } else {
    voiceReply.value = ''
    await startRecording(onTextToken, onAudioData, onStreamEnd, onSTT)
  }
}
const { isSpeaking, speak } = useVoice()
const inputText = ref('')
const msgArea = ref(null)
const inputRef = ref(null)

// 自动滚到底部
watch(
  () => messages.value.length,
  async () => { await nextTick(); scrollToBottom() }
)
// 流式更新时也滚动
watch(
  () => {
    const last = messages.value[messages.value.length - 1]
    return last ? last.content : ''
  },
  () => { scrollToBottom() }
)

// 回复完成后自动聚焦输入框
watch(isLoading, (val) => {
  if (!val) {
    nextTick(() => { inputRef.value?.focus() })
  }
})

function scrollToBottom() {
  if (msgArea.value) {
    msgArea.value.scrollTop = msgArea.value.scrollHeight
  }
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text) return
  sendMessage(text)
  inputText.value = ''
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 快捷指令
const quickCommands = [
  { label: '时间', text: '现在几点了？' },
  { label: '计算', text: '帮我算一下 ' },
  { label: '提醒', text: '提醒我 ' },
  { label: '搜索', text: '帮我在网上查一下 ' },
]
function quickSend(cmd) {
  sendMessage(cmd.text)
}

// ============================================
// 代码雨（Matrix Rain）
// ============================================
onMounted(() => {
  const canvas = document.getElementById('matrixCanvas')
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  function resize() {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  resize()
  window.addEventListener('resize', resize)

  // 字符集：片假名 + 数字 + 世界线相关符号
  const chars = 'ｦｧｨｩｪｫｬｭｮｯｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789ΩΣαβγδελμσφψΔΛΓΣ%±→←↑↓×÷'
  const fontSize = 14
  const columns = Math.floor(canvas.width / fontSize)
  const drops = new Array(columns).fill(0)
  // 每列一个速度级别：0=快(亮白) 1=中(亮绿) 2=慢(暗绿)
  const speeds = new Array(columns).fill(0).map(() => Math.floor(Math.random() * 3))

  function draw() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    ctx.font = fontSize + 'px "Courier New", monospace'

    for (let i = 0; i < drops.length; i++) {
      const char = chars[Math.floor(Math.random() * chars.length)]
      const x = i * fontSize
      const y = drops[i] * fontSize

      // 三色层次：首字符亮白 > 亮绿 > 暗绿
      const head = Math.random() > 0.97
      if (head) {
        ctx.fillStyle = '#ffffff'
        ctx.shadowColor = '#ffffff'
        ctx.shadowBlur = 4
      } else if (speeds[i] === 0) {
        ctx.fillStyle = '#66ff88'
        ctx.shadowColor = 'transparent'
        ctx.shadowBlur = 0
      } else if (speeds[i] === 1) {
        ctx.fillStyle = '#00ff41'
        ctx.shadowColor = 'transparent'
        ctx.shadowBlur = 0
      } else {
        ctx.fillStyle = '#008822'
        ctx.shadowColor = 'transparent'
        ctx.shadowBlur = 0
      }

      ctx.fillText(char, x, y)

      // 不同速度列不同下落速度
      const velocity = speeds[i] === 0 ? 1.5 : speeds[i] === 1 ? 1 : 0.6
      drops[i] += velocity

      // 重置雨滴
      if (y > canvas.height && Math.random() > 0.975) {
        drops[i] = 0
        speeds[i] = Math.floor(Math.random() * 3)
      }
    }
    ctx.shadowBlur = 0
  }

  setInterval(draw, 50)
})

// ============================================
// 世界线变动率
// ============================================
// 基础值 1.048596，末位随机跳动 ±0.000005
const baseValue = 1.048596
let rawJitter = Math.random() * 0.00001 - 0.000005
const worldLine = ref((baseValue + rawJitter).toFixed(6))

setInterval(() => {
  // 随机漂移，偶尔大幅跳跃（模拟探测仪不稳定）
  const jump = Math.random() > 0.97 ? (Math.random() - 0.5) * 0.002 : 0
  rawJitter += (Math.random() - 0.5) * 0.000002 + jump
  rawJitter = Math.max(-0.00005, Math.min(0.00005, rawJitter))
  worldLine.value = (baseValue + rawJitter).toFixed(6)
}, 80)
</script>

<template>
  <div class="app-root">
    <!-- 代码雨背景 -->
    <canvas class="matrix-rain" id="matrixCanvas"></canvas>

    <!-- 主布局 -->
    <div class="main-layout">
      <!-- 标题栏 -->
      <header class="title-bar">
        <span class="title-text">AMADEUS</span>
        <span class="title-sub">— Makise Kurisu —</span>
        <span class="world-line">WL {{ worldLine }}%</span>
        <button class="btn-clear" @click="clearHistory">新对话</button>
        <button class="btn-mic" :class="{ active: isListening }" @click="toggleMic">
  {{ isListening ? '🔴 录音中...' : '🎤' }}
</button>
      </header>

      <!-- 角色区域 -->
      <div class="character-area">
        <img class="kurisu-img" src="/kurisu.png" alt="Makise Kurisu" />
      </div>

      <!-- Galgame 式对话框 -->
      <div class="dialog-box">
        <!-- 消息区域（可滚动） -->
        <div class="message-area" ref="msgArea">
          <div v-if="messages.length === 0" class="empty-hint">
            ▸ 世界线变动率探测仪待机中...
          </div>
          <div
            v-for="(msg, index) in messages"
            :key="msg.id"
            :class="['message-bubble', msg.role]"
          >
            <span class="msg-label">{{ msg.role === 'user' ? '小陆' : 'Amadeus' }}</span>
            <span class="msg-content">
              <template v-if="msg.role === 'assistant' && isLoading && !msg.content">
                <span class="thinking-text">▮ 思考中...</span>
              </template>
              <template v-else>
                {{ msg.content }}<span v-if="msg.role === 'assistant' && isLoading && msg.content && index === messages.length - 1" class="cursor-blink">█</span>
              </template>
              <button
                v-if="msg.role === 'assistant' && msg.content && !isLoading"
                class="btn-speak"
                :disabled="isSpeaking"
                @click="speak(msg.content)"
                :title="isSpeaking ? '播放中...' : '朗读'"
              >🔊</button>
            </span>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="input-line">
          <span class="prompt">▸</span>
          <input
            ref="inputRef"
            v-model="inputText"
            class="chat-input"
            type="text"
            placeholder="输入消息..."
            :disabled="isLoading"
            @keydown="handleKeydown"
          />
          <button class="btn-send" :disabled="isLoading" @click="handleSend">
            {{ isLoading ? '...' : '发送' }}
          </button>
        </div>

        <!-- 快捷指令栏 -->
        <div class="quick-bar">
          <button
            v-for="cmd in quickCommands"
            :key="cmd.label"
            class="btn-quick"
            :disabled="isLoading"
            @click="quickSend(cmd)"
          >{{ cmd.label }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ========================================
   Galgame 终端风格 — Steins;Gate
   ======================================== */

.app-root {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #0a0a0a;
  font-family: 'Courier New', 'Microsoft YaHei', monospace;
  color: #00ff41;
}

/* ---- 代码雨 ---- */
.matrix-rain {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 0;
  opacity: 0.15;
}

/* ---- 主布局 ---- */
.main-layout {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  padding: 12px 20px 20px;
  box-sizing: border-box;
}

/* ---- 标题栏 ---- */
.title-bar {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 8px;
}
.title-text {
  font-size: 28px;
  font-weight: bold;
  letter-spacing: 6px;
  color: #e94560;
  text-shadow: 0 0 12px #e94560;
}
.title-sub {
  font-size: 14px;
  color: #888;
}
.btn-clear {
  margin-left: auto;
  background: transparent;
  border: 1px solid #333;
  color: #888;
  padding: 4px 12px;
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
}
.btn-clear:hover {
  border-color: #00ff41;
  color: #00ff41;
}

/* ---- 角色区 ---- */
.character-area {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  min-height: 0;
}
.kurisu-img {
  height: 90%;
  max-height: 480px;
  object-fit: contain;
  filter: drop-shadow(0 0 20px rgba(0, 255, 65, 0.25));
  animation: kurisu-breathe 4s ease-in-out infinite;
}
@keyframes kurisu-breathe {
  0%, 100% { filter: drop-shadow(0 0 20px rgba(0, 255, 65, 0.25)); }
  50% { filter: drop-shadow(0 0 35px rgba(0, 255, 65, 0.45)); }
}

/* ---- 世界线变动率 ---- */
.world-line {
  font-size: 13px;
  color: #00ff41;
  letter-spacing: 1px;
  margin-left: 12px;
  font-family: 'Courier New', monospace;
}

/* ---- 对话框 ---- */
.dialog-box {
  width: 100%;
  max-width: 850px;
  background: rgba(0, 0, 0, 0.75);
  border: 1px solid #00ff41;
  border-radius: 6px;
  box-shadow: 0 0 10px rgba(0, 255, 65, 0.1), inset 0 0 10px rgba(0, 255, 65, 0.03);
  display: flex;
  flex-direction: column;
  height: 280px;
}

/* ---- 消息区 ---- */
.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.empty-hint {
  color: #00ff4166;
  text-align: center;
  margin: auto;
  font-size: 13px;
}

/* ---- 消息气泡 ---- */
.message-bubble {
  max-width: 85%;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  animation: msg-fade-in 0.3s ease-out;
}
@keyframes msg-fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.message-bubble.user {
  align-self: flex-end;
  background: rgba(0, 204, 255, 0.1);
  border: 1px solid #00ccff44;
  color: #00ccff;
}
.message-bubble.assistant {
  align-self: flex-start;
  background: rgba(0, 255, 65, 0.05);
  border: 1px solid #00ff4144;
  color: #00ff41;
}
.msg-label {
  display: block;
  font-size: 11px;
  margin-bottom: 2px;
  opacity: 0.7;
}
.msg-content {
  white-space: pre-wrap;
}

/* ---- 思考中动画 ---- */
.thinking-text {
  animation: pulse 1.5s ease-in-out infinite;
  color: #00ff4188;
}
@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

/* ---- 打字光标闪烁 ---- */
.cursor-blink {
  animation: blink 0.6s step-end infinite;
  color: #00ff41;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ---- 输入行 ---- */
.input-line {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-top: 1px solid #00ff4122;
}
.prompt {
  color: #00ff41;
  font-size: 16px;
}
.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #00ff41;
  font-family: inherit;
  font-size: 14px;
  caret-color: #00ff41;
}
.chat-input::placeholder {
  color: #00ff4133;
}
.btn-send {
  background: transparent;
  border: 1px solid #00ff41;
  color: #00ff41;
  padding: 4px 16px;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  border-radius: 3px;
}
.btn-send:hover {
  background: #00ff4111;
}
.btn-send:disabled {
  border-color: #333;
  color: #333;
  cursor: not-allowed;
}

/* ---- 快捷指令栏 ---- */
.quick-bar {
  display: flex;
  gap: 6px;
  padding: 6px 16px;
  border-top: 1px solid #00ff4111;
}
.btn-quick {
  background: rgba(0, 255, 65, 0.04);
  border: 1px solid #00ff4122;
  color: #00ff4188;
  padding: 3px 10px;
  cursor: pointer;
  font-family: inherit;
  font-size: 11px;
  border-radius: 3px;
  transition: all 0.15s;
}
.btn-quick:hover {
  background: rgba(0, 255, 65, 0.1);
  border-color: #00ff4188;
  color: #00ff41;
}
.btn-quick:disabled {
  display: none;
}

/* ---- 语音按钮 ---- */
.btn-speak {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.5;
  transition: opacity 0.15s;
  padding: 0 4px;
  vertical-align: middle;
}
.btn-speak:hover {
  opacity: 1;
}
.btn-speak:disabled {
  opacity: 0.2;
  cursor: not-allowed;
}

/* ---- 滚动条 ---- */
.message-area::-webkit-scrollbar {
  width: 4px;
}
.message-area::-webkit-scrollbar-track {
  background: transparent;
}
.message-area::-webkit-scrollbar-thumb {
  background: #00ff4133;
  border-radius: 2px;
}

.btn-mic {
  background: transparent;
  border: 1px solid #333;
  color: #888;
  padding: 4px 12px;
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  margin-right: 8px;
}
.btn-mic:hover {
  border-color: #00ff41;
  color: #00ff41;
}
.btn-mic.active {
  border-color: #e94560;
  color: #e94560;
  animation: pulse 1s ease-in-out infinite;
}
</style>
