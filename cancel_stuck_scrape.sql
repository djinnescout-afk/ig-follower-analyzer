-- Cancel the stuck scrape job
-- Step 1: See what columns exist and find processing jobs

SELECT *
FROM scrape_runs
WHERE scrape_type = 'client_following'
  AND status = 'processing'
ORDER BY created_at DESC
LIMIT 3;

-- Step 2: After seeing the results, cancel the stuck one(s)
-- Uncomment and run this after you see the ID:
/*
UPDATE scrape_runs
SET 
  status = 'failed',
  completed_at = NOW(),
  result = '{"error": "Manually cancelled - stuck in processing"}'
WHERE 
  id = 'PASTE_ID_HERE';
*/

-- OR cancel ALL stuck processing jobs older than 10 minutes:
/*
UPDATE scrape_runs
SET 
  status = 'failed',
  completed_at = NOW(),
  result = '{"error": "Manually cancelled - stuck in processing"}'
WHERE 
  scrape_type = 'client_following'
  AND status = 'processing'
  AND created_at < NOW() - INTERVAL '10 minutes';
*/
