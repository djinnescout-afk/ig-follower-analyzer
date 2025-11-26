-- Check for duplicate pages by ig_username
SELECT 
  ig_username, 
  COUNT(*) as count,
  STRING_AGG(id::text, ', ') as ids,
  STRING_AGG(follower_count::text, ', ') as follower_counts
FROM pages
WHERE ig_username = 'blackforager' OR ig_username = 'plrhustle'
GROUP BY ig_username
ORDER BY count DESC;

-- Check all duplicates in the database
SELECT 
  ig_username, 
  COUNT(*) as count,
  STRING_AGG(id::text, ', ') as ids
FROM pages
GROUP BY ig_username
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 20;

-- Check follower counts for specific pages
SELECT id, ig_username, follower_count, last_scraped, created_at, updated_at
FROM pages
WHERE ig_username IN ('blackforager', 'plrhustle')
ORDER BY ig_username, created_at;

