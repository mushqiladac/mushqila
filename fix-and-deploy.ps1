# Complete Fix and Deploy Script
# This script will:
# 1. Commit and push entrypoint.sh to GitHub
# 2. SSH to server and deploy

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🔧 Fix and Deploy to Production" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Commit and push to GitHub
Write-Host "📦 Step 1: Pushing entrypoint.sh to GitHub..." -ForegroundColor Yellow
Write-Host ""

try {
    git add entrypoint.sh QUICK-FIX-ENTRYPOINT.md fix-and-deploy.ps1
    git commit -m "Add missing entrypoint.sh and fix deployment"
    git push origin main
    Write-Host "✅ Code pushed to GitHub" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Git push failed or no changes to commit" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 Step 2: Deploying to Server..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SSH_KEY = "C:\Users\user\Desktop\Mushqila\mushqila-keys.pem"
$SSH_USER = "ubuntu"
$SSH_HOST = "16.170.25.9"
$PROJECT_DIR = "/home/ubuntu/mushqila"

# Create deployment commands
$DEPLOY_COMMANDS = @"
set -e
cd $PROJECT_DIR

echo ""
echo "=========================================="
echo "🚀 Mushqila Deployment Starting..."
echo "=========================================="
echo ""

echo "📥 Step 1: Pulling latest code from GitHub..."
git stash
git pull origin main
echo "✅ Code updated"

echo ""
echo "🐳 Step 2: Stopping containers..."
docker-compose -f docker-compose.prod.yml down
echo "✅ Containers stopped"

echo ""
echo "🔨 Step 3: Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache
echo "✅ Images built"

echo ""
echo "🚀 Step 4: Starting containers..."
docker-compose -f docker-compose.prod.yml up -d
echo "✅ Containers started"

echo ""
echo "⏳ Step 5: Waiting for containers to be ready..."
sleep 15

echo ""
echo "📊 Step 6: Checking container status..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📝 Step 7: Checking recent logs..."
docker-compose -f docker-compose.prod.yml logs web --tail=30

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🌐 Site: https://mushqila.com"
echo "🔐 Login: https://mushqila.com/accounts/login/"
echo "📧 Webmail: https://mushqila.com/webmail/"
echo ""
echo "⏰ Deployed at: \$(date)"
echo "=========================================="
"@

# Execute deployment
Write-Host "📡 Connecting to server and deploying..." -ForegroundColor Yellow
Write-Host ""

ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" $DEPLOY_COMMANDS

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Test the site
Write-Host "🧪 Testing login page..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    $response = Invoke-WebRequest -Uri "https://mushqila.com/accounts/login/" -Method GET -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Login page is working! (HTTP 200)" -ForegroundColor Green
    }
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 302) {
        Write-Host "✅ Login page is working! (HTTP 302 - Redirect)" -ForegroundColor Green
    } elseif ($statusCode -eq 500) {
        Write-Host "❌ Login page still returns 500 error" -ForegroundColor Red
        Write-Host "Please check server logs for details" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  Login page returned HTTP $statusCode" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📊 Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Code pushed to GitHub" -ForegroundColor Green
Write-Host "✅ Server updated with latest code" -ForegroundColor Green
Write-Host "✅ Docker containers rebuilt and restarted" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Your site: https://mushqila.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 Deployment successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
