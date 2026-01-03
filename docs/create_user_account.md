# Creating User Accounts Manually

Since we're not allowing public signup, you need to create user accounts manually through the Supabase dashboard or API.

## Method 1: Supabase Dashboard (Easiest)

1. Go to your Supabase project dashboard
2. Navigate to **Authentication** > **Users**
3. Click **"Add user"** or **"Invite user"**
4. Enter the user's email address
5. Set a temporary password (user will be prompted to change it on first login)
6. Click **"Create user"** or **"Send invite"**

## Method 2: Supabase Admin API (Programmatic)

You can create a simple Python script to create users:

```python
from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for admin operations

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Create a new user
response = supabase.auth.admin.create_user({
    "email": "user@example.com",
    "password": "temporary_password_123",
    "email_confirm": True  # Skip email confirmation
})

print(f"User created: {response.user.id}")
```

## Method 3: SQL (Direct Database)

**⚠️ Not recommended** - This bypasses Supabase Auth and may cause issues. Only use if you understand the implications.

```sql
-- This creates a user in auth.users but doesn't set up proper auth metadata
-- You'd need to manually set up the auth schema which is complex
-- Stick to Method 1 or 2 instead
```

## Important Notes

- **Password Requirements**: Supabase enforces password requirements (minimum length, complexity). Check your Supabase project settings.
- **Email Verification**: If email verification is enabled, users won't be able to log in until they verify. You can disable this in Supabase Auth settings or set `email_confirm: True` when creating users.
- **User ID**: The user ID (UUID) from `auth.users` will be used as the `user_id` in all your tables. This is automatically handled by the RLS policies.

## Disabling Public Signup

1. Go to **Authentication** > **Settings** in Supabase dashboard
2. Under **"Auth Providers"**, disable **"Enable email signup"**
3. This prevents new users from creating accounts themselves

## Testing

After creating a user account:
1. Go to `/login` on your app
2. Enter the email and password you set
3. You should be redirected to the dashboard
4. All data will be automatically filtered to that user's data


