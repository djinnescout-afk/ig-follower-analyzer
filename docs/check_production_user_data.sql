-- Check your user_id and data in PRODUCTION
-- Run this in PRODUCTION Supabase SQL Editor

-- 1. Find your user_id
SELECT id, email FROM auth.users WHERE email = 'djinnescout@gmail.com';

-- 2. Check if you have any clients assigned to your user_id
SELECT COUNT(*) as client_count, user_id 
FROM clients 
GROUP BY user_id
ORDER BY client_count DESC;

-- 3. Check if you have any pages assigned to your user_id
SELECT COUNT(*) as page_count, user_id 
FROM pages 
GROUP BY user_id
ORDER BY page_count DESC;

-- 4. Check your specific user_id (from logs: ff6e0c97-6f0a-4415-9fba-451667641863)
SELECT 
    (SELECT COUNT(*) FROM clients WHERE user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863') as your_client_count,
    (SELECT COUNT(*) FROM pages WHERE user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863') as your_page_count;

-- 5. Check what user_ids have data
SELECT 'clients' as table_name, user_id, COUNT(*) as count
FROM clients
GROUP BY user_id
UNION ALL
SELECT 'pages' as table_name, user_id, COUNT(*) as count
FROM pages
GROUP BY user_id
ORDER BY count DESC;

