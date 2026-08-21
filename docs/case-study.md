# Case Study — AI-Doc

**Maria Imran · TSS AI Developer Training Programme · August 2026**

---

## What AI-Doc is

AI-Doc is a multi-application developer platform I built from scratch over ten weeks as part of the TSS training programme. It is a live, deployed system — not a tutorial exercise — that combines authentication, a relational database, a LangChain chatbot with tool use, a LangGraph multi-agent pipeline, and a retrieval-augmented generation system backed by pgvector. The platform lives at [aidoc.talent.techsupersonic.com](https://aidoc.talent.techsupersonic.com) and demonstrates what it looks like to build AI-facing features to a production standard rather than a demo standard.

The project exists to answer one specific question: can a developer who is relatively new to LLM tooling build something that a client could actually hand to a second developer to maintain? That question shaped every decision I made, from authentication to observability to test coverage.

---

## System architecture

```
Browser (React 18 + Vite)
     │  HTTPS
     ▼
Traefik (reverse proxy + TLS via Let's Encrypt)
     │
     ▼
FastAPI :8000          ←→  PostgreSQL 16 + pgvector
     │                 ←→  Redis 7
     ├── /auth/*            Google OAuth 2.0, httpOnly JWT cookies
     ├── /chat/*            LangChain LCEL chain, Redis-backed message history
     ├── /agents/*          LangGraph StateGraph, supervisor + worker nodes
     ├── /knowledge/*       LangChain RAG: document ingest + retrieval
     └── /metrics/*         Request counts, latency, model usage
```

The frontend is a single-page React application with a persistent sidebar shell. Authentication happens once at the shell level — Google OAuth sets an httpOnly JWT cookie, and every subsequent API request carries it automatically. The four main applications (Chat, Agents, Knowledge, Metrics) are lazy-loaded pages within that shell; they share auth and database infrastructure without any changes to either.

The backend is a FastAPI service. All database access is async via SQLAlchemy and asyncpg. LangChain and LangGraph calls that use synchronous drivers (PGVector uses psycopg2 internally) are wrapped in `run_in_executor` to keep the event loop unblocked. Redis provides chat message persistence. pgvector stores document embeddings.

---

## Key engineering decisions

### 1. Claude instead of GPT

The brief specified the OpenAI API. I switched to Anthropic's Claude (Haiku for inference, the same model across all endpoints) for two reasons: I had access to the API key, and the Haiku model is meaningfully cheaper per token than GPT-3.5-turbo for the same capability level at this task. The LangChain abstractions (`ChatAnthropic` vs `ChatOpenAI`) made this a one-line change, which itself was a useful thing to learn — the LCEL layer genuinely decouples prompt logic from provider.

I should have written this up as an ADR at the time. I did not, and the lead correctly flagged it. The lesson: when you deviate from a brief, document it immediately. Not because you need permission, but because the decision gets harder to reconstruct later, and a client doing a code review will see the deviation without the reasoning behind it.

### 2. FastEmbeddings instead of OpenAI embeddings

The RAG phase called for an embedding model. I used FastEmbed with the BAAI/bge-small-en-v1.5 model (384-dimensional vectors) rather than OpenAI's text-embedding-ada-002 (1536-dimensional). The reasoning: FastEmbed runs locally, so there is no per-call cost for embedding during ingest or retrieval, and the bge-small model benchmarks well for semantic similarity despite being much smaller. The tradeoff is that the embedding space is different — documents embedded with one model cannot be retrieved with another, so switching models would require re-embedding the entire corpus. I made this decision once and stuck with it, which is the right call.

### 3. RedisChatMessageHistory over in-memory history

My first implementation of the chat memory passed conversation history from the frontend on every request. This meant history was held in the browser, was lost on page refresh, and was invisible to the server. The lead identified this as a blocker. I rebuilt it using LangChain's `RedisChatMessageHistory` wrapped in `RunnableWithMessageHistory`. The history is now keyed by user ID, stored in Redis with a 7-day TTL, and loaded automatically before each chain invocation. The server owns the conversation state, which is the correct architecture for any multi-session or multi-device scenario.

The rebuild was not technically complex, but it required understanding that `RunnableWithMessageHistory` expects the executor to accept `input` and return `output` as top-level keys — not the message list structure the frontend was passing. Getting that mapping right (the `input_messages_key` and `history_messages_key` parameters) took more time than the implementation itself.

### 4. Keeping the documents table alongside PGVector's tables

LangChain's PGVector creates its own schema: `langchain_pg_collection` and `langchain_pg_embedding`. I also kept my own `documents` table for the document listing UI. These two stores serve different purposes: PGVector stores the chunked, embedded content for retrieval; the `documents` table stores document metadata (filename, upload time, chunk count) for display. I link them by storing `document_id` in PGVector chunk metadata, which allows retrieval to be filtered to a specific document when the user asks a question about one file rather than the whole corpus.

This felt like over-engineering at the time. In retrospect it is the right separation — the UI concern (list of documents) and the retrieval concern (chunk store) are genuinely different, and mixing them would have made both harder to reason about.

### 5. Mocked tests over integration tests for the AI-facing code

The brief asked for tests on the chat, agent, and RAG code. I wrote unit tests with mocked LLM calls rather than integration tests that hit the Anthropic API. The reasons: integration tests are slow, incur API cost on every CI run, and are non-deterministic — the same input does not always produce the same output from a language model. Mocked tests are fast and deterministic and verify what matters: that the auth guards work, that the SSE streaming format is correct, that errors surface in the stream rather than as 500s, and that the right functions are called with the right arguments.

The tradeoff is that mocked tests do not catch prompt regressions or model behaviour changes. That is what the eval harness is for — a separate, on-demand workflow that makes real API calls and scores responses with an LLM judge.

---

## What I learned

The thing that shifted most is how I think about the difference between code that works and code that can be operated. Before this project, my measure of done was: does it produce the right output when I run it? By the end of Phase 5, done means something more demanding: does it produce the right output reliably, is the failure mode visible when it does not, and can someone else understand what it is doing from the observability data alone?

That shift happened concretely during the LangSmith tracing work. Once I could see each chain step in the trace — what went into the retriever, what chunks came back, what the model was given, what it returned — I stopped trusting my local intuitions about what the system was doing and started reading the actual evidence. That is a different way of working with LLM systems, and I think it is the right one.

The other thing I underestimated is how much design decisions compound. The choice to use httpOnly cookies for JWT storage (rather than localStorage) seemed like a minor preference in Phase 1. By Phase 4, it meant I had a working cross-subdomain auth story, a natural session TTL, and no frontend token management code. None of that was planned — it fell out of one decision made early on. Good early decisions reduce friction later. Bad early decisions become technical debt that you carry through every subsequent phase.

What I would change: I would document decisions at the moment I make them, not retrospectively. The ADRs I wrote for this case study were reconstructed from memory and git log. An ADR written at decision time captures the context you actually had — the alternatives you rejected, the constraints that existed, the thing you were uncertain about. A retrospective ADR captures the post-hoc rationalisation, which is a different and less useful thing.

---

## What I would add with more time

- **Rate limiting** on the LLM-calling endpoints. Currently, any authenticated user can send unlimited requests. This is the highest-priority security gap identified in the OWASP review.
- **Chunk-level sanitisation** before RAG injection. Retrieved document chunks are placed directly in the LLM's context. A document containing adversarial instructions would be injected without any inspection.
- **Streaming from the LangGraph pipeline.** The agents endpoint currently buffers the full pipeline result and then streams it. True streaming would yield each node's output as it is produced, which would improve perceived latency significantly on long-running pipelines.
- **A second evaluation run** after the improvements identified in Phase 5. The eval harness documents a before score. I did not have time to make targeted improvements and run it again to produce the after score the brief asks for.

---

*AI-Doc — TSS Developer Training Programme — Phase 5 complete*
