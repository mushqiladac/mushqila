# 🔑 Fix GitHub Actions SSH Authentication Error

## Error
```
ssh: handshake failed: ssh: unable to authenticate, attempted methods [none publickey], no supported methods remain
```

This means the SSH key in GitHub Secrets is incorrect or not properly formatted.

---

## Solution: Update EC2_SSH_KEY Secret

### Step 1: Get Your SSH Private Key

#### On Windows (PowerShell):
```powershell
# Navigate to where your .pem file is
cd C:\path\to\your\key

# Display the key content
Get-Content your-key.pem

# Or copy to clipboard
Get-Content your-key.pem | Set-Clipboard
```

#### On Mac/Linux:
```bash
# Display the key
cat your-key.pem

# Or copy to clipboard
# Mac:
cat your-key.pem | pbcopy

# Linux:
cat your-key.pem | xclip -selection clipboard
```

### Step 2: Verify Key Format

Your key should look like this:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
(many lines of random characters)
...
-----END RSA PRIVATE KEY-----
```

**Important:**
- Must start with `-----BEGIN RSA PRIVATE KEY-----` or `-----BEGIN OPENSSH PRIVATE KEY-----`
- Must end with `-----END RSA PRIVATE KEY-----` or `-----END OPENSSH PRIVATE KEY-----`
- Include ALL lines including BEGIN and END
- No extra spaces or characters

### Step 3: Update GitHub Secret

1. Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions

2. Find **EC2_SSH_KEY** secret

3. Click the **pencil icon** (Update) or **trash icon** (Delete) then recreate

4. **Delete the old secret** (recommended):
   - Click trash icon next to EC2_SSH_KEY
   - Confirm deletion

5. **Create new secret**:
   - Click **New repository secret**
   - Name: `EC2_SSH_KEY`
   - Value: Paste your ENTIRE private key content
   - Click **Add secret**

### Step 4: Verify Other Secrets

While you're there, verify these secrets exist:

#### EC2_HOST
```
Name: EC2_HOST
Value: 16.170.25.9
```

#### EC2_USER
```
Name: EC2_USER
Value: ubuntu
```

---

## Alternative: Test SSH Key Locally First

Before adding to GitHub, test if your key works:

```bash
# Test SSH connection
ssh -i your-key.pem ubuntu@16.170.25.9 "echo 'SSH works!'"

# If this works, your key is correct
# If this fails, fix the key first
```

### Common SSH Key Issues:

#### Issue 1: Wrong Permissions (Linux/Mac)
```bash
chmod 400 your-key.pem
```

#### Issue 2: Wrong Key Format
```bash
# Convert if needed
ssh-keygen -p -f your-key.pem -m pem -P "" -N ""
```

#### Issue 3: Key Not Authorized on EC2
```bash
# SSH to EC2 (if you have access another way)
# Check authorized keys
cat ~/.ssh/authorized_keys

# Your key's public key should be there
```

---

## Step-by-Step: Copy SSH Key Correctly

### Method 1: Using Notepad (Windows)

1. Right-click your `.pem` file
2. Open with **Notepad**
3. Select ALL (Ctrl+A)
4. Copy (Ctrl+C)
5. Go to GitHub Secrets
6. Paste (Ctrl+V)
7. Make sure no extra lines at start/end
8. Save

### Method 2: Using PowerShell (Windows)

```powershell
# This will copy to clipboard
Get-Content your-key.pem | Set-Clipboard

# Then paste in GitHub
```

### Method 3: Using Terminal (Mac/Linux)

```bash
# Display and manually copy
cat your-key.pem

# Or copy to clipboard
cat your-key.pem | pbcopy  # Mac
cat your-key.pem | xclip -selection clipboard  # Linux
```

---

## After Updating Secret

### Test the Deployment Again

1. Go to: https://github.com/mushqiladac/mushqila/actions

2. Click on the failed workflow

3. Click **Re-run all jobs** button (top right)

4. Watch it run - should work now!

---

## If Still Failing

### Check EC2 SSH Configuration

SSH to EC2 manually and check:

```bash
# Check SSH daemon config
sudo cat /etc/ssh/sshd_config | grep -E "PubkeyAuthentication|PasswordAuthentication"

# Should see:
# PubkeyAuthentication yes
# PasswordAuthentication no

# Check authorized keys
cat ~/.ssh/authorized_keys

# Check permissions
ls -la ~/.ssh/
# Should be: drwx------ (700) for .ssh directory
# Should be: -rw------- (600) for authorized_keys file
```

### Fix Permissions if Needed

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

---

## Quick Checklist

Before re-running workflow:

- [ ] SSH key copied correctly (including BEGIN/END lines)
- [ ] No extra spaces or newlines
- [ ] EC2_HOST = 16.170.25.9
- [ ] EC2_USER = ubuntu
- [ ] EC2_SSH_KEY = complete private key
- [ ] Tested SSH locally: `ssh -i key.pem ubuntu@16.170.25.9`

---

## Alternative: Use Password Authentication (Not Recommended)

If you can't get SSH key working, you can use password (less secure):

1. Enable password auth on EC2:
```bash
sudo nano /etc/ssh/sshd_config
# Change: PasswordAuthentication yes
sudo systemctl restart sshd
```

2. Set password for ubuntu user:
```bash
sudo passwd ubuntu
```

3. Update GitHub workflow to use password instead of key

**But SSH key is much more secure - fix the key instead!**

---

## Summary

The issue is that GitHub Actions can't authenticate to EC2 because:
1. SSH key is not in correct format in GitHub Secret
2. Or key doesn't match what's authorized on EC2

**Fix:** Copy your ENTIRE .pem file content to EC2_SSH_KEY secret, then re-run the workflow.

---

**After fixing, go to GitHub Actions and click "Re-run all jobs"!** 🚀
