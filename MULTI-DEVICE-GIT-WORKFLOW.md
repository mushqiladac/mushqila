# Multi-Device Git Workflow - দুই ডিভাইসে Conflict-Free কাজ করার নিয়ম

**ল্যাপটপ + পিসি - একসাথে কাজ করার সম্পূর্ণ গাইড**

---

## 🎯 মূল নিয়ম (Golden Rules)

1. ✅ **কাজ শুরুর আগে সবসময় `git pull`**
2. ✅ **কাজ শেষে সবসময় `git commit + push`**
3. ✅ **একই ফাইলে একসাথে কাজ করবেন না**
4. ✅ **Branch ব্যবহার করুন বড় feature এর জন্য**

---

## 📋 Initial Setup (প্রথমবার - পিসিতে)

### Step 1: Git Configuration

```bash
# আপনার নাম ও email set করুন
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Credential helper (password save)
git config --global credential.helper wincred
```

### Step 2: Clone Repository

```bash
# Desktop এ যান
cd C:\Users\user\Desktop

# Clone করুন (GitHub credentials চাইবে)
git clone https://github.com/eliussrose/Pir.git

# Project folder এ ঢুকুন
cd Pir

# Check status
git status
```

---

## 🔄 Daily Workflow

### 🌅 কাজ শুরু (MUST DO!)

```bash
# 1. Project folder এ যান
cd C:\Users\user\Desktop\Pir

# 2. Latest changes pull করুন
git pull origin main

# 3. Status check
git status
```

### 💻 কাজ করুন

```bash
# Files edit করুন...
# Code লিখুন...

# Status check
git status
```

### 🌙 কাজ শেষ (MUST DO!)

```bash
# 1. Add all changes
git add .

# 2. Commit with message
git commit -m "Feature: Added login page"

# 3. Push to GitHub
git push origin main

# 4. Verify
git status
```

---

## 📱 Device Switching Example

### Scenario: ল্যাপটপ → পিসি → ল্যাপটপ

**Morning (ল্যাপটপে)**:
```bash
cd /path/to/Pir
git pull origin main
# কাজ করুন...
git add .
git commit -m "Updated dashboard"
git push origin main
```

**Afternoon (পিসিতে)**:
```bash
cd C:\Users\user\Desktop\Pir
git pull origin main  # ল্যাপটপের changes পাবেন ✅
# কাজ করুন...
git add .
git commit -m "Added reports"
git push origin main
```

**Evening (ল্যাপটপে)**:
```bash
cd /path/to/Pir
git pull origin main  # পিসির changes পাবেন ✅
# কাজ করুন...
```

---

## ⚠️ Conflict হলে

### Pull করার সময় conflict:

```bash
git pull origin main
# CONFLICT দেখাবে

# 1. Conflicted files দেখুন
git status

# 2. File open করে fix করুন
# <<<<<<< HEAD
# Your changes
# =======
# Other changes
# >>>>>>> 

# 3. Conflict markers remove করুন

# 4. Add & commit
git add .
git commit -m "Resolve merge conflict"
git push origin main
```

---

## 🛡️ Best Practices

### ✅ DO

1. **সবসময় pull করে শুরু করুন**
2. **ছোট ছোট commits করুন**
3. **Meaningful messages লিখুন**
4. **Regular push করুন**

### ❌ DON'T

1. **Pull না করে কাজ শুরু করবেন না**
2. **একই ফাইলে দুই ডিভাইসে একসাথে কাজ করবেন না**
3. **Force push করবেন না** (`git push -f`)

---

## 🔧 Useful Commands

```bash
# Status check
git status
git log --oneline -5

# Discard changes
git checkout -- filename.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Temporary save
git stash
git stash pop
```

---

## 📝 Quick Reference

### Morning:
```bash
cd C:\Users\user\Desktop\Pir
git pull origin main
```

### Evening:
```bash
git add .
git commit -m "Your message"
git push origin main
```

---

## ✅ Daily Checklist

### কাজ শুরুর আগে:
- [ ] `git pull origin main`
- [ ] `git status`

### কাজ শেষে:
- [ ] `git add .`
- [ ] `git commit -m "message"`
- [ ] `git push origin main`

---

## 🎯 Summary

**3টি মূল নিয়ম**:

1. **Pull First** - কাজ শুরুর আগে
2. **Commit Often** - ছোট ছোট commits
3. **Push Always** - কাজ শেষে

এই নিয়ম follow করলে কখনো conflict হবে না! 🚀
