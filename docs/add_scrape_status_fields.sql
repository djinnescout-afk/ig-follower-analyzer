-- Add scrape status tracking fields to pages table
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_scrape_status TEXT CHECK (last_scrape_status IN ('success', 'failed'));
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_scrape_error TEXT;

-- Add index for filtering by scrape status
CREATE INDEX IF NOT EXISTS idx_pages_scrape_status ON pages(last_scrape_status);

-- Add comment
COMMENT ON COLUMN pages.last_scrape_status IS 'Status of the last profile scrape attempt: success or failed';
COMMENT ON COLUMN pages.last_scrape_error IS 'Error message if last scrape failed (e.g., "Profile is private")';

