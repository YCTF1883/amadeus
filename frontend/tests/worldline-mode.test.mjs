import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { useChat } from '../src/composables/useChat.js'

function installBrowserStubs() {
  globalThis.localStorage = {
    getItem() { return null },
    setItem() {},
  }
}

test('worldline mode is included in chat requests', async () => {
  installBrowserStubs()
  let requestBody = null
  globalThis.fetch = async (_url, options) => {
    requestBody = JSON.parse(options.body)
    return {
      ok: true,
      body: {
        getReader() {
          return { async read() { return { done: true, value: undefined } } }
        },
      },
    }
  }

  const chat = useChat()
  chat.worldlineEnabled.value = true
  chat.worldlineMode.value = 'observe'
  await chat.sendMessage('如果牛顿没有研究引力，会怎样？')

  assert.equal(requestBody.worldline_enabled, true)
  assert.equal(requestBody.worldline_mode, 'observe')
})

test('conversation dock exposes the worldline switch and two modes', async () => {
  const component = await readFile(new URL('../src/components/ConversationDock.vue', import.meta.url), 'utf8')
  assert.match(component, /世界线推演/)
  assert.match(component, /观测模式/)
  assert.match(component, /沉浸模式/)
  assert.match(component, /update:worldline-mode/)
})

test('chat stream preserves line breaks from JSON text events', async () => {
  installBrowserStubs()
  const encoder = new TextEncoder()
  const chunks = [
    encoder.encode('data: {"type":"text","content":"第一行\\n第二行"}\n\ndata: [DONE]\n\n'),
  ]

  globalThis.fetch = async () => ({
    ok: true,
    body: {
      getReader() {
        return {
          async read() {
            return chunks.length
              ? { done: false, value: chunks.shift() }
              : { done: true, value: undefined }
          },
        }
      },
    },
  })

  const chat = useChat()
  await chat.sendMessage('测试换行')

  assert.equal(chat.messages.value.at(-1).content, '第一行\n第二行')
})
