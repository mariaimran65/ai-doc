import { useState, useEffect } from 'react'
import { IconChartBar } from '@tabler/icons-react'
import styles from './Metrics.module.css'

interface Counts {
  users: number
  documents: number
  chunks: number
  total_runs: number
  completed_runs: number
  active_sessions: number
}

interface SignIn {
  email: string
  name: string | null
  provider: string
  signed_in_at: string
}

interface Run {
  id: string
  triggered_by: string
  task: string
  started_at: string
  duration_seconds: number | null
}

interface MetricsData {
  counts: Counts
  recent_signins: SignIn[]
  recent_runs: Run[]
}

const STATS = (c: Counts) => [
  { label: 'Users', value: c.users },
  { label: 'Documents', value: c.documents },
  { label: 'Chunks indexed', value: c.chunks },
  { label: 'Agent runs', value: c.total_runs },
  { label: 'Completed runs', value: c.completed_runs },
  { label: 'Active sessions', value: c.active_sessions },
]

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

export default function Metrics() {
  const [data, setData] = useState<MetricsData | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/metrics/', { credentials: 'include' })
      .then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(e.detail)))
      .then(setData)
      .catch(e => setError(String(e)))
  }, [])

  if (error) return <div className={styles.shell}><p className={styles.loading}>Error: {error}</p></div>
  if (!data) return <div className={styles.shell}><p className={styles.loading}>Loading…</p></div>

  return (
    <div className={styles.shell}>

      {/* LangSmith banner */}
      <div className={styles.banner}>
        <IconChartBar size={20} className={styles.bannerIcon} />
        <div className={styles.bannerText}>
          <p className={styles.bannerTitle}>LangSmith Tracing</p>
          <p className={styles.bannerDesc}>
            Set <code>LANGCHAIN_TRACING_V2=true</code> and <code>LANGCHAIN_API_KEY=ls__...</code> in your{' '}
            <code>.env</code> to trace every Chat, Agent, and Knowledge call at{' '}
            <code>smith.langchain.com</code>.
          </p>
        </div>
      </div>

      {/* Stat cards */}
      <div>
        <p className={styles.sectionTitle}>Platform counts</p>
        <div className={styles.statGrid}>
          {STATS(data.counts).map(s => (
            <div key={s.label} className={styles.statCard}>
              <p className={styles.statValue}>{s.value}</p>
              <p className={styles.statLabel}>{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent sign-ins */}
      <div>
        <p className={styles.sectionTitle}>Recent active sessions</p>
        <div className={styles.tableWrap}>
          {data.recent_signins.length === 0 ? (
            <p className={styles.empty}>No active sessions</p>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Provider</th>
                  <th>Signed in</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_signins.map((s, i) => (
                  <tr key={i}>
                    <td>{s.email}</td>
                    <td>
                      <span className={`${styles.badge} ${styles.badgeGoogle}`}>{s.provider}</span>
                    </td>
                    <td>{timeAgo(s.signed_in_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Recent agent runs */}
      <div>
        <p className={styles.sectionTitle}>Recent agent runs</p>
        <div className={styles.tableWrap}>
          {data.recent_runs.length === 0 ? (
            <p className={styles.empty}>No completed runs yet</p>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Task</th>
                  <th>User</th>
                  <th>Duration</th>
                  <th>Started</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_runs.map(r => (
                  <tr key={r.id}>
                    <td style={{ maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {r.task}
                    </td>
                    <td>{r.triggered_by}</td>
                    <td>{r.duration_seconds != null ? `${r.duration_seconds.toFixed(1)}s` : '—'}</td>
                    <td>{timeAgo(r.started_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

    </div>
  )
}
