#!/bin/bash

# Fix Django Admin 500 Error - Static Files Collection
# Run this on production server: ubuntu@ip-172-31-36-20

echo "=========================================="
echo "Django Admin 500 Error Fix"
echo "=========================================="
echo ""

# Navigate to project directory
cd ~/mushqila

echo "1. Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput --clear

echo ""
echo "2. Setting proper permissions..."
docker-compose exec -T web chown -R www-data:www-data /app/staticfiles

echo ""
echo "3. Restarting web container..."
docker-compose restart web

echo ""
echo "4. Checking container status..."
docker-compose ps

echo ""
echo "5. Testing admin URL..."
sleep 5
curl -I https://mushqila.com/admin/

echo ""
echo "=========================================="
echo "Fix completed!"
echo "=========================================="
echo ""
echo "Test admin panel: https://mushqila.com/admin/"
echo ""
echo "If still not working, check logs:"
echo "  docker-compose logs -f web"
echo ""
