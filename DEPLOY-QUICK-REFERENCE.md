# 🚀 Deployment Quick Reference

## One-Command Deploy

### Windows
```powershell
.\deploy.ps1
```

### Linux/Mac
```bash
./deploy.sh
```

### Manual
```bash
git add . && git commit -m "Deploy" && git push origin main
```

---

## Essential Commands

### Check Before Deploy
```bash
./pre-deploy-check.sh  # Run pre-deployment checks
```

### Monitor Deployment
```
https://github.com/mushqiladac/mushqila/actions
```

### SSH to Server
```bash
ssh -i your-key.pem ubuntu@16.170.25.9
```

### Check Container Status
```bash
cd ~/mushqila
docker-compose -f docker-compose.prod.yml ps
```

### View Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f web
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart web
```

### Quick Rollback
```bash
cd ~
ls -lht mushqila_backup_*  # List backups
sudo rm -rf mushqila
sudo mv mushqila_backup_YYYYMMDD_HHMMSS mushqila
cd mushqila
docker-compose -f docker-compose.prod.yml up -d
```

---

## URLs to Check

- **Main Site**: https://mushqila.com
- **Admin**: https://mushqila.com/admin/
- **Webmail**: https://mushqila.com/webmail/
- **Login**: https://mushqila.com/accounts/login/
- **GitHub Actions**: https://github.com/mushqiladac/mushqila/actions

---

## Deployment Time

⏱️ **2-4 minutes** (automatic, zero downtime)

---

## GitHub Secrets Required

Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions

- `EC2_HOST`: 16.170.25.9
- `EC2_USER`: ubuntu
- `EC2_SSH_KEY`: Your SSH private key

---

## Troubleshooting Quick Fixes

### Site Down (502)
```bash
docker-compose -f docker-compose.prod.yml restart web
sudo systemctl restart nginx
```

### 500 Error
```bash
docker-compose -f docker-compose.prod.yml logs web | tail -50
docker-compose -f docker-compose.prod.yml restart web
```

### Static Files Missing
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput --clear
```

### Database Issues
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml restart web
```

---

## Emergency Contacts

- **Server IP**: 16.170.25.9
- **Domain**: mushqila.com
- **GitHub**: https://github.com/mushqiladac/mushqila

---

## Deployment Checklist

- [ ] Run pre-deploy check: `./pre-deploy-check.sh`
- [ ] Commit changes: `git commit -m "..."`
- [ ] Push to GitHub: `git push origin main`
- [ ] Monitor: GitHub Actions
- [ ] Verify: https://mushqila.com
- [ ] Check logs if issues

---

**That's it! Deploy with confidence!** 🎉
