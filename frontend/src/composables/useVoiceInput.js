import { ref } from 'vue'

export function useVoiceInput() {
  const isListening = ref(false)
  const recognizedText = ref('')
  let ws = null
  let mediaRecorder = null
  let audioChunks = []

  function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) return ws
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${location.host}/ws/voice-chat`)
    return ws
  }

  async function startRecording(onTextToken, onAudioData, onStreamEnd, onSTT) {
    if (isListening.value) return

    // 请求麦克风权限
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
    audioChunks = []

    mediaRecorder.ondataavailable = (e) => {
      audioChunks.push(e.data)
    }

    mediaRecorder.onstop = async () => {
      // 停止所有音轨
      stream.getTracks().forEach(t => t.stop())

      if (audioChunks.length === 0) return

      // WebM → WAV 转换（后端 FunASR 需要 WAV）
      const webmBlob = new Blob(audioChunks, { type: 'audio/webm' })
      const wavBlob = await convertWebmToWav(webmBlob)

      // 发送给后端
      const socket = connect()
      if (socket.readyState !== WebSocket.OPEN) {
        await new Promise(resolve => { socket.onopen = resolve })
      }

      // 处理回复
      socket.onmessage = (event) => {
        const msg = JSON.parse(event.data)
        if (msg.type === 'stt') {
          recognizedText.value = msg.data
          if (onSTT) onSTT(msg.data)
        } else if (msg.type === 'text' && onTextToken) {
          onTextToken(msg.data)
        } else if (msg.type === 'stream_end' && onStreamEnd) {
          onStreamEnd()
        } else if (msg.type === 'audio' && onAudioData) {
          onAudioData(msg.data)
        }
      }

      socket.send(wavBlob)
    }

    mediaRecorder.start()
    isListening.value = true
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    isListening.value = false
  }

  return { isListening, recognizedText, startRecording, stopRecording }
}

// WebM → WAV（前端转换，避免后端依赖 ffmpeg）
async function convertWebmToWav(webmBlob) {
  const audioCtx = new AudioContext({ sampleRate: 16000 })
  const arrayBuffer = await webmBlob.arrayBuffer()
  const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer)

  // 提取单声道 PCM
  const pcm = audioBuffer.getChannelData(0)
  const numSamples = pcm.length
  const sampleRate = audioBuffer.sampleRate

  // WAV 头 + PCM 数据
  const wavBuffer = new ArrayBuffer(44 + numSamples * 2)
  const view = new DataView(wavBuffer)

  function writeString(offset, str) {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i))
    }
  }

  writeString(0, 'RIFF')
  view.setUint32(4, 36 + numSamples * 2, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)        // PCM
  view.setUint16(22, 1, true)        // 单声道
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, numSamples * 2, true)

  // 写 PCM（float32 → int16）
  let offset = 44
  for (let i = 0; i < numSamples; i++) {
    const sample = Math.max(-1, Math.min(1, pcm[i]))
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true)
    offset += 2
  }

  return new Blob([wavBuffer], { type: 'audio/wav' })
}