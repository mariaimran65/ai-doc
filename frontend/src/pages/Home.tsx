import { Link } from 'react-router-dom'
import {
  IconBook2,
  IconMessageChatbot,
  IconRobot,
  IconDatabase,
  IconChartBar,
  IconArrowRight,
  IconCircleCheckFilled,
} from '@tabler/icons-react'
import { useAuth } from '../context/AuthContext'
import styles from './Home.module.css'

const PHASES = [
  {
    num: 1,
    name: 'Foundations',
    desc: 'FastAPI + React + Google OAuth + async PostgreSQL',
    tags: ['FastAPI', 'React', 'Auth', 'Docker'],
    live: true,
  },
  {
    num: 2,
    name: 'LangChain Chat',
    desc: 'LCEL agent with tool use, streaming SSE, and chat history',
    tags: ['LangChain', 'Anthropic', 'SSE', 'Tools'],
    live: true,
    path: '/chat',
  },
  {
    num: 3,
    name: 'Multi-Agent',
    desc: 'LangGraph supervisor coordinating researcher, coder, and summariser agents',
    tags: ['LangGraph', 'StateGraph', 'Supervisor'],
    live: true,
    path: '/agents',
  },
  {
    num: 4,
    name: 'RAG Pipeline',
    desc: 'pgvector cosine search with fastembed local embeddings and Claude Q&A',
    tags: ['pgvector', 'fastembed', 'RAG', 'PDF'],
    live: true,
    path: '/knowledge',
  },
  {
    num: 5,
    name: 'Observability',
    desc: 'LangSmith tracing, platform metrics dashboard, and usage analytics',
    tags: ['LangSmith', 'Metrics', 'Tracing'],
    live: true,
    path: '/metrics',
  },
]

const QUICK_LINKS = [
  { name: 'Chat', desc: 'LangChain agent with web search', path: '/chat', Icon: IconMessageChatbot },
  { name: 'Agents', desc: 'Multi-agent task pipeline', path: '/agents', Icon: IconRobot },
  { name: 'Knowledge', desc: 'Upload PDFs and ask questions', path: '/knowledge', Icon: IconDatabase },
  { name: 'Metrics', desc: 'Platform usage and tracing', path: '/metrics', Icon: IconChartBar },
  { name: 'Docs', desc: 'Architecture and API reference', path: '/docs', Icon: IconBook2 },
]

export default function Home() {
  const { user } = useAuth()
  const email = user?.email ?? ''
  const name = email
    .split('@')[0]
    .replace(/[._]/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())

  return (
    <div className={styles.page}>
      {/* Hero */}
      <div className={styles.hero}>
        <div className={styles.heroGlow} />
        <p className={styles.eyebrow}>Welcome back</p>
        <h1 className={styles.heading}>{name}</h1>
        <p className={styles.subheading}>
          Your production AI engineering platform — 5 phases, all live.
        </p>
      </div>

      {/* Phase timeline */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Platform Phases</h2>
        <div className={styles.phases}>
          {PHASES.map(p => (
            <div key={p.num} className={styles.phase}>
              <div className={styles.phaseHeader}>
                <span className={styles.phaseNum}>Phase {p.num}</span>
                <span className={styles.phaseLive}>
                  <IconCircleCheckFilled size={12} />
                  Live
                </span>
              </div>
              <p className={styles.phaseName}>{p.name}</p>
              <p className={styles.phaseDesc}>{p.desc}</p>
              <div className={styles.phaseTags}>
                {p.tags.map(t => (
                  <span key={t} className={styles.tag}>{t}</span>
                ))}
              </div>
              {p.path && (
                <Link to={p.path} className={styles.phaseLink}>
                  Open <IconArrowRight size={11} />
                </Link>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Quick access */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Quick Access</h2>
        <div className={styles.quickGrid}>
          {QUICK_LINKS.map(({ name: n, desc, path, Icon }) => (
            <Link key={path} to={path} className={styles.quickCard}>
              <div className={styles.quickIcon}>
                <Icon size={17} />
              </div>
              <div>
                <p className={styles.quickName}>{n}</p>
                <p className={styles.quickDesc}>{desc}</p>
              </div>
              <IconArrowRight size={14} className={styles.quickArrow} />
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
