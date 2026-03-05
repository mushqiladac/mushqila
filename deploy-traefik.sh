#!/bin/bash

# Traefik Deployment Script for Mushqila
# This script automates the Traefik SSL deployment process

set -e  # Exit on error

echo "🚀 Starting Traefik SSL Deployment..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on EC2
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ Error: .env.production file not found!${NC}"
    echo "Please create .env.production file first."
    exit 1
fi

# Step 1: Create Docker network
echo -e "${YELLOW}📡 Step 1: Creating Docker network 'proxy'...${NC}"
if docker network inspect proxy >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Network 'proxy' already exists${NC}"
else
    docker network create proxy
    echo -e "${GREEN}✅ Network 'proxy' created${NC}"
fi
echo ""

# Step 2: Create traefik-data directory and acme.json
echo -e "${YELLOW}📁 Step 2: Setting up Traefik data directory...${NC}"
mkdir -p traefik-data
if [ ! -f "traefik-data/acme.json" ]; then
    touch traefik-data/acme.json
    chmod 600 traefik-data/acme.json
    echo -e "${GREEN}✅ acme.json created with correct permissions${NC}"
else
    chmod 600 traefik-data/acme.json
    echo -e "${GREEN}✅ acme.json already exists, permissions updated${NC}"
fi
echo ""

# Step 3: Check Cloudflare API token
echo -e "${YELLOW}🔑 Step 3: Checking Cloudflare API configuration...${NC}"
if grep -q "CLOUDFLARE_API_TOKEN=your_cloudflare_api_token_here" .env.production; then
    echo -e "${RED}❌ Warning: Cloudflare API token not configured!${NC}"
    echo "Please update CLOUDFLARE_API_TOKEN in .env.production"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
elif grep -q "CLOUDFLARE_API_TOKEN=" .env.production; then
    echo -e "${GREEN}✅ Cloudflare API token configured${NC}"
else
    echo -e "${RED}❌ Warning: CLOUDFLARE_API_TOKEN not found in .env.production${NC}"
    echo "Please add Cloudflare configuration to .env.production"
    exit 1
fi
echo ""

# Step 4: Stop old deployment
echo -e "${YELLOW}🛑 Step 4: Stopping old deployment...${NC}"
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    docker-compose -f docker-compose.prod.yml down
    echo -e "${GREEN}✅ Old deployment stopped${NC}"
else
    echo -e "${GREEN}✅ No old deployment running${NC}"
fi
echo ""

# Step 5: Build and start Traefik deployment
echo -e "${YELLOW}🏗️  Step 5: Building and starting Traefik deployment...${NC}"
docker-compose -f docker-compose.traefik.yml up -d --build
echo -e "${GREEN}✅ Traefik deployment started${NC}"
echo ""

# Step 6: Wait for services to be ready
echo -e "${YELLOW}⏳ Step 6: Waiting for services to start...${NC}"
sleep 10
echo ""

# Step 7: Check container status
echo -e "${YELLOW}📊 Step 7: Checking container status...${NC}"
docker-compose -f docker-compose.traefik.yml ps
echo ""

# Step 8: Show Traefik logs
echo -e "${YELLOW}📝 Step 8: Checking Traefik logs for SSL certificate...${NC}"
echo "Waiting for SSL certificate generation (this may take 2-3 minutes)..."
echo ""

# Wait and check for certificate
for i in {1..30}; do
    if docker logs traefik 2>&1 | grep -q "Certificates obtained"; then
        echo -e "${GREEN}✅ SSL Certificate obtained successfully!${NC}"
        break
    fi
    echo -n "."
    sleep 5
done
echo ""
echo ""

# Step 9: Final status
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "Access your site at:"
echo "  - https://mushqila.com"
echo "  - https://www.mushqila.com"
echo "  - https://mushqila.com/admin/"
echo "  - https://mushqila.com/webmail/"
echo "  - https://traefik.mushqila.com (Dashboard - admin/admin)"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.traefik.yml logs -f"
echo "  - Check status: docker-compose -f docker-compose.traefik.yml ps"
echo "  - Restart: docker-compose -f docker-compose.traefik.yml restart"
echo "  - Stop: docker-compose -f docker-compose.traefik.yml down"
echo ""
echo -e "${YELLOW}Note: SSL certificate generation may take 2-3 minutes.${NC}"
echo -e "${YELLOW}Check Traefik logs: docker logs traefik -f${NC}"
echo ""
