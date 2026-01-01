-- Add date_closed column to clients table
-- This field defaults to created_at but can be set to any date
-- Used for filtering pages by when clients closed

-- Add the column
ALTER TABLE clients ADD COLUMN IF NOT EXISTS date_closed TIMESTAMPTZ;

-- Create a trigger to set date_closed = created_at if NULL on insert
CREATE OR REPLACE FUNCTION set_client_date_closed()
RETURNS TRIGGER AS $$
BEGIN
    -- If date_closed is not provided, default to created_at
    IF NEW.date_closed IS NULL THEN
        NEW.date_closed = NEW.created_at;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS set_clients_date_closed ON clients;

-- Create the trigger
CREATE TRIGGER set_clients_date_closed
    BEFORE INSERT ON clients
    FOR EACH ROW
    EXECUTE FUNCTION set_client_date_closed();

-- Update existing rows to set date_closed = created_at if NULL
UPDATE clients SET date_closed = created_at WHERE date_closed IS NULL;

-- Create index for efficient date filtering
CREATE INDEX IF NOT EXISTS idx_clients_date_closed ON clients(date_closed);

