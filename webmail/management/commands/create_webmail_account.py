from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from webmail.models import EmailAccount

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a new webmail email account'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email address')
        parser.add_argument('--password', type=str, required=True, help='Password for webmail login')
        parser.add_argument('--first-name', type=str, default='', help='First name')
        parser.add_argument('--last-name', type=str, default='', help='Last name')
        parser.add_argument('--mobile', type=str, default='', help='Mobile number')
        parser.add_argument('--alternate-email', type=str, default='', help='Alternate email address')
        parser.add_argument('--user-id', type=int, help='User ID to associate with (optional, will create new user if not provided)')
        parser.add_argument('--display-name', type=str, help='Display name (optional, will use first+last name if not provided)')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        mobile = options['mobile']
        alternate_email = options['alternate_email']
        user_id = options.get('user_id')
        display_name = options.get('display_name')

        # Check if email already exists
        if EmailAccount.objects.filter(email_address=email).exists():
            self.stdout.write(self.style.ERROR(f'Email account {email} already exists!'))
            return

        # Get or create user
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(self.style.SUCCESS(f'Using existing user: {user.username}'))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found!'))
                return
        else:
            # Create new user
            username = email.split('@')[0]
            # Make username unique if it already exists
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            self.stdout.write(self.style.SUCCESS(f'Created new user: {user.username}'))

        # Set display name
        if not display_name:
            if first_name and last_name:
                display_name = f"{first_name} {last_name}"
            elif first_name:
                display_name = first_name
            else:
                display_name = email.split('@')[0]

        # Create email account
        account = EmailAccount.objects.create(
            user=user,
            email_address=email,
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            mobile_number=mobile,
            alternate_email=alternate_email,
            is_default=True,
            is_active=True
        )
        
        # Set password
        account.set_password(password)
        account.save()

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Email Account Created Successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Email: {account.email_address}')
        self.stdout.write(f'Display Name: {account.display_name}')
        self.stdout.write(f'First Name: {account.first_name}')
        self.stdout.write(f'Last Name: {account.last_name}')
        self.stdout.write(f'Mobile: {account.mobile_number}')
        self.stdout.write(f'Alternate Email: {account.alternate_email}')
        self.stdout.write(f'User: {user.username}')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.WARNING('User can now login to webmail using:'))
        self.stdout.write(f'  Email: {email}')
        self.stdout.write(f'  Password: [the password you provided]')
        self.stdout.write(self.style.SUCCESS('=' * 60))
