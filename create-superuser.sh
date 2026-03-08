#!/bin/bash
# Create Django Superuser Script

echo "=== Creating Django Superuser ==="
echo "Email: mushqiladac@gmail.com"
echo "Password: Sinan210@"
echo ""

# Create superuser using environment variables
docker-compose -f docker-compose.prod.yml exec -T web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

email = 'mushqiladac@gmail.com'
password = 'Sinan210@'

if User.objects.filter(email=email).exists():
    print(f'User {email} already exists')
    user = User.objects.get(email=email)
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f'Updated existing user {email} with superuser privileges')
else:
    User.objects.create_superuser(
        email=email,
        password=password,
        first_name='Admin',
        last_name='User'
    )
    print(f'Created superuser {email}')
EOF

echo ""
echo "✓ Superuser setup complete!"
echo "You can now login at: https://mushqila.com/admin/"
