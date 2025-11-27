-- Cleanup Orphaned Pages (pages with no client_following relationships)

-- Step 1: VERIFY - Look at a sample before deleting
SELECT 
  p.ig_username,
  p.full_name,
  p.client_count,
  p.category,
  p.created_at
FROM pages p
WHERE p.id NOT IN (SELECT DISTINCT page_id FROM client_following)
ORDER BY p.created_at DESC
LIMIT 50;

-- Step 2: DELETE all orphaned pages (UNCOMMENT TO RUN)
/*
DELETE FROM pages
WHERE id NOT IN (SELECT DISTINCT page_id FROM client_following);
*/

-- Step 3: VERIFY deletion worked
/*
SELECT COUNT(*) as remaining_orphaned_pages
FROM pages p
WHERE p.id NOT IN (SELECT DISTINCT page_id FROM client_following);
*/

-- Step 4: Verify all remaining pages have at least 1 client
/*
SELECT 
  MIN(client_count) as min_clients,
  MAX(client_count) as max_clients,
  AVG(client_count) as avg_clients,
  COUNT(*) as total_pages
FROM pages;
*/


