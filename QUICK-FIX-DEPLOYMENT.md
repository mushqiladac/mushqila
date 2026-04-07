# ⚡ Quick Fix: GitHub Actions Deployment Failed

## Problem
GitHub Actions deployment failed with SSH authentication error.

## Quick Solution (5 minutes)

### Option 1: Fix GitHub Secret (Recommended)

1. **Get your SSH key**:
   ```powershell
   # Windows PowerShell
   Get-Content your-key.pem
   ```

2. **Copy the ENTIRE output** (including `-----BEGIN` and `-----END` lines)

3. **Update GitHub Secret**:
   - Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions
   - Delete old `EC2_SSH_KEY`
   - Create new `EC2_SSH_KEY` with copied content
   - Save

4. **Re-run workflow**:
   - Go to: https://github.com/mushqiladac/mushqila/actions
   - Click failed workflow
   - Click "Re-run all jobs"

---

### Option 2: Manual Deployment (Faster for now)

Since GitHub Actions is failing, deploy manually:

```bash
# 1. SSH to EC2
ssh -i your-key.pem ubuntu@16.170.25.9

# 2. Navigate to project
cd ~/mushqila

# 3. Pull latest code
git pull origin main

# 4. Stop containers
docker-compose -f docker-compose.prod.yml down

# 5. Rebuild and start
docker-compose -f docker-compose.prod.yml up -d --build

# 6. Wait 10 seconds
sleep 10

# 7. Check status
docker-compose -f docker-compose.prod.yml ps

# 8. Restart Nginx
sudo systemctl restart nginx

# 9. Test
curl http://localhost:8000/
curl https://mushqila.com/
```

---

## What to Do Now

### Immediate Action (Manual Deploy):
```bash
ssh -i your-key.pem ubuntu@16.170.25.9
cd ~/mushqila
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
sudo systemctl restart nginx
```

### Later (Fix GitHub Actions):
1. Update EC2_SSH_KEY secret with correct key
2. Re-run the workflow
3. Future deployments will be automatic

---

## Verify Deployment

After manual deployment:

```bash
# Check containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs --tail=20 web

# Test site
curl https://mushqila.com/
```

Open browser: https://mushqila.com

---

## Create Email Accounts

After site is working:

```bash
# On EC2
docker-compose -f docker-compose.prod.yml exec web python manage.py create_email_accounts
```

This will create:
- shahin_sarker@mushqila.com
- aysha@mushqila.com
- refat@mushqila.com
- support@mushqila.com
- eliuss@mushqila.com

---

## Summary

1. **Now**: Deploy manually (commands above)
2. **Later**: Fix GitHub Actions SSH key
3. **Then**: Automatic deployments will work

**Run the manual deployment commands now to get site working!** 🚀
