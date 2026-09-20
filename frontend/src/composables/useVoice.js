import { useAudioPlayback } from './useAudioPlayback.js'

export function useVoice(playback = useAudioPlayback()) {
  let ws = null

  function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) return ws

    // 根据当前页面协议自动选 ws:// 或 wss://
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws/voice`

    ws = new WebSocket(url)
    ws.binaryType = 'arraybuffer'

    ws.onopen = () => console.log('🔊 语音通道已连接')
    ws.onclose = () => console.log('🔊 语音通道已断开')
    ws.onerror = (e) => console.error('语音通道错误:', e)

    return ws
  }

  async function speak(text) {
    if (!text.trim() || playback.isSpeaking.value) return
    const socket = connect()

    // 等 WebSocket 连上再发
    if (socket.readyState !== WebSocket.OPEN) {
      await new Promise(resolve => {
        socket.onopen = resolve
      })
    }

    socket.onmessage = event => {
      playback.playBlob(new Blob([event.data], { type: 'audio/wav' })).catch(() => {})
    }

    socket.send(text)
  }

  return { speak }
}
