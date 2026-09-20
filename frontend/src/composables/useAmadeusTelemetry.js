import { computed, onMounted, onUnmounted, ref } from 'vue'

export function useAmadeusTelemetry({ messages, files }) {
  const baseValue = 1.048596
  const worldLine = ref(baseValue.toFixed(6))
  const sysTime = ref('')
  let rawJitter = 0
  let clockTimer = 0
  let worldLineTimer = 0

  const messageCount = computed(() => messages.value.length)
  const toolCount = computed(() => messages.value.reduce(
    (total, message) => total + (Array.isArray(message.toolCalls) ? message.toolCalls.length : 0),
    0,
  ))
  const fileCount = computed(() => files.value.length)
  const chunkCount = computed(() => files.value.reduce(
    (total, file) => total + (file.chunk_count || 0),
    0,
  ))

  onMounted(() => {
    const updateTime = () => {
      sysTime.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    }
    updateTime()
    clockTimer = window.setInterval(updateTime, 1000)
    worldLineTimer = window.setInterval(() => {
      const jump = Math.random() > 0.97 ? (Math.random() - 0.5) * 0.002 : 0
      rawJitter += (Math.random() - 0.5) * 0.000002 + jump
      rawJitter = Math.max(-0.00005, Math.min(0.00005, rawJitter))
      worldLine.value = (baseValue + rawJitter).toFixed(6)
    }, 80)
  })

  onUnmounted(() => {
    window.clearInterval(clockTimer)
    window.clearInterval(worldLineTimer)
  })

  return { worldLine, sysTime, messageCount, toolCount, fileCount, chunkCount }
}
