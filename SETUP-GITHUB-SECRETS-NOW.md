# Setup GitHub Secrets - Step by Step

## Go to GitHub Repository Settings

1. Visit: https://github.com/mushqiladac/mushqila
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret** for each secret below

---

## Add These Secrets (Copy-Paste Values)

### 1. EC2_HOST
```
16.170.25.9
```

### 2. EC2_USERNAME
```
ubuntu
```

### 3. EC2_SSH_KEY
**You need to paste your SSH private key content here**
- Open your `.pem` file in notepad
- Copy ENTIRE content (including BEGIN/END lines)
- Paste in GitHub secret

Example format:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
(your key content)
...
-----END RSA PRIVATE KEY-----
```

### 4. DB_HOST
```
database-1.cb4mqoeyyym6.eu-north-1.rds.amazonaws.com
```

### 5. DB_NAME
```
postgres
```

### 6. DB_USER
```
postgres
```

### 7. DB_PASSWORD
```
Sinan210
```

### 8. DB_PORT
```
5432
```

### 9. SECRET_KEY
**Generate a new one using this command on your local machine:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Then paste the generated key as secret value.

### 10. ALLOWED_HOSTS
```
16.170.25.9,ec2-16-170-25-9.eu-north-1.compute.amazonaws.com
```

### 11. DEBUG
```
False
```

### 12. AWS_ACCESS_KEY_ID (for SES)
```
[Your SES Access Key - Get from AWS SES Console]
```

### 13. AWS_SECRET_ACCESS_KEY (for SES)
```
[Your SES Secret Key - Get from AWS SES Console]
```

### 14. AWS_REGION
```
eu-north-1
```

### 15. EMAIL_HOST
```
email-smtp.eu-north-1.amazonaws.com
```

### 16. EMAIL_PORT
```
587
```

### 17. DEFAULT_FROM_EMAIL
**Use your verified SES email address**
```
noreply@yourdomain.com
```
(Replace with your actual verified email)

---

## After Adding All Secrets

Your secrets list should show:
- EC2_HOST
- EC2_USERNAME
- EC2_SSH_KEY
- DB_HOST
- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_PORT
- SECRET_KEY
- ALLOWED_HOSTS
- DEBUG
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION
- EMAIL_HOST
- EMAIL_PORT
- DEFAULT_FROM_EMAIL

---

## Next: Setup EC2 Instance

After adding secrets, you need to setup EC2 instance. See: `EC2-INITIAL-SETUP.md`
