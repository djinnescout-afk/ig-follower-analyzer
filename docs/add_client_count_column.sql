-- Migration: Add client_count column to pages table
-- Run this in Supabase SQL Editor

-- 1. Add the column
ALTER TABLE pages ADD COLUMN IF NOT EXISTS client_count INTEGER DEFAULT 0;

-- 2. Populate it with current counts
UPDATE pages
SET client_count = (
    SELECT COUNT(*)
    FROM client_following
    WHERE client_following.page_id = pages.id
);

-- 3. Create a function to update client_count
CREATE OR REPLACE FUNCTION update_page_client_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE pages
        SET client_count = client_count + 1
        WHERE id = NEW.page_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE pages
        SET client_count = client_count - 1
        WHERE id = OLD.page_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 4. Create trigger on client_following table
DROP TRIGGER IF EXISTS trigger_update_page_client_count ON client_following;
CREATE TRIGGER trigger_update_page_client_count
AFTER INSERT OR DELETE ON client_following
FOR EACH ROW
EXECUTE FUNCTION update_page_client_count();

-- 5. Verify the migration
SELECT 
    ig_username, 
    client_count, 
    (SELECT COUNT(*) FROM client_following WHERE page_id = pages.id) as actual_count
FROM pages
WHERE client_count > 0
LIMIT 10;

