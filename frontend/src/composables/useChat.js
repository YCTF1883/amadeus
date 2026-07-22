import { ref, watch } from 'vue'

export function useChat() {
  // ============================================
  // 状态
  // ============================================
  const messages = ref([])
  const isLoading = ref(false)

  // 从 localStorage 读取上次的 thread_id，没有就生成新的
  const threadId = ref(
    localStorage.getItem('amadeus_thread_id') ||
    'session_' + crypto.randomUUID().slice(0, 8)
  )

  // ============================================
  // 发送消息（SSE 流式）
  // ============================================
  async function sendMessage(text) {
    if (!text.trim()) return
    if (isLoading.value) return

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
          thread_id: threadId.value
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

          // 第一个 token 是 JSON 元信息（thread_id）
          if (data.startsWith('{')) {
            try {
              const meta = JSON.parse(data)
              if (meta.type === 'meta' && meta.thread_id) {
                threadId.value = meta.thread_id
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
    } finally {
      isLoading.value = false
    }
  }

  // ============================================
  // 清空对话
  // ============================================
  function clearHistory() {
    messages.value = []
    threadId.value = 'session_' + crypto.randomUUID().slice(0, 8)
  }

  // ============================================
  // thread_id 变化时自动存 localStorage
  // ============================================
  watch(threadId, (newId) => {
    localStorage.setItem('amadeus_thread_id', newId)
  })

  return { messages, isLoading, threadId, sendMessage, clearHistory }
}
