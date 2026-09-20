<script setup>
import { computed } from 'vue'

const props = defineProps({
  stats: { type: Object, default: () => ({}) },
  characterState: { type: String, default: 'idle' },
  isSpeaking: { type: Boolean, default: false },
  audioLevel: { type: Number, default: 0 },
})

const rows = computed(() => [
  ['消息', props.stats.messageCount ?? 0],
  ['工具调用', props.stats.toolCount ?? 0],
  ['活动任务', props.stats.activeToolCount ?? 0],
  ['知识文件', props.stats.fileCount ?? 0],
  ['知识片段', props.stats.chunkCount ?? 0],
])
</script>

<template>
  <aside class="system-inspector" aria-label="系统检查器">
    <header>
      <span>INSPECTOR</span>
      <i :class="{ active: isSpeaking }"></i>
    </header>

    <section>
      <h2>运行状态</h2>
      <dl>
        <div><dt>角色状态</dt><dd>{{ characterState.toUpperCase() }}</dd></div>
        <div><dt>渲染器</dt><dd>{{ stats.renderer || 'STATIC' }}</dd></div>
        <div><dt>系统时间</dt><dd>{{ stats.sysTime || '--:--:--' }}</dd></div>
      </dl>
    </section>

    <section>
      <h2>会话计数</h2>
      <dl>
        <div v-for="([label, value]) in rows" :key="label">
          <dt>{{ label }}</dt><dd>{{ value }}</dd>
        </div>
      </dl>
    </section>

    <section>
      <h2>音频电平</h2>
      <div class="level-track" :aria-label="`音频电平 ${Math.round(audioLevel * 100)}%`">
        <span :style="{ width: `${Math.round(audioLevel * 100)}%` }"></span>
      </div>
    </section>
  </aside>
</template>

<style scoped>
.system-inspector { min-width: 0; height: 100%; padding: 18px 16px; border-left: 1px solid rgba(71, 255, 142, 0.14); background: rgba(6, 12, 13, 0.76); color: #8da39a; font-size: 11px; }
header { display: flex; align-items: center; justify-content: space-between; height: 28px; color: #d7ebe2; font-size: 10px; }
header i { width: 6px; height: 6px; border-radius: 50%; background: #41564e; }
header i.active { background: #f04f7a; box-shadow: 0 0 9px #f04f7a; }
section { padding: 16px 0; border-top: 1px solid rgba(130, 165, 151, 0.14); }
h2 { margin: 0 0 11px; color: #5f776e; font-size: 9px; font-weight: 600; text-transform: uppercase; }
dl { margin: 0; }
dl div { display: flex; justify-content: space-between; gap: 12px; min-width: 0; padding: 5px 0; }
dt { min-width: 0; overflow-wrap: anywhere; }
dd { margin: 0; color: #bdd2ca; font-variant-numeric: tabular-nums; text-align: right; }
.level-track { height: 3px; overflow: hidden; background: #14221d; }
.level-track span { display: block; height: 100%; min-width: 2px; background: #49ef8c; box-shadow: 0 0 7px #49ef8c; transition: width 100ms linear; }
</style>
