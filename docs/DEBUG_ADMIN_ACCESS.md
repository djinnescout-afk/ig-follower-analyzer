# Debugging Admin Access Issues

## Step 1: Verify Environment Variable in Render

1. Go to Render Dashboard → Your Staging API Service
2. Go to **Environment** tab
3. Verify `ADMIN_EMAILS` is set correctly:
   - Should be: `your-email@example.com` (no quotes, no spaces)
   - For multiple admins: `admin1@example.com,admin2@example.com`
4. **Save** if you made changes
5. Wait for service to restart (check Events tab)

## Step 2: Check Render Logs

1. Go to Render Dashboard → Your Staging API Service
2. Click **Logs** tab
3. Look for lines like:
   ```
   [ADMIN] ADMIN_EMAILS env var value: 'your-email@example.com'
   [ADMIN] Parsed admin emails: ['your-email@example.com']
   ```
4. If you see `NOT_SET` or empty, the env var isn't being read

## Step 3: Test the Admin Endpoint Directly

Open your browser console on the staging frontend and run:

```javascript
fetch('https://your-staging-api-url.onrender.com/api/admin/test-admin', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('supabase.auth.token')}`
  }
})
.then(r => r.json())
.then(console.log)
```

Or use the browser's Network tab:
1. Open DevTools → Network tab
2. Refresh the page
3. Look for request to `/api/admin/test-admin`
4. Check the response - it should show:
   ```json
   {
     "user_id": "...",
     "user_email": "your-email@example.com",
     "admin_emails_from_env": ["your-email@example.com"],
     "is_admin": true,
     "env_var_raw": "your-email@example.com"
   }
   ```

## Step 4: Verify Frontend API URL

1. Check Vercel Dashboard → Your Staging Project
2. Go to **Settings** → **Environment Variables**
3. Verify `NEXT_PUBLIC_API_URL` points to your **staging** API:
   - Should be: `https://your-staging-api.onrender.com`
   - NOT: `https://ig-analyzer-api.onrender.com` (that's production)

## Step 5: Common Issues

### Issue: Email Case Mismatch
- The check is case-insensitive, but verify the email matches exactly
- Check for typos: `youremail@example.com` vs `your-email@example.com`

### Issue: Service Didn't Restart
- After changing env vars in Render, the service must restart
- Check Events tab to see if restart happened
- Manually restart if needed: Render Dashboard → Your Service → Manual Deploy → Clear build cache & deploy

### Issue: Wrong Supabase Project
- Verify `SUPABASE_URL` in Render points to **staging** Supabase project
- The admin check looks up the user in the Supabase project specified by `SUPABASE_URL`
- If it's pointing to production, it won't find staging users

### Issue: User Not in Staging Supabase
- Make sure you've created the user account in your **staging** Supabase project
- The email must exist in `auth.users` table in staging
- You can create it via:
  - Staging frontend sign-up
  - Or manually in Supabase Dashboard → Authentication → Users

## Step 6: Quick Test

Run this in your browser console on staging frontend:

```javascript
// Check what the frontend thinks
const response = await fetch('/api/admin/test-admin')
const data = await response.json()
console.log('Admin check result:', data)
```

This will show you exactly what the backend is returning.


