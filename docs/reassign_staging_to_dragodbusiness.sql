-- Reassign staging data from djinnescout@gmail.com to dragodbusiness@gmail.com
-- Run this in STAGING Supabase SQL Editor

-- STEP 1: Get the user_id for dragodbusiness@gmail.com in staging
SELECT id, email FROM auth.users WHERE email = 'dragodbusiness@gmail.com';
-- Copy the UUID from the id column above - this is the CORRECT user_id

-- STEP 2: Get the user_id for djinnescout@gmail.com in staging (WRONG - has the data)
SELECT id, email FROM auth.users WHERE email = 'djinnescout@gmail.com';
-- This is the user_id that currently has the data (needs to be moved)

-- STEP 3: Check current data assignment
SELECT 
    'Current assignment' as status,
    (SELECT id FROM auth.users WHERE email = 'djinnescout@gmail.com') as wrong_user_id,
    (SELECT COUNT(*) FROM clients WHERE user_id = (SELECT id FROM auth.users WHERE email = 'djinnescout@gmail.com')) as clients_on_wrong_user,
    (SELECT COUNT(*) FROM pages WHERE user_id = (SELECT id FROM auth.users WHERE email = 'djinnescout@gmail.com')) as pages_on_wrong_user;

SELECT 
    'Target assignment' as status,
    (SELECT id FROM auth.users WHERE email = 'dragodbusiness@gmail.com') as correct_user_id,
    (SELECT COUNT(*) FROM clients WHERE user_id = (SELECT id FROM auth.users WHERE email = 'dragodbusiness@gmail.com')) as clients_on_correct_user,
    (SELECT COUNT(*) FROM pages WHERE user_id = (SELECT id FROM auth.users WHERE email = 'dragodbusiness@gmail.com')) as pages_on_correct_user;

-- STEP 4: Reassign all data to dragodbusiness@gmail.com
-- Replace 'DRAGODBUSINESS_USER_ID' with the UUID from STEP 1
-- Replace 'DJINNESCOUT_USER_ID' with the UUID from STEP 2

UPDATE clients 
SET user_id = (SELECT id FROM auth.users WHERE email = 'dragodbusiness@gmail.com')
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'djinnescout@gmail.com');

UPDATE pages 
SET user_id = (SELECT id FROM auth.users WHERE email = 'dragodbusiness@gmail.com')
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'djinnescout@gmail.com');

UPDATE scrape_runs 
SET user_id = (SELECT id FROM auth.users WHERE email = 'dragodbusiness@gmail.com')
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'djinnescout@gmail.com');

-- Fix related tables to match parent tables
UPDATE client_following cf
SET user_id = c.user_id
FROM clients c
WHERE cf.client_id = c.id;

UPDATE page_profiles pp
SET user_id = p.user_id
FROM pages p
WHERE pp.page_id = p.id;

UPDATE outreach_tracking ot
SET user_id = p.user_id
FROM pages p
WHERE ot.page_id = p.id;

-- STEP 5: Verify
SELECT 
    'After reassignment' as status,
    (SELECT COUNT(*) FROM clients WHERE user_id = (SELECT id FROM auth.users WHERE email = 'dragodbusiness@gmail.com')) as clients_on_dragodbusiness,
    (SELECT COUNT(*) FROM pages WHERE user_id = (SELECT id FROM auth.users WHERE email = 'dragodbusiness@gmail.com')) as pages_on_dragodbusiness,
    (SELECT COUNT(*) FROM clients WHERE user_id = (SELECT id FROM auth.users WHERE email = 'djinnescout@gmail.com')) as clients_on_djinnescout,
    (SELECT COUNT(*) FROM pages WHERE user_id = (SELECT id FROM auth.users WHERE email = 'djinnescout@gmail.com')) as pages_on_djinnescout;

