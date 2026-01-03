-- Assign all existing production data to a specific user
-- Run this in PRODUCTION Supabase SQL Editor
-- 
-- STEP 1: Find your user ID
-- Replace 'djinnescout@gmail.com' with the actual email if different
SELECT id, email FROM auth.users WHERE email = 'djinnescout@gmail.com';

-- STEP 2: Copy the UUID from above and replace YOUR_USER_ID below, then run:

-- Assign all existing data to the user
UPDATE clients 
SET user_id = 'YOUR_USER_ID' 
WHERE user_id IS NULL;

UPDATE pages 
SET user_id = 'YOUR_USER_ID' 
WHERE user_id IS NULL;

UPDATE scrape_runs 
SET user_id = 'YOUR_USER_ID' 
WHERE user_id IS NULL;

-- For client_following, get user_id from the related client:
UPDATE client_following cf
SET user_id = c.user_id
FROM clients c
WHERE cf.client_id = c.id AND cf.user_id IS NULL;

-- For page_profiles, get user_id from the related page:
UPDATE page_profiles pp
SET user_id = p.user_id
FROM pages p
WHERE pp.page_id = p.id AND pp.user_id IS NULL;

-- For outreach_tracking, get user_id from the related page:
UPDATE outreach_tracking ot
SET user_id = p.user_id
FROM pages p
WHERE ot.page_id = p.id AND ot.user_id IS NULL;

-- STEP 3: Verify all data is assigned
SELECT 
    'clients' as table_name, 
    COUNT(*) as total_rows, 
    COUNT(user_id) as rows_with_user_id,
    COUNT(*) - COUNT(user_id) as rows_missing_user_id
FROM clients
UNION ALL
SELECT 'pages', COUNT(*), COUNT(user_id), COUNT(*) - COUNT(user_id) FROM pages
UNION ALL
SELECT 'client_following', COUNT(*), COUNT(user_id), COUNT(*) - COUNT(user_id) FROM client_following
UNION ALL
SELECT 'scrape_runs', COUNT(*), COUNT(user_id), COUNT(*) - COUNT(user_id) FROM scrape_runs
UNION ALL
SELECT 'page_profiles', COUNT(*), COUNT(user_id), COUNT(*) - COUNT(user_id) FROM page_profiles
UNION ALL
SELECT 'outreach_tracking', COUNT(*), COUNT(user_id), COUNT(*) - COUNT(user_id) FROM outreach_tracking;


