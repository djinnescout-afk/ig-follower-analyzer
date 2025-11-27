-- Sync client_count column for all pages based on actual client_following relationships
-- This updates pages where the client_count doesn't match the actual count

UPDATE pages
SET client_count = subquery.count
FROM (
    SELECT 
        p.id,
        COUNT(cf.client_id) as count
    FROM pages p
    LEFT JOIN client_following cf ON p.id = cf.page_id
    GROUP BY p.id
) AS subquery
WHERE pages.id = subquery.id
AND (pages.client_count IS NULL OR pages.client_count != subquery.count);

-- Verify the results
SELECT 
    COUNT(*) as total_pages,
    COUNT(*) FILTER (WHERE client_count = 0) as pages_with_zero_clients,
    COUNT(*) FILTER (WHERE client_count >= 1) as pages_with_clients,
    COUNT(*) FILTER (WHERE client_count IS NULL) as pages_with_null_count
FROM pages;

-- Show breakdown of uncategorized pages by client_count
SELECT 
    client_count,
    COUNT(*) as page_count
FROM pages
WHERE category IS NULL AND archived = false
GROUP BY client_count
ORDER BY client_count ASC;


