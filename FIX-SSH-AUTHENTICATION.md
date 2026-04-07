# 🔧 Fix SSH Authentication Error

## Problem
```
ssh: handshake failed: ssh: unable to authenticate, attempted methods [none publickey], no supported methods remain
```

This means GitHub Actions can't authenticate to your EC2 server.

---

## Solution 1: Fix SSH Key Format (Most Common)

### Step 1: Get Your SSH Key

**On Windows:**
```powershell
# Find your .pem file
Get-Content your-key.pem
```

**On Linux/Mac:**
```bash
cat your-key.pem
```

### Step 2: Verify Key Format

Your key should look like this:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
(many lines of base64 encoded data)
...
-----END RSA PRIVATE KEY-----
```

**Important:** 
- Must start with `-----BEGIN RSA PRIVATE KEY-----`
- Must end with `-----END RSA PRIVATE KEY-----`
- No extra spaces or newlines at start/end
- All lines included

### Step 3: Update GitHub Secret

1. Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions
2. Find `EC2_SSH_KEY`
3. Click **Update**
4. Copy the ENTIRE key (including BEGIN and END lines)
5. Paste into the value field
6. Click **Update secret**

---

## Solution 2: Test SSH Key Locally First

Before updating GitHub, test if the key works:

```bash
# Test SSH connection
ssh -i your-key.pem ubuntu@16.170.25.9 "echo 'SSH works!'"
```

If this fails, the key itself has issues.

### Fix Key Permissions (Linux/Mac)
```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@16.170.25.9
```

### Fix Key Permissions (Windows)
```powershell
# Right-click your-key.pem → Properties → Security
# Remove all users except yourself
# Give yourself Full Control
```

---

## Solution 3: Generate New SSH Key Pair

If the key is corrupted or lost:

### On Your Local Machine:

```bash
# Generate new key pair
ssh-keygen -t rsa -b 4096 -f mushqila-deploy-key -N ""

# This creates:
# mushqila-deploy-key (private key)
# mushqila-deploy-key.pub (public key)
```

### Add Public Key to EC2:

**Method A: Using existing SSH access**
```bash
# If you can still SSH with old key
ssh -i old-key.pem ubuntu@16.170.25.9

# Add new public key
cat >> ~/.ssh/authorized_keys << 'EOF'
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQ... (paste your new public key here)
EOF

# Set permissions
chmod 600 ~/.ssh/authorized_keys
```

**Method B: Using AWS Console**
1. Go to AWS EC2 Console
2. Select your instance
3. Actions → Security → Get System Log
4. Or use EC2 Instance Connect

### Update GitHub Secret:

```bash
# Copy private key
cat mushqila-deploy-key

# Go to GitHub → Settings → Secrets → Actions
# Update EC2_SSH_KEY with the private key content
```

---

## Solution 4: Use Alternative Deployment Method

If SSH continues to fail, use AWS Systems Manager (no SSH needed):

### Update Workflow to Use SSM

<function_calls>
<invoke name="strReplace">
<parameter name="path">.github/workflows/deploy.yml