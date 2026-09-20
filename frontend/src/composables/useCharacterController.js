import { computed, unref } from 'vue'
import { resolveCharacterState } from '../domain/characterState.js'

export function useCharacterController(signals) {
  const characterState = computed(() => resolveCharacterState({
    hasError: Boolean(unref(signals.hasError)),
    isSpeaking: Boolean(unref(signals.isSpeaking)),
    isListening: Boolean(unref(signals.isListening)),
    runningToolCount: Number(unref(signals.runningToolCount) || 0),
    isLoading: Boolean(unref(signals.isLoading)),
  }))

  const audioLevel = computed(() =>
    Math.max(0, Math.min(1, Number(unref(signals.audioLevel) || 0)))
  )

  return { characterState, audioLevel }
}
