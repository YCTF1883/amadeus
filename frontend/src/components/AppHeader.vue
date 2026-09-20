<script setup>
defineProps({
  worldLine: { type: String, default: '1.048596' },
  isListening: { type: Boolean, default: false },
  connectionLabel: { type: String, default: 'ONLINE' },
})

defineEmits(['new-conversation', 'toggle-mic'])
</script>

<template>
  <header class="app-header">
    <div class="identity">
      <strong>AMADEUS</strong>
      <span>Makise Kurisu</span>
    </div>

    <div class="telemetry" aria-label="系统状态">
      <span class="connection"><i></i>{{ connectionLabel }}</span>
      <span class="world-line"><small>WORLD LINE</small>{{ worldLine }}</span>
    </div>

    <div class="header-actions">
      <button
        class="icon-button"
        :class="{ active: isListening }"
        type="button"
        :aria-label="isListening ? '停止语音输入' : '开始语音输入'"
        :title="isListening ? '停止语音输入' : '开始语音输入'"
        @click="$emit('toggle-mic')"
      >
        <span class="mic-icon" aria-hidden="true"></span>
      </button>
      <button class="new-button" type="button" @click="$emit('new-conversation')">
        <span aria-hidden="true">＋</span> 新对话
      </button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: minmax(210px, 1fr) auto minmax(210px, 1fr);
  align-items: center;
  min-height: 62px;
  padding: 0 24px;
  border-bottom: 1px solid rgba(71, 255, 142, 0.2);
  background: rgba(5, 9, 11, 0.88);
  backdrop-filter: blur(18px);
}

.identity,
.telemetry,
.header-actions {
  display: flex;
  align-items: center;
}

.identity { gap: 14px; min-width: 0; }
.identity strong { color: #f04f7a; font-family: Georgia, serif; font-size: 20px; letter-spacing: 0; }
.identity span { color: #94a5a0; font-size: 11px; }
.telemetry { gap: 22px; justify-content: center; font-size: 11px; }
.connection { display: flex; align-items: center; gap: 7px; color: #87eaa9; }
.connection i { width: 6px; height: 6px; border-radius: 50%; background: #42ef83; box-shadow: 0 0 8px #42ef83; }
.world-line { display: flex; align-items: baseline; gap: 8px; color: #e7fff0; font-variant-numeric: tabular-nums; }
.world-line small { color: #647972; font-size: 9px; }
.header-actions { justify-content: flex-end; gap: 9px; }
button { font: inherit; }
.icon-button,
.new-button { border: 1px solid #29433a; background: #0b1212; color: #b8cbc4; cursor: pointer; }
.icon-button { display: grid; place-items: center; width: 34px; height: 34px; padding: 0; border-radius: 6px; }
.icon-button:hover,
.icon-button.active { border-color: #42ef83; color: #42ef83; }
.new-button { height: 34px; padding: 0 12px; border-radius: 6px; }
.new-button:hover { border-color: #f04f7a; color: #fff; }
.mic-icon { position: relative; width: 8px; height: 14px; border: 2px solid currentColor; border-radius: 5px; }
.mic-icon::before { content: ''; position: absolute; left: -5px; bottom: -5px; width: 14px; height: 9px; border: 2px solid currentColor; border-top: 0; border-radius: 0 0 8px 8px; }
.mic-icon::after { content: ''; position: absolute; left: 2px; bottom: -8px; width: 2px; height: 4px; background: currentColor; }

@media (max-width: 760px) {
  .app-header { grid-template-columns: 1fr auto; min-height: 56px; padding: 0 14px; }
  .identity span, .connection { display: none; }
  .telemetry { justify-content: flex-end; margin-right: 10px; }
  .header-actions { grid-column: 2; }
  .telemetry { grid-column: 1; grid-row: 1; justify-self: center; }
  .identity { grid-column: 1; grid-row: 1; justify-self: start; }
  .new-button { width: 34px; padding: 0; font-size: 0; }
  .new-button span { font-size: 18px; }
}
</style>
