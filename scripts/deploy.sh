#!/bin/bash

# Finance App Deployment Script
# This script handles deployment of the finance app to production

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/mushqila"
BACKUP_DIR="/var/www/backups/mushqila"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="/var/log/mushqila/deploy.log"

# Functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Main deployment function
deploy() {
    log "Starting finance app deployment..."
    
    # Create backup
    log "Creating backup..."
    if [ -d "$PROJECT_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
        cp -r "$PROJECT_DIR" "$BACKUP_DIR/$BACKUP_NAME"
        success "Backup created: $BACKUP_DIR/$BACKUP_NAME"
    else
        warning "No existing project directory found, skipping backup"
    fi
    
    # Navigate to project directory
    cd "$PROJECT_DIR" || error "Cannot navigate to project directory"
    
    # Activate virtual environment
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        success "Virtual environment activated"
    else
        error "Virtual environment not found"
    fi
    
    # Install/update dependencies
    log "Installing dependencies..."
    pip install -r requirements.txt || error "Failed to install dependencies"
    success "Dependencies installed"
    
    # Run database migrations
    log "Running database migrations..."
    python manage.py migrate finance --settings=config.settings_production --noinput || error "Migration failed"
    success "Migrations completed"
    
    # Collect static files
    log "Collecting static files..."
    python manage.py collectstatic --noinput --settings=config.settings_production || error "Static files collection failed"
    success "Static files collected"
    
    # Create initial data if needed
    log "Checking initial data setup..."
    python manage.py setup_finance --settings=config.settings_production || warning "Initial data setup failed (may already exist)"
    
    # Restart services
    log "Restarting services..."
    sudo systemctl restart gunicorn || error "Failed to restart gunicorn"
    sudo systemctl restart nginx || error "Failed to restart nginx"
    success "Services restarted"
    
    # Health check
    log "Performing health check..."
    sleep 5  # Give services time to start
    
    if curl -f -s http://localhost/finance/ > /dev/null; then
        success "Health check passed"
    else
        error "Health check failed"
    fi
    
    # Run security checks
    log "Running security checks..."
    python manage.py check --deploy --settings=config.settings_production || warning "Security check found issues"
    
    success "Deployment completed successfully!"
}

# Rollback function
rollback() {
    log "Starting rollback..."
    
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR" | head -n 1)
    if [ -z "$LATEST_BACKUP" ]; then
        error "No backup found for rollback"
    fi
    
    log "Rolling back to: $LATEST_BACKUP"
    
    # Stop services
    sudo systemctl stop gunicorn nginx
    
    # Restore from backup
    rm -rf "$PROJECT_DIR"
    cp -r "$BACKUP_DIR/$LATEST_BACKUP" "$PROJECT_DIR"
    
    # Restart services
    sudo systemctl start gunicorn nginx
    
    success "Rollback completed"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    health)
        log "Performing health check..."
        if curl -f -s http://localhost/finance/ > /dev/null; then
            success "Application is healthy"
        else
            error "Application health check failed"
        fi
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|health}"
        exit 1
        ;;
esac
