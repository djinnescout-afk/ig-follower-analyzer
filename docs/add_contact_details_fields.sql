-- Add contact detail fields to pages table
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_email TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_phone TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_whatsapp TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_telegram TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_other TEXT;

-- Add indexes for searching by contact info
CREATE INDEX IF NOT EXISTS idx_pages_contact_email ON pages(contact_email);
CREATE INDEX IF NOT EXISTS idx_pages_contact_phone ON pages(contact_phone);





