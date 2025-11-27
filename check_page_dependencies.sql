-- Check what else references pages table before deleting

-- 1. Check if there are any foreign key constraints referencing pages
SELECT
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND ccu.table_name = 'pages';

-- 2. Check outreach_tracking table (might reference pages)
SELECT COUNT(*) as outreach_records_for_orphaned_pages
FROM outreach_tracking ot
WHERE ot.page_id IN (
    SELECT p.id FROM pages p
    WHERE p.id NOT IN (SELECT DISTINCT page_id FROM client_following)
);

-- 3. Check if any orphaned pages have important data
SELECT 
    COUNT(*) as total_orphaned,
    SUM(CASE WHEN category IS NOT NULL THEN 1 ELSE 0 END) as categorized,
    SUM(CASE WHEN follower_count > 0 THEN 1 ELSE 0 END) as has_followers,
    SUM(CASE WHEN manual_promo_status IS NOT NULL THEN 1 ELSE 0 END) as has_promo_status,
    SUM(CASE WHEN contact_email IS NOT NULL OR contact_phone IS NOT NULL THEN 1 ELSE 0 END) as has_contact_info
FROM pages p
WHERE p.id NOT IN (SELECT DISTINCT page_id FROM client_following);

-- 4. Sample of orphaned pages with actual data (not just empty records)
SELECT 
    ig_username,
    category,
    follower_count,
    manual_promo_status,
    created_at
FROM pages p
WHERE p.id NOT IN (SELECT DISTINCT page_id FROM client_following)
    AND (category IS NOT NULL OR follower_count > 0 OR manual_promo_status IS NOT NULL)
ORDER BY created_at DESC
LIMIT 20;


