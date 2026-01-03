-- Multi-Tenant Authentication Migration
-- Run this in Supabase SQL Editor
-- This adds user_id to all tables and enables Row-Level Security

-- Step 1: Add user_id column to all tables
-- Note: Existing data will be NULL - you'll need to assign it to an admin user manually

ALTER TABLE clients ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE client_following ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE scrape_runs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE page_profiles ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE outreach_tracking ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Step 2: Create indexes on user_id for performance
CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE INDEX IF NOT EXISTS idx_pages_user_id ON pages(user_id);
CREATE INDEX IF NOT EXISTS idx_client_following_user_id ON client_following(user_id);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_user_id ON scrape_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_page_profiles_user_id ON page_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_outreach_tracking_user_id ON outreach_tracking(user_id);

-- Step 3: Enable Row-Level Security on all tables
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_following ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE page_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_tracking ENABLE ROW LEVEL SECURITY;

-- Step 4: Create RLS policies for clients table
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

-- Step 5: Create RLS policies for pages table
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

-- Step 6: Create RLS policies for client_following table
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

-- Step 7: Create RLS policies for scrape_runs table
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

-- Step 8: Create RLS policies for page_profiles table
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

-- Step 9: Create RLS policies for outreach_tracking table
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

-- Step 10: Create function to automatically set user_id on insert
-- This ensures user_id is always set when inserting new rows
CREATE OR REPLACE FUNCTION set_user_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.user_id IS NULL THEN
        NEW.user_id = auth.uid();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create triggers to auto-set user_id
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

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Multi-tenant authentication migration completed!';
    RAISE NOTICE '📝 Next steps:';
    RAISE NOTICE '   1. Assign existing data to an admin user (see assign_existing_data.sql)';
    RAISE NOTICE '   2. Disable public signup in Supabase Auth settings';
    RAISE NOTICE '   3. Create user accounts manually via Supabase dashboard or admin API';
END $$;


