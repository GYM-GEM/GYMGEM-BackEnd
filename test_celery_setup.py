#!/usr/bin/env python
"""
Test script to verify Celery and Celery Beat are configured correctly.
Run this before starting the worker and beat services.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GymGem.settings')
django.setup()

from django.conf import settings
from chat.cron import delete_old_messages

def test_celery_configuration():
    """Test basic Celery configuration"""
    print("=" * 60)
    print("CELERY CONFIGURATION TEST")
    print("=" * 60)
    
    # Check broker
    print(f"\n✓ Broker URL: {settings.CELERY_BROKER_URL}")
    print(f"✓ Result Backend: {settings.CELERY_RESULT_BACKEND}")
    print(f"✓ Accept Content: {settings.CELERY_ACCEPT_CONTENT}")
    print(f"✓ Task Serializer: {settings.CELERY_TASK_SERIALIZER}")
    print(f"✓ Result Serializer: {settings.CELERY_RESULT_SERIALIZER}")
    print(f"✓ Timezone: {settings.CELERY_TIMEZONE}")
    
    return True

def test_celery_beat_schedule():
    """Test Celery Beat schedule configuration"""
    print("\n" + "=" * 60)
    print("CELERY BEAT SCHEDULE TEST")
    print("=" * 60)
    
    if not hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
        print("\n❌ CELERY_BEAT_SCHEDULE not found in settings!")
        return False
    
    beat_schedule = settings.CELERY_BEAT_SCHEDULE
    
    if not beat_schedule:
        print("\n❌ CELERY_BEAT_SCHEDULE is empty!")
        return False
    
    print(f"\n✓ Found {len(beat_schedule)} scheduled task(s):")
    
    for task_name, task_config in beat_schedule.items():
        print(f"\n  Task Name: {task_name}")
        print(f"  Task Path: {task_config['task']}")
        print(f"  Schedule: {task_config['schedule']}")
        print(f"  Description: Runs at {task_config['schedule']}")
    
    return True

def test_task_import():
    """Test if the task can be imported"""
    print("\n" + "=" * 60)
    print("TASK IMPORT TEST")
    print("=" * 60)
    
    try:
        print(f"\n✓ Task imported successfully: {delete_old_messages}")
        print(f"✓ Task name: {delete_old_messages.name}")
        return True
    except Exception as e:
        print(f"\n❌ Failed to import task: {e}")
        return False

def test_task_execution():
    """Test if the task can be executed"""
    print("\n" + "=" * 60)
    print("TASK EXECUTION TEST")
    print("=" * 60)
    
    try:
        print("\n⏳ Running delete_old_messages task...")
        result = delete_old_messages()
        print(f"✓ Task executed successfully!")
        print(f"  Return value: {result}")
        
        # Check if there are any messages to clean up
        from chat.models import Message
        from django.utils import timezone
        from datetime import timedelta
        
        threshold = timezone.now() - timedelta(days=7)
        old_deleted_count = Message.objects.filter(is_deleted=True, edited_at__lt=threshold).count()
        
        if old_deleted_count > 0:
            print(f"  Note: Found {old_deleted_count} old deleted messages that will be cleaned up")
        else:
            print(f"  Note: No old deleted messages to clean up (this is normal)")
        
        return True
    except Exception as e:
        print(f"\n❌ Task execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n🚀 Starting Celery Setup Verification...")
    print("=" * 60)
    
    tests = [
        ("Celery Configuration", test_celery_configuration),
        ("Celery Beat Schedule", test_celery_beat_schedule),
        ("Task Import", test_task_import),
        ("Task Execution", test_task_execution),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        print("\nYou can now start the services:")
        print("  1. Start Celery Worker:  celery -A GymGem worker --loglevel=info")
        print("  2. Start Celery Beat:    celery -A GymGem beat --loglevel=info")
        print("\nThe task 'delete_old_messages' will run daily at 2:00 AM UTC")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("\nPlease review the errors above and fix the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
