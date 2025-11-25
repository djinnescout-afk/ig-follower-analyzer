-- Promo Tracking Fields Migration
-- Run this in Supabase SQL Editor

-- Manual promo status (VA input)
ALTER TABLE pages ADD COLUMN IF NOT EXISTS manual_promo_status TEXT 
    CHECK (manual_promo_status IN ('unknown', 'warm', 'not_open'));

-- Website promo detection (auto-scraped)
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_has_promo_page BOOLEAN DEFAULT FALSE;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_contact_email TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_has_contact_form BOOLEAN DEFAULT FALSE;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_last_scraped_at TIMESTAMPTZ;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pages_manual_promo ON pages(manual_promo_status);
CREATE INDEX IF NOT EXISTS idx_pages_website_promo ON pages(website_has_promo_page);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Promo tracking fields added successfully!';
END $$;


