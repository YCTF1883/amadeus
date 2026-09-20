<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  renderer: { type: String, default: 'static' },
  modelId: { type: String, default: 'makise-kurisu' },
  imageSrc: { type: String, default: '/kurisu.png' },
  state: { type: String, default: 'idle' },
  audioLevel: { type: Number, default: 0 },
})

const emit = defineEmits(['ready', 'error'])
const imageFailed = ref(false)
const imageKey = ref(0)

const labels = {
  idle: '待机',
  listening: '倾听中',
  thinking: '思考中',
  working: '执行任务',
  speaking: '语音输出',
  error: '连接异常',
}

const stateLabel = computed(() => labels[props.state] || labels.idle)
const stageStyle = computed(() => ({
  '--audio-level': Math.max(0, Math.min(1, props.audioLevel)),
}))

function handleReady(event) {
  imageFailed.value = false
  emit('ready', event)
}

function handleError(event) {
  imageFailed.value = true
  emit('error', event)
}

function retryImage() {
  imageFailed.value = false
  imageKey.value += 1
}
</script>

<template>
  <section
    class="character-stage"
    :data-renderer="renderer"
    :data-state="state"
    :style="stageStyle"
    :aria-label="`角色舞台，${stateLabel}`"
  >
    <div class="stage-grid" aria-hidden="true"></div>
    <div class="stage-glow" aria-hidden="true"></div>

    <img
      v-if="!imageFailed"
      :key="imageKey"
      class="character-image"
      :src="imageSrc"
      :alt="modelId === 'makise-kurisu' ? '牧濑红莉栖' : modelId"
      @load="handleReady"
      @error="handleError"
    >

    <div v-else class="stage-fallback" role="status">
      <span class="fallback-mark">A</span>
      <strong>MAKISE KURISU</strong>
      <small>角色资源暂时不可用</small>
      <button type="button" @click="retryImage">重试</button>
    </div>

    <div class="stage-caption">
      <span class="state-signal"><i></i>{{ stateLabel }}</span>
      <span>{{ renderer.toUpperCase() }} / {{ modelId }}</span>
    </div>
  </section>
</template>

<style scoped>
.character-stage {
  --audio-level: 0;
  position: relative;
  min-width: 0;
  min-height: 360px;
  height: 100%;
  overflow: hidden;
  isolation: isolate;
}
.stage-grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(55, 255, 133, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(55, 255, 133, 0.04) 1px, transparent 1px); background-size: 36px 36px; mask-image: linear-gradient(to bottom, transparent, #000 35%, #000); }
.stage-glow { position: absolute; inset: 22% 16% 8%; border: 1px solid rgba(67, 236, 133, 0.08); box-shadow: inset 0 -56px 80px rgba(30, 231, 113, calc(0.06 + var(--audio-level) * 0.12)); transition: box-shadow 120ms linear; }
.character-image { position: absolute; z-index: 2; left: 50%; bottom: 22px; width: min(70%, 560px); height: calc(100% - 44px); transform: translateX(-50%); object-fit: contain; object-position: center bottom; filter: drop-shadow(0 18px 28px rgba(0, 0, 0, 0.55)) drop-shadow(0 0 calc(8px + var(--audio-level) * 22px) rgba(50, 255, 137, 0.3)); }
.stage-caption { position: absolute; z-index: 3; right: 16px; bottom: 14px; left: 16px; display: flex; justify-content: space-between; gap: 12px; color: #60756d; font-size: 10px; }
.state-signal { display: flex; align-items: center; gap: 7px; color: #bfe8ce; }
.state-signal i { width: 7px; height: 7px; border-radius: 50%; background: #49ef8c; box-shadow: 0 0 calc(5px + var(--audio-level) * 14px) #49ef8c; }
[data-state='error'] .state-signal i { background: #f04f7a; box-shadow: 0 0 9px #f04f7a; }
.stage-fallback { position: absolute; z-index: 2; inset: 18% 20%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 9px; border: 1px dashed #365047; color: #b5c9c1; text-align: center; }
.fallback-mark { display: grid; place-items: center; width: 54px; height: 54px; border: 1px solid #f04f7a; color: #f04f7a; font: 700 25px Georgia, serif; }
.stage-fallback small { color: #6f837b; }
.stage-fallback button { margin-top: 7px; padding: 7px 14px; border: 1px solid #3a5e50; border-radius: 5px; background: #0a1210; color: #82dfa5; cursor: pointer; }
@media (max-width: 900px) { .character-stage { min-height: 420px; } .character-image { width: min(82%, 520px); } }
</style>
