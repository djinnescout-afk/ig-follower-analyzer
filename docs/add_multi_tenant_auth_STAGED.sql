-- Multi-Tenant Authentication Migration - STAGED VERSION
-- Run these in order, one section at a time
-- This is safer if you have existing data

-- ============================================
-- STAGE 1: Add user_id columns (safe to run)
-- ============================================
-- Run this first - it won't break anything, just adds columns
ALTER TABLE clients ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE client_following ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE scrape_runs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE page_profiles ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE outreach_tracking ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- ============================================
-- STAGE 2: Create indexes (safe to run)
-- ============================================
CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE INDEX IF NOT EXISTS idx_pages_user_id ON pages(user_id);
CREATE INDEX IF NOT EXISTS idx_client_following_user_id ON client_following(user_id);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_user_id ON scrape_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_page_profiles_user_id ON page_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_outreach_tracking_user_id ON outreach_tracking(user_id);

-- ============================================
-- STAGE 3: Assign existing data to a user
-- ============================================
-- ⚠️ IMPORTANT: Run this BEFORE enabling RLS!
-- First, create your admin user account in Supabase Auth dashboard
-- Then get the user ID:
-- SELECT id, email FROM auth.users WHERE email = 'your-admin@email.com';
-- Replace 'YOUR_ADMIN_USER_ID' below with the actual UUID

-- Uncomment and run this after you have your admin user ID:
/*
UPDATE clients SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;
UPDATE pages SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;
UPDATE scrape_runs SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;
UPDATE page_profiles SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;
UPDATE outreach_tracking SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;

-- For client_following, get user_id from the related client:
UPDATE client_following cf
SET user_id = c.user_id
FROM clients c
WHERE cf.client_id = c.id AND cf.user_id IS NULL;

-- For page_profiles, get user_id from the related page:
UPDATE page_profiles pp
SET user_id = p.user_id
FROM pages p
WHERE pp.page_id = p.id AND pp.user_id IS NULL;

-- For outreach_tracking, get user_id from the related page:
UPDATE outreach_tracking ot
SET user_id = p.user_id
FROM pages p
WHERE ot.page_id = p.id AND ot.user_id IS NULL;
*/

-- ============================================
-- STAGE 4: Enable RLS (only after assigning data!)
-- ============================================
-- ⚠️ Don't run this until you've assigned user_id to all existing rows!
-- Once RLS is enabled, you won't be able to see rows with NULL user_id
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_following ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE page_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_tracking ENABLE ROW LEVEL SECURITY;

-- ============================================
-- STAGE 5: Create RLS policies
-- ============================================
-- Run this after RLS is enabled

-- Clients policies
DROP POLICY IF EXISTS "Users can view their own clients" ON clients;
CREATE POLICY "Users can view their own clients" ON clients
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own clients" ON clients;
CREATE POLICY "Users can insert their own clients" ON clients
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own clients" ON clients;
CREATE POLICY "Users can update their own clients" ON clients
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own clients" ON clients;
CREATE POLICY "Users can delete their own clients" ON clients
    FOR DELETE USING (auth.uid() = user_id);

-- Pages policies
DROP POLICY IF EXISTS "Users can view their own pages" ON pages;
CREATE POLICY "Users can view their own pages" ON pages
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own pages" ON pages;
CREATE POLICY "Users can insert their own pages" ON pages
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own pages" ON pages;
CREATE POLICY "Users can update their own pages" ON pages
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own pages" ON pages;
CREATE POLICY "Users can delete their own pages" ON pages
    FOR DELETE USING (auth.uid() = user_id);

-- Client_following policies
DROP POLICY IF EXISTS "Users can view their own client_following" ON client_following;
CREATE POLICY "Users can view their own client_following" ON client_following
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own client_following" ON client_following;
CREATE POLICY "Users can insert their own client_following" ON client_following
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own client_following" ON client_following;
CREATE POLICY "Users can update their own client_following" ON client_following
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own client_following" ON client_following;
CREATE POLICY "Users can delete their own client_following" ON client_following
    FOR DELETE USING (auth.uid() = user_id);

-- Scrape_runs policies
DROP POLICY IF EXISTS "Users can view their own scrape_runs" ON scrape_runs;
CREATE POLICY "Users can view their own scrape_runs" ON scrape_runs
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own scrape_runs" ON scrape_runs;
CREATE POLICY "Users can insert their own scrape_runs" ON scrape_runs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own scrape_runs" ON scrape_runs;
CREATE POLICY "Users can update their own scrape_runs" ON scrape_runs
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own scrape_runs" ON scrape_runs;
CREATE POLICY "Users can delete their own scrape_runs" ON scrape_runs
    FOR DELETE USING (auth.uid() = user_id);

-- Page_profiles policies
DROP POLICY IF EXISTS "Users can view their own page_profiles" ON page_profiles;
CREATE POLICY "Users can view their own page_profiles" ON page_profiles
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own page_profiles" ON page_profiles;
CREATE POLICY "Users can insert their own page_profiles" ON page_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own page_profiles" ON page_profiles;
CREATE POLICY "Users can update their own page_profiles" ON page_profiles
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own page_profiles" ON page_profiles;
CREATE POLICY "Users can delete their own page_profiles" ON page_profiles
    FOR DELETE USING (auth.uid() = user_id);

-- Outreach_tracking policies
DROP POLICY IF EXISTS "Users can view their own outreach_tracking" ON outreach_tracking;
CREATE POLICY "Users can view their own outreach_tracking" ON outreach_tracking
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own outreach_tracking" ON outreach_tracking;
CREATE POLICY "Users can insert their own outreach_tracking" ON outreach_tracking
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own outreach_tracking" ON outreach_tracking;
CREATE POLICY "Users can update their own outreach_tracking" ON outreach_tracking
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own outreach_tracking" ON outreach_tracking;
CREATE POLICY "Users can delete their own outreach_tracking" ON outreach_tracking
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================
-- STAGE 6: Create triggers (safe to run anytime)
-- ============================================
CREATE OR REPLACE FUNCTION set_user_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.user_id IS NULL THEN
        NEW.user_id = auth.uid();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS set_clients_user_id ON clients;
CREATE TRIGGER set_clients_user_id
    BEFORE INSERT ON clients
    FOR EACH ROW
    EXECUTE FUNCTION set_user_id();

DROP TRIGGER IF EXISTS set_pages_user_id ON pages;
CREATE TRIGGER set_pages_user_id
    BEFORE INSERT ON pages
    FOR EACH ROW
    EXECUTE FUNCTION set_user_id();

DROP TRIGGER IF EXISTS set_client_following_user_id ON client_following;
CREATE TRIGGER set_client_following_user_id
    BEFORE INSERT ON client_following
    FOR EACH ROW
    EXECUTE FUNCTION set_user_id();

DROP TRIGGER IF EXISTS set_scrape_runs_user_id ON scrape_runs;
CREATE TRIGGER set_scrape_runs_user_id
    BEFORE INSERT ON scrape_runs
    FOR EACH ROW
    EXECUTE FUNCTION set_user_id();

DROP TRIGGER IF EXISTS set_page_profiles_user_id ON page_profiles;
CREATE TRIGGER set_page_profiles_user_id
    BEFORE INSERT ON page_profiles
    FOR EACH ROW
    EXECUTE FUNCTION set_user_id();

DROP TRIGGER IF EXISTS set_outreach_tracking_user_id ON outreach_tracking;
CREATE TRIGGER set_outreach_tracking_user_id
    BEFORE INSERT ON outreach_tracking
    FOR EACH ROW
    EXECUTE FUNCTION set_user_id();


