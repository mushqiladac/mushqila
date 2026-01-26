import os
from celery import Celery
from decouple import config

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery app
app = Celery('mushqila')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Redis configuration
app.conf.broker_url = config('REDIS_URL', default='redis://localhost:6379/0')
app.conf.result_backend = config('REDIS_URL', default='redis://localhost:6379/0')

# Celery Beat schedule (for periodic tasks)
app.conf.beat_schedule = {
    # Example: Check flight status every hour
    'check-flight-status': {
        'task': 'flights.tasks.check_flight_status',
        'schedule': 3600.0,  # Every hour
    },
}

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
