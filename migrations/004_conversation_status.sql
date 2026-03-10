-- ============================================================
-- Migration 004 — Add status column to conversations
--
-- Status lifecycle:
--   processing → conversation ingested but extraction not yet complete
--   indexed    → AI extraction (topics, commitments, entities) complete
--
-- Default is 'processing'; extract_from_conversation task sets 'indexed'.
-- ============================================================

ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'processing'
    CHECK (status IN ('processing', 'indexed'));

-- Index for fast filtering by status (e.g. "show me indexed conversations")
CREATE INDEX IF NOT EXISTS conversations_status_idx ON conversations (user_id, status);
