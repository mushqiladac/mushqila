# GitHub Secrets Setup for CI/CD

## Required Secrets

আপনার GitHub repository তে এই secrets add করতে হবে:

### 1. EC2_HOST
- Value: `13.60.112.227`
- Description: EC2 server এর IP address

### 2. EC2_USERNAME
- Value: `ubuntu`
- Description: EC2 server এর username

### 3. EC2_SSH_KEY
- Value: আপনার `.pem` file এর content
- Description: EC2 server এ SSH করার জন্য private key

---

## How to Add Secrets

### Step 1: GitHub Repository তে যান
1. https://github.com/mushqiladac/sinan যান
2. **Settings** tab এ click করুন
3. Left sidebar এ **Secrets and variables** > **Actions** click করুন

### Step 2: Secrets Add করুন

#### EC2_HOST Secret:
1. **New repository secret** button click করুন
2. Name: `EC2_HOST`
3. Value: `13.60.112.227`
4. **Add secret** click করুন

#### EC2_USERNAME Secret:
1. **New repository secret** button click করুন
2. Name: `EC2_USERNAME`
3. Value: `ubuntu`
4. **Add secret** click করুন

#### EC2_SSH_KEY Secret:
1. **New repository secret** button click করুন
2. Name: `EC2_SSH_KEY`
3. Value: আপনার `.pem` file এর পুরো content copy করে paste করুন
   
   **Important:** 
   - `.pem` file টি Notepad দিয়ে open করুন
   - পুরো content copy করুন (including `-----BEGIN RSA PRIVATE KEY-----` এবং `-----END RSA PRIVATE KEY-----`)
   - GitHub secret field এ paste করুন
   
4. **Add secret** click করুন

---

## Verify Setup

Secrets add করার পর:

1. Repository এর **Actions** tab এ যান
2. **Deploy to EC2** workflow দেখতে পাবেন
3. **Run workflow** button click করে manually test করতে পারেন

---

## Automatic Deployment

এখন থেকে যখনই আপনি `dwd` branch এ code push করবেন:

```bash
git add .
git commit -m "Your commit message"
git push origin dwd
```

Automatically:
1. GitHub Actions trigger হবে
2. EC2 server এ SSH করবে
3. Latest code pull করবে
4. Docker containers rebuild করবে
5. Migrations run করবে
6. Static files collect করবে
7. Application restart হবে

---

## Monitor Deployment

Deployment status দেখতে:
1. GitHub repository এর **Actions** tab এ যান
2. Latest workflow run click করুন
3. Real-time logs দেখতে পারবেন

---

## Troubleshooting

### যদি deployment fail হয়:

1. **Actions** tab এ error logs check করুন
2. EC2 server এ manually SSH করে check করুন:
   ```bash
   ssh -i your-key.pem ubuntu@13.60.112.227
   cd ~/mushqila
   docker-compose -f docker-compose.prod.yml logs
   ```

### Common Issues:

1. **SSH Key Error**: 
   - `.pem` file এর পুরো content correctly copy করেছেন কিনা check করুন
   - Line breaks ঠিক আছে কিনা verify করুন

2. **Permission Denied**:
   - EC2 Security Group এ port 22 (SSH) open আছে কিনা check করুন
   - SSH key সঠিক কিনা verify করুন

3. **Docker Build Failed**:
   - EC2 server এ disk space আছে কিনা check করুন: `df -h`
   - Old images clean করুন: `docker system prune -a`

---

## Next Steps

1. ✅ GitHub Secrets add করুন
2. ✅ `.github/workflows/deploy.yml` file push করুন
3. ✅ Test করুন manually workflow run করে
4. ✅ Code change করে push করে automatic deployment test করুন

