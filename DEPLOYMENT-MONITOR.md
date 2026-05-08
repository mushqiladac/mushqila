# Deployment Monitor - GitHub Actions

## Current Deployment

**Workflow**: Deploy to Production #107  
**Commit**: `4318800` - Finance login dashboard redirect fix  
**Triggered by**: mushqiladac (push to main)  
**Status**: 🟡 In Progress

## Monitor Deployment

### GitHub Actions URL
```
https://github.com/mushqiladac/mushqila/actions/runs/latest
```

Or go to:
1. https://github.com/mushqiladac/mushqila
2. Click "Actions" tab
3. Click on "Deploy to Production #107"

## Deployment Steps (Automated)

### ✅ Step 1: Checkout Code
- Downloads latest code from GitHub
- Usually completes in ~5 seconds

### 🔄 Step 2: Deploy to EC2
This step includes multiple sub-steps:

1. **SSH Connection** (~5 sec)
   - Connects to EC2 server
   - Authenticates with SSH key

2. **Pull Latest Code** (~10 sec)
   - `git fetch origin main`
   - `git reset --hard origin/main`

3. **Stop Old Containers** (~10 sec)
   - `docker-compose -f docker-compose.prod.yml down`

4. **Clean Docker Cache** (~30 sec)
   - `docker system prune -af --volumes`

5. **Build Fresh Image** (~5-8 min)
   - `docker-compose -f docker-compose.prod.yml build --no-cache`
   - This is the longest step

6. **Start Containers** (~20 sec)
   - `docker-compose -f docker-compose.prod.yml up -d`

7. **Wait for Startup** (~20 sec)
   - Allows containers to initialize

8. **Run Migrations** (~10 sec)
   - `python manage.py migrate --noinput`

9. **Collect Static Files** (~15 sec)
   - `python manage.py collectstatic --noinput --clear`

10. **Show Status** (~5 sec)
    - `docker-compose ps`

**Total Time**: ~10-15 minutes

### 🔄 Step 3: Health Check
- Waits 10 seconds
- Checks https://mushqila.com/accounts/login/
- Expected: HTTP 200 or 302
- If fails: Deployment marked as failed

## Expected Timeline

```
00:00 - Deployment started
00:05 - Code checked out
00:15 - SSH connected, pulling code
00:25 - Old containers stopped
00:55 - Docker cache cleaned
08:00 - Fresh image built (longest step)
08:20 - New containers started
08:40 - Waiting for startup
08:50 - Migrations running
09:05 - Static files collected
09:10 - Health check
09:20 - ✅ Deployment complete!
```

## Check Deployment Status

### Option 1: GitHub Actions UI
1. Go to: https://github.com/mushqiladac/mushqila/actions
2. Look for green ✅ or red ❌
3. Click on workflow to see details

### Option 2: Check Website
```bash
# Check if site is accessible
curl -I https://mushqila.com/accounts/login/

# Expected: HTTP/2 200 or HTTP/2 302
```

### Option 3: SSH to Server
```bash
# SSH to production
ssh ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com

# Check container status
cd ~/mushqila
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs web --tail=50
```

## After Deployment Completes

### Test Finance Login
```
URL: https://mushqila.com/finance/login/
Email: saddam110@mushqila.com
Password: Sinan210
User Type: এডমিন

Expected Result:
✅ সফলভাবে লগইন হয়েছে!
✅ Redirect to: https://mushqila.com/finance/dashboard/
✅ No "dashboard not found" error
✅ Dashboard loads properly
```

### Test Admin Panel
```
URL: https://mushqila.com/admin/
Expected: Login page with proper styling (no 500 error)
```

### Test Main Site
```
URL: https://mushqila.com/
Expected: Landing page loads
```

### Test B2B Login
```
URL: https://mushqila.com/accounts/login/
Expected: Login page loads
```

## If Deployment Fails

### Check GitHub Actions Logs
1. Go to failed workflow
2. Click on "deploy" job
3. Expand failed step
4. Look for error message

### Common Failures

#### 1. SSH Connection Failed
**Error**: "Permission denied (publickey)"
**Solution**: Check GitHub Secrets (EC2_SSH_KEY)

#### 2. Docker Build Failed
**Error**: "Error response from daemon"
**Solution**: 
- Check Dockerfile syntax
- Check if EC2 has enough disk space
- SSH to server and check logs

#### 3. Database Migration Failed
**Error**: "OperationalError"
**Solution**:
- Check database credentials in .env.production
- Verify RDS is accessible
- Check RDS security group

#### 4. Health Check Failed
**Error**: "Health check failed: HTTP 502"
**Solution**:
- Check container logs
- Verify nginx is running
- Check if web container is healthy

### Manual Deployment (If GitHub Actions Fails)

```bash
# SSH to server
ssh ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com

# Navigate to project
cd ~/mushqila

# Pull latest code
git pull origin main

# Deploy
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Wait and run migrations
sleep 20
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Check status
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs web --tail=50
```

## Deployment Checklist

After deployment completes, verify:

- [ ] GitHub Actions shows green ✅
- [ ] Main site loads: https://mushqila.com/
- [ ] Admin panel loads: https://mushqila.com/admin/
- [ ] Finance login works: https://mushqila.com/finance/login/
- [ ] Finance dashboard loads without errors
- [ ] B2B login works: https://mushqila.com/accounts/login/
- [ ] Webmail loads: https://mushqila.com/webmail/login/
- [ ] No 500 errors in logs
- [ ] Static files loading properly

## Rollback (If Needed)

If deployment causes issues:

```bash
# SSH to server
ssh ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com

# Navigate to project
cd ~/mushqila

# Rollback to previous commit
git log --oneline -5  # See recent commits
git reset --hard <previous-commit-hash>

# Redeploy
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## Monitoring Commands

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View logs (live)
docker-compose -f docker-compose.prod.yml logs -f web

# Check last 100 lines
docker-compose -f docker-compose.prod.yml logs web --tail=100

# Check for errors
docker-compose -f docker-compose.prod.yml logs web | grep ERROR

# Check disk space
df -h

# Check memory
free -h

# Check Docker disk usage
docker system df
```

## Success Indicators

### ✅ Deployment Successful
- GitHub Actions shows green checkmark
- All containers running (web, db, redis, celery, nginx)
- Health check passed (HTTP 200/302)
- No errors in logs
- Website accessible

### ❌ Deployment Failed
- GitHub Actions shows red X
- Containers not running or restarting
- Health check failed (HTTP 502/500)
- Errors in logs
- Website not accessible

## Current Deployment Status

**Started**: When you pushed to GitHub  
**Expected Completion**: ~10-15 minutes from start  
**Monitor at**: https://github.com/mushqiladac/mushqila/actions

## What Was Deployed

### Finance Login Fix
- Changed `redirect('finance:dashboard')` to `HttpResponseRedirect(reverse('finance:dashboard'))`
- Bypasses Django's LOGIN_REDIRECT_URL setting
- Fixes "dashboard not found" error
- File: `finance/views/web_views.py`

### Expected Impact
- ✅ Finance login will work without errors
- ✅ Users will be redirected to finance dashboard
- ✅ No more "Reverse for 'dashboard' not found" error
- ✅ All user types (admin, manager, user) can login

---

**Status**: Deployment in progress via GitHub Actions  
**Monitor**: https://github.com/mushqiladac/mushqila/actions  
**ETA**: ~10-15 minutes from push
