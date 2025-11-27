-- Check the most recent completed scrape and what it did

-- 1. Find the most recent completed scrape
SELECT 
  id,
  scrape_type,
  status,
  created_at,
  completed_at,
  result
FROM scrape_runs
WHERE scrape_type = 'client_following'
  AND status = 'completed'
ORDER BY completed_at DESC
LIMIT 1;

-- 2. Check if @blackalchemysolutions exists and what its follower count is
SELECT 
  id,
  ig_username,
  follower_count,
  last_scraped,
  created_at
FROM pages
WHERE ig_username = 'blackalchemysolutions';

-- 3. Check if @blackalchemysolutions was included in the recent scrape
SELECT 
  cf.id,
  cf.created_at,
  p.ig_username,
  p.follower_count,
  p.last_scraped
FROM client_following cf
JOIN pages p ON cf.page_id = p.id
WHERE p.ig_username = 'blackalchemysolutions'
ORDER BY cf.created_at DESC
LIMIT 3;


