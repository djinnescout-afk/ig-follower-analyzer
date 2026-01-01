-- Assign existing data to a specific user
-- Run this AFTER creating your first admin user account
-- Replace 'YOUR_ADMIN_USER_ID' with the actual UUID from auth.users table

-- First, find your admin user ID:
-- SELECT id, email FROM auth.users WHERE email = 'admin@example.com';

-- Then update all tables to assign existing data to that user:
-- (Uncomment and replace YOUR_ADMIN_USER_ID with actual UUID)

/*
UPDATE clients SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;
UPDATE pages SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;
UPDATE client_following SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;
UPDATE scrape_runs SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;
UPDATE page_profiles SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;
UPDATE outreach_tracking SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;
*/

-- For client_following, we need to get user_id from the related client:
UPDATE client_following cf
SET user_id = c.user_id
FROM clients c
WHERE cf.client_id = c.id AND cf.user_id IS NULL;

-- For page_profiles, we need to get user_id from the related page:
UPDATE page_profiles pp
SET user_id = p.user_id
FROM pages p
WHERE pp.page_id = p.id AND pp.user_id IS NULL;

-- For outreach_tracking, we need to get user_id from the related page:
UPDATE outreach_tracking ot
SET user_id = p.user_id
FROM pages p
WHERE ot.page_id = p.id AND ot.user_id IS NULL;

-- Verify all data is assigned:
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

