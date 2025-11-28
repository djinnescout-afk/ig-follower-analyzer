-- Add 'unlikely' to promo_status constraint

ALTER TABLE pages
DROP CONSTRAINT IF EXISTS pages_promo_status_check;

ALTER TABLE pages
ADD CONSTRAINT pages_promo_status_check 
CHECK (promo_status IN ('unknown', 'warm', 'unlikely', 'not_open', 'accepted'));



