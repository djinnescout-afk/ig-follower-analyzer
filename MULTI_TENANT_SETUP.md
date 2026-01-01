# Multi-Tenant Authentication Setup Guide

This guide walks you through setting up multi-tenant authentication for the IG Follower Analyzer.

## Prerequisites

- Supabase project with database already set up
- Access to Supabase dashboard
- Environment variables configured

## Step 1: Database Migration

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Run the migration script: `docs/add_multi_tenant_auth.sql`
4. This will:
   - Add `user_id` column to all tables
   - Create indexes on `user_id`
   - Enable Row-Level Security (RLS)
   - Create RLS policies for all tables
   - Create triggers to auto-set `user_id` on insert

## Step 2: Assign Existing Data

If you have existing data, you need to assign it to a user:

1. Create your first admin user account (see Step 3)
2. Get the user's UUID from `auth.users` table:
   ```sql
   SELECT id, email FROM auth.users WHERE email = 'admin@example.com';
   ```
3. Run the assignment script: `docs/assign_existing_data.sql`
4. Replace `YOUR_ADMIN_USER_ID` with the actual UUID from step 2

## Step 3: Configure Supabase Auth

1. Go to **Authentication** > **Settings** in Supabase dashboard
2. **Disable** "Enable email signup" (we're creating accounts manually)
3. Optionally disable "Enable email confirmations" if you want immediate access
4. Note your **JWT Secret** (found in **Settings** > **API** > **JWT Settings**)

## Step 4: Environment Variables

### Backend (API)

Add to your `.env` or Render environment variables:

```bash
# Existing variables
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
APIFY_TOKEN=your_apify_token

# New variables
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret  # Optional but recommended for production
```

### Frontend (Web)

Add to your `.env.local` or Vercel environment variables:

```bash
# Existing variables
NEXT_PUBLIC_API_URL=your_api_url

# New variables
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Step 5: Install Dependencies

### Backend

```bash
cd api
pip install -r requirements.txt
```

This will install `PyJWT==2.8.0` for JWT verification.

### Frontend

```bash
cd web
npm install
```

This will install `@supabase/supabase-js` for authentication.

## Step 6: Create User Accounts

See `docs/create_user_account.md` for detailed instructions on creating user accounts manually.

Quick method:
1. Go to Supabase dashboard > **Authentication** > **Users**
2. Click **"Add user"**
3. Enter email and password
4. Create the user

## Step 7: Test the Setup

1. Start your backend API
2. Start your frontend (or deploy to Vercel)
3. Navigate to `/login`
4. Log in with a user account you created
5. Verify that:
   - You can see the dashboard
   - Data is filtered to your user only
   - You can create/edit clients and pages
   - All operations are scoped to your user

## Troubleshooting

### "Invalid or expired token" error

- Check that `SUPABASE_JWT_SECRET` is set correctly in backend
- Verify the JWT token is being sent in the Authorization header
- Check browser console for auth errors

### "Row not found or access denied" error

- Verify RLS policies are enabled on all tables
- Check that `user_id` is set correctly on rows
- Ensure the user_id in the JWT matches the user_id in the database

### Users can see each other's data

- Verify RLS policies are active: `SELECT * FROM pg_policies WHERE tablename = 'pages';`
- Check that all queries include `.eq("user_id", user_id)` filter
- Ensure service key is not being used for user queries (should use user JWT)

### Login page shows but can't log in

- Check Supabase Auth settings (email signup might be disabled incorrectly)
- Verify user exists in `auth.users` table
- Check email/password are correct
- Look for errors in browser console

## Security Notes

- **Never commit** `.env` files with secrets
- **Use service key** only for admin operations (creating users, migrations)
- **Use anon key + user JWT** for regular operations (respects RLS)
- **JWT Secret** should be kept secure - it's used to verify tokens
- **RLS policies** are your primary security layer - test them thoroughly

## Next Steps

- Set up payment processing (Stripe/Paddle) for subscriptions
- Add usage limits based on subscription tier
- Create admin dashboard for managing users
- Add team collaboration features (if needed)

