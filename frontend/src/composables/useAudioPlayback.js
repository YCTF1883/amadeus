import { ref } from 'vue'

function base64ToWavBlob(value) {
  const bytes = Uint8Array.from(atob(value), char => char.charCodeAt(0))
  return new Blob([bytes], { type: 'audio/wav' })
}

export function useAudioPlayback({
  audioFactory = src => new Audio(src),
  urlApi = URL,
  contextFactory = typeof AudioContext === 'undefined' ? null : () => new AudioContext(),
} = {}) {
  const isSpeaking = ref(false)
  const audioLevel = ref(0)
  const audioError = ref('')
  let currentAudio = null
  let currentUrl = ''
  let audioContext = null
  let analyser = null
  let meterFrame = 0

  function stopMeter() {
    if (meterFrame && typeof cancelAnimationFrame !== 'undefined') {
      cancelAnimationFrame(meterFrame)
    }
    meterFrame = 0
    analyser = null
    if (audioContext) audioContext.close().catch(() => {})
    audioContext = null
    audioLevel.value = 0
  }

  function release() {
    stopMeter()
    if (currentUrl) urlApi.revokeObjectURL(currentUrl)
    currentUrl = ''
    currentAudio = null
    isSpeaking.value = false
  }

  function startMeter(audio) {
    if (!contextFactory || typeof requestAnimationFrame === 'undefined') return
    try {
      audioContext = contextFactory()
      const source = audioContext.createMediaElementSource(audio)
      analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      analyser.connect(audioContext.destination)
      const bins = new Uint8Array(analyser.frequencyBinCount)
      const readLevel = () => {
        if (!analyser) return
        analyser.getByteFrequencyData(bins)
        audioLevel.value = bins.reduce((sum, value) => sum + value, 0) / bins.length / 255
        meterFrame = requestAnimationFrame(readLevel)
      }
      readLevel()
    } catch {
      stopMeter()
    }
  }

  function stop() {
    if (currentAudio && !currentAudio.paused) currentAudio.pause()
    release()
  }

  async function playBlob(blob) {
    stop()
    audioError.value = ''
    currentUrl = urlApi.createObjectURL(blob)
    const audio = audioFactory(currentUrl)
    currentAudio = audio
    audio.onended = () => {
      if (currentAudio === audio) release()
    }
    audio.onerror = () => {
      if (currentAudio !== audio) return
      audioError.value = '语音播放失败'
      release()
    }
    isSpeaking.value = true
    startMeter(audio)
    try {
      await audio.play()
      return audio
    } catch (error) {
      audioError.value = `语音播放失败：${error.message}`
      if (currentAudio === audio) release()
      throw error
    }
  }

  function playBase64Wav(value) {
    return playBlob(base64ToWavBlob(value))
  }

  return { isSpeaking, audioLevel, audioError, playBlob, playBase64Wav, stop }
}
