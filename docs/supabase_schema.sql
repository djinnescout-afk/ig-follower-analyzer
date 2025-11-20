-- IG Follower Analyzer - Supabase Database Schema
-- Run this entire script in Supabase SQL Editor

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

CREATE INDEX idx_clients_username ON clients(ig_username);

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

CREATE INDEX idx_pages_username ON pages(ig_username);

-- 3. Client Following (relationship table)
CREATE TABLE IF NOT EXISTS client_following (
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (client_id, page_id)
);

CREATE INDEX idx_client_following_client ON client_following(client_id);
CREATE INDEX idx_client_following_page ON client_following(page_id);

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

CREATE INDEX idx_scrape_runs_status ON scrape_runs(status);
CREATE INDEX idx_scrape_runs_type ON scrape_runs(scrape_type);
CREATE INDEX idx_scrape_runs_created ON scrape_runs(created_at DESC);

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

CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pages_updated_at
    BEFORE UPDATE ON pages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Disable Row Level Security for now (using service_role key)
ALTER TABLE clients DISABLE ROW LEVEL SECURITY;
ALTER TABLE pages DISABLE ROW LEVEL SECURITY;
ALTER TABLE client_following DISABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_runs DISABLE ROW LEVEL SECURITY;
ALTER TABLE page_profiles DISABLE ROW LEVEL SECURITY;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Database schema created successfully!';
    RAISE NOTICE 'Tables: clients, pages, client_following, scrape_runs, page_profiles';
END $$;

