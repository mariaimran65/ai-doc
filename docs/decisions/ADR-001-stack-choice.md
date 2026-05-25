# ADR-001 — Stack choice: React + FastAPI

**Status:** Accepted  
**Date:** 2026-05-22  
**Author:** Maria Imran  
**Phase:** 1 — Foundations

---

## Context

The AI-Doc platform requires a frontend and a backend. The frontend must support a multi-application shell with shared navigation, per-application sub-menus, and client-side routing. The backend must expose REST API endpoints, handle OAuth callbacks, manage PostgreSQL sessions, and serve LangChain chains via LangServe in Phase 2.

Three options were evaluated:

| Option | Frontend | Backend |
|--------|----------|---------|
| A | Next.js (full-stack) | — (built-in API routes) |
| B | React | FastAPI (Python) |
| C | Vue or Svelte | FastAPI (Python) |

The decision needed to account for the full programme arc — not just Phase 1 infrastructure, but Phases 2 through 5, which introduce LangChain, LangGraph, LangServe, pgvector, LangSmith, and a production evaluation framework. All of these are Python-native libraries.

---

## Decision

**Option B — React with FastAPI** is adopted as the stack for this project.

React handles the frontend shell, routing, and all UI. FastAPI handles authentication, database access, the LangChain integration, and the LangServe API layer. The two communicate over HTTP via a REST API. Both services run in Docker and are defined in the same Compose file.

---

## Reasoning

### Why FastAPI over Next.js API routes

LangChain, LangGraph, LangServe, LangSmith, and pgvector are all Python-native. Running the AI layer inside a Node.js backend (Next.js API routes) would require either calling out to a Python subprocess or running a separate Python service regardless — which reintroduces the split-service complexity without the benefits of a proper Python backend.

FastAPI was chosen over Flask and Django for three reasons. First, it has native async support, which is essential for streaming LangChain responses without blocking. Second, LangServe (Phase 2) wraps FastAPI directly — `add_routes(app, chain, path="/api/chat")` is a single line that works because LangServe is built on top of FastAPI. Third, FastAPI's automatic OpenAPI schema generation produces the API Reference documentation in the Docs application with no extra work.

### Why React over Vue or Svelte

React is the frontend framework most commonly found in international AI product teams. Choosing React means the platform demonstrates a stack that transfers directly to client engagements without translation. Vue and Svelte are reasonable alternatives but would require prior strong experience to use at the pace this programme demands; they would not provide additional benefit over React for any of the AI-specific work in Phases 2 through 5.

### Why not Next.js full-stack

Next.js is a strong option for frontend-first developers and would reduce the initial setup burden in Phase 1. It was rejected because its server-side rendering model adds complexity to the multi-application shell architecture without meaningful benefit — the shell is an authenticated SPA, not a public-facing content site where SSR improves SEO or time-to-first-byte. More importantly, the LangChain layer in Phases 2 through 5 is Python-only; using Next.js API routes as the backend would eventually require a separate Python service anyway, turning a two-service architecture into three without a clean separation of concerns.

---

## Consequences

**Accepted costs:**

- Two separate services to run, configure, and deploy (React dev server + FastAPI). The Docker Compose file manages this locally; Dokploy manages it in production.
- CORS must be configured correctly between the React frontend and the FastAPI backend. This is documented in the Runbook.
- The React build must be served correctly in production — either by FastAPI serving the static build, or by a separate static file service. This decision is documented in ADR-002 (Docker setup).

**Benefits realised across all phases:**

- The Python backend is the natural home for every AI library introduced in Phases 2 through 5 — no bridging, no subprocesses, no language mismatch.
- LangServe slots directly into the FastAPI app in Phase 2 with a single call.
- FastAPI's async support handles streaming LLM responses cleanly in Phase 2.
- The split architecture makes it straightforward to scale the AI backend independently of the frontend in Phase 5.
- The React frontend is fully decoupled from the backend — it only depends on the API contract, which means the backend can be tested independently.

---

## Alternatives considered and rejected

**Next.js full-stack** — rejected because SSR adds complexity with no meaningful benefit for an authenticated SPA, and the Python AI layer would eventually require a separate service regardless.

**Vue + FastAPI** — rejected because the Vue learning curve would slow Phase 1 delivery without providing any advantage in the AI-engineering phases. Would be a valid choice with prior Vue experience.

**Svelte + FastAPI** — rejected for the same reason as Vue. Svelte's smaller ecosystem also reduces the availability of compatible component libraries.

---

## Review notes

This decision should be revisited if:

- A future phase requires server-side rendering for a public-facing application registered in the shell.
- The team grows to include developers with strong Vue or Svelte backgrounds and no React experience.

Neither condition is expected in the current programme scope.

---

*ADR-001 — accepted — no further review required unless the conditions above are met.*
