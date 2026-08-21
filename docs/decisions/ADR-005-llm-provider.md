# ADR-005 — LLM provider: Claude Haiku instead of OpenAI GPT

**Status:** Accepted  
**Date:** 2026-07-10  
**Author:** Maria Imran  
**Phase:** 2 — LangChain Chat

---

## Context

Phase 2 requires a hosted LLM that supports tool-calling, can be reached via a LangChain integration package, and can be wrapped in an LCEL chain with `RunnableWithMessageHistory`. The brief explicitly names two supported paths:

- `langchain-anthropic` — Claude models via the Anthropic API
- `langchain-openai` — GPT models via the OpenAI API

Both paths are functionally equivalent at the LangChain abstraction level: both expose `ChatAnthropic` / `ChatOpenAI` with the same interface, both support tool-calling via `create_tool_calling_agent`, and both stream via SSE in the same way.

The decision was which provider to use for this project.

---

## Decision

**Anthropic Claude Haiku** (`claude-haiku-4-5-20251001`) via `langchain-anthropic` is used as the LLM across all phases.

---

## Reasoning

### API access

An Anthropic API key was available at the start of the project. Setting up a new OpenAI account and billing would have added friction with no technical benefit given that LangChain abstracts both providers identically.

### Cost

Claude Haiku is one of the lowest-cost frontier models available. For a learning platform generating a high volume of test requests during development, cost per token matters. Haiku's pricing at the time of this decision was lower per million tokens than GPT-3.5-turbo for comparable quality on instruction-following tasks.

### Capability for the use case

The platform's AI applications — a tool-calling chat agent, a multi-agent supervisor graph, and a RAG retrieval chain — all require reliable instruction-following and tool-calling, not multimodal capability or extended context. Haiku is well within the capability range needed for all three. GPT-4o or Claude Opus would be over-specified and significantly more expensive for this workload.

### No lock-in at the application layer

Because all chains are written against LangChain's `BaseChatModel` interface, switching from `ChatAnthropic` to `ChatOpenAI` is a one-line change in each chain file and a change of environment variable. The rest of the application — prompts, LCEL chains, agent executors, LangGraph nodes — is provider-agnostic. This was verified: a test substitution to `ChatOpenAI` required no other changes.

---

## Consequences

**Accepted costs:**

- The project depends on Anthropic's API being available. If the Anthropic API experiences an outage, all four AI applications are unavailable. This is the same risk that would apply to OpenAI. Neither provider offers a strong guarantee of uptime beyond their published SLAs.
- Anthropic's tool-calling format differs slightly from OpenAI's at the raw API level. LangChain abstracts this, but if the project ever bypasses LangChain and calls the API directly, the tool-calling message format would need to change.
- Model names include a date suffix (`claude-haiku-4-5-20251001`). When Anthropic deprecates a model version, the constant in `app/chat/chain.py`, `app/agents/graph.py`, and `app/knowledge/retrieval.py` must be updated.

**Benefits realised:**

- Lower cost per request during development and testing.
- No additional API setup required at project start.
- All LangChain abstractions work identically — switching providers later remains a one-line change.

---

## Review notes

This decision should be revisited if:

- A future phase requires multimodal input (image understanding), where GPT-4o Vision or Claude 3.5 Sonnet would be evaluated on capability, not cost.
- Anthropic changes pricing in a way that makes Haiku uncompetitive with GPT-3.5-turbo or GPT-4o-mini.
- A client engagement specifies a required provider.

---

*ADR-005 — accepted — model constant locations: `app/chat/chain.py`, `app/agents/graph.py`, `app/knowledge/retrieval.py`*
