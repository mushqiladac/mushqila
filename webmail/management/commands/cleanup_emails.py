from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from webmail.models import Email
from webmail.services import S3Service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cleanup old emails from trash and archive old emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--trash-days',
            type=int,
            default=30,
            help='Delete emails from trash older than X days (default: 30)'
        )
        parser.add_argument(
            '--archive-days',
            type=int,
            default=90,
            help='Archive emails older than X days (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        trash_days = options['trash_days']
        archive_days = options['archive_days']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('Starting email cleanup...'))
        
        # Delete old trash emails
        trash_cutoff = timezone.now() - timedelta(days=trash_days)
        trash_emails = Email.objects.filter(
            folder='trash',
            updated_at__lt=trash_cutoff
        )
        
        trash_count = trash_emails.count()
        self.stdout.write(f'Found {trash_count} trash emails to delete (older than {trash_days} days)')
        
        if not dry_run and trash_count > 0:
            deleted_count = 0
            for email in trash_emails:
                try:
                    # Delete from S3
                    if email.s3_key:
                        s3 = S3Service(bucket_name=email.account.s3_bucket_name)
                        s3.delete_email(email.s3_key)
                    
                    # Delete attachments from S3
                    for attachment in email.attachments.all():
                        if attachment.s3_key:
                            s3.delete_attachment(attachment.s3_key)
                    
                    # Delete from database
                    email.delete()
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f'Failed to delete email {email.id}: {str(e)}')
            
            self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} trash emails'))
        
        # Archive old emails
        archive_cutoff = timezone.now() - timedelta(days=archive_days)
        archive_emails = Email.objects.filter(
            folder__in=['inbox', 'sent'],
            received_at__lt=archive_cutoff
        ).exclude(is_starred=True)
        
        archive_count = archive_emails.count()
        self.stdout.write(f'Found {archive_count} emails to archive (older than {archive_days} days)')
        
        if not dry_run and archive_count > 0:
            archived_count = archive_emails.update(folder='archive')
            self.stdout.write(self.style.SUCCESS(f'Archived {archived_count} emails'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes made'))
        else:
            self.stdout.write(self.style.SUCCESS('Email cleanup completed!'))
