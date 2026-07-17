import { ref } from 'vue'

export function useVoice() {
  const isSpeaking = ref(false)
  let ws = null
  let audioCtx = null

  function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) return ws

    // 根据当前页面协议自动选 ws:// 或 wss://
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws/voice`

    ws = new WebSocket(url)

    ws.onopen = () => console.log('🔊 语音通道已连接')
    ws.onclose = () => console.log('🔊 语音通道已断开')
    ws.onerror = (e) => console.error('语音通道错误:', e)

    return ws
  }

  async function speak(text) {
    if (!text.trim() || isSpeaking.value) return

    isSpeaking.value = true
    const socket = connect()

    // 等 WebSocket 连上再发
    if (socket.readyState !== WebSocket.OPEN) {
      await new Promise(resolve => {
        socket.onopen = resolve
      })
    }

    // 准备接收音频
    socket.onmessage = async (event) => {
      const blob = new Blob([event.data], { type: 'audio/wav' })
      const url = URL.createObjectURL(blob)

      const audio = new Audio(url)
      audio.onended = () => {
        URL.revokeObjectURL(url)
        isSpeaking.value = false
      }
      audio.onerror = () => {
        isSpeaking.value = false
      }
      await audio.play()
    }

    socket.send(text)
  }

  return { isSpeaking, speak }
}