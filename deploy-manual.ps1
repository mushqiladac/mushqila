# Manual Deployment Script for Windows
# Run this from PowerShell in project directory

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 Manual Deployment to Production" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SSH_KEY = "C:\Users\user\Desktop\Mushqila\mushqila-keys.pem"
$SSH_USER = "ubuntu"
$SSH_HOST = "16.170.25.9"
$PROJECT_DIR = "/home/ubuntu/mushqila"

Write-Host "📡 Connecting to server..." -ForegroundColor Yellow

# Create deployment commands
$DEPLOY_COMMANDS = @"
set -e
cd $PROJECT_DIR

echo ""
echo "🔄 Stashing local changes..."
git stash

echo ""
echo "📥 Pulling latest code..."
git pull origin main

echo ""
echo "🐳 Rebuilding Docker containers..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache web

echo ""
echo "🚀 Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "⏳ Waiting for containers to start..."
sleep 10

echo ""
echo "📊 Running migrations..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

echo ""
echo "📁 Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput --clear

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📝 Recent logs:"
docker-compose -f docker-compose.prod.yml logs web --tail=20
"@

# Execute deployment
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" $DEPLOY_COMMANDS

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Site: https://mushqila.com" -ForegroundColor Cyan
Write-Host "🔐 Login: https://mushqila.com/accounts/login/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Testing login page..." -ForegroundColor Yellow

# Test the site
try {
    $response = Invoke-WebRequest -Uri "https://mushqila.com/accounts/login/" -Method GET -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Login page is working! (HTTP 200)" -ForegroundColor Green
    }
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 302) {
        Write-Host "✅ Login page is working! (HTTP 302 - Redirect)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Login page returned HTTP $statusCode" -ForegroundColor Yellow
        Write-Host "Please check manually: https://mushqila.com/accounts/login/" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 Deployment successful!" -ForegroundColor Green
