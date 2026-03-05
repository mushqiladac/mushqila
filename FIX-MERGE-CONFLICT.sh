#!/bin/bash

# Fix merge conflict and deploy Traefik
# Run this on EC2: bash FIX-MERGE-CONFLICT.sh

echo "🔧 Fixing merge conflict and deploying Traefik..."
echo ""

# Step 1: Stash local changes
echo "📦 Stashing local changes..."
git stash

# Step 2: Pull latest code
echo "⬇️  Pulling latest code..."
git pull origin main

# Step 3: Check if boto3 is in requirements.txt
echo "🔍 Checking requirements.txt..."
if grep -q "boto3" requirements.txt; then
    echo "✅ boto3 already in requirements.txt"
else
    echo "➕ Adding boto3 to requirements.txt..."
    echo "boto3==1.34.34" >> requirements.txt
    echo "botocore==1.34.34" >> requirements.txt
fi

# Step 4: Show what we have
echo ""
echo "📋 Current requirements.txt (last 5 lines):"
tail -5 requirements.txt
echo ""

# Step 5: Make deploy script executable
echo "🔑 Making deploy script executable..."
chmod +x deploy-traefik.sh

# Step 6: Show next steps
echo ""
echo "✅ Merge conflict fixed!"
echo ""
echo "📝 Next steps:"
echo "1. Get Cloudflare API token from: https://dash.cloudflare.com"
echo "2. Update .env.production with Cloudflare token"
echo "3. Run: ./deploy-traefik.sh"
echo ""
