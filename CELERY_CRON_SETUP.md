# Celery Periodic Tasks (Cron Jobs) Setup

## Overview
This document explains the Celery Beat configuration for periodic tasks in the GymGem application.

## Current Periodic Tasks

### 1. Delete Old Messages Task
**Task Name:** `delete-old-messages-daily`
**Task Path:** `chat.cron.delete_old_messages`
**Schedule:** Daily at 2:00 AM UTC
**Purpose:** Permanently deletes soft-deleted messages older than 7 days

#### How It Works
```python
# File: chat/cron.py
@shared_task
def delete_old_messages():
    threshold = timezone.now() - timedelta(days=7)
    Message.objects.filter(is_deleted=True, edited_at__lt=threshold).delete()
```

1. Calculates threshold: current time - 7 days
2. Queries for messages where:
   - `is_deleted = True` (soft-deleted)
   - `edited_at < threshold` (older than 7 days)
3. Permanently deletes those messages from database

## Configuration

### Celery Settings (`GymGem/settings.py`)
```python
# Basic Celery Configuration
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Schedule - Periodic Tasks
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'delete-old-messages-daily': {
        'task': 'chat.cron.delete_old_messages',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2:00 AM UTC
    },
}
```

### Celery App Configuration (`GymGem/celery.py`)
```python
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GymGem.settings')

app = Celery('GymGem')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### App Initialization (`GymGem/__init__.py`)
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

## Running the Services

### Prerequisites
1. **Redis Server** must be running:
   ```bash
   sudo systemctl start redis-server
   # OR
   bash install_redis.sh
   ```

2. **Virtual Environment** must be activated:
   ```bash
   source venv/bin/activate
   ```

### Start Celery Worker (Required)
The worker processes the actual tasks:
```bash
celery -A GymGem worker --loglevel=info
```

**What it does:**
- Connects to Redis broker
- Listens for tasks to execute
- Processes tasks when triggered

**Expected output:**
```
-------------- celery@hostname v5.x.x
--- ***** ----- 
-- ******* ---- Linux-x.x.x-x86_64-with-glibc2.xx
- *** --- * --- 
- ** ---------- [config]
- ** ---------- .> app:         GymGem:0x7f...
- ** ---------- .> transport:   redis://127.0.0.1:6379/0
- *** --- * --- .> results:     redis://127.0.0.1:6379/0
-- ******* ---- 
--- ***** ----- 
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . chat.cron.delete_old_messages

[2025-11-13 12:00:00,000: INFO/MainProcess] Connected to redis://127.0.0.1:6379/0
[2025-11-13 12:00:00,000: INFO/MainProcess] celery@hostname ready.
```

### Start Celery Beat (Scheduler - Required)
The beat scheduler triggers tasks at scheduled times:
```bash
celery -A GymGem beat --loglevel=info
```

**What it does:**
- Reads CELERY_BEAT_SCHEDULE from settings
- Monitors scheduled tasks
- Sends tasks to the worker at scheduled times

**Expected output:**
```
celery beat v5.x.x is starting.
__    -    ... __   -        _
LocalTime -> 2025-11-13 12:00:00
Configuration ->
    . broker -> redis://127.0.0.1:6379/0
    . loader -> celery.loaders.app.AppLoader
    . scheduler -> celery.beat.PersistentScheduler
    . db -> celerybeat-schedule
    . logfile -> [stderr]@%INFO
    . maxinterval -> 5.00 minutes (300s)

[2025-11-13 12:00:00,000: INFO/MainProcess] beat: Starting...
[2025-11-13 12:00:00,000: INFO/MainProcess] Scheduler: Sending due task delete-old-messages-daily (chat.cron.delete_old_messages)
```

### Run Both Services (Recommended for Development)
Use separate terminal windows:

**Terminal 1 - Worker:**
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
celery -A GymGem worker --loglevel=info
```

**Terminal 2 - Beat:**
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
celery -A GymGem beat --loglevel=info
```

## Testing

### Test All Configuration
Run the comprehensive test script:
```bash
python test_celery_setup.py
```

**This tests:**
- ✓ Celery configuration
- ✓ Beat schedule setup
- ✓ Task import
- ✓ Task execution

### Manually Trigger Task
To test the task immediately without waiting for schedule:
```bash
python manage.py shell
```

```python
from chat.cron import delete_old_messages
delete_old_messages()
# Or trigger via Celery
delete_old_messages.delay()
```

### Check Task Status
```bash
celery -A GymGem inspect active      # See running tasks
celery -A GymGem inspect scheduled   # See scheduled tasks
celery -A GymGem inspect registered  # See all registered tasks
```

## Schedule Examples

### Common Crontab Patterns
```python
# Every 30 minutes
'schedule': crontab(minute='*/30')

# Every hour
'schedule': crontab(minute=0)

# Every 6 hours
'schedule': crontab(minute=0, hour='*/6')

# Daily at 2:00 AM
'schedule': crontab(hour=2, minute=0)

# Every Sunday at 3:00 AM
'schedule': crontab(day_of_week=0, hour=3, minute=0)

# First day of month at midnight
'schedule': crontab(day_of_month=1, hour=0, minute=0)

# Weekdays at 9:00 AM
'schedule': crontab(day_of_week='1-5', hour=9, minute=0)
```

### Interval-Based Schedules
```python
from celery.schedules import schedule as interval_schedule

# Every 30 seconds
'schedule': interval_schedule(seconds=30)

# Every 10 minutes
'schedule': interval_schedule(minutes=10)

# Every 2 hours
'schedule': interval_schedule(hours=2)
```

## Adding New Periodic Tasks

### Step 1: Create Task Function
Create a new file or add to `chat/cron.py`:
```python
from celery import shared_task

@shared_task
def my_new_task():
    # Your task logic here
    print("Task executed!")
    return "Success"
```

### Step 2: Add to Beat Schedule
Edit `GymGem/settings.py`:
```python
CELERY_BEAT_SCHEDULE = {
    'delete-old-messages-daily': {
        'task': 'chat.cron.delete_old_messages',
        'schedule': crontab(hour=2, minute=0),
    },
    'my-new-task': {
        'task': 'chat.cron.my_new_task',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
```

### Step 3: Restart Services
```bash
# Stop current services (Ctrl+C in each terminal)
# Restart worker and beat
celery -A GymGem worker --loglevel=info
celery -A GymGem beat --loglevel=info
```

## Monitoring & Debugging

### View Beat Schedule Database
Celery Beat stores schedule state in `celerybeat-schedule`:
```bash
# This file is auto-generated and updated by Celery Beat
ls -lh celerybeat-schedule
```

### Common Issues

#### Issue: "No nodes replied within time constraint"
**Cause:** Worker is not running
**Solution:** Start the Celery worker

#### Issue: Task not executing at scheduled time
**Causes:**
1. Celery Beat not running
2. Redis connection issues
3. Task path incorrect in schedule

**Solutions:**
```bash
# 1. Check Beat is running
ps aux | grep "celery.*beat"

# 2. Check Redis is running
redis-cli ping  # Should return "PONG"

# 3. Verify task path
python manage.py shell -c "from chat.cron import delete_old_messages; print(delete_old_messages.name)"
```

#### Issue: Task executes but fails
**Solution:** Check worker logs for error details

### Enable More Verbose Logging
```bash
celery -A GymGem worker --loglevel=debug
celery -A GymGem beat --loglevel=debug
```

## Production Deployment

### Using Supervisor (Recommended)
Create `/etc/supervisor/conf.d/gymgem-celery.conf`:
```ini
[program:gymgem-celery-worker]
command=/home/feteha/GYMGEM-BackEnd/venv/bin/celery -A GymGem worker --loglevel=info
directory=/home/feteha/GYMGEM-BackEnd
user=feteha
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.err

[program:gymgem-celery-beat]
command=/home/feteha/GYMGEM-BackEnd/venv/bin/celery -A GymGem beat --loglevel=info
directory=/home/feteha/GYMGEM-BackEnd
user=feteha
numprocs=1
autostart=true
autorestart=true
startsecs=10
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat.err
```

Start services:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start gymgem-celery-worker
sudo supervisorctl start gymgem-celery-beat
```

### Using Systemd
Create `/etc/systemd/system/gymgem-celery-worker.service`:
```ini
[Unit]
Description=GymGem Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=feteha
Group=feteha
WorkingDirectory=/home/feteha/GYMGEM-BackEnd
Environment="PATH=/home/feteha/GYMGEM-BackEnd/venv/bin"
ExecStart=/home/feteha/GYMGEM-BackEnd/venv/bin/celery -A GymGem worker --detach --loglevel=info --logfile=/var/log/celery/worker.log
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/gymgem-celery-beat.service`:
```ini
[Unit]
Description=GymGem Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=feteha
Group=feteha
WorkingDirectory=/home/feteha/GYMGEM-BackEnd
Environment="PATH=/home/feteha/GYMGEM-BackEnd/venv/bin"
ExecStart=/home/feteha/GYMGEM-BackEnd/venv/bin/celery -A GymGem beat --loglevel=info --logfile=/var/log/celery/beat.log
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gymgem-celery-worker
sudo systemctl enable gymgem-celery-beat
sudo systemctl start gymgem-celery-worker
sudo systemctl start gymgem-celery-beat
```

## Summary

✅ **Configured:**
- Celery app initialization
- Redis broker connection
- Celery Beat schedule
- Delete old messages task (daily at 2 AM UTC)

✅ **Tested:**
- Configuration valid
- Task imports successfully
- Task executes without errors
- Beat schedule recognized

✅ **Ready to Use:**
1. Start Redis: `sudo systemctl start redis-server`
2. Start Worker: `celery -A GymGem worker --loglevel=info`
3. Start Beat: `celery -A GymGem beat --loglevel=info`

The cron job will now automatically clean up deleted messages every day at 2:00 AM UTC! 🎉
