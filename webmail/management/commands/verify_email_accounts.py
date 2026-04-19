from django.core.management.base import BaseCommand
from webmail.models import EmailAccount
from webmail.services.ses_auto_config import SESAutoConfigService


class Command(BaseCommand):
    help = 'Check verification status of all email accounts in SES'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Check specific email address only'
        )
    
    def handle(self, *args, **options):
        config_service = SESAutoConfigService()
        
        # Filter accounts
        if options.get('email'):
            accounts = EmailAccount.objects.filter(email_address=options['email'])
            if not accounts.exists():
                self.stdout.write(self.style.ERROR(f"Email account not found: {options['email']}"))
                return
        else:
            accounts = EmailAccount.objects.all()
        
        self.stdout.write(f"Checking {accounts.count()} email account(s)...")
        self.stdout.write("=" * 70)
        
        verified_count = 0
        not_verified_count = 0
        error_count = 0
        
        for account in accounts:
            result = config_service.check_verification_status(account.email_address)
            
            if result['success']:
                if result['verified']:
                    status = self.style.SUCCESS("✓ VERIFIED")
                    verified_count += 1
                else:
                    status = self.style.WARNING(f"✗ NOT VERIFIED ({result['status']})")
                    not_verified_count += 1
                
                self.stdout.write(f"{account.email_address:40} {status}")
                
                # Update database if status changed
                if result['verified'] and not account.ses_verified:
                    account.ses_verified = True
                    account.save(update_fields=['ses_verified'])
                    self.stdout.write(f"  → Database updated")
                elif not result['verified'] and account.ses_verified:
                    account.ses_verified = False
                    account.save(update_fields=['ses_verified'])
                    self.stdout.write(f"  → Database updated")
            else:
                self.stdout.write(
                    self.style.ERROR(f"{account.email_address:40} ✗ ERROR")
                )
                self.stdout.write(f"  → {result.get('error')}")
                error_count += 1
        
        self.stdout.write("=" * 70)
        self.stdout.write(f"Summary:")
        self.stdout.write(f"  Verified: {verified_count}")
        self.stdout.write(f"  Not Verified: {not_verified_count}")
        self.stdout.write(f"  Errors: {error_count}")
        self.stdout.write("=" * 70)
        
        if not_verified_count > 0:
            self.stdout.write(self.style.WARNING(
                "\nNote: Users need to click the verification link in their email."
            ))
