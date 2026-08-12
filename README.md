# AI-Doc

A personal developer platform and AI-engineering portfolio. You build this application phase by phase, each one adding a new capability to the same codebase. The platform is designed to grow without a fixed end point — new phases are added to the programme as you progress, and each phase you complete makes the next one faster because the foundation is your own work and you understand every part of it.

## What the platform is

AI-Doc is a multi-application platform. The outer shell handles authentication once, and every application registered inside it shares that login without any changes to the auth layer. Each application has its own navigation, its own sub-menus, and its own URL namespace. The platform grows by adding applications — you never restructure the shell to accommodate a new tool, you simply register the new one.

## Prerequisites

| Tool | Link | Required from |
|---|---|---|
| Git | git-scm.com | Phase 1 |
| GitHub account | github.com | Phase 1 |
| Docker Desktop | docker.com | Phase 1 |
| pgAdmin | pgadmin.org | Phase 1 |
| Dokploy access | TSS server | Phase 1 |
| Claude.ai | claude.ai | Phase 1 |
| n8n | n8n.io | Phase 3 |

## How to begin

Read `00-overview.md` completely before touching anything else. It explains the mindset, the SDLC discipline, and the AI-Driven Development protocol that every phase assumes you have absorbed. Resources who skip it consistently get stuck in Phase 1 for the wrong reasons.

## Current phases

```
01-phase-1-foundations.md     Weeks 1–2   Platform shell, SSO, database, Docker, CI/CD
02-phase-2-langchain.md       Weeks 3–5   LangChain core, LCEL, chatbot, tools, LangServe
03-phase-3-agents.md          Weeks 5–7   LangGraph, multi-agent, supervisor pattern, n8n
04-phase-4-rag.md             Weeks 7–9   LangChain retrieval, pgvector, RAG, Redis memory
05-phase-5-production.md      Weeks 9–10  LangSmith, OWASP, evals, case study, presentation
```

New phases are added here as the programme grows. Each extends the same codebase — nothing already built is discarded.

## Live site

**[https://aidoc.talent.techsupersonic.com/](https://aidoc.talent.techsupersonic.com/)**

Deployed via Dokploy from the `main` branch. PRs merge in phase order (1 → 5); the live site updates automatically on each merge.

## Tech stack

PostgreSQL · pgvector · Redis · Docker · GitHub Actions · FastAPI · React 18 + TypeScript + Vite · LangChain · LangGraph · LangSmith · Claude API (Anthropic)

## Phase 5 status

| Area | Status | Notes |
|---|---|---|
| LangSmith tracing | Done | `LANGCHAIN_TRACING_V2=true` wired in Docker env |
| Metrics endpoint (`/metrics`) | Done | Request counts, latency, model usage tracked in DB |
| Redis chat memory | Done | `RedisChatMessageHistory` keyed by user_id, 7-day TTL |
| LangChain RAG tools | Done | `PyPDFLoader`, `RecursiveCharacterTextSplitter`, `PGVector`, LCEL chain |
| Tests — chat, agents, knowledge | Done | `test_chat.py`, `test_agents.py`, `test_knowledge.py` added |
| OWASP security review | Not done | Identified as needed; not implemented this phase |
| Evals / LangSmith datasets | Not done | No eval harness written yet |
| Case study write-up | Not done | Deferred — content for next review |

---

*AI-Doc — TSS Developer Training Programme*
*Version 1.0 — May 2026*
