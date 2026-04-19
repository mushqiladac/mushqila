from django.core.management.base import BaseCommand
from webmail.models import EmailAccount
from webmail.services.ses_auto_config import SESAutoConfigService


class Command(BaseCommand):
    help = 'Setup SES and S3 for all existing email accounts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if already configured'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Setup specific email address only'
        )
    
    def handle(self, *args, **options):
        config_service = SESAutoConfigService()
        force = options.get('force', False)
        
        # Filter accounts
        if options.get('email'):
            accounts = EmailAccount.objects.filter(email_address=options['email'])
            if not accounts.exists():
                self.stdout.write(self.style.ERROR(f"Email account not found: {options['email']}"))
                return
        else:
            accounts = EmailAccount.objects.all()
        
        self.stdout.write(f"Setting up {accounts.count()} email account(s)...")
        self.stdout.write("=" * 70)
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for account in accounts:
            # Skip if already configured (unless force)
            if account.ses_verified and account.s3_bucket_name and not force:
                self.stdout.write(
                    f"⊘ {account.email_address:40} Already configured"
                )
                self.stdout.write(f"  Use --force to reconfigure")
                skip_count += 1
                continue
            
            self.stdout.write(f"\n⚙ Setting up {account.email_address}...")
            
            # Run setup
            result = config_service.setup_new_email_account(account.email_address)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {account.email_address:40} Setup complete")
                )
                
                # Show step details
                for step in result['steps']:
                    status = self.style.SUCCESS("✓") if step['success'] else self.style.ERROR("✗")
                    self.stdout.write(f"  {status} {step['step']}: {step['message']}")
                
                # Update account
                if result.get('bucket'):
                    account.s3_bucket_name = result['bucket']
                if result.get('inbox_prefix'):
                    account.s3_inbox_prefix = result['inbox_prefix']
                account.save(update_fields=['s3_bucket_name', 's3_inbox_prefix'])
                
                success_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ {account.email_address:40} Setup failed")
                )
                
                # Show error details
                for step in result['steps']:
                    if not step['success']:
                        self.stdout.write(
                            self.style.ERROR(f"  ✗ {step['step']}: {step['message']}")
                        )
                
                error_count += 1
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(f"Summary:")
        self.stdout.write(f"  Success: {success_count}")
        self.stdout.write(f"  Skipped: {skip_count}")
        self.stdout.write(f"  Errors: {error_count}")
        self.stdout.write("=" * 70)
        
        if success_count > 0:
            self.stdout.write(self.style.SUCCESS(
                "\nSetup complete! Users will receive verification emails."
            ))
            self.stdout.write(
                "Run 'python manage.py verify_email_accounts' to check verification status."
            )
