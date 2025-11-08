# Redis Setup Guide for Django Channels

## What is Redis?
Redis is an in-memory data store used as a message broker for Django Channels. It enables:
- **Real-time WebSocket communication** across multiple server instances
- **Horizontal scaling** - run multiple Django servers behind a load balancer
- **Message persistence** - messages survive server restarts
- **Better performance** than InMemoryChannelLayer

## Installation Steps

### 1. Install Redis Server (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install redis-server
```

### 2. Start Redis Service
```bash
# Start Redis
sudo systemctl start redis-server

# Enable Redis to start on boot
sudo systemctl enable redis-server

# Check Redis status
sudo systemctl status redis-server
```

### 3. Verify Redis is Running
```bash
# Should return "PONG"
redis-cli ping
```

### 4. Test with Django
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GymGem.settings')
import django
django.setup()
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()
async_to_sync(channel_layer.send)('test', {'type': 'test', 'text': 'Hello'})
print('✅ Redis is working!')
"
```

## Configuration

### Current Settings (settings.py)
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")],
            "capacity": 1500,  # Max messages before dropping
            "expiry": 10,      # Message expiry in seconds
        },
    }
}
```

### Environment Variables (.env)
```bash
# Default local Redis
REDIS_URL=redis://127.0.0.1:6379/0

# Redis with password
# REDIS_URL=redis://:yourpassword@127.0.0.1:6379/0

# Redis Cloud/Managed service
# REDIS_URL=redis://username:password@hostname:port/database
```

## Redis Configuration Options

### Basic Redis Security (Optional)
Edit `/etc/redis/redis.conf`:
```bash
# Set password
requirepass your_strong_password_here

# Bind to localhost only (more secure)
bind 127.0.0.1 ::1

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

After changes:
```bash
sudo systemctl restart redis-server
```

### Using Redis with Password
Update `.env`:
```bash
REDIS_URL=redis://:your_strong_password_here@127.0.0.1:6379/0
```

## Production Considerations

### 1. Redis Persistence
Redis can persist data to disk. In `/etc/redis/redis.conf`:
```
# Save to disk every 60 seconds if at least 1 key changed
save 60 1

# RDB persistence
dbfilename dump.rdb
dir /var/lib/redis
```

### 2. Memory Limits
Set max memory in `/etc/redis/redis.conf`:
```
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 3. Monitoring
```bash
# Monitor Redis in real-time
redis-cli monitor

# Check memory usage
redis-cli info memory

# Check connected clients
redis-cli client list
```

### 4. Redis Cloud Services (Production)
For production, consider managed Redis services:
- **AWS ElastiCache** - `redis://your-cluster.cache.amazonaws.com:6379`
- **Redis Cloud** - `redis://username:password@host:port/db`
- **Azure Cache for Redis** - `redis://name.redis.cache.windows.net:6379`
- **DigitalOcean Managed Redis** - Connection string provided

## Fallback to InMemoryChannelLayer

If Redis is unavailable (development/testing), switch back in `settings.py`:
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}
```

**Note**: InMemoryChannelLayer:
- ✅ Works without external services
- ✅ Good for development/testing
- ❌ Single server only (no scaling)
- ❌ Messages lost on restart
- ❌ Not for production

## Testing Redis with Chat Service

### 1. Start Redis
```bash
sudo systemctl start redis-server
```

### 2. Run Django Server
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
python manage.py runserver
```

### 3. Test WebSocket Connection
The chat service will now use Redis for:
- Real-time message broadcasting
- Typing indicators
- Read receipts
- Message edit/delete notifications

All WebSocket messages are now routed through Redis, enabling:
- Multiple Django servers
- Load balancing
- Better reliability

## Troubleshooting

### Redis won't start
```bash
# Check logs
sudo journalctl -u redis-server -n 50

# Check config syntax
redis-server /etc/redis/redis.conf --test-memory 1
```

### Connection refused
```bash
# Is Redis running?
sudo systemctl status redis-server

# Is Redis listening?
sudo netstat -tlnp | grep 6379

# Can you connect locally?
redis-cli ping
```

### Permission denied
```bash
# Check Redis user permissions
ls -la /var/lib/redis
sudo chown redis:redis /var/lib/redis -R
```

## Quick Install Script

Run this to install and configure Redis:
```bash
#!/bin/bash
sudo apt update
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server
redis-cli ping
echo "✅ Redis installed and running!"
```

## Next Steps

1. **Install Redis** (see above)
2. **Verify connection** works
3. **Test chat service** with WebSocket
4. **Monitor Redis** in production
5. Consider **Redis Cloud** for production deployment
