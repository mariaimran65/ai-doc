# AI-Doc Platform — Project Walkthrough

**Developer:** Maria Imran  
**Repo:** github.com/mariaimran65/ai-doc  
**Live URL:** https://aidoc.talent.techsupersonic.com  
**Date:** July 2026

---

## What Was Built

A production multi-application AI platform built across 5 phases. Each phase adds a new application to the platform. The platform is a single authenticated web app with a shared navigation — adding a new app only requires one line in the registry file.

---

## Phase 1 — Foundations

**Branch:** `phase-1/foundations` | **PR:** #1

### What it does
- Google OAuth 2.0 sign-in — users authenticate with their Google account
- JWT issued as an httpOnly cookie after successful OAuth
- Authenticated shell — all routes protected, unauthenticated users redirected to login
- Dark-theme UI with a shared top nav, avatar dropdown, and app grid on the home dashboard

### Technical decisions
| Decision | Reason |
|---|---|
| Vite proxy for OAuth callback | Cookie must be scoped to the frontend domain (`aidoc.talent.techsupersonic.com`). Routing the callback through the Vite proxy ensures the `Set-Cookie` header is received in the right domain context. |
| httpOnly JWT cookie | Cannot be read by JavaScript — protects against XSS token theft. |
| Traefik labels as sole routing source | Dokploy does not inject labels for Compose stacks automatically. Labels in `docker-compose.prod.yml` are the only routing mechanism. |
| `APP_REGISTRY` typed array | Adding a new application only requires one entry — nav, home grid, and placeholder route all appear automatically. |

### Stack
- **Frontend:** React 18 + TypeScript + Vite + react-router-dom + CSS Modules
- **Backend:** FastAPI + async SQLAlchemy + asyncpg
- **Database:** PostgreSQL 16 with pgvector extension
- **Cache:** Redis
- **Reverse proxy:** Traefik (TLS via Let's Encrypt)
- **Deployment:** Dokploy on a self-hosted VM

### Schema (forward-compatible through Phase 4)
- `users` — OAuth identity, provider + provider_user_id as canonical key
- `sessions` — JWT session tokens with expiry
- `pipeline_runs` — agent execution history (Phase 3)
- `documents` + `document_chunks` — RAG storage with vector embeddings (Phase 4)
- `active_sessions` view — joined sessions + users for metrics
- `recent_signins` view — last 20 sign-in events
- `completed_pipeline_runs` view — finished agent runs with duration

---

## Phase 2 — Chat (LangChain)

**Branch:** `phase-2/langchain` | **PR:** #2

### What it does
- LangChain-powered chatbot using `claude-haiku-4-5` (Anthropic)
- Responses stream token-by-token using Server-Sent Events (SSE)
- Full conversation history sent on every request — the model has context of the whole session
- Two tools the assistant can call:
  - `web_search` — DuckDuckGo search, no API key required
  - `get_current_user` — returns the signed-in user's email

### Technical decisions
| Decision | Reason |
|---|---|
| LCEL `create_tool_calling_agent` | Cleaner than legacy AgentExecutor chains — composable, testable |
| SSE streaming | Frontend renders tokens as they arrive rather than waiting for the full response |
| Conversation history sent from frontend | Stateless backend — no session storage needed, simpler scaling |
| AgentExecutor in `run_in_executor` | Blocking call moved off the async event loop — keeps FastAPI responsive |

### Key files
- `backend/app/chat/tools.py` — tool definitions
- `backend/app/chat/chain.py` — LangChain agent setup
- `backend/app/chat/router.py` — `POST /api/chat/` SSE endpoint
- `frontend/src/pages/Chat.tsx` — streaming chat UI

---

## Phase 3 — Agents (LangGraph)

**Branch:** `phase-3/langgraph` | **PR:** #3

### What it does
- LangGraph `StateGraph` with a **supervisor pattern**
- Supervisor uses Claude structured output to decide which worker to call next
- Three specialist workers:
  - **Researcher** — DuckDuckGo web search + summarisation
  - **Coder** — Python code example generation
  - **Summariser** — synthesises all worker outputs into a final markdown answer
- Each step streams back to the UI live — you can watch the agents work in real time
- Infinite loop guard — supervisor auto-routes to summariser after 3 iterations

### Graph flow
```
START → Supervisor → Researcher → Supervisor → Coder → Supervisor → Summariser → END
```
The supervisor can skip workers it doesn't need based on the task.

### Technical decisions
| Decision | Reason |
|---|---|
| Pydantic structured output for supervisor | Guarantees the supervisor returns a valid next-worker name — no string parsing |
| Annotated steps list with `operator.add` | Each node appends to the steps list without overwriting — full execution trace preserved |
| Stream steps then final output separately | UI can show live progress without waiting for the whole run |

### Key files
- `backend/app/agents/graph.py` — StateGraph + supervisor node
- `backend/app/agents/workers.py` — researcher, coder, summariser nodes
- `backend/app/agents/router.py` — `POST /api/agents/run` SSE endpoint
- `frontend/src/pages/Agents.tsx` — execution trace panel + output panel

---

## Phase 4 — Knowledge (RAG)

**Branch:** `phase-4/rag` | **PR:** #4

### What it does
- Upload PDF or `.txt` files (drag-and-drop or file picker, max 10 MB)
- Document is extracted, split into overlapping chunks, embedded, and stored in pgvector
- Ask questions — the system retrieves the most relevant chunks and generates a grounded answer
- Can query a specific document or across all uploaded documents
- Embedding works without API credits — only answer generation needs Anthropic

### RAG pipeline
```
Upload file
    → Extract text (pypdf for PDF, UTF-8 for txt)
    → Split into 400-word chunks with 80-word overlap
    → Embed all chunks with BAAI/bge-small-en-v1.5 (384 dims, runs locally via fastembed)
    → Store in pgvector document_chunks table

Ask question
    → Embed the query with the same model
    → Cosine similarity search in pgvector (top 5 chunks)
    → Claude generates answer grounded strictly in retrieved excerpts
    → Answer streams back as SSE
```

### Technical decisions
| Decision | Reason |
|---|---|
| `fastembed` with `bge-small-en-v1.5` | Runs locally inside Docker — no API key or credits needed for embedding. Lightweight ONNX runtime, no PyTorch. |
| 384-dim vectors | Matches bge-small-en-v1.5 output — schema updated from 1536 (OpenAI default) to 384 |
| Word-based chunking with overlap | Preserves sentence context across chunk boundaries without complex sentence splitting |
| `CAST(:vec AS vector)` in SQL | asyncpg cannot parse `:param::type` syntax — explicit CAST is unambiguous |
| Grounded prompting | System prompt instructs Claude to answer only from retrieved excerpts — prevents hallucination |

### Key files
- `backend/app/knowledge/embeddings.py` — fastembed wrapper
- `backend/app/knowledge/ingest.py` — extract → chunk → embed → store
- `backend/app/knowledge/retrieval.py` — pgvector search + answer generation
- `backend/app/knowledge/router.py` — upload, list documents, ask endpoints
- `frontend/src/pages/Knowledge.tsx` — upload panel + document list + Q&A chat

---

## Phase 5 — Observability (LangSmith + Metrics)

**Branch:** `phase-5/observability` | **PR:** #5

### What it does
- **LangSmith tracing** — set 3 env vars and every LangChain/LangGraph call across Chat, Agents, and Knowledge is automatically traced at `smith.langchain.com`
- **Metrics dashboard** — platform-wide usage statistics pulled from the DB views
  - Total users, documents, chunks indexed, agent runs, completed runs, active sessions
  - Recent active sessions table (who is signed in right now)
  - Recent completed agent runs table (task, user, duration)

### LangSmith setup (already configured locally)
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your key>
LANGCHAIN_PROJECT=ai-doc
```
Zero code changes required — LangChain reads these env vars automatically.

### Key files
- `backend/app/metrics/router.py` — `GET /api/metrics/` querying DB views
- `frontend/src/pages/Metrics.tsx` — stat cards + tables

---

## Infrastructure

### Local development
```bash
cd docker
docker compose up --build
# App at http://localhost:5173
```

### Production
- Hosted on Dokploy at `env.talent.techsupersonic.com`
- Frontend: `aidoc.talent.techsupersonic.com`
- API: `api-aidoc.talent.techsupersonic.com`
- TLS via Let's Encrypt through Traefik
- Dokploy auto-deploys on push to `main`

### CI (GitHub Actions)
Every push and PR runs:
1. **Lint** — ruff (Python) + ESLint (TypeScript)
2. **Test** — pytest
3. **Build** — Docker image build
4. **Schema validation** — sqlfluff on `schema/schema.sql`

---

## What Needs to Happen to Go Fully Live

| Item | Owner | Status |
|---|---|---|
| Merge PRs #1 → #2 → #3 → #4 → #5 | Lead | Pending review |
| Add Anthropic API credits ($5 minimum) | Maria | Pending — needed for Chat, Agents, Knowledge Q&A |
| Add LangSmith key to Dokploy production env | Maria | Key generated, needs adding in Dokploy UI |

---

## Demo Script (for walkthrough)

1. **Home** — show the app grid, all 6 apps (Home, Docs, Chat, Agents, Knowledge, Metrics)
2. **Login** — sign in with Google, show the JWT cookie in DevTools
3. **Docs** — walk through Architecture diagram, ADR list, Runbook, API Reference tabs
4. **Chat** — send a message, show streaming tokens, ask "who am I?" to trigger the `get_current_user` tool
5. **Agents** — enter a task, watch the execution trace (supervisor → researcher → coder → summariser)
6. **Knowledge** — upload a PDF, show chunk count, ask a question about it
7. **Metrics** — show the counts and your own session in the active sessions table
8. **LangSmith** — open `smith.langchain.com` and show a trace from one of the above calls

---

*All code is in the `phase-5/observability` branch which includes all previous phases.*
