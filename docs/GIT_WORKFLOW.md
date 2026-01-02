# Git Workflow Guide

This guide explains the Git workflow for deploying to staging and production.

## Branch Structure

```
main (production)
  ↑
staging (staging environment)
  ↑
feature branches (development)
```

## Branches

### `main` Branch
- **Purpose**: Production code
- **Deploys to**: Production environment (Vercel + Render)
- **Protection**: Should require PR approval (recommended)
- **Never commit directly to main** (except hotfixes)

### `staging` Branch
- **Purpose**: Staging/testing environment
- **Deploys to**: Staging environment (Vercel staging + Render staging)
- **Auto-deploys**: Yes, on every push
- **Safe to test**: Yes, completely isolated from production

### Feature Branches
- **Purpose**: Development of new features
- **Naming**: `feature/description` or `fix/description`
- **Deploys to**: Nothing (or PR previews on Vercel)
- **Merge to**: `staging` first, then `main`

## Standard Workflow

### 1. Start New Feature

```bash
# Make sure you're on staging and up to date
git checkout staging
git pull origin staging

# Create feature branch
git checkout -b feature/add-new-filter

# Make your changes
# ... edit files ...

# Commit changes
git add .
git commit -m "Add new filter feature"

# Push feature branch
git push origin feature/add-new-filter
```

### 2. Deploy to Staging

```bash
# Switch to staging branch
git checkout staging

# Merge your feature
git merge feature/add-new-filter

# Push to staging (triggers auto-deploy)
git push origin staging
```

**What happens:**
- Vercel detects push to `staging` branch
- Auto-deploys frontend to staging URL
- Render detects push to `staging` branch
- Auto-deploys backend to staging service

### 3. Test on Staging

1. Visit staging URL (e.g., `https://ig-follower-analyzer-staging.vercel.app`)
2. Test all functionality
3. Verify no errors in console
4. Check that data displays correctly
5. Test all user flows

### 4. Deploy to Production

Once testing is complete:

```bash
# Switch to main branch
git checkout main

# Make sure main is up to date
git pull origin main

# Merge staging into main
git merge staging

# Push to main (triggers auto-deploy to production)
git push origin main
```

**What happens:**
- Vercel detects push to `main` branch
- Auto-deploys frontend to production URL
- Render detects push to `main` branch
- Auto-deploys backend to production service

### 5. Keep Staging in Sync

After deploying to production, staging should match main:

```bash
# This should already be done if you merged staging → main
# But if you made direct changes to main (hotfix), sync back:

git checkout staging
git merge main
git push origin staging
```

## Hotfix Workflow

For urgent production fixes:

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-fix

# Make the fix
# ... edit files ...
git add .
git commit -m "Hotfix: Fix critical bug"

# Deploy directly to production
git checkout main
git merge hotfix/critical-bug-fix
git push origin main

# Then sync to staging
git checkout staging
git merge main
git push origin staging
```

## Best Practices

### 1. Always Test on Staging First

**Never skip staging!** Always:
1. Merge to staging
2. Test thoroughly
3. Then merge to production

### 2. Keep Commits Clean

- Write clear commit messages
- One logical change per commit
- Don't commit broken code

### 3. Regular Syncing

- Keep `staging` and `main` in sync
- After merging to production, merge back to staging
- This ensures staging always has the latest production code

### 4. Branch Naming

Use clear, descriptive names:
- ✅ `feature/add-date-range-filter`
- ✅ `fix/authentication-redirect-loop`
- ✅ `hotfix/critical-database-error`
- ❌ `fix`
- ❌ `new-stuff`
- ❌ `test`

### 5. Pull Before Push

Always pull before pushing:
```bash
git pull origin staging  # or main
git push origin staging
```

## Common Commands

### Check Current Branch
```bash
git branch
# or
git status
```

### Switch Branches
```bash
git checkout staging
git checkout main
git checkout feature/my-feature
```

### See What Changed
```bash
# See uncommitted changes
git status

# See commit history
git log --oneline

# See differences
git diff
```

### Undo Changes

**Uncommitted changes:**
```bash
# Discard all changes
git checkout -- .

# Discard specific file
git checkout -- path/to/file
```

**Last commit (not pushed):**
```bash
git reset --soft HEAD~1  # Keep changes
git reset --hard HEAD~1   # Discard changes
```

## Troubleshooting

### Merge Conflicts

If you get merge conflicts:

```bash
# See conflicted files
git status

# Edit files to resolve conflicts
# Look for <<<<<<< markers

# After resolving:
git add .
git commit -m "Resolve merge conflicts"
```

### Accidentally Committed to Wrong Branch

```bash
# If not pushed yet:
git reset --soft HEAD~1  # Undo commit, keep changes
git checkout correct-branch
git commit -m "Your message"

# If already pushed:
# Create new commit on correct branch, or use git revert
```

### Staging Out of Sync

```bash
# If staging is behind main:
git checkout staging
git merge main
git push origin staging

# If main is behind staging:
git checkout main
git merge staging
git push origin main
```

## Branch Protection (Recommended)

Consider protecting the `main` branch:

1. Go to GitHub/GitLab repository settings
2. Find "Branch protection rules"
3. Add rule for `main` branch:
   - Require pull request reviews
   - Require status checks to pass
   - Require branches to be up to date

This prevents accidental direct commits to production.

## Summary

**Standard Flow:**
```
Feature Branch → Staging → Test → Main → Production
```

**Hotfix Flow:**
```
Hotfix Branch → Main → Production → Staging (sync)
```

**Key Rules:**
1. ✅ Always test on staging first
2. ✅ Keep staging and main in sync
3. ✅ Use descriptive branch names
4. ✅ Write clear commit messages
5. ❌ Never skip staging
6. ❌ Never commit directly to main (except hotfixes)

