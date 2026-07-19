import React, { useState } from 'react'
import styles from './Docs.module.css'

type Tab = 'architecture' | 'decisions' | 'runbook' | 'api'

const TABS: { id: Tab; label: string }[] = [
  { id: 'architecture', label: 'Architecture' },
  { id: 'decisions', label: 'Decisions' },
  { id: 'runbook', label: 'Runbook' },
  { id: 'api', label: 'API Reference' },
]

const DIAGRAM = `
  Browser
     │  HTTPS
     ▼
  Traefik (reverse proxy + TLS)
     │             │
     ▼             ▼
  Vite dev    FastAPI :8000
  :5173       /api/*
     │
     └── proxy /api → http://api:8000
                         │
                    PostgreSQL + pgvector
                    Redis (cache / sessions)
`.trim()

const ADR_LIST = [
  { num: 'ADR-001', title: 'Vite proxy for OAuth cookie alignment', date: 'July 2025', status: 'accepted' },
  { num: 'ADR-002', title: 'Traefik labels as sole routing source', date: 'July 2025', status: 'accepted' },
  { num: 'ADR-003', title: 'httpOnly JWT cookies over localStorage', date: 'July 2025', status: 'accepted' },
  { num: 'ADR-004', title: 'LangChain for Phase 2 chat (Phase 3: LangGraph)', date: 'August 2025', status: 'draft' },
]

const ENDPOINTS = [
  { method: 'GET', path: '/api/auth/login', desc: 'Redirects to Google OAuth consent screen.' },
  { method: 'GET', path: '/api/auth/callback', desc: 'Handles OAuth callback, sets httpOnly JWT cookie.' },
  { method: 'GET', path: '/api/auth/me', desc: 'Returns current authenticated user.' },
  { method: 'POST', path: '/api/auth/logout', desc: 'Clears the auth cookie.' },
  { method: 'GET', path: '/api/health', desc: 'Service health check.' },
]

function Architecture() {
  return (
    <div className={styles.body}>
      <p className={styles.sectionTitle}>System Architecture</p>
      <pre className={styles.diagram}>{DIAGRAM}</pre>
      <p className={styles.archNote}>
        All traffic enters through <code>Traefik</code> which terminates TLS via Let&apos;s Encrypt.
        The Vite dev server proxies <code>/api/*</code> to FastAPI so that the OAuth callback
        cookie is scoped to the frontend domain, eliminating cross-subdomain auth issues.
        PostgreSQL runs with the <code>pgvector</code> extension for Phase 4 embeddings.
        Redis is available for caching and future session storage.
      </p>
    </div>
  )
}

function Decisions() {
  return (
    <div className={styles.body}>
      <p className={styles.sectionTitle}>Architecture Decision Records</p>
      <div className={styles.adrList}>
        {ADR_LIST.map(adr => (
          <button key={adr.num} className={styles.adrCard}>
            <span className={styles.adrNum}>{adr.num}</span>
            <div className={styles.adrInfo}>
              <p className={styles.adrTitle}>{adr.title}</p>
              <p className={styles.adrDate}>{adr.date}</p>
            </div>
            <span className={adr.status === 'accepted' ? styles.statusAccepted : styles.statusDraft}>
              {adr.status}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

function Runbook() {
  return (
    <div className={styles.body}>
      <p className={styles.sectionTitle}>Runbook</p>

      <div className={styles.runSection}>
        <p className={styles.runHeading}>Local development</p>
        <div className={styles.step}>
          <span className={styles.stepNum}>1</span>
          <p className={styles.stepText}>Clone the repo and copy <code>.env.example</code> → <code>.env</code></p>
        </div>
        <div className={styles.step}>
          <span className={styles.stepNum}>2</span>
          <p className={styles.stepText}>Fill in <code>GOOGLE_CLIENT_ID</code>, <code>GOOGLE_CLIENT_SECRET</code>, <code>SECRET_KEY</code></p>
        </div>
        <div className={styles.step}>
          <span className={styles.stepNum}>3</span>
          <p className={styles.stepText}>Run the stack with Docker Compose</p>
        </div>
        <div className={styles.codeLine}>docker compose up --build</div>
        <div className={styles.step}>
          <span className={styles.stepNum}>4</span>
          <p className={styles.stepText}>Open <code>http://localhost:5173</code></p>
        </div>
      </div>

      <div className={styles.runSection}>
        <p className={styles.runHeading}>Production deploy (Dokploy)</p>
        <div className={styles.step}>
          <span className={styles.stepNum}>1</span>
          <p className={styles.stepText}>Push to main — GitHub Actions runs lint + tests</p>
        </div>
        <div className={styles.step}>
          <span className={styles.stepNum}>2</span>
          <p className={styles.stepText}>Dokploy auto-deploys on push via webhook</p>
        </div>
        <div className={styles.step}>
          <span className={styles.stepNum}>3</span>
          <p className={styles.stepText}>Traefik picks up labels from <code>docker-compose.prod.yml</code> and issues TLS cert</p>
        </div>
        <div className={styles.step}>
          <span className={styles.stepNum}>4</span>
          <p className={styles.stepText}>Verify at aidoc.talent.techsupersonic.com</p>
        </div>
      </div>
    </div>
  )
}

function APIReference() {
  return (
    <div className={styles.body}>
      <p className={styles.sectionTitle}>API Reference</p>
      {ENDPOINTS.map(ep => (
        <div key={ep.path} className={styles.endpointCard}>
          <div className={styles.epRow}>
            <span className={ep.method === 'GET' ? styles.methodGet : styles.methodPost}>{ep.method}</span>
            <span className={styles.epPath}>{ep.path}</span>
          </div>
          <p className={styles.epDesc}>{ep.desc}</p>
        </div>
      ))}
    </div>
  )
}

export default function Docs() {
  const [active, setActive] = useState<Tab>('architecture')

  const panels: Record<Tab, () => React.ReactElement> = {
    architecture: Architecture,
    decisions: Decisions,
    runbook: Runbook,
    api: APIReference,
  }
  const Content = panels[active]

  return (
    <div className={styles.shell}>
      <div className={styles.subnav}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`${styles.tab} ${active === tab.id ? styles.tabActive : ''}`}
            onClick={() => setActive(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <Content />
    </div>
  )
}
