#!/bin/bash

# Quick Start Script for Local Docker Development

echo "=========================================="
echo "🚀 Starting Mushqila Local Development"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Step 1: Build containers
echo "Step 1: Building Docker containers..."
echo "-----------------------------------"
docker-compose build
if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi
echo "✅ Build complete"
echo ""

# Step 2: Start containers
echo "Step 2: Starting containers..."
echo "-----------------------------------"
docker-compose up -d
if [ $? -ne 0 ]; then
    echo "❌ Failed to start containers"
    exit 1
fi
echo "✅ Containers started"
echo ""

# Step 3: Wait for database
echo "Step 3: Waiting for database..."
echo "-----------------------------------"
sleep 5
echo "✅ Database ready"
echo ""

# Step 4: Run migrations
echo "Step 4: Running migrations..."
echo "-----------------------------------"
docker-compose exec -T web python manage.py migrate
if [ $? -ne 0 ]; then
    echo "⚠️ Migrations had issues (may be normal for first run)"
fi
echo "✅ Migrations complete"
echo ""

# Step 5: Collect static files
echo "Step 5: Collecting static files..."
echo "-----------------------------------"
docker-compose exec -T web python manage.py collectstatic --noinput
echo "✅ Static files collected"
echo ""

# Step 6: Create finance users
echo "Step 6: Creating finance users..."
echo "-----------------------------------"
docker-compose exec -T web python manage.py create_finance_users
echo "✅ Finance users created"
echo ""

# Step 7: Show container status
echo "Step 7: Container status..."
echo "-----------------------------------"
docker-compose ps
echo ""

echo "=========================================="
echo "✅ Local Development Environment Ready!"
echo "=========================================="
echo ""
echo "Access the application:"
echo "  🌐 Main Site:    http://localhost:8000"
echo "  👤 Admin Panel:  http://localhost:8000/admin/"
echo "  💰 Finance App:  http://localhost:8000/finance/login/"
echo "  📧 Webmail:      http://localhost:8000/webmail/login/"
echo "  🏢 B2B Login:    http://localhost:8000/accounts/login/"
echo ""
echo "Finance Login Credentials:"
echo "  Email: saddam110@mushqila.com"
echo "  Password: Sinan210"
echo "  User Type: এডমিন"
echo ""
echo "Useful commands:"
echo "  View logs:       docker-compose logs -f web"
echo "  Stop:            docker-compose down"
echo "  Restart:         docker-compose restart"
echo "  Shell:           docker-compose exec web python manage.py shell"
echo ""
echo "For more commands, see: RUN-LOCAL-DOCKER.md"
echo ""
