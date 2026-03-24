-- ============================================================
-- Migration 013 — Dashboard read-path counters and indexes
--
-- 1. Adds nullable entity_count to user_index so the app can
--    store grouped entity totals without breaking older rows.
-- 2. Backfills the exact counters that can be computed in SQL.
-- 3. Adds composite indexes used by Home/dashboard reads.
-- ============================================================

ALTER TABLE user_index
    ADD COLUMN IF NOT EXISTS entity_count INT;

UPDATE user_index AS ui
SET
    conversation_count = COALESCE(
        (
            SELECT COUNT(*)::INT
            FROM conversations AS c
            WHERE c.user_id = ui.user_id
        ),
        0
    ),
    topic_count = COALESCE(
        (
            SELECT COUNT(*)::INT
            FROM topic_clusters AS tc
            WHERE tc.user_id = ui.user_id
        ),
        0
    ),
    commitment_count = COALESCE(
        (
            SELECT COUNT(*)::INT
            FROM commitments AS cm
            WHERE cm.user_id = ui.user_id
        ),
        0
    );

CREATE INDEX IF NOT EXISTS commitments_user_status_action_created_idx
    ON commitments (user_id, status, action_type, created_at DESC);

CREATE INDEX IF NOT EXISTS briefs_user_event_generated_idx
    ON briefs (user_id, calendar_event_id, generated_at DESC)
    WHERE calendar_event_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS conversations_user_status_meeting_date_idx
    ON conversations (user_id, status, meeting_date DESC);

CREATE INDEX IF NOT EXISTS topics_user_conversation_created_idx
    ON topics (user_id, conversation_id, created_at DESC);
