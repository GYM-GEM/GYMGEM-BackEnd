# Running Django with WebSocket Support

## ⚠️ IMPORTANT: Django `runserver` Does NOT Support WebSockets!

The standard Django development server (`python manage.py runserver`) **only supports HTTP**, not WebSockets.

For WebSocket connections to work, you **MUST** use an ASGI server like **Daphne** or **Uvicorn**.

---

## Running the Server Correctly

### Option 1: Using Daphne (Recommended for Django Channels)

**Start the server:**
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
daphne -b 0.0.0.0 -p 8000 GymGem.asgi:application
```

**With auto-reload (development):**
```bash
daphne -b 0.0.0.0 -p 8000 --reload GymGem.asgi:application
```

**Expected output:**
```
2025-11-13 12:00:00 [INFO] Starting server at tcp:port=8000:interface=0.0.0.0
2025-11-13 12:00:00 [INFO] HTTP/2 support enabled
2025-11-13 12:00:00 [INFO] Configuring endpoint tcp:port=8000:interface=0.0.0.0
2025-11-13 12:00:00 [INFO] Listening on TCP address 0.0.0.0:8000
```

### Option 2: Using Uvicorn (Alternative)

**Install Uvicorn:**
```bash
pip install uvicorn[standard]
```

**Start the server:**
```bash
uvicorn GymGem.asgi:application --host 0.0.0.0 --port 8000 --reload
```

---

## WebSocket Connection URLs

### Development (Local)
```
ws://127.0.0.1:8000/ws/chat/{conversation_id}/?token={jwt_access_token}
```

### Production (HTTPS)
```
wss://yourdomain.com/ws/chat/{conversation_id}/?token={jwt_access_token}
```

**Note:** `wss://` (secure WebSocket) is required when your site uses HTTPS.

---

## Testing WebSocket Connection

### Your URL Example:
```
ws://127.0.0.1:8000/ws/chat/1/?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Breakdown:**
- **Protocol:** `ws://` (WebSocket)
- **Host:** `127.0.0.1:8000`
- **Path:** `/ws/chat/1/`
- **Conversation ID:** `1`
- **Authentication:** JWT token in query parameter

### Using Test Script

Run the provided test script:
```bash
python test_websocket.py
```

This will:
1. Decode and display JWT token information
2. Test WebSocket connection
3. Send test messages
4. Verify all WebSocket features

### Using Browser Console

Open browser DevTools console and paste:

```javascript
// Connect to WebSocket
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";
const ws = new WebSocket(`ws://127.0.0.1:8000/ws/chat/1/?token=${token}`);

// Connection opened
ws.onopen = () => {
    console.log('✅ Connected!');
    
    // Send a message
    ws.send(JSON.stringify({
        type: 'message',
        content: 'Hello from browser!'
    }));
};

// Listen for messages
ws.onmessage = (event) => {
    console.log('← Received:', JSON.parse(event.data));
};

// Connection closed
ws.onclose = (event) => {
    console.log('Disconnected:', event.code, event.reason);
};

// Error handler
ws.onerror = (error) => {
    console.error('❌ Error:', error);
};
```

### Using Postman/Insomnia

1. Create new WebSocket request
2. URL: `ws://127.0.0.1:8000/ws/chat/1/?token=YOUR_TOKEN`
3. Click "Connect"
4. Send JSON messages:
   ```json
   {
     "type": "message",
     "content": "Hello!"
   }
   ```

---

## Complete Development Setup

### Terminal Layout (4 terminals)

**Terminal 1 - Django Server (ASGI):**
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
daphne -b 0.0.0.0 -p 8000 GymGem.asgi:application
```

**Terminal 2 - Celery Worker:**
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
celery -A GymGem worker --loglevel=info
```

**Terminal 3 - Celery Beat:**
```bash
cd /home/feteha/GYMGEM-BackEnd
source venv/bin/activate
celery -A GymGem beat --loglevel=info
```

**Terminal 4 - Redis (if not running as service):**
```bash
redis-server
```

---

## Troubleshooting

### Issue: "Connection Refused"
**Cause:** Server not running or wrong port
**Solution:** 
- Start server with Daphne: `daphne GymGem.asgi:application`
- Check correct port (default 8000)

### Issue: "404 Not Found" when connecting to WebSocket
**Cause:** Using `runserver` instead of Daphne
**Solution:** Stop `runserver` and use Daphne

### Issue: "WebSocket connection to 'ws://...' failed"
**Cause:** Several possibilities
**Solutions:**
1. Server not running → Start Daphne
2. Using HTTP server → Use Daphne (ASGI)
3. Wrong URL → Check conversation ID exists
4. Invalid token → Get fresh token from login

### Issue: Connection closes immediately with code 4001/4003/4004
**Meanings:**
- **4001:** Authentication failed (invalid/expired token)
- **4003:** Not a participant in this conversation
- **4004:** Conversation does not exist

**Solutions:**
- **4001:** Login again to get fresh token
- **4003:** Start/join conversation first via REST API
- **4004:** Create conversation first or use correct ID

### Issue: Token expired
**Check expiration:**
```bash
python test_websocket.py
# Will show token expiration status
```

**Get new token:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"your_password"}'
```

---

## Production Deployment

### Using Daphne with Systemd

Create `/etc/systemd/system/gymgem-daphne.service`:

```ini
[Unit]
Description=GymGem Daphne ASGI Server
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=feteha
Group=feteha
WorkingDirectory=/home/feteha/GYMGEM-BackEnd
Environment="PATH=/home/feteha/GYMGEM-BackEnd/venv/bin"
ExecStart=/home/feteha/GYMGEM-BackEnd/venv/bin/daphne \
    -b 0.0.0.0 \
    -p 8000 \
    GymGem.asgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable gymgem-daphne
sudo systemctl start gymgem-daphne
sudo systemctl status gymgem-daphne
```

### Using Nginx as Reverse Proxy

Add to Nginx config:

```nginx
# WebSocket support
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

upstream gymgem_asgi {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # WebSocket connections
    location /ws/ {
        proxy_pass http://gymgem_asgi;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-lived connections
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Regular HTTP requests
    location / {
        proxy_pass http://gymgem_asgi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /home/feteha/GYMGEM-BackEnd/staticfiles/;
    }

    # Media files
    location /media/ {
        alias /home/feteha/GYMGEM-BackEnd/media/;
    }
}
```

**For HTTPS (SSL):**
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # WebSocket will use wss:// (secure WebSocket)
    location /ws/ {
        # ... same as above
    }
}
```

---

## Key Differences: runserver vs Daphne

| Feature | runserver | Daphne (ASGI) |
|---------|-----------|---------------|
| HTTP Support | ✅ Yes | ✅ Yes |
| WebSocket Support | ❌ No | ✅ Yes |
| Protocol | WSGI | ASGI |
| Production Ready | ❌ No | ✅ Yes |
| Auto-reload | ✅ Yes | ✅ Yes (with --reload) |
| Performance | Low | High |
| Concurrency | Limited | High |

---

## Summary

### ✅ DO (Correct Way)
```bash
# Start with Daphne (supports WebSockets)
daphne -b 0.0.0.0 -p 8000 GymGem.asgi:application
```

### ❌ DON'T (Wrong Way)
```bash
# DO NOT use runserver for WebSockets
python manage.py runserver  # ❌ WebSockets won't work!
```

### WebSocket URLs Will Work When:
1. ✅ Server running with Daphne/Uvicorn (ASGI)
2. ✅ Redis running (for Channel Layer)
3. ✅ Valid JWT token provided
4. ✅ User is participant in conversation
5. ✅ Conversation exists

---

## Quick Start Checklist

- [ ] Install Daphne: `pip install daphne`
- [ ] Start Redis: `sudo systemctl start redis-server`
- [ ] Start Daphne: `daphne GymGem.asgi:application`
- [ ] Get JWT token: Login via `/api/auth/login/`
- [ ] Test WebSocket: `python test_websocket.py`
- [ ] Connect client: `ws://127.0.0.1:8000/ws/chat/1/?token=YOUR_TOKEN`

🎉 **Your WebSocket API is now ready to use!**
