<script setup>
const props = defineProps({
  files: { type: Array, default: () => [] },
  isUploading: { type: Boolean, default: false },
  isRagLoading: { type: Boolean, default: false },
  ragQuestion: { type: String, default: '' },
  ragAnswer: { type: String, default: '' },
  ragSources: { type: Array, default: () => [] },
  error: { type: String, default: '' },
  message: { type: String, default: '' },
})

const emit = defineEmits(['refresh', 'upload', 'delete', 'ask', 'update:ragQuestion'])

function handleFile(event) {
  const file = event.target.files?.[0]
  if (file) emit('upload', file)
  event.target.value = ''
}

function handleQuestion(value) {
  emit('update:ragQuestion', value)
}

function handleQuestionKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    if (props.ragQuestion.trim() && !props.isRagLoading) emit('ask')
  }
}

function formatFileSize(size) {
  if (!size) return '0 B'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function shortMd5(md5) {
  return md5 ? md5.slice(0, 8) : '--------'
}
</script>

<template>
  <aside class="knowledge-workspace" aria-label="知识工作区">
    <header class="panel-header">
      <div>
        <span>RAG WORKSPACE</span>
        <h2>知识库</h2>
      </div>
      <button class="icon-button" type="button" title="刷新文件列表" aria-label="刷新文件列表" @click="$emit('refresh')">↻</button>
    </header>

    <label class="upload-zone" :class="{ busy: isUploading }">
      <input
        type="file"
        accept=".pdf,.txt,.md,.markdown,.docx,.csv,.json"
        :disabled="isUploading"
        @change="handleFile"
      >
      <span class="upload-icon" aria-hidden="true">↑</span>
      <strong>{{ isUploading ? '解析入库中' : '添加知识文件' }}</strong>
      <small>PDF · DOCX · TXT · MD · CSV · JSON</small>
    </label>

    <p v-if="message" class="notice success" role="status">{{ message }}</p>
    <p v-if="error" class="notice error" role="alert">{{ error }}</p>

    <div class="file-list">
      <div v-if="files.length === 0" class="empty-files">
        <span>暂无知识文件</span>
        <small>上传资料后可进行检索问答</small>
      </div>

      <article v-for="file in files" :key="file.file_id" class="file-row">
        <div class="file-copy">
          <div class="file-heading">
            <strong>{{ file.filename }}</strong>
            <span :class="['file-status', file.status]">{{ file.status || 'ready' }}</span>
          </div>
          <div class="file-meta">
            <span>{{ formatFileSize(file.size) }}</span>
            <span>{{ file.chunk_count || 0 }} CHUNKS</span>
            <span>MD5 {{ shortMd5(file.md5) }}</span>
          </div>
          <p v-if="file.error" class="file-error">{{ file.error }}</p>
        </div>
        <button type="button" class="delete-button" @click="$emit('delete', file)">删除</button>
      </article>
    </div>

    <section class="rag-section">
      <div class="section-heading">
        <span>DOCUMENT QUERY</span>
        <i :class="{ active: isRagLoading }"></i>
      </div>
      <textarea
        :value="ragQuestion"
        rows="3"
        placeholder="基于已上传文档提问…"
        :disabled="isRagLoading"
        @input="handleQuestion($event.target.value)"
        @keydown="handleQuestionKeydown"
      ></textarea>
      <button
        class="ask-button"
        type="button"
        :disabled="isRagLoading || !ragQuestion.trim()"
        @click="$emit('ask')"
      >
        {{ isRagLoading ? '正在检索' : '检索回答' }}
      </button>

      <div v-if="ragAnswer" class="rag-answer">{{ ragAnswer }}</div>
      <div v-if="ragSources.length" class="rag-sources">
        <h3>引用来源</h3>
        <article v-for="(source, index) in ragSources" :key="source.file_id + source.snippet + index">
          <strong>{{ source.filename }}</strong>
          <p>{{ source.snippet }}</p>
        </article>
      </div>
    </section>
  </aside>
</template>

<style scoped>
.knowledge-workspace { display: flex; flex-direction: column; min-width: 0; min-height: 0; height: 100%; padding: 17px 16px 18px; border-right: 1px solid rgba(71, 255, 142, 0.14); background: rgba(5, 11, 12, 0.82); color: #a6bab2; }
.panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.panel-header span, .section-heading span { color: #567068; font-size: 9px; }
h2 { margin: 3px 0 0; color: #f04f7a; font-size: 18px; font-weight: 600; }
button, textarea { font: inherit; }
.icon-button { width: 30px; height: 30px; border: 1px solid #29443a; border-radius: 5px; background: #0b1412; color: #75ce96; cursor: pointer; }
.icon-button:hover { border-color: #48e988; color: #c8ffdc; }
.upload-zone { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 0 0 100px; gap: 5px; border: 1px dashed #315445; background: rgba(34, 221, 112, 0.025); color: #9ddbb4; cursor: pointer; text-align: center; }
.upload-zone:hover { border-color: #48e988; background: rgba(34, 221, 112, 0.05); }
.upload-zone.busy { border-color: #d5a14d; color: #d5a14d; cursor: wait; }
.upload-zone input { display: none; }
.upload-icon { font-size: 24px; line-height: 1; }
.upload-zone strong { font-size: 12px; font-weight: 500; }
.upload-zone small { color: #587069; font-size: 9px; }
.notice { margin: 9px 0 0; padding: 7px 8px; border-left: 2px solid; font-size: 10px; overflow-wrap: anywhere; }
.notice.success { border-color: #49e78a; background: rgba(73, 231, 138, 0.05); color: #83dba4; }
.notice.error, .file-error { border-color: #f04f7a; color: #f17a9a; }
.file-list { flex: 1 1 180px; min-width: 0; min-height: 110px; margin-top: 13px; overflow: auto; scrollbar-width: thin; scrollbar-color: #254b3a transparent; }
.empty-files { display: flex; min-height: 96px; flex-direction: column; align-items: center; justify-content: center; gap: 6px; border-top: 1px solid #17251f; border-bottom: 1px solid #17251f; color: #667b73; font-size: 11px; }
.empty-files small { color: #40534c; font-size: 9px; }
.file-row { display: flex; min-width: 0; gap: 10px; align-items: flex-start; padding: 11px 0; border-top: 1px solid #17251f; }
.file-copy { flex: 1; min-width: 0; }
.file-heading { display: flex; min-width: 0; align-items: flex-start; gap: 7px; }
.file-heading strong { min-width: 0; color: #c5d9d1; font-size: 11px; font-weight: 500; overflow-wrap: anywhere; }
.file-status { flex: 0 0 auto; color: #6f857c; font-size: 8px; text-transform: uppercase; }
.file-status.ready, .file-status.indexed { color: #4ee38a; }
.file-status.error { color: #f04f7a; }
.file-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; color: #50655d; font-size: 8px; }
.file-error { margin: 6px 0 0; font-size: 9px; overflow-wrap: anywhere; }
.delete-button { flex: 0 0 auto; padding: 3px 5px; border: 0; background: transparent; color: #7c5a63; font-size: 9px; cursor: pointer; }
.delete-button:hover { color: #f04f7a; }
.rag-section { flex: 0 0 auto; min-width: 0; padding-top: 14px; border-top: 1px solid #26382f; }
.section-heading { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.section-heading i { width: 5px; height: 5px; border-radius: 50%; background: #40574e; }
.section-heading i.active { background: #48e988; box-shadow: 0 0 8px #48e988; }
textarea { box-sizing: border-box; width: 100%; min-width: 0; min-height: 62px; resize: vertical; border: 1px solid #29443a; border-radius: 4px; outline: 0; background: rgba(1, 6, 7, 0.72); padding: 8px; color: #c0d7ce; font-size: 11px; line-height: 1.5; }
textarea:focus { border-color: #3cbf72; }
textarea::placeholder { color: #42554e; }
.ask-button { width: 100%; height: 30px; margin-top: 6px; border: 1px solid #315a6b; border-radius: 4px; background: rgba(40, 142, 181, 0.06); color: #74c8e7; cursor: pointer; }
.ask-button:disabled { opacity: 0.38; cursor: not-allowed; }
.rag-answer { margin-top: 10px; padding: 9px 0 9px 10px; border-left: 2px solid #4aaccf; color: #b8d2dc; font-size: 11px; line-height: 1.6; white-space: pre-wrap; overflow-wrap: anywhere; }
.rag-sources { min-width: 0; margin-top: 10px; }
.rag-sources h3 { margin: 0 0 6px; color: #5f7b70; font-size: 9px; font-weight: 500; }
.rag-sources article { min-width: 0; padding: 7px 0; border-top: 1px solid #17251f; }
.rag-sources strong { color: #7fae9b; font-size: 9px; overflow-wrap: anywhere; }
.rag-sources p { margin: 4px 0 0; color: #687f76; font-size: 9px; line-height: 1.5; overflow-wrap: anywhere; }
</style>
