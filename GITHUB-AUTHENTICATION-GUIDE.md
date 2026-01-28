# GitHub Authentication Setup Guide

## সমস্যা
```
remote: Permission to mushqiladac/mushqila.git denied to eliussrose.
fatal: unable to access 'https://github.com/mushqiladac/mushqila.git/': The requested URL returned error: 403
```

এই error হচ্ছে কারণ:
1. আপনার local Git configuration এ ভুল username আছে (eliussrose)
2. সঠিক GitHub credentials configure করা নেই

---

## সমাধান - Option 1: Personal Access Token (Recommended)

### Step 1: Personal Access Token তৈরি করুন

1. যান: https://github.com/settings/tokens
2. "Generate new token" → "Generate new token (classic)" ক্লিক করুন
3. Note: `Mushqila Deployment`
4. Expiration: `No expiration` (অথবা আপনার পছন্দ অনুযায়ী)
5. Select scopes:
   - ✅ `repo` (সব checkboxes)
   - ✅ `workflow`
6. "Generate token" ক্লিক করুন
7. **Token টি copy করে নিরাপদ জায়গায় রাখুন** (এটি আর দেখাবে না!)

### Step 2: Git Configuration Update করুন

```bash
# Global username set করুন
git config --global user.name "mushqiladac"

# Global email set করুন
git config --global user.email "your-email@example.com"

# Check configuration
git config --global --list
```

### Step 3: Remote URL Update করুন (Token সহ)

```bash
# Current remote remove করুন
git remote remove origin

# Token সহ নতুন remote add করুন
git remote add origin https://YOUR_TOKEN@github.com/mushqiladac/mushqila.git

# অথবা username:token format এ
git remote add origin https://mushqiladac:YOUR_TOKEN@github.com/mushqiladac/mushqila.git
```

**Replace `YOUR_TOKEN` with your actual Personal Access Token**

### Step 4: Push করুন

```bash
git push -u origin main
```

---

## সমাধান - Option 2: SSH Key (More Secure)

### Step 1: SSH Key Generate করুন

```bash
# SSH key generate করুন
ssh-keygen -t ed25519 -C "your-email@example.com"

# Enter file location (default: C:\Users\user\.ssh\id_ed25519)
# Enter passphrase (optional, but recommended)

# SSH key copy করুন
type C:\Users\user\.ssh\id_ed25519.pub
```

### Step 2: GitHub এ SSH Key Add করুন

1. যান: https://github.com/settings/keys
2. "New SSH key" ক্লিক করুন
3. Title: `Mushqila Deployment Key`
4. Key: আপনার public key paste করুন (id_ed25519.pub এর content)
5. "Add SSH key" ক্লিক করুন

### Step 3: Remote URL Change করুন

```bash
# Current remote remove করুন
git remote remove origin

# SSH URL add করুন
git remote add origin git@github.com:mushqiladac/mushqila.git

# Test SSH connection
ssh -T git@github.com
```

### Step 4: Push করুন

```bash
git push -u origin main
```

---

## সমাধান - Option 3: GitHub Desktop (Easiest)

### Step 1: GitHub Desktop Install করুন

Download: https://desktop.github.com/

### Step 2: GitHub Desktop এ Login করুন

1. GitHub Desktop open করুন
2. File → Options → Accounts
3. "Sign in" ক্লিক করুন
4. Browser এ GitHub login করুন

### Step 3: Repository Add করুন

1. File → Add local repository
2. Choose: `C:\Users\user\Desktop\Mushqila`
3. "Add repository" ক্লিক করুন

### Step 4: Publish করুন

1. "Publish repository" button ক্লিক করুন
2. Name: `mushqila`
3. Organization: `mushqiladac` select করুন
4. "Publish repository" ক্লিক করুন

---

## সমাধান - Option 4: Credential Manager (Windows)

### Step 1: Windows Credential Manager Clear করুন

```bash
# Git credential helper check করুন
git config --global credential.helper

# Credential manager clear করুন
git credential-manager erase https://github.com
```

### Step 2: Push করার সময় নতুন credentials দিন

```bash
git push -u origin main
```

Windows একটি popup দেখাবে যেখানে আপনি:
- Username: `mushqiladac`
- Password: `YOUR_PERSONAL_ACCESS_TOKEN` (not your GitHub password!)

---

## Quick Fix Commands

### যদি এখনই push করতে চান:

```bash
# 1. Git config update করুন
git config --global user.name "mushqiladac"
git config --global user.email "your-email@example.com"

# 2. Remote remove করুন
git remote remove origin

# 3. Token সহ remote add করুন (TOKEN replace করুন)
git remote add origin https://YOUR_TOKEN@github.com/mushqiladac/mushqila.git

# 4. Push করুন
git push -u origin main
```

---

## Verification Commands

```bash
# Check current user
git config user.name
git config user.email

# Check remote URL
git remote -v

# Check credential helper
git config --global credential.helper

# Test connection
git ls-remote origin
```

---

## Security Notes

### ⚠️ Important:
1. **Never commit your Personal Access Token** to the repository
2. Token টি `.env` file এ রাখবেন না
3. Token expire হলে নতুন token generate করুন
4. SSH key ব্যবহার করা বেশি secure

### Token Permissions:
- Minimum required: `repo` scope
- For CI/CD: `workflow` scope also needed

---

## Troubleshooting

### Error: "Support for password authentication was removed"
**Solution:** Personal Access Token ব্যবহার করুন, password নয়

### Error: "Permission denied (publickey)"
**Solution:** SSH key সঠিকভাবে configure করুন

### Error: "Could not read from remote repository"
**Solution:** Repository access check করুন, সঠিক URL verify করুন

---

## আমাকে বলুন:

1. **আপনার কাছে কি Personal Access Token আছে?**
   - হ্যাঁ → Token দিন, আমি command দিচ্ছি
   - না → উপরের Step 1 follow করে token তৈরি করুন

2. **অথবা GitHub Desktop ব্যবহার করতে চান?**
   - সহজ এবং user-friendly
   - No command line needed

3. **অথবা SSH key setup করতে চান?**
   - বেশি secure
   - One-time setup

আপনি কোন option পছন্দ করেন?
