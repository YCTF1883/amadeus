import { computed, ref, watch } from 'vue'
import { countRunningTools } from '../domain/characterState.js'

export function useChat() {
  // ============================================
  // 状态
  // ============================================
  const messages = ref([])
  const isLoading = ref(false)
  const chatError = ref('')
  const runningToolCount = computed(() => countRunningTools(messages.value))
  const worldlineEnabled = ref(localStorage.getItem('amadeus_worldline_enabled') === 'true')
  const worldlineMode = ref(localStorage.getItem('amadeus_worldline_mode') || 'observe')

  // 从 localStorage 读取上次的 thread_id，没有就生成新的
  const threadId = ref(
    localStorage.getItem('amadeus_thread_id') ||
    'session_' + crypto.randomUUID().slice(0, 8)
  )

  // ============================================
  // 工具调用处理（内部）
  // ============================================
  function handleToolStart(event) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (!lastMsg || lastMsg.role !== 'assistant') return
    // 替换整个对象触发 Vue 响应式
    const idx = messages.value.length - 1
    const updated = { ...messages.value[idx] }
    if (!updated.toolCalls) updated.toolCalls = []
    updated.toolCalls.push({
      callId: event.tool_name + '_' + Date.now(),
      name: event.tool_name,
      status: 'running',
      input: event.tool_input,
      output: null,
      error: null,
    })
    messages.value[idx] = updated
  }

  function handleToolEnd(event) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (!lastMsg || lastMsg.role !== 'assistant' || !lastMsg.toolCalls) return
    const idx = messages.value.length - 1
    const updated = { ...messages.value[idx] }
    const tc = updated.toolCalls.find(t => t.name === event.tool_name && t.status === 'running')
    if (tc) {
      if (event.type === 'tool_error') {
        tc.status = 'error'
        tc.error = event.error
      } else {
        tc.status = 'done'
        tc.output = event.tool_output
      }
    }
    messages.value[idx] = updated
  }

  // ============================================
  // 发送消息（SSE 流式）
  // ============================================
  async function sendMessage(text) {
    if (!text.trim()) return
    if (isLoading.value) return

    chatError.value = ''
    // 1. 用户消息加入列表
    messages.value.push({
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date()
    })

    // 2. 占位：给 assistant 预留空消息（token 逐个往里填）
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      toolCalls: [],
      timestamp: new Date()
    })

    isLoading.value = true

    try {
      // 3. 发 POST 请求 → SSE 流
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          thread_id: threadId.value,
          worldline_enabled: worldlineEnabled.value,
          worldline_mode: worldlineMode.value,
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      // 4. 循环读 SSE 数据
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        // 5. 逐行处理
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          if (line === '') continue

          const data = line.slice(6) // 去掉 "data: " 前缀

          if (data === '[DONE]') {
            isLoading.value = false
            return
          }

          // JSON 事件：元信息 or 工具调用
          if (data.startsWith('{')) {
            try {
              const event = JSON.parse(data)
              if (event.type === 'meta' && event.thread_id) {
                threadId.value = event.thread_id
                continue
              }
              if (event.type === 'text') {
                const lastMsg = messages.value[messages.value.length - 1]
                if (lastMsg && lastMsg.role === 'assistant') {
                  lastMsg.content += event.content || ''
                }
                continue
              }
              if (event.type === 'tool_start') {
                handleToolStart(event)
                continue
              }
              if (event.type === 'tool_end' || event.type === 'tool_error') {
                handleToolEnd(event)
                continue
              }
            } catch {}
            continue
          }

          // 普通文本 token → 追加到最后一条 assistant 消息
          const lastMsg = messages.value[messages.value.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.content += data
          }
        }
      }
    } catch (err) {
      console.error('发送失败:', err)
      chatError.value = `发送失败：${err.message}`
    } finally {
      isLoading.value = false
    }
  }

  // ============================================
  // 清空对话
  // ============================================
  function clearHistory() {
    messages.value = []
    chatError.value = ''
    threadId.value = 'session_' + crypto.randomUUID().slice(0, 8)
  }

  // ============================================
  // thread_id 变化时自动存 localStorage
  // ============================================
  watch(threadId, (newId) => {
    localStorage.setItem('amadeus_thread_id', newId)
  })
  watch(worldlineEnabled, (enabled) => {
    localStorage.setItem('amadeus_worldline_enabled', String(enabled))
  })
  watch(worldlineMode, (mode) => {
    localStorage.setItem('amadeus_worldline_mode', mode)
  })

  return {
    messages,
    isLoading,
    runningToolCount,
    chatError,
    threadId,
    worldlineEnabled,
    worldlineMode,
    sendMessage,
    clearHistory,
  }
}
