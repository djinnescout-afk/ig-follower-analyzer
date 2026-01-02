-- Investigate why user_ids don't match in PRODUCTION
-- Run this in PRODUCTION Supabase SQL Editor

-- 1. Check ALL users with your email (in case there are duplicates)
SELECT id, email, created_at, last_sign_in_at 
FROM auth.users 
WHERE email = 'djinnescout@gmail.com' OR email ILIKE '%djinnescout%'
ORDER BY created_at;

-- 2. Check which user_id has the data
SELECT 
    'Data owner' as label,
    '2945e327-6ae5-418c-b59d-291e18ab04f3' as user_id,
    (SELECT email FROM auth.users WHERE id = '2945e327-6ae5-418c-b59d-291e18ab04f3') as email,
    (SELECT COUNT(*) FROM clients WHERE user_id = '2945e327-6ae5-418c-b59d-291e18ab04f3') as clients,
    (SELECT COUNT(*) FROM pages WHERE user_id = '2945e327-6ae5-418c-b59d-291e18ab04f3') as pages;

-- 3. Check which user_id you're logged in as (from JWT)
SELECT 
    'Current login' as label,
    'ff6e0c97-6f0a-4415-9fba-451667641863' as user_id,
    (SELECT email FROM auth.users WHERE id = 'ff6e0c97-6f0a-4415-9fba-451667641863') as email,
    (SELECT COUNT(*) FROM clients WHERE user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863') as clients,
    (SELECT COUNT(*) FROM pages WHERE user_id = 'ff6e0c97-6f0a-4415-9fba-451667641863') as pages;

-- 4. Check if there are multiple accounts (could happen if you signed up twice)
SELECT 
    id,
    email,
    created_at,
    last_sign_in_at,
    (SELECT COUNT(*) FROM clients WHERE user_id = id) as client_count,
    (SELECT COUNT(*) FROM pages WHERE user_id = id) as page_count
FROM auth.users
WHERE email = 'djinnescout@gmail.com'
ORDER BY created_at;

-- 5. Check AuthContext user_id (from browser logs)
SELECT 
    'AuthContext' as label,
    '63df0039-313c-4555-959f-55c28be8d7b2' as user_id,
    (SELECT email FROM auth.users WHERE id = '63df0039-313c-4555-959f-55c28be8d7b2') as email,
    (SELECT COUNT(*) FROM clients WHERE user_id = '63df0039-313c-4555-959f-55c28be8d7b2') as clients,
    (SELECT COUNT(*) FROM pages WHERE user_id = '63df0039-313c-4555-959f-55c28be8d7b2') as pages;

