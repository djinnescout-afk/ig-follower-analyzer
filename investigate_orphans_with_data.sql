-- Investigate the 1047 orphaned pages with follower counts

-- 1. Sample of orphaned pages with follower counts
SELECT 
  ig_username,
  follower_count,
  created_at,
  last_scraped
FROM pages p
WHERE p.id NOT IN (SELECT DISTINCT page_id FROM client_following)
  AND follower_count > 0
ORDER BY follower_count DESC
LIMIT 30;

-- 2. When were these pages created? (might show a pattern)
SELECT 
  DATE(created_at) as creation_date,
  COUNT(*) as orphans_created
FROM pages p
WHERE p.id NOT IN (SELECT DISTINCT page_id FROM client_following)
  AND follower_count > 0
GROUP BY DATE(created_at)
ORDER BY creation_date DESC
LIMIT 20;

-- 3. Check if we can find these pages in any failed scrape_runs
SELECT 
  sr.id as scrape_run_id,
  sr.client_id,
  sr.status,
  sr.created_at,
  sr.result
FROM scrape_runs sr
WHERE sr.status = 'failed'
  AND sr.scrape_type = 'client_following'
ORDER BY sr.created_at DESC
LIMIT 10;

-- OPTION 1: Just delete them (they're orphaned anyway)
/*
DELETE FROM pages
WHERE id NOT IN (SELECT DISTINCT page_id FROM client_following);
*/

-- OPTION 2: Keep them but fix client_count to 0 for accuracy
/*
UPDATE pages
SET client_count = 0
WHERE id NOT IN (SELECT DISTINCT page_id FROM client_following)
  AND client_count != 0;
*/


