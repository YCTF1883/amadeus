import test from 'node:test'
import assert from 'node:assert/strict'
import { normalizeAssistantText } from '../src/domain/messageFormatting.js'

test('assistant text removes markdown decoration and keeps paragraphs', () => {
  const input = '## 结论\n**牛顿**仍可能研究引力。\n---\n\n第二段。'

  assert.equal(
    normalizeAssistantText(input),
    '结论\n牛顿仍可能研究引力。\n\n第二段。',
  )
})
