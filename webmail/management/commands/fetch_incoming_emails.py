from django.core.management.base import BaseCommand
from webmail.services.ses_receiving_service import SESReceivingService


class Command(BaseCommand):
    help = 'Fetch incoming emails from AWS SES/S3'

    def handle(self, *args, **options):
        self.stdout.write('Fetching incoming emails from S3...')
        
        service = SESReceivingService()
        emails = service.fetch_new_emails()
        
        if emails:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Successfully fetched {len(emails)} new email(s)')
            )
            for email_data in emails:
                self.stdout.write(f"  - {email_data['subject']} from {email_data['from_address']}")
        else:
            self.stdout.write(
                self.style.WARNING('No new emails found')
            )
