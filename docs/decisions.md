# Architecture Decision Records

This file is the living log of every significant architectural decision made during the development of AI-Doc. A decision belongs here if it involved a genuine choice between alternatives, if the reasoning is not visible from the code alone, or if someone reading the codebase six months from now would reasonably wonder why a particular approach was taken.

The goal is not to document every line of code. It is to capture the context and reasoning behind choices that are difficult to reverse or that carry meaningful tradeoffs — so that future contributors, including yourself, can understand and build on the decisions rather than inadvertently undoing them.

---

## Template

Copy this template for each new ADR. Number them sequentially.

```
## ADR-XXX — [Short descriptive title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Superseded by ADR-XXX

### Context
One paragraph. What problem were you solving? What constraints were in play?
What made this a non-trivial decision rather than an obvious one?

### Options considered
A brief description of two or more approaches you evaluated.

### Decision
What did you choose and why? Reference the options above by name.

### Consequences
What becomes easier as a result of this decision?
What becomes harder or more constrained?
What are the known risks or tradeoffs you are accepting?
```

---

## ADR-001 — Stack choice

**Date:** [Fill in when written]
**Status:** Accepted

### Context
[Describe what you evaluated: Next.js alone, React plus FastAPI, Vue plus FastAPI, or another combination. Describe the constraints — your existing experience, the role you are targeting, the complexity tradeoffs between a monolith and a split stack. This is your first ADR and it sets the standard for the ones that follow.]

### Options considered
[Fill in the options you genuinely evaluated.]

### Decision
[Fill in what you chose and why.]

### Consequences
[Fill in what becomes easier, what becomes harder, and what risks you are accepting.]

---

## ADR-002 — OAuth provider and flow design

**Date:** [Fill in]
**Status:** Accepted

### Context
[Describe why you chose Google or GitHub OAuth rather than username-password authentication. Describe what the authorisation code grant type is and why the code exchange happens server-side. Describe what the state parameter does and why omitting it is a vulnerability.]

### Options considered
[Fill in]

### Decision
[Fill in]

### Consequences
[Fill in]

---

## ADR-003 — Database migration strategy

**Date:** [Fill in]
**Status:** Accepted

### Context
[Describe the two primary options: a single idempotent schema.sql file using CREATE TABLE IF NOT EXISTS throughout, versus a numbered migrations folder managed by Alembic (Python) or Drizzle (TypeScript). Describe the operational difference: the idempotent file is simple and safe but loses the history of incremental changes; numbered migrations preserve history but require a migration runner and more discipline to maintain.]

### Options considered
[Fill in]

### Decision
[Fill in]

### Consequences
[Fill in]

---

## ADR-004 — Multi-application shell architecture

**Date:** [Fill in]
**Status:** Accepted

### Context
[Describe the platform architecture you designed in Phase 1: the outer shell handling authentication and top-level navigation, each application owning its own sub-navigation and routes, and the single-registration-point pattern for adding new applications. Explain why this structure was chosen over a simpler single-page application or a separate deployment per tool.]

### Options considered
[Fill in]

### Decision
[Fill in]

### Consequences
[Fill in]

---

## ADR-005 — LLM provider: Claude Haiku instead of OpenAI GPT

**Date:** 2026-07-10  
**Status:** Accepted  
**Full record:** [docs/decisions/ADR-005-llm-provider.md](decisions/ADR-005-llm-provider.md)

### Context
The brief offered a choice of LLM provider (`langchain-anthropic` or `langchain-openai`). An Anthropic API key was available; an OpenAI key was not. LangChain abstracts both providers identically at the application layer.

### Decision
Claude Haiku (`claude-haiku-4-5-20251001`) via `langchain-anthropic` is used across all phases. Switching providers is a one-line change in each chain file — no other application logic would need to change.

### Consequences
Lower cost per request during development. No OpenAI account setup required. Risk: dependency on Anthropic API availability (same risk as OpenAI). Model name includes a date suffix that must be updated when Anthropic deprecates a version.

---

## ADR-006 — Embedding model: FastEmbed (BAAI/bge-small-en-v1.5, 384 dims)

**Date:** 2026-07-10  
**Status:** Accepted  
**Full record:** [docs/decisions/ADR-006-embedding-model.md](decisions/ADR-006-embedding-model.md)

### Context
The brief specified `OpenAIEmbeddings` with `text-embedding-3-small` (1536-dimensional). The brief also explicitly required an ADR if a different model was used: *"If you are using a different embedding model, the dimension must match exactly — document this in an ADR."*

### Decision
FastEmbed with BAAI/bge-small-en-v1.5 (384-dimensional, local inference) is used instead. The `embedding` column in `document_chunks` was changed from `VECTOR(1536)` to `VECTOR(384)`. The embedding model used at upload time and at query time must always be the same.

### Consequences
No API cost or key required for embedding. Embedding works offline. Retrieval quality is comparable for English technical documents. Switching to OpenAIEmbeddings later requires re-ingesting all documents (vectors are dimension-incompatible).

---

*Add new ADRs below this line as the project progresses. Each phase requires at least one new ADR. By Phase 5, the ADR log should contain a minimum of ten records covering all major decisions across the system.*
