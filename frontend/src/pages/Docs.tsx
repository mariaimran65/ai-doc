import React, { useState } from 'react'
import styles from './Docs.module.css'

type Tab = 'architecture' | 'decisions' | 'runbook' | 'api' | 'security' | 'case-study'

const TABS: { id: Tab; label: string }[] = [
  { id: 'architecture', label: 'Architecture' },
  { id: 'decisions', label: 'Decisions' },
  { id: 'runbook', label: 'Runbook' },
  { id: 'api', label: 'API Reference' },
  { id: 'security', label: 'Security' },
  { id: 'case-study', label: 'Case Study' },
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

// ---------------------------------------------------------------------------
// Security — OWASP LLM Top 10 review
// ---------------------------------------------------------------------------

const OWASP_ITEMS = [
  {
    id: 'LLM01',
    title: 'Prompt Injection',
    risk: 'medium',
    summary: 'Malicious input or retrieved document chunk overrides system prompt behaviour.',
    scenario:
      'A PDF uploaded to the Knowledge app contains hidden instructions. When retrieved as a RAG chunk, the instruction is injected into the LLM context and may be followed.',
    mitigations: [
      'System prompt is injected before any user content in every chain.',
      'Retrieved chunks are placed in the human message, structurally separated from instruction-bearing parts of the prompt.',
      'RAG prompt constrains the model to answer strictly from document excerpts.',
      'Uploaded file types are restricted to PDF and plain text.',
    ],
    residual: 'Medium — chunk-level sanitisation not yet implemented.',
  },
  {
    id: 'LLM02',
    title: 'Insecure Output Handling',
    risk: 'low',
    summary: 'LLM output containing HTML or script tags reaches the browser or database without validation.',
    scenario:
      'Agent pipeline returns a string containing <script>alert(1)</script>. If the frontend rendered this as innerHTML, it would execute in the user\'s browser.',
    mitigations: [
      'React JSX renders all content as text by default — HTML entities are escaped, not executed.',
      'SSE tokens are JSON-encoded before transmission, escaping special characters.',
      'Agent output is ephemeral — it is not persisted to the database in any current flow.',
    ],
    residual: 'Low — any future feature that persists LLM output must treat it as untrusted input.',
  },
  {
    id: 'LLM08',
    title: 'Excessive Agency',
    risk: 'low',
    summary: 'The agent has more tool access or autonomy than necessary; misbehaviour causes disproportionate damage.',
    scenario:
      'A future version adds a database-write tool to the agent pipeline. An adversarial task or prompt injection could cause the agent to overwrite platform data.',
    mitigations: [
      'Current tools are read-only: DuckDuckGo search only. No write access to the database.',
      'Tool list is explicitly defined in code — no dynamic tool loading.',
      'LangGraph supervisor routes to a fixed set of known workers.',
      'LangSmith tracing records every tool call for audit.',
    ],
    residual: 'Low — each new tool added must be reviewed for blast radius before inclusion.',
  },
  {
    id: 'LLM04',
    title: 'Model Denial of Service',
    risk: 'medium',
    summary: 'Large or repeated requests cause high-latency, high-cost LLM calls.',
    mitigations: ['Document upload capped at 10 MB at the API level.'],
    residual: 'Medium — no per-user rate limiting on chat or agent endpoints yet.',
  },
  {
    id: 'LLM06',
    title: 'Sensitive Information Disclosure',
    risk: 'low',
    summary: 'LLM reveals another user\'s document content or system secrets.',
    mitigations: [
      'PGVector retrieval filtered by user_id — one user\'s chunks cannot appear in another\'s context.',
      'API keys and secrets are in env vars only, never placed in model context.',
    ],
    residual: 'Low.',
  },
]

const RISK_COLORS: Record<string, string> = {
  low: styles.riskLow,
  medium: styles.riskMedium,
  high: styles.riskHigh,
}

function Security() {
  const [open, setOpen] = useState<string | null>(null)
  return (
    <div className={styles.body}>
      <p className={styles.sectionTitle}>OWASP LLM Top 10 — Security Assessment</p>
      <p className={styles.archNote} style={{ marginBottom: 20 }}>
        Full report in <code>docs/security-review.md</code>. Three risks assessed in detail below.
      </p>
      <div className={styles.owaspList}>
        {OWASP_ITEMS.map(item => (
          <div key={item.id} className={styles.owaspCard}>
            <button
              className={styles.owaspHeader}
              onClick={() => setOpen(open === item.id ? null : item.id)}
            >
              <span className={styles.owaspId}>{item.id}</span>
              <span className={styles.owaspTitle}>{item.title}</span>
              <span className={`${styles.riskBadge} ${RISK_COLORS[item.risk]}`}>{item.risk}</span>
              <span className={styles.chevron}>{open === item.id ? '▲' : '▼'}</span>
            </button>
            {open === item.id && (
              <div className={styles.owaspBody}>
                <p className={styles.owaspSummary}>{item.summary}</p>
                {item.scenario && (
                  <>
                    <p className={styles.owaspLabel}>Attack scenario</p>
                    <p className={styles.owaspText}>{item.scenario}</p>
                  </>
                )}
                {item.mitigations && item.mitigations.length > 0 && (
                  <>
                    <p className={styles.owaspLabel}>Mitigations implemented</p>
                    <ul className={styles.owaspUl}>
                      {item.mitigations.map((m, i) => <li key={i}>{m}</li>)}
                    </ul>
                  </>
                )}
                <p className={styles.owaspLabel}>Residual risk</p>
                <p className={styles.owaspText}>{item.residual}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Case Study
// ---------------------------------------------------------------------------

const CASE_STUDY_SECTIONS = [
  {
    heading: 'What AI-Doc is',
    body: 'AI-Doc is a multi-application developer platform built from scratch over ten weeks as part of the TSS training programme. It is a live, deployed system — not a tutorial exercise — that combines authentication, a relational database, a LangChain chatbot with tool use, a LangGraph multi-agent pipeline, and a retrieval-augmented generation system backed by pgvector. The platform lives at aidoc.talent.techsupersonic.com and demonstrates what it looks like to build AI-facing features to a production standard rather than a demo standard.',
  },
  {
    heading: 'Claude instead of GPT',
    body: 'The brief specified the OpenAI API. I switched to Anthropic\'s Claude (Haiku) for two reasons: API access and cost — Haiku is cheaper per token than GPT-3.5-turbo for the same capability at this task. LangChain\'s abstractions made this a one-line change, which itself was a useful thing to learn — the LCEL layer genuinely decouples prompt logic from provider. I should have documented this as an ADR at the time. The lesson: when you deviate from a brief, record the reasoning immediately.',
  },
  {
    heading: 'Redis chat memory',
    body: 'My first implementation passed conversation history from the frontend on every request. History was held in the browser, lost on refresh, and invisible to the server. I rebuilt it using LangChain\'s RedisChatMessageHistory wrapped in RunnableWithMessageHistory. History is now keyed by user ID, stored in Redis with a 7-day TTL, and loaded automatically before each chain invocation. The server owns the conversation state — the correct architecture for any multi-session scenario. Getting the input_messages_key and history_messages_key mapping right took more time than the implementation itself.',
  },
  {
    heading: 'Mocked tests over integration tests',
    body: 'I wrote unit tests with mocked LLM calls rather than integration tests that hit the API. Integration tests are slow, cost money on every CI run, and are non-deterministic — the same input does not always produce the same output from a language model. Mocked tests verify what matters: auth guards work, SSE format is correct, errors surface in the stream rather than as 500s, and the right functions are called with the right arguments. Prompt regression testing is handled by the separate eval harness, which runs on demand.',
  },
  {
    heading: 'What changed in how I think',
    body: 'The shift that stuck most is the difference between code that works and code that can be operated. Once I could see each chain step in LangSmith — what went into the retriever, what chunks came back, what the model was given, what it returned — I stopped trusting my local intuitions and started reading the actual evidence. That is a different way of working with LLM systems, and I think it is the right one. Good early decisions also compound: the choice to use httpOnly cookies in Phase 1 meant working cross-subdomain auth by Phase 4 with no extra effort.',
  },
]

function CaseStudy() {
  return (
    <div className={styles.body}>
      <p className={styles.sectionTitle}>Case Study</p>
      <p className={styles.archNote} style={{ marginBottom: 24 }}>
        Full document in <code>docs/case-study.md</code>.
      </p>
      <div className={styles.caseStudyList}>
        {CASE_STUDY_SECTIONS.map(section => (
          <div key={section.heading} className={styles.caseCard}>
            <p className={styles.caseHeading}>{section.heading}</p>
            <p className={styles.caseBody}>{section.body}</p>
          </div>
        ))}
      </div>
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
    security: Security,
    'case-study': CaseStudy,
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
