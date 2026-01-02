# Safe Merge Process: Staging → Main

This process ensures staging changes are safely merged to production without introducing errors.

## Pre-Merge Checklist

Before merging staging → main, verify:

### 1. Staging Works Completely
- [ ] All features work in staging
- [ ] No console errors
- [ ] No API errors
- [ ] Login works
- [ ] Clients load
- [ ] Pages load
- [ ] Admin works (if applicable)
- [ ] All tabs functional

### 2. Schema Verification
- [ ] Staging schema matches production (use SQL comparison query)
- [ ] All migrations have been run in production (if new migrations added)
- [ ] No breaking schema changes that need coordination

### 3. Environment Variables
- [ ] Production env vars are set correctly
- [ ] No new env vars needed in production
- [ ] All env vars documented

### 4. Code Review
- [ ] Review all changes in staging branch
- [ ] Check for breaking changes
- [ ] Verify no production-only code was modified
- [ ] Ensure no hardcoded staging URLs

### 5. Testing
- [ ] Test critical user flows
- [ ] Test edge cases
- [ ] Test error handling
- [ ] Verify no regressions

## Merge Process

### Step 1: Final Staging Verification
```bash
# Make sure staging branch is up to date
git checkout staging
git pull origin staging

# Verify latest commit
git log -1
```

### Step 2: Create Merge Commit
```bash
# Switch to main
git checkout main
git pull origin main

# Merge staging into main
git merge staging --no-ff -m "Merge staging into main: [brief description]"

# Review the merge
git log --oneline -5
```

### Step 3: Push to Production
```bash
# Push to main (triggers production deployment)
git push origin main
```

### Step 4: Monitor Deployment
1. Watch Vercel deployment logs
2. Watch Render deployment logs
3. Check for errors
4. Verify deployment succeeded

### Step 5: Post-Deploy Verification
1. Test production site
2. Check critical features
3. Monitor error logs
4. Verify no regressions

## Rollback Plan

If something goes wrong:

### Immediate Rollback
```bash
# Revert the merge commit
git revert -m 1 HEAD
git push origin main
```

### Partial Rollback
If only specific changes are problematic:
1. Create hotfix branch from previous main
2. Cherry-pick only safe commits
3. Merge hotfix to main

## Best Practices

### 1. Small, Frequent Merges
- Merge small batches of changes
- Easier to test and verify
- Easier to rollback if needed

### 2. Feature Flags
- Use feature flags for risky changes
- Can enable/disable without redeploy
- Safer for production

### 3. Staged Rollouts
- Deploy to small percentage first
- Monitor for issues
- Gradually increase

### 4. Communication
- Notify team before major merges
- Document breaking changes
- Share rollback plan

## Common Pitfalls to Avoid

1. **Merging Without Testing**: Always test in staging first
2. **Large Batches**: Small merges are safer
3. **Skipping Verification**: Always verify staging works
4. **Ignoring Warnings**: Address warnings before merging
5. **No Rollback Plan**: Always have a rollback plan

## Emergency Procedures

If production breaks:

1. **Immediate**: Revert the merge (see Rollback Plan)
2. **Investigate**: Check logs, identify issue
3. **Fix**: Create hotfix branch
4. **Test**: Test fix in staging
5. **Deploy**: Merge hotfix to main
6. **Verify**: Confirm fix works

## Post-Merge

After successful merge:

1. **Monitor**: Watch production for 24-48 hours
2. **Logs**: Check error logs regularly
3. **Metrics**: Monitor performance metrics
4. **Feedback**: Collect user feedback
5. **Document**: Document any issues and fixes

