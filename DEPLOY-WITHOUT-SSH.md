# 🚀 Deploy Without SSH Access

## Problem
SSH key not working: `Permission denied (publickey)`

This means the SSH key doesn't match what's authorized on EC2.

---

## Solution Options

### Option 1: AWS Console - EC2 Instance Connect (Easiest)

1. **Go to AWS Console**: https://console.aws.amazon.com/ec2/

2. **Find your instance**:
   - Services → EC2
   - Instances → Find instance with IP 16.170.25.9

3. **Connect using EC2 Instance Connect**:
   - Select your instance
   - Click **Connect** button (top right)
   - Choose **EC2 Instance Connect** tab
   - Click **Connect**

4. **Run deployment commands**:
   ```bash
   cd /home/ubuntu/mushqila
   git pull origin main
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d --build
   sudo systemctl restart nginx
   docker-compose -f docker-compose.prod.yml exec web python manage.py create_email_accounts
   ```

---

### Option 2: AWS Systems Manager (SSM)

If EC2 Instance Connect doesn't work:

1. **Go to AWS Console**: https://console.aws.amazon.com/systems-manager/

2. **Session Manager**:
   - Left sidebar → Session Manager
   - Click **Start session**
   - Select your EC2 instance
   - Click **Start session**

3. **Switch to ubuntu user**:
   ```bash
   sudo su - ubuntu
   cd ~/mushqila
   ```

4. **Run deployment commands** (same as above)

---

### Option 3: Fix SSH Key (Permanent Solution)

#### Step 1: Generate New Key Pair in AWS

1. **AWS Console** → EC2 → Key Pairs
2. **Create key pair**:
   - Name: `mushqila-deploy-key`
   - Type: RSA
   - Format: .pem
   - Click **Create**
3. **Download** the new key (save it safely!)

#### Step 2: Add New Key to EC2 Instance

Using EC2 Instance Connect or SSM:

```bash
# Add your new public key
echo "YOUR_NEW_PUBLIC_KEY" >> ~/.ssh/authorized_keys

# Fix permissions
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

#### Step 3: Test New Key

```powershell
# Windows
ssh -i "path\to\mushqila-deploy-key.pem" ubuntu@16.170.25.9
```

#### Step 4: Update GitHub Secret

1. Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions
2. Update `EC2_SSH_KEY` with new key content
3. Re-run GitHub Actions workflow

---

### Option 4: Use Existing Key (If You Have Another One)

Do you have another .pem file that works? Try:

```powershell
# List all .pem files
Get-ChildItem -Path C:\Users\user -Recurse -Filter *.pem -ErrorAction SilentlyContinue

# Try each one
ssh -i "path\to\other-key.pem" ubuntu@16.170.25.9
```

---

## Quick Deploy via AWS Console (Recommended Now)

### Step-by-Step:

1. **Open AWS Console**: https://console.aws.amazon.com/ec2/

2. **Go to EC2 Instances**

3. **Find instance** with IP `16.170.25.9`

4. **Click Connect** button

5. **Choose "EC2 Instance Connect"**

6. **Click Connect** (opens terminal in browser)

7. **Run these commands**:
   ```bash
   # Switch to ubuntu user
   sudo su - ubuntu
   
   # Go to project
   cd ~/mushqila
   
   # Pull latest code
   git pull origin main
   
   # Deploy
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d --build
   
   # Wait 10 seconds
   sleep 10
   
   # Restart Nginx
   sudo systemctl restart nginx
   
   # Create email accounts
   docker-compose -f docker-compose.prod.yml exec web python manage.py create_email_accounts
   
   # Check status
   docker-compose -f docker-compose.prod.yml ps
   
   # Test
   curl http://localhost:8000/
   ```

8. **Open browser**: https://mushqila.com

---

## Why SSH Key Not Working?

Possible reasons:
1. **Wrong key**: This key wasn't used to create the EC2 instance
2. **Key not authorized**: Public key not in `~/.ssh/authorized_keys`
3. **Different instance**: This key is for a different EC2 instance
4. **Key changed**: EC2 instance was recreated with different key

---

## For Future: Setup Proper SSH Access

Once you have console access:

### 1. Check Current Authorized Keys
```bash
cat ~/.ssh/authorized_keys
```

### 2. Add Your Key
```bash
# Get your public key from private key
ssh-keygen -y -f /path/to/mhcl-key.pem

# Add to authorized keys
echo "YOUR_PUBLIC_KEY" >> ~/.ssh/authorized_keys
```

### 3. Test
```powershell
ssh -i "C:\Users\user\Desktop\Mushqila\mhcl-key.pem" ubuntu@16.170.25.9
```

---

## Summary

**Right Now:**
1. Use AWS Console → EC2 Instance Connect
2. Run deployment commands
3. Site will be live

**Later:**
1. Fix SSH key issue
2. Update GitHub Actions secret
3. Automatic deployments will work

**Use AWS Console EC2 Instance Connect - it's the fastest way!** 🚀

---

## AWS Console Login

If you don't remember:
- URL: https://console.aws.amazon.com/
- Account ID: (check your AWS account)
- Username: (your IAM user)
- Password: (your password)

Or use root account email/password.
