-- Debug why plrhustle didn't get its follower count updated

-- 1. Check current state
SELECT 
  ig_username,
  full_name,
  client_count,
  follower_count,
  category,
  last_scraped
FROM pages
WHERE ig_username = 'plrhustle';

-- 2. Check which clients follow plrhustle
SELECT 
  c.ig_username as client,
  cf.created_at
FROM client_following cf
JOIN clients c ON cf.client_id = c.id
JOIN pages p ON cf.page_id = p.id
WHERE p.ig_username = 'plrhustle'
ORDER BY cf.created_at DESC;

-- 3. Check recent scrape for ejustcoolin
SELECT 
  id,
  client_id,
  status,
  created_at,
  started_at,
  completed_at
FROM scrape_runs
WHERE scrape_type = 'client_following'
ORDER BY created_at DESC
LIMIT 5;


