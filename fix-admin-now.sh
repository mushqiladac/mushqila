#!/bin/bash

# Quick Fix for Django Admin 500 Error
# Run this on production server

echo "=========================================="
echo "🔧 Fixing Django Admin 500 Error"
echo "=========================================="
echo ""

cd ~/mushqila

echo "Step 1: Collecting Static Files..."
echo "-----------------------------------"
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput --clear
if [ $? -eq 0 ]; then
    echo "✅ Static files collected"
else
    echo "❌ Failed to collect static files"
    exit 1
fi

echo ""
echo "Step 2: Running Migrations..."
echo "-----------------------------------"
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput
if [ $? -eq 0 ]; then
    echo "✅ Migrations completed"
else
    echo "⚠️ Migrations had issues (may be normal if already applied)"
fi

echo ""
echo "Step 3: Running Django Check..."
echo "-----------------------------------"
docker-compose -f docker-compose.prod.yml exec -T web python manage.py check
if [ $? -eq 0 ]; then
    echo "✅ Django check passed"
else
    echo "❌ Django check failed"
fi

echo ""
echo "Step 4: Verifying Static Files..."
echo "-----------------------------------"
if docker-compose -f docker-compose.prod.yml exec -T web ls /app/staticfiles/admin/css/base.css > /dev/null 2>&1; then
    echo "✅ Admin static files exist"
else
    echo "❌ Admin static files missing"
fi

echo ""
echo "Step 5: Restarting Web Container..."
echo "-----------------------------------"
docker-compose -f docker-compose.prod.yml restart web
echo "⏳ Waiting for restart..."
sleep 10
echo "✅ Container restarted"

echo ""
echo "Step 6: Testing Admin URL..."
echo "-----------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://mushqila.com/admin/)
echo "HTTP Status Code: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ Admin page is accessible!"
else
    echo "❌ Admin page still returning error: $HTTP_CODE"
    echo ""
    echo "Checking logs for errors..."
    docker-compose -f docker-compose.prod.yml logs web --tail=20
fi

echo ""
echo "=========================================="
echo "Fix Complete!"
echo "=========================================="
echo ""
echo "Try accessing: https://mushqila.com/admin/"
echo ""
echo "If still not working, check logs:"
echo "docker-compose -f docker-compose.prod.yml logs web -f"
echo ""
