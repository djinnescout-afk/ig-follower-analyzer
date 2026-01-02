-- COMPLETE MIGRATION SCRIPT FOR STAGING
-- This script runs ALL migrations in the correct order to make staging match production
-- Run this ENTIRE script in your staging Supabase SQL Editor
-- DO NOT run individual migrations - run this complete script

-- ============================================================================
-- STEP 1: Base Schema
-- ============================================================================
-- This creates the initial tables
-- (Contents of supabase_schema.sql)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Clients table
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    ig_username TEXT UNIQUE NOT NULL,
    following_count INTEGER DEFAULT 0,
    last_scraped TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clients_username ON clients(ig_username);

-- 2. Pages table
CREATE TABLE IF NOT EXISTS pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ig_username TEXT UNIQUE NOT NULL,
    full_name TEXT,
    follower_count INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    is_private BOOLEAN DEFAULT FALSE,
    last_scraped TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pages_username ON pages(ig_username);

-- 3. Client Following (relationship table)
CREATE TABLE IF NOT EXISTS client_following (
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (client_id, page_id)
);

CREATE INDEX IF NOT EXISTS idx_client_following_client ON client_following(client_id);
CREATE INDEX IF NOT EXISTS idx_client_following_page ON client_following(page_id);

-- 4. Scrape Runs (job queue and history)
CREATE TABLE IF NOT EXISTS scrape_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scrape_type TEXT NOT NULL CHECK (scrape_type IN ('client_following', 'profile_scrape')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    page_ids UUID[],
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_scrape_runs_status ON scrape_runs(status);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_type ON scrape_runs(scrape_type);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_created ON scrape_runs(created_at DESC);

-- 5. Page Profiles (detailed profile data)
CREATE TABLE IF NOT EXISTS page_profiles (
    page_id UUID PRIMARY KEY REFERENCES pages(id) ON DELETE CASCADE,
    profile_pic_base64 TEXT,
    profile_pic_mime_type TEXT,
    bio TEXT,
    posts JSONB,
    promo_status TEXT DEFAULT 'unknown',
    promo_indicators JSONB,
    contact_email TEXT,
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- Update triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_pages_updated_at ON pages;
CREATE TRIGGER update_pages_updated_at
    BEFORE UPDATE ON pages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STEP 2: VA Categorization Fields
-- ============================================================================
-- (Contents of add_va_categorization_fields.sql)

ALTER TABLE pages ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS known_contact_methods TEXT[];
ALTER TABLE pages ADD COLUMN IF NOT EXISTS successful_contact_method TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS current_main_contact_method TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS ig_account_for_dm TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS promo_price DECIMAL(10,2);
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_url TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS va_notes TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_reviewed_by TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_reviewed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_pages_category ON pages(category);
CREATE INDEX IF NOT EXISTS idx_pages_last_reviewed ON pages(last_reviewed_at DESC);

-- Outreach tracking table
CREATE TABLE IF NOT EXISTS outreach_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('not_contacted', 'contacted', 'responded', 'negotiating', 'booked', 'declined')),
    date_contacted TIMESTAMPTZ,
    follow_up_date TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outreach_page ON outreach_tracking(page_id);
CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach_tracking(status);
CREATE INDEX IF NOT EXISTS idx_outreach_follow_up ON outreach_tracking(follow_up_date);

DROP TRIGGER IF EXISTS update_outreach_updated_at ON outreach_tracking;
CREATE TRIGGER update_outreach_updated_at
    BEFORE UPDATE ON outreach_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STEP 3: Multi-Tenant Auth (STAGED version - adds user_id to existing tables)
-- ============================================================================
-- (Contents of add_multi_tenant_auth_STAGED.sql)

-- Add user_id to all tables
ALTER TABLE clients ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE client_following ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE scrape_runs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE page_profiles ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE outreach_tracking ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Create indexes for user_id
CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE INDEX IF NOT EXISTS idx_pages_user_id ON pages(user_id);
CREATE INDEX IF NOT EXISTS idx_client_following_user_id ON client_following(user_id);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_user_id ON scrape_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_page_profiles_user_id ON page_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_outreach_tracking_user_id ON outreach_tracking(user_id);

-- Enable RLS
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_following ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE page_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_tracking ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Clients
DROP POLICY IF EXISTS "Users can view own clients" ON clients;
CREATE POLICY "Users can view own clients" ON clients FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own clients" ON clients;
CREATE POLICY "Users can insert own clients" ON clients FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own clients" ON clients;
CREATE POLICY "Users can update own clients" ON clients FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own clients" ON clients;
CREATE POLICY "Users can delete own clients" ON clients FOR DELETE USING (auth.uid() = user_id);

-- Pages
DROP POLICY IF EXISTS "Users can view own pages" ON pages;
CREATE POLICY "Users can view own pages" ON pages FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own pages" ON pages;
CREATE POLICY "Users can insert own pages" ON pages FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own pages" ON pages;
CREATE POLICY "Users can update own pages" ON pages FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own pages" ON pages;
CREATE POLICY "Users can delete own pages" ON pages FOR DELETE USING (auth.uid() = user_id);

-- Client Following
DROP POLICY IF EXISTS "Users can view own client_following" ON client_following;
CREATE POLICY "Users can view own client_following" ON client_following FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own client_following" ON client_following;
CREATE POLICY "Users can insert own client_following" ON client_following FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own client_following" ON client_following;
CREATE POLICY "Users can update own client_following" ON client_following FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own client_following" ON client_following;
CREATE POLICY "Users can delete own client_following" ON client_following FOR DELETE USING (auth.uid() = user_id);

-- Scrape Runs
DROP POLICY IF EXISTS "Users can view own scrape_runs" ON scrape_runs;
CREATE POLICY "Users can view own scrape_runs" ON scrape_runs FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own scrape_runs" ON scrape_runs;
CREATE POLICY "Users can insert own scrape_runs" ON scrape_runs FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own scrape_runs" ON scrape_runs;
CREATE POLICY "Users can update own scrape_runs" ON scrape_runs FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own scrape_runs" ON scrape_runs;
CREATE POLICY "Users can delete own scrape_runs" ON scrape_runs FOR DELETE USING (auth.uid() = user_id);

-- Page Profiles
DROP POLICY IF EXISTS "Users can view own page_profiles" ON page_profiles;
CREATE POLICY "Users can view own page_profiles" ON page_profiles FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own page_profiles" ON page_profiles;
CREATE POLICY "Users can insert own page_profiles" ON page_profiles FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own page_profiles" ON page_profiles;
CREATE POLICY "Users can update own page_profiles" ON page_profiles FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own page_profiles" ON page_profiles;
CREATE POLICY "Users can delete own page_profiles" ON page_profiles FOR DELETE USING (auth.uid() = user_id);

-- Outreach Tracking
DROP POLICY IF EXISTS "Users can view own outreach_tracking" ON outreach_tracking;
CREATE POLICY "Users can view own outreach_tracking" ON outreach_tracking FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own outreach_tracking" ON outreach_tracking;
CREATE POLICY "Users can insert own outreach_tracking" ON outreach_tracking FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own outreach_tracking" ON outreach_tracking;
CREATE POLICY "Users can update own outreach_tracking" ON outreach_tracking FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own outreach_tracking" ON outreach_tracking;
CREATE POLICY "Users can delete own outreach_tracking" ON outreach_tracking FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- STEP 4: Client Count Column
-- ============================================================================
-- (Contents of add_client_count_column.sql)

ALTER TABLE pages ADD COLUMN IF NOT EXISTS client_count INTEGER DEFAULT 0;

-- Function to update client_count
CREATE OR REPLACE FUNCTION update_page_client_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE pages
        SET client_count = (
            SELECT COUNT(DISTINCT client_id)
            FROM client_following
            WHERE page_id = NEW.page_id
        )
        WHERE id = NEW.page_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE pages
        SET client_count = (
            SELECT COUNT(DISTINCT client_id)
            FROM client_following
            WHERE page_id = OLD.page_id
        )
        WHERE id = OLD.page_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_client_count ON client_following;
CREATE TRIGGER trigger_update_client_count
    AFTER INSERT OR DELETE ON client_following
    FOR EACH ROW
    EXECUTE FUNCTION update_page_client_count();

-- Initial update
UPDATE pages
SET client_count = (
    SELECT COUNT(DISTINCT client_id)
    FROM client_following
    WHERE client_following.page_id = pages.id
);

-- ============================================================================
-- STEP 5: Date Closed Column for Clients
-- ============================================================================
-- (Contents of add_date_closed_to_clients.sql)

ALTER TABLE clients ADD COLUMN IF NOT EXISTS date_closed TIMESTAMPTZ;

CREATE OR REPLACE FUNCTION set_client_date_closed()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.date_closed IS NULL THEN
        NEW.date_closed = NEW.created_at;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_clients_date_closed ON clients;
CREATE TRIGGER set_clients_date_closed
    BEFORE INSERT ON clients
    FOR EACH ROW
    EXECUTE FUNCTION set_client_date_closed();

UPDATE clients SET date_closed = created_at WHERE date_closed IS NULL;

CREATE INDEX IF NOT EXISTS idx_clients_date_closed ON clients(date_closed);

-- ============================================================================
-- STEP 6: Change Successful Contact Method to Array
-- ============================================================================
-- (Contents of change_successful_contact_method_to_array.sql)

-- First, migrate existing data
UPDATE pages
SET successful_contact_methods = ARRAY[successful_contact_method]::TEXT[]
WHERE successful_contact_method IS NOT NULL
  AND successful_contact_methods IS NULL;

-- Add the new array column if it doesn't exist
ALTER TABLE pages ADD COLUMN IF NOT EXISTS successful_contact_methods TEXT[];

-- Drop the old column
ALTER TABLE pages DROP COLUMN IF EXISTS successful_contact_method;

-- ============================================================================
-- STEP 7: All Missing Pages Columns (from production)
-- ============================================================================
-- (Contents of add_missing_pages_columns.sql)

-- Archive-related columns
ALTER TABLE pages ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS archived_by TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;

-- Contact method tracking
ALTER TABLE pages ADD COLUMN IF NOT EXISTS attempted_contact_methods TEXT[];

-- Contact detail fields
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_email TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_phone TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_whatsapp TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_telegram TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS contact_other TEXT;

-- Scrape status and error tracking
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_scrape_status TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_scrape_error TEXT;

-- Manual promo status
ALTER TABLE pages ADD COLUMN IF NOT EXISTS manual_promo_status TEXT;

-- Website-related columns
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_contact_email TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_has_contact_form BOOLEAN;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_has_promo_page BOOLEAN;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS website_last_scraped_at TIMESTAMPTZ;

-- Create indexes for commonly filtered columns
CREATE INDEX IF NOT EXISTS idx_pages_archived_at ON pages(archived_at);
CREATE INDEX IF NOT EXISTS idx_pages_last_scrape_status ON pages(last_scrape_status);
CREATE INDEX IF NOT EXISTS idx_pages_manual_promo_status ON pages(manual_promo_status);

-- ============================================================================
-- STEP 8: Category Counts Function
-- ============================================================================
-- (Contents of add_category_counts_function.sql)

CREATE OR REPLACE FUNCTION get_category_counts(p_user_id UUID)
RETURNS TABLE (
    category TEXT,
    count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(p.category, 'uncategorized')::TEXT as category,
        COUNT(*)::BIGINT as count
    FROM pages p
    WHERE p.user_id = p_user_id
    GROUP BY COALESCE(p.category, 'uncategorized')
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- STEP 9: Concentration Sorting RPC
-- ============================================================================
-- (Contents of add_concentration_sorting_rpc.sql)

CREATE OR REPLACE FUNCTION get_pages_by_concentration(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    ig_username TEXT,
    full_name TEXT,
    follower_count INTEGER,
    client_count INTEGER,
    concentration NUMERIC,
    category TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.ig_username,
        p.full_name,
        p.follower_count,
        p.client_count,
        CASE 
            WHEN p.client_count > 0 THEN 
                (p.follower_count::NUMERIC / p.client_count::NUMERIC)
            ELSE NULL
        END as concentration,
        p.category,
        p.created_at
    FROM pages p
    WHERE p.user_id = p_user_id
      AND p.client_count > 0
    ORDER BY concentration DESC NULLS LAST
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ All migrations completed successfully!';
    RAISE NOTICE 'Staging database schema should now match production.';
END $$;

