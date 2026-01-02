-- Check user_id assignment in staging
-- Run this in STAGING Supabase SQL Editor

-- Check what user_ids exist in your data
SELECT 
    'clients' as table_name,
    user_id,
    COUNT(*) as count
FROM clients
GROUP BY user_id
ORDER BY count DESC;

SELECT 
    'pages' as table_name,
    user_id,
    COUNT(*) as count
FROM pages
GROUP BY user_id
ORDER BY count DESC;

-- Check your current user ID (from JWT - you saw this in logs: ff6e0c97-6f0a-4415-9fba-451667641863)
SELECT id, email FROM auth.users WHERE email = 'djinnescout@gmail.com';

-- Check if data exists for your user_id
SELECT COUNT(*) as client_count FROM clients WHERE user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863';
SELECT COUNT(*) as page_count FROM pages WHERE user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863';

