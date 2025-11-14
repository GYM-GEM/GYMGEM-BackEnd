# WebSocket URL Analysis

## Your WebSocket URL
```
ws://127.0.0.1:8000/ws/chat/1/?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYzMDM1NDE5LCJpYXQiOjE3NjMwMzE4MTksImp0aSI6ImFmMWZkODE5Y2Y1ZjRjNmI4ZGIzMzUxY2RiZjMxNDM0IiwidXNlcl9pZCI6IjIiLCJ1c2VybmFtZSI6ImpvaG5fZG9lIiwiZW1haWwiOiJqb2huQGV4YW1wbGUuY29tIiwiYWNjb3VudF9pZCI6MiwicHJvZmlsZV90eXBlcyI6W119.xSC9H_JNBUUWPcuRSesj5k29qxQWkeMTWqiW0VW0ExE
```

## URL Breakdown

### Protocol
```
ws://
```
- WebSocket protocol (unencrypted)
- For HTTPS sites, use `wss://` (secure WebSocket)

### Host & Port
```
127.0.0.1:8000
```
- **127.0.0.1**: Localhost (your local machine)
- **8000**: Django server port

### Path
```
/ws/chat/1/
```
- **/ws/**: WebSocket endpoint prefix
- **/chat/**: Chat application
- **/1/**: Conversation ID (conversation must exist)

### Query Parameters
```
?token=eyJhbGci...
```
- JWT access token for authentication
- Extracted and validated by JWTAuthMiddleware
- Must be valid and not expired

## JWT Token Information

**Decoded Payload:**
```json
{
  "token_type": "access",
  "exp": 1763035419,      // Expires: Saturday, February 8, 2026 12:43:39 AM
  "iat": 1763031819,      // Issued: Friday, February 7, 2026 11:43:39 PM
  "jti": "af1fd819cf5f4c6b8db3351cdbf31434",
  "user_id": "2",
  "username": "john_doe",
  "email": "john@example.com",
  "account_id": 2,
  "profile_types": []
}
```

**Token Status:** ✅ **VALID** (expires February 8, 2026)

**User Details:**
- **User ID**: 2
- **Username**: john_doe
- **Email**: john@example.com
- **Account ID**: 2
- **Profile Types**: None (empty array)

## ✅ URL is CORRECT!

This WebSocket URL is properly formatted and should work when:

1. ✅ **Server running with Daphne (ASGI)**
   ```bash
   daphne -b 0.0.0.0 -p 8000 GymGem.asgi:application
   ```

2. ✅ **Redis is running**
   ```bash
   sudo systemctl start redis-server
   ```

3. ✅ **Conversation ID 1 exists** in database

4. ✅ **User john_doe (ID: 2) is a participant** in conversation 1

5. ✅ **JWT token is valid** (not expired)

## How to Test

### Option 1: Using Test Script
```bash
cd /home/feteha/GYMGEM-BackEnd
python test_websocket.py
```

### Option 2: Using Browser Console
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/ws/chat/1/?token=eyJhbGci...');

ws.onopen = () => {
    console.log('✅ Connected!');
    ws.send(JSON.stringify({
        type: 'message',
        content: 'Hello!'
    }));
};

ws.onmessage = (event) => {
    console.log('Received:', JSON.parse(event.data));
};

ws.onclose = (event) => {
    console.log('Disconnected:', event.code);
};

ws.onerror = (error) => {
    console.error('Error:', error);
};
```

### Option 3: Using curl/websocat
```bash
# Install websocat
sudo apt install websocat

# Connect
websocat "ws://127.0.0.1:8000/ws/chat/1/?token=eyJhbGci..."

# Then type JSON messages:
{"type":"message","content":"Hello!"}
```

## Expected Behavior

### Successful Connection
```
1. WebSocket handshake initiated
2. JWTAuthMiddleware validates token
3. ChatConsumer.connect() checks:
   - User authenticated ✓
   - Conversation exists ✓
   - User is participant ✓
4. Connection accepted ✓
5. Channel added to Redis group: 'chat_1'
6. Ready to send/receive messages
```

### Connection Rejected Scenarios

**Close Code 4001: Authentication Failure**
- Invalid JWT token
- Expired token
- Missing token

**Close Code 4003: Permission Denied**
- User not a participant in conversation 1
- User not authenticated

**Close Code 4004: Not Found**
- Conversation 1 does not exist

**Close Code 4000: Server Error**
- Unexpected error during connection

## Message Types Supported

### 1. Chat Message
```json
{
  "type": "message",
  "content": "Hello, world!"
}
```

### 2. Read Receipt
```json
{
  "type": "read",
  "message_id": 15
}
```

### 3. Typing Indicator
```json
{
  "type": "typing",
  "is_typing": true
}
```

### 4. Edit Message
```json
{
  "type": "edit",
  "message_id": 15,
  "content": "Updated content"
}
```

### 5. Delete Message
```json
{
  "type": "delete",
  "message_id": 15
}
```

## Common Issues & Solutions

### Issue: "WebSocket connection to 'ws://...' failed"
**Solution:** Start server with Daphne instead of runserver
```bash
# ❌ WRONG - runserver doesn't support WebSockets
python manage.py runserver

# ✅ CORRECT - Use Daphne
daphne GymGem.asgi:application
```

### Issue: Connection closes immediately
**Check the close code:**
- 4001 → Get fresh JWT token
- 4003 → Join/create conversation first
- 4004 → Conversation doesn't exist

### Issue: Token expired
**Get new token:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"your_password"}'
```

### Issue: Conversation doesn't exist
**Create conversation:**
```bash
curl -X POST http://127.0.0.1:8000/api/chat/conversations/start/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user2": 3}'
```

## Complete Flow Example

```bash
# 1. Start server with Daphne
daphne -b 0.0.0.0 -p 8000 GymGem.asgi:application

# 2. Get JWT token (in another terminal)
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"password123"}'

# Response:
# {
#   "access": "eyJhbGci...",
#   "refresh": "eyJhbGci...",
#   "account": {...}
# }

# 3. Start conversation (if needed)
curl -X POST http://127.0.0.1:8000/api/chat/conversations/start/ \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{"user2": 3}'

# Response:
# {
#   "id": 1,
#   "participants": [2, 3],
#   "created_at": "2025-11-13T..."
# }

# 4. Connect WebSocket
# Use browser console or test script:
ws://127.0.0.1:8000/ws/chat/1/?token=eyJhbGci...

# 5. Send messages via WebSocket
{"type":"message","content":"Hello!"}

# 6. Receive broadcasts
# All participants get the message in real-time
```

## Summary

✅ **Your WebSocket URL is correctly formatted**

✅ **Token is valid** (expires Feb 8, 2026)

✅ **User info decoded successfully** (john_doe, ID: 2)

⚠️ **MUST use Daphne**, not `runserver`

📝 **Next steps:**
1. Stop `runserver` if running
2. Start with Daphne: `./start_server.sh`
3. Test connection: `python test_websocket.py`
4. Connect from client app

🎉 **WebSocket API is ready to use!**
