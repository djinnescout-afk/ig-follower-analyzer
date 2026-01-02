-- Add All Missing Columns to Pages Table
-- Run this in your STAGING Supabase SQL Editor
-- This adds all columns that exist in production but are missing in staging

-- Archive-related columns
ALTER TABLE pages ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS archived_by TEXT;

-- Contact method tracking
ALTER TABLE pages ADD COLUMN IF NOT EXISTS attempted_contact_methods TEXT[];

-- Contact detail fields (if not already added by add_va_categorization_fields.sql)
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_email TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_phone TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_whatsapp TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_telegram TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_other TEXT;

-- Scrape status and error tracking
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_scrape_status TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_scrape_error TEXT;

-- Manual promo status (if not already added by add_va_categorization_fields.sql)
ALTER TABLE pages ADD COLUMN IF NOT EXISTS manual_promo_status TEXT;

-- Website-related columns
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_contact_email TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_has_contact_form BOOLEAN;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_has_promo_page BOOLEAN;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_last_scraped_at TIMESTAMPTZ;

-- Create indexes for commonly filtered columns
CREATE INDEX IF NOT EXISTS idx_pages_archived_at ON pages(archived_at);
CREATE INDEX IF NOT EXISTS idx_pages_last_scrape_status ON pages(last_scrape_status);
CREATE INDEX IF NOT EXISTS idx_pages_manual_promo_status ON pages(manual_promo_status);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ All missing columns added to pages table successfully!';
END $$;

