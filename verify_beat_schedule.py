#!/usr/bin/env python
"""Quick verification that Beat schedule is loaded correctly."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GymGem.settings')
django.setup()

from django.conf import settings
from celery import Celery

app = Celery('GymGem')
app.config_from_object('django.conf:settings', namespace='CELERY')

print("=" * 60)
print("CELERY BEAT SCHEDULE VERIFICATION")
print("=" * 60)

if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
    schedule = settings.CELERY_BEAT_SCHEDULE
    print(f"\n✓ Found {len(schedule)} scheduled task(s):\n")
    
    for name, config in schedule.items():
        print(f"Task: {name}")
        print(f"  • Path: {config['task']}")
        print(f"  • Schedule: {config['schedule']}")
        print()
    
    print("=" * 60)
    print("✅ Celery Beat is properly configured!")
    print("\nTo start the scheduler:")
    print("  celery -A GymGem beat --loglevel=info")
else:
    print("\n❌ CELERY_BEAT_SCHEDULE not found!")
