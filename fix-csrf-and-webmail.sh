#!/bin/bash

echo "=== Fixing CSRF and Webmail Issues ==="

# Step 1: Update docker-compose.traefik.yml to add proper headers middleware
echo "Step 1: Updating Traefik configuration..."

cat > docker-compose.traefik.yml << 'DOCKER_COMPOSE_EOF'
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik-data/traefik.yml:/traefik.yml:ro
      - ./traefik-data/acme.json:/acme.json
      - ./traefik-data/config.yml:/config.yml:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.entrypoints=http"
      - "traefik.http.routers.traefik.rule=Host(`traefik.mushqila.com`)"
      - "traefik.http.middlewares.traefik-auth.basicauth.users=admin:$apr1$8evjzm8h$FU3mLYqYt5Y8FKZcqkqNX1"
      - "traefik.http.middlewares.traefik-https-redirect.redirectscheme.scheme=https"
      - "traefik.http.middlewares.sslheader.headers.customrequestheaders.X-Forwarded-Proto=https"
      - "traefik.http.routers.traefik.middlewares=traefik-https-redirect"
      - "traefik.http.routers.traefik-secure.entrypoints=https"
      - "traefik.http.routers.traefik-secure.rule=Host(`traefik.mushqila.com`)"
      - "traefik.http.routers.traefik-secure.middlewares=traefik-auth"
      - "traefik.http.routers.traefik-secure.tls=true"
      - "traefik.http.routers.traefik-secure.tls.certresolver=letsencrypt"
      - "traefik.http.routers.traefik-secure.service=api@internal"
    networks:
      - proxy

  web:
    build: .
    container_name: mushqila_web
    restart: unless-stopped
    env_file:
      - .env.production
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - redis
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mushqila.entrypoints=http"
      - "traefik.http.routers.mushqila.rule=Host(`mushqila.com`) || Host(`www.mushqila.com`)"
      - "traefik.http.middlewares.mushqila-https-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.mushqila.middlewares=mushqila-https-redirect"
      - "traefik.http.routers.mushqila-secure.entrypoints=https"
      - "traefik.http.routers.mushqila-secure.rule=Host(`mushqila.com`) || Host(`www.mushqila.com`)"
      - "traefik.http.routers.mushqila-secure.tls=true"
      - "traefik.http.routers.mushqila-secure.tls.certresolver=letsencrypt"
      - "traefik.http.routers.mushqila-secure.service=mushqila"
      # CRITICAL FIX: Apply SSL header middleware to secure router
      - "traefik.http.routers.mushqila-secure.middlewares=sslheader"
      - "traefik.http.services.mushqila.loadbalancer.server.port=8000"
      - "traefik.docker.network=proxy"
    networks:
      - proxy
      - internal

  redis:
    image: redis:7-alpine
    container_name: mushqila_redis
    restart: unless-stopped
    networks:
      - internal

  celery:
    build: .
    container_name: mushqila_celery
    command: celery -A config worker -l info
    restart: unless-stopped
    env_file:
      - .env.production
    depends_on:
      - redis
      - web
    networks:
      - internal

  celery-beat:
    build: .
    container_name: mushqila_celery_beat
    command: celery -A config beat -l info
    restart: unless-stopped
    env_file:
      - .env.production
    depends_on:
      - redis
      - web
    networks:
      - internal

volumes:
  static_volume:
  media_volume:

networks:
  proxy:
    external: true
  internal:
    external: false
DOCKER_COMPOSE_EOF

echo "✓ docker-compose.traefik.yml updated with SSL header middleware"

# Step 2: Update settings.py to add CSRF_COOKIE_DOMAIN and SESSION_COOKIE_DOMAIN
echo ""
echo "Step 2: Updating Django settings for CSRF..."

# Create a Python script to update settings
cat > update_settings.py << 'PYTHON_EOF'
import re

# Read settings.py
with open('config/settings.py', 'r') as f:
    content = f.read()

# Check if CSRF settings already exist
if 'CSRF_COOKIE_DOMAIN' not in content:
    # Find the AWS Configuration section or end of file
    insert_position = content.find('# ===========================\n# AWS Configuration for Webmail')
    
    if insert_position == -1:
        # If AWS section not found, add at the end
        insert_position = len(content)
    
    csrf_settings = '''
# ===========================
# CSRF and Session Configuration for Proxy
# ===========================
# Get CSRF trusted origins from environment
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='').split(',')

# Cookie settings for proxy setup
CSRF_COOKIE_DOMAIN = config('CSRF_COOKIE_DOMAIN', default=None)
SESSION_COOKIE_DOMAIN = config('SESSION_COOKIE_DOMAIN', default=None)

# Security settings for HTTPS
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

# Proxy SSL header
SECURE_PROXY_SSL_HEADER_NAME = config('SECURE_PROXY_SSL_HEADER', default='HTTP_X_FORWARDED_PROTO,https')
if SECURE_PROXY_SSL_HEADER_NAME:
    parts = SECURE_PROXY_SSL_HEADER_NAME.split(',')
    if len(parts) == 2:
        SECURE_PROXY_SSL_HEADER = (parts[0], parts[1])

'''
    
    content = content[:insert_position] + csrf_settings + '\n' + content[insert_position:]
    
    # Write back
    with open('config/settings.py', 'w') as f:
        f.write(content)
    
    print("✓ Added CSRF and session configuration to settings.py")
else:
    print("✓ CSRF settings already exist in settings.py")
PYTHON_EOF

python3 update_settings.py
rm update_settings.py

echo ""
echo "=== Deployment Instructions ==="
echo ""
echo "Run these commands on EC2:"
echo ""
echo "# 1. Pull latest changes"
echo "cd ~/mushqila"
echo "git pull"
echo ""
echo "# 2. Stop containers"
echo "docker-compose -f docker-compose.traefik.yml down"
echo ""
echo "# 3. Start containers with new configuration"
echo "docker-compose -f docker-compose.traefik.yml up -d"
echo ""
echo "# 4. Check logs"
echo "docker logs mushqila_web --tail=50"
echo ""
echo "# 5. Test admin login at https://mushqila.com/admin/login/"
echo "# 6. Test webmail at https://mushqila.com/webmail/"
echo ""
echo "=== Fix Complete ==="
