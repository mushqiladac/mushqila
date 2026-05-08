# GitHub Actions Deployment Fix

## Problem
GitHub Actions deployment is failing after pushing code.

## Possible Causes

### 1. Missing GitHub Secrets ⚠️
The workflow requires 3 secrets that might not be configured:
- `EC2_HOST` - EC2 instance hostname
- `EC2_USERNAME` - SSH username (ubuntu)
- `EC2_SSH_KEY` - Private SSH key

### 2. SSH Connection Issues
- Invalid SSH key
- EC2 security group blocking GitHub Actions IP
- Wrong hostname or username

### 3. Docker Build Issues
- Insufficient disk space on EC2
- Docker daemon not running
- Build errors in Dockerfile

### 4. Database Connection Issues
- Wrong RDS credentials in .env.production
- RDS security group blocking EC2

## Quick Fix Steps

### Step 1: Check GitHub Secrets

Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions

Verify these secrets exist:
- ✅ EC2_HOST
- ✅ EC2_USERNAME  
- ✅ EC2_SSH_KEY

If missing, add them:

**EC2_HOST:**
```
ec2-16-171-21-135.eu-north-1.compute.amazonaws.com
```

**EC2_USERNAME:**
```
ubuntu
```

**EC2_SSH_KEY:**
```
-----BEGIN RSA PRIVATE KEY-----
[Your private key content here]
-----END RSA PRIVATE KEY-----
```

### Step 2: Disable Auto-Deploy (Temporary)

If you want to deploy manually instead:

```bash
# Rename workflow file to disable it
git mv .github/workflows/deploy.yml .github/workflows/deploy.yml.disabled
git commit -m "chore: Temporarily disable auto-deploy"
git push origin main
```

### Step 3: Manual Deployment

Deploy manually via SSH:

```bash
# SSH to EC2
ssh ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com

# Navigate to project
cd ~/mushqila

# Pull latest code
git pull origin main

# Deploy
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for startup
sleep 20

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Step 4: View GitHub Actions Logs

1. Go to: https://github.com/mushqiladac/mushqila/actions
2. Click on the failed workflow run
3. Click "deploy" job
4. Look for the error message (usually in red)

Common errors:
- **"Input required and not supplied: host"** → Missing EC2_HOST secret
- **"Permission denied (publickey)"** → Invalid SSH key
- **"Connection refused"** → Wrong hostname or EC2 not accessible
- **"Error response from daemon"** → Docker build issue
- **"Health check failed"** → Site not accessible after deployment

## Simplified Workflow (Alternative)

If the current workflow is too complex, here's a simpler version:

```yaml
name: Deploy to Production

on:
  workflow_dispatch:  # Manual trigger only

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /home/ubuntu/mushqila
            git pull origin main
            docker-compose -f docker-compose.prod.yml up -d --build
```

Save this as `.github/workflows/deploy-simple.yml` for manual deployments only.

## Recommended Approach

**For now, I recommend:**

1. ✅ **Disable auto-deploy** (rename workflow file)
2. ✅ **Deploy manually via SSH** (more reliable)
3. ✅ **Fix GitHub secrets** (add missing secrets)
4. ✅ **Test workflow manually** (workflow_dispatch)
5. ✅ **Re-enable auto-deploy** (when working)

## Manual Deploy Command (One-liner)

```bash
ssh ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com "cd ~/mushqila && git pull origin main && docker-compose -f docker-compose.prod.yml up -d --build && sleep 20 && docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate && docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput"
```

## Check Current Deployment Status

```bash
# Check if site is accessible
curl -I https://mushqila.com/accounts/login/

# Expected: HTTP/2 200 or HTTP/2 302
```

## Next Steps

1. **Check GitHub Actions logs** to see exact error
2. **Add missing secrets** if needed
3. **Deploy manually** for now
4. **Fix workflow** once we know the error
5. **Test workflow** with workflow_dispatch trigger

---

**Status**: Waiting for GitHub Actions log details
**Recommendation**: Deploy manually via SSH for now
