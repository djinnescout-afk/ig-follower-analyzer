-- Fixed SQL to investigate pages with 0 clients

-- 1. Count pages with 0 clients
SELECT COUNT(*) as zero_client_pages
FROM pages
WHERE client_count = 0 OR client_count IS NULL;

-- 2. Check if client_count is just wrong, or pages are truly orphaned
SELECT 
  CASE 
    WHEN p.client_count = 0 AND COALESCE(actual_count, 0) > 0 THEN 'BROKEN TRIGGER - Has relationships but shows 0'
    WHEN p.client_count = 0 AND COALESCE(actual_count, 0) = 0 THEN 'ORPHANED - No relationships at all'
    WHEN p.client_count IS NULL AND COALESCE(actual_count, 0) > 0 THEN 'NULL - Has relationships'
    WHEN p.client_count IS NULL AND COALESCE(actual_count, 0) = 0 THEN 'NULL - No relationships'
  END as issue_type,
  COUNT(*) as page_count
FROM pages p
LEFT JOIN (
  SELECT page_id, COUNT(*) as actual_count
  FROM client_following
  GROUP BY page_id
) cf ON cf.page_id = p.id
WHERE p.client_count = 0 OR p.client_count IS NULL
GROUP BY issue_type;

-- 3. Sample of truly orphaned pages (no client_following records)
SELECT 
  p.ig_username,
  p.client_count,
  p.created_at,
  p.last_scraped
FROM pages p
WHERE p.id NOT IN (SELECT DISTINCT page_id FROM client_following)
ORDER BY p.created_at DESC
LIMIT 20;

-- 4. Count truly orphaned pages
SELECT COUNT(*) as truly_orphaned
FROM pages p
WHERE p.id NOT IN (SELECT DISTINCT page_id FROM client_following);


