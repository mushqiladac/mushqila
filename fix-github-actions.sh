#!/bin/bash

# GitHub Actions Deployment Fix Script

echo "=========================================="
echo "GitHub Actions Deployment Troubleshooting"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "This script will help you fix GitHub Actions deployment issues."
echo ""

# Step 1: Check if workflow file exists
echo "Step 1: Checking workflow file..."
if [ -f ".github/workflows/deploy.yml" ]; then
    echo -e "${GREEN}✓${NC} Workflow file exists"
else
    echo -e "${RED}✗${NC} Workflow file not found"
    exit 1
fi

# Step 2: Check GitHub secrets
echo ""
echo "Step 2: GitHub Secrets Check"
echo "-----------------------------------"
echo "Please verify these secrets exist in GitHub:"
echo "https://github.com/mushqiladac/mushqila/settings/secrets/actions"
echo ""
echo "Required secrets:"
echo "  1. EC2_HOST = ec2-16-171-21-135.eu-north-1.compute.amazonaws.com"
echo "  2. EC2_USERNAME = ubuntu"
echo "  3. EC2_SSH_KEY = [Your private SSH key]"
echo ""
read -p "Are all secrets configured? (y/n): " secrets_ok

if [ "$secrets_ok" != "y" ]; then
    echo ""
    echo -e "${YELLOW}⚠${NC} Please add missing secrets to GitHub:"
    echo "1. Go to: https://github.com/mushqiladac/mushqila/settings/secrets/actions"
    echo "2. Click 'New repository secret'"
    echo "3. Add each secret with the values above"
    echo ""
    exit 1
fi

# Step 3: Test SSH connection
echo ""
echo "Step 3: Testing SSH Connection..."
echo "-----------------------------------"
read -p "Do you want to test SSH connection? (y/n): " test_ssh

if [ "$test_ssh" = "y" ]; then
    echo "Testing SSH connection to EC2..."
    ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com "echo 'SSH connection successful'" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} SSH connection successful"
    else
        echo -e "${RED}✗${NC} SSH connection failed"
        echo "Please check:"
        echo "  - SSH key is correct"
        echo "  - EC2 security group allows SSH from your IP"
        echo "  - EC2 instance is running"
        exit 1
    fi
fi

# Step 4: Options
echo ""
echo "=========================================="
echo "What would you like to do?"
echo "=========================================="
echo "1. Deploy manually via SSH (Recommended)"
echo "2. Disable auto-deploy (rename workflow)"
echo "3. View GitHub Actions logs"
echo "4. Create simplified workflow"
echo "5. Exit"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Deploying manually via SSH..."
        echo "-----------------------------------"
        ssh ubuntu@ec2-16-171-21-135.eu-north-1.compute.amazonaws.com << 'ENDSSH'
            set -e
            cd ~/mushqila
            echo "📥 Pulling latest code..."
            git pull origin main
            echo "🐳 Deploying with Docker..."
            docker-compose -f docker-compose.prod.yml down
            docker-compose -f docker-compose.prod.yml up -d --build
            echo "⏳ Waiting for startup..."
            sleep 20
            echo "📊 Running migrations..."
            docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate
            echo "📁 Collecting static files..."
            docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
            echo "✅ Deployment complete!"
            docker-compose -f docker-compose.prod.yml ps
ENDSSH
        echo ""
        echo -e "${GREEN}✓${NC} Manual deployment completed!"
        ;;
    
    2)
        echo ""
        echo "Disabling auto-deploy..."
        if [ -f ".github/workflows/deploy.yml" ]; then
            git mv .github/workflows/deploy.yml .github/workflows/deploy.yml.disabled
            git commit -m "chore: Temporarily disable auto-deploy"
            echo -e "${GREEN}✓${NC} Auto-deploy disabled"
            echo "To re-enable, rename deploy.yml.disabled back to deploy.yml"
        else
            echo -e "${RED}✗${NC} Workflow file not found"
        fi
        ;;
    
    3)
        echo ""
        echo "Opening GitHub Actions logs..."
        echo "URL: https://github.com/mushqiladac/mushqila/actions"
        echo ""
        echo "Look for:"
        echo "  - Red error messages"
        echo "  - Failed steps"
        echo "  - Connection errors"
        ;;
    
    4)
        echo ""
        echo "Creating simplified workflow..."
        cat > .github/workflows/deploy-simple.yml << 'EOF'
name: Deploy to Production (Simple)

on:
  workflow_dispatch:  # Manual trigger only

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_KEY }}
          command_timeout: 20m
          script: |
            cd /home/ubuntu/mushqila
            git pull origin main
            docker-compose -f docker-compose.prod.yml up -d --build
            sleep 20
            docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate
            docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
EOF
        echo -e "${GREEN}✓${NC} Simplified workflow created: .github/workflows/deploy-simple.yml"
        echo "This workflow can be triggered manually from GitHub Actions tab"
        ;;
    
    5)
        echo "Exiting..."
        exit 0
        ;;
    
    *)
        echo -e "${RED}✗${NC} Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
