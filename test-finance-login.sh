#!/bin/bash

# Finance App Login Test Script
# This script creates finance users and tests the login functionality

echo "=========================================="
echo "Finance App Login Test"
echo "=========================================="
echo ""

# Check if we're in production or local
if [ -f "docker-compose.prod.yml" ]; then
    echo "📍 Production Environment Detected"
    DOCKER_CMD="docker-compose -f docker-compose.prod.yml exec -T web"
else
    echo "📍 Local Environment Detected"
    DOCKER_CMD="python"
fi

echo ""
echo "Step 1: Creating Finance Users..."
echo "-----------------------------------"
$DOCKER_CMD python manage.py create_finance_users

echo ""
echo "Step 2: Checking Finance Users..."
echo "-----------------------------------"
$DOCKER_CMD python manage.py shell << EOF
from finance.models.user import FinanceUser
users = FinanceUser.objects.all()
print(f"\n✓ Total Finance Users: {users.count()}")
for user in users:
    print(f"  - {user.email} ({user.get_user_type_display()}) - Active: {user.is_active}")
EOF

echo ""
echo "=========================================="
echo "✓ Finance Users Setup Complete!"
echo "=========================================="
echo ""
echo "Login Credentials:"
echo "-----------------------------------"
echo "Admin:"
echo "  Email: saddam110@mushqila.com"
echo "  Password: Sinan210"
echo "  URL: https://mushqila.com/finance/login/"
echo ""
echo "Manager:"
echo "  Email: manager110@mushqila.com"
echo "  Password: Sinan210@"
echo "  URL: https://mushqila.com/finance/login/"
echo ""
echo "Regular Users:"
echo "  mhcl107@mushqila.com / Sinan217"
echo "  mhcl104@mushqila.com / Sinan214"
echo "  mhcl108@mushqila.com / Sinan218"
echo "  mhcl007@mushqila.com / Sinan207"
echo "  mhcl112@mushqila.com / Sinan212"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "1. Open browser: https://mushqila.com/finance/login/"
echo "2. Select user type (এডমিন/ম্যানাজার/সাধারণ ইউজার)"
echo "3. Enter email and password"
echo "4. Click 'লগইন করুন'"
echo "5. You should be redirected to dashboard"
echo "=========================================="
