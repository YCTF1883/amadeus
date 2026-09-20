import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

test('App composes the role workbench', async () => {
  const app = await readFile(new URL('../src/App.vue', import.meta.url), 'utf8')
  for (const name of ['MatrixBackdrop', 'AppHeader', 'KnowledgeWorkspace', 'CharacterStage', 'SystemInspector', 'ConversationDock']) {
    assert.match(app, new RegExp(`<${name}`))
  }
  assert.doesNotMatch(app, /class="kurisu-img"/)
  assert.doesNotMatch(app, /new Audio\(/)
  assert.doesNotMatch(app, /getContext\('2d'\)/)
})

test('workbench CSS defines desktop and mobile boundaries', async () => {
  const css = await readFile(new URL('../src/styles/workbench.css', import.meta.url), 'utf8')
  assert.match(css, /grid-template-areas/)
  assert.match(css, /@media\s*\(max-width:\s*900px\)/)
  assert.match(css, /minmax\(0,\s*1fr\)/)
  assert.match(css, /prefers-reduced-motion/)
  assert.match(css, /min-height:\s*40px/)
})
