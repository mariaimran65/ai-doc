import { useState, useRef, useEffect, useCallback } from 'react'
import { IconSend, IconMessageChatbot } from '@tabler/icons-react'
import { useAuth } from '../context/AuthContext'
import styles from './Chat.module.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const HINTS = [
  'What is LangChain LCEL?',
  'How does RAG work?',
  'Explain tool use in LangChain',
  'What did I just ask you?',
]

function initials(email: string) {
  return email.split('@')[0].slice(0, 2).toUpperCase()
}

export default function Chat() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const autoResize = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  const send = useCallback(async (text?: string) => {
    const content = (text ?? input).trim()
    if (!content || streaming) return

    const userMsg: Message = { role: 'user', content }
    const nextMessages = [...messages, userMsg]
    setMessages(nextMessages)
    setInput('')
    setStreaming(true)

    // Placeholder assistant message that we'll fill as tokens arrive
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const res = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: nextMessages }),
        credentials: 'include',
      })

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`)
      }

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
                copy[copy.length - 1] = {
                  role: 'assistant',
                  content: `Error: ${parsed.error}`,
                }
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
          } catch {
            // ignore JSON parse errors for partial SSE chunks
          }
        }
      }
    } catch (err) {
      setMessages(prev => {
        const copy = [...prev]
        copy[copy.length - 1] = {
          role: 'assistant',
          content: `Sorry, something went wrong: ${err instanceof Error ? err.message : 'Unknown error'}`,
        }
        return copy
      })
    } finally {
      setStreaming(false)
    }
  }, [input, messages, streaming])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const userInitials = user ? initials(user.email) : '?'

  return (
    <div className={styles.shell}>
      <div className={styles.messages}>
        {messages.length === 0 ? (
          <div className={styles.empty}>
            <IconMessageChatbot size={36} className={styles.emptyIcon} />
            <p className={styles.emptyTitle}>Ask me anything about AI engineering</p>
            <div className={styles.emptyHints}>
              {HINTS.map(h => (
                <button key={h} className={styles.hint} onClick={() => send(h)}>
                  {h}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => {
            const isUser = m.role === 'user'
            const isLastAssistant = !isUser && i === messages.length - 1 && streaming
            return (
              <div key={i} className={`${styles.row} ${isUser ? styles.rowUser : ''}`}>
                <div className={`${styles.avatar} ${isUser ? styles.avatarUser : styles.avatarAssistant}`}>
                  {isUser ? userInitials : 'AI'}
                </div>
                <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAssistant}`}>
                  {m.content}
                  {isLastAssistant && m.content === '' && <span className={styles.cursor} />}
                  {isLastAssistant && m.content !== '' && <span className={styles.cursor} />}
                </div>
              </div>
            )
          })
        )}
        <div ref={bottomRef} />
      </div>

      <div className={styles.inputBar}>
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          placeholder="Message AI-Doc..."
          value={input}
          rows={1}
          onChange={e => { setInput(e.target.value); autoResize() }}
          onKeyDown={handleKeyDown}
          disabled={streaming}
        />
        <button
          className={styles.sendBtn}
          onClick={() => send()}
          disabled={!input.trim() || streaming}
          aria-label="Send"
        >
          <IconSend size={16} />
        </button>
      </div>
    </div>
  )
}
