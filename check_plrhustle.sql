-- Check if plrhustle meets the criteria for follower count scraping

SELECT 
  ig_username,
  full_name,
  client_count,
  category,
  follower_count,
  last_scraped
FROM pages
WHERE ig_username = 'plrhustle';

-- Check which clients follow plrhustle
SELECT 
  c.ig_username as client_username,
  p.ig_username as page_username,
  cf.created_at
FROM client_following cf
JOIN clients c ON cf.client_id = c.id
JOIN pages p ON cf.page_id = p.id
WHERE p.ig_username = 'plrhustle';


