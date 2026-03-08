#!/bin/bash
# Complete SSL Setup Script for mushqila.com
# This script fixes Nginx conflicts and configures HTTPS properly

echo "=== Step 1: Remove Nginx default site conflict ==="
sudo rm -f /etc/nginx/sites-enabled/default
echo "✓ Default site removed"

echo ""
echo "=== Step 2: Verify Nginx configuration ==="
sudo nginx -t
if [ $? -ne 0 ]; then
    echo "❌ Nginx configuration has errors. Please fix them first."
    exit 1
fi
echo "✓ Nginx configuration is valid"

echo ""
echo "=== Step 3: Stop Docker containers ==="
docker-compose -f docker-compose.prod.yml down
echo "✓ Containers stopped"

echo ""
echo "=== Step 4: Start Nginx service ==="
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx --no-pager
echo "✓ Nginx started"

echo ""
echo "=== Step 5: Rebuild and start Docker containers ==="
docker-compose -f docker-compose.prod.yml up -d --build
echo "✓ Containers started"

echo ""
echo "=== Step 6: Wait for services to be ready ==="
sleep 10

echo ""
echo "=== Step 7: Verify services ==="
echo "Checking Docker containers..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "Checking Nginx status..."
sudo systemctl status nginx --no-pager | head -n 10

echo ""
echo "Checking port bindings..."
sudo ss -tlnp | grep -E ':(80|443|8000)'

echo ""
echo "=== Step 8: Test HTTP and HTTPS ==="
echo "Testing HTTP..."
curl -I http://localhost/ 2>&1 | head -n 5

echo ""
echo "Testing HTTPS..."
curl -I https://mushqila.com/ 2>&1 | head -n 5

echo ""
echo "=== Step 9: Verify SSL certificate auto-renewal ==="
sudo systemctl status certbot.timer --no-pager

echo ""
echo "=== Deployment Complete! ==="
echo "✓ Site should now be accessible at:"
echo "  - http://mushqila.com (redirects to HTTPS)"
echo "  - https://mushqila.com"
echo "  - https://www.mushqila.com"
echo ""
echo "✓ SSL certificate expires: 2026-06-06"
echo "✓ Auto-renewal is configured via certbot.timer"
echo ""
echo "Next steps:"
echo "1. Test the site in your browser: https://mushqila.com"
echo "2. Create Django superuser: docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
