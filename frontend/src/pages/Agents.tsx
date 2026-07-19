import { useState, useRef, useEffect } from 'react'
import { IconRobot, IconPlayerPlay } from '@tabler/icons-react'
import styles from './Agents.module.css'

interface Step {
  node: string
  output: string
}

const EXAMPLE_TASKS = [
  'Research LangGraph and write a Python supervisor pattern example',
  'Explain how RAG works and show a basic implementation',
  'Research FastAPI best practices and show a dependency injection example',
]

const NODE_DOT: Record<string, string> = {
  supervisor: styles.dotSupervisor,
  researcher: styles.dotResearcher,
  coder: styles.dotCoder,
  summariser: styles.dotSummariser,
}

export default function Agents() {
  const [task, setTask] = useState('')
  const [running, setRunning] = useState(false)
  const [steps, setSteps] = useState<Step[]>([])
  const [output, setOutput] = useState('')
  const [error, setError] = useState('')
  const stepsEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    stepsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [steps])

  const run = async (taskText?: string) => {
    const t = (taskText ?? task).trim()
    if (!t || running) return

    setTask(t)
    setRunning(true)
    setSteps([])
    setOutput('')
    setError('')

    try {
      const res = await fetch('/api/agents/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: t }),
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
              setError(parsed.error)
            } else if (parsed.step) {
              setSteps(prev => [...prev, parsed.step as Step])
            } else if (parsed.final) {
              setOutput(parsed.final)
            }
          } catch {
            // ignore partial SSE chunks
          }
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className={styles.shell}>
      <div className={styles.taskRow}>
        <textarea
          className={styles.textarea}
          placeholder="Describe a task for the agent system…"
          value={task}
          rows={2}
          onChange={e => setTask(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); run() } }}
          disabled={running}
        />
        <button className={styles.runBtn} onClick={() => run()} disabled={!task.trim() || running}>
          {running ? <span className={styles.spinner} /> : <IconPlayerPlay size={14} />}
          {running ? 'Running…' : 'Run'}
        </button>
      </div>

      {!steps.length && !running && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {EXAMPLE_TASKS.map(t => (
            <button
              key={t}
              style={{
                fontSize: 12, color: 'var(--text-5)', background: 'var(--surface)',
                border: '0.5px solid var(--border)', borderRadius: 'var(--radius-sm)',
                padding: '6px 12px', cursor: 'pointer',
              }}
              onClick={() => run(t)}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      <div className={styles.body}>
        {/* Step feed */}
        <div className={styles.stepPanel}>
          <div className={styles.panelHeader}>Execution trace</div>
          <div className={styles.stepList}>
            {steps.length === 0 ? (
              <p className={styles.stepEmpty}>Steps appear here as agents run</p>
            ) : (
              steps.map((s, i) => (
                <div key={i} className={styles.step}>
                  <div className={styles.stepNode}>
                    <span className={`${styles.dot} ${NODE_DOT[s.node] ?? ''}`} />
                    <span className={styles.nodeName}>{s.node}</span>
                  </div>
                  <p className={styles.stepOutput}>{s.output}</p>
                </div>
              ))
            )}
            <div ref={stepsEndRef} />
          </div>
        </div>

        {/* Output */}
        <div className={styles.outputPanel}>
          <div className={styles.panelHeader}>Final output</div>
          <div className={styles.outputBody}>
            {error ? (
              <p className={styles.outputText} style={{ color: '#e05a5a' }}>Error: {error}</p>
            ) : output ? (
              <p className={styles.outputText}>{output}</p>
            ) : (
              <div className={styles.outputEmpty}>
                <IconRobot size={32} className={styles.outputEmptyIcon} />
                <span>{running ? 'Agents working…' : 'Output appears here after the run'}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
