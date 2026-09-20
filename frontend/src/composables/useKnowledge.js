import { ref } from 'vue'

export function useKnowledge() {
  const files = ref([])
  const isUploading = ref(false)
  const isRagLoading = ref(false)
  const ragQuestion = ref('')
  const ragAnswer = ref('')
  const ragSources = ref([])
  const knowledgeError = ref('')
  const knowledgeMessage = ref('')

  async function loadFiles() {
    knowledgeError.value = ''
    try {
      const resp = await fetch('/api/knowledge/files')
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      files.value = await resp.json()
    } catch (err) {
      knowledgeError.value = `文件列表加载失败：${err.message}`
    }
  }

  async function uploadFile(file) {
    if (!file) return
    isUploading.value = true
    knowledgeError.value = ''
    knowledgeMessage.value = ''
    try {
      const form = new FormData()
      form.append('file', file)
      const resp = await fetch('/api/knowledge/upload', {
        method: 'POST',
        body: form,
      })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`)
      knowledgeMessage.value = data.message || '上传完成'
      await loadFiles()
    } catch (err) {
      knowledgeError.value = `上传失败：${err.message}`
    } finally {
      isUploading.value = false
    }
  }

  async function deleteFile(fileId) {
    if (!fileId) return
    knowledgeError.value = ''
    knowledgeMessage.value = ''
    try {
      const resp = await fetch(`/api/knowledge/files/${fileId}`, {
        method: 'DELETE',
      })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`)
      knowledgeMessage.value = data.message || '已删除'
      await loadFiles()
    } catch (err) {
      knowledgeError.value = `删除失败：${err.message}`
    }
  }

  async function askRag(question) {
    const q = (question || ragQuestion.value).trim()
    if (!q) return
    isRagLoading.value = true
    knowledgeError.value = ''
    ragAnswer.value = ''
    ragSources.value = []
    try {
      const resp = await fetch('/api/rag/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, k: 4 }),
      })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`)
      ragAnswer.value = data.answer || ''
      ragSources.value = data.sources || []
    } catch (err) {
      knowledgeError.value = `RAG 问答失败：${err.message}`
    } finally {
      isRagLoading.value = false
    }
  }

  return {
    files,
    isUploading,
    isRagLoading,
    ragQuestion,
    ragAnswer,
    ragSources,
    knowledgeError,
    knowledgeMessage,
    loadFiles,
    uploadFile,
    deleteFile,
    askRag,
  }
}
