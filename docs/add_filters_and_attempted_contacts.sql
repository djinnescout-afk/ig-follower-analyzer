-- Add filters support and attempted contact methods tracking
-- Run this in Supabase SQL Editor

-- Add attempted_contact_methods field to track which methods have been tried
ALTER TABLE pages ADD COLUMN IF NOT EXISTS attempted_contact_methods TEXT[];

-- Create index for filtering by attempted contact methods
CREATE INDEX IF NOT EXISTS idx_pages_attempted_contact_methods ON pages USING GIN(attempted_contact_methods);

-- Update the manual_promo_status check constraint to include 'accepted'
ALTER TABLE pages DROP CONSTRAINT IF EXISTS pages_manual_promo_status_check;
ALTER TABLE pages ADD CONSTRAINT pages_manual_promo_status_check 
    CHECK (manual_promo_status IN ('unknown', 'warm', 'not_open', 'accepted'));

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Filters and attempted contact methods added successfully!';
END $$;

