-- Account State Management
-- This migration sets up account states (active/paused) for users
-- Account state is stored in auth.users.raw_user_meta_data

-- Note: This SQL script documents the approach. Actual updates to auth.users
-- must be done via Supabase Admin API or Dashboard, as direct SQL updates
-- to auth.users are restricted.

-- For existing users, set account_state to 'active' via Supabase Admin API:
-- 
-- Using Supabase Dashboard:
-- 1. Go to Authentication > Users
-- 2. For each user, click Edit
-- 3. In User Metadata, add: { "account_state": "active" }
-- 4. Save
--
-- Or using Supabase Admin API (Python example):
-- admin_client.auth.admin.update_user_by_id(
--     user_id,
--     {"user_metadata": {"account_state": "active"}}
-- )

-- New users will default to 'active' if set in Supabase Auth settings
-- or handled in your signup flow.

-- To set a user to paused:
-- admin_client.auth.admin.update_user_by_id(
--     user_id,
--     {"user_metadata": {"account_state": "paused"}}
-- )

-- To set a user to active:
-- admin_client.auth.admin.update_user_by_id(
--     user_id,
--     {"user_metadata": {"account_state": "active"}}
-- )

-- Query to check user account states (via Admin API):
-- response = admin_client.auth.admin.list_users()
-- for user in response.users:
--     account_state = user.user_metadata.get("account_state", "active")
--     print(f"User {user.email}: {account_state}")

