export const CHARACTER_STATES = Object.freeze({
  IDLE: 'idle',
  LISTENING: 'listening',
  THINKING: 'thinking',
  WORKING: 'working',
  SPEAKING: 'speaking',
  ERROR: 'error',
})

export function countRunningTools(messages = []) {
  return messages.reduce((total, message) => {
    const calls = Array.isArray(message.toolCalls) ? message.toolCalls : []
    return total + calls.filter(call => call.status === 'running').length
  }, 0)
}

export function resolveCharacterState({
  hasError = false,
  isSpeaking = false,
  isListening = false,
  runningToolCount = 0,
  isLoading = false,
} = {}) {
  if (hasError) return CHARACTER_STATES.ERROR
  if (isSpeaking) return CHARACTER_STATES.SPEAKING
  if (isListening) return CHARACTER_STATES.LISTENING
  if (runningToolCount > 0) return CHARACTER_STATES.WORKING
  if (isLoading) return CHARACTER_STATES.THINKING
  return CHARACTER_STATES.IDLE
}
