#!/bin/bash

# Quick deployment script for Mushqila
# This will commit changes and trigger GitHub Actions deployment

set -e

echo "=========================================="
echo "🚀 Mushqila Deployment Script"
echo "=========================================="
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Check for uncommitted changes
if [ -z "$(git status --porcelain)" ]; then
    echo "ℹ️  No changes to commit"
    echo "Do you want to trigger deployment anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        echo "Deployment cancelled"
        exit 0
    fi
else
    echo "📝 Changes detected:"
    git status --short
    echo ""
fi

# Get commit message
echo "Enter commit message (or press Enter for default):"
read -r commit_msg

if [ -z "$commit_msg" ]; then
    commit_msg="Deploy: $(date '+%Y-%m-%d %H:%M:%S')"
fi

echo ""
echo "📦 Preparing deployment..."
echo "   Commit message: $commit_msg"
echo ""

# Add all changes
echo "→ Adding changes..."
git add .

# Commit
echo "→ Committing..."
git commit -m "$commit_msg" || {
    echo "ℹ️  Nothing to commit, triggering deployment anyway..."
}

# Push to main
echo "→ Pushing to GitHub..."
git push origin main

echo ""
echo "=========================================="
echo "✅ Code pushed to GitHub!"
echo "=========================================="
echo ""
echo "🔄 GitHub Actions will now:"
echo "   1. Create backup"
echo "   2. Pull latest code"
echo "   3. Validate syntax"
echo "   4. Build Docker images"
echo "   5. Deploy with zero downtime"
echo "   6. Run migrations"
echo "   7. Collect static files"
echo "   8. Health check"
echo ""
echo "📊 Monitor deployment at:"
echo "   https://github.com/mushqiladac/mushqila/actions"
echo ""
echo "🌐 Site will be live at:"
echo "   https://mushqila.com"
echo ""
echo "⏱️  Estimated time: 3-4 minutes"
echo "=========================================="
