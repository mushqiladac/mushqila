# GitHub Actions Automatic Deployment Setup

## Overview
এই guide অনুসরণ করে আপনি GitHub থেকে automatic deployment enable করতে পারবেন। একবার setup করলে, যখনই আপনি GitHub এ code push করবেন, automatically EC2 তে deploy হবে।

## Prerequisites
- ✅ EC2 instance running (13.60.112.227)
- ✅ Docker installed on EC2
- ✅ Repository cloned on EC2 (`~/mushqila`)
- ✅ `.env.production` file created on EC2

## Step 1: EC2 SSH Key Setup

### Option A: Use Existing Key (Recommended)
যদি আপনার কাছে EC2 এর SSH private key থাকে (`keys-mhcl.pem`):

1. Key file open করুন
2. পুরো content copy করুন (-----BEGIN RSA PRIVATE KEY----- থেকে -----END RSA PRIVATE KEY----- পর্যন্ত)

### Option B: Create New Key Pair
যদি key না থাকে, EC2 তে নতুন key pair তৈরি করুন:

```bash
# EC2 Instance Connect terminal এ run করুন
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy
```

Private key copy করুন (output থেকে)

## Step 2: GitHub Secrets Setup

1. **GitHub repository তে যান**: https://github.com/mushqiladac/mushqila

2. **Settings** → **Secrets and variables** → **Actions** এ যান

3. **New repository secret** click করুন

4. এই secret add করুন:
   - **Name**: `EC2_SSH_KEY`
   - **Value**: আপনার SSH private key paste করুন
   
5. **Add secret** click করুন

## Step 3: Test Deployment

### Manual Trigger (Test করার জন্য)
1. GitHub repository তে যান
2. **Actions** tab এ click করুন
3. **Deploy to AWS EC2** workflow select করুন
4. **Run workflow** button click করুন
5. **Run workflow** confirm করুন

### Automatic Trigger
এখন যখনই আপনি `main` branch এ code push করবেন, automatically deployment হবে:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

## Step 4: Monitor Deployment

GitHub Actions tab এ গিয়ে deployment progress দেখতে পারবেন:
- ✅ Green checkmark = Success
- ❌ Red X = Failed
- 🟡 Yellow dot = In progress

## Deployment Process

Workflow automatically এই steps করবে:
1. ✅ Latest code pull করবে
2. ✅ Docker containers rebuild করবে
3. ✅ Containers restart করবে
4. ✅ Database migrations run করবে
5. ✅ Static files collect করবে

## Troubleshooting

### Error: "Permission denied (publickey)"
**Solution**: GitHub Secrets এ `EC2_SSH_KEY` সঠিকভাবে add করা আছে কিনা check করুন

### Error: "Repository not found"
**Solution**: EC2 তে manually repository clone করুন:
```bash
cd ~
git clone https://github.com/mushqiladac/mushqila.git
```

### Error: "docker-compose: command not found"
**Solution**: EC2 তে Docker Compose install করুন:
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Current Configuration

- **EC2 IP**: 13.60.112.227
- **EC2 User**: ubuntu
- **Project Path**: /home/ubuntu/mushqila
- **Deployment File**: docker-compose.prod.yml

## Next Steps

1. ✅ GitHub Secret add করুন (`EC2_SSH_KEY`)
2. ✅ Test deployment run করুন
3. ✅ Code changes push করে automatic deployment test করুন

## Security Notes

- ⚠️ SSH private key কখনো code এ commit করবেন না
- ⚠️ GitHub Secrets secure এবং encrypted
- ⚠️ `.env.production` file এ sensitive data আছে, এটা `.gitignore` এ add করা আছে

## Support

যদি কোনো problem হয়:
1. GitHub Actions logs check করুন
2. EC2 তে manually commands run করে test করুন
3. Container logs check করুন: `docker-compose -f docker-compose.prod.yml logs`
