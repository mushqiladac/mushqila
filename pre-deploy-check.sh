#!/bin/bash

# Pre-deployment checklist script
# Run this before deploying to ensure everything is ready

echo "=========================================="
echo "🔍 Pre-Deployment Checklist"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Function to check status
check_pass() {
    echo "✅ $1"
}

check_fail() {
    echo "❌ $1"
    ((ERRORS++))
}

check_warn() {
    echo "⚠️  $1"
    ((WARNINGS++))
}

# 1. Check if in git repository
echo "1. Checking Git Repository..."
if [ -d .git ]; then
    check_pass "Git repository found"
else
    check_fail "Not a git repository"
fi

# 2. Check for uncommitted changes
echo ""
echo "2. Checking for uncommitted changes..."
if [ -z "$(git status --porcelain)" ]; then
    check_warn "No uncommitted changes (deployment will use last commit)"
else
    check_pass "Uncommitted changes found (will be deployed)"
    git status --short
fi

# 3. Check Python syntax
echo ""
echo "3. Checking Python syntax..."
python_errors=0
for file in $(find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./env/*"); do
    if ! python -m py_compile "$file" 2>/dev/null; then
        check_fail "Syntax error in: $file"
        python_errors=1
    fi
done

if [ $python_errors -eq 0 ]; then
    check_pass "No Python syntax errors"
fi

# 4. Check critical files exist
echo ""
echo "4. Checking critical files..."
critical_files=(
    "config/urls.py"
    "config/settings.py"
    "docker-compose.prod.yml"
    ".github/workflows/deploy.yml"
    "requirements.txt"
)

for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_fail "$file missing"
    fi
done

# 5. Check for common issues
echo ""
echo "5. Checking for common issues..."

# Check for duplicate lines in urls.py
if grep -q "path('', include('b2c.urls'))," config/urls.py; then
    duplicates=$(grep -c "path('', include('b2c.urls'))," config/urls.py)
    if [ $duplicates -gt 1 ]; then
        check_fail "Duplicate lines found in config/urls.py"
    else
        check_pass "No duplicate lines in config/urls.py"
    fi
fi

# Check for TODO/FIXME comments
todo_count=$(grep -r "TODO\|FIXME" --include="*.py" . 2>/dev/null | wc -l)
if [ $todo_count -gt 0 ]; then
    check_warn "$todo_count TODO/FIXME comments found"
else
    check_pass "No TODO/FIXME comments"
fi

# 6. Check Docker files
echo ""
echo "6. Checking Docker configuration..."
if [ -f "Dockerfile" ]; then
    check_pass "Dockerfile exists"
else
    check_warn "Dockerfile not found"
fi

if [ -f "docker-compose.prod.yml" ]; then
    check_pass "docker-compose.prod.yml exists"
else
    check_fail "docker-compose.prod.yml missing"
fi

# 7. Check environment files
echo ""
echo "7. Checking environment files..."
if [ -f ".env.example" ]; then
    check_pass ".env.example exists"
else
    check_warn ".env.example not found"
fi

if [ -f ".env.production.template" ]; then
    check_pass ".env.production.template exists"
else
    check_warn ".env.production.template not found"
fi

# 8. Check GitHub Actions workflow
echo ""
echo "8. Checking GitHub Actions..."
if [ -f ".github/workflows/deploy.yml" ]; then
    check_pass "Deployment workflow exists"
    
    # Check if workflow is valid YAML
    if command -v python3 &> /dev/null; then
        if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))" 2>/dev/null; then
            check_pass "Workflow YAML is valid"
        else
            check_fail "Workflow YAML is invalid"
        fi
    fi
else
    check_fail "Deployment workflow missing"
fi

# 9. Check for large files
echo ""
echo "9. Checking for large files..."
large_files=$(find . -type f -size +10M -not -path "./.git/*" -not -path "./venv/*" 2>/dev/null)
if [ -z "$large_files" ]; then
    check_pass "No large files (>10MB) found"
else
    check_warn "Large files found (may slow deployment):"
    echo "$large_files"
fi

# 10. Check git remote
echo ""
echo "10. Checking Git remote..."
if git remote -v | grep -q "github.com"; then
    check_pass "GitHub remote configured"
    git remote -v | head -2
else
    check_fail "GitHub remote not configured"
fi

# Summary
echo ""
echo "=========================================="
echo "📊 Summary"
echo "=========================================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed!"
    echo ""
    echo "Ready to deploy! Run:"
    echo "  ./deploy.sh (Linux/Mac)"
    echo "  .\deploy.ps1 (Windows)"
    echo "  git push origin main (Manual)"
    echo ""
    exit 0
else
    echo "❌ Please fix errors before deploying"
    echo ""
    exit 1
fi
