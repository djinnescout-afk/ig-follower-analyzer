-- Create a PostgreSQL function for efficient category counting
-- This avoids fetching all rows and counts them at the database level

CREATE OR REPLACE FUNCTION get_category_counts()
RETURNS TABLE(category TEXT, count BIGINT) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    p.category,
    COUNT(*)::BIGINT as count
  FROM pages p
  WHERE p.category IS NOT NULL
  GROUP BY p.category
  ORDER BY p.category;
END;
$$ LANGUAGE plpgsql STABLE;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION get_category_counts() TO authenticated, anon;

