#!/bin/bash
# Quick Setup Script for GitHub Actions

echo "=========================================="
echo "🚀 GitHub Actions Setup Helper"
echo "=========================================="
echo ""

echo "This script will help you set up GitHub Actions for zero-downtime deployment."
echo ""

# Check if .github/workflows directory exists
if [ ! -d ".github/workflows" ]; then
    echo "✓ Creating .github/workflows directory..."
    mkdir -p .github/workflows
fi

# Check if deploy.yml exists
if [ -f ".github/workflows/deploy.yml" ]; then
    echo "✓ deploy.yml already exists"
else
    echo "❌ deploy.yml not found!"
    echo "Please ensure the workflow file is created."
    exit 1
fi

echo ""
echo "=========================================="
echo "📋 Setup Checklist"
echo "=========================================="
echo ""

echo "Please complete these steps:"
echo ""
echo "1. GitHub Secrets Setup:"
echo "   → Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions"
echo "   → Add these secrets:"
echo "     - EC2_HOST: 16.170.25.9"
echo "     - EC2_USER: ubuntu"
echo "     - EC2_SSH_KEY: [Your SSH private key content]"
echo ""

echo "2. SSH Key Preparation:"
echo "   → Copy your SSH key:"
if command -v clip &> /dev/null; then
    echo "     Windows: Get-Content your-key.pem | clip"
elif command -v pbcopy &> /dev/null; then
    echo "     Mac: cat your-key.pem | pbcopy"
else
    echo "     Linux: cat your-key.pem | xclip -selection clipboard"
fi
echo ""

echo "3. Test SSH Connection:"
echo "   → Run: ssh -i your-key.pem ubuntu@16.170.25.9 'echo SSH works!'"
echo ""

echo "4. Verify EC2 Setup:"
echo "   → Docker installed"
echo "   → Docker Compose installed"
echo "   → .env.production file exists"
echo "   → Project directory: /home/ubuntu/mushqila"
echo ""

echo "=========================================="
echo "🧪 Testing"
echo "=========================================="
echo ""

echo "After setup, test with:"
echo ""
echo "1. Manual Trigger:"
echo "   → GitHub → Actions → Run workflow"
echo ""
echo "2. Automatic Trigger:"
echo "   → Make a change and push:"
echo "     git add ."
echo "     git commit -m 'Test: GitHub Actions'"
echo "     git push origin main"
echo ""

echo "=========================================="
echo "📚 Documentation"
echo "=========================================="
echo ""
echo "Full guide: GITHUB-ACTIONS-SETUP.md"
echo ""

echo "=========================================="
echo "✅ Setup Helper Complete"
echo "=========================================="
echo ""
echo "Next: Configure GitHub Secrets and test deployment!"
