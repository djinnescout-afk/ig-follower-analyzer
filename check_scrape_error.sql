-- Check the error details for the failed bossmossseamoss scrape

SELECT 
  id,
  scrape_type,
  status,
  created_at,
  completed_at,
  result
FROM scrape_runs
WHERE scrape_type = 'client_following'
  AND created_at >= '2025-11-26 22:00:00'
ORDER BY created_at DESC
LIMIT 5;


