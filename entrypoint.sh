#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting Mushqila Application..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "✅ Redis is ready!"

# Run database migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create cache table if it doesn't exist
echo "🗄️  Creating cache table..."
python manage.py createcachetable || true

# Start Gunicorn server
echo "🌐 Starting Gunicorn server..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
