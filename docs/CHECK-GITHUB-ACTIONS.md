# GitHub Actions Deployment Troubleshooting

## Required Secrets

The deployment workflow requires these GitHub Secrets to be configured:

### 1. EC2_HOST
- **Value**: `ec2-16-171-21-135.eu-north-1.compute.amazonaws.com` or IP `16.171.21.135`
- **Description**: EC2 instance hostname or IP address

### 2. EC2_USERNAME
- **Value**: `ubuntu`
- **Description**: SSH username for EC2 instance

### 3. EC2_SSH_KEY
- **Value**: Private SSH key content
- **Description**: The private key used to SSH into the EC2 instance

## How to Check Secrets

1. Go to GitHub repository: https://github.com/mushqiladac/mushqila
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Verify all three secrets exist:
   - `EC2_HOST`
   - `EC2_USERNAME`
   - `EC2_SSH_KEY`

## Common Failure Reasons

### 1. Missing or Invalid Secrets
**Symptom**: "Error: Input required and not supplied: host"
**Solution**: Add the missing secret in GitHub repository settings

### 2. SSH Key Permission Denied
**Symptom**: "Permission denied (publickey)"
**Solution**: 
- Verify EC2_SSH_KEY contains the correct private key
- Ensure the key matches the public key in EC2 instance's `~/.ssh/authorized_keys`

### 3. Docker Build Failure
**Symptom**: "Error response from daemon" or build errors
**Solution**:
- Check if EC2 instance has enough disk space
- Check if Docker is running on EC2
- Review build logs for specific errors

### 4. Database Connection Issues
**Symptom**: "psycopg2.OperationalError: connection failed"
**Solution**:
- Verify `.env.production` has correct AWS RDS credentials
- Check RDS security group allows EC2 instance

### 5. Health Check Failure
**Symptom**: "Health check failed: HTTP 502"
**Solution**:
- Check if containers are running: `docker-compose -f docker-compose.prod.yml ps`
- Check logs: `docker-compose -f docker-compose.prod.yml logs web`
- Verify Nginx is properly configured

## How to View GitHub Actions Logs

1. Go to: https://github.com/mushqiladac/mushqila/actions
2. Click on the failed workflow run
3. Click on the "deploy" job
4. Expand each step to see detailed logs
5. Look for error messages (usually in red)

## Manual Deployment (If GitHub Actions Fails)

If GitHub Actions continues to fail, deploy manually:

```bash
# SSH to EC2
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

## Workflow Steps Explained

### Step 1: Checkout code
- Downloads repository code to GitHub Actions runner
- Should always succeed

### Step 2: Deploy to EC2
- **Connects via SSH** to EC2 instance
- **Pulls latest code** from GitHub
- **Stops old containers**
- **Cleans Docker cache**
- **Builds fresh image**
- **Starts containers**
- **Runs migrations**
- **Collects static files**

### Step 3: Health Check
- Waits 10 seconds
- Checks if https://mushqila.com/accounts/login/ returns 200 or 302
- Fails if site is not accessible

## Debugging Commands

### Check if secrets are being used correctly:
```bash
# On EC2, check if deployment script ran
ls -la /home/ubuntu/mushqila/.git/
git log -1

# Check Docker status
docker ps -a
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs web --tail=100
docker-compose -f docker-compose.prod.yml logs nginx --tail=50
```

### Check EC2 resources:
```bash
# Disk space
df -h

# Memory
free -h

# Docker disk usage
docker system df
```

## Fix GitHub Actions Secrets

If secrets are missing or incorrect:

### 1. Get EC2 SSH Key
```bash
# On your local machine where you have the key
cat ~/.ssh/mushqila-key.pem
# or
cat ~/.ssh/id_rsa
```

### 2. Add to GitHub
1. Copy the entire private key (including BEGIN and END lines)
2. Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions
3. Click "New repository secret"
4. Name: `EC2_SSH_KEY`
5. Value: Paste the private key
6. Click "Add secret"

### 3. Add EC2_HOST
- Name: `EC2_HOST`
- Value: `ec2-16-171-21-135.eu-north-1.compute.amazonaws.com`

### 4. Add EC2_USERNAME
- Name: `EC2_USERNAME`
- Value: `ubuntu`

## Test SSH Connection Locally

Before relying on GitHub Actions, test SSH locally:

```bash
# Test SSH connection
ssh -i ~/.ssh/mushqila-key.pem ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com

# If successful, you should see Ubuntu prompt
ubuntu@ip-172-31-36-20:~$
```

## Disable GitHub Actions (Temporary)

If you want to disable auto-deployment temporarily:

1. Rename `.github/workflows/deploy.yml` to `.github/workflows/deploy.yml.disabled`
2. Commit and push
3. Deploy manually via SSH

## Re-enable GitHub Actions

1. Rename back to `.github/workflows/deploy.yml`
2. Commit and push
3. Workflow will run automatically

## Current Status Check

To check current deployment status:

```bash
# SSH to server
ssh ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com

# Check containers
cd ~/mushqila
docker-compose -f docker-compose.prod.yml ps

# Check if site is accessible
curl -I https://mushqila.com/accounts/login/
```

## Expected Output

### Successful Deployment:
```
✅ Code updated
✅ Containers stopped
✅ Docker cleaned
✅ Image built
✅ Containers started
✅ Migrations done
✅ Static files collected
✅ Deployment Complete!
✅ Site is live!
```

### Failed Deployment:
Look for error messages like:
- ❌ Permission denied
- ❌ Error response from daemon
- ❌ Health check failed
- ❌ Connection refused

## Next Steps

1. **Check GitHub Actions logs** at: https://github.com/mushqiladac/mushqila/actions
2. **Identify the specific error** from the logs
3. **Fix the issue** based on error type
4. **Re-run the workflow** or push a new commit
5. **Verify deployment** by checking https://mushqila.com

## Contact Information

If deployment continues to fail:
1. Share the GitHub Actions log output
2. Share EC2 container logs: `docker-compose -f docker-compose.prod.yml logs web`
3. Share any error messages from the workflow

---

**Last Updated**: May 8, 2026
**Status**: Troubleshooting Guide Ready
