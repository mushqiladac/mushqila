# Test Deployment

This file is created to test automatic CI/CD deployment.

Timestamp: 2026-01-28 19:00:00

## What happens when you push:

1. GitHub Actions detects push to `dwd` branch
2. Connects to EC2 server via SSH
3. Pulls latest code
4. Rebuilds Docker containers
5. Runs migrations
6. Collects static files
7. Restarts application

## Status: Testing...
