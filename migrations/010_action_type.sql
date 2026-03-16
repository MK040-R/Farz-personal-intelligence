-- Migration 010: Add action_type to commitments
-- Distinguishes between things the user owes (commitment) vs. things they are tracking from others (follow_up)

ALTER TABLE commitments
  ADD COLUMN IF NOT EXISTS action_type TEXT NOT NULL DEFAULT 'commitment'
    CHECK (action_type IN ('commitment', 'follow_up'));
