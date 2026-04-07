# Quick deployment script for Mushqila (PowerShell)
# This will commit changes and trigger GitHub Actions deployment

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 Mushqila Deployment Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path .git)) {
    Write-Host "❌ Error: Not a git repository" -ForegroundColor Red
    exit 1
}

# Check for uncommitted changes
$status = git status --porcelain
if ([string]::IsNullOrEmpty($status)) {
    Write-Host "ℹ️  No changes to commit" -ForegroundColor Yellow
    $response = Read-Host "Do you want to trigger deployment anyway? (y/n)"
    if ($response -ne "y") {
        Write-Host "Deployment cancelled" -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "📝 Changes detected:" -ForegroundColor Green
    git status --short
    Write-Host ""
}

# Get commit message
Write-Host "Enter commit message (or press Enter for default):" -ForegroundColor Cyan
$commit_msg = Read-Host

if ([string]::IsNullOrEmpty($commit_msg)) {
    $commit_msg = "Deploy: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

Write-Host ""
Write-Host "📦 Preparing deployment..." -ForegroundColor Green
Write-Host "   Commit message: $commit_msg" -ForegroundColor Gray
Write-Host ""

# Add all changes
Write-Host "→ Adding changes..." -ForegroundColor Yellow
git add .

# Commit
Write-Host "→ Committing..." -ForegroundColor Yellow
try {
    git commit -m $commit_msg
} catch {
    Write-Host "ℹ️  Nothing to commit, triggering deployment anyway..." -ForegroundColor Yellow
}

# Push to main
Write-Host "→ Pushing to GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ Code pushed to GitHub!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🔄 GitHub Actions will now:" -ForegroundColor Cyan
Write-Host "   1. Create backup" -ForegroundColor Gray
Write-Host "   2. Pull latest code" -ForegroundColor Gray
Write-Host "   3. Validate syntax" -ForegroundColor Gray
Write-Host "   4. Build Docker images" -ForegroundColor Gray
Write-Host "   5. Deploy with zero downtime" -ForegroundColor Gray
Write-Host "   6. Run migrations" -ForegroundColor Gray
Write-Host "   7. Collect static files" -ForegroundColor Gray
Write-Host "   8. Health check" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 Monitor deployment at:" -ForegroundColor Cyan
Write-Host "   https://github.com/mushqiladac/mushqila/actions" -ForegroundColor Blue
Write-Host ""
Write-Host "🌐 Site will be live at:" -ForegroundColor Cyan
Write-Host "   https://mushqila.com" -ForegroundColor Blue
Write-Host ""
Write-Host "⏱️  Estimated time: 3-4 minutes" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan

# Open browser to GitHub Actions
$openBrowser = Read-Host "Open GitHub Actions in browser? (y/n)"
if ($openBrowser -eq "y") {
    Start-Process "https://github.com/mushqiladac/mushqila/actions"
}
