-- Reassign all production data to your user_id
-- Run this in PRODUCTION Supabase SQL Editor
-- 
-- Your user_id from logs: ff6e0c97-6f0a-4415-9fba-451667641863

-- Reassign all data to your user_id
UPDATE clients 
SET user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863' 
WHERE user_id IS NULL OR user_id != 'ff6e0c97-6f0a-4415-9fba-451667641863';

UPDATE pages 
SET user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863' 
WHERE user_id IS NULL OR user_id != 'ff6e0c97-6f0a-4415-9fba-451667641863';

UPDATE scrape_runs 
SET user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863' 
WHERE user_id IS NULL OR user_id != 'ff6e0c97-6f0a-4415-9fba-451667641863';

-- Fix related tables to match parent tables
UPDATE client_following cf
SET user_id = c.user_id
FROM clients c
WHERE cf.client_id = c.id;

UPDATE page_profiles pp
SET user_id = p.user_id
FROM pages p
WHERE pp.page_id = p.id;

UPDATE outreach_tracking ot
SET user_id = p.user_id
FROM pages p
WHERE ot.page_id = p.id;

-- Verify
SELECT COUNT(*) as client_count FROM clients WHERE user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863';
SELECT COUNT(*) as page_count FROM pages WHERE user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863';


