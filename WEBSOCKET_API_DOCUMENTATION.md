# WebSocket API Documentation

## Overview

The GYMGEM backend provides two main WebSocket endpoints for real-time communication:

1. **Chat WebSocket** - Real-time messaging between users
2. **Interactive Sessions WebSocket** - WebRTC signaling for trainer-trainee sessions

---

## Chat WebSocket

### Connection Details

**Endpoint:** `ws://[host]/ws/chat/[conversation_id]/`

**Query Parameters:**
- `token` (required): JWT authentication token

**Example:**
```javascript
const token = "eyJ0eXAiOiJKV1QiLCJhbGc...";
const conversationId = 42;
const url = `ws://localhost:8000/ws/chat/${conversationId}/?token=${token}`;
const socket = new WebSocket(url);
```

### Authentication

- Token must be valid JWT token from login endpoint
- User making connection must be a participant in the conversation
- Connection rejected with code 4001 if authentication fails
- Connection rejected with code 4002 if user not in conversation

### Message Protocol

#### Outgoing Messages (Client → Server)

**1. Send Chat Message**
```json
{
  "type": "chat_message",
  "content": "Hello world",
  "file": null
}
```
- `content` (string, required): Message text
- `file` (File, optional): File attachment for media

**2. Mark Message as Read**
```json
{
  "type": "read_receipt",
  "message_id": 123
}
```

**3. Send Typing Indicator**
```json
{
  "type": "typing_indicator"
}
```
Send this repeatedly while user is actively typing.

**4. Edit Message**
```json
{
  "type": "edit_message",
  "message_id": 123,
  "new_content": "Updated message text"
}
```
- Only the message sender can edit
- Original message must exist in conversation

**5. Delete Message**
```json
{
  "type": "delete_message",
  "message_id": 123
}
```
- Only the message sender can delete
- Deletion is soft-delete (records kept for history)

#### Incoming Messages (Server → Client)

**1. Chat Message Received**
```json
{
  "type": "chat_message",
  "message_id": 123,
  "sender_id": 5,
  "sender_username": "john_trainer",
  "content": "Great workout today!",
  "created_at": "2026-01-04T14:30:00Z",
  "has_attachment": false
}
```

**2. Read Receipt Notification**
```json
{
  "type": "read_receipt",
  "message_id": 123,
  "read_by_profile_id": 5,
  "read_at": "2026-01-04T14:32:00Z"
}
```

**3. Typing Indicator**
```json
{
  "type": "typing_indicator",
  "profile_id": 5,
  "username": "john_trainer"
}
```

**4. Message Edited**
```json
{
  "type": "message_edited",
  "message_id": 123,
  "new_content": "Updated message text",
  "edited_at": "2026-01-04T14:35:00Z"
}
```

**5. Message Deleted**
```json
{
  "type": "message_deleted",
  "message_id": 123
}
```

**6. Error Response**
```json
{
  "type": "error",
  "message": "You do not have permission to edit this message"
}
```

### Heartbeat Mechanism

The server sends heartbeat pings every 30 seconds to keep the connection alive.

**Heartbeat Message:**
```json
{
  "type": "ping"
}
```

**Client Response:**
```json
{
  "type": "pong"
}
```

### Connection Lifecycle

```
1. Client connects with token and conversation_id
   ↓
2. Server validates authentication
   ↓
3. Server validates user is conversation participant
   ↓
4. Connection established (WebSocket OPEN)
   ↓
5. Exchange messages, typing indicators, read receipts
   ↓
6. Server sends heartbeat ping every 30 seconds
   ↓
7. Client can disconnect or server closes connection on timeout
```

### Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 4001 | Authentication failed | Re-authenticate and reconnect |
| 4002 | User not in conversation | Check conversation ID |
| 4003 | Conversation not found | Verify conversation exists |
| 4004 | Invalid message format | Check message structure |
| 1000 | Normal closure | Connection closed normally |
| 1001 | Going away | Server shutting down |
| 1002 | Protocol error | Invalid message protocol |
| 1006 | Abnormal closure | Network error - reconnect |

### Example Implementation (JavaScript)

```javascript
class ChatSocket {
  constructor(conversationId, token) {
    this.conversationId = conversationId;
    this.token = token;
    this.socket = null;
  }

  connect() {
    const url = `ws://localhost:8000/ws/chat/${this.conversationId}/?token=${this.token}`;
    this.socket = new WebSocket(url);

    this.socket.onopen = (e) => {
      console.log('Chat connected');
      this.setupHeartbeat();
    };

    this.socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      this.handleMessage(data);
    };

    this.socket.onerror = (error) => {
      console.error('Chat error:', error);
    };

    this.socket.onclose = (e) => {
      console.log('Chat disconnected');
      this.clearHeartbeat();
    };
  }

  sendMessage(content) {
    this.socket.send(JSON.stringify({
      type: 'chat_message',
      content: content,
      file: null
    }));
  }

  handleMessage(data) {
    switch (data.type) {
      case 'chat_message':
        console.log(`${data.sender_username}: ${data.content}`);
        break;
      case 'typing_indicator':
        console.log(`${data.username} is typing...`);
        break;
      case 'error':
        console.error(data.message);
        break;
    }
  }

  setupHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: 'pong' }));
      }
    }, 25000); // 25 seconds (server sends every 30)
  }

  clearHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
    }
  }
}

// Usage
const chat = new ChatSocket(42, 'your-jwt-token');
chat.connect();

// Send message
chat.sendMessage('Hello world!');

// Cleanup
chat.disconnect();
```

---

## Interactive Sessions WebSocket

### Connection Details

**Endpoint:** `ws://[host]/ws/interactive_sessions/[session_id]/`

**Query Parameters:**
- `token` (required): JWT authentication token

**Example:**
```javascript
const token = "eyJ0eXAiOiJKV1QiLCJhbGc...";
const sessionId = 15;
const url = `ws://localhost:8000/ws/interactive_sessions/${sessionId}/?token=${token}`;
const socket = new WebSocket(url);
```

### Authentication

- Token must be valid JWT token from login endpoint
- User making connection must be the trainer or trainee in the session
- Session must be in "accepted" or "scheduled" status
- Connection rejected if authentication fails

### Message Protocol

#### Outgoing Messages (Client → Server)

**1. Join Session**
```json
{
  "type": "join",
  "role": "trainer"
}
```
- `role` (string, required): "trainer" or "trainee"
- Must be sent immediately after connection
- Only one of each role allowed per session

**2. Leave Session**
```json
{
  "type": "leave"
}
```

**3. WebRTC Offer (Trainee initiates)**
```json
{
  "type": "webrtc",
  "event_type": "OFFER",
  "payload": {
    "sdp": "v=0\r\no=- 4611731400430051336..."
  }
}
```

**4. WebRTC Answer (Trainer responds)**
```json
{
  "type": "webrtc",
  "event_type": "ANSWER",
  "payload": {
    "sdp": "v=0\r\no=- 7082901984654957937..."
  }
}
```

**5. ICE Candidate**
```json
{
  "type": "webrtc",
  "event_type": "ICE_CANDIDATE",
  "payload": {
    "candidate": "candidate:842163049...",
    "sdpMLineIndex": 0,
    "sdpMid": "0"
  }
}
```

**6. Direct Message**
```json
{
  "type": "direct_message",
  "payload": {
    "message": "Can you hear me?"
  }
}
```

#### Incoming Messages (Server → Client)

**1. Join Acknowledged**
```json
{
  "type": "join_acknowledged",
  "profile_id": 5,
  "role": "trainer",
  "joined_at": "2026-01-04T14:30:00Z"
}
```

**2. Participant Joined**
```json
{
  "type": "participant_joined",
  "profile_id": 10,
  "role": "trainee",
  "joined_at": "2026-01-04T14:31:00Z"
}
```

**3. Participant Left**
```json
{
  "type": "participant_left",
  "profile_id": 10,
  "role": "trainee"
}
```

**4. WebRTC Signaling (relayed from peer)**
```json
{
  "type": "direct_webrtc",
  "event_type": "OFFER",
  "from_role": "trainee",
  "payload": {
    "sdp": "v=0\r\no=- 4611731400430051336..."
  }
}
```

**5. Direct Message**
```json
{
  "type": "direct_message",
  "from_role": "trainer",
  "payload": {
    "message": "Yes, I can hear you!"
  }
}
```

**6. Session Forced Disconnect**
```json
{
  "type": "force_disconnect",
  "reason": "timeout",
  "message": "Session ended after 40 minutes"
}
```

**7. Error Response**
```json
{
  "type": "error",
  "message": "Trainer already joined this session"
}
```

### Session Timing

| Setting | Value | Purpose |
|---------|-------|---------|
| SESSION_TTL | 40 minutes | Maximum session duration |
| PRESENCE_TTL | 41 minutes | Presence data retention |
| MIN_PRESENCE_SECONDS | 10 minutes | Minimum for financial operations |
| HEARTBEAT_INTERVAL | 30 seconds | Connection keepalive |

### Automatic Session Finalization

- Session automatically ends after 40 minutes regardless of activity
- Financial transactions processed if both participants were present 10+ minutes
- Participants notified before disconnect via `force_disconnect` message
- Session status updated to "completed" in database

### Connection Lifecycle

```
1. Client connects with token and session_id
   ↓
2. Server validates authentication and session membership
   ↓
3. Client sends {"type": "join", "role": "..."}
   ↓
4. Server broadcasts join notification to other participant
   ↓
5. When both joined: WebRTC signaling can begin
   ↓
6. Peer 1 sends OFFER, Peer 2 sends ANSWER, ICE candidates exchanged
   ↓
7. Media/video connection established
   ↓
8. Server sends heartbeat ping every 30 seconds
   ↓
9. Either participant sends LEAVE or 40-minute timeout
   ↓
10. Server finalizes session and processes payments (if eligible)
```

### WebRTC Signaling Flow

```
TRAINEE                          SERVER                          TRAINER
   |                               |                               |
   | 1. Connect ws                 |                               |
   |------>                        |                               |
   | 2. Join (trainee)             |                               |
   |------>                        |                               |
   |                         Wait for trainer                      |
   |                               | 3. Connect ws                 |
   |                               |                      <--------
   |                               | 4. Join (trainer)             |
   |                               |                      <--------
   |                    broadcast join_ack                         |
   | 5. join_ack                   |                               |
   |<------                        | 5. join_ack                   |
   |<------------------------------------------------               |
   |                    broadcast participant_joined               |
   | 6. participant_joined (trainer) |                             |
   |<------                        | 6. participant_joined (trainee)|
   |                               |                      <--------
   |                               |                               |
   | 7. OFFER (SDP)                |                               |
   |------>                        | 7. direct_webrtc OFFER        |
   |                               |                      ----->
   |                               |                   8. ANSWER (SDP)
   | 8. ANSWER (via direct_webrtc) |                      <---
   |<------                        |                               |
   |                               |                               |
   | 9. ICE candidates             |                               |
   |------>                        | 9. direct_webrtc ICE          |
   |                               |                      ----->
   |                   ICE candidates                      <---
   |<------                        |                               |
   |                               |                               |
   | ====== Media connection established ======                   |
   | Can exchange audio/video                                      |
   | Can send direct_message if needed                             |
   |                               |                               |
   | 10. After 40 minutes or leave |                               |
   | Leave (or timeout)            |                               |
   |------>                        | force_disconnect              |
   |                               |                      ----->
   | force_disconnect              |                               |
   |<------                        |                               |
   |                    Session finalized, payments processed      |
```

### Example Implementation (JavaScript with WebRTC)

```javascript
class InteractiveSessionSocket {
  constructor(sessionId, token, isTrainer) {
    this.sessionId = sessionId;
    this.token = token;
    this.isTrainer = isTrainer;
    this.socket = null;
    this.peerConnection = null;
    this.localStream = null;
  }

  async connect() {
    const url = `ws://localhost:8000/ws/interactive_sessions/${this.sessionId}/?token=${this.token}`;
    this.socket = new WebSocket(url);

    this.socket.onopen = async (e) => {
      console.log('Session connected');
      
      // Setup WebRTC before joining
      await this.setupWebRTC();
      
      // Join session
      this.socket.send(JSON.stringify({
        type: 'join',
        role: this.isTrainer ? 'trainer' : 'trainee'
      }));
      
      this.setupHeartbeat();
    };

    this.socket.onmessage = async (e) => {
      const data = JSON.parse(e.data);
      await this.handleMessage(data);
    };

    this.socket.onerror = (error) => {
      console.error('Session error:', error);
    };

    this.socket.onclose = (e) => {
      console.log('Session disconnected');
      this.cleanup();
    };
  }

  async setupWebRTC() {
    // Create peer connection
    this.peerConnection = new RTCPeerConnection({
      iceServers: [
        { urls: ['stun:stun.l.google.com:19302'] }
      ]
    });

    // Get local media
    this.localStream = await navigator.mediaDevices.getUserMedia({
      audio: true,
      video: { width: 1280, height: 720 }
    });

    // Add tracks to peer connection
    this.localStream.getTracks().forEach(track => {
      this.peerConnection.addTrack(track, this.localStream);
    });

    // Handle ICE candidates
    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        this.socket.send(JSON.stringify({
          type: 'webrtc',
          event_type: 'ICE_CANDIDATE',
          payload: {
            candidate: event.candidate.candidate,
            sdpMLineIndex: event.candidate.sdpMLineIndex,
            sdpMid: event.candidate.sdpMid
          }
        }));
      }
    };

    // Handle remote track
    this.peerConnection.ontrack = (event) => {
      console.log('Remote track received:', event.track.kind);
      // Add to video element
      const video = document.getElementById('remote-video');
      if (video.srcObject !== event.streams[0]) {
        video.srcObject = event.streams[0];
      }
    };

    // Add local stream to video element
    const localVideo = document.getElementById('local-video');
    localVideo.srcObject = this.localStream;
  }

  async handleMessage(data) {
    switch (data.type) {
      case 'join_acknowledged':
        console.log(`${data.role} joined session`);
        break;

      case 'participant_joined':
        console.log(`${data.role} joined - can start signaling`);
        if (!this.isTrainer) {
          await this.sendOffer();
        }
        break;

      case 'direct_webrtc':
        await this.handleWebRTC(data.event_type, data.payload);
        break;

      case 'direct_message':
        console.log(`${data.from_role}: ${data.payload.message}`);
        break;

      case 'force_disconnect':
        console.log(`Session ended: ${data.message}`);
        this.cleanup();
        break;

      case 'error':
        console.error(data.message);
        break;
    }
  }

  async handleWebRTC(eventType, payload) {
    switch (eventType) {
      case 'OFFER':
        const offer = new RTCSessionDescription({
          type: 'offer',
          sdp: payload.sdp
        });
        await this.peerConnection.setRemoteDescription(offer);
        await this.sendAnswer();
        break;

      case 'ANSWER':
        const answer = new RTCSessionDescription({
          type: 'answer',
          sdp: payload.sdp
        });
        await this.peerConnection.setRemoteDescription(answer);
        break;

      case 'ICE_CANDIDATE':
        const candidate = new RTCIceCandidate({
          candidate: payload.candidate,
          sdpMLineIndex: payload.sdpMLineIndex,
          sdpMid: payload.sdpMid
        });
        await this.peerConnection.addIceCandidate(candidate);
        break;
    }
  }

  async sendOffer() {
    const offer = await this.peerConnection.createOffer();
    await this.peerConnection.setLocalDescription(offer);

    this.socket.send(JSON.stringify({
      type: 'webrtc',
      event_type: 'OFFER',
      payload: {
        sdp: offer.sdp
      }
    }));
  }

  async sendAnswer() {
    const answer = await this.peerConnection.createAnswer();
    await this.peerConnection.setLocalDescription(answer);

    this.socket.send(JSON.stringify({
      type: 'webrtc',
      event_type: 'ANSWER',
      payload: {
        sdp: answer.sdp
      }
    }));
  }

  sendMessage(text) {
    this.socket.send(JSON.stringify({
      type: 'direct_message',
      payload: {
        message: text
      }
    }));
  }

  leave() {
    this.socket.send(JSON.stringify({
      type: 'leave'
    }));
  }

  setupHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: 'pong' }));
      }
    }, 25000); // 25 seconds (server sends every 30)
  }

  cleanup() {
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
    if (this.localStream) {
      this.localStream.getTracks().forEach(t => t.stop());
    }
    if (this.peerConnection) {
      this.peerConnection.close();
    }
    if (this.socket) {
      this.socket.close();
    }
  }
}

// Usage
const session = new InteractiveSessionSocket(15, 'your-jwt-token', false); // false = trainee
await session.connect();

// Send message if needed
session.sendMessage("Can you hear me?");

// End session
session.leave();
```

---

## Best Practices

### General Guidelines

1. **Always validate token before connecting** - Ensure token is fresh and valid
2. **Implement automatic reconnection** - Networks can drop unexpectedly
3. **Handle heartbeat timeouts** - If no heartbeat received for 60 seconds, reconnect
4. **Use exponential backoff for reconnection** - Start with 1s, max 30s
5. **Clean up resources on disconnect** - Stop all timers, close streams
6. **Log all messages during development** - Helps debug connection issues
7. **Test with slow networks** - Use browser DevTools to throttle connection

### Connection Resilience

```javascript
class ResilientSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.reconnectDelay = options.reconnectDelay || 1000;
    this.maxReconnectDelay = options.maxReconnectDelay || 30000;
    this.messageQueue = [];
    this.isConnecting = false;
  }

  connect() {
    if (this.isConnecting) return;
    this.isConnecting = true;

    try {
      this.socket = new WebSocket(this.url);
      
      this.socket.onopen = () => {
        console.log('Connected');
        this.isConnecting = false;
        this.reconnectDelay = 1000;
        this.flushQueue();
      };

      this.socket.onclose = () => {
        this.isConnecting = false;
        this.reconnect();
      };

      this.socket.onerror = (error) => {
        console.error('Socket error:', error);
        this.isConnecting = false;
      };
    } catch (error) {
      console.error('Connection error:', error);
      this.isConnecting = false;
      this.reconnect();
    }
  }

  reconnect() {
    console.log(`Reconnecting in ${this.reconnectDelay}ms`);
    setTimeout(() => {
      this.connect();
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2,
        this.maxReconnectDelay
      );
    }, this.reconnectDelay);
  }

  send(message) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(message);
    } else {
      this.messageQueue.push(message);
    }
  }

  flushQueue() {
    while (this.messageQueue.length) {
      const message = this.messageQueue.shift();
      this.socket.send(message);
    }
  }
}
```

### Error Recovery

- Implement exponential backoff for reconnection attempts
- Queue messages while disconnected
- Resend critical messages after reconnection
- Notify user of connection status changes
- Log detailed error information for debugging

---

## Troubleshooting

### Connection Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| 403 Forbidden | Invalid token or expired | Get new token and reconnect |
| 404 Not Found | Invalid conversation/session ID | Check ID is correct |
| Connection timeout | Network latency or firewall | Check network, increase timeout |
| Messages not delivered | Stale connection | Implement heartbeat |
| Memory leak | Not cleaning up on disconnect | Call cleanup() in onclose |

### Performance Issues

- **High message latency** - Check network conditions, consider batching
- **CPU spike** - May be message flood, implement rate limiting
- **Memory growth** - Ensure old messages are garbage collected
- **Browser crash** - Check message queue size, implement max queue limit

### WebRTC Issues

- **No audio/video** - Check getUserMedia permissions
- **Connection fails** - Verify STUN/TURN servers available
- **One-way audio** - May be firewall, check ICE candidate gathering
- **Jitter** - Network issue, not WebSocket issue, reduce bitrate

---

## Related Documentation

- [REST API Documentation](API_DOCUMENTATION.md)
- [Authentication Guide](authenticationAndAuthorization/README.md)
- [Database Models](models.py)
- [WebSocket Setup Guide](WEBSOCKET_SERVER_GUIDE.md)
