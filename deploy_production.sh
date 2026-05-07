#!/bin/bash

# Production Deployment Script for Mushqila Finance App
# This script sets up PostgreSQL and deploys the application

set -e

echo "🚀 Starting Production Deployment for Mushqila Finance App..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first."
    echo "Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "CentOS/RHEL: sudo yum install postgresql-server postgresql-contrib"
    echo "macOS: brew install postgresql"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running. Starting PostgreSQL..."
    sudo systemctl start postgresql || sudo service postgresql start
fi

# Database configuration
DB_NAME=${DB_NAME:-mushqila}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-EMR@55nondita}

echo "📊 Setting up PostgreSQL database..."

# Create database if it doesn't exist
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database $DB_NAME already exists"

# Create user if it doesn't exist
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "User $DB_USER already exists"

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"

echo "✅ PostgreSQL database setup completed"

# Set environment variables
export DJANGO_SETTINGS_MODULE=config.settings_production
export DB_NAME=$DB_NAME
export DB_USER=$DB_USER
export DB_PASSWORD=$DB_PASSWORD
export DB_HOST=localhost
export DB_PORT=5432

echo "🔧 Running Django migrations..."
python manage.py migrate --settings=config.settings_production

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --settings=config.settings_production

echo "👥 Creating production users..."
python create_production_users.py

echo "🔐 Creating superuser (if needed)..."
python manage.py createsuperuser --settings=config.settings_production --noinput || echo "Superuser already exists"

echo "🎯 Production deployment completed successfully!"
echo ""
echo "📋 Summary:"
echo "- PostgreSQL database: $DB_NAME"
echo "- Database user: $DB_USER"
echo "- Settings module: config.settings_production"
echo ""
echo "🔑 Default Users Created:"
echo "1. Admin: saddam110@mushqila.com / Sinan210"
echo "2. Manager: manager110@mushqila.com / Sinan210@"
echo "3. User: mhcl107@mushqila.com / Sinan217"
echo "4. User: mhcl104@mushqila.com / Sinan214"
echo "5. User: mhcl108@mushqila.com / Sinan218"
echo "6. User: mhcl007@mushqila.com / Sinan207"
echo "7. User: mhcl112@mushqila.com / Sinan212"
echo ""
echo "🌐 To start the production server:"
echo "export DJANGO_SETTINGS_MODULE=config.settings_production"
echo "python manage.py runserver 0.0.0.0:8000"
