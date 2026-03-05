#!/bin/bash

# 🚀 Deploy Webmail Fix - Add boto3
# Run this on EC2

echo "================================================"
echo "🚀 Deploying Webmail Fix (boto3)"
echo "================================================"
echo ""

cd ~/mushqila || exit 1

echo "📥 Step 1: Pulling latest code..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed"
    exit 1
fi

echo "✅ Code updated"
echo ""

echo "🛑 Step 2: Stopping containers..."
docker-compose -f docker-compose.prod.yml down

echo "✅ Containers stopped"
echo ""

echo "🔨 Step 3: Rebuilding with boto3..."
docker-compose -f docker-compose.prod.yml up -d --build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Containers rebuilt"
echo ""

echo "⏳ Step 4: Waiting 60 seconds..."
sleep 60

echo "✅ Services ready"
echo ""

echo "📊 Step 5: Checking status..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📝 Step 6: Checking logs..."
docker-compose -f docker-compose.prod.yml logs --tail=20 web

echo ""
echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "🌐 Test webmail:"
echo "   http://mushqila.com/webmail/"
echo ""
echo "📊 Monitor logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f web"
echo ""
echo "================================================"
