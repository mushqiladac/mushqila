from celery import shared_task
from webmail.services.ses_receiving_service import SESReceivingService
import logging

logger = logging.getLogger(__name__)


@shared_task
def fetch_incoming_emails():
    """Celery task to fetch incoming emails from S3"""
    try:
        service = SESReceivingService()
        emails = service.fetch_new_emails()
        logger.info(f'Fetched {len(emails)} incoming emails')
        return f'Fetched {len(emails)} emails'
    except Exception as e:
        logger.error(f'Error fetching incoming emails: {str(e)}')
        return f'Error: {str(e)}'
