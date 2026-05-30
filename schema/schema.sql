-- AI-Doc — Database Schema
-- Version 1.0 — Phase 1 initial schema, forward-compatible through Phase 4
--
-- Apply with:
--   psql -h localhost -p 5432 -U your_db_user -d your_db_name -f schema/schema.sql
--
-- This file is idempotent — safe to run multiple times.
-- All statements use IF NOT EXISTS or CREATE OR REPLACE.
-- Tables introduced in later phases are included here with IF NOT EXISTS guards
-- so the schema file stays the single source of truth for the entire programme.

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------

-- pgcrypto provides gen_random_uuid() for UUID primary keys.
-- UUIDs are preferred over auto-incrementing integers for all user-facing IDs.
-- They do not leak record counts, are globally unique, and are safe in URLs.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- pgvector adds the vector column type and cosine similarity search.
-- Requires the pgvector/pgvector:pg16 Docker image (or equivalent version).
-- Used from Phase 4 onward; activating it here in Phase 1 keeps the schema
-- file as a single source of truth without requiring changes later.
CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- Function: auto-update updated_at
-- ---------------------------------------------------------------------------

-- Attached as a trigger to every table with an updated_at column.
-- The database maintains the timestamp, not the application code.
-- Application code can be bypassed; the database trigger cannot.
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- Table: users
-- Phase 1
-- ---------------------------------------------------------------------------

-- The canonical identity key is (provider, provider_user_id), not email.
-- The same email address can exist independently across different OAuth providers
-- and represent genuinely separate accounts. The unique constraint enforces this.
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    name TEXT,
    provider TEXT NOT NULL CHECK (provider IN ('google', 'github')),
    provider_user_id TEXT NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_users_provider_id UNIQUE (provider, provider_user_id)
);

CREATE OR REPLACE TRIGGER users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ---------------------------------------------------------------------------
-- Table: sessions
-- Phase 1
-- ---------------------------------------------------------------------------

-- Active user sessions. Each row represents a session token issued after
-- successful OAuth authentication. The expires_at column is enforced by
-- application logic — expired sessions are rejected at the middleware level.
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE TRIGGER sessions_updated_at
BEFORE UPDATE ON sessions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions (token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at);

-- ---------------------------------------------------------------------------
-- Table: pipeline_runs
-- Phase 3
-- ---------------------------------------------------------------------------

-- Each row represents one execution of the LangGraph agent pipeline.
-- The trace column stores the complete run trace as JSON — the supervisor
-- decision, which workers were called in what order, and each worker's output.
-- This is the data source for the Run History page in the Agents application.
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    task TEXT NOT NULL,                    -- the task description that triggered the run
    status TEXT NOT NULL DEFAULT 'running'
    CHECK (status IN ('running', 'completed', 'failed')),
    final_output TEXT,                                    -- the synthesised output from the supervisor
    trace JSONB,                                   -- full run trace: worker results, routing decisions
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE TRIGGER pipeline_runs_updated_at
BEFORE UPDATE ON pipeline_runs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Index: the Run History page retrieves runs per user in reverse chronological order
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_user_id ON pipeline_runs (user_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started ON pipeline_runs (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs (status);

-- ---------------------------------------------------------------------------
-- Table: documents
-- Phase 4
-- ---------------------------------------------------------------------------

-- One row per uploaded document. The full extracted text is stored here.
-- Individual chunks are stored in document_chunks with their embeddings.
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    source_name TEXT NOT NULL,                    -- original filename
    raw_text TEXT NOT NULL,                    -- full extracted text from the document
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE TRIGGER documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents (user_id);

-- ---------------------------------------------------------------------------
-- Table: document_chunks
-- Phase 4
-- ---------------------------------------------------------------------------

-- One row per chunk of a document. Each chunk has a vector embedding.
-- The embedding dimension is 1536, matching OpenAI text-embedding-3-small.
-- If using a different embedding model, the dimension must match exactly.
-- Changing the dimension after data has been inserted requires dropping
-- and recreating the column — document this choice in an ADR and commit to it.
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,                   -- position of this chunk within the document
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),                           -- the semantic representation of chunk_text
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ivfflat index for approximate nearest-neighbour cosine similarity search.
-- ivfflat is chosen over hnsw for lower memory overhead at moderate dataset sizes
-- (up to a few hundred thousand rows). For larger datasets, hnsw provides better
-- query performance at the cost of higher memory use. See ADR for the full tradeoff.
-- The lists parameter (100) controls the number of clusters. A common starting
-- point is sqrt(number of rows), revisited when the table exceeds 100k rows.
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id
ON document_chunks (document_id);

-- ---------------------------------------------------------------------------
-- Views
-- ---------------------------------------------------------------------------

-- Active sessions joined with user details.
-- Used by the platform for session validation and by the agent's user tools.
CREATE OR REPLACE VIEW active_sessions AS
SELECT
    s.id AS session_id,
    s.user_id,
    u.email,
    u.name,
    u.provider,
    s.created_at AS signed_in_at,
    s.expires_at
FROM sessions AS s
INNER JOIN users AS u ON s.user_id = u.id
WHERE s.expires_at > now()
ORDER BY s.created_at DESC;

-- The 20 most recent sign-in events.
-- Used by the Phase 2 get_recent_signins tool.
CREATE OR REPLACE VIEW recent_signins AS
SELECT
    u.id AS user_id,
    u.email,
    u.name,
    u.provider,
    s.created_at AS signed_in_at
FROM sessions AS s
INNER JOIN users AS u ON s.user_id = u.id
ORDER BY s.created_at DESC
LIMIT 20;

-- Completed pipeline runs with their final output, ordered most recent first.
-- Used by the Run History page in the Agents application.
CREATE OR REPLACE VIEW completed_pipeline_runs AS
SELECT
    r.id,
    r.user_id,
    u.name AS triggered_by,
    r.task,
    r.final_output,
    r.trace,
    r.started_at,
    r.completed_at,
    extract(EPOCH FROM (r.completed_at - r.started_at)) AS duration_seconds
FROM pipeline_runs AS r
INNER JOIN users AS u ON r.user_id = u.id
WHERE r.status = 'completed'
ORDER BY r.completed_at DESC;

-- ---------------------------------------------------------------------------
-- Helpers (commented — uncomment and run manually when needed)
-- ---------------------------------------------------------------------------

-- Full reset (destructive — removes all data and tables):
-- DROP TABLE IF EXISTS document_chunks, documents, pipeline_runs, sessions, users CASCADE;
-- DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;

-- Count documents and chunks per user:
-- SELECT u.email, COUNT(DISTINCT d.id) AS docs, COUNT(c.id) AS chunks
-- FROM users u
-- LEFT JOIN documents d ON d.user_id = u.id
-- LEFT JOIN document_chunks c ON c.document_id = d.id
-- GROUP BY u.email;

-- Check the ivfflat index is being used for embedding searches:
-- EXPLAIN SELECT * FROM document_chunks
-- ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector LIMIT 5;
