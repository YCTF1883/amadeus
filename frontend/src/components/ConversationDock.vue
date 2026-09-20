<script setup>
import { nextTick, ref, watch } from 'vue'
import { normalizeAssistantText } from '../domain/messageFormatting.js'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  isLoading: { type: Boolean, default: false },
  isSpeaking: { type: Boolean, default: false },
  isListening: { type: Boolean, default: false },
  worldlineEnabled: { type: Boolean, default: false },
  worldlineMode: { type: String, default: 'observe' },
  error: { type: String, default: '' },
})

const emit = defineEmits([
  'send',
  'quick-send',
  'speak',
  'toggle-mic',
  'update:worldline-enabled',
  'update:worldline-mode',
])
const inputText = ref('')
const messageArea = ref(null)

const quickCommands = [
  { label: '时间', text: '现在几点了？' },
  { label: '计算', text: '帮我算一下 ' },
  { label: '提醒', text: '提醒我 ' },
  { label: '搜索', text: '帮我在网上查一下 ' },
]

function submit() {
  const value = inputText.value.trim()
  if (!value || props.isLoading) return
  emit('send', value)
  inputText.value = ''
}

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submit()
  }
}

function quickSend(command) {
  if (props.isLoading) return
  emit('quick-send', command.text)
}

function toolIcon(name) {
  const map = {
    get_current_time: '◷',
    calculate: '∑',
    create_reminder: '⌁',
    send_email: '@',
    search_knowledge_base: '▤',
    add_to_knowledge_base: '+',
    delete_from_knowledge_base: '−',
    search_web: '◎',
    fetch_text_from_url: '↗',
  }
  return map[name] || '◇'
}

function toolLabel(name) {
  const map = {
    get_current_time: '获取时间',
    calculate: '计算',
    create_reminder: '创建提醒',
    send_email: '发送邮件',
    search_knowledge_base: '搜索知识库',
    add_to_knowledge_base: '存入知识库',
    delete_from_knowledge_base: '删除知识',
    search_web: '网页搜索',
    fetch_text_from_url: '抓取网页',
  }
  return map[name] || name
}

function truncateOutput(output) {
  if (!output) return ''
  const value = typeof output === 'string' ? output : JSON.stringify(output)
  return value.length > 160 ? `${value.slice(0, 160)}…` : value
}

function displayMessage(message) {
  return message.role === 'assistant'
    ? normalizeAssistantText(message.content)
    : message.content
}

async function scrollToLatest() {
  await nextTick()
  if (messageArea.value) messageArea.value.scrollTop = messageArea.value.scrollHeight
}

watch(() => props.messages.length, scrollToLatest)
watch(() => props.messages.at(-1)?.content, scrollToLatest)
</script>

<template>
  <section class="conversation-dock" aria-label="对话控制台">
    <div ref="messageArea" class="message-area" aria-live="polite">
      <div v-if="messages.length === 0" class="empty-hint">
        <span>AMADEUS CHANNEL / READY</span>
        <strong>世界线变动率探测仪待机中</strong>
      </div>

      <article
        v-for="(message, index) in messages"
        :key="message.id"
        :class="['message', message.role]"
      >
        <header>
          <span>{{ message.role === 'user' ? 'YOU' : 'AMADEUS' }}</span>
          <time>{{ message.timestamp ? new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false }) : '' }}</time>
        </header>

        <div class="message-body">
          <span
            v-if="message.role === 'assistant' && isLoading && !message.content && (!message.toolCalls || message.toolCalls.length === 0)"
            class="thinking"
            aria-label="思考中"
          ><i></i><i></i><i></i></span>
          <template v-else>
            <p>{{ displayMessage(message) }}<span v-if="message.role === 'assistant' && isLoading && message.content && index === messages.length - 1" class="cursor">▋</span></p>
          </template>
          <button
            v-if="message.role === 'assistant' && message.content && !isLoading"
            class="speak-button"
            type="button"
            :disabled="isSpeaking"
            :title="isSpeaking ? '播放中' : '朗读此消息'"
            aria-label="朗读此消息"
            @click="$emit('speak', message.content)"
          >))</button>
        </div>

        <div v-if="message.role === 'assistant' && message.toolCalls?.length" class="tool-calls">
          <article v-for="tool in message.toolCalls" :key="tool.callId" :class="['tool-row', tool.status]">
            <div class="tool-heading">
              <span class="tool-icon" aria-hidden="true">{{ toolIcon(tool.name) }}</span>
              <strong>{{ toolLabel(tool.name) }}</strong>
              <span class="tool-status">{{ tool.status === 'running' ? '执行中' : tool.status === 'done' ? '完成' : '异常' }}</span>
            </div>
            <p v-if="tool.status === 'running'">{{ tool.input }}</p>
            <p v-else-if="tool.status === 'done'">{{ truncateOutput(tool.output) }}</p>
            <p v-else class="tool-error">{{ tool.error }}</p>
          </article>
        </div>
      </article>
    </div>

    <p v-if="error" class="dock-error" role="alert">{{ error }}</p>

    <div class="worldline-controls">
      <button
        class="worldline-switch"
        :class="{ active: worldlineEnabled }"
        type="button"
        role="switch"
        :aria-checked="worldlineEnabled"
        :disabled="isLoading"
        @click="emit('update:worldline-enabled', !worldlineEnabled)"
      >
        <span class="switch-track" aria-hidden="true"><i></i></span>
        <span>世界线推演</span>
      </button>

      <div v-if="worldlineEnabled" class="mode-segments" aria-label="世界线推演模式">
        <button
          type="button"
          :class="{ active: worldlineMode === 'observe' }"
          :disabled="isLoading"
          @click="emit('update:worldline-mode', 'observe')"
        >观测模式</button>
        <button
          type="button"
          :class="{ active: worldlineMode === 'immersive' }"
          :disabled="isLoading"
          @click="emit('update:worldline-mode', 'immersive')"
        >沉浸模式</button>
      </div>
    </div>

    <div class="composer">
      <span class="prompt" aria-hidden="true">›</span>
      <textarea
        v-model="inputText"
        rows="1"
        placeholder="向 Amadeus 发送消息…"
        :disabled="isLoading"
        @keydown="handleKeydown"
      ></textarea>
      <button
        class="mic-button"
        :class="{ active: isListening }"
        type="button"
        :disabled="isLoading || isSpeaking"
        :aria-label="isListening ? '停止语音输入' : '开始语音输入'"
        :title="isListening ? '停止语音输入' : '开始语音输入'"
        @click="$emit('toggle-mic')"
      ><span aria-hidden="true"></span></button>
      <button class="send-button" type="button" :disabled="isLoading || !inputText.trim()" @click="submit">
        {{ isLoading ? '响应中' : '发送' }}
      </button>
    </div>

    <div class="quick-bar" aria-label="快捷指令">
      <button
        v-for="command in quickCommands"
        :key="command.label"
        type="button"
        :disabled="isLoading"
        @click="quickSend(command)"
      >{{ command.label }}</button>
    </div>
  </section>
</template>

<style scoped>
.conversation-dock { display: grid; grid-template-rows: minmax(0, 1fr) auto auto auto auto; min-width: 0; height: clamp(280px, 38vh, 460px); border-top: 1px solid rgba(71, 255, 142, 0.18); background: rgba(3, 8, 9, 0.93); color: #b9cec6; }
.message-area { min-width: 0; min-height: 0; overflow-y: auto; padding: 13px 18px; scrollbar-width: thin; scrollbar-color: #28523e transparent; }
.empty-hint { display: flex; height: 100%; min-height: 70px; flex-direction: column; align-items: center; justify-content: center; gap: 7px; color: #445950; text-align: center; }
.empty-hint span { font-size: 9px; }
.empty-hint strong { color: #658078; font-size: 11px; font-weight: 400; }
.message { min-width: 0; max-width: 880px; margin: 0 auto 12px; }
.message header { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 5px; color: #587067; font-size: 8px; }
.message.assistant header span { color: #e85b81; }
.message.user header span { color: #56b9dd; }
.message-body { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: start; gap: 9px; }
.message-body p { min-width: 0; margin: 0; color: #bfd1ca; font-size: 12px; line-height: 1.65; white-space: pre-wrap; overflow-wrap: anywhere; }
.user .message-body p { color: #9fc7d6; }
.cursor { color: #4bec8b; animation: blink 900ms steps(1) infinite; }
.speak-button { width: 26px; height: 24px; border: 0; background: transparent; color: #547068; font-size: 9px; cursor: pointer; }
.speak-button:hover { color: #4bec8b; }
.speak-button:disabled { opacity: 0.35; }
.thinking { display: flex; gap: 4px; padding: 7px 0; }
.thinking i { width: 4px; height: 10px; background: #3fe681; animation: meter 850ms ease-in-out infinite; }
.thinking i:nth-child(2) { animation-delay: 130ms; }
.thinking i:nth-child(3) { animation-delay: 260ms; }
.tool-calls { display: grid; gap: 5px; margin-top: 8px; }
.tool-row { min-width: 0; padding: 7px 9px; border-left: 2px solid #3c7056; background: rgba(54, 128, 85, 0.06); }
.tool-row.running { border-color: #d6a24c; }
.tool-row.error { border-color: #f04f7a; }
.tool-heading { display: grid; grid-template-columns: 18px minmax(0, 1fr) auto; align-items: center; gap: 5px; }
.tool-icon { color: #70d998; text-align: center; }
.tool-heading strong { min-width: 0; color: #8fb9a3; font-size: 9px; font-weight: 500; overflow-wrap: anywhere; }
.tool-status { color: #60796f; font-size: 8px; }
.tool-row.running .tool-status { color: #d6a24c; }
.tool-row.error .tool-status, .tool-error { color: #f07c9c; }
.tool-row p { margin: 5px 0 0 23px; color: #61776e; font-size: 9px; line-height: 1.45; white-space: pre-wrap; overflow-wrap: anywhere; }
.dock-error { margin: 0; padding: 6px 18px; border-top: 1px solid rgba(240, 79, 122, 0.2); color: #ed7897; font-size: 10px; overflow-wrap: anywhere; }
.worldline-controls { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: 10px; padding: 7px 14px; border-top: 1px solid #172720; background: rgba(14, 24, 21, 0.78); }
.worldline-switch { display: inline-flex; align-items: center; gap: 7px; min-height: 28px; padding: 0; border: 0; background: transparent; color: #6f847c; font: inherit; font-size: 10px; cursor: pointer; }
.worldline-switch.active { color: #5dea95; }
.switch-track { position: relative; width: 28px; height: 14px; border: 1px solid #355247; border-radius: 8px; background: #09110f; transition: border-color 160ms ease, background 160ms ease; }
.switch-track i { position: absolute; top: 2px; left: 2px; width: 8px; height: 8px; border-radius: 50%; background: #657a72; transition: transform 160ms ease, background 160ms ease; }
.worldline-switch.active .switch-track { border-color: #36b96d; background: rgba(53, 195, 111, 0.12); }
.worldline-switch.active .switch-track i { transform: translateX(14px); background: #4cec8d; }
.mode-segments { display: grid; grid-template-columns: repeat(2, minmax(70px, 1fr)); min-width: 164px; border: 1px solid #2b4339; border-radius: 4px; overflow: hidden; }
.mode-segments button { min-height: 26px; padding: 0 9px; border: 0; border-right: 1px solid #2b4339; background: transparent; color: #647b72; font: inherit; font-size: 9px; cursor: pointer; }
.mode-segments button:last-child { border-right: 0; }
.mode-segments button.active { background: rgba(72, 233, 136, 0.1); color: #81e9aa; }
.composer { display: grid; grid-template-columns: auto minmax(0, 1fr) 34px auto; align-items: end; gap: 8px; padding: 9px 14px 7px; border-top: 1px solid #172720; }
.prompt { align-self: center; color: #43e584; font-size: 20px; }
.composer textarea { box-sizing: border-box; width: 100%; max-height: 86px; min-height: 34px; resize: none; border: 0; outline: 0; background: transparent; padding: 8px 0; color: #d0e1da; font: inherit; font-size: 12px; line-height: 1.5; }
.composer textarea::placeholder { color: #3e534b; }
.mic-button, .send-button { height: 34px; border: 1px solid #29453a; border-radius: 5px; background: #091310; color: #88a69a; cursor: pointer; font: inherit; }
.mic-button { display: grid; place-items: center; width: 34px; padding: 0; }
.mic-button span { position: relative; width: 7px; height: 12px; border: 2px solid currentColor; border-radius: 5px; }
.mic-button span::after { content: ''; position: absolute; left: -5px; bottom: -5px; width: 13px; height: 8px; border: 2px solid currentColor; border-top: 0; border-radius: 0 0 7px 7px; }
.mic-button.active { border-color: #f04f7a; color: #f04f7a; }
.send-button { min-width: 62px; padding: 0 13px; border-color: #34734f; color: #86dca7; }
button:disabled { opacity: 0.35; cursor: not-allowed; }
.quick-bar { display: flex; gap: 4px; padding: 0 14px 9px 37px; }
.quick-bar button { padding: 3px 9px; border: 0; border-right: 1px solid #24382f; background: transparent; color: #597268; font: inherit; font-size: 9px; cursor: pointer; }
.quick-bar button:hover { color: #61d991; }
@keyframes blink { 50% { opacity: 0; } }
@keyframes meter { 50% { transform: scaleY(0.45); opacity: 0.45; } }
@media (max-width: 600px) { .message-area { padding-inline: 12px; } .worldline-controls { align-items: stretch; flex-direction: column; } .mode-segments { width: 100%; } .composer { padding-inline: 10px; } .quick-bar { padding-left: 28px; } }
</style>
