-- VA Categorization Fields Migration
-- Run this in Supabase SQL Editor

-- Add VA categorization fields to pages table
ALTER TABLE pages ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS known_contact_methods TEXT[];
ALTER TABLE pages ADD COLUMN IF NOT EXISTS successful_contact_method TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS current_main_contact_method TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS ig_account_for_dm TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS promo_price DECIMAL(10,2);
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_url TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS va_notes TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_reviewed_by TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_reviewed_at TIMESTAMPTZ;

-- Create indexes for filtering
CREATE INDEX IF NOT EXISTS idx_pages_category ON pages(category);
CREATE INDEX IF NOT EXISTS idx_pages_last_reviewed ON pages(last_reviewed_at DESC);

-- Outreach tracking table
CREATE TABLE IF NOT EXISTS outreach_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('not_contacted', 'contacted', 'responded', 'negotiating', 'booked', 'declined')),
    date_contacted TIMESTAMPTZ,
    follow_up_date TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outreach_page ON outreach_tracking(page_id);
CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach_tracking(status);
CREATE INDEX IF NOT EXISTS idx_outreach_follow_up ON outreach_tracking(follow_up_date);

CREATE TRIGGER update_outreach_updated_at
    BEFORE UPDATE ON outreach_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ VA categorization fields added successfully!';
END $$;

