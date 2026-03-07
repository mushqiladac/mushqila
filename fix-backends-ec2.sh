#!/bin/bash

# Copy the fixed backends.py from local to EC2 container

cd ~/mushqila

# Create a temporary fixed version
cat > /tmp/backends_fix.py << 'PYTHON_FIX'
        # Check login attempts before proceeding
        is_blocked, remaining = check_login_attempts(username)
        if is_blocked:
            logger.warning(f"Login blocked for {username} from {ip_address}: Too many attempts")
PYTHON_FIX

# Show what we're looking for
echo "=== Current buggy code in container ==="
docker-compose -f docker-compose.traefik.yml exec web grep -A 3 "Check login attempts before proceeding" accounts/backends.py | head -5

# Apply the fix using docker exec and sed
echo ""
echo "=== Applying fix ==="
docker-compose -f docker-compose.traefik.yml exec web sed -i '57s/.*/        is_blocked, remaining = check_login_attempts(username)/' accounts/backends.py
docker-compose -f docker-compose.traefik.yml exec web sed -i '58s/.*/        if is_blocked:/' accounts/backends.py
docker-compose -f docker-compose.traefik.yml exec web sed -i '59s/.*/            logger.warning(f"Login blocked for {username} from {ip_address}: Too many attempts")/' accounts/backends.py

# Also fix the phone backend around line 280
docker-compose -f docker-compose.traefik.yml exec web sed -i '/Check login attempts$/,+2 s/allowed, message = check_login_attempts(ip_address, phone)/is_blocked, remaining = check_login_attempts(phone)/' accounts/backends.py
docker-compose -f docker-compose.traefik.yml exec web sed -i '/Check login attempts$/,+2 s/if not allowed:/if is_blocked:/' accounts/backends.py

# Verify
echo ""
echo "=== Verifying fix in container ==="
docker-compose -f docker-compose.traefik.yml exec web grep -A 3 "Check login attempts before proceeding" accounts/backends.py | head -5

# Restart gunicorn to reload code
echo ""
echo "=== Restarting web container ==="
docker-compose -f docker-compose.traefik.yml restart web

sleep 5
echo "=== Done! Test admin login now ==="
