-- Fix user_id assignment in staging
-- Run this in STAGING Supabase SQL Editor

-- STEP 1: Find your user ID
SELECT id, email FROM auth.users WHERE email = 'djinnescout@gmail.com';
-- Copy the UUID from the id column above

-- STEP 2: Check what user_ids exist in the data
SELECT 'clients' as table_name, user_id, COUNT(*) as count
FROM clients
GROUP BY user_id
ORDER BY count DESC;

SELECT 'pages' as table_name, user_id, COUNT(*) as count  
FROM pages
GROUP BY user_id
ORDER BY count DESC;

-- STEP 3: Replace YOUR_USER_ID below with the UUID from STEP 1, then run:

-- Assign all data to your user
UPDATE clients 
SET user_id = 'YOUR_USER_ID' 
WHERE user_id IS NULL OR user_id != 'YOUR_USER_ID';

UPDATE pages 
SET user_id = 'YOUR_USER_ID' 
WHERE user_id IS NULL OR user_id != 'YOUR_USER_ID';

UPDATE scrape_runs 
SET user_id = 'YOUR_USER_ID' 
WHERE user_id IS NULL OR user_id != 'YOUR_USER_ID';

-- For related tables, get user_id from parent tables
UPDATE client_following cf
SET user_id = c.user_id
FROM clients c
WHERE cf.client_id = c.id AND (cf.user_id IS NULL OR cf.user_id != c.user_id);

UPDATE page_profiles pp
SET user_id = p.user_id
FROM pages p
WHERE pp.page_id = p.id AND (pp.user_id IS NULL OR pp.user_id != p.user_id);

UPDATE outreach_tracking ot
SET user_id = p.user_id
FROM pages p
WHERE ot.page_id = p.id AND (ot.user_id IS NULL OR ot.user_id != p.user_id);

-- STEP 4: Verify
SELECT COUNT(*) as client_count FROM clients WHERE user_id = 'YOUR_USER_ID';
SELECT COUNT(*) as page_count FROM pages WHERE user_id = 'YOUR_USER_ID';


