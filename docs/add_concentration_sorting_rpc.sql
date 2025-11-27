-- Create RPC function for sorting pages by calculated concentration fields
-- This allows sorting by follower_count/client_count without adding columns

CREATE OR REPLACE FUNCTION get_pages_with_concentration(
  p_categorized BOOLEAN DEFAULT NULL,
  p_category TEXT DEFAULT NULL,
  p_search TEXT DEFAULT NULL,
  p_include_archived BOOLEAN DEFAULT FALSE,
  p_sort_by TEXT DEFAULT 'client_count',
  p_order_dir TEXT DEFAULT 'desc',
  p_limit INTEGER DEFAULT 100,
  p_offset INTEGER DEFAULT 0
) RETURNS SETOF pages AS $$
BEGIN
  RETURN QUERY
  SELECT * FROM pages p
  WHERE 
    -- Archived filter
    (p_include_archived OR p.archived = FALSE)
    -- Categorized filter
    AND (p_categorized IS NULL 
         OR (p_categorized AND p.category IS NOT NULL) 
         OR (NOT p_categorized AND p.category IS NULL))
    -- Category filter
    AND (p_category IS NULL OR p.category = p_category)
    -- Search filter
    AND (p_search IS NULL 
         OR p.ig_username ILIKE '%' || p_search || '%' 
         OR p.full_name ILIKE '%' || p_search || '%')
  ORDER BY
    -- Concentration sorting (follower_count / client_count)
    CASE WHEN p_sort_by = 'concentration' AND p_order_dir = 'desc' 
         THEN (p.follower_count::DECIMAL / NULLIF(p.client_count, 0)) 
         END DESC NULLS LAST,
    CASE WHEN p_sort_by = 'concentration' AND p_order_dir = 'asc' 
         THEN (p.follower_count::DECIMAL / NULLIF(p.client_count, 0)) 
         END ASC NULLS LAST,
    -- Concentration per dollar sorting (normalized by 1M)
    CASE WHEN p_sort_by = 'concentration_per_dollar' AND p_order_dir = 'desc' 
         THEN ((p.follower_count::DECIMAL / NULLIF(p.client_count, 0)) / NULLIF(p.promo_price, 0) / 1000000) 
         END DESC NULLS LAST,
    CASE WHEN p_sort_by = 'concentration_per_dollar' AND p_order_dir = 'asc' 
         THEN ((p.follower_count::DECIMAL / NULLIF(p.client_count, 0)) / NULLIF(p.promo_price, 0) / 1000000) 
         END ASC NULLS LAST,
    -- Standard field sorting (descending)
    CASE WHEN p_sort_by = 'client_count' AND p_order_dir = 'desc' THEN p.client_count END DESC NULLS LAST,
    CASE WHEN p_sort_by = 'client_count' AND p_order_dir = 'asc' THEN p.client_count END ASC NULLS LAST,
    CASE WHEN p_sort_by = 'follower_count' AND p_order_dir = 'desc' THEN p.follower_count END DESC NULLS LAST,
    CASE WHEN p_sort_by = 'follower_count' AND p_order_dir = 'asc' THEN p.follower_count END ASC NULLS LAST,
    CASE WHEN p_sort_by = 'last_reviewed_at' AND p_order_dir = 'desc' THEN p.last_reviewed_at END DESC NULLS LAST,
    CASE WHEN p_sort_by = 'last_reviewed_at' AND p_order_dir = 'asc' THEN p.last_reviewed_at END ASC NULLS LAST,
    -- Secondary sort by id for deterministic pagination
    p.id ASC
  LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

-- Usage examples:
-- 
-- Sort by concentration (descending):
-- SELECT * FROM get_pages_with_concentration(
--   p_categorized := TRUE,
--   p_category := 'Black Theme Page',
--   p_sort_by := 'concentration',
--   p_order_dir := 'desc',
--   p_limit := 100
-- );
--
-- Sort by concentration per dollar (descending):
-- SELECT * FROM get_pages_with_concentration(
--   p_categorized := TRUE,
--   p_sort_by := 'concentration_per_dollar',
--   p_order_dir := 'desc',
--   p_limit := 100
-- );

