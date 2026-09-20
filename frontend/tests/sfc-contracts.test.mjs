import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { parse, compileTemplate } from '@vue/compiler-sfc'

async function loadSfc(name) {
  const filename = new URL(`../src/components/${name}.vue`, import.meta.url)
  const source = await readFile(filename, 'utf8')
  const { descriptor, errors } = parse(source, { filename: filename.pathname })
  assert.deepEqual(errors, [])
  assert.ok(descriptor.template, `${name} must have a template`)
  const result = compileTemplate({
    source: descriptor.template.content,
    filename: filename.pathname,
    id: `test-${name}`,
  })
  assert.deepEqual(result.errors, [])
  return source
}

for (const name of ['AppHeader', 'CharacterStage', 'SystemInspector', 'MatrixBackdrop', 'KnowledgeWorkspace', 'ConversationDock']) {
  test(`${name} compiles`, async () => { await loadSfc(name) })
}

test('CharacterStage has renderer-neutral state and fallback', async () => {
  const source = await loadSfc('CharacterStage')
  assert.match(source, /renderer/)
  assert.match(source, /audioLevel/)
  assert.match(source, /@error/)
  assert.match(source, /stage-fallback/)
  assert.match(source, /重试/)
})

test('KnowledgeWorkspace preserves knowledge actions and states', async () => {
  const source = await loadSfc('KnowledgeWorkspace')
  for (const token of ['refresh', 'upload', 'delete', 'ask', 'update:ragQuestion']) {
    assert.match(source, new RegExp(token))
  }
  assert.match(source, /\.pdf,\.txt,\.md,\.markdown,\.docx,\.csv,\.json/)
  assert.match(source, /暂无知识文件/)
  assert.match(source, /引用来源/)
})

test('ConversationDock preserves conversation actions', async () => {
  const source = await loadSfc('ConversationDock')
  for (const token of ['send', 'quick-send', 'speak', 'toggle-mic']) {
    assert.match(source, new RegExp(token))
  }
  assert.match(source, /toolCalls/)
  assert.match(source, /世界线变动率探测仪待机中/)
  assert.match(source, /shiftKey/)
})
