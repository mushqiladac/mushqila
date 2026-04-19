from django.core.management.base import BaseCommand
from webmail.models import EmailAccount


class Command(BaseCommand):
    help = 'Set default passwords for existing email accounts that have empty passwords'

    def add_arguments(self, parser):
        parser.add_argument(
            '--default-password',
            type=str,
            default='changeme123',
            help='Default password to set for accounts without password (default: changeme123)'
        )

    def handle(self, *args, **options):
        default_password = options['default_password']
        
        # Find accounts with empty passwords
        accounts = EmailAccount.objects.filter(password='')
        count = accounts.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No accounts found with empty passwords.'))
            return
        
        self.stdout.write(f'Found {count} accounts with empty passwords.')
        self.stdout.write(f'Setting default password: {default_password}')
        
        for account in accounts:
            account.set_password(default_password)
            account.save()
            self.stdout.write(f'  ✓ Updated: {account.email_address}')
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} accounts!'))
        self.stdout.write(self.style.WARNING('IMPORTANT: Users should change their passwords after first login.'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
