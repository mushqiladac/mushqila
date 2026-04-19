# Deployment Status

## Latest Deployment

**Commit**: `3395e17` - fix: Add webmail logout functionality and fix admin CSRF logout issue

**Pushed**: Just now

**Status**: 🚀 Deploying via GitHub Actions

---

## Changes Deployed

### Webmail Logout Feature
✅ Added webmail logout view
✅ Added logout URL route
✅ Added logout button in sidebar with confirmation
✅ Logout redirects to login page with success message

### Admin CSRF Fix
✅ Fixed admin logout CSRF verification failed error
✅ Added CSRF_TRUSTED_ORIGINS configuration
✅ Updated .env and .env.example files

---

## How to Monitor Deployment

### 1. GitHub Actions
Visit: https://github.com/mushqiladac/mushqila/actions

You'll see:
- ✅ Green checkmark = Deployment successful
- 🟡 Yellow circle = Deployment in progress
- ❌ Red X = Deployment failed

### 2. Check Deployment Logs

Click on the latest workflow run to see:
- Code checkout
- Docker build
- Container restart
- Database migrations
- Static files collection
- Health check

### 3. Verify Deployment

After deployment completes (usually 5-10 minutes):

**Test Admin Logout:**
1. Visit: https://mushqila.com/admin/
2. Login with admin credentials
3. Click logout
4. Should logout without CSRF error ✅

**Test Webmail Logout:**
1. Visit: https://mushqila.com/webmail/
2. Login with webmail credentials
3. Click "Logout" in sidebar
4. Confirm logout
5. Should redirect to login page ✅

---

## Deployment Timeline

```
[Push to GitHub] → [GitHub Actions Triggered] → [Deploy to EC2]
     ↓                      ↓                          ↓
  Instant            Starts in ~30s              5-10 minutes
```

### Deployment Steps (Automated):

1. **Pull Code** (30s)
   - Fetch latest from GitHub
   - Reset to origin/main

2. **Stop Containers** (30s)
   - Stop running containers
   - Clean up old data

3. **Build Image** (3-5 min)
   - Build fresh Docker image
   - Install dependencies

4. **Start Containers** (1 min)
   - Start web, db, nginx containers
   - Wait for startup

5. **Run Migrations** (30s)
   - Apply database changes
   - Update schema

6. **Collect Static** (30s)
   - Gather CSS, JS, images
   - Prepare for serving

7. **Health Check** (10s)
   - Verify site is accessible
   - Check HTTP status

---

## Troubleshooting

### If Deployment Fails:

1. **Check GitHub Actions Logs**
   - Click on failed workflow
   - Read error messages
   - Look for specific step that failed

2. **Common Issues:**

   **Build Failed:**
   - Check requirements.txt
   - Verify Python dependencies
   - Check Dockerfile syntax

   **Migration Failed:**
   - Check migration files
   - Verify database connection
   - Check for conflicts

   **Container Won't Start:**
   - Check docker-compose.prod.yml
   - Verify environment variables
   - Check port conflicts

3. **Manual Rollback:**
   ```bash
   ssh ubuntu@mushqila.com
   cd /home/ubuntu/mushqila
   git log --oneline -5  # See recent commits
   git reset --hard <previous-commit-hash>
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

---

## Environment Variables on Server

Make sure these are set in `/home/ubuntu/mushqila/.env.production`:

```env
# CSRF Configuration (IMPORTANT!)
CSRF_TRUSTED_ORIGINS=https://mushqila.com,https://www.mushqila.com

# Other required variables
SECRET_KEY=<production-secret-key>
DEBUG=False
ALLOWED_HOSTS=mushqila.com,www.mushqila.com
DB_NAME=mushqila_prod
DB_USER=mushqila_user
DB_PASSWORD=<secure-password>
# ... etc
```

---

## Post-Deployment Checklist

After deployment completes:

- [ ] Admin login works
- [ ] Admin logout works (no CSRF error)
- [ ] Webmail login works
- [ ] Webmail logout works
- [ ] Static files loading (CSS, JS, images)
- [ ] Database queries working
- [ ] Email sending works (if configured)
- [ ] All pages accessible

---

## Quick Commands

### Check Deployment Status:
```bash
# SSH to server
ssh ubuntu@mushqila.com

# Check containers
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Check Django
docker-compose -f docker-compose.prod.yml exec web python manage.py check
```

### Manual Deployment (if needed):
```bash
ssh ubuntu@mushqila.com
cd /home/ubuntu/mushqila
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## Support

If deployment fails or issues occur:
1. Check GitHub Actions logs
2. SSH to server and check Docker logs
3. Review error messages
4. Check environment variables
5. Verify database connection

---

**Last Updated**: Just now
**Next Deployment**: Automatic on next push to main branch
