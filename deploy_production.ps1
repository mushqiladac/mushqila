# Production Deployment Script for Mushqila Finance App (PowerShell)
# This script sets up PostgreSQL and deploys the application

Write-Host "🚀 Starting Production Deployment for Mushqila Finance App..." -ForegroundColor Green

# Check if PostgreSQL is installed
try {
    $psqlVersion = & psql --version 2>$null
    Write-Host "✅ PostgreSQL found: $psqlVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ PostgreSQL is not installed. Please install PostgreSQL first." -ForegroundColor Red
    Write-Host "Download from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    exit 1
}

# Database configuration
$DB_NAME = if ($env:DB_NAME) { $env:DB_NAME } else { "mushqila" }
$DB_USER = if ($env:DB_USER) { $env:DB_USER } else { "postgres" }
$DB_PASSWORD = if ($env:DB_PASSWORD) { $env:DB_PASSWORD } else { "EMR@55nondita" }

Write-Host "📊 Setting up PostgreSQL database..." -ForegroundColor Blue

# Set environment variables
$env:DJANGO_SETTINGS_MODULE = "config.settings_production"
$env:DB_NAME = $DB_NAME
$env:DB_USER = $DB_USER
$env:DB_PASSWORD = $DB_PASSWORD
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"

Write-Host "🔧 Running Django migrations..." -ForegroundColor Blue
try {
    python manage.py migrate --settings=config.settings_production
    Write-Host "✅ Migrations completed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Migration failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Collecting static files..." -ForegroundColor Blue
try {
    python manage.py collectstatic --noinput --settings=config.settings_production
    Write-Host "✅ Static files collected successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Static file collection failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "👥 Creating production users..." -ForegroundColor Blue
try {
    python create_production_users.py
    Write-Host "✅ Production users created successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ User creation failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "🔐 Creating superuser (if needed)..." -ForegroundColor Blue
try {
    python manage.py createsuperuser --settings=config.settings_production --noinput
    Write-Host "✅ Superuser creation completed" -ForegroundColor Green
} catch {
    Write-Host "ℹ️ Superuser already exists or creation skipped" -ForegroundColor Yellow
}

Write-Host "🎯 Production deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "- PostgreSQL database: $DB_NAME" -ForegroundColor White
Write-Host "- Database user: $DB_USER" -ForegroundColor White
Write-Host "- Settings module: config.settings_production" -ForegroundColor White
Write-Host ""
Write-Host "🔑 Default Users Created:" -ForegroundColor Cyan
Write-Host "1. Admin: saddam110@mushqila.com / Sinan210" -ForegroundColor White
Write-Host "2. Manager: manager110@mushqila.com / Sinan210@" -ForegroundColor White
Write-Host "3. User: mhcl107@mushqila.com / Sinan217" -ForegroundColor White
Write-Host "4. User: mhcl104@mushqila.com / Sinan214" -ForegroundColor White
Write-Host "5. User: mhcl108@mushqila.com / Sinan218" -ForegroundColor White
Write-Host "6. User: mhcl007@mushqila.com / Sinan207" -ForegroundColor White
Write-Host "7. User: mhcl112@mushqila.com / Sinan212" -ForegroundColor White
Write-Host ""
Write-Host "🌐 To start the production server:" -ForegroundColor Cyan
Write-Host 'env:DJANGO_SETTINGS_MODULE="config.settings_production"' -ForegroundColor Yellow
Write-Host "python manage.py runserver 0.0.0.0:8000" -ForegroundColor Yellow
