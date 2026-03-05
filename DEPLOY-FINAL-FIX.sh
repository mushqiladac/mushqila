#!/bin/bash

# 🚀 Final Deployment Fix Script
# Run this on EC2 to deploy the latest code with webmail URL fix

echo "================================================"
echo "🚀 Mushqila Final Deployment Fix"
echo "================================================"
echo ""

# Navigate to project directory
cd ~/mushqila || exit 1

echo "📥 Step 1: Pulling latest code from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed. Check your connection."
    exit 1
fi

echo "✅ Code updated successfully"
echo ""

echo "🛑 Step 2: Stopping containers..."
docker-compose -f docker-compose.prod.yml down

echo "✅ Containers stopped"
echo ""

echo "🧹 Step 3: Cleaning Docker cache..."
docker system prune -f

echo "✅ Docker cleaned"
echo ""

echo "🔨 Step 4: Building and starting containers..."
docker-compose -f docker-compose.prod.yml up -d --build

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed. Check logs."
    exit 1
fi

echo "✅ Containers started"
echo ""

echo "⏳ Step 5: Waiting 60 seconds for services to start..."
sleep 60

echo "✅ Services should be ready"
echo ""

echo "📊 Step 6: Checking container status..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📝 Step 7: Checking recent logs..."
docker-compose -f docker-compose.prod.yml logs --tail=20 web

echo ""
echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "🌐 Test these URLs in your browser:"
echo "   - http://mushqila.com"
echo "   - http://www.mushqila.com"
echo "   - http://16.170.25.9"
echo "   - http://mushqila.com/accounts/landing/"
echo "   - http://mushqila.com/landing2/"
echo "   - http://mushqila.com/admin/"
echo "   - http://mushqila.com/webmail/"
echo ""
echo "✅ What to verify:"
echo "   - Landing page loads"
echo "   - Payment logos in footer"
echo "   - Search widget works"
echo "   - Navbar buttons styled"
echo "   - Webmail accessible"
echo ""
echo "📊 Monitor logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f web"
echo ""
echo "🔄 If issues, restart:"
echo "   docker-compose -f docker-compose.prod.yml restart web"
echo ""
echo "================================================"
