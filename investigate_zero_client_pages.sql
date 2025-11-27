-- Investigate pages with 0 clients (THIS SHOULD NOT EXIST!)

-- 1. Count pages with 0 clients
SELECT COUNT(*) as zero_client_pages
FROM pages
WHERE client_count = 0 OR client_count IS NULL;

-- 2. Check if these pages have actual client_following relationships
SELECT 
  p.ig_username,
  p.client_count,
  COUNT(cf.id) as actual_relationship_count,
  p.created_at,
  p.last_scraped
FROM pages p
LEFT JOIN client_following cf ON cf.page_id = p.id
WHERE p.client_count = 0 OR p.client_count IS NULL
GROUP BY p.id, p.ig_username, p.client_count, p.created_at, p.last_scraped
ORDER BY actual_relationship_count DESC, p.created_at DESC
LIMIT 20;

-- 3. Check if client_count trigger is working
-- Compare client_count column vs actual count
SELECT 
  CASE 
    WHEN p.client_count = actual_count THEN 'Correct'
    WHEN p.client_count < actual_count THEN 'Undercounted'
    WHEN p.client_count > actual_count THEN 'Overcounted'
    WHEN p.client_count = 0 AND actual_count > 0 THEN 'BROKEN - Has relationships but shows 0'
    WHEN p.client_count = 0 AND actual_count = 0 THEN 'ORPHANED - No relationships'
  END as status,
  COUNT(*) as page_count
FROM pages p
LEFT JOIN (
  SELECT page_id, COUNT(*) as actual_count
  FROM client_following
  GROUP BY page_id
) cf ON cf.page_id = p.id
GROUP BY status
ORDER BY page_count DESC;

-- 4. Find truly orphaned pages (no client_following records at all)
SELECT 
  p.ig_username,
  p.full_name,
  p.client_count,
  p.created_at,
  p.last_scraped
FROM pages p
LEFT JOIN client_following cf ON cf.page_id = p.id
WHERE cf.id IS NULL
ORDER BY p.created_at DESC
LIMIT 50;


