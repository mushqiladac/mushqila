# 🔧 Quick Fix - webmail/models.py Syntax Error

## সমস্যা
`webmail/models.py` line 211 এ একটা incomplete line ছিল: `c`

এটা `NameError: name 'c' is not defined` error দিচ্ছিল।

## সমাধান
Line 211 থেকে `c` remove করা হয়েছে।

## এখন কি করবেন?

### Windows থেকে:

```powershell
cd C:\Users\user\Desktop\Mushqila

# Add and commit
git add webmail/models.py
git commit -m "Fix: Remove incomplete line from webmail/models.py"
git push origin main
```

### Server এ:

```bash
cd /home/ubuntu/mushqila

# Pull latest code
git pull origin main

# Restart containers
docker-compose -f docker-compose.prod.yml restart web

# Check logs
docker-compose -f docker-compose.prod.yml logs web --tail=50

# Check status
docker-compose -f docker-compose.prod.yml ps
```

---

**Fixed**: 2026-04-07
