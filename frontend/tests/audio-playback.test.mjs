import test from 'node:test'
import assert from 'node:assert/strict'
import { useAudioPlayback } from '../src/composables/useAudioPlayback.js'

function createHarness({ rejectPlay = false } = {}) {
  const urls = []
  const revoked = []
  const audios = []
  const playback = useAudioPlayback({
    urlApi: {
      createObjectURL() {
        const url = `blob:test-${urls.length + 1}`
        urls.push(url)
        return url
      },
      revokeObjectURL(url) { revoked.push(url) },
    },
    audioFactory(src) {
      const audio = {
        src,
        paused: false,
        onended: null,
        onerror: null,
        pause() { this.paused = true },
        play() {
          return rejectPlay
            ? Promise.reject(new Error('autoplay blocked'))
            : Promise.resolve()
        },
      }
      audios.push(audio)
      return audio
    },
    contextFactory: null,
  })
  return { playback, urls, revoked, audios }
}

test('ended playback releases URL and speaking state', async () => {
  const { playback, urls, revoked, audios } = createHarness()
  await playback.playBlob(new Blob(['wav']))
  assert.equal(playback.isSpeaking.value, true)
  audios[0].onended()
  assert.equal(playback.isSpeaking.value, false)
  assert.deepEqual(revoked, urls)
  assert.equal(playback.audioLevel.value, 0)
})

test('rejected playback cleans up and exposes an error', async () => {
  const { playback, urls, revoked } = createHarness({ rejectPlay: true })
  await assert.rejects(playback.playBlob(new Blob(['wav'])), /autoplay blocked/)
  assert.equal(playback.isSpeaking.value, false)
  assert.deepEqual(revoked, urls)
  assert.match(playback.audioError.value, /autoplay blocked/)
})

test('new playback stops the current clip', async () => {
  const { playback, revoked, audios } = createHarness()
  await playback.playBlob(new Blob(['first']))
  await playback.playBlob(new Blob(['second']))
  assert.equal(audios[0].paused, true)
  assert.equal(revoked.length, 1)
  assert.equal(playback.isSpeaking.value, true)
})
