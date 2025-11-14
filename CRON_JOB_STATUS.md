# ✅ Celery Cron Job - Setup Verification Complete

## Summary
Your Celery periodic task (cron job) is **correctly established** and ready to use!

## What's Configured

### Task Details
- **Task Name**: `delete-old-messages-daily`
- **Task Function**: `chat.cron.delete_old_messages`
- **Schedule**: Daily at 2:00 AM UTC (`crontab: 0 2 * * *`)
- **Purpose**: Permanently deletes soft-deleted chat messages older than 7 days

### How It Works
```
User deletes message → is_deleted=True (soft delete, kept in DB)
                         ↓
                    7 days pass
                         ↓
            Celery Beat triggers at 2 AM UTC
                         ↓
          delete_old_messages task executes
                         ↓
        Message permanently deleted from DB
```

## Verification Results

### ✅ All Tests Passed
```
✓ PASSED: Celery Configuration
✓ PASSED: Celery Beat Schedule  
✓ PASSED: Task Import
✓ PASSED: Task Execution
```

### Configuration Files
1. **GymGem/settings.py** - Contains CELERY_BEAT_SCHEDULE
2. **GymGem/celery.py** - Celery app initialization
3. **GymGem/__init__.py** - Imports celery_app
4. **chat/cron.py** - Task definition with @shared_task

## How to Use

### Start Services (Development)

**Terminal 1 - Start Django Server:**
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
python manage.py runserver
```

**Terminal 2 - Start Celery Worker:**
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
celery -A GymGem worker --loglevel=info
```

**Terminal 3 - Start Celery Beat:**
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
celery -A GymGem beat --loglevel=info
```

### Expected Output

**When Beat triggers the task at 2 AM:**
```
[2025-11-13 02:00:00,000: INFO/Beat] Scheduler: Sending due task delete-old-messages-daily (chat.cron.delete_old_messages)
```

**Worker processes the task:**
```
[2025-11-13 02:00:00,123: INFO/MainProcess] Task chat.cron.delete_old_messages[abc-123] received
[2025-11-13 02:00:00,456: INFO/ForkPoolWorker-1] Task chat.cron.delete_old_messages[abc-123] succeeded in 0.333s
```

## Testing Commands

### Test Everything
```bash
python test_celery_setup.py
```

### Verify Beat Schedule
```bash
python verify_beat_schedule.py
```

### Manually Trigger Task (For Testing)
```bash
python manage.py shell
```
```python
from chat.cron import delete_old_messages
delete_old_messages()  # Run immediately
```

### Or trigger via Celery:
```python
from chat.cron import delete_old_messages
result = delete_old_messages.delay()  # Async execution
print(result.id)  # Task ID
```

## Changing the Schedule

Edit `GymGem/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'delete-old-messages-daily': {
        'task': 'chat.cron.delete_old_messages',
        
        # Choose one schedule:
        
        # Every 30 minutes
        'schedule': crontab(minute='*/30'),
        
        # Every 6 hours
        'schedule': crontab(minute=0, hour='*/6'),
        
        # Daily at 2 AM (current)
        'schedule': crontab(hour=2, minute=0),
        
        # Every Sunday at 3 AM
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
        
        # Twice a day (8 AM and 8 PM)
        'schedule': crontab(hour='8,20', minute=0),
    },
}
```

**After changing, restart Beat:**
```bash
# Stop Beat (Ctrl+C)
# Start again
celery -A GymGem beat --loglevel=info
```

## Monitoring

### Check if services are running
```bash
# Check worker
ps aux | grep "celery.*worker"

# Check beat
ps aux | grep "celery.*beat"
```

### View Celery logs
```bash
# Worker logs show task execution
celery -A GymGem worker --loglevel=debug

# Beat logs show when tasks are scheduled
celery -A GymGem beat --loglevel=debug
```

### Inspect active tasks
```bash
celery -A GymGem inspect active
celery -A GymGem inspect scheduled
celery -A GymGem inspect registered
```

## Troubleshooting

### Issue: Worker not starting
**Error**: `kombu.exceptions.SerializerNotInstalled: No encoder/decoder installed for [`
**Solution**: Already fixed! CELERY_ACCEPT_CONTENT is now a list `['json']` not a string

### Issue: Task not running at scheduled time
**Check:**
1. Is Redis running? `redis-cli ping` (should return PONG)
2. Is Celery Beat running? `ps aux | grep "celery.*beat"`
3. Is Celery Worker running? `ps aux | grep "celery.*worker"`

### Issue: Task fails during execution
**Check worker logs for error details**

## Files Created/Modified

### Created:
- ✅ `test_celery_setup.py` - Comprehensive test script
- ✅ `verify_beat_schedule.py` - Quick schedule verification
- ✅ `CELERY_CRON_SETUP.md` - Complete documentation

### Modified:
- ✅ `GymGem/settings.py` - Added CELERY_BEAT_SCHEDULE
- ✅ `chat/cron.py` - Already had the task (no changes needed)

## Next Steps

1. **Start Redis** (if not running):
   ```bash
   sudo systemctl start redis-server
   ```

2. **Start Celery Services**:
   - Worker (processes tasks)
   - Beat (schedules tasks)

3. **Monitor the first scheduled run** at 2:00 AM UTC

4. **For Production**: Set up Supervisor or Systemd (see CELERY_CRON_SETUP.md)

## Documentation Reference

- **Full Guide**: `CELERY_CRON_SETUP.md`
- **Application Flow**: `APPLICATION_FLOW.md` 
- **Redis Setup**: `REDIS_SETUP.md`

---

## ✨ Status: READY TO USE

Your cron job is properly configured and will automatically run every day at 2:00 AM UTC to clean up old deleted messages!

To start using it right now:
```bash
# Terminal 1
celery -A GymGem worker --loglevel=info

# Terminal 2  
celery -A GymGem beat --loglevel=info
```

🎉 **All systems operational!**
