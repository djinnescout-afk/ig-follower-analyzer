-- Page Archival System Migration
-- Run this in Supabase SQL Editor

-- Add archival fields to pages table
ALTER TABLE pages ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS archived_by TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS archive_reason TEXT;

-- Create index for filtering archived pages
CREATE INDEX IF NOT EXISTS idx_pages_archived ON pages(archived);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Page archival fields added successfully!';
END $$;


