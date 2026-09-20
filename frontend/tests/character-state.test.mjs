import test from 'node:test'
import assert from 'node:assert/strict'
import { CHARACTER_STATES, countRunningTools, resolveCharacterState } from '../src/domain/characterState.js'
import { useCharacterController } from '../src/composables/useCharacterController.js'

test('character state follows priority and recovers', () => {
  assert.equal(resolveCharacterState({}), CHARACTER_STATES.IDLE)
  assert.equal(resolveCharacterState({ isLoading: true }), CHARACTER_STATES.THINKING)
  assert.equal(resolveCharacterState({ isLoading: true, runningToolCount: 1 }), CHARACTER_STATES.WORKING)
  assert.equal(resolveCharacterState({ runningToolCount: 1, isListening: true }), CHARACTER_STATES.LISTENING)
  assert.equal(resolveCharacterState({ isListening: true, isSpeaking: true }), CHARACTER_STATES.SPEAKING)
  assert.equal(resolveCharacterState({ isSpeaking: true, hasError: true }), CHARACTER_STATES.ERROR)
  assert.equal(resolveCharacterState({ hasError: false, isLoading: true }), CHARACTER_STATES.THINKING)
})

test('running tool count spans all messages', () => {
  const messages = [
    { role: 'assistant', toolCalls: [{ status: 'done' }, { status: 'running' }] },
    { role: 'user', content: 'next' },
    { role: 'assistant', toolCalls: [{ status: 'running' }, { status: 'error' }] },
  ]
  assert.equal(countRunningTools(messages), 2)
  assert.equal(countRunningTools([]), 0)
  assert.equal(countRunningTools(), 0)
})

test('character controller module is importable and clamps audio level', () => {
  const controller = useCharacterController({
    hasError: false,
    isSpeaking: false,
    isListening: false,
    runningToolCount: 0,
    isLoading: false,
    audioLevel: 2,
  })
  assert.equal(controller.characterState.value, CHARACTER_STATES.IDLE)
  assert.equal(controller.audioLevel.value, 1)
})
