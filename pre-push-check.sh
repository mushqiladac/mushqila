#!/bin/bash

# Pre-push check script for Mushqila project
# Run this before pushing to GitHub

echo "🔍 Running pre-push checks..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Check 1: Python syntax
echo "1️⃣  Checking Python syntax..."
python -m py_compile config/*.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python syntax OK${NC}"
else
    echo -e "${RED}✗ Python syntax errors found${NC}"
    ERRORS=$((ERRORS+1))
fi
echo ""

# Check 2: Required files exist
echo "2️⃣  Checking required files..."
REQUIRED_FILES=(
    "Dockerfile"
    "docker-compose.yml"
    "docker-compose.prod.yml"
    "requirements.txt"
    ".env.production"
    ".github/workflows/deploy.yml"
    "entrypoint.sh"
    "deploy.sh"
    "setup-ec2.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file missing"
        ERRORS=$((ERRORS+1))
    fi
done
echo ""

# Check 3: .gitignore includes sensitive files
echo "3️⃣  Checking .gitignore..."
SENSITIVE_PATTERNS=(
    ".env"
    ".env.production"
    "*.pem"
    "*.key"
    "db.sqlite3"
)

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if grep -q "$pattern" .gitignore 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $pattern in .gitignore"
    else
        echo -e "${YELLOW}⚠${NC} $pattern not in .gitignore"
    fi
done
echo ""

# Check 4: No sensitive data in files
echo "4️⃣  Checking for sensitive data..."
if grep -r "password.*=" --include="*.py" --exclude-dir=menv --exclude-dir=venv . | grep -v "PASSWORD" | grep -v "# " | grep -v "def " > /dev/null; then
    echo -e "${YELLOW}⚠ Possible passwords found in code${NC}"
else
    echo -e "${GREEN}✓ No obvious passwords in code${NC}"
fi
echo ""

# Check 5: Docker files are valid
echo "5️⃣  Checking Docker configuration..."
if command -v docker &> /dev/null; then
    docker-compose -f docker-compose.prod.yml config > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Docker Compose configuration valid${NC}"
    else
        echo -e "${RED}✗ Docker Compose configuration invalid${NC}"
        ERRORS=$((ERRORS+1))
    fi
else
    echo -e "${YELLOW}⚠ Docker not installed, skipping Docker checks${NC}"
fi
echo ""

# Check 6: GitHub Actions workflow is valid
echo "6️⃣  Checking GitHub Actions workflow..."
if [ -f ".github/workflows/deploy.yml" ]; then
    echo -e "${GREEN}✓ GitHub Actions workflow exists${NC}"
else
    echo -e "${RED}✗ GitHub Actions workflow missing${NC}"
    ERRORS=$((ERRORS+1))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to push to GitHub${NC}"
    echo ""
    echo "Next steps:"
    echo "1. git add ."
    echo "2. git commit -m 'Your message'"
    echo "3. git push origin main"
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) found. Please fix before pushing${NC}"
    exit 1
fi
