import { useState, useEffect, useRef } from 'react'
import { IconDatabase, IconUpload } from '@tabler/icons-react'
import styles from './Knowledge.module.css'

interface Doc {
  id: string
  title: string
  source_name: string
  chunks: number
  created_at: string
}

interface QAMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function Knowledge() {
  const [docs, setDocs] = useState<Doc[]>([])
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState<{ text: string; ok: boolean } | null>(null)
  const [messages, setMessages] = useState<QAMessage[]>([])
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { loadDocs() }, [])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function loadDocs() {
    try {
      const res = await fetch('/api/knowledge/documents', { credentials: 'include' })
      if (res.ok) setDocs(await res.json())
    } catch { /* ignore */ }
  }

  async function handleUpload(file: File) {
    setUploading(true)
    setUploadMsg(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('/api/knowledge/upload', {
        method: 'POST', body: form, credentials: 'include',
      })
      const data = await res.json()
      if (res.ok) {
        setUploadMsg({ text: `Ingested ${data.chunks} chunks from "${data.filename}"`, ok: true })
        await loadDocs()
      } else {
        setUploadMsg({ text: data.detail ?? 'Upload failed', ok: false })
      }
    } catch (e) {
      setUploadMsg({ text: String(e), ok: false })
    } finally {
      setUploading(false)
    }
  }

  async function ask() {
    const q = question.trim()
    if (!q || asking) return
    setMessages(prev => [...prev, { role: 'user', content: q }, { role: 'assistant', content: '' }])
    setQuestion('')
    setAsking(true)

    try {
      const res = await fetch('/api/knowledge/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, document_id: selectedDoc }),
        credentials: 'include',
      })
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          const data = line.slice(5).trim()
          if (data === '[DONE]') break
          try {
            const parsed = JSON.parse(data)
            if (parsed.error) {
              setMessages(prev => {
                const copy = [...prev]
                copy[copy.length - 1] = { role: 'assistant', content: `Error: ${parsed.error}` }
                return copy
              })
              return
            }
            if (parsed.token) {
              setMessages(prev => {
                const copy = [...prev]
                copy[copy.length - 1] = {
                  role: 'assistant',
                  content: copy[copy.length - 1].content + parsed.token,
                }
                return copy
              })
            }
          } catch { /* ignore */ }
        }
      }
    } catch (e) {
      setMessages(prev => {
        const copy = [...prev]
        copy[copy.length - 1] = { role: 'assistant', content: `Error: ${String(e)}` }
        return copy
      })
    } finally {
      setAsking(false)
    }
  }

  const activeDoc = docs.find(d => d.id === selectedDoc)

  return (
    <div className={styles.shell}>
      <div className={styles.cols}>
        {/* Sidebar */}
        <div className={styles.sidebar}>
          <div
            className={styles.uploadBox}
            onClick={() => fileRef.current?.click()}
            onDragOver={e => e.preventDefault()}
            onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleUpload(f) }}
          >
            <IconUpload size={24} className={styles.uploadIcon} />
            <div className={styles.uploadLabel}>
              <strong>Click or drag a file here</strong>
              PDF or .txt · max 10 MB
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.txt"
              className={styles.uploadInput}
              onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f) }}
            />
            <button className={styles.uploadBtn} disabled={uploading} onClick={e => { e.stopPropagation(); fileRef.current?.click() }}>
              {uploading ? 'Ingesting…' : 'Upload document'}
            </button>
          </div>

          {uploadMsg && (
            <p className={`${styles.uploadStatus} ${uploadMsg.ok ? styles.uploadSuccess : styles.uploadError}`}>
              {uploadMsg.text}
            </p>
          )}

          <div className={styles.docList}>
            {docs.length === 0 ? (
              <p className={styles.noDocMsg}>No documents yet</p>
            ) : (
              docs.map(doc => (
                <button
                  key={doc.id}
                  className={`${styles.docCard} ${selectedDoc === doc.id ? styles.docCardActive : ''}`}
                  onClick={() => setSelectedDoc(doc.id === selectedDoc ? null : doc.id)}
                >
                  <p className={styles.docName}>{doc.source_name}</p>
                  <p className={styles.docMeta}>{doc.chunks} chunks · {doc.created_at.slice(0, 10)}</p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Q&A panel */}
        <div className={styles.qaPanel}>
          <div className={styles.qaMessages}>
            {messages.length === 0 ? (
              <div className={styles.qaEmpty}>
                <IconDatabase size={32} className={styles.qaEmptyIcon} />
                <span>
                  {docs.length === 0
                    ? 'Upload a document to start asking questions'
                    : activeDoc
                    ? `Asking about: ${activeDoc.source_name}`
                    : 'Select a document or ask across all documents'}
                </span>
              </div>
            ) : (
              messages.map((m, i) => (
                <div
                  key={i}
                  className={`${styles.qaBubble} ${m.role === 'user' ? styles.qaBubbleUser : styles.qaBubbleAssistant}`}
                >
                  {m.content}
                </div>
              ))
            )}
            <div ref={bottomRef} />
          </div>

          <div className={styles.qaInputBar}>
            <input
              className={styles.qaInput}
              placeholder={docs.length === 0 ? 'Upload a document first…' : 'Ask a question about your documents…'}
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') ask() }}
              disabled={asking || docs.length === 0}
            />
            <button className={styles.askBtn} onClick={ask} disabled={!question.trim() || asking || docs.length === 0}>
              {asking ? '…' : 'Ask'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
