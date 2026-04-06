from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from webmail.models import EmailAccount

User = get_user_model()


class Command(BaseCommand):
    help = 'Create 8 email accounts for mushqila.com'

    def handle(self, *args, **options):
        # Define 5 email accounts for Mushqila team
        email_accounts = [
            {
                'email': 'shahin_sarker@mushqila.com',
                'username': 'shahin_sarker',
                'display_name': 'Shahin Sarker',
                'password': 'Shahin@Mushqila2026'
            },
            {
                'email': 'aysha@mushqila.com',
                'username': 'aysha',
                'display_name': 'Aysha',
                'password': 'Aysha@Mushqila2026'
            },
            {
                'email': 'refat@mushqila.com',
                'username': 'refat',
                'display_name': 'Refat',
                'password': 'Refat@Mushqila2026'
            },
            {
                'email': 'support@mushqila.com',
                'username': 'support',
                'display_name': 'Mushqila Support',
                'password': 'Support@Mushqila2026'
            },
            {
                'email': 'eliuss@mushqila.com',
                'username': 'eliuss',
                'display_name': 'Eliuss',
                'password': 'Eliuss@Mushqila2026'
            },
        ]

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Creating 5 Email Accounts for Mushqila Team'))
        self.stdout.write('='*70 + '\n')

        created_count = 0
        updated_count = 0

        for account_data in email_accounts:
            email = account_data['email']
            username = account_data['username']
            display_name = account_data['display_name']
            password = account_data['password']

            # Create or get user
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': display_name.split()[0],
                    'last_name': ' '.join(display_name.split()[1:]) if len(display_name.split()) > 1 else '',
                }
            )

            if user_created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created user: {username}')
                )
            else:
                # Update password for existing user
                user.set_password(password)
                user.email = email
                user.save()
                self.stdout.write(
                    self.style.WARNING(f'⚠ Updated existing user: {username}')
                )

            # Create or get email account
            email_account, account_created = EmailAccount.objects.get_or_create(
                user=user,
                email_address=email,
                defaults={
                    'display_name': display_name,
                    'is_default': True,
                    'is_active': True,
                }
            )

            if account_created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created email account: {email}')
                )
            else:
                updated_count += 1
                email_account.display_name = display_name
                email_account.is_active = True
                email_account.save()
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ Updated email account: {email}')
                )

            self.stdout.write(
                f'    Username: {username}\n'
                f'    Password: {password}\n'
                f'    Email: {email}\n'
            )

        self.stdout.write('\n' + '='*70)
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Summary: {created_count} created, {updated_count} updated'
            )
        )
        self.stdout.write('='*70 + '\n')

        # Print login instructions
        self.stdout.write('\n' + self.style.SUCCESS('LOGIN INSTRUCTIONS:'))
        self.stdout.write('='*70)
        self.stdout.write('URL: https://mushqila.com/webmail/login/')
        self.stdout.write('\nCredentials:\n')
        
        for account_data in email_accounts:
            self.stdout.write(
                f"  {account_data['email']}\n"
                f"    Username: {account_data['username']}\n"
                f"    Password: {account_data['password']}\n"
            )
        
        self.stdout.write('='*70 + '\n')
        
        self.stdout.write(
            self.style.WARNING(
                '\n⚠ IMPORTANT: Change these default passwords after first login!'
            )
        )
