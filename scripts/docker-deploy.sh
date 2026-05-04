#!/bin/bash

# Docker Deployment Script for Finance App
# This script handles Docker deployment with proper error handling

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

error() {
    echo -e "${RED}ERROR: $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

# Main deployment function
deploy() {
    log "Starting Docker deployment for Finance App..."
    
    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down || warning "No containers to stop"
    
    # Build new images
    log "Building Docker images..."
    docker-compose -f docker-compose.prod.yml build || error "Docker build failed"
    
    # Start containers
    log "Starting containers..."
    docker-compose -f docker-compose.prod.yml up -d || error "Container startup failed"
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    log "Running database migrations..."
    docker-compose -f docker-compose.prod.yml exec web python manage.py migrate finance --settings=config.settings_production --noinput || error "Migration failed"
    
    # Create initial data
    log "Creating initial data..."
    docker-compose -f docker-compose.prod.yml exec web python manage.py setup_finance --settings=config.settings_production || warning "Initial data setup failed (may already exist)"
    
    # Collect static files
    log "Collecting static files..."
    docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput --settings=config.settings_production || error "Static files collection failed"
    
    # Check container status
    log "Checking container status..."
    docker-compose -f docker-compose.prod.yml ps
    
    # Health check
    log "Performing health check..."
    sleep 5
    
    if curl -f -s http://localhost:8000/finance/ > /dev/null; then
        success "Health check passed"
    else
        warning "Health check failed - checking logs"
        docker-compose -f docker-compose.prod.yml logs web --tail=20
    fi
    
    success "Docker deployment completed successfully!"
}

# Logs function
logs() {
    log "Showing container logs..."
    docker-compose -f docker-compose.prod.yml logs -f --tail=50
}

# Cleanup function
cleanup() {
    log "Cleaning up Docker resources..."
    docker-compose -f docker-compose.prod.yml down -v
    docker system prune -f
    success "Cleanup completed"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    logs)
        logs
        ;;
    cleanup)
        cleanup
        ;;
    restart)
        log "Restarting containers..."
        docker-compose -f docker-compose.prod.yml restart
        success "Containers restarted"
        ;;
    status)
        log "Container status:"
        docker-compose -f docker-compose.prod.yml ps
        ;;
    *)
        echo "Usage: $0 {deploy|logs|cleanup|restart|status}"
        exit 1
        ;;
esac
