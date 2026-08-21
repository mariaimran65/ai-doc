# ADR-003 — Migration Strategy: Idempotent schema.sql

**Status:** Accepted  
**Date:** 2026-05-25  
**Author:** Maria Imran  
**Phase:** 1 — Foundations

---

## Context

The AI-Doc platform uses PostgreSQL as its database. The schema evolves across five phases — Phase 1 introduces `users` and `sessions`, Phase 3 adds `pipeline_runs`, and Phase 4 adds `documents` and `document_chunks` with a pgvector embedding column. A strategy is needed for how schema changes are applied to the database in both local development and production.

Two approaches were evaluated:

| Option | Approach | Tooling |
|--------|----------|---------|
| A | Numbered migration files applied in sequence | Alembic (SQLAlchemy's migration tool) |
| B | Single idempotent SQL file applied at container start | Plain SQL with `IF NOT EXISTS` guards |

---

## Decision

**Option B — a single idempotent `schema/schema.sql` file** is adopted as the migration strategy for this programme.

The file is mounted into the PostgreSQL container at `/docker-entrypoint-initdb.d/schema.sql`, which means it is applied automatically when the container starts with an empty data volume. Every statement uses `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, or `CREATE OR REPLACE FUNCTION/VIEW`, making the file safe to re-apply at any time without error.

This file is the **single source of truth** for the database schema. When a new phase adds tables or columns, they are appended to `schema.sql`. The file is never deleted and replaced — it grows forward.

---

## Reasoning

### Why not Alembic

Alembic is the standard migration tool in the SQLAlchemy ecosystem. It generates numbered migration files (`0001_create_users.py`, `0002_add_pipeline_runs.py`) and applies them in sequence, tracking which have run in a `alembic_version` table. This is the correct approach for a long-lived production system with multiple developers and a history of schema changes that must be auditable.

For this programme, Alembic introduces two costs that outweigh its benefits at this scale:

1. **Operational overhead.** Every schema change requires generating a migration file, reviewing the auto-generated SQL (which is often wrong for complex changes like pgvector columns or custom types), and running `alembic upgrade head`. This adds friction to a programme where schema changes are planned in advance and reviewed as part of the phase specification.

2. **Learning curve without payoff.** Alembic migration patterns are worth learning, but teaching them in Phase 1 competes with the time needed to understand OAuth, Docker Compose, SQLAlchemy async sessions, and the platform shell architecture. Adding Alembic before any of the AI engineering content is a priority inversion.

### Why idempotent SQL is sufficient here

The schema for all five phases is known in advance and documented in `schema.sql` before Phase 1 begins. There are no surprise schema changes driven by unknown requirements. This means the primary benefit of numbered migrations — being able to reason about what state the database is in at any point in history — does not apply. The state is always the same: the current contents of `schema.sql`.

The `IF NOT EXISTS` pattern provides the same practical safety guarantee: the file can be applied to an empty database, a partially-initialised database, or a fully-initialised database without error. `docker compose down -v && docker compose up` always produces a clean, correct schema.

### Forward compatibility

Each new phase appends to `schema.sql`. Existing tables are never altered in a way that would break prior phases — new columns are added as nullable, new tables have no hard dependencies on the column ordering of old tables. This is a constraint that must be respected when writing Phase 3 and Phase 4 additions.

---

## Consequences

**Benefits:**

- Zero tooling overhead. The schema is applied by PostgreSQL's own init mechanism — no Python code, no migration runner, no version table.
- The schema file is readable as documentation. A developer can open `schema.sql` and see the complete current state of the database without reconstructing it from a sequence of migration files.
- `docker compose down -v && docker compose up --build` produces a fully correct database every time, which is important during Phase 1 and Phase 2 development when the schema is still being understood.

**Accepted costs:**

- There is no rollback mechanism. If a mistake is made in `schema.sql`, the fix is to correct the file and reset the volume (`docker compose down -v`). In production (Dokploy), a schema error requires manual intervention. This is acceptable because all schema changes are reviewed before Phase advancement.
- There is no migration history. It is not possible to ask "what was the schema at the end of Phase 2?" without using `git log`. This is acceptable because `git` provides that history via the commit log on `schema.sql`.
- Alembic will need to be adopted if the platform is handed to a team that cannot tolerate the volume-reset workflow. That adoption is straightforward — `alembic init` + one baseline migration from the current `schema.sql`.

---

## Alternatives considered and rejected

**Alembic numbered migrations** — rejected for Phase 1 through 5 because the schema is known in advance, the team is one developer, and the learning overhead competes with higher-priority Phase 1 goals. Should be adopted if the project moves to a multi-developer team after Phase 5.

---

## Review notes

This decision should be revisited after Phase 5 if:

- A second developer joins and needs to apply schema changes independently.
- The production database requires a rollback mechanism for a failed schema change.
- A future phase introduces a schema change that cannot be expressed safely as an idempotent `IF NOT EXISTS` statement.

---

*ADR-003 — accepted — no further review required unless the conditions above are met.*
