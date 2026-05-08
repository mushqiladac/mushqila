#!/bin/bash

# Script to check Django admin error on production

echo "=========================================="
echo "Checking Django Admin Error (500)"
echo "=========================================="
echo ""

# Check if we're on production server
if [ -d "/home/ubuntu/mushqila" ]; then
    echo "📍 Running on Production Server"
    PROJECT_DIR="/home/ubuntu/mushqila"
    DOCKER_CMD="docker-compose -f docker-compose.prod.yml"
else
    echo "📍 Running Locally"
    PROJECT_DIR="."
    DOCKER_CMD="docker-compose"
fi

cd $PROJECT_DIR

echo ""
echo "Step 1: Checking Container Status"
echo "-----------------------------------"
$DOCKER_CMD ps

echo ""
echo "Step 2: Checking Web Container Logs (Last 50 lines)"
echo "-----------------------------------"
$DOCKER_CMD logs web --tail=50

echo ""
echo "Step 3: Checking Database Connection"
echo "-----------------------------------"
$DOCKER_CMD exec -T web python manage.py dbshell << EOF
SELECT 1;
\q
EOF

echo ""
echo "Step 4: Checking Static Files"
echo "-----------------------------------"
$DOCKER_CMD exec -T web ls -la /app/staticfiles/admin/ | head -20

echo ""
echo "Step 5: Running Django Check"
echo "-----------------------------------"
$DOCKER_CMD exec -T web python manage.py check

echo ""
echo "Step 6: Testing Admin URL"
echo "-----------------------------------"
curl -I https://mushqila.com/admin/

echo ""
echo "Step 7: Checking for Missing Migrations"
echo "-----------------------------------"
$DOCKER_CMD exec -T web python manage.py showmigrations | grep "\[ \]"

echo ""
echo "=========================================="
echo "Common Fixes:"
echo "=========================================="
echo ""
echo "1. Collect Static Files:"
echo "   $DOCKER_CMD exec web python manage.py collectstatic --noinput"
echo ""
echo "2. Run Migrations:"
echo "   $DOCKER_CMD exec web python manage.py migrate"
echo ""
echo "3. Check Settings:"
echo "   - DEBUG = False (production)"
echo "   - ALLOWED_HOSTS includes domain"
echo "   - Database credentials correct"
echo ""
echo "4. Restart Containers:"
echo "   $DOCKER_CMD restart"
echo ""
echo "5. View Full Logs:"
echo "   $DOCKER_CMD logs web -f"
echo ""
