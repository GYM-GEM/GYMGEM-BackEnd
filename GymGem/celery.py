from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GymGem.settings')

app = Celery('GymGem')

app.config_from_object('django.conf:settings', namespace='CELERY')
# GymGem/celery.py

app.conf.beat_schedule = {
    'flush-expired-tokens': {
        'task': 'authenticationAndAuthorization.tasks.flush_expired_tokens',
        'schedule': crontab(hour=3, minute=0),  # Run daily at 3 AM
    },
}

app.autodiscover_tasks()
