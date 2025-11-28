-- Change successful_contact_method from text to text[] (array)
-- This allows tracking multiple successful contact methods instead of just one

-- First, convert existing data to array format
UPDATE pages
SET successful_contact_method = ARRAY[successful_contact_method]::text[]
WHERE successful_contact_method IS NOT NULL;

-- Then alter the column type
ALTER TABLE pages
ALTER COLUMN successful_contact_method TYPE text[]
USING CASE 
  WHEN successful_contact_method IS NULL THEN NULL
  ELSE ARRAY[successful_contact_method]
END;

-- Rename the column to reflect it's now plural
ALTER TABLE pages
RENAME COLUMN successful_contact_method TO successful_contact_methods;



