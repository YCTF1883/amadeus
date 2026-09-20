<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

const canvasRef = ref(null)
let timer = null
let resizeHandler = null

onMounted(() => {
  const canvas = canvasRef.value
  const ctx = canvas?.getContext('2d')
  if (!canvas || !ctx) return

  const chars = 'ｦｧｨｩｪｫｬｭｮｯｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789ΩΣαβγδελμσφψΔΛΓΣ%±→←↑↓×÷'
  const fontSize = 14
  let drops = []
  let speeds = []

  resizeHandler = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
    const columns = Math.ceil(canvas.width / fontSize)
    drops = new Array(columns).fill(0)
    speeds = new Array(columns).fill(0).map(() => Math.floor(Math.random() * 3))
  }

  const draw = () => {
    ctx.fillStyle = 'rgba(2, 6, 7, 0.08)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.font = `${fontSize}px "Courier New", monospace`
    for (let index = 0; index < drops.length; index += 1) {
      const x = index * fontSize
      const y = drops[index] * fontSize
      const head = Math.random() > 0.97
      ctx.fillStyle = head ? '#d9ffe5' : speeds[index] === 0 ? '#56d77e' : speeds[index] === 1 ? '#18964d' : '#0d4d2a'
      ctx.shadowColor = head ? '#8affad' : 'transparent'
      ctx.shadowBlur = head ? 4 : 0
      ctx.fillText(chars[Math.floor(Math.random() * chars.length)], x, y)
      drops[index] += speeds[index] === 0 ? 1.5 : speeds[index] === 1 ? 1 : 0.6
      if (y > canvas.height && Math.random() > 0.975) {
        drops[index] = 0
        speeds[index] = Math.floor(Math.random() * 3)
      }
    }
    ctx.shadowBlur = 0
  }

  resizeHandler()
  window.addEventListener('resize', resizeHandler)
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    timer = window.setInterval(draw, 50)
  } else {
    draw()
  }
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
})
</script>

<template>
  <canvas ref="canvasRef" class="matrix-backdrop" aria-hidden="true"></canvas>
</template>

<style scoped>
.matrix-backdrop { position: fixed; inset: 0; z-index: 0; width: 100%; height: 100%; opacity: 0.11; pointer-events: none; }
</style>
