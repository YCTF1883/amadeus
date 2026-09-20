import test from 'node:test'
import assert from 'node:assert/strict'
import { useChat } from '../src/composables/useChat.js'

test('clearing history also clears a prior chat error', () => {
  globalThis.localStorage = {
    getItem() { return null },
    setItem() {},
  }

  const chat = useChat()
  chat.chatError.value = '发送失败'
  chat.messages.value.push({ id: 1, role: 'user', content: 'test' })
  chat.clearHistory()

  assert.equal(chat.chatError.value, '')
  assert.deepEqual(chat.messages.value, [])
})
