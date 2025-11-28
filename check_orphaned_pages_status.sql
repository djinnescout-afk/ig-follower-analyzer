-- Check for pages with 0 clients (orphaned pages)
-- These shouldn't exist because pages should only be created when a client follows them

-- 1. Count pages with 0 clients
SELECT 
  COUNT(*) as pages_with_zero_clients,
  COUNT(CASE WHEN archived = false THEN 1 END) as unarchived_zero_clients
FROM pages
WHERE client_count = 0;

-- 2. Total pages breakdown
SELECT 
  'Total pages' as category,
  COUNT(*) as count
FROM pages
WHERE archived = false
UNION ALL
SELECT 
  'Pages with 1+ clients' as category,
  COUNT(*) as count
FROM pages
WHERE archived = false AND client_count >= 1
UNION ALL
SELECT 
  'Pages with 0 clients (ORPHANED)' as category,
  COUNT(*) as count
FROM pages
WHERE archived = false AND client_count = 0
UNION ALL
SELECT 
  'Uncategorized (1+ clients)' as category,
  COUNT(*) as count
FROM pages
WHERE archived = false AND client_count >= 1 AND category IS NULL
UNION ALL
SELECT 
  'Categorized (1+ clients)' as category,
  COUNT(*) as count
FROM pages
WHERE archived = false AND client_count >= 1 AND category IS NOT NULL;

-- 3. Sample of orphaned pages (most recent)
SELECT 
  id,
  ig_username,
  full_name,
  follower_count,
  client_count,
  created_at,
  category
FROM pages
WHERE client_count = 0 AND archived = false
ORDER BY created_at DESC
LIMIT 20;



